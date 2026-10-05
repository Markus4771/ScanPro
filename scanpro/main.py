import json
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import __version__
from .db import Base, DATABASE_URL, engine, get_db, initialize_database
from .models import Destination, InboxImport, JobDelivery, JobDocument, JobDocumentMetadata, JobImageProcessing, JobOcrResult, JobProcessing, JobSeparationMarker, ProfileImageProcessing, ProfileNamingSettings, ProfileOcrSettings, ProfileOutputSettings, ProfilePaperlessRules, ProfileProcessing, ProfileShare, ScanJob, ScanProfile, Scanner, ScannerConnectionSettings, ScannerStaticTarget, Workflow
from .schemas import (
    DestinationCreate,
    DestinationUpdate,
    ScanProfileCreate,
    ScanProfileUpdate,
    ProfileShareUpdate,
    ProfileProcessingUpdate,
    ProfileImageProcessingUpdate,
    ProfileOcrSettingsUpdate,
    ProfileNamingSettingsUpdate,
    ProfilePaperlessRulesUpdate,
    ProfileOutputSettingsUpdate,
    ScannerCreate,
    ScannerImport,
    ScannerUpdate,
    ScannerConnectionSettingsUpdate,
    ScannerStaticTargetUpdate,
    TestScanRequest,
    WorkflowCreate,
    WorkflowUpdate,
)
from .services.blank_pages import BlankPageError, remove_blank_pages
from .services.documents import apply_image_processing, prepare_job_documents
from .services.destinations import DestinationError, public_config, test_destination
from .services.naps2 import Naps2Error, discover_devices, scan_to_pdf
from .services.scanner_connection import check_reachability, classify_scanner_state, effective_scanner_target, get_connection_settings, get_static_target
from .services.profile_shares import ProfileShareError, normalize_share_name, profile_path, write_profile_samba_config
from .services.image_processing import ImageProcessingError
from .services.ocr import OcrError, apply_ocr
from .services.naming import NamingError, resolve_document_metadata
from .services.paperless import PaperlessError, fetch_choices, get_task_status, resolve_upload_metadata
from .services.output_formats import OutputFormatError, convert_documents_to_output_format, get_output_settings
from .services.separation import SeparationError, validate_split
from .services.workflows import deliver_job
from .migrations import CURRENT_SCHEMA_VERSION, get_schema_version, run_schema_migrations

initialize_database()
Base.metadata.create_all(bind=engine)
run_schema_migrations(engine)


def sync_profile_shares(db: Session) -> None:
    shares = db.query(ProfileShare).filter(ProfileShare.enabled.is_(True)).order_by(ProfileShare.id).all()
    rendered: list[tuple[str, str]] = []
    for share in shares:
        path = Path(share.path)
        path.mkdir(parents=True, exist_ok=True)
        rendered.append((share.share_name, str(path)))
    write_profile_samba_config(rendered)

app = FastAPI(title="ScanPro", version=__version__)
JOBS_DIR = Path("/var/lib/scanpro/jobs")
WEB_DIR = Path(__file__).parent / "web"

@app.get("/", response_class=HTMLResponse)
def root():
    index = WEB_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "schema_version": get_schema_version(engine),
    }

@app.get("/api/system/database")
def database_status():
    db_path = DATABASE_URL.removeprefix("sqlite:///") if DATABASE_URL.startswith("sqlite:///") else DATABASE_URL
    journal_mode = None
    foreign_keys = None
    if DATABASE_URL.startswith("sqlite:///"):
        with engine.connect() as connection:
            journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar()
            foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
    return {
        "database_url": DATABASE_URL,
        "path": db_path,
        "schema_version": get_schema_version(engine),
        "target_schema_version": CURRENT_SCHEMA_VERSION,
        "journal_mode": journal_mode,
        "foreign_keys": bool(foreign_keys) if foreign_keys is not None else None,
    }

@app.get("/api/scanners/discover")
def discover_scanners(driver: str = Query("sane", pattern="^(sane|escl)$")):
    try:
        return {"driver": driver, "devices": discover_devices(driver)}
    except Naps2Error as exc:
        raise HTTPException(500, str(exc)) from exc

@app.get("/api/scanners")
def list_scanners(db: Session = Depends(get_db)):
    return db.query(Scanner).order_by(Scanner.name).all()

@app.get("/api/scanner-static-targets")
def list_scanner_static_targets(db: Session = Depends(get_db)):
    scanners = db.query(Scanner).order_by(Scanner.name).all()
    result = []
    for scanner in scanners:
        row = get_static_target(db, scanner)
        result.append({
            "scanner_id": scanner.id,
            "enabled": bool(row.enabled) if row else False,
            "driver": row.driver if row else scanner.driver,
            "device_name": row.device_name if row else scanner.name,
            "device_id": row.device_id if row else (scanner.device_id or ""),
            "address": row.address if row else (scanner.address or ""),
        })
    return result

@app.put("/api/scanners/{scanner_id}/static-target")
def update_scanner_static_target(
    scanner_id: int,
    payload: ScannerStaticTargetUpdate,
    db: Session = Depends(get_db),
):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")

    driver = payload.driver.strip().lower()
    if driver not in {"sane", "escl"}:
        raise HTTPException(400, "Driver muss sane oder escl sein.")

    row = get_static_target(db, scanner)
    if not row:
        row = ScannerStaticTarget(scanner_id=scanner_id)
        db.add(row)

    row.enabled = payload.enabled
    row.driver = driver
    row.device_name = payload.device_name.strip() or scanner.name
    row.device_id = payload.device_id.strip()
    row.address = payload.address.strip()
    db.commit(); db.refresh(row)
    return {
        "scanner_id": scanner_id,
        "enabled": row.enabled,
        "driver": row.driver,
        "device_name": row.device_name,
        "device_id": row.device_id,
        "address": row.address,
    }

