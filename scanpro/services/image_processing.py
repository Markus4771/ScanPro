from dataclasses import dataclass
from pathlib import Path
import tempfile

import cv2
import fitz
import numpy as np
import pytesseract
from PIL import Image


class ImageProcessingError(RuntimeError):
    pass


@dataclass
class ImageProcessingOptions:
    auto_rotate: bool = False
    deskew: bool = False
    auto_crop: bool = False
    remove_borders: bool = False


@dataclass
class ImageProcessingResult:
    pages_processed: int = 0
    pages_rotated: int = 0
    pages_deskewed: int = 0
    pages_cropped: int = 0
    pages_border_cleaned: int = 0


def _rotate_bound(image: np.ndarray, angle: float, border_value: int = 255) -> np.ndarray:
    height, width = image.shape[:2]
    center = (width / 2.0, height / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))
    matrix[0, 2] += (new_width / 2) - center[0]
    matrix[1, 2] += (new_height / 2) - center[1]
    return cv2.warpAffine(
        image,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(border_value, border_value, border_value),
    )


def _auto_rotate(image: np.ndarray) -> tuple[np.ndarray, bool]:
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        osd = pytesseract.image_to_osd(Image.fromarray(rgb), output_type=pytesseract.Output.DICT)
        rotation = int(osd.get("rotate", 0) or 0)
    except Exception:
        return image, False

    if rotation not in {90, 180, 270}:
        return image, False
    if rotation == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE), True
    if rotation == 180:
        return cv2.rotate(image, cv2.ROTATE_180), True
    return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE), True


def _deskew(image: np.ndarray) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    _, threshold = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(threshold > 0))
    if coords.shape[0] < 100:
        return image, False

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    else:
        angle = angle

    # OpenCV's point coordinates are row/column, so the sign must be inverted.
    correction = -float(angle)
    if abs(correction) < 0.25 or abs(correction) > 12:
        return image, False
    return _rotate_bound(image, correction), True


def _trim_dark_borders(image: np.ndarray) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    top, bottom, left, right = 0, height, 0, width
    max_y = max(1, int(height * 0.08))
    max_x = max(1, int(width * 0.08))

    while top < max_y and np.mean(gray[top, :] < 80) > 0.55:
        top += 1
    while bottom > height - max_y and np.mean(gray[bottom - 1, :] < 80) > 0.55:
        bottom -= 1
    while left < max_x and np.mean(gray[:, left] < 80) > 0.55:
        left += 1
    while right > width - max_x and np.mean(gray[:, right - 1] < 80) > 0.55:
        right -= 1

    if top == 0 and bottom == height and left == 0 and right == width:
        return image, False
    if bottom - top < height * 0.5 or right - left < width * 0.5:
        return image, False
    return image[top:bottom, left:right], True


def _auto_crop(image: np.ndarray) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = gray < 245
    coords = np.argwhere(mask)
    if coords.size == 0:
        return image, False

    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    height, width = gray.shape
    margin_x = max(8, int(width * 0.01))
    margin_y = max(8, int(height * 0.01))
    x0 = max(0, int(x0) - margin_x)
    x1 = min(width - 1, int(x1) + margin_x)
    y0 = max(0, int(y0) - margin_y)
    y1 = min(height - 1, int(y1) + margin_y)

    cropped = image[y0:y1 + 1, x0:x1 + 1]
    if cropped.shape[0] >= height * 0.98 and cropped.shape[1] >= width * 0.98:
        return image, False
    return cropped, True


def process_pdf(pdf_path: str, options: ImageProcessingOptions) -> ImageProcessingResult:
    source = Path(pdf_path)
    if not source.exists():
        raise ImageProcessingError(f"PDF wurde nicht gefunden: {source}")

    if not any((options.auto_rotate, options.deskew, options.auto_crop, options.remove_borders)):
        return ImageProcessingResult()

    doc = fitz.open(source)
    out = fitz.open()
    result = ImageProcessingResult()

    try:
        for page in doc:
            pix = page.get_pixmap(dpi=200, colorspace=fitz.csRGB, alpha=False)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            result.pages_processed += 1

            if options.auto_rotate:
                image, changed = _auto_rotate(image)
                result.pages_rotated += int(changed)

            if options.deskew:
                image, changed = _deskew(image)
                result.pages_deskewed += int(changed)

            if options.remove_borders:
                image, changed = _trim_dark_borders(image)
                result.pages_border_cleaned += int(changed)

            if options.auto_crop:
                image, changed = _auto_crop(image)
                result.pages_cropped += int(changed)

            ok, encoded = cv2.imencode(".png", image)
            if not ok:
                raise ImageProcessingError("Bild konnte nicht als PNG kodiert werden.")

            rect = page.rect
            new_page = out.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=encoded.tobytes(), keep_proportion=True)

        with tempfile.NamedTemporaryFile(
            dir=source.parent, prefix=f".{source.stem}-processed-", suffix=".pdf", delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

        out.save(temp_path, garbage=4, deflate=True)
        out.close()
        doc.close()
        temp_path.replace(source)
        return result
    except Exception as exc:
        try:
            out.close()
        except Exception:
            pass
        try:
            doc.close()
        except Exception:
            pass
        if isinstance(exc, ImageProcessingError):
            raise
        raise ImageProcessingError(f"Bildoptimierung fehlgeschlagen: {exc}") from exc
