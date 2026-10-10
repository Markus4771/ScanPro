"""Regression checks for orientation handling with existing OCR text layers."""
from pathlib import Path
from types import SimpleNamespace

from scanpro.services import processor


def test_auto_rotate_reprocesses_existing_text_layer(monkeypatch, tmp_path):
    source = tmp_path / "upside-down.pdf"
    source.write_bytes(b"test")
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b"fixed")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(processor.subprocess, "run", fake_run)
    profile = SimpleNamespace(ocr_language="deu", auto_rotate=True,
                              deskew=False, pdfa_enabled=False)
    result = processor.ocr_pdf(source, profile)
    assert result.exists()
    assert "--force-ocr" in commands[0]
    assert "--skip-text" not in commands[0]
    assert "--rotate-pages" in commands[0]
    assert commands[0][commands[0].index("--rotate-pages-threshold") + 1] == "2.0"


def test_ocr_without_rotation_keeps_existing_text(monkeypatch, tmp_path):
    source = tmp_path / "already-text.pdf"
    source.write_bytes(b"test")
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b"fixed")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(processor.subprocess, "run", fake_run)
    profile = SimpleNamespace(ocr_language="deu", auto_rotate=False,
                              deskew=False, pdfa_enabled=False)
    processor.ocr_pdf(source, profile)
    assert "--skip-text" in commands[0]
    assert "--force-ocr" not in commands[0]


def test_rotation_with_deskew_uses_compatible_flags(monkeypatch, tmp_path):
    source = tmp_path / "crooked.pdf"
    source.write_bytes(b"test")
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b"fixed")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(processor.subprocess, "run", fake_run)
    profile = SimpleNamespace(ocr_language="deu", auto_rotate=True,
                              deskew=True, pdfa_enabled=False)
    processor.ocr_pdf(source, profile)
    assert "--force-ocr" in commands[0]
    assert "--deskew" in commands[0]
    assert "--redo-ocr" not in commands[0]