@app.get("/api/scanner-connection-settings")
def list_scanner_connection_settings(db: Session = Depends(get_db)):
    scanners = db.query(Scanner).order_by(Scanner.name).all()
    return [
        {
            "scanner_id": scanner.id,
            "location": get_connection_settings(db, scanner).location,
            "connection_type": get_connection_settings(db, scanner).connection_type,
            "timeout_seconds": get_connection_settings(db, scanner).timeout_seconds,
            "retries": get_connection_settings(db, scanner).retries,
        }
        for scanner in scanners
    ]

@app.put("/api/scanners/{scanner_id}/connection-settings")
def update_scanner_connection_settings(
    scanner_id: int,
    payload: ScannerConnectionSettingsUpdate,
    db: Session = Depends(get_db),
):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")

    connection_type = payload.connection_type.strip().lower()
    if connection_type not in {"local", "vpn"}:
        raise HTTPException(400, "connection_type muss local oder vpn sein.")
    if not 5 <= payload.timeout_seconds <= 600:
        raise HTTPException(400, "Timeout muss zwischen 5 und 600 Sekunden liegen.")
    if not 0 <= payload.retries <= 5:
        raise HTTPException(400, "Retries müssen zwischen 0 und 5 liegen.")

    row = get_connection_settings(db, scanner)
    row.location = payload.location.strip() or "Lokal"
    row.connection_type = connection_type
    row.timeout_seconds = payload.timeout_seconds
    row.retries = payload.retries
    db.commit(); db.refresh(row)
    return {
        "scanner_id": scanner_id,
        "location": row.location,
        "connection_type": row.connection_type,
        "timeout_seconds": row.timeout_seconds,
        "retries": row.retries,
    }

@app.post("/api/scanners/{scanner_id}/reachability")
def scanner_reachability(scanner_id: int, db: Session = Depends(get_db)):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")
    settings = get_connection_settings(db, scanner)
    target = effective_scanner_target(db, scanner)
    reachability_scanner = Scanner(
        name=target["device_name"],
        driver=target["driver"],
        address=target["address"],
        device_id=target["device_id"],
    )
    result = check_reachability(
        reachability_scanner,
        timeout_seconds=4.0 if settings.connection_type == "vpn" else 2.0,
    )
    return {
        "scanner_id": scanner.id,
        "reachable": result.reachable,
        "method": result.method,
        "detail": result.detail,
        "location": settings.location,
        "connection_type": settings.connection_type,
    }

@app.get("/api/scanners/status")
def scanner_status(db: Session = Depends(get_db)):
    scanners = db.query(Scanner).order_by(Scanner.name).all()
    by_driver: dict[str, set[str]] = {}
    result = []
    for scanner in scanners:
        if scanner.driver not in by_driver:
            try:
                devices = discover_devices(scanner.driver)
                by_driver[scanner.driver] = {d["name"] for d in devices}
            except Naps2Error:
                by_driver[scanner.driver] = set()
        settings = get_connection_settings(db, scanner)
        target = effective_scanner_target(db, scanner)
        discovered = target["device_name"] in by_driver.get(target["driver"], set())
        reachability_scanner = Scanner(
            name=target["device_name"],
            driver=target["driver"],
            address=target["address"],
            device_id=target["device_id"],
        )
        reachability = check_reachability(
            reachability_scanner,
            timeout_seconds=4.0 if settings.connection_type == "vpn" else 2.0,
        )
        online = discovered or reachability.reachable
        discovery_ok = discovered or target["source"] == "static"
        state = classify_scanner_state(discovery_ok, reachability.reachable)
        result.append({
            "id": scanner.id,
            "name": scanner.name,
            "enabled": scanner.enabled,
            "online": online,
            "state": state,
            "discovered": discovered,
            "reachable": reachability.reachable,
            "reachability_method": reachability.method,
            "reachability_detail": reachability.detail,
            "driver": target["driver"],
            "address": target["address"],
            "target_source": target["source"],
            "target_device_name": target["device_name"],
            "target_device_id": target["device_id"],
            "location": settings.location,
            "connection_type": settings.connection_type,
            "timeout_seconds": settings.timeout_seconds,
            "retries": settings.retries,
        })
    return result

