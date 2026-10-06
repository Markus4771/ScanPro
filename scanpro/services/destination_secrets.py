import json

from sqlalchemy.orm import Session

from ..models import Destination
from .secret_store import delete_secret, put_secret, secret_ref


def protect_destination_config(
    destination_id: int,
    destination_type: str,
    config: dict,
    previous_config_json: str | None = None,
) -> dict:
    cfg = dict(config)
    try:
        previous = json.loads(previous_config_json or "{}")
    except json.JSONDecodeError:
        previous = {}

    if destination_type == "smb":
        incoming = cfg.pop("password", None)
        existing_ref = previous.get("password_secret_ref")
        if incoming == "********":
            incoming = None
        if incoming is not None:
            ref = existing_ref or secret_ref(destination_id, "smb-password")
            put_secret(ref, str(incoming))
            cfg["password_secret_ref"] = ref
        elif existing_ref:
            cfg["password_secret_ref"] = existing_ref

    if destination_type == "paperless":
        incoming = cfg.pop("token", None)
        existing_ref = previous.get("token_secret_ref")
        if incoming == "********":
            incoming = None
        if incoming is not None:
            ref = existing_ref or secret_ref(destination_id, "paperless-token")
            put_secret(ref, str(incoming))
            cfg["token_secret_ref"] = ref
        elif existing_ref:
            cfg["token_secret_ref"] = existing_ref

    return cfg


def migrate_destination_secrets(db: Session) -> int:
    changed = 0
    rows = db.query(Destination).all()
    for row in rows:
        try:
            cfg = json.loads(row.config_json or "{}")
        except json.JSONDecodeError:
            continue

        original = dict(cfg)

        if row.type == "smb" and "password" in cfg:
            value = cfg.pop("password")
            if value:
                ref = cfg.get("password_secret_ref") or secret_ref(row.id, "smb-password")
                put_secret(ref, str(value))
                cfg["password_secret_ref"] = ref

        if row.type == "paperless" and "token" in cfg:
            value = cfg.pop("token")
            if value:
                ref = cfg.get("token_secret_ref") or secret_ref(row.id, "paperless-token")
                put_secret(ref, str(value))
                cfg["token_secret_ref"] = ref

        if cfg != original:
            row.config_json = json.dumps(cfg, ensure_ascii=False)
            changed += 1

    if changed:
        db.commit()
    return changed


def delete_destination_secrets(destination: Destination) -> None:
    try:
        cfg = json.loads(destination.config_json or "{}")
    except json.JSONDecodeError:
        return
    delete_secret(cfg.get("password_secret_ref"))
    delete_secret(cfg.get("token_secret_ref"))
