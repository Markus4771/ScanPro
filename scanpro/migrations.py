from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import Engine, text


CURRENT_SCHEMA_VERSION = 8


@dataclass(frozen=True)
class Migration:
    version: int
    description: str
    statements: tuple[str, ...] = ()


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        description="Baseline for ScanPro 0.5.2-dev persistent database",
        statements=(),
    ),
    Migration(
        version=2,
        description="Paperless profile metadata rules",
        statements=(),
    ),
    Migration(
        version=3,
        description="Photo profile output settings",
        statements=(),
    ),
    Migration(
        version=4,
        description="VPN and remote scanner connection settings",
        statements=(),
    ),
    Migration(
        version=5,
        description="Static remote scanner targets",
        statements=(),
    ),
    Migration(
        version=6,
        description="Encrypted destination secret store",
        statements=(),
    ),
    Migration(
        version=7,
        description="Scanner menu profile assignments",
        statements=(),
    ),
    Migration(
        version=8,
        description="Scanner menu destinations",
        statements=(),
    ),
)


def _ensure_version_table(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        row = connection.execute(
            text("SELECT version FROM schema_version WHERE id = 1")
        ).scalar_one_or_none()
        if row is None:
            connection.execute(
                text(
                    "INSERT INTO schema_version (id, version) VALUES (1, 0)"
                )
            )


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    with engine.begin() as connection:
        rows = connection.execute(text(f"PRAGMA table_info({table})")).mappings().all()
        return any(row["name"] == column for row in rows)


def get_schema_version(engine: Engine) -> int:
    _ensure_version_table(engine)
    with engine.begin() as connection:
        return int(
            connection.execute(
                text("SELECT version FROM schema_version WHERE id = 1")
            ).scalar_one()
        )


def run_schema_migrations(engine: Engine) -> int:
    _ensure_version_table(engine)
    current = get_schema_version(engine)

    # Schema 8 repair is intentionally idempotent. SQLAlchemy create_all()
    # does not add columns to existing SQLite tables, while fresh databases
    # may already contain the column from the current model definition.
    if not _column_exists(engine, "scanner_menu_entries", "destination_id"):
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE scanner_menu_entries "
                "ADD COLUMN destination_id INTEGER REFERENCES destinations(id)"
            ))

    for migration in MIGRATIONS:
        if migration.version <= current:
            continue

        with engine.begin() as connection:
            for statement in migration.statements:
                connection.execute(text(statement))
            connection.execute(
                text(
                    """
                    UPDATE schema_version
                    SET version = :version, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """
                ),
                {"version": migration.version},
            )
        current = migration.version

    return current
