import json
import os
import subprocess
import tempfile
from pathlib import Path

import httpx


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
    if destination_type == "paperless" and "token" in cfg:
        cfg["token"] = "********"
    return cfg


def _paperless_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Accept": "application/json; version=10",
    }


def _paperless_verify(cfg: dict) -> bool:
    return bool(cfg.get("verify_ssl", True))


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

    if destination_type == "paperless":
        base_url = str(cfg.get("base_url", "")).strip().rstrip("/")
        token = str(cfg.get("token", "")).strip()
        if not base_url or not token:
            raise DestinationError("Paperless-URL und API-Token sind erforderlich.")

        try:
            response = httpx.get(
                f"{base_url}/api/documents/?page_size=1",
                headers=_paperless_headers(token),
                timeout=15,
                verify=_paperless_verify(cfg),
            )
        except httpx.HTTPError as exc:
            raise DestinationError(f"Paperless-Verbindung fehlgeschlagen: {exc}") from exc

        if response.status_code >= 400:
            raise DestinationError(
                f"Paperless antwortet mit HTTP {response.status_code}: {response.text[:300]}"
            )

        server_version = response.headers.get("X-Version", "unbekannt")
        api_version = response.headers.get("X-Api-Version", "unbekannt")
        return {
            "ok": True,
            "message": f"Paperless erreichbar (Server {server_version}, API {api_version}).",
        }

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


def deliver_file(
    destination_type: str,
    config_json: str,
    source_path: str,
    target_name: str | None = None,
) -> str:
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

    if destination_type == "paperless":
        base_url = str(cfg.get("base_url", "")).strip().rstrip("/")
        token = str(cfg.get("token", "")).strip()
        if not base_url or not token:
            raise DestinationError("Paperless-URL und API-Token sind erforderlich.")

        title = str(cfg.get("title", "")).strip()
        if not title and target_name:
            title = Path(target_name).stem

        data: list[tuple[str, str]] = []
        if title:
            data.append(("title", title))

        for key in ("correspondent", "document_type", "storage_path"):
            value = cfg.get(key)
            if value not in (None, ""):
                data.append((key, str(value)))

        tags = cfg.get("tags", [])
        if isinstance(tags, str):
            tags = [item.strip() for item in tags.split(",") if item.strip()]
        for tag in tags or []:
            data.append(("tags", str(tag)))

        try:
            with source.open("rb") as handle:
                response = httpx.post(
                    f"{base_url}/api/documents/post_document/",
                    headers=_paperless_headers(token),
                    data=data,
                    files={
                        "document": (
                            target_name or source.name,
                            handle,
                            "application/pdf",
                        )
                    },
                    timeout=120,
                    verify=_paperless_verify(cfg),
                )
        except httpx.HTTPError as exc:
            raise DestinationError(f"Paperless-Upload fehlgeschlagen: {exc}") from exc
        except OSError as exc:
            raise DestinationError(f"Quelldatei konnte nicht geöffnet werden: {exc}") from exc

        if response.status_code >= 400:
            raise DestinationError(
                f"Paperless-Upload HTTP {response.status_code}: {response.text[:500]}"
            )

        task_id = response.text.strip().strip('"')
        return f"paperless-task:{task_id}"

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
