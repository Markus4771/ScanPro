import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import cv2
import img2pdf
import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from ..db import DATA_ROOT
from ..models import Destination, JobDelivery, JobDocument, ProcessingProfile, ScanInput, ScanJob
from .delivery import DeliveryError, deliver


class ProcessingError(RuntimeError):
    pass


TRIANGLE_RENDER_DPI = 120


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value[:160] or "scan"


def template_value(
    template: str,
    profile: ProcessingProfile,
    scan_input: ScanInput,
    job: ScanJob,
    document_sequence: int = 1,
) -> str:
    now = datetime.now()
    value = template or ""
    for key, replacement in {
        "{date}": now.strftime("%Y-%m-%d"),
        "{year}": now.strftime("%Y"),
        "{month}": now.strftime("%m"),
        "{day}": now.strftime("%d"),
        "{time}": now.strftime("%H-%M-%S"),
        "{datetime}": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "{input}": scan_input.name,
        "{profile}": profile.name,
        "{job}": str(job.id),
        "{document}": f"{document_sequence:03d}",
    }.items():
        value = value.replace(key, replacement)
    return value


def final_name(
    profile: ProcessingProfile,
    scan_input: ScanInput,
    job: ScanJob,
    source: Path,
    document_sequence: int = 1,
) -> str:
    stem = template_value(
        profile.filename_template, profile, scan_input, job, document_sequence
    )
    return safe_name(stem) + (source.suffix.lower() or ".pdf")


def subfolder_parts(
    profile: ProcessingProfile,
    scan_input: ScanInput,
    job: ScanJob,
    document_sequence: int = 1,
) -> list[str]:
    raw = template_value(
        profile.subfolder_template, profile, scan_input, job, document_sequence
    ).strip()
    if not raw:
        return []
    raw = raw.replace("\\", "/")
    return [
        safe_name(part)
        for part in raw.split("/")
        if part.strip() not in {"", ".", ".."}
    ]


