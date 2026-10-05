from pathlib import Path
from sqlalchemy.orm import Session

from ..models import JobDocument, JobImageProcessing, JobSeparationMarker, ProfileImageProcessing, ScanJob, ScanProfile
from .image_processing import ImageProcessingError, ImageProcessingOptions, process_pdf
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
        result = split_pdf(source, profile.split_method, str(output_dir))
        paths = result.outputs
        for marker in result.markers:
            db.add(JobSeparationMarker(scan_job_id=job.id, page=marker.page, marker_type=marker.type, value=marker.value))
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



def apply_image_processing(
    db: Session,
    job: ScanJob,
    profile: ScanProfile,
    documents: list[JobDocument],
) -> list[JobImageProcessing]:
    config = (
        db.query(ProfileImageProcessing)
        .filter(ProfileImageProcessing.profile_id == profile.id)
        .first()
    )
    if not config or not any(
        (config.auto_rotate, config.deskew, config.auto_crop, config.remove_borders)
    ):
        return []

    options = ImageProcessingOptions(
        auto_rotate=config.auto_rotate,
        deskew=config.deskew,
        auto_crop=config.auto_crop,
        remove_borders=config.remove_borders,
    )

    rows: list[JobImageProcessing] = []
    for document in documents:
        result = process_pdf(document.path, options, render_dpi=profile.dpi)
        row = JobImageProcessing(
            scan_job_id=job.id,
            document_id=document.id,
            pages_processed=result.pages_processed,
            pages_rotated=result.pages_rotated,
            pages_deskewed=result.pages_deskewed,
            pages_cropped=result.pages_cropped,
            pages_border_cleaned=result.pages_border_cleaned,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
