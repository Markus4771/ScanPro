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
    smb_password: str = ""
    enabled: bool = True
