import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import img2pdf
from PIL import Image
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from ..db import DATA_ROOT
from ..models import Destination, JobDelivery, JobDocument, ProcessingProfile, ScanInput, ScanJob
from .delivery import DeliveryError, deliver


class ProcessingError(RuntimeError):
    pass


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value[:160] or "scan"


def template_value(template: str, profile: ProcessingProfile, scan_input: ScanInput, job: ScanJob) -> str:
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
        "{document}": "001",
    }.items():
        value = value.replace(key, replacement)
    return value


def final_name(profile: ProcessingProfile, scan_input: ScanInput, job: ScanJob, source: Path) -> str:
    stem = template_value(profile.filename_template, profile, scan_input, job)
    return safe_name(stem) + (source.suffix.lower() or ".pdf")


def subfolder_parts(profile: ProcessingProfile, scan_input: ScanInput, job: ScanJob) -> list[str]:
    raw = template_value(profile.subfolder_template, profile, scan_input, job).strip()
    if not raw:
        return []
    raw = raw.replace("\\", "/")
    return [safe_name(part) for part in raw.split("/") if part.strip() not in {"", ".", ".."}]


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
            raise ProcessingError(result.stderr.strip() or "Leerseitenanalyse fehlgeschlagen.")

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
    needs_raster = color_mode in {"gray", "bw"} or bool(profile.normalize_a4) or selected_dpi > 0
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
            raise ProcessingError(result.stderr.strip() or "PDF-Normalisierung fehlgeschlagen.")

        images = sorted(Path(tmp).glob("page-*.png"))
        if not images:
            return source

        if profile.normalize_a4:
            layout_fun = img2pdf.get_layout_fun((img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297)))
            pdf_bytes = img2pdf.convert([str(p) for p in images], layout_fun=layout_fun)
        else:
            pdf_bytes = img2pdf.convert([str(p) for p in images])
        target.write_bytes(pdf_bytes)
    return target


def ocr_pdf(source: Path, profile: ProcessingProfile) -> Path:
    target = source.with_name(source.stem + "-ocr.pdf")
    command = [
        "ocrmypdf",
        "--skip-text",
        "--optimize", "1",
        "--language", profile.ocr_language,
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

    result = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if result.returncode not in {0, 6}:
        raise ProcessingError(result.stderr.strip() or result.stdout.strip() or "OCR fehlgeschlagen.")
    return target if target.exists() else source


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

    output = work
    if output.suffix.lower() == ".pdf":
        if profile.remove_blank_pages:
            output = remove_blank_pdf_pages(output, profile.blank_threshold)
        output = raster_normalize_pdf(output, profile)
        if profile.ocr_enabled:
            output = ocr_pdf(output, profile)

    name = final_name(profile, scan_input, job, output)

    folder_parts = subfolder_parts(profile, scan_input, job)
    output_dir = DATA_ROOT / "Ausgang" / safe_name(destination.name)
    for part in folder_parts:
        output_dir /= part
    output_dir.mkdir(parents=True, exist_ok=True)
    internal_output = output_dir / name
    shutil.copy2(output, internal_output)

    db.add(JobDocument(
        scan_job_id=job.id,
        sequence=1,
        path=str(internal_output),
        final_name=name,
    ))
    db.commit()

    delivery = JobDelivery(scan_job_id=job.id, destination_id=destination.id, status="delivering")
    db.add(delivery)
    db.commit()

    try:
        relative_name = "/".join(folder_parts + [name])
        delivery.target = deliver(destination, internal_output, name, relative_name)
        delivery.status = "delivered"
        job.status = "delivered"
        job.error = None
    except DeliveryError as exc:
        delivery.status = "error"
        delivery.error = str(exc)
        job.status = "delivery_error"
        job.error = str(exc)

    job.completed_at = datetime.utcnow()
    db.commit()
