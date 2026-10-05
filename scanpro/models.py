from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Scanner(Base):
    __tablename__ = "scanners"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    backend: Mapped[str] = mapped_column(String(30), default="naps2")
    driver: Mapped[str] = mapped_column(String(30), default="escl")
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    capabilities_json: Mapped[str] = mapped_column(Text, default="{}")

class Destination(Base):
    __tablename__ = "destinations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str] = mapped_column(String(30), default="local")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")

class ScanProfile(Base):
    __tablename__ = "scan_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    dpi: Mapped[int] = mapped_column(Integer, default=300)
    color_mode: Mapped[str] = mapped_column(String(30), default="color")
    duplex: Mapped[bool] = mapped_column(Boolean, default=True)
    ocr_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    split_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    split_method: Mapped[str] = mapped_column(String(30), default="none")

class ProfileShare(Base):
    __tablename__ = "profile_shares"
    __table_args__ = (UniqueConstraint("profile_id"), UniqueConstraint("share_name"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id", ondelete="CASCADE"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    share_name: Mapped[str] = mapped_column(String(80))
    path: Mapped[str] = mapped_column(String(255))

class InboxImport(Base):
    __tablename__ = "inbox_imports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id"))
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"), unique=True)
    source_path: Mapped[str] = mapped_column(Text)
    imported_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    scanner_id: Mapped[int | None] = mapped_column(ForeignKey("scanners.id"), nullable=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int | None] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    input_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