@app.post("/api/scanners")
def create_scanner(payload: ScannerCreate, db: Session = Depends(get_db)):
    obj = Scanner(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.post("/api/scanners/import")
def import_scanner(payload: ScannerImport, db: Session = Depends(get_db)):
    existing = db.query(Scanner).filter(Scanner.name == payload.name).first()
    if existing:
        existing.driver = payload.driver
        existing.address = payload.address
        existing.device_id = payload.device_id
        existing.backend = "naps2"
        existing.enabled = True
        db.commit(); db.refresh(existing)
        return existing
    obj = Scanner(name=payload.name, backend="naps2", driver=payload.driver, address=payload.address, device_id=payload.device_id, enabled=True)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.patch("/api/scanners/{scanner_id}")
def update_scanner(scanner_id: int, payload: ScannerUpdate, db: Session = Depends(get_db)):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")
    data = payload.model_dump(exclude_none=True)
    if "name" in data and data["name"] != scanner.name:
        exists = db.query(Scanner).filter(Scanner.name == data["name"]).first()
        if exists:
            raise HTTPException(409, "Ein Scanner mit diesem Namen existiert bereits.")
    for key, value in data.items():
        setattr(scanner, key, value)
    db.commit(); db.refresh(scanner)
    return scanner

@app.delete("/api/scanners/{scanner_id}")
def delete_scanner(scanner_id: int, db: Session = Depends(get_db)):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")
    linked = db.query(Workflow).filter(Workflow.scanner_id == scanner_id).first()
    if linked:
        raise HTTPException(409, "Scanner wird noch von einem Workflow verwendet.")
    connection_settings = (
        db.query(ScannerConnectionSettings)
        .filter(ScannerConnectionSettings.scanner_id == scanner_id)
        .first()
    )
    if connection_settings:
        db.delete(connection_settings)
    static_target = (
        db.query(ScannerStaticTarget)
        .filter(ScannerStaticTarget.scanner_id == scanner_id)
        .first()
    )
    if static_target:
        db.delete(static_target)
    db.delete(scanner); db.commit()
    return {"deleted": True, "id": scanner_id}

@app.post("/api/scanners/{scanner_id}/testscan")
def test_scan(scanner_id: int, payload: TestScanRequest, db: Session = Depends(get_db)):
    scanner = db.get(Scanner, scanner_id)
    if not scanner:
        raise HTTPException(404, "Scanner wurde nicht gefunden.")
    if not scanner.enabled:
        raise HTTPException(400, "Scanner ist deaktiviert.")
    job = ScanJob(status="queued")
    db.add(job); db.commit(); db.refresh(job)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = JOBS_DIR / f"testscan-{job.id}-{timestamp}.pdf"
    job.output_path = str(output); job.status = "scanning"; db.commit()
    settings = get_connection_settings(db, scanner)
    target = effective_scanner_target(db, scanner)
    try:
        scan_to_pdf(
            output=output,
            device=target["device_name"],
            driver=target["driver"],
            dpi=payload.dpi,
            duplex=payload.duplex,
            color_mode=payload.color_mode,
            timeout_seconds=settings.timeout_seconds,
            retries=settings.retries,
            airscan_device=target.get("airscan_device"),
        )
        job.status = "finished"; job.error = None; db.commit(); db.refresh(job)
        return {
            "job_id": job.id,
            "status": job.status,
            "scanner": scanner.name,
            "output_path": job.output_path,
            "file_url": f"/api/jobs/{job.id}/file",
        }
    except Naps2Error as exc:
        job.status = "error"; job.error = str(exc); db.commit()
        raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ScanJob).order_by(ScanJob.id.desc()).limit(100).all()
    result = []
    for job in jobs:
        inbox = db.query(InboxImport).filter(InboxImport.scan_job_id == job.id).first()
        workflow = db.get(Workflow, job.workflow_id) if job.workflow_id else None
        profile_id = inbox.profile_id if inbox else (workflow.profile_id if workflow else None)
        profile = db.get(ScanProfile, profile_id) if profile_id else None
        deliveries = db.query(JobDelivery).filter(JobDelivery.scan_job_id == job.id).order_by(JobDelivery.id).all()
        processing = db.query(JobProcessing).filter(JobProcessing.scan_job_id == job.id).first()
        documents = db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).order_by(JobDocument.sequence).all()
        markers = db.query(JobSeparationMarker).filter(JobSeparationMarker.scan_job_id == job.id).order_by(JobSeparationMarker.page).all()
        image_rows = db.query(JobImageProcessing).filter(JobImageProcessing.scan_job_id == job.id).all()
        ocr_rows = db.query(JobOcrResult).filter(JobOcrResult.scan_job_id == job.id).all()
        metadata_rows = db.query(JobDocumentMetadata).filter(JobDocumentMetadata.scan_job_id == job.id).all()
        metadata_by_document = {row.document_id: row for row in metadata_rows}
        result.append({
            "id": job.id,
            "workflow_id": job.workflow_id,
            "status": job.status,
            "input_path": job.input_path,
            "output_path": job.output_path,
            "error": job.error,
            "created_at": job.created_at,
            "profile_id": profile_id,
            "profile_name": profile.name if profile else None,
            "source": "profile-smb" if inbox else "scanner",
            "blank_pages_removed": processing.blank_pages_removed if processing else 0,
            "blank_pages": json.loads(processing.blank_pages_json) if processing else [],
            "ocr": {
                "documents": len(ocr_rows),
                "characters": sum(row.characters for row in ocr_rows),
                "languages": sorted({row.language for row in ocr_rows}),
            },
            "image_processing": {
                "pages_processed": sum(row.pages_processed for row in image_rows),
                "pages_rotated": sum(row.pages_rotated for row in image_rows),
                "pages_deskewed": sum(row.pages_deskewed for row in image_rows),
                "pages_cropped": sum(row.pages_cropped for row in image_rows),
                "pages_border_cleaned": sum(row.pages_border_cleaned for row in image_rows),
            },
            "separation_markers": [
                {
                    "id": marker.id,
                    "page": marker.page,
                    "type": marker.marker_type,
                    "value": marker.value,
                }
                for marker in markers
            ],
            "documents": [
                {
                    "id": document.id,
                    "sequence": document.sequence,
                    "path": document.path,
                    "split_method": document.split_method,
                    "final_filename": metadata_by_document.get(document.id).final_filename if metadata_by_document.get(document.id) else None,
                    "metadata": json.loads(metadata_by_document.get(document.id).metadata_json) if metadata_by_document.get(document.id) else None,
                    "file_url": f"/api/job-documents/{document.id}/file",
                }
                for document in documents
            ],
            "deliveries": [
                {
                    "id": item.id,
                    "destination_id": item.destination_id,
                    "workflow_id": item.workflow_id,
                    "status": item.status,
                    "target_path": item.target_path,
                    "error": item.error,
                }
                for item in deliveries
            ],
        })
    return result

