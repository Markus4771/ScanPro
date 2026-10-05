from enum import StrEnum

class SplitMethod(StrEnum):
    NONE = "none"
    PATCH_T = "patch-t"
    QR = "qr"
    BARCODE = "barcode"
    BLANK_PAGE = "blank-page"
    MANUAL = "manual"

def validate_split(enabled: bool, method: str) -> None:
    if not enabled:
        return
    try:
        parsed = SplitMethod(method)
    except ValueError as exc:
        raise ValueError(f"Unbekannte Trennmethode: {method}") from exc
    if parsed is SplitMethod.NONE:
        raise ValueError("Bei aktivierter Trennung muss eine Trennmethode gewählt werden.")
