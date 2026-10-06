from pydantic import BaseModel, Field


class ProfilePayload(BaseModel):
    name: str
    ocr_enabled: bool = True
    ocr_language: str = "deu"
    remove_blank_pages: bool = False
    auto_rotate: bool = False
    deskew: bool = False
    auto_crop: bool = False
    split_method: str = "none"
    filename_template: str = "{date}_{input}_{job}_{document}"


class DestinationPayload(BaseModel):
    name: str
    type: str = "local"
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class ScanInputPayload(BaseModel):
    name: str
    share_name: str
    profile_id: int
    destination_id: int
    enabled: bool = True
