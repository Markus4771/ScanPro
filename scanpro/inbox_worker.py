import logging
import time
from pathlib import Path

from .db import Base, SessionLocal, engine, initialize_database
from .models import ScanInput, ScanJob
from .services.processor import process_job
from .services.shares import sync_samba_config

ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
logger = logging.getLogger(__name__)
POLL_SECONDS = 2
_seen: dict[str, tuple[int, int, int]] = {}


def stable(path: Path) -> bool:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return False
    key = str(path)
    old = _seen.get(key)
    signature = (stat.st_size, stat.st_mtime_ns)
    rounds = old[2] + 1 if old and old[:2] == signature else 1
    _seen[key] = (signature[0], signature[1], rounds)
    return rounds >= 2


def handle(db, scan_input: ScanInput, path: Path):
    job = ScanJob(
        owner_id=scan_input.owner_id,
        input_id=scan_input.id,
        profile_id=scan_input.profile_id,
        destination_id=scan_input.destination_id,
        status="queued",
        source_path=str(path),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    try:
        process_job(db, job)
    except Exception as exc:
        logger.exception("ScanJob %s fehlgeschlagen (Quelldatei: %s)", job_id, path)
        db.rollback()
        failed_job = db.get(ScanJob, job_id)
        if failed_job is not None:
            failed_job.status = "error"
            failed_job.error = str(exc)
            db.commit()


def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    initialize_database()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        sync_samba_config(db)

    while True:
        with SessionLocal() as db:
            inputs = db.query(ScanInput).filter(ScanInput.enabled.is_(True)).all()
            for scan_input in inputs:
                root = Path(scan_input.path)
                root.mkdir(parents=True, exist_ok=True)
                for path in sorted(root.iterdir()):
                    if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
                        continue
                    if not stable(path):
                        continue
                    _seen.pop(str(path), None)
                    handle(db, scan_input, path)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()
