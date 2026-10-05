from enum import StrEnum
import os
import subprocess
from pathlib import Path

import fitz


class SplitMethod(StrEnum):
    NONE = "none"
    PATCH_T = "patch-t"
    QR = "qr"
    BARCODE = "barcode"
    BLANK_PAGE = "blank-page"
    MANUAL = "manual"


class SeparationError(RuntimeError):
    pass


def validate_split(enabled: bool, method: str) -> None:
    if not enabled:
        return
    try:
        parsed = SplitMethod(method)
    except ValueError as exc:
        raise ValueError(f"Unbekannte Trennmethode: {method}") from exc
    if parsed is SplitMethod.NONE:
        raise ValueError("Bei aktivierter Trennung muss eine Trennmethode gewählt werden.")


def _is_blank(page: fitz.Page, white_ratio_threshold: float = 0.995, dark_threshold: int = 245) -> bool:
    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), colorspace=fitz.csGRAY, alpha=False)
    samples = pix.samples
    if not samples:
        return False
    white = sum(1 for value in samples if value >= dark_threshold)
    return (white / len(samples)) >= white_ratio_threshold


def split_by_blank_pages(pdf_path: str, output_dir: str) -> list[str]:
    source = Path(pdf_path)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)

    groups: list[list[int]] = []
    current: list[int] = []
    for index, page in enumerate(doc):
        if _is_blank(page):
            if current:
                groups.append(current)
                current = []
            continue
        current.append(index)
    if current:
        groups.append(current)

    if not groups:
        doc.close()
        raise SeparationError("Keine Dokumentseiten gefunden; alle Seiten wurden als leer erkannt.")

    outputs: list[str] = []
    for number, pages in enumerate(groups, start=1):
        out = fitz.open()
        for page_index in pages:
            out.insert_pdf(doc, from_page=page_index, to_page=page_index)
        path = target_dir / f"document-{number:03d}.pdf"
        out.save(path, garbage=4, deflate=True)
        out.close()
        outputs.append(str(path))
    doc.close()
    return outputs


def split_by_patch_t(pdf_path: str, output_dir: str) -> list[str]:
    source = Path(pdf_path)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    pattern = target_dir / "document-$(nnn).pdf"

    env = os.environ.copy()
    env["HOME"] = "/var/lib/scanpro"
    env["XDG_CONFIG_HOME"] = "/var/lib/scanpro/.config"
    env["XDG_CACHE_HOME"] = "/var/lib/scanpro/.cache"

    command = [
        "naps2", "console",
        "-i", str(source),
        "-n", "0",
        "-o", str(pattern),
        "--splitpatcht",
        "-f",
        "-v",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
            cwd="/var/lib/scanpro",
            env=env,
        )
    except FileNotFoundError as exc:
        raise SeparationError("NAPS2 wurde für Patch-T nicht gefunden.") from exc
    except subprocess.TimeoutExpired as exc:
        raise SeparationError("Patch-T-Verarbeitung hat das Zeitlimit überschritten.") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SeparationError(detail or "Patch-T-Verarbeitung ist fehlgeschlagen.")

    outputs = sorted(str(path) for path in target_dir.glob("document-*.pdf"))
    if not outputs:
        raise SeparationError("Patch-T-Verarbeitung hat keine Dokumente erzeugt.")
    return outputs


def split_pdf(pdf_path: str, method: str, output_dir: str) -> list[str]:
    if method == SplitMethod.BLANK_PAGE:
        return split_by_blank_pages(pdf_path, output_dir)
    if method == SplitMethod.PATCH_T:
        return split_by_patch_t(pdf_path, output_dir)
    raise SeparationError(f"Trennmethode ist noch nicht implementiert: {method}")
