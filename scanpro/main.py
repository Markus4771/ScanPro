import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import __version__
from .db import Base, DATA_ROOT, engine, get_db, initialize_database
from .models import Destination, JobDelivery, JobDocument, ProcessingProfile, ScanInput, ScanJob
from .schemas import DestinationPayload, ProfilePayload, ScanInputPayload
from .services.shares import ShareError, input_path, normalize_share_name, reload_samba, sync_samba_config

initialize_database()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ScanPro", version=__version__)


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "schema_version": 1}


@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/api/profiles")
def list_profiles(db: Session = Depends(get_db)):
    return db.query(ProcessingProfile).order_by(ProcessingProfile.name).all()


@app.post("/api/profiles")
def create_profile(payload: ProfilePayload, db: Session = Depends(get_db)):
    if db.query(ProcessingProfile).filter(ProcessingProfile.name == payload.name).first():
        raise HTTPException(409, "Profil existiert bereits.")
    row = ProcessingProfile(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row


@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: int, payload: ProfilePayload, db: Session = Depends(get_db)):
    row = db.get(ProcessingProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profil nicht gefunden.")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit(); db.refresh(row)
    return row


@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    if db.query(ScanInput).filter(ScanInput.profile_id == profile_id).first():
        raise HTTPException(409, "Profil wird noch von einem Scan-Eingang verwendet.")
    row = db.get(ProcessingProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profil nicht gefunden.")
    db.delete(row); db.commit()
    return {"deleted": True}


@app.get("/api/destinations")
def list_destinations(db: Session = Depends(get_db)):
    rows = db.query(Destination).order_by(Destination.name).all()
    result = []
    for r in rows:
        cfg = json.loads(r.config_json or "{}")
        if "password" in cfg and cfg["password"]:
            cfg["password"] = "********"
        if "token" in cfg and cfg["token"]:
            cfg["token"] = "********"
        result.append({"id": r.id, "name": r.name, "type": r.type, "enabled": r.enabled, "config": cfg})
    return result


@app.post("/api/destinations")
def create_destination(payload: DestinationPayload, db: Session = Depends(get_db)):
    if payload.type not in {"local", "smb", "paperless"}:
        raise HTTPException(400, "Zieltyp muss local, smb oder paperless sein.")
    if db.query(Destination).filter(Destination.name == payload.name).first():
        raise HTTPException(409, "Scanziel existiert bereits.")
    row = Destination(
        name=payload.name, type=payload.type, enabled=payload.enabled,
        config_json=json.dumps(payload.config, ensure_ascii=False),
    )
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "type": row.type, "enabled": row.enabled, "config": payload.config}


@app.put("/api/destinations/{destination_id}")
def update_destination(destination_id: int, payload: DestinationPayload, db: Session = Depends(get_db)):
    row = db.get(Destination, destination_id)
    if not row:
        raise HTTPException(404, "Scanziel nicht gefunden.")
    row.name = payload.name
    row.type = payload.type
    row.enabled = payload.enabled
    row.config_json = json.dumps(payload.config, ensure_ascii=False)
    db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "type": row.type, "enabled": row.enabled, "config": payload.config}


@app.delete("/api/destinations/{destination_id}")
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    if db.query(ScanInput).filter(ScanInput.destination_id == destination_id).first():
        raise HTTPException(409, "Scanziel wird noch von einem Scan-Eingang verwendet.")
    row = db.get(Destination, destination_id)
    if not row:
        raise HTTPException(404, "Scanziel nicht gefunden.")
    db.delete(row); db.commit()
    return {"deleted": True}


@app.get("/api/inputs")
def list_inputs(request: Request, db: Session = Depends(get_db)):
    host = request.url.hostname or "SCANPRO"
    rows = db.query(ScanInput).order_by(ScanInput.name).all()
    result = []
    for r in rows:
        profile = db.get(ProcessingProfile, r.profile_id)
        destination = db.get(Destination, r.destination_id)
        result.append({
            "id": r.id,
            "name": r.name,
            "share_name": r.share_name,
            "path": r.path,
            "network_path": f"\\\\{host}\\{r.share_name}",
            "profile_id": r.profile_id,
            "profile_name": profile.name if profile else None,
            "destination_id": r.destination_id,
            "destination_name": destination.name if destination else None,
            "enabled": r.enabled,
            "username": "scanpro",
        })
    return result


