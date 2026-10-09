"""Reconcile known ScanPro output files with their database records.

Never remove files or job history. Do not infer jobs from untracked files.
"""
from pathlib import Path

from sqlalchemy.orm import Session

from ..db import DATA_ROOT
from ..models import JobDocument, ScanJob


def sync_output_files(db: Session) -> dict[str, int]:
    output_root = (DATA_ROOT / "Ausgang").resolve()
    scanned = missing = restored = 0
    rows = db.query(JobDocument, ScanJob.status).join(
        ScanJob, JobDocument.scan_job_id == ScanJob.id
    ).all()
    for document, job_status in rows:
        # Do not classify a file as missing while its processing job is active.
        if job_status in {"queued", "processing"}:
            continue
        path = Path(document.path)
        # Database records may reference external destinations; never scan those.
        try:
            absolute = path.absolute()
            absolute.relative_to(output_root)
        except ValueError:
            continue
        # Symlinked files are not followed, preventing traversal out of Ausgang.
        present = absolute.is_file() and not absolute.is_symlink()
        scanned += 1
        if not present:
            missing += 1
        elif not bool(document.file_present):
            restored += 1
        document.file_present = present
    db.commit()
    return {"checked": scanned, "missing": missing, "restored": restored}
