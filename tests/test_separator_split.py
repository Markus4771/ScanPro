from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from scanpro.services.processor import split_marker_pdf


def test_separator_groups(tmp_path):
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=595, height=842)
    with source.open("wb") as stream:
        writer.write(stream)

    def render(args, **kwargs):
        prefix = Path(args[-1])
        for i in range(1, 6):
            (prefix.parent / f"page-{i}.png").write_bytes(b"fixture")
        return SimpleNamespace(returncode=0, stderr="")

    for method in ("blank-page", "qr", "barcode"):
        profile = SimpleNamespace(split_method=method, blank_threshold=99)
        detector = "_blank_marker" if method == "blank-page" else "_coded_marker"
        def marked(path, *args):
            return path.stem.endswith("-3")
        with patch("scanpro.services.processor.subprocess.run", side_effect=render):
            with patch("scanpro.services.processor." + detector, side_effect=marked):
                outputs = split_marker_pdf(source, profile)
        assert [len(PdfReader(str(path)).pages) for path in outputs] == [2, 2]