@app.post("/api/inputs")
def create_input(payload: ScanInputPayload, db: Session = Depends(get_db)):
    if not db.get(ProcessingProfile, payload.profile_id):
        raise HTTPException(400, "Profil existiert nicht.")
    destination = db.get(Destination, payload.destination_id)
    if not destination or not destination.enabled:
        raise HTTPException(400, "Scanziel existiert nicht oder ist deaktiviert.")
    try:
        share = normalize_share_name(payload.share_name or payload.name)
    except ShareError as exc:
        raise HTTPException(400, str(exc)) from exc
    if db.query(ScanInput).filter((ScanInput.name == payload.name) | (ScanInput.share_name == share)).first():
        raise HTTPException(409, "Name oder Freigabe wird bereits verwendet.")
    row = ScanInput(
        name=payload.name,
        share_name=share,
        path="",
        profile_id=payload.profile_id,
        destination_id=payload.destination_id,
        enabled=payload.enabled,
    )
    db.add(row); db.commit(); db.refresh(row)
    row.path = str(input_path(row.id))
    db.commit()
    sync_samba_config(db); reload_samba()
    return {"id": row.id, "share_name": row.share_name, "path": row.path}


@app.put("/api/inputs/{input_id}")
def update_input(input_id: int, payload: ScanInputPayload, db: Session = Depends(get_db)):
    row = db.get(ScanInput, input_id)
    if not row:
        raise HTTPException(404, "Scan-Eingang nicht gefunden.")
    if not db.get(ProcessingProfile, payload.profile_id):
        raise HTTPException(400, "Profil existiert nicht.")
    if not db.get(Destination, payload.destination_id):
        raise HTTPException(400, "Scanziel existiert nicht.")
    try:
        share = normalize_share_name(payload.share_name or payload.name)
    except ShareError as exc:
        raise HTTPException(400, str(exc)) from exc
    row.name = payload.name
    row.share_name = share
    row.profile_id = payload.profile_id
    row.destination_id = payload.destination_id
    row.enabled = payload.enabled
    row.path = str(input_path(row.id))
    db.commit()
    sync_samba_config(db); reload_samba()
    return {"id": row.id, "share_name": row.share_name, "path": row.path}


@app.delete("/api/inputs/{input_id}")
def delete_input(input_id: int, db: Session = Depends(get_db)):
    if db.query(ScanJob).filter(ScanJob.input_id == input_id).first():
        raise HTTPException(409, "Scan-Eingang wurde bereits benutzt und kann nur deaktiviert werden.")
    row = db.get(ScanInput, input_id)
    if not row:
        raise HTTPException(404, "Scan-Eingang nicht gefunden.")
    db.delete(row); db.commit()
    sync_samba_config(db); reload_samba()
    return {"deleted": True}


@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    rows = db.query(ScanJob).order_by(ScanJob.id.desc()).limit(100).all()
    result = []
    for job in rows:
        scan_input = db.get(ScanInput, job.input_id)
        profile = db.get(ProcessingProfile, job.profile_id)
        destination = db.get(Destination, job.destination_id)
        documents = db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).order_by(JobDocument.sequence).all()
        deliveries = db.query(JobDelivery).filter(JobDelivery.scan_job_id == job.id).all()
        result.append({
            "id": job.id,
            "status": job.status,
            "input_name": scan_input.name if scan_input else None,
            "profile_name": profile.name if profile else None,
            "destination_name": destination.name if destination else None,
            "error": job.error,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "documents": [
                {"id": d.id, "sequence": d.sequence, "final_name": d.final_name, "file_url": f"/api/documents/{d.id}/file"}
                for d in documents
            ],
            "deliveries": [
                {"id": d.id, "status": d.status, "target": d.target, "error": d.error}
                for d in deliveries
            ],
        })
    return result


@app.get("/api/documents/{document_id}/file")
def document_file(document_id: int, db: Session = Depends(get_db)):
    row = db.get(JobDocument, document_id)
    if not row or not Path(row.path).exists():
        raise HTTPException(404, "Datei nicht gefunden.")
    return FileResponse(row.path, filename=row.final_name)


@app.get("/api/system")
def system_status(db: Session = Depends(get_db)):
    return {
        "version": __version__,
        "data_root": str(DATA_ROOT),
        "profiles": db.query(ProcessingProfile).count(),
        "destinations": db.query(Destination).count(),
        "inputs": db.query(ScanInput).count(),
        "jobs": db.query(ScanJob).count(),
    }
