"""Auto-crop and interrupted job safety tests."""
from pathlib import Path
from types import SimpleNamespace
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw
from scanpro.services import processor
from scanpro.inbox_worker import mark_interrupted_jobs
from scanpro.db import Base
from scanpro.models import ScanJob
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_auto_crop_reduces_large_blank_margins(monkeypatch, tmp_path):
    pdf = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with pdf.open("wb") as fp:
        writer.write(fp)

    def render(args, **kwargs):
        img = Image.new("L", (595, 842), 255)
        ImageDraw.Draw(img).rectangle((90, 80, 510, 750), fill=50)
        img.save(args[-1] + "-1.png")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(processor.subprocess, "run", render)
    result = processor.auto_crop_pdf(pdf)
    cropped = PdfReader(str(result)).pages[0].cropbox
    assert float(cropped.width) < 595
    assert float(cropped.height) < 842


def test_interrupted_jobs_preserve_history():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(ScanJob(id=1, input_id=1, profile_id=1, destination_id=1,
                       source_path="/tmp/input.pdf", status="processing"))
        db.commit()
        mark_interrupted_jobs(db)
        assert db.get(ScanJob, 1).status == "interrupted"
