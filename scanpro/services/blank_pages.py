from pathlib import Path
import fitz

class BlankPageError(RuntimeError):
    pass

def remove_blank_pages(pdf_path: str, white_ratio_threshold: float = 0.995, dark_threshold: int = 245) -> dict:
    source = Path(pdf_path)
    if not source.exists():
        raise BlankPageError(f"PDF wurde nicht gefunden: {source}")

    doc = fitz.open(source)
    keep: list[int] = []
    removed: list[int] = []

    for index, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), colorspace=fitz.csGRAY, alpha=False)
        samples = pix.samples
        if not samples:
            keep.append(index)
            continue
        white = sum(1 for value in samples if value >= dark_threshold)
        ratio = white / len(samples)
        if ratio >= white_ratio_threshold:
            removed.append(index + 1)
        else:
            keep.append(index)

    if not removed:
        doc.close()
        return {"removed": 0, "pages": []}

    if not keep:
        doc.close()
        raise BlankPageError("Alle Seiten wurden als leer erkannt. Original-PDF bleibt erhalten.")

    out = fitz.open()
    for index in keep:
        out.insert_pdf(doc, from_page=index, to_page=index)

    temp = source.with_suffix(".blank-clean.pdf")
    out.save(temp, garbage=4, deflate=True)
    out.close()
    doc.close()
    temp.replace(source)
    return {"removed": len(removed), "pages": removed}
