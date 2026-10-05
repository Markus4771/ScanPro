from pydantic import BaseModel, Field

class ScannerCreate(BaseModel):
    name: str
    manufacturer: str | None = None
    model: str | None = None
    backend: str = "naps2"
    driver: str = "sane"
    address: str | None = None
    device_id: str | None = None
    enabled: bool = True

class ScannerImport(BaseModel):
    name: str
    driver: str = "sane"
    address: str | None = None
    device_id: str | None = None

class ScannerUpdate(BaseModel):
    name: str | None = None
    driver: str | None = None
    address: str | None = None
    device_id: str | None = None
    enabled: bool | None = None

class TestScanRequest(BaseModel):
    dpi: int = 300
    duplex: bool = False
    color_mode: str = "color"

class DestinationCreate(BaseModel):
    name: str
    type: str = "local"
    enabled: bool = True
    config: dict = Field(default_factory=dict)

class DestinationUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    enabled: bool | None = None
    config: dict | None = None

class ScanProfileCreate(BaseModel):
    name: str
    dpi: int = 300
    color_mode: str = "color"
    duplex: bool = True
    ocr_enabled: bool = False
    split_enabled: bool = False
    split_method: str = "none"

class ScanProfileUpdate(BaseModel):
    name: str | None = None
    dpi: int | None = None
    color_mode: str | None = None
    duplex: bool | None = None
    ocr_enabled: bool | None = None
    split_enabled: bool | None = None
    split_method: str | None = None

class ProfileShareUpdate(BaseModel):
    enabled: bool
    share_name: str | None = None

class WorkflowCreate(BaseModel):
    name: str
    scanner_id: int | None = None
    profile_id: int
    destination_id: int
    enabled: bool = True
