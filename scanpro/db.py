import os
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATA_ROOT = Path(os.getenv("SCANPRO_DATA_ROOT", "/var/lib/scanpro-v1"))
DEFAULT_DB_PATH = DATA_ROOT / "scanpro-v1.db"
DATABASE_URL = os.getenv("SCANPRO_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, connection_record):
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def initialize_database():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if DATABASE_URL.startswith("sqlite:///"):
        path = Path(DATABASE_URL.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=30)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.commit()
        finally:
            connection.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
