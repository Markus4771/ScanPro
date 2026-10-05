from pathlib import Path

import fitz
from PIL import Image
from sqlalchemy.orm import Session

from ..models import JobDocument, ProfileOutputSettings, ScanJob, ScanProfile


class OutputFormatError(RuntimeError):
    pass


IMAGE_ROOT = Path("/var/lib/scanpro/jobs/images")


def get_output_settings(db: Session, profile: ScanProfile) -> ProfileOutputSettings | None:
    return (
        db.query(ProfileOutputSettings)
        .filter(ProfileOutputSettings.profile_id == profile.id)
        .first()
    )


def convert_documents_to_output_format(
    db: Session,
    job: ScanJob,
    profile: ScanProfile,
    documents: list[JobDocument],
) -> list[JobDocument]:
    settings = get_output_settings(db, profile)
    if not settings or settings.output_format == "pdf":
        return documents

    fmt = settings.output_format.lower()
    if fmt not in {"jpeg", "png"}:
        raise OutputFormatError(f"Nicht unterstütztes Ausgabeformat: {fmt}")

    if profile.split_enabled:
        raise OutputFormatError(
            "Bildprofile unterstützen aktuell keine Dokumenttrennung. "
            "Bitte Trennung im Profil deaktivieren."
        )

    output_dir = IMAGE_ROOT / str(job.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for document in documents:
        source = Path(document.path)
        if not source.exists():
            raise OutputFormatError(f"Quelldokument wurde nicht gefunden: {source}")

        pdf = fitz.open(source)
        try:
            for page_index, page in enumerate(pdf, start=1):
                pix = page.get_pixmap(dpi=profile.dpi, colorspace=fitz.csRGB, alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                sequence = len(generated) + 1
                suffix = ".jpg" if fmt == "jpeg" else ".png"
                target = output_dir / f"image-{sequence:03d}{suffix}"

                if fmt == "jpeg":
                    image.save(
                        target,
                        format="JPEG",
                        quality=max(1, min(100, settings.jpeg_quality)),
                        optimize=True,
                    )
                else:
                    image.save(target, format="PNG", optimize=True)
                generated.append(target)
        finally:
            pdf.close()

    if not generated:
        raise OutputFormatError("Es wurden keine Bildseiten erzeugt.")

    first = documents[0]
    first.path = str(generated[0])
    first.split_method = "none"

    for stale in documents[1:]:
        db.delete(stale)

    rows = [first]
    for sequence, target in enumerate(generated[1:], start=2):
        row = JobDocument(
            scan_job_id=job.id,
            sequence=sequence,
            path=str(target),
            split_method="none",
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
