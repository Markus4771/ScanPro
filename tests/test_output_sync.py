"""Output sync regression coverage."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scanpro.db import Base
from scanpro.models import JobDocument, ScanJob
from scanpro.services import output_sync


def test_output_sync_marks_deleted_and_restored_without_changing_job(tmp_path, monkeypatch):
    monkeypatch.setattr(output_sync, "DATA_ROOT", tmp_path)
    outgoing = tmp_path / "Ausgang" / "PDF"
    outgoing.mkdir(parents=True)
    pdf = outgoing / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(ScanJob(id=1, input_id=1, profile_id=1, destination_id=1,
                       source_path="/tmp/test.pdf", status="delivered"))
        db.add(JobDocument(scan_job_id=1, sequence=1, path=str(pdf),
                           final_name=pdf.name, split_method="none"))
        db.commit()
        assert output_sync.sync_output_files(db)["missing"] == 0
        pdf.unlink()
        assert output_sync.sync_output_files(db)["missing"] == 1
        assert db.query(JobDocument).first().file_present is False
        assert db.query(ScanJob).first().status == "delivered"
        pdf.write_bytes(b"%PDF-1.4")
        assert output_sync.sync_output_files(db)["restored"] == 1
        assert db.query(JobDocument).first().file_present is True


def test_output_sync_skips_active_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(output_sync, "DATA_ROOT", tmp_path)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(ScanJob(id=2, input_id=1, profile_id=1, destination_id=1,
                       source_path="/tmp/test.pdf", status="processing"))
        db.add(JobDocument(scan_job_id=2, sequence=1,
                           path=str(tmp_path / "Ausgang" / "missing.pdf"),
                           final_name="missing.pdf", split_method="none"))
        db.commit()
        assert output_sync.sync_output_files(db)["checked"] == 0
        assert db.query(JobDocument).first().file_present is True
