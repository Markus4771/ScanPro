from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import Engine, text


CURRENT_SCHEMA_VERSION = 4


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
