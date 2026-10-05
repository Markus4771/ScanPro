from pydantic import BaseModel, Field

class ScannerCreate(BaseModel):
    name: str
    manufacturer: str | None = None
    model: str | None = None
    backend: str = "naps2"
    driver: str = "escl"
    address: str | None = None
    device_id: str | None = None
    enabled: bool = True

class DestinationCreate(BaseModel):
    name: str
    type: str = "local"
    enabled: bool = True
    config: dict = Field(default_factory=dict)

class ScanProfileCreate(BaseModel):
    name: str
    dpi: int = 300
    color_mode: str = "color"
    duplex: bool = True
    ocr_enabled: bool = False
    split_enabled: bool = False
    split_method: str = "none"

class WorkflowCreate(BaseModel):
    name: str
    scanner_id: int | None = None
    profile_id: int
    destination_id: int
    enabled: bool = True
