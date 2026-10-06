import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..db import DATA_ROOT
from ..models import Destination, JobDelivery, JobDocument, ProcessingProfile, ScanInput, ScanJob
from .delivery_v1 import DeliveryError, deliver


class ProcessingError(RuntimeError):
    pass


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value[:160] or "scan"


def final_name(profile: ProcessingProfile, scan_input: ScanInput, job: ScanJob, source: Path) -> str:
    now = datetime.now()
    stem = profile.filename_template
    for key, value in {
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H-%M-%S"),
        "{datetime}": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "{input}": scan_input.name,
        "{job}": str(job.id),
        "{document}": "001",
    }.items():
        stem = stem.replace(key, value)
    return safe_name(stem) + (source.suffix.lower() or ".pdf")


def ocr_pdf(source: Path, language: str) -> Path:
    target = source.with_name(source.stem + "-ocr.pdf")
    result = subprocess.run(
        [
            "ocrmypdf",
            "--skip-text",
            "--optimize",
            "1",
            "--language",
            language,
            str(source),
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode not in {0, 6}:
        raise ProcessingError(result.stderr.strip() or result.stdout.strip() or "OCR fehlgeschlagen.")
    return target if target.exists() else source


def process_job(db: Session, job: ScanJob) -> None:
    scan_input = db.get(ScanInput, job.input_id)
    profile = db.get(ProcessingProfile, job.profile_id)
    destination = db.get(Destination, job.destination_id)
    if not scan_input or not profile or not destination:
        raise ProcessingError("Eingang, Profil oder Ziel fehlt.")

    source = Path(job.source_path)
    work_dir = DATA_ROOT / "jobs" / str(job.id)
    work_dir.mkdir(parents=True, exist_ok=True)
    work = work_dir / source.name
    shutil.move(str(source), work)
    job.working_path = str(work)
    job.status = "processing"
    db.commit()

    output = work
    if profile.ocr_enabled and work.suffix.lower() == ".pdf":
        output = ocr_pdf(work, profile.ocr_language)

    name = final_name(profile, scan_input, job, output)
    db.add(JobDocument(scan_job_id=job.id, sequence=1, path=str(output), final_name=name))
    db.commit()

    delivery = JobDelivery(scan_job_id=job.id, destination_id=destination.id, status="delivering")
    db.add(delivery)
    db.commit()

    try:
        delivery.target = deliver(destination, output, name)
        delivery.status = "delivered"
        job.status = "delivered"
        job.error = None
    except DeliveryError as exc:
        delivery.status = "error"
        delivery.error = str(exc)
        job.status = "delivery_error"
        job.error = str(exc)

    job.completed_at = datetime.utcnow()
    db.commit()
