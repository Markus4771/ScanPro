import json
import shutil
import subprocess
from pathlib import Path

import httpx

from ..models import Destination


class DeliveryError(RuntimeError):
    pass


def config(destination: Destination) -> dict:
    try:
        return json.loads(destination.config_json or "{}")
    except json.JSONDecodeError as exc:
        raise DeliveryError("Ungültige Zielkonfiguration.") from exc


def deliver(destination: Destination, source: Path, final_name: str) -> str:
    cfg = config(destination)

    if destination.type == "local":
        root = Path(str(cfg.get("path", ""))).expanduser()
        if not str(root):
            raise DeliveryError("Lokaler Zielpfad fehlt.")
        root.mkdir(parents=True, exist_ok=True)
        target = root / final_name
        shutil.copy2(source, target)
        return str(target)

    if destination.type == "smb":
        server = str(cfg.get("server", "")).strip()
        share = str(cfg.get("share", "")).strip()
        username = str(cfg.get("username", "")).strip()
        password = str(cfg.get("password", ""))
        domain = str(cfg.get("domain", "")).strip()
        subfolder = str(cfg.get("subfolder", "")).strip().strip("/")
        if not server or not share or not username:
            raise DeliveryError("SMB-Ziel ist unvollständig.")
        remote = f"//{server}/{share}"
        remote_name = f"{subfolder}/{final_name}" if subfolder else final_name
        user = f"{domain}\\{username}" if domain else username
        result = subprocess.run(
            ["smbclient", remote, "-U", f"{user}%{password}", "-c", f'put "{source}" "{remote_name}"'],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise DeliveryError(
                result.stderr.strip() or result.stdout.strip() or "SMB-Upload fehlgeschlagen."
            )
        return f"{remote}/{remote_name}"

    if destination.type == "paperless":
        base_url = str(cfg.get("base_url", "")).rstrip("/")
        token = str(cfg.get("token", "")).strip()
        if not base_url or not token:
            raise DeliveryError("Paperless-URL oder Token fehlt.")
        with source.open("rb") as handle:
            response = httpx.post(
                f"{base_url}/api/documents/post_document/",
                headers={"Authorization": f"Token {token}"},
                files={"document": (final_name, handle, "application/octet-stream")},
                timeout=120,
                verify=bool(cfg.get("verify_ssl", True)),
            )
        if response.status_code >= 300:
            raise DeliveryError(f"Paperless-Upload fehlgeschlagen: HTTP {response.status_code}")
        return f"paperless:{response.text.strip()}"

    raise DeliveryError(f"Unbekannter Zieltyp: {destination.type}")
