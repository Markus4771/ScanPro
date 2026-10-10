from pydantic import BaseModel, Field


class LoginPayload(BaseModel):
    username: str
    password: str


class UserPayload(BaseModel):
    username: str
    display_name: str
    password: str
    is_admin: bool = False
    enabled: bool = True


class PasswordChangePayload(BaseModel):
    current_password: str
    new_password: str


class SmbPasswordPayload(BaseModel):
    smb_password: str


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
    pdfa_enabled: bool = False
    color_mode: str = "keep"
    dpi: int = 0
    normalize_a4: bool = False
    blank_threshold: int = 99
    subfolder_template: str = ""
    triangle_position: str = "any"
    triangle_min_size_mm: int = 12
    triangle_remove_page: bool = True
    qr_marker_content: str = ""


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
    smb_username: str = ""
    smb_password: str = ""
    enabled: bool = True
