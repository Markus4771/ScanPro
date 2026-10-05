import json
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import __version__
from .db import Base, engine, get_db
from .models import Destination, ProfileShare, ScanJob, ScanProfile, Scanner, Workflow
from .schemas import (
    DestinationCreate,
    DestinationUpdate,
    ScanProfileCreate,
    ScanProfileUpdate,
    ProfileShareUpdate,
    ScannerCreate,
    ScannerImport,
    ScannerUpdate,
    TestScanRequest,
    WorkflowCreate,
)
from .services.destinations import DestinationError, public_config, test_destination
from .services.naps2 import Naps2Error, discover_devices, scan_to_pdf
from .services.profile_shares import ProfileShareError, normalize_share_name, profile_path, write_profile_samba_config
from .services.separation import validate_split

Base.metadata.create_all(bind=engine)


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
    if data["type"] not in {"local", "smb"}:
        raise HTTPException(400, "Aktuell werden nur lokale und SMB-Ziele unterstützt.")
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
    if "type" in data and data["type"] not in {"local", "smb"}:
        raise HTTPException(400, "Aktuell werden nur lokale und SMB-Ziele unterstützt.")
    if "config" in data:
        cfg = data.pop("config")
        if obj.type == "smb" and cfg.get("password") == "********":
            previous = json.loads(obj.config_json or "{}")
            cfg["password"] = previous.get("password", "")
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
    db.delete(profile)
    db.commit()
    sync_profile_shares(db)
    return {"deleted": True, "id": profile_id}

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
