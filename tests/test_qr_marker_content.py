"""QR separator value matching regression tests."""
from types import SimpleNamespace
import numpy as np
from PIL import Image
from scanpro.services import processor


def test_qr_marker_requires_exact_content(monkeypatch, tmp_path):
    png = tmp_path / "qr.png"
    Image.new("RGB", (20, 20), "white").save(png)
    class Reader:
        def read_barcodes(self, image):
            return [SimpleNamespace(format="QRCode", text="SCANPRO-TRENNSEITE")]
    import sys
    monkeypatch.setitem(sys.modules, "zxingcpp", Reader())
    assert processor._coded_marker(png, "qr", "SCANPRO-TRENNSEITE")
    assert not processor._coded_marker(png, "qr", "anderer-inhalt")
    assert processor._coded_marker(png, "qr", "")
    assert not processor._coded_marker(png, "barcode", "")
