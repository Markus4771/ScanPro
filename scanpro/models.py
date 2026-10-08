from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    smb_username: Mapped[str] = mapped_column(String(80), unique=True)
    smb_password: Mapped[str] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProcessingProfile(Base):
    __tablename__ = "processing_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    ocr_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ocr_language: Mapped[str] = mapped_column(String(40), default="deu")
    remove_blank_pages: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_rotate: Mapped[bool] = mapped_column(Boolean, default=False)
    deskew: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_crop: Mapped[bool] = mapped_column(Boolean, default=False)
    split_method: Mapped[str] = mapped_column(String(30), default="none")
    filename_template: Mapped[str] = mapped_column(String(255), default="{date}_{input}_{job}_{document}")
    pdfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    color_mode: Mapped[str] = mapped_column(String(20), default="keep")
    dpi: Mapped[int] = mapped_column(Integer, default=0)
    normalize_a4: Mapped[bool] = mapped_column(Boolean, default=False)
    blank_threshold: Mapped[int] = mapped_column(Integer, default=99)
    subfolder_template: Mapped[str] = mapped_column(String(255), default="")


class Destination(Base):
    __tablename__ = "destinations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str] = mapped_column(String(30), default="local")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")


class ScanInput(Base):
    __tablename__ = "scan_inputs"
    __table_args__ = (UniqueConstraint("share_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    share_name: Mapped[str] = mapped_column(String(80))
    path: Mapped[str] = mapped_column(String(255))
    smb_username: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    smb_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("processing_profiles.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    input_id: Mapped[int] = mapped_column(ForeignKey("scan_inputs.id"))
    profile_id: Mapped[int] = mapped_column(ForeignKey("processing_profiles.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    source_path: Mapped[str] = mapped_column(Text)
    working_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class JobDocument(Base):
    __tablename__ = "job_documents"
    __table_args__ = (UniqueConstraint("scan_job_id", "sequence"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(Text)
    final_name: Mapped[str] = mapped_column(String(255))


class JobDelivery(Base):
    __tablename__ = "job_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id", ondelete="CASCADE"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    target: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
