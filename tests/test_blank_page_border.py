"""Regression: a thin dark scanner border must not make a blank page nonblank."""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw
from pypdf import PdfWriter, PdfReader

from scanpro.services import processor


def test_remove_blank_page_with_dark_scanner_border(monkeypatch, tmp_path):
    source = tmp_path / "scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    writer.add_blank_page(width=595, height=842)
    with source.open("wb") as f:
        writer.write(f)

    def fake_render(cmd, **kwargs):
        prefix = Path(cmd[-1])
        blank = Image.new("L", (413, 585), 255)
        ImageDraw.Draw(blank).rectangle((0, 0, 412, 584), outline=0, width=4)
        blank.save(str(prefix) + "-1.png")
        content = Image.new("L", (413, 585), 255)
        ImageDraw.Draw(content).rectangle((35, 30, 350, 520), fill=80)
        content.save(str(prefix) + "-2.png")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(processor.subprocess, "run", fake_render)
    result = processor.remove_blank_pdf_pages(source, 99)
    assert result != source
    assert len(PdfReader(str(result)).pages) == 1
