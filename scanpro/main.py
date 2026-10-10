import hashlib
import json
import re
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import __version__
from .auth import admin_user, current_user, hash_password, new_session, verify_password
from .db import Base, DATA_ROOT, claim_unowned_rows, engine, get_db, initialize_database
from .models import (
    Destination, JobDelivery, JobDocument, ProcessingProfile, ScanInput, ScanJob,
    User, UserSession,
)
from .schemas import (
    DestinationPayload, LoginPayload, PasswordChangePayload, ProfilePayload, ScanInputPayload,
    SmbPasswordPayload, UserPayload,
)
from .services.output_sync import sync_output_files
from .services.shares import (
    ShareError, delete_samba_user, ensure_samba_username_available, input_path, normalize_share_name, reload_samba,
    set_samba_password, sync_samba_config,
)

initialize_database()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ScanPro", version=__version__)


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "schema_version": 4}


@app.get("/", response_class=HTMLResponse)
def index():
    html = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/setup-status")
def setup_status(db: Session = Depends(get_db)):
    return {"needs_setup": db.query(User).count() == 0}


@app.post("/api/setup")
def setup(payload: UserPayload, response: Response, db: Session = Depends(get_db)):
    if db.query(User).count() != 0:
        raise HTTPException(409, "ScanPro wurde bereits eingerichtet.")
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    row = User(
        username=payload.username.strip(),
        display_name=payload.display_name.strip() or payload.username.strip(),
        password_hash=password_hash,
        smb_username="legacy_" + payload.username.strip(),
        smb_password="",
        is_admin=True,
        enabled=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    claim_unowned_rows(row.id)
    token = new_session(db, row)
    response.set_cookie("scanpro_session", token, httponly=True, samesite="lax")
    sync_samba_config(db)
    reload_samba()
    return user_json(row)


@app.post("/api/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    row = db.query(User).filter(User.username == payload.username.strip()).first()
    if not row or not row.enabled or not verify_password(payload.password, row.password_hash):
        raise HTTPException(401, "Benutzername oder Passwort ist falsch.")
    token = new_session(db, row)
    response.set_cookie("scanpro_session", token, httponly=True, samesite="lax")
    return user_json(row)


@app.post("/api/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    token = request.cookies.get("scanpro_session")
    if token:
        digest = hashlib.sha256(token.encode()).hexdigest()
        db.query(UserSession).filter(UserSession.token_hash == digest).delete()
        db.commit()
    response.delete_cookie("scanpro_session")
    return {"ok": True}


def user_json(row: User) -> dict:
    return {
        "id": row.id,
        "username": row.username,
        "display_name": row.display_name,
        "is_admin": row.is_admin,
        "enabled": row.enabled,
    }


@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return user_json(user)


@app.post("/api/me/password")
def change_own_password(
    payload: PasswordChangePayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Das aktuelle Passwort ist falsch.")
    if payload.current_password == payload.new_password:
        raise HTTPException(400, "Das neue Passwort muss sich vom aktuellen Passwort unterscheiden.")
    try:
        user.password_hash = hash_password(payload.new_password)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.commit()
    return {"changed": True}


@app.get("/api/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_user),
):
    return [user_json(u) for u in db.query(User).order_by(User.username).all()]


@app.post("/api/users")
def create_user(
    payload: UserPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_user),
):
    username = payload.username.strip()
    if not username:
        raise HTTPException(400, "Benutzername fehlt.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, "Benutzer existiert bereits.")
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    row = User(
        username=username,
        display_name=payload.display_name.strip() or username,
        password_hash=password_hash,
        smb_username="legacy_" + username,
        smb_password="",
        is_admin=payload.is_admin,
        enabled=payload.enabled,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return user_json(row)


@app.post("/api/users/{user_id}/remove")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_user),
):
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(404, "Benutzer nicht gefunden.")
    if row.id == admin.id:
        raise HTTPException(400, "Der aktuell angemeldete Benutzer kann sich nicht selbst löschen.")

    if row.is_admin and row.enabled:
        other_admins = db.query(User).filter(
            User.id != row.id,
            User.is_admin.is_(True),
            User.enabled.is_(True),
        ).count()
        if other_admins == 0:
            raise HTTPException(400, "Der letzte aktive Administrator kann nicht gelöscht werden.")

    # Aktive SMB-Freigaben des Benutzers stilllegen und Samba-Konten merken.
    samba_users = []
    inputs = db.query(ScanInput).filter(ScanInput.owner_id == row.id).all()
    for item in inputs:
        if item.smb_username:
            samba_users.append(item.smb_username)
        item.enabled = False
        item.smb_username = None
        item.smb_password = None
        item.name = f"[gelöscht Benutzer {row.id} / Eingang {item.id}]"
        item.share_name = f"__deleted_user_{row.id}_input_{item.id}"
        item.owner_id = None

    # Profile und Ziele bleiben als historische Referenzen erhalten,
    # sind aber keinem aktiven Benutzer mehr zugeordnet.
    for profile in db.query(ProcessingProfile).filter(ProcessingProfile.owner_id == row.id).all():
        profile.name = f"[gelöscht Benutzer {row.id} / Profil {profile.id}]"
        profile.owner_id = None

    for destination in db.query(Destination).filter(Destination.owner_id == row.id).all():
        if destination.type == "local_smb":
            cfg = json.loads(destination.config_json or "{}")
            if cfg.get("username"):
                samba_users.append(str(cfg["username"]))
            cfg["username"] = ""
            cfg["password"] = ""
            destination.config_json = json.dumps(cfg, ensure_ascii=False)
        destination.name = f"[gelöscht Benutzer {row.id} / Ziel {destination.id}]"
        destination.enabled = False
        destination.owner_id = None

    # Historische Jobs bleiben bestehen, verlieren aber den Benutzerbezug.
    db.query(ScanJob).filter(ScanJob.owner_id == row.id).update(
        {ScanJob.owner_id: None}, synchronize_session=False
    )

    # Alle Sitzungen des Benutzers entfernen und anschließend den Benutzer löschen.
    db.query(UserSession).filter(UserSession.user_id == row.id).delete(
        synchronize_session=False
    )
    db.delete(row)
    db.commit()

    # Samba nach dem DB-Commit bereinigen. Fehler dort dürfen die bereits
    # erfolgreiche Benutzerlöschung nicht zurückrollen.
    try:
        sync_samba_config(db)
        reload_samba()
        for samba_username in samba_users:
            delete_samba_user(samba_username)
    except Exception:
        pass

    return {
        "deleted": True,
        "preserved_jobs": db.query(ScanJob).filter(ScanJob.owner_id.is_(None)).count(),
        "disabled_shares": len(inputs),
    }


def profile_json(row: ProcessingProfile) -> dict:
    return {
        "id": row.id, "name": row.name, "ocr_enabled": row.ocr_enabled,
        "ocr_language": row.ocr_language, "remove_blank_pages": row.remove_blank_pages,
        "auto_rotate": row.auto_rotate, "deskew": row.deskew, "auto_crop": row.auto_crop,
        "split_method": row.split_method, "filename_template": row.filename_template,
        "pdfa_enabled": row.pdfa_enabled, "color_mode": row.color_mode,
        "dpi": row.dpi, "normalize_a4": row.normalize_a4,
        "blank_threshold": row.blank_threshold,
        "subfolder_template": row.subfolder_template,
        "triangle_position": row.triangle_position,
        "triangle_min_size_mm": row.triangle_min_size_mm,
        "triangle_remove_page": row.triangle_remove_page,
        "qr_marker_content": row.qr_marker_content,
    }


def owned(db: Session, model, row_id: int, user: User):
    row = db.get(model, row_id)
    if not row or getattr(row, "owner_id", None) != user.id:
        raise HTTPException(404, "Eintrag nicht gefunden.")
    return row


@app.get("/api/profiles")
def list_profiles(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(ProcessingProfile).filter(
        ProcessingProfile.owner_id == user.id
    ).order_by(ProcessingProfile.name).all()
    return [profile_json(row) for row in rows]


@app.post("/api/profiles")
def create_profile(
    payload: ProfilePayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if db.query(ProcessingProfile).filter(
        ProcessingProfile.owner_id == user.id,
        ProcessingProfile.name == payload.name,
    ).first():
        raise HTTPException(409, "Profil existiert bereits.")
    if payload.color_mode not in {"keep", "gray", "bw"}:
        raise HTTPException(400, "Farbmodus ist ungültig.")
    if payload.dpi not in {0, 150, 200, 300, 400, 600}:
        raise HTTPException(400, "DPI muss Original, 150, 200, 300, 400 oder 600 sein.")
    if payload.blank_threshold < 90 or payload.blank_threshold > 100:
        raise HTTPException(400, "Leerseiten-Schwellwert muss zwischen 90 und 100 liegen.")
    if payload.pdfa_enabled and not payload.ocr_enabled:
        raise HTTPException(400, "PDF/A benötigt in ScanPro derzeit aktiviertes OCR.")
    if payload.split_method == "triangle":
        if payload.triangle_position not in {"any", "top_left", "top_right", "bottom_left", "bottom_right"}:
            raise HTTPException(400, "Dreieck-Position ist ungültig.")
        if payload.triangle_min_size_mm < 5 or payload.triangle_min_size_mm > 80:
            raise HTTPException(400, "Dreieck-Mindestgröße muss zwischen 5 und 80 mm liegen.")

    row = ProcessingProfile(owner_id=user.id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return profile_json(row)


@app.put("/api/profiles/{profile_id}")
def update_profile(
    profile_id: int,
    payload: ProfilePayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, ProcessingProfile, profile_id, user)
    if db.query(ProcessingProfile).filter(
        ProcessingProfile.owner_id == user.id,
        ProcessingProfile.name == payload.name,
        ProcessingProfile.id != profile_id,
    ).first():
        raise HTTPException(409, "Profil existiert bereits.")
    if payload.color_mode not in {"keep", "gray", "bw"}:
        raise HTTPException(400, "Farbmodus ist ungültig.")
    if payload.dpi not in {0, 150, 200, 300, 400, 600}:
        raise HTTPException(400, "DPI muss Original, 150, 200, 300, 400 oder 600 sein.")
    if not 90 <= payload.blank_threshold <= 100:
        raise HTTPException(400, "Leerseiten-Schwellwert muss zwischen 90 und 100 liegen.")
    if payload.pdfa_enabled and not payload.ocr_enabled:
        raise HTTPException(400, "PDF/A benötigt in ScanPro derzeit aktiviertes OCR.")
    if payload.split_method == "triangle":
        if payload.triangle_position not in {"any", "top_left", "top_right", "bottom_left", "bottom_right"}:
            raise HTTPException(400, "Dreieck-Position ist ungültig.")
        if not 5 <= payload.triangle_min_size_mm <= 80:
            raise HTTPException(400, "Dreieck-Mindestgröße muss zwischen 5 und 80 mm liegen.")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return profile_json(row)


@app.post("/api/profiles/{profile_id}/remove")
@app.delete("/api/profiles/{profile_id}")
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, ProcessingProfile, profile_id, user)

    if db.query(ScanInput).filter(
        ScanInput.owner_id == user.id,
        ScanInput.profile_id == profile_id,
        ScanInput.enabled.is_(True),
    ).first():
        raise HTTPException(409, "Profil wird noch von einem aktiven Scan-Eingang verwendet.")

    # Auch alte Jobs ohne owner_id müssen die Historie schützen.
    has_jobs = db.query(ScanJob).filter(
        ScanJob.profile_id == profile_id,
    ).first() is not None

    if has_jobs:
        # Für alte ScanJobs erhalten, aber aus der Benutzeroberfläche entfernen.
        original_name = row.name
        row.name = f"[gelöscht #{row.id}] {original_name}"
        row.owner_id = None
        db.commit()
    else:
        db.delete(row)
        db.commit()

    return {"deleted": True, "history_preserved": has_jobs}


@app.get("/api/destinations")
def list_destinations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Destination).filter(
        Destination.owner_id == user.id
    ).order_by(Destination.name).all()
    result = []
    changed = False
    for r in rows:
        cfg = json.loads(r.config_json or "{}")
        if r.type == "smb" and str(cfg.get("share", "")).strip() != "Ausgang":
            old_share = str(cfg.get("share", "")).strip()
            if not str(cfg.get("subfolder", "")).strip():
                cfg["subfolder"] = old_share or r.name
            cfg["share"] = "Ausgang"
            r.config_json = json.dumps(cfg, ensure_ascii=False)
            changed = True

        visible_cfg = dict(cfg)
        if "password" in visible_cfg and visible_cfg["password"]:
            visible_cfg["password"] = "********"
        if "token" in visible_cfg and visible_cfg["token"]:
            visible_cfg["token"] = "********"
        result.append({"id": r.id, "name": r.name, "type": r.type, "enabled": r.enabled, "config": visible_cfg})

    if changed:
        db.commit()
    return result


@app.post("/api/destinations")
def create_destination(
    payload: DestinationPayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if payload.type not in {"local", "local_smb", "smb", "paperless"}:
        raise HTTPException(400, "Zieltyp muss local, local_smb, smb oder paperless sein.")
    if db.query(Destination).filter(
        Destination.owner_id == user.id, Destination.name == payload.name
    ).first():
        raise HTTPException(409, "Scanziel existiert bereits.")
    config = dict(payload.config)
    if payload.type == "smb":
        old_share = str(config.get("share", "")).strip()
        subfolder = str(config.get("subfolder", "")).strip()
        config["share"] = "Ausgang"
        if not subfolder:
            config["subfolder"] = old_share or payload.name.strip()

    if payload.type == "local_smb":
        try:
            normalize_share_name(payload.name)
        except ShareError as exc:
            raise HTTPException(400, str(exc)) from exc
        password = str(config.get("password", ""))
        if len(password) < 8:
            raise HTTPException(400, "SMB-Passwort muss mindestens 8 Zeichen lang sein.")
        requested_user = str(config.get("username", "")).strip().lower()
        if requested_user:
            if not re.fullmatch(r"[a-z_][a-z0-9_-]{2,30}", requested_user):
                raise HTTPException(400, "Benutzer muss 3 bis 31 Zeichen haben; erlaubt sind Kleinbuchstaben, Zahlen, _ und -.")
            for existing in db.query(Destination).filter(Destination.type == "local_smb").all():
                existing_user = str(json.loads(existing.config_json or "{}").get("username", "")).lower()
                if requested_user == existing_user:
                    raise HTTPException(409, "Dieser Samba-Benutzer wird bereits von einem Scanziel verwendet.")
            if db.query(ScanInput).filter(ScanInput.smb_username == requested_user).first():
                raise HTTPException(409, "Dieser Samba-Benutzer wird bereits von einem Scan-Eingang verwendet.")
            try:
                ensure_samba_username_available(requested_user)
            except ShareError as exc:
                raise HTTPException(409, str(exc)) from exc
            config["username"] = requested_user
        config["share"] = "Ausgang"
        config["subfolder"] = payload.name.strip()

    row = Destination(
        owner_id=user.id, name=payload.name, type=payload.type,
        enabled=payload.enabled, config_json=json.dumps(config, ensure_ascii=False),
    )
    db.add(row)
    db.flush()

    if payload.type == "local_smb":
        config["username"] = config.get("username") or f"scanpro_d{row.id}"
        row.config_json = json.dumps(config, ensure_ascii=False)
        try:
            set_samba_password(config["username"], config["password"])
        except ShareError as exc:
            db.rollback()
            raise HTTPException(500, str(exc)) from exc

    db.commit()
    db.refresh(row)
    if payload.type == "local_smb":
        sync_samba_config(db)
        reload_samba()
    return {"id": row.id, "name": row.name, "type": row.type, "enabled": row.enabled}


@app.get("/api/destinations/{destination_id}/connection-details")
def destination_connection_details(
    destination_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, Destination, destination_id, user)
    cfg = json.loads(row.config_json or "{}")
    if row.type == "smb":
        return {
            "type": "smb",
            "server": cfg.get("server", ""),
            "share": cfg.get("share", "Ausgang"),
            "subfolder": cfg.get("subfolder", ""),
            "username": cfg.get("username", ""),
            "password": cfg.get("password", ""),
            "domain": cfg.get("domain", ""),
        }
    if row.type == "local_smb":
        return {
            "type": "local_smb",
            "share": "Ausgang",
            "subfolder": row.name,
            "username": cfg.get("username", ""),
            "password": cfg.get("password", ""),
        }
    if row.type == "paperless":
        return {
            "type": "paperless",
            "base_url": cfg.get("base_url", ""),
            "token": cfg.get("token", ""),
            "verify_ssl": bool(cfg.get("verify_ssl", True)),
        }
    return {"type": row.type, "path": cfg.get("path", "")}


@app.put("/api/destinations/{destination_id}/smb-password")
def change_destination_smb_password(
    destination_id: int,
    payload: SmbPasswordPayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, Destination, destination_id, user)
    if row.type != "local_smb":
        raise HTTPException(400, "Dieses Scanziel ist keine lokale SMB-Freigabe.")
    if len(payload.smb_password) < 8:
        raise HTTPException(400, "SMB-Passwort muss mindestens 8 Zeichen lang sein.")
    cfg = json.loads(row.config_json or "{}")
    username = str(cfg.get("username", "")).strip() or f"scanpro_d{row.id}"
    try:
        set_samba_password(username, payload.smb_password)
    except ShareError as exc:
        raise HTTPException(500, str(exc)) from exc
    cfg["username"] = username
    cfg["password"] = payload.smb_password
    cfg["share"] = "Ausgang"
    cfg["subfolder"] = row.name
    row.config_json = json.dumps(cfg, ensure_ascii=False)
    db.commit()
    sync_samba_config(db)
    reload_samba()
    return {"id": row.id, "username": username, "password": payload.smb_password}


@app.post("/api/destinations/{destination_id}/remove")
@app.delete("/api/destinations/{destination_id}")
def delete_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, Destination, destination_id, user)
    cfg = json.loads(row.config_json or "{}")
    samba_username = str(cfg.get("username", "")).strip() if row.type == "local_smb" else ""

    if db.query(ScanInput).filter(
        ScanInput.owner_id == user.id,
        ScanInput.destination_id == destination_id,
        ScanInput.enabled.is_(True),
    ).first():
        raise HTTPException(409, "Scanziel wird noch von einem aktiven Scan-Eingang verwendet.")

    has_jobs = db.query(ScanJob).filter(
        ScanJob.destination_id == destination_id,
    ).first() is not None

    if has_jobs:
        original_name = row.name
        row.name = f"[gelöscht #{row.id}] {original_name}"
        row.owner_id = None
        row.enabled = False
        if row.type == "local_smb":
            cfg["username"] = ""
            cfg["password"] = ""
            row.config_json = json.dumps(cfg, ensure_ascii=False)
        db.commit()
    else:
        db.delete(row)
        db.commit()

    if samba_username:
        try:
            sync_samba_config(db)
            reload_samba()
            delete_samba_user(samba_username)
        except Exception:
            pass

    return {"deleted": True, "history_preserved": has_jobs}


@app.get("/api/inputs")
def list_inputs(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    host = request.url.hostname or "SCANPRO"
    rows = db.query(ScanInput).filter(
        ScanInput.owner_id == user.id,
        ScanInput.enabled.is_(True),
        ~ScanInput.name.startswith("[gelöscht"),
        ~ScanInput.share_name.startswith("__deleted_"),
    ).order_by(ScanInput.name).all()
    result = []
    for r in rows:
        profile = db.get(ProcessingProfile, r.profile_id)
        destination = db.get(Destination, r.destination_id)
        result.append({
            "id": r.id, "name": r.name, "share_name": r.share_name, "path": r.path,
            "network_path": f"\\\\{host}\\Eingang\\{r.share_name}",
            "profile_id": r.profile_id, "profile_name": profile.name if profile else None,
            "destination_id": r.destination_id,
            "destination_name": destination.name if destination else None,
            "enabled": r.enabled, "username": r.smb_username,
            "password": r.smb_password,
        })
    return result


@app.post("/api/inputs")
def create_input(
    payload: ScanInputPayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    profile = owned(db, ProcessingProfile, payload.profile_id, user)
    destination = owned(db, Destination, payload.destination_id, user)
    if not destination.enabled:
        raise HTTPException(400, "Scanziel ist deaktiviert.")
    try:
        share = normalize_share_name(payload.share_name or payload.name)
    except ShareError as exc:
        raise HTTPException(400, str(exc)) from exc
    if db.query(ScanInput).filter(ScanInput.share_name == share).first():
        raise HTTPException(409, "Freigabename wird bereits verwendet.")
    if db.query(ScanInput).filter(
        ScanInput.owner_id == user.id, ScanInput.name == payload.name
    ).first():
        raise HTTPException(409, "Name wird bereits verwendet.")
    if len(payload.smb_password) < 8:
        raise HTTPException(400, "SMB-Passwort muss mindestens 8 Zeichen lang sein.")
    requested_user = payload.smb_username.strip().lower()
    if requested_user:
        if not re.fullmatch(r"[a-z_][a-z0-9_-]{2,30}", requested_user):
            raise HTTPException(400, "SMB-Benutzer: 3 bis 31 Zeichen, Kleinbuchstaben, Zahlen, _ oder -.")
        if db.query(ScanInput).filter(ScanInput.smb_username == requested_user).first():
            raise HTTPException(409, "SMB-Benutzer wird bereits von einem Scan-Eingang verwendet.")
        for existing in db.query(Destination).filter(Destination.type == "local_smb").all():
            cfg = json.loads(existing.config_json or "{}")
            if str(cfg.get("username", "")).lower() == requested_user:
                raise HTTPException(409, "SMB-Benutzer wird bereits von einem Scanziel verwendet.")
        try:
            ensure_samba_username_available(requested_user)
        except ShareError as exc:
            raise HTTPException(409, str(exc)) from exc
    row = ScanInput(
        owner_id=user.id, name=payload.name, share_name=share, path="",
        smb_username=requested_user or None, smb_password=payload.smb_password,
        profile_id=profile.id, destination_id=destination.id, enabled=payload.enabled,
    )
    db.add(row); db.flush()
    row.smb_username = row.smb_username or f"scanpro_s{row.id}"
    row.path = str(input_path(row.id, row.share_name))
    try:
        set_samba_password(row.smb_username, payload.smb_password)
    except ShareError as exc:
        db.rollback()
        raise HTTPException(500, str(exc)) from exc
    db.commit(); db.refresh(row)
    sync_samba_config(db); reload_samba()
    return {"id": row.id, "share_name": row.share_name, "path": row.path,
            "username": row.smb_username, "password": row.smb_password}


@app.put("/api/inputs/{input_id}/smb-password")
def change_input_smb_password(
    input_id: int,
    payload: SmbPasswordPayload,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, ScanInput, input_id, user)
    if len(payload.smb_password) < 8:
        raise HTTPException(400, "SMB-Passwort muss mindestens 8 Zeichen lang sein.")
    if not row.smb_username:
        row.smb_username = f"scanpro_s{row.id}"
    try:
        set_samba_password(row.smb_username, payload.smb_password)
    except ShareError as exc:
        raise HTTPException(500, str(exc)) from exc
    row.smb_password = payload.smb_password
    db.commit()
    sync_samba_config(db); reload_samba()
    return {"id": row.id, "username": row.smb_username, "password": row.smb_password}


@app.post("/api/inputs/{input_id}/remove")
@app.delete("/api/inputs/{input_id}")
def delete_input(
    input_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = owned(db, ScanInput, input_id, user)
    samba_username = row.smb_username
    # Bei Altbeständen kann owner_id in alten Jobs fehlen. Entscheidend ist,
    # ob irgendein historischer Job auf diesen Eingang verweist.
    has_jobs = db.query(ScanJob).filter(
        ScanJob.input_id == input_id
    ).first() is not None

    # Immer zuerst aus dem aktiven Betrieb nehmen. Das ist absichtlich
    # idempotent, damit auch Einträge aus älteren fehlerhaften Builds
    # erneut "gelöscht" werden können.
    row.enabled = False
    row.smb_username = None
    row.smb_password = None

    if has_jobs:
        row.name = f"[gelöscht #{row.id}]"
        row.share_name = f"__deleted_{row.id}"
        db.commit()
    else:
        # Ohne historische Jobs kann der Datensatz vollständig entfernt werden.
        # Explizites flush/commit macht das Verhalten für migrierte Altbestände eindeutig.
        db.delete(row)
        db.flush()
        db.commit()

    # Samba-Bereinigung darf das erfolgreiche Entfernen aus der WebGUI
    # nicht mehr verhindern.
    try:
        sync_samba_config(db)
        reload_samba()
        delete_samba_user(samba_username)
    except Exception:
        pass

    return {"deleted": True, "history_preserved": has_jobs}


@app.get("/api/debug/inputs/{input_id}")
def debug_input(
    input_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = db.get(ScanInput, input_id)
    if not row:
        return {"exists": False}
    return {
        "exists": True,
        "id": row.id,
        "owner_id": row.owner_id,
        "current_user_id": user.id,
        "enabled": row.enabled,
        "name": row.name,
        "share_name": row.share_name,
        "smb_username": row.smb_username,
        "jobs": db.query(ScanJob).filter(ScanJob.input_id == input_id).count(),
    }


@app.post("/api/output/sync")
def sync_output_now(db: Session = Depends(get_db), user: User = Depends(current_user)):
    # Only admins may reconcile shared output file statuses for every user.
    if not user.is_admin:
        raise HTTPException(403, "Nur Administratoren dürfen den Ausgang abgleichen.")
    return sync_output_files(db)


@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: int, db: Session = Depends(get_db),
              user: User = Depends(current_user)):
    job = owned(db, ScanJob, job_id, user)
    if job.status not in {"error", "interrupted"}:
        raise HTTPException(409, "Nur fehlgeschlagene oder unterbrochene Jobs können wiederholt werden.")
    if db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).first():
        raise HTTPException(409, "Bereits erzeugte Dokumente vorhanden. Manuell prüfen, um Duplikate zu vermeiden.")
    if job.working_path and Path(job.working_path).exists():
        raise HTTPException(409, "Arbeitsdatei vorhanden. Manuelle Prüfung erforderlich, um Duplikate zu vermeiden.")
    if not Path(job.source_path).is_file():
        raise HTTPException(409, "Originaldatei nicht mehr im Eingang vorhanden. Keine sichere Wiederholung möglich.")
    job.status = "retry_queued"
    job.error = None
    db.commit()
    return {"id": job.id, "status": job.status}


@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(ScanJob).filter(
        ScanJob.owner_id == user.id
    ).order_by(ScanJob.id.desc()).limit(100).all()
    result = []
    for job in rows:
        scan_input = db.get(ScanInput, job.input_id)
        profile = db.get(ProcessingProfile, job.profile_id)
        destination = db.get(Destination, job.destination_id)
        documents = db.query(JobDocument).filter(
            JobDocument.scan_job_id == job.id
        ).order_by(JobDocument.sequence).all()
        deliveries = db.query(JobDelivery).filter(JobDelivery.scan_job_id == job.id).all()
        result.append({
            "id": job.id, "status": job.status,
            "input_name": scan_input.name if scan_input else None,
            "profile_name": profile.name if profile else None,
            "destination_name": destination.name if destination else None,
            "error": job.error, "created_at": job.created_at,
            "completed_at": job.completed_at,
            "documents": [
                {"id": d.id, "sequence": d.sequence, "final_name": d.final_name,
                 "file_present": d.file_present,
                 "file_url": f"/api/documents/{d.id}/file" if d.file_present else None}
                for d in documents
            ],
            "deliveries": [
                {"id": d.id, "status": d.status, "target": d.target, "error": d.error}
                for d in deliveries
            ],
        })
    return result


@app.get("/api/documents/{document_id}/file")
def document_file(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    row = db.get(JobDocument, document_id)
    if not row:
        raise HTTPException(404, "Datei nicht gefunden.")
    job = db.get(ScanJob, row.scan_job_id)
    if not job or job.owner_id != user.id or not Path(row.path).exists():
        raise HTTPException(404, "Datei nicht gefunden.")
    return FileResponse(row.path, filename=row.final_name)


@app.get("/api/system")
def system_status(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return {
        "version": __version__, "data_root": str(DATA_ROOT),
        "input_root": str(DATA_ROOT / "Eingang"),
        "processing_root": str(DATA_ROOT / "Verarbeitung"),
        "output_root": str(DATA_ROOT / "Ausgang"),
        "archive_root": str(DATA_ROOT / "Archiv"),
        "profiles": db.query(ProcessingProfile).filter(ProcessingProfile.owner_id == user.id).count(),
        "destinations": db.query(Destination).filter(Destination.owner_id == user.id).count(),
        "inputs": db.query(ScanInput).filter(ScanInput.owner_id == user.id).count(),
        "jobs": db.query(ScanJob).filter(ScanJob.owner_id == user.id).count(),
    }
