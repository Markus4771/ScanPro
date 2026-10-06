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


class WorkflowUpdate(BaseModel):
    name: str | None = None
    scanner_id: int | None = None
    profile_id: int | None = None
    destination_id: int | None = None
    enabled: bool | None = None


class ProfileProcessingUpdate(BaseModel):
    remove_blank_pages: bool = False


class ProfileImageProcessingUpdate(BaseModel):
    auto_rotate: bool = False
    deskew: bool = False
    auto_crop: bool = False
    remove_borders: bool = False


class ProfileOcrSettingsUpdate(BaseModel):
    language: str = "deu"


class ProfileNamingSettingsUpdate(BaseModel):
    filename_template: str = "{date}_{profile}_{job}_{document}"
    use_ocr_first_line: bool = False


class ProfilePaperlessRulesUpdate(BaseModel):
    title_template: str = "{filename}"
    correspondent_map: dict = Field(default_factory=dict)
    document_type_map: dict = Field(default_factory=dict)
    tags_map: dict = Field(default_factory=dict)
    ocr_contains_rules: list[dict] = Field(default_factory=list)


class ProfileOutputSettingsUpdate(BaseModel):
    mode: str = "document"
    output_format: str = "pdf"
    jpeg_quality: int = 92


class ScannerConnectionSettingsUpdate(BaseModel):
    location: str = "Lokal"
    connection_type: str = "local"
    timeout_seconds: int = 60
    retries: int = 1


class ScannerStaticTargetUpdate(BaseModel):
    enabled: bool = False
    driver: str = "sane"
    device_name: str = ""
    device_id: str = ""
    address: str = ""


class ScannerMenuEntryUpdate(BaseModel):
    enabled: bool = True
    display_name: str = ""
    destination_id: int | None = None
