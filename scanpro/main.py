import json
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import __version__
from .db import Base, engine, get_db
from .models import Destination, ScanJob, ScanProfile, Scanner, Workflow
from .schemas import (
    DestinationCreate,
    ScanProfileCreate,
    ScannerCreate,
    ScannerImport,
    ScannerUpdate,
    TestScanRequest,
    WorkflowCreate,
)
from .services.naps2 import Naps2Error, discover_devices, scan_to_pdf
from .services.separation import validate_split

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ScanPro", version=__version__)
JOBS_DIR = Path("/var/lib/scanpro/jobs")
WEB_DIR = Path(__file__).parent / "web"

@app.get("/", response_class=HTMLResponse)
def root():
    index = WEB_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}

@app.get("/api/scanners/discover")
def discover_scanners(driver: str = Query("sane", pattern="^(sane|escl)$")):
    try:
        return {"driver": driver, "devices": discover_devices(driver)}
    except Naps2Error as exc:
        raise HTTPException(500, str(exc)) from exc

@app.get("/api/scanners")
def list_scanners(db: Session = Depends(get_db)):
    return db.query(Scanner).order_by(Scanner.name).all()

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
        online = scanner.name in by_driver[scanner.driver]
        result.append({
            "id": scanner.id,
            "name": scanner.name,
            "enabled": scanner.enabled,
            "online": online,
            "driver": scanner.driver,
            "address": scanner.address,
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
    try:
        scan_to_pdf(output=output, device=scanner.name, driver=scanner.driver, dpi=payload.dpi, duplex=payload.duplex, color_mode=payload.color_mode)
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
    return db.query(ScanJob).order_by(ScanJob.id.desc()).limit(100).all()

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
    return FileResponse(path, media_type="application/pdf", filename=path.name)

@app.get("/api/destinations")
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).order_by(Destination.name).all()

@app.post("/api/destinations")
def create_destination(payload: DestinationCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(); config = data.pop("config")
    obj = Destination(**data, config_json=json.dumps(config))
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/api/profiles")
def list_profiles(db: Session = Depends(get_db)):
    return db.query(ScanProfile).order_by(ScanProfile.name).all()

@app.post("/api/profiles")
def create_profile(payload: ScanProfileCreate, db: Session = Depends(get_db)):
    validate_split(payload.split_enabled, payload.split_method)
    obj = ScanProfile(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/api/workflows")
def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.name).all()

@app.post("/api/workflows")
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    if not db.get(ScanProfile, payload.profile_id):
        raise HTTPException(400, "Scanprofil existiert nicht.")
    if not db.get(Destination, payload.destination_id):
        raise HTTPException(400, "Scanziel existiert nicht.")
    if payload.scanner_id is not None and not db.get(Scanner, payload.scanner_id):
        raise HTTPException(400, "Scanner existiert nicht.")
    obj = Workflow(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj
