import json
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from . import __version__
from .db import Base, engine, get_db
from .models import Destination, ScanProfile, Scanner, Workflow
from .schemas import DestinationCreate, ScanProfileCreate, ScannerCreate, WorkflowCreate
from .services.separation import validate_split

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ScanPro", version=__version__)

@app.get("/")
def root():
    return {"name": "ScanPro", "version": __version__, "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}

@app.get("/api/scanners")
def list_scanners(db: Session = Depends(get_db)):
    return db.query(Scanner).order_by(Scanner.name).all()

@app.post("/api/scanners")
def create_scanner(payload: ScannerCreate, db: Session = Depends(get_db)):
    obj = Scanner(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/api/destinations")
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).order_by(Destination.name).all()

@app.post("/api/destinations")
def create_destination(payload: DestinationCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    config = data.pop("config")
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
