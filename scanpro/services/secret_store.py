import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


SECRET_ROOT = Path(os.getenv("SCANPRO_SECRET_DIR", "/var/lib/scanpro/secrets"))
KEY_FILE = SECRET_ROOT / "master.key"


class SecretStoreError(RuntimeError):
    pass


def _ensure_root() -> None:
    SECRET_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        SECRET_ROOT.chmod(0o700)
    except OSError:
        pass


def ensure_master_key() -> bytes:
    _ensure_root()
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes().strip()
        if key:
            return key

    key = Fernet.generate_key()
    temp = KEY_FILE.with_suffix(".tmp")
    temp.write_bytes(key + b"\n")
    temp.chmod(0o600)
    temp.replace(KEY_FILE)
    KEY_FILE.chmod(0o600)
    return key


def _fernet() -> Fernet:
    try:
        return Fernet(ensure_master_key())
    except Exception as exc:
        raise SecretStoreError(f"Secret-Store-Schlüssel konnte nicht geladen werden: {exc}") from exc


def _path(ref: str) -> Path:
    safe = "".join(ch for ch in ref if ch.isalnum() or ch in {"-", "_", "."})
    if not safe or safe != ref:
        raise SecretStoreError("Ungültige Secret-Referenz.")
    return SECRET_ROOT / f"{safe}.secret"


def put_secret(ref: str, value: str) -> None:
    if value is None:
        value = ""
    _ensure_root()
    encrypted = _fernet().encrypt(value.encode("utf-8"))
    target = _path(ref)
    temp = target.with_suffix(".tmp")
    temp.write_bytes(encrypted)
    temp.chmod(0o600)
    temp.replace(target)
    target.chmod(0o600)


def get_secret(ref: str) -> str:
    target = _path(ref)
    if not target.exists():
        raise SecretStoreError(f"Secret fehlt: {ref}")
    try:
        return _fernet().decrypt(target.read_bytes()).decode("utf-8")
    except InvalidToken as exc:
        raise SecretStoreError(f"Secret konnte nicht entschlüsselt werden: {ref}") from exc
    except OSError as exc:
        raise SecretStoreError(f"Secret konnte nicht gelesen werden: {ref}: {exc}") from exc


def delete_secret(ref: str | None) -> None:
    if not ref:
        return
    try:
        _path(ref).unlink(missing_ok=True)
    except OSError as exc:
        raise SecretStoreError(f"Secret konnte nicht gelöscht werden: {ref}: {exc}") from exc


def secret_ref(destination_id: int, field: str) -> str:
    return f"destination-{destination_id}-{field}"
