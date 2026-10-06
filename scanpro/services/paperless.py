import json
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from .destinations import resolve_config

from ..models import (
    Destination,
    JobDocument,
    JobDocumentMetadata,
    JobOcrResult,
    JobSeparationMarker,
    ProfilePaperlessRules,
    ScanJob,
    ScanProfile,
)


class PaperlessError(RuntimeError):
    pass


def _cfg(destination: Destination) -> dict:
    try:
        return resolve_config(destination.type, destination.config_json)
    except Exception as exc:
        raise PaperlessError(f"Paperless-Zielkonfiguration konnte nicht geladen werden: {exc}") from exc


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Accept": "application/json; version=10",
    }


def fetch_choices(destination: Destination) -> dict:
    cfg = _cfg(destination)
    base_url = str(cfg.get("base_url", "")).strip().rstrip("/")
    token = str(cfg.get("token", "")).strip()
    verify = bool(cfg.get("verify_ssl", True))
    if not base_url or not token:
        raise PaperlessError("Paperless-URL und API-Token fehlen.")

    endpoints = {
        "correspondents": "correspondents",
        "document_types": "document_types",
        "storage_paths": "storage_paths",
        "tags": "tags",
    }
    result = {}
    try:
        with httpx.Client(headers=_headers(token), timeout=20, verify=verify) as client:
            for key, endpoint in endpoints.items():
                response = client.get(f"{base_url}/api/{endpoint}/?page_size=1000")
                if response.status_code >= 400:
                    raise PaperlessError(
                        f"Paperless {endpoint}: HTTP {response.status_code}: {response.text[:300]}"
                    )
                payload = response.json()
                rows = payload.get("results", payload if isinstance(payload, list) else [])
                result[key] = [
                    {"id": row.get("id"), "name": row.get("name", str(row.get("id")))}
                    for row in rows
                ]
    except httpx.HTTPError as exc:
        raise PaperlessError(f"Paperless-Verbindung fehlgeschlagen: {exc}") from exc
    return result


def get_task_status(destination: Destination, task_id: str) -> dict:
    cfg = _cfg(destination)
    base_url = str(cfg.get("base_url", "")).strip().rstrip("/")
    token = str(cfg.get("token", "")).strip()
    verify = bool(cfg.get("verify_ssl", True))
    if not base_url or not token:
        raise PaperlessError("Paperless-URL und API-Token fehlen.")
    try:
        response = httpx.get(
            f"{base_url}/api/tasks/?task_id={task_id}",
            headers=_headers(token),
            timeout=15,
            verify=verify,
        )
    except httpx.HTTPError as exc:
        raise PaperlessError(f"Paperless-Taskstatus fehlgeschlagen: {exc}") from exc
    if response.status_code >= 400:
        raise PaperlessError(
            f"Paperless-Taskstatus HTTP {response.status_code}: {response.text[:300]}"
        )
    payload = response.json()
    rows = payload.get("results", payload if isinstance(payload, list) else [])
    return rows[0] if rows else {"task_id": task_id, "status": "unknown"}


def _ocr_text(db: Session, document_id: int) -> str:
    row = (
        db.query(JobOcrResult)
        .filter(JobOcrResult.document_id == document_id)
        .order_by(JobOcrResult.id.desc())
        .first()
    )
    return row.text if row else ""


def _code_value(db: Session, job_id: int, sequence: int) -> str:
    markers = (
        db.query(JobSeparationMarker)
        .filter(JobSeparationMarker.scan_job_id == job_id)
        .order_by(JobSeparationMarker.page, JobSeparationMarker.id)
        .all()
    )
    if not markers:
        return ""
    if markers[0].page == 1:
        idx = sequence - 1
    else:
        idx = sequence - 2
    return markers[idx].value if 0 <= idx < len(markers) else ""


def resolve_upload_metadata(
    db: Session,
    job: ScanJob,
    profile: ScanProfile,
    document: JobDocument,
    metadata: JobDocumentMetadata | None,
) -> dict:
    rules = (
        db.query(ProfilePaperlessRules)
        .filter(ProfilePaperlessRules.profile_id == profile.id)
        .first()
    )
    if not rules:
        return {}

    code = _code_value(db, job.id, document.sequence)
    ocr = _ocr_text(db, document.id)
    filename = metadata.final_filename if metadata else Path(document.path).name
    first_line = next((line.strip() for line in ocr.splitlines() if line.strip()), "")

    variables = {
        "filename": Path(filename).stem,
        "profile": profile.name,
        "job": str(job.id),
        "document": f"{document.sequence:03d}",
        "code": code,
        "ocr_first_line": first_line,
    }

    try:
        title = rules.title_template.format(**variables).strip()
    except KeyError as exc:
        raise PaperlessError(f"Unbekannte Variable in Paperless-Titelregel: {exc.args[0]}") from exc

    result: dict = {}
    if title:
        result["title"] = title

    correspondent_map = json.loads(rules.correspondent_map_json or "{}")
    document_type_map = json.loads(rules.document_type_map_json or "{}")
    tags_map = json.loads(rules.tags_map_json or "{}")

    if code and code in correspondent_map:
        result["correspondent"] = correspondent_map[code]
    if code and code in document_type_map:
        result["document_type"] = document_type_map[code]
    if code and code in tags_map:
        result["tags"] = tags_map[code]

    for rule in json.loads(rules.ocr_contains_rules_json or "[]"):
        needle = str(rule.get("contains", "")).strip()
        if not needle or needle.lower() not in ocr.lower():
            continue
        if rule.get("correspondent") not in (None, ""):
            result["correspondent"] = rule["correspondent"]
        if rule.get("document_type") not in (None, ""):
            result["document_type"] = rule["document_type"]
        if rule.get("tags"):
            existing = list(result.get("tags", []))
            for tag in rule["tags"]:
                if tag not in existing:
                    existing.append(tag)
            result["tags"] = existing

    return result
