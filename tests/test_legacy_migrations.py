"""Regression tests for databases created by older ScanPro versions."""
import sqlite3

from scanpro import db


def test_legacy_job_tables_are_migrated_without_data_loss(tmp_path, monkeypatch):
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as con:
        con.executescript("""
            CREATE TABLE job_documents (
                id INTEGER PRIMARY KEY,
                scan_job_id INTEGER NOT NULL,
                sequence INTEGER NOT NULL,
                path TEXT NOT NULL,
                split_method VARCHAR(30) NOT NULL,
                created_at DATETIME NOT NULL
            );
            CREATE TABLE job_deliveries (
                id INTEGER PRIMARY KEY,
                scan_job_id INTEGER NOT NULL,
                destination_id INTEGER NOT NULL,
                status VARCHAR(30) NOT NULL
            );
            INSERT INTO job_documents VALUES
                (1, 12, 1, '/tmp/out/example.pdf', 'none', '2026-10-09');
            INSERT INTO job_deliveries VALUES (1, 12, 1, 'delivered');
        """)
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(db, "DATABASE_URL", f"sqlite:///{database}")
    db.initialize_database()
    db.initialize_database()  # idempotent across service restarts
    with sqlite3.connect(database) as con:
        columns_docs = db._columns(con, "job_documents")
        columns_delivery = db._columns(con, "job_deliveries")
        assert {"final_name", "split_method", "created_at"} <= columns_docs
        assert {"target", "error", "created_at"} <= columns_delivery
        assert con.execute(
            "SELECT id, scan_job_id, final_name FROM job_documents"
        ).fetchall() == [(1, 12, "example.pdf")]
        assert con.execute(
            "SELECT id, scan_job_id, status FROM job_deliveries"
        ).fetchall() == [(1, 12, "delivered")]
