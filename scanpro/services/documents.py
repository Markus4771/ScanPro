from pathlib import Path
from sqlalchemy.orm import Session

from ..models import JobDocument, ScanJob, ScanProfile
from .separation import SeparationError, split_pdf

DOCUMENT_ROOT = Path("/var/lib/scanpro/jobs/documents")


def prepare_job_documents(db: Session, job: ScanJob, profile: ScanProfile) -> list[JobDocument]:
    source = job.output_path or job.input_path
    if not source:
        raise SeparationError("ScanJob hat keine Quelldatei.")

    existing = db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).order_by(JobDocument.sequence).all()
    if existing:
        return existing

    paths: list[str]
    method = "none"
    if profile.split_enabled:
        method = profile.split_method
        output_dir = DOCUMENT_ROOT / str(job.id)
        paths = split_pdf(source, profile.split_method, str(output_dir))
    else:
        paths = [source]

    rows: list[JobDocument] = []
    for sequence, path in enumerate(paths, start=1):
        row = JobDocument(
            scan_job_id=job.id,
            sequence=sequence,
            path=path,
            split_method=method,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
