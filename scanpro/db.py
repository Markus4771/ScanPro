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
    "id", "input_id", "profile_id", "destination_id", "status",
    "source_path", "working_path", "error", "created_at", "completed_at",
}


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _repair_legacy_scan_jobs(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "scan_jobs"):
        return
    columns = _columns(connection, "scan_jobs")
    if SCAN_JOBS_COLUMNS.issubset(columns):
        return
    count = connection.execute("SELECT COUNT(*) FROM scan_jobs").fetchone()[0]
    if count:
        raise RuntimeError(
            "Alte scan_jobs-Tabelle erkannt. Sie enthält bereits "
            f"{count} Job(s) und wird aus Sicherheitsgründen nicht automatisch ersetzt."
        )
    connection.execute("DROP TABLE scan_jobs")


def _add_owner_columns(connection: sqlite3.Connection) -> None:
    for table in ("processing_profiles", "destinations", "scan_inputs", "scan_jobs"):
        if _table_exists(connection, table) and "owner_id" not in _columns(connection, table):
            connection.execute(f"ALTER TABLE {table} ADD COLUMN owner_id INTEGER")


def _add_share_credentials(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "scan_inputs"):
        return
    columns = _columns(connection, "scan_inputs")
    if "smb_username" not in columns:
        connection.execute("ALTER TABLE scan_inputs ADD COLUMN smb_username VARCHAR(80)")
    if "smb_password" not in columns:
        connection.execute("ALTER TABLE scan_inputs ADD COLUMN smb_password TEXT")


def _add_profile_processing_columns(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "processing_profiles"):
        return
    columns = _columns(connection, "processing_profiles")
    additions = {
        "pdfa_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "color_mode": "VARCHAR(20) NOT NULL DEFAULT 'keep'",
        "dpi": "INTEGER NOT NULL DEFAULT 300",
        "normalize_a4": "BOOLEAN NOT NULL DEFAULT 0",
        "blank_threshold": "INTEGER NOT NULL DEFAULT 99",
        "subfolder_template": "VARCHAR(255) NOT NULL DEFAULT ''",
    }
    for name, definition in additions.items():
        if name not in columns:
            connection.execute(
                f"ALTER TABLE processing_profiles ADD COLUMN {name} {definition}"
            )


def initialize_database():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if DATABASE_URL.startswith("sqlite:///"):
        path = Path(DATABASE_URL.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=30)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            _repair_legacy_scan_jobs(connection)
            _add_owner_columns(connection)
            _add_share_credentials(connection)
            _add_profile_processing_columns(connection)
            connection.execute("PRAGMA foreign_keys=ON")
            connection.commit()
        finally:
            connection.close()


def claim_unowned_rows(user_id: int) -> None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return
    path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    connection = sqlite3.connect(path, timeout=30)
    try:
        for table in ("processing_profiles", "destinations", "scan_inputs", "scan_jobs"):
            if _table_exists(connection, table) and "owner_id" in _columns(connection, table):
                connection.execute(
                    f"UPDATE {table} SET owner_id=? WHERE owner_id IS NULL", (user_id,)
                )
        connection.commit()
    finally:
        connection.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
