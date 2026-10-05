import json
import os
import subprocess
import tempfile
from pathlib import Path

class DestinationError(RuntimeError):
    pass

def _load_config(config_json: str) -> dict:
    try:
        return json.loads(config_json or "{}")
    except json.JSONDecodeError as exc:
        raise DestinationError("Ungültige Zielkonfiguration.") from exc

def public_config(destination_type: str, config_json: str) -> dict:
    cfg = _load_config(config_json)
    if destination_type == "smb" and "password" in cfg:
        cfg["password"] = "********"
    return cfg

def test_destination(destination_type: str, config_json: str) -> dict:
    cfg = _load_config(config_json)
    if destination_type == "local":
        path = Path(cfg.get("path", "")).expanduser()
        if not str(path):
            raise DestinationError("Lokaler Zielpfad fehlt.")
        path.mkdir(parents=True, exist_ok=True)
        try:
            fd, temp_path = tempfile.mkstemp(prefix=".scanpro-test-", dir=path)
            os.close(fd)
            Path(temp_path).unlink(missing_ok=True)
        except OSError as exc:
            raise DestinationError(f"Kein Schreibzugriff auf {path}: {exc}") from exc
        return {"ok": True, "message": f"Lokales Ziel ist beschreibbar: {path}"}

    if destination_type == "smb":
        server = cfg.get("server")
        share = cfg.get("share")
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        domain = cfg.get("domain", "")
        subfolder = cfg.get("subfolder", "")
        if not server or not share:
            raise DestinationError("SMB-Server und Freigabe sind erforderlich.")

        target = f"//{server}/{share}"
        auth_user = f"{domain}\\{username}" if domain and username else username
        auth = f"{auth_user}%{password}" if username else "%"
        command = ["smbclient", target, "-U", auth, "-c", "ls"]
        if subfolder:
            command[-1] = f'cd "{subfolder}"; ls'
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        except FileNotFoundError as exc:
            raise DestinationError("smbclient ist nicht installiert.") from exc
        except subprocess.TimeoutExpired as exc:
            raise DestinationError("SMB-Verbindungstest hat das Zeitlimit überschritten.") from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise DestinationError(detail or "SMB-Verbindung fehlgeschlagen.")
        return {"ok": True, "message": f"SMB-Ziel erreichbar: {target}"}

    raise DestinationError(f"Zieltyp wird noch nicht unterstützt: {destination_type}")


def deliver_file(destination_type: str, config_json: str, source_path: str, target_name: str | None = None) -> str:
    cfg = _load_config(config_json)
    source = Path(source_path)
    if not source.exists():
        raise DestinationError(f"Quelldatei wurde nicht gefunden: {source}")

    if destination_type == "local":
        path = Path(cfg.get("path", "")).expanduser()
        if not str(path):
            raise DestinationError("Lokaler Zielpfad fehlt.")
        path.mkdir(parents=True, exist_ok=True)
        target = path / (target_name or source.name)
        import shutil
        try:
            shutil.copy2(source, target)
        except OSError as exc:
            raise DestinationError(f"Datei konnte nicht nach {target} kopiert werden: {exc}") from exc
        return str(target)

    if destination_type == "smb":
        server = cfg.get("server")
        share = cfg.get("share")
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        domain = cfg.get("domain", "")
        subfolder = cfg.get("subfolder", "")
        if not server or not share:
            raise DestinationError("SMB-Server und Freigabe sind erforderlich.")

        target = f"//{server}/{share}"
        auth_user = f"{domain}\\{username}" if domain and username else username
        auth = f"{auth_user}%{password}" if username else "%"
        remote_name = (target_name or source.name).replace('"', "_")
        command_text = f'put "{source}" "{remote_name}"'
        if subfolder:
            command_text = f'cd "{subfolder}"; {command_text}'
        command = ["smbclient", target, "-U", auth, "-c", command_text]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        except FileNotFoundError as exc:
            raise DestinationError("smbclient ist nicht installiert.") from exc
        except subprocess.TimeoutExpired as exc:
            raise DestinationError("SMB-Übertragung hat das Zeitlimit überschritten.") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise DestinationError(detail or "SMB-Übertragung fehlgeschlagen.")
        suffix = f"/{subfolder}" if subfolder else ""
        return f"{target}{suffix}/{remote_name}"

    raise DestinationError(f"Zieltyp wird noch nicht unterstützt: {destination_type}")
