import argparse
import shutil
import time
from pathlib import Path

from .db import Base, SessionLocal, engine, initialize_database
from .models import InboxImport, JobProcessing, ProfileProcessing, ProfileShare, ScanJob, ScanProfile

JOBS_ROOT = Path("/var/lib/scanpro/jobs/inbox")
POLL_SECONDS = 2
STABLE_ROUNDS = 2
ALLOWED_SUFFIXES = {".pdf"}

from .migrations import run_schema_migrations

initialize_database()
Base.metadata.create_all(bind=engine)
run_schema_migrations(engine)

from .services.blank_pages import BlankPageError, remove_blank_pages
from .services.documents import apply_image_processing, prepare_job_documents
from .services.image_processing import ImageProcessingError
from .services.ocr import OcrError, apply_ocr
from .services.separation import SeparationError
from .services.workflows import deliver_to_matching_inbox_workflows


def _safe_filename(name: str) -> str:
    return Path(name).name.replace("/", "_").replace("\\", "_")


def import_file(profile_id: int, source: Path) -> int:
    db = SessionLocal()
    try:
        job = ScanJob(status="importing", input_path=str(source))
        db.add(job)
        db.commit()
        db.refresh(job)

        target_dir = JOBS_ROOT / str(profile_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"job-{job.id}-{_safe_filename(source.name)}"

        try:
            shutil.move(str(source), str(target))
        except Exception as exc:
            job.status = "error"
            job.error = f"Inbox-Import fehlgeschlagen: {exc}"
            db.commit()
            raise

        job.input_path = str(target)
        job.output_path = str(target)
        job.status = "imported"
        job.error = None
        db.add(
            InboxImport(
                profile_id=profile_id,
                scan_job_id=job.id,
                source_path=str(source),
                imported_path=str(target),
            )
        )
        db.commit()

        profile = db.get(ScanProfile, profile_id)
        processing = db.query(ProfileProcessing).filter(ProfileProcessing.profile_id == profile_id).first()
        if processing and processing.remove_blank_pages and not (
            profile and profile.split_enabled and profile.split_method == "blank-page"
        ):
            try:
                result = remove_blank_pages(str(target))
                db.add(JobProcessing(
                    scan_job_id=job.id,
                    blank_pages_removed=result["removed"],
                    blank_pages_json=__import__("json").dumps(result["pages"]),
                ))
                db.commit()
            except BlankPageError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                return job.id

        if profile:
            try:
                documents = prepare_job_documents(db, job, profile)
                if profile.split_enabled:
                    job.status = "separated"
                    db.commit()
            except SeparationError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                return job.id

            try:
                apply_image_processing(db, job, profile, documents)
            except ImageProcessingError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                return job.id

            try:
                apply_ocr(db, job, profile, documents)
            except OcrError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                return job.id

        deliver_to_matching_inbox_workflows(db, job, profile_id)
        return job.id
    finally:
        db.close()


def scan_once(state: dict[str, tuple[int, int, int]]) -> int:
    db = SessionLocal()
    try:
        shares = (
            db.query(ProfileShare)
            .filter(ProfileShare.enabled.is_(True))
            .order_by(ProfileShare.id)
            .all()
        )
        share_data = [(share.profile_id, Path(share.path)) for share in shares]
    finally:
        db.close()

    imported = 0
    active_paths = set()

    for profile_id, folder in share_data:
        folder.mkdir(parents=True, exist_ok=True)
        for source in folder.iterdir():
            if not source.is_file() or source.name.startswith("."):
                continue
            if source.suffix.lower() not in ALLOWED_SUFFIXES:
                continue

            key = str(source)
            active_paths.add(key)
            try:
                stat = source.stat()
            except FileNotFoundError:
                state.pop(key, None)
                continue

            previous = state.get(key)
            signature = (stat.st_size, stat.st_mtime_ns)
            if previous and previous[:2] == signature:
                rounds = previous[2] + 1
            else:
                rounds = 1
            state[key] = (signature[0], signature[1], rounds)

            if rounds >= STABLE_ROUNDS:
                try:
                    import_file(profile_id, source)
                    imported += 1
                    state.pop(key, None)
                except Exception as exc:
                    print(f"Inbox-Import fehlgeschlagen für {source}: {exc}", flush=True)

    for key in list(state):
        if key not in active_paths:
            state.pop(key, None)

    return imported


def run_forever() -> None:
    state: dict[str, tuple[int, int, int]] = {}
    print("ScanPro Profil-Inbox-Worker gestartet.", flush=True)
    while True:
        try:
            scan_once(state)
        except Exception as exc:
            print(f"Inbox-Worker Fehler: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Inboxen einmal prüfen und beenden")
    args = parser.parse_args()
    state: dict[str, tuple[int, int, int]] = {}
    if args.once:
        scan_once(state)
        time.sleep(POLL_SECONDS)
        scan_once(state)
    else:
        run_forever()


if __name__ == "__main__":
    main()