@app.get("/api/inbox-imports")
def list_inbox_imports(db: Session = Depends(get_db)):
    rows = db.query(InboxImport).order_by(InboxImport.id.desc()).limit(100).all()
    result = []
    for row in rows:
        profile = db.get(ScanProfile, row.profile_id)
        result.append({
            "id": row.id,
            "scan_job_id": row.scan_job_id,
            "profile_id": row.profile_id,
            "profile_name": profile.name if profile else None,
            "source_path": row.source_path,
            "imported_path": row.imported_path,
            "created_at": row.created_at,
        })
    return result

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(404, "ScanJob wurde nicht gefunden.")
    return job

@app.get("/api/jobs/{job_id}/file")
def get_job_file(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ScanJob, job_id)
    if not job or not job.output_path:
        raise HTTPException(404, "Keine Datei für diesen ScanJob vorhanden.")
    path = Path(job.output_path)
    if not path.exists() or JOBS_DIR not in path.parents:
        raise HTTPException(404, "Scan-Datei wurde nicht gefunden.")
    return FileResponse(path, filename=path.name)

@app.get("/api/job-documents/{document_id}/metadata")
def get_job_document_metadata(document_id: int, db: Session = Depends(get_db)):
    document = db.get(JobDocument, document_id)
    if not document:
        raise HTTPException(404, "Dokument wurde nicht gefunden.")
    row = (
        db.query(JobDocumentMetadata)
        .filter(JobDocumentMetadata.document_id == document_id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Für dieses Dokument liegen noch keine Metadaten vor.")
    return {
        "document_id": document_id,
        "final_filename": row.final_filename,
        "metadata": json.loads(row.metadata_json),
    }

@app.get("/api/job-documents/{document_id}/ocr")
def get_job_document_ocr(document_id: int, db: Session = Depends(get_db)):
    document = db.get(JobDocument, document_id)
    if not document:
        raise HTTPException(404, "Dokument wurde nicht gefunden.")
    row = (
        db.query(JobOcrResult)
        .filter(JobOcrResult.document_id == document_id)
        .order_by(JobOcrResult.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, "Für dieses Dokument liegt kein OCR-Ergebnis vor.")
    return {
        "document_id": document_id,
        "language": row.language,
        "characters": row.characters,
        "text": row.text,
    }

@app.get("/api/job-documents/{document_id}/file")
def get_job_document_file(document_id: int, db: Session = Depends(get_db)):
    document = db.get(JobDocument, document_id)
    if not document:
        raise HTTPException(404, "Dokument wurde nicht gefunden.")
    path = Path(document.path)
    if not path.exists() or JOBS_DIR not in path.parents:
        raise HTTPException(404, "Dokumentdatei wurde nicht gefunden.")
    return FileResponse(path, filename=path.name)

@app.get("/api/destinations/{destination_id}/paperless/choices")
def paperless_choices(destination_id: int, db: Session = Depends(get_db)):
    destination = db.get(Destination, destination_id)
    if not destination or destination.type != "paperless":
        raise HTTPException(404, "Paperless-Ziel wurde nicht gefunden.")
    try:
        return fetch_choices(destination)
    except PaperlessError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/deliveries/{delivery_id}/paperless-task")
def paperless_task(delivery_id: int, db: Session = Depends(get_db)):
    delivery = db.get(JobDelivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Delivery wurde nicht gefunden.")
    destination = db.get(Destination, delivery.destination_id)
    if not destination or destination.type != "paperless":
        raise HTTPException(400, "Delivery gehört nicht zu einem Paperless-Ziel.")
    if not delivery.target_path or not delivery.target_path.startswith("paperless-task:"):
        raise HTTPException(404, "Keine Paperless-Task-ID vorhanden.")
    task_id = delivery.target_path.split(":", 1)[1]
    try:
        return get_task_status(destination, task_id)
    except PaperlessError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/profile-output-settings")
def list_profile_output_settings(db: Session = Depends(get_db)):
    rows = db.query(ProfileOutputSettings).order_by(ProfileOutputSettings.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "mode": row.mode,
            "output_format": row.output_format,
            "jpeg_quality": row.jpeg_quality,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/output-settings")
def update_profile_output_settings(
    profile_id: int,
    payload: ProfileOutputSettingsUpdate,
    db: Session = Depends(get_db),
):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")

    mode = payload.mode.strip().lower()
    output_format = payload.output_format.strip().lower()
    if mode not in {"document", "photo"}:
        raise HTTPException(400, "Profilmodus muss document oder photo sein.")
    if output_format not in {"pdf", "jpeg", "png"}:
        raise HTTPException(400, "Ausgabeformat muss PDF, JPEG oder PNG sein.")
    if not 1 <= payload.jpeg_quality <= 100:
        raise HTTPException(400, "JPEG-Qualität muss zwischen 1 und 100 liegen.")

    if output_format in {"jpeg", "png"}:
        profile.ocr_enabled = False
        profile.split_enabled = False
        profile.split_method = "none"
        profile.color_mode = "color"

    row = db.query(ProfileOutputSettings).filter(ProfileOutputSettings.profile_id == profile_id).first()
    if not row:
        row = ProfileOutputSettings(profile_id=profile_id)
        db.add(row)
    row.mode = mode
    row.output_format = output_format
    row.jpeg_quality = payload.jpeg_quality
    db.commit(); db.refresh(row)
    return {
        "profile_id": profile_id,
        "mode": row.mode,
        "output_format": row.output_format,
        "jpeg_quality": row.jpeg_quality,
    }

@app.get("/api/profile-paperless-rules")
def list_profile_paperless_rules(db: Session = Depends(get_db)):
    rows = db.query(ProfilePaperlessRules).order_by(ProfilePaperlessRules.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "title_template": row.title_template,
            "correspondent_map": json.loads(row.correspondent_map_json or "{}"),
            "document_type_map": json.loads(row.document_type_map_json or "{}"),
            "tags_map": json.loads(row.tags_map_json or "{}"),
            "ocr_contains_rules": json.loads(row.ocr_contains_rules_json or "[]"),
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/paperless-rules")
def update_profile_paperless_rules(
    profile_id: int,
    payload: ProfilePaperlessRulesUpdate,
    db: Session = Depends(get_db),
):
    if not db.get(ScanProfile, profile_id):
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")
    row = db.query(ProfilePaperlessRules).filter(ProfilePaperlessRules.profile_id == profile_id).first()
    if not row:
        row = ProfilePaperlessRules(profile_id=profile_id)
        db.add(row)
    row.title_template = payload.title_template.strip() or "{filename}"
    row.correspondent_map_json = json.dumps(payload.correspondent_map, ensure_ascii=False)
    row.document_type_map_json = json.dumps(payload.document_type_map, ensure_ascii=False)
    row.tags_map_json = json.dumps(payload.tags_map, ensure_ascii=False)
    row.ocr_contains_rules_json = json.dumps(payload.ocr_contains_rules, ensure_ascii=False)
    db.commit(); db.refresh(row)
    return {"profile_id": profile_id, "saved": True}

@app.get("/api/destinations")
def list_destinations(db: Session = Depends(get_db)):
    rows = db.query(Destination).order_by(Destination.name).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "type": row.type,
            "enabled": row.enabled,
            "config": public_config(row.type, row.config_json),
        }
        for row in rows
    ]

@app.post("/api/destinations")
def create_destination(payload: DestinationCreate, db: Session = Depends(get_db)):
    exists = db.query(Destination).filter(Destination.name == payload.name).first()
    if exists:
        raise HTTPException(409, "Ein Scanziel mit diesem Namen existiert bereits.")
    data = payload.model_dump(); config = data.pop("config")
    if data["type"] not in {"local", "smb", "paperless"}:
        raise HTTPException(400, "Unterstützte Zieltypen: lokal, SMB und Paperless-ngx.")
    obj = Destination(**data, config_json=json.dumps(config))
    db.add(obj); db.commit(); db.refresh(obj)
    return {
        "id": obj.id,
        "name": obj.name,
        "type": obj.type,
        "enabled": obj.enabled,
        "config": public_config(obj.type, obj.config_json),
    }

@app.patch("/api/destinations/{destination_id}")
def update_destination(destination_id: int, payload: DestinationUpdate, db: Session = Depends(get_db)):
    obj = db.get(Destination, destination_id)
    if not obj:
        raise HTTPException(404, "Scanziel wurde nicht gefunden.")
    data = payload.model_dump(exclude_none=True)
    if "name" in data and data["name"] != obj.name:
        exists = db.query(Destination).filter(Destination.name == data["name"]).first()
        if exists:
            raise HTTPException(409, "Ein Scanziel mit diesem Namen existiert bereits.")
    if "type" in data and data["type"] not in {"local", "smb", "paperless"}:
        raise HTTPException(400, "Unterstützte Zieltypen: lokal, SMB und Paperless-ngx.")
    if "config" in data:
        cfg = data.pop("config")
        previous = json.loads(obj.config_json or "{}")
        if obj.type == "smb" and cfg.get("password") == "********":
            cfg["password"] = previous.get("password", "")
        if obj.type == "paperless" and cfg.get("token") == "********":
            cfg["token"] = previous.get("token", "")
        obj.config_json = json.dumps(cfg)
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit(); db.refresh(obj)
    return {
        "id": obj.id,
        "name": obj.name,
        "type": obj.type,
        "enabled": obj.enabled,
        "config": public_config(obj.type, obj.config_json),
    }

@app.delete("/api/destinations/{destination_id}")
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    obj = db.get(Destination, destination_id)
    if not obj:
        raise HTTPException(404, "Scanziel wurde nicht gefunden.")
    linked = db.query(Workflow).filter(Workflow.destination_id == destination_id).first()
    if linked:
        raise HTTPException(409, "Scanziel wird noch von einem Workflow verwendet.")
    db.delete(obj); db.commit()
    return {"deleted": True, "id": destination_id}

@app.post("/api/destinations/{destination_id}/test")
def test_destination_endpoint(destination_id: int, db: Session = Depends(get_db)):
    obj = db.get(Destination, destination_id)
    if not obj:
        raise HTTPException(404, "Scanziel wurde nicht gefunden.")
    try:
        return test_destination(obj.type, obj.config_json)
    except DestinationError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/profiles")
def list_profiles(db: Session = Depends(get_db)):
    return db.query(ScanProfile).order_by(ScanProfile.name).all()

@app.get("/api/profile-naming-settings")
def list_profile_naming_settings(db: Session = Depends(get_db)):
    rows = db.query(ProfileNamingSettings).order_by(ProfileNamingSettings.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "filename_template": row.filename_template,
            "use_ocr_first_line": row.use_ocr_first_line,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/naming-settings")
def update_profile_naming_settings(
    profile_id: int,
    payload: ProfileNamingSettingsUpdate,
    db: Session = Depends(get_db),
):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")

    template = payload.filename_template.strip()
    if not template:
        raise HTTPException(400, "Dateinamensvorlage darf nicht leer sein.")

    allowed = {"date", "time", "datetime", "profile", "job", "document", "code", "code_type", "ocr_first_line"}
    import string
    formatter = string.Formatter()
    try:
        for _, field_name, _, _ in formatter.parse(template):
            if field_name and field_name not in allowed:
                raise HTTPException(400, f"Unbekannte Variable: {field_name}")
    except ValueError as exc:
        raise HTTPException(400, f"Ungültige Dateinamensvorlage: {exc}") from exc

    row = (
        db.query(ProfileNamingSettings)
        .filter(ProfileNamingSettings.profile_id == profile_id)
        .first()
    )
    if row:
        row.filename_template = template
        row.use_ocr_first_line = payload.use_ocr_first_line
    else:
        row = ProfileNamingSettings(
            profile_id=profile_id,
            filename_template=template,
            use_ocr_first_line=payload.use_ocr_first_line,
        )
        db.add(row)

    db.commit(); db.refresh(row)
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "filename_template": row.filename_template,
        "use_ocr_first_line": row.use_ocr_first_line,
    }

@app.get("/api/profile-ocr-settings")
def list_profile_ocr_settings(db: Session = Depends(get_db)):
    rows = db.query(ProfileOcrSettings).order_by(ProfileOcrSettings.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "language": row.language,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/ocr-settings")
def update_profile_ocr_settings(
    profile_id: int,
    payload: ProfileOcrSettingsUpdate,
    db: Session = Depends(get_db),
):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")

    language = payload.language.strip()
    if not language:
        raise HTTPException(400, "OCR-Sprache darf nicht leer sein.")

    row = (
        db.query(ProfileOcrSettings)
        .filter(ProfileOcrSettings.profile_id == profile_id)
        .first()
    )
    if row:
        row.language = language
    else:
        row = ProfileOcrSettings(profile_id=profile_id, language=language)
        db.add(row)

    db.commit(); db.refresh(row)
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "language": row.language,
    }

@app.get("/api/profile-image-processing")
def list_profile_image_processing(db: Session = Depends(get_db)):
    rows = db.query(ProfileImageProcessing).order_by(ProfileImageProcessing.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "auto_rotate": row.auto_rotate,
            "deskew": row.deskew,
            "auto_crop": row.auto_crop,
            "remove_borders": row.remove_borders,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/image-processing")
def update_profile_image_processing(
    profile_id: int,
    payload: ProfileImageProcessingUpdate,
    db: Session = Depends(get_db),
):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")

    row = (
        db.query(ProfileImageProcessing)
        .filter(ProfileImageProcessing.profile_id == profile_id)
        .first()
    )
    if row:
        row.auto_rotate = payload.auto_rotate
        row.deskew = payload.deskew
        row.auto_crop = payload.auto_crop
        row.remove_borders = payload.remove_borders
    else:
        row = ProfileImageProcessing(
            profile_id=profile_id,
            auto_rotate=payload.auto_rotate,
            deskew=payload.deskew,
            auto_crop=payload.auto_crop,
            remove_borders=payload.remove_borders,
        )
        db.add(row)

    db.commit(); db.refresh(row)
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "auto_rotate": row.auto_rotate,
        "deskew": row.deskew,
        "auto_crop": row.auto_crop,
        "remove_borders": row.remove_borders,
    }

@app.get("/api/profile-processing")
def list_profile_processing(db: Session = Depends(get_db)):
    rows = db.query(ProfileProcessing).order_by(ProfileProcessing.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "remove_blank_pages": row.remove_blank_pages,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/processing")
def update_profile_processing(profile_id: int, payload: ProfileProcessingUpdate, db: Session = Depends(get_db)):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")
    row = db.query(ProfileProcessing).filter(ProfileProcessing.profile_id == profile_id).first()
    if row:
        row.remove_blank_pages = payload.remove_blank_pages
    else:
        row = ProfileProcessing(profile_id=profile_id, remove_blank_pages=payload.remove_blank_pages)
        db.add(row)
    db.commit(); db.refresh(row)
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "remove_blank_pages": row.remove_blank_pages,
    }

@app.get("/api/profile-shares")
def list_profile_shares(db: Session = Depends(get_db)):
    rows = db.query(ProfileShare).order_by(ProfileShare.profile_id).all()
    return [
        {
            "id": row.id,
            "profile_id": row.profile_id,
            "enabled": row.enabled,
            "share_name": row.share_name,
            "path": row.path,
        }
        for row in rows
    ]

@app.put("/api/profiles/{profile_id}/share")
def configure_profile_share(profile_id: int, payload: ProfileShareUpdate, db: Session = Depends(get_db)):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")

    share = db.query(ProfileShare).filter(ProfileShare.profile_id == profile_id).first()

    if payload.enabled:
        try:
            share_name = normalize_share_name(payload.share_name or profile.name)
        except ProfileShareError as exc:
            raise HTTPException(400, str(exc)) from exc

        duplicate = db.query(ProfileShare).filter(
            ProfileShare.share_name == share_name,
            ProfileShare.profile_id != profile_id,
        ).first()
        if duplicate:
            raise HTTPException(409, "Dieser SMB-Freigabename wird bereits verwendet.")

        path = str(profile_path(profile_id))
        if share:
            share.enabled = True
            share.share_name = share_name
            share.path = path
        else:
            share = ProfileShare(
                profile_id=profile_id,
                enabled=True,
                share_name=share_name,
                path=path,
            )
            db.add(share)
    elif share:
        share.enabled = False

    db.commit()
    sync_profile_shares(db)

    if not share:
        return {"profile_id": profile_id, "enabled": False, "share_name": None, "path": None}
    db.refresh(share)
    return {
        "id": share.id,
        "profile_id": share.profile_id,
        "enabled": share.enabled,
        "share_name": share.share_name,
        "path": share.path,
    }

@app.post("/api/profiles")
def create_profile(payload: ScanProfileCreate, db: Session = Depends(get_db)):
    validate_split(payload.split_enabled, payload.split_method)
    exists = db.query(ScanProfile).filter(ScanProfile.name == payload.name).first()
    if exists:
        raise HTTPException(409, "Ein Scanprofil mit diesem Namen existiert bereits.")
    obj = ScanProfile(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.patch("/api/profiles/{profile_id}")
def update_profile(profile_id: int, payload: ScanProfileUpdate, db: Session = Depends(get_db)):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")
    data = payload.model_dump(exclude_none=True)
    split_enabled = data.get("split_enabled", profile.split_enabled)
    split_method = data.get("split_method", profile.split_method)
    validate_split(split_enabled, split_method)
    if "name" in data and data["name"] != profile.name:
        exists = db.query(ScanProfile).filter(ScanProfile.name == data["name"]).first()
        if exists:
            raise HTTPException(409, "Ein Scanprofil mit diesem Namen existiert bereits.")
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(ScanProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Scanprofil wurde nicht gefunden.")
    linked = db.query(Workflow).filter(Workflow.profile_id == profile_id).first()
    if linked:
        raise HTTPException(409, "Scanprofil wird noch von einem Workflow verwendet.")
    share = db.query(ProfileShare).filter(ProfileShare.profile_id == profile_id).first()
    if share:
        db.delete(share)
    processing = db.query(ProfileProcessing).filter(ProfileProcessing.profile_id == profile_id).first()
    if processing:
        db.delete(processing)
    image_processing = db.query(ProfileImageProcessing).filter(ProfileImageProcessing.profile_id == profile_id).first()
    if image_processing:
        db.delete(image_processing)
    ocr_settings = db.query(ProfileOcrSettings).filter(ProfileOcrSettings.profile_id == profile_id).first()
    if ocr_settings:
        db.delete(ocr_settings)
    naming_settings = db.query(ProfileNamingSettings).filter(ProfileNamingSettings.profile_id == profile_id).first()
    if naming_settings:
        db.delete(naming_settings)
    output_settings = db.query(ProfileOutputSettings).filter(ProfileOutputSettings.profile_id == profile_id).first()
    if output_settings:
        db.delete(output_settings)
    paperless_rules = db.query(ProfilePaperlessRules).filter(ProfilePaperlessRules.profile_id == profile_id).first()
    if paperless_rules:
        db.delete(paperless_rules)
    db.delete(profile)
    db.commit()
    sync_profile_shares(db)
    return {"deleted": True, "id": profile_id}

@app.get("/api/workflows")
def list_workflows(db: Session = Depends(get_db)):
    rows = db.query(Workflow).order_by(Workflow.name).all()
    result = []
    for row in rows:
        scanner = db.get(Scanner, row.scanner_id) if row.scanner_id else None
        profile = db.get(ScanProfile, row.profile_id)
        destination = db.get(Destination, row.destination_id)
        result.append({
            "id": row.id,
            "name": row.name,
            "scanner_id": row.scanner_id,
            "scanner_name": scanner.name if scanner else None,
            "source_type": "scanner" if scanner else "profile-smb",
            "profile_id": row.profile_id,
            "profile_name": profile.name if profile else None,
            "destination_id": row.destination_id,
            "destination_name": destination.name if destination else None,
            "enabled": row.enabled,
        })
    return result

@app.post("/api/workflows")
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    if db.query(Workflow).filter(Workflow.name == payload.name).first():
        raise HTTPException(409, "Ein Workflow mit diesem Namen existiert bereits.")
    if not db.get(ScanProfile, payload.profile_id):
        raise HTTPException(400, "Scanprofil existiert nicht.")
    destination = db.get(Destination, payload.destination_id)
    if not destination:
        raise HTTPException(400, "Scanziel existiert nicht.")
    if payload.scanner_id is not None and not db.get(Scanner, payload.scanner_id):
        raise HTTPException(400, "Scanner existiert nicht.")
    obj = Workflow(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.patch("/api/workflows/{workflow_id}")
def update_workflow(workflow_id: int, payload: WorkflowUpdate, db: Session = Depends(get_db)):
    obj = db.get(Workflow, workflow_id)
    if not obj:
        raise HTTPException(404, "Workflow wurde nicht gefunden.")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != obj.name:
        if db.query(Workflow).filter(Workflow.name == data["name"]).first():
            raise HTTPException(409, "Ein Workflow mit diesem Namen existiert bereits.")
    if "profile_id" in data and data["profile_id"] is not None and not db.get(ScanProfile, data["profile_id"]):
        raise HTTPException(400, "Scanprofil existiert nicht.")
    if "destination_id" in data and data["destination_id"] is not None and not db.get(Destination, data["destination_id"]):
        raise HTTPException(400, "Scanziel existiert nicht.")
    if "scanner_id" in data and data["scanner_id"] is not None and not db.get(Scanner, data["scanner_id"]):
        raise HTTPException(400, "Scanner existiert nicht.")
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit(); db.refresh(obj)
    return obj

@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    obj = db.get(Workflow, workflow_id)
    if not obj:
        raise HTTPException(404, "Workflow wurde nicht gefunden.")
    used = db.query(ScanJob).filter(ScanJob.workflow_id == workflow_id).first()
    if used:
        raise HTTPException(409, "Workflow wurde bereits von ScanJobs verwendet und kann nicht gelöscht werden. Deaktiviere ihn stattdessen.")
    db.delete(obj); db.commit()
    return {"deleted": True, "id": workflow_id}

@app.post("/api/workflows/{workflow_id}/run")
def run_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow wurde nicht gefunden.")
    if not workflow.enabled:
        raise HTTPException(400, "Workflow ist deaktiviert.")
    if workflow.scanner_id is None:
        raise HTTPException(400, "SMB-Inbox-Workflows werden automatisch durch eingehende Dateien gestartet.")

    scanner = db.get(Scanner, workflow.scanner_id)
    profile = db.get(ScanProfile, workflow.profile_id)
    destination = db.get(Destination, workflow.destination_id)
    if not scanner or not scanner.enabled:
        raise HTTPException(400, "Scanner ist nicht verfügbar oder deaktiviert.")
    if not profile:
        raise HTTPException(400, "Scanprofil existiert nicht.")
    if not destination or not destination.enabled:
        raise HTTPException(400, "Scanziel ist nicht verfügbar oder deaktiviert.")

    job = ScanJob(workflow_id=workflow.id, status="scanning")
    db.add(job); db.commit(); db.refresh(job)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = JOBS_DIR / f"workflow-{workflow.id}-job-{job.id}-{timestamp}.pdf"
    job.output_path = str(output)
    db.commit()

    connection_settings = get_connection_settings(db, scanner)
    target = effective_scanner_target(db, scanner)
    try:
        scan_to_pdf(
            output=output,
            device=target["device_name"],
            driver=target["driver"],
            dpi=profile.dpi,
            duplex=profile.duplex,
            color_mode=profile.color_mode,
            timeout_seconds=connection_settings.timeout_seconds,
            retries=connection_settings.retries,
            airscan_device=target.get("airscan_device"),
        )
        job.status = "finished"
        job.error = None
        db.commit()

        processing = db.query(ProfileProcessing).filter(ProfileProcessing.profile_id == profile.id).first()
        if processing and processing.remove_blank_pages and not (
            profile.split_enabled and profile.split_method == "blank-page"
        ):
            try:
                result = remove_blank_pages(str(output))
                db.add(JobProcessing(
                    scan_job_id=job.id,
                    blank_pages_removed=result["removed"],
                    blank_pages_json=json.dumps(result["pages"]),
                ))
                db.commit()
            except BlankPageError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

        try:
            documents = prepare_job_documents(db, job, profile)
            if profile.split_enabled:
                job.status = "separated"
                db.commit()
        except SeparationError as exc:
            job.status = "processing_error"
            job.error = str(exc)
            db.commit()
            raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

        try:
            apply_image_processing(db, job, profile, documents)
        except ImageProcessingError as exc:
            job.status = "processing_error"
            job.error = str(exc)
            db.commit()
            raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

        try:
            documents = convert_documents_to_output_format(db, job, profile, documents)
        except OutputFormatError as exc:
            job.status = "processing_error"
            job.error = str(exc)
            db.commit()
            raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

        output_settings = get_output_settings(db, profile)
        if not output_settings or output_settings.output_format == "pdf":
            try:
                apply_ocr(db, job, profile, documents)
            except OcrError as exc:
                job.status = "processing_error"
                job.error = str(exc)
                db.commit()
                raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc
    except Naps2Error as exc:
        job.status = "error"
        job.error = str(exc)
        db.commit()
        raise HTTPException(500, {"job_id": job.id, "error": str(exc)}) from exc

    documents = db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).order_by(JobDocument.sequence).all()
    deliveries = []
    if documents:
        for document in documents:
            try:
                metadata = resolve_document_metadata(db, job, profile, document)
                paperless_metadata = {}
                if destination.type == "paperless":
                    paperless_metadata = resolve_upload_metadata(
                        db, job, profile, document, metadata
                    )
                deliveries.append(
                    deliver_job(
                        db,
                        job,
                        workflow,
                        destination,
                        source_path=document.path,
                        target_name=metadata.final_filename,
                        metadata=paperless_metadata,
                    )
                )
            except (NamingError, PaperlessError) as exc:
                delivery = JobDelivery(
                    scan_job_id=job.id,
                    workflow_id=workflow.id,
                    destination_id=destination.id,
                    status="error",
                    error=str(exc),
                )
                db.add(delivery)
                db.commit()
                db.refresh(delivery)
                deliveries.append(delivery)
    else:
        deliveries.append(deliver_job(db, job, workflow, destination, source_path=job.output_path or ""))

    if deliveries and all(item.status == "delivered" for item in deliveries):
        job.status = "delivered"
        job.error = None
    else:
        job.status = "delivery_error"
        errors = [item.error for item in deliveries if item.error]
        job.error = " | ".join(errors) if errors else "Weiterleitung fehlgeschlagen."
    db.commit()

    return {
        "job_id": job.id,
        "status": job.status,
        "workflow": workflow.name,
        "scanner": scanner.name,
        "profile": profile.name,
        "destination": destination.name,
        "output_path": job.output_path,
        "file_url": f"/api/jobs/{job.id}/file",
        "documents": [
            {
                "id": document.id,
                "sequence": document.sequence,
                "path": document.path,
                "final_filename": (
                    db.query(JobDocumentMetadata)
                    .filter(JobDocumentMetadata.document_id == document.id)
                    .first()
                    .final_filename
                    if db.query(JobDocumentMetadata)
                    .filter(JobDocumentMetadata.document_id == document.id)
                    .first()
                    else None
                ),
                "file_url": f"/api/job-documents/{document.id}/file",
            }
            for document in documents
        ],
        "deliveries": [
            {
                "status": item.status,
                "target_path": item.target_path,
                "error": item.error,
            }
            for item in deliveries
        ],
    }