def _triangle_roi(image: np.ndarray, position: str) -> tuple[np.ndarray, int, int]:
    height, width = image.shape[:2]
    position = (position or "any").lower()
    if position == "top_left":
        return image[: height // 2, : width // 2], 0, 0
    if position == "top_right":
        return image[: height // 2, width // 2 :], width // 2, 0
    if position == "bottom_left":
        return image[height // 2 :, : width // 2], 0, height // 2
    if position == "bottom_right":
        return image[height // 2 :, width // 2 :], width // 2, height // 2
    return image, 0, 0


def image_has_triangle(image_path: Path, position: str, min_size_mm: int) -> bool:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return False

    roi, _, _ = _triangle_roi(image, position)
    if roi.size == 0:
        return False

    blurred = cv2.GaussianBlur(roi, (5, 5), 0)
    threshold = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        9,
    )
    kernel = np.ones((3, 3), np.uint8)
    threshold = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(
        threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )

    min_px = max(12, int((max(5, min_size_mm) / 25.4) * TRIANGLE_RENDER_DPI))
    min_area = max(80.0, min_px * min_px * 0.10)
    max_area = roi.shape[0] * roi.shape[1] * 0.30

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        approx = cv2.approxPolyDP(contour, 0.06 * perimeter, True)
        if len(approx) != 3:
            continue

        x, y, width, height = cv2.boundingRect(approx)
        if max(width, height) < min_px:
            continue

        hull = cv2.convexHull(approx)
        hull_area = cv2.contourArea(hull)
        if hull_area <= 0:
            continue
        solidity = area / hull_area
        if solidity < 0.60:
            continue

        return True

    return False


def split_triangle_pdf(source: Path, profile: ProcessingProfile) -> list[Path]:
    reader = PdfReader(str(source))
    if len(reader.pages) <= 1:
        return [source]

    marker_pages: set[int] = set()
    with tempfile.TemporaryDirectory(prefix="scanpro-triangle-") as tmp:
        prefix = Path(tmp) / "page"
        result = subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-gray",
                "-r",
                str(TRIANGLE_RENDER_DPI),
                str(source),
                str(prefix),
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise ProcessingError(
                result.stderr.strip() or "Dreieck-Erkennung konnte Seiten nicht rendern."
            )

        images = sorted(Path(tmp).glob("page-*.png"))
        if len(images) != len(reader.pages):
            raise ProcessingError("Dreieck-Erkennung konnte nicht alle PDF-Seiten analysieren.")

        for index, image_path in enumerate(images):
            if image_has_triangle(
                image_path,
                profile.triangle_position,
                profile.triangle_min_size_mm,
            ):
                marker_pages.add(index)

    if not marker_pages:
        return [source]

    groups: list[list[int]] = []
    current: list[int] = []

    for index in range(len(reader.pages)):
        is_marker = index in marker_pages
        if is_marker:
            if current:
                groups.append(current)
                current = []
            if not profile.triangle_remove_page:
                current.append(index)
            continue
        current.append(index)

    if current:
        groups.append(current)

    if not groups:
        raise ProcessingError(
            "Alle Seiten wurden als Dreieck-Trennseiten erkannt. "
            "Bitte Position oder Mindestgröße im Profil anpassen."
        )

    outputs: list[Path] = []
    for sequence, page_indexes in enumerate(groups, start=1):
        target = source.with_name(f"{source.stem}-split-{sequence:03d}.pdf")
        writer = PdfWriter()
        for page_index in page_indexes:
            writer.add_page(reader.pages[page_index])
        with target.open("wb") as handle:
            writer.write(handle)
        outputs.append(target)

    return outputs



def _blank_marker(image_path: Path, threshold: int) -> bool:
    """Classify a separator page using the same white-pixel metric as blank removal."""
    with Image.open(image_path) as image:
        gray = image.convert("L")
        histogram = gray.histogram()
        total = max(1, gray.width * gray.height)
        white_ratio = sum(histogram[245:]) / total
    return white_ratio >= max(90, min(100, int(threshold or 99))) / 100.0


def _coded_marker(image_path: Path, method: str) -> bool:
    """Detect QR or linear/matrix barcodes; recognition is restricted by profile method."""
    import zxingcpp

    with Image.open(image_path) as image:
        rgb = np.asarray(image.convert("RGB"))
    try:
        results = zxingcpp.read_barcodes(rgb)
    except Exception as exc:
        raise ProcessingError(f"Barcode-Erkennung fehlgeschlagen: {exc}") from exc
    for result in results:
        fmt = str(result.format).lower()
        is_qr = "qr" in fmt
        if method == "qr" and is_qr:
            return True
        if method == "barcode" and not is_qr:
            return True
    return False


def split_marker_pdf(source: Path, profile: ProcessingProfile) -> list[Path]:
    """Split scanned PDFs at blank / QR / barcode marker pages.

    Marker pages are removed; an initial or repeated marker doesn't create an
    empty output. The original is returned unchanged if no markers were found.
    """
    method = profile.split_method
    if method not in {"blank-page", "qr", "barcode"}:
        raise ProcessingError(f"Unbekanntes Trennverfahren: {method}")
    reader = PdfReader(str(source))
    if len(reader.pages) <= 1:
        return [source]

    with tempfile.TemporaryDirectory(prefix="scanpro-marker-") as tmp:
        prefix = Path(tmp) / "page"
        dpi = 80 if method == "blank-page" else 200
        result = subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), str(source), str(prefix)],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode:
            raise ProcessingError(result.stderr.strip() or "Trennseiten konnten nicht gerendert werden.")
        images = sorted(Path(tmp).glob("page-*.png"))
        if len(images) != len(reader.pages):
            raise ProcessingError("Trennseitenanalyse ist unvollständig.")
        markers = set()
        for index, image_path in enumerate(images):
            found = (
                _blank_marker(image_path, profile.blank_threshold)
                if method == "blank-page"
                else _coded_marker(image_path, method)
            )
            if found:
                markers.add(index)

    if not markers:
        return [source]
    groups = []
    current = []
    for index in range(len(reader.pages)):
        if index in markers:
            if current:
                groups.append(current)
                current = []
        else:
            current.append(index)
    if current:
        groups.append(current)
    if not groups:
        raise ProcessingError("Alle Seiten wurden als Trennseiten erkannt.")
    outputs = []
    for sequence, indexes in enumerate(groups, start=1):
        target = source.with_name(f"{source.stem}-split-{sequence:03d}.pdf")
        writer = PdfWriter()
        for index in indexes:
            writer.add_page(reader.pages[index])
        with target.open("wb") as handle:
            writer.write(handle)
        outputs.append(target)
    return outputs


def remove_blank_pdf_pages(source: Path, threshold: int) -> Path:
    threshold = max(90, min(100, int(threshold or 99)))
    target = source.with_name(source.stem + "-noblank.pdf")
    with tempfile.TemporaryDirectory(prefix="scanpro-blank-") as tmp:
        prefix = Path(tmp) / "page"
        result = subprocess.run(
            ["pdftoppm", "-png", "-gray", "-r", "50", str(source), str(prefix)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise ProcessingError(
                result.stderr.strip() or "Leerseitenanalyse fehlgeschlagen."
            )

        images = sorted(Path(tmp).glob("page-*.png"))
        reader = PdfReader(str(source))
        if not images or len(images) != len(reader.pages):
            return source

        keep: list[int] = []
        cutoff = threshold / 100.0
        for index, image_path in enumerate(images):
            with Image.open(image_path).convert("L") as image:
                histogram = image.histogram()
                pixels = max(1, image.width * image.height)
                white_pixels = sum(histogram[245:])
                white_ratio = white_pixels / pixels
            if white_ratio < cutoff:
                keep.append(index)

        if not keep or len(keep) == len(reader.pages):
            return source

        writer = PdfWriter()
        for index in keep:
            writer.add_page(reader.pages[index])
        with target.open("wb") as handle:
            writer.write(handle)
    return target


def raster_normalize_pdf(source: Path, profile: ProcessingProfile) -> Path:
    if source.suffix.lower() != ".pdf":
        return source
    color_mode = (profile.color_mode or "keep").lower()
    selected_dpi = int(profile.dpi or 0)
    needs_raster = (
        color_mode in {"gray", "bw"}
        or bool(profile.normalize_a4)
        or selected_dpi > 0
    )
    if not needs_raster:
        return source

    dpi = max(72, min(600, selected_dpi or 300))
    target = source.with_name(source.stem + "-normalized.pdf")
    with tempfile.TemporaryDirectory(prefix="scanpro-normalize-") as tmp:
        prefix = Path(tmp) / "page"
        cmd = ["pdftoppm", "-png", "-r", str(dpi)]
        if color_mode == "gray":
            cmd.append("-gray")
        elif color_mode == "bw":
            cmd.append("-mono")
        if profile.normalize_a4:
            width = round(8.2677 * dpi)
            height = round(11.6929 * dpi)
            cmd += ["-scale-to-x", str(width), "-scale-to-y", str(height)]
        cmd += [str(source), str(prefix)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise ProcessingError(
                result.stderr.strip() or "PDF-Normalisierung fehlgeschlagen."
            )

        images = sorted(Path(tmp).glob("page-*.png"))
        if not images:
            return source

        if profile.normalize_a4:
            layout_fun = img2pdf.get_layout_fun(
                (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
            )
            pdf_bytes = img2pdf.convert(
                [str(path) for path in images], layout_fun=layout_fun
            )
        else:
            pdf_bytes = img2pdf.convert([str(path) for path in images])
        target.write_bytes(pdf_bytes)
    return target


def ocr_pdf(source: Path, profile: ProcessingProfile) -> Path:
    target = source.with_name(source.stem + "-ocr.pdf")
    command = [
        "ocrmypdf",
        "--skip-text",
        "--optimize",
        "1",
        "--language",
        profile.ocr_language,
    ]
    if profile.auto_rotate:
        command.append("--rotate-pages")
    if profile.deskew:
        command.append("--deskew")
    if profile.pdfa_enabled:
        command += ["--output-type", "pdfa"]
    else:
        command += ["--output-type", "pdf"]
    command += [str(source), str(target)]

    result = subprocess.run(
        command, capture_output=True, text=True, timeout=900
    )
    if result.returncode not in {0, 6}:
        raise ProcessingError(
            result.stderr.strip() or result.stdout.strip() or "OCR fehlgeschlagen."
        )
    return target if target.exists() else source


def prepare_document(source: Path, profile: ProcessingProfile) -> Path:
    output = source
    if output.suffix.lower() == ".pdf":
        if profile.remove_blank_pages:
            output = remove_blank_pdf_pages(output, profile.blank_threshold)
        output = raster_normalize_pdf(output, profile)
        if profile.ocr_enabled:
            output = ocr_pdf(output, profile)
    return output


def process_job(db: Session, job: ScanJob) -> None:
    scan_input = db.get(ScanInput, job.input_id)
    profile = db.get(ProcessingProfile, job.profile_id)
    destination = db.get(Destination, job.destination_id)
    if not scan_input or not profile or not destination:
        raise ProcessingError("Eingang, Profil oder Ziel fehlt.")

    source = Path(job.source_path)
    work_dir = DATA_ROOT / "Verarbeitung" / "jobs" / str(job.id)
    work_dir.mkdir(parents=True, exist_ok=True)
    work = work_dir / source.name
    shutil.move(str(source), work)
    job.working_path = str(work)
    job.status = "processing"
    db.commit()

    documents = [work]
    if work.suffix.lower() == ".pdf":
        if profile.split_method == "triangle":
            documents = split_triangle_pdf(work, profile)
        elif profile.split_method in {"blank-page", "qr", "barcode"}:
            documents = split_marker_pdf(work, profile)

    delivery_errors: list[str] = []

    for sequence, document in enumerate(documents, start=1):
        output = prepare_document(document, profile)
        name = final_name(profile, scan_input, job, output, sequence)

        folder_parts = subfolder_parts(profile, scan_input, job, sequence)
        output_dir = DATA_ROOT / "Ausgang" / safe_name(destination.name)
        for part in folder_parts:
            output_dir /= part
        output_dir.mkdir(parents=True, exist_ok=True)

        internal_output = output_dir / name
        shutil.copy2(output, internal_output)

        db.add(
            JobDocument(
                scan_job_id=job.id,
                sequence=sequence,
                path=str(internal_output),
                final_name=name,
                split_method=profile.split_method or "none",
            )
        )
        db.commit()

        delivery = JobDelivery(
            scan_job_id=job.id,
            destination_id=destination.id,
            status="delivering",
        )
        db.add(delivery)
        db.commit()

        try:
            relative_name = "/".join(folder_parts + [name])
            delivery.target = deliver(
                destination, internal_output, name, relative_name
            )
            delivery.status = "delivered"
        except DeliveryError as exc:
            delivery.status = "error"
            delivery.error = str(exc)
            delivery_errors.append(f"Dokument {sequence:03d}: {exc}")
        db.commit()

    if delivery_errors:
        job.status = "delivery_error"
        job.error = " | ".join(delivery_errors)
    else:
        job.status = "delivered"
        job.error = None

    job.completed_at = datetime.utcnow()
    db.commit()
