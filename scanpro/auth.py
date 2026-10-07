import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, UserSession

PBKDF2_ROUNDS = 310_000


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Passwort muss mindestens 10 Zeichen lang sein.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return "pbkdf2_sha256$%s$%s$%s" % (PBKDF2_ROUNDS, salt.hex(), digest.hex())


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def new_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.add(UserSession(user_id=user.id, token_hash=token_hash))
    db.commit()
    return token


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("scanpro_session")
    if not token:
        raise HTTPException(401, "Anmeldung erforderlich.")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
    if not session:
        raise HTTPException(401, "Sitzung ungültig.")
    user = db.get(User, session.user_id)
    if not user or not user.enabled:
        raise HTTPException(401, "Benutzer ist deaktiviert.")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Administratorrechte erforderlich.")
    return user
