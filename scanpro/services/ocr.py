import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import JobDocument, JobOcrResult, ProfileOcrSettings, ScanJob, ScanProfile


class OcrError(RuntimeError):
    pass


def _ocr_language(db: Session, profile: ScanProfile) -> str:
    settings = (
        db.query(ProfileOcrSettings)
        .filter(ProfileOcrSettings.profile_id == profile.id)
        .first()
    )
    return (settings.language if settings else "deu").strip() or "deu"


def apply_ocr(
    db: Session,
    job: ScanJob,
    profile: ScanProfile,
    documents: list[JobDocument],
) -> list[JobOcrResult]:
    if not profile.ocr_enabled:
        return []

    language = _ocr_language(db, profile)
    rows: list[JobOcrResult] = []

    for document in documents:
        source = Path(document.path)
        if not source.exists():
            raise OcrError(f"OCR-Quelldatei wurde nicht gefunden: {source}")

        with tempfile.NamedTemporaryFile(
            dir=source.parent,
            prefix=f".{source.stem}-ocr-",
            suffix=".pdf",
            delete=False,
        ) as pdf_tmp:
            output_pdf = Path(pdf_tmp.name)

        with tempfile.NamedTemporaryFile(
            dir=source.parent,
            prefix=f".{source.stem}-ocr-",
            suffix=".txt",
            delete=False,
        ) as txt_tmp:
            sidecar = Path(txt_tmp.name)

        command = [
            "ocrmypdf",
            "--skip-text",
            "--deskew",
            "--clean-final",
            "--optimize",
            "1",
            "--language",
            language,
            "--sidecar",
            str(sidecar),
            str(source),
            str(output_pdf),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except FileNotFoundError as exc:
            output_pdf.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
            raise OcrError("OCRmyPDF ist nicht installiert.") from exc
        except subprocess.TimeoutExpired as exc:
            output_pdf.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
            raise OcrError("OCR-Verarbeitung hat das Zeitlimit überschritten.") from exc

        if result.returncode not in {0, 6}:
            detail = (result.stderr or result.stdout).strip()
            output_pdf.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
            raise OcrError(detail or "OCRmyPDF ist fehlgeschlagen.")

        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            output_pdf.replace(source)
        else:
            output_pdf.unlink(missing_ok=True)

        text = ""
        try:
            text = sidecar.read_text(encoding="utf-8", errors="replace")
        finally:
            sidecar.unlink(missing_ok=True)

        row = JobOcrResult(
            scan_job_id=job.id,
            document_id=document.id,
            language=language,
            text=text,
            characters=len(text),
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
