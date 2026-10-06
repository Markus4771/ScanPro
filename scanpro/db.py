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


SCAN_JOBS_COLUMNS = {
    "id",
    "input_id",
    "profile_id",
    "destination_id",
    "status",
    "source_path",
    "working_path",
    "error",
    "created_at",
    "completed_at",
}


def _repair_legacy_scan_jobs(connection: sqlite3.Connection) -> None:
    table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scan_jobs'"
    ).fetchone()
    if not table:
        return

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(scan_jobs)").fetchall()
    }
    if SCAN_JOBS_COLUMNS.issubset(columns):
        return

    count = connection.execute("SELECT COUNT(*) FROM scan_jobs").fetchone()[0]
    if count:
        raise RuntimeError(
            "Alte scan_jobs-Tabelle erkannt. Sie enthält bereits "
            f"{count} Job(s) und wird aus Sicherheitsgründen nicht automatisch ersetzt."
        )

    # Frühere 1.0-dev Builds hatten hier noch workflow_id/input_path/output_path.
    # Ist die Tabelle leer, kann SQLAlchemy sie anschließend korrekt neu anlegen.
    connection.execute("DROP TABLE scan_jobs")


def initialize_database():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if DATABASE_URL.startswith("sqlite:///"):
        path = Path(DATABASE_URL.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=30)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            # Vor dem Aktivieren der Foreign Keys eine leere Legacy-Tabelle reparieren.
            _repair_legacy_scan_jobs(connection)
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
