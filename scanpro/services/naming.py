import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import (
    JobDocument,
    JobDocumentMetadata,
    JobOcrResult,
    JobSeparationMarker,
    ProfileNamingSettings,
    ScanJob,
    ScanProfile,
)


class NamingError(RuntimeError):
    pass


def _sanitize(value: str, max_length: int = 80) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip()
    value = re.sub(r"[\\/:*?"<>|\r\n\t]+", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" ._-")
    if not value:
        return "scan"
    return value[:max_length]


def _first_ocr_line(db: Session, document_id: int) -> str:
    row = (
        db.query(JobOcrResult)
        .filter(JobOcrResult.document_id == document_id)
        .order_by(JobOcrResult.id.desc())
        .first()
    )
    if not row or not row.text:
        return ""
    for line in row.text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _marker_for_document(
    db: Session,
    job_id: int,
    document_sequence: int,
) -> JobSeparationMarker | None:
    markers = (
        db.query(JobSeparationMarker)
        .filter(JobSeparationMarker.scan_job_id == job_id)
        .order_by(JobSeparationMarker.page, JobSeparationMarker.id)
        .all()
    )
    if not markers:
        return None

    # Common scan pattern: separator page precedes the next document.
    # If a separator is the very first page, it belongs to document 1.
    if markers[0].page == 1:
        index = document_sequence - 1
    else:
        index = document_sequence - 2
    if 0 <= index < len(markers):
        return markers[index]
    return None


def resolve_document_metadata(
    db: Session,
    job: ScanJob,
    profile: ScanProfile,
    document: JobDocument,
) -> JobDocumentMetadata:
    existing = (
        db.query(JobDocumentMetadata)
        .filter(JobDocumentMetadata.document_id == document.id)
        .first()
    )
    if existing:
        return existing

    settings = (
        db.query(ProfileNamingSettings)
        .filter(ProfileNamingSettings.profile_id == profile.id)
        .first()
    )
    template = settings.filename_template if settings else "{date}_{profile}_{document}"
    use_ocr_first_line = settings.use_ocr_first_line if settings else False

    marker = _marker_for_document(db, job.id, document.sequence)
    ocr_first_line = _first_ocr_line(db, document.id)

    created = job.created_at or datetime.utcnow()
    variables = {
        "date": created.strftime("%Y-%m-%d"),
        "time": created.strftime("%H-%M-%S"),
        "datetime": created.strftime("%Y-%m-%d_%H-%M-%S"),
        "profile": profile.name,
        "job": str(job.id),
        "document": f"{document.sequence:03d}",
        "code": marker.value if marker else "",
        "code_type": marker.marker_type if marker else "",
        "ocr_first_line": ocr_first_line if use_ocr_first_line else "",
    }

    try:
        stem = template.format(**variables)
    except KeyError as exc:
        raise NamingError(f"Unbekannte Variable im Dateinamen: {exc.args[0]}") from exc

    stem = _sanitize(stem, 180)
    final_filename = f"{stem}.pdf"
    duplicate = (
        db.query(JobDocumentMetadata)
        .filter(
            JobDocumentMetadata.scan_job_id == job.id,
            JobDocumentMetadata.final_filename == final_filename,
        )
        .first()
    )
    if duplicate:
        final_filename = f"{stem}-{document.sequence:03d}.pdf"

    metadata = {
        "profile": profile.name,
        "job_id": job.id,
        "document_sequence": document.sequence,
        "code": marker.value if marker else None,
        "code_type": marker.marker_type if marker else None,
        "ocr_first_line": ocr_first_line or None,
        "source_filename": Path(document.path).name,
        "final_filename": final_filename,
    }

    row = JobDocumentMetadata(
        scan_job_id=job.id,
        document_id=document.id,
        final_filename=final_filename,
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
