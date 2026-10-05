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


class JobDelivery(Base):
    __tablename__ = "job_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    workflow_id: Mapped[int | None] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    target_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileProcessing(Base):
    __tablename__ = "profile_processing"
    __table_args__ = (UniqueConstraint("profile_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id", ondelete="CASCADE"))
    remove_blank_pages: Mapped[bool] = mapped_column(Boolean, default=False)


class JobProcessing(Base):
    __tablename__ = "job_processing"
    __table_args__ = (UniqueConstraint("scan_job_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    blank_pages_removed: Mapped[int] = mapped_column(Integer, default=0)
    blank_pages_json: Mapped[str] = mapped_column(Text, default="[]")


class JobDocument(Base):
    __tablename__ = "job_documents"
    __table_args__ = (UniqueConstraint("scan_job_id", "sequence"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(Text)
    split_method: Mapped[str] = mapped_column(String(30), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobSeparationMarker(Base):
    __tablename__ = "job_separation_markers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    page: Mapped[int] = mapped_column(Integer)
    marker_type: Mapped[str] = mapped_column(String(40))
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileImageProcessing(Base):
    __tablename__ = "profile_image_processing"
    __table_args__ = (UniqueConstraint("profile_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id", ondelete="CASCADE"))
    auto_rotate: Mapped[bool] = mapped_column(Boolean, default=False)
    deskew: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_crop: Mapped[bool] = mapped_column(Boolean, default=False)
    remove_borders: Mapped[bool] = mapped_column(Boolean, default=False)


class JobImageProcessing(Base):
    __tablename__ = "job_image_processing"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("job_documents.id"), nullable=True)
    pages_processed: Mapped[int] = mapped_column(Integer, default=0)
    pages_rotated: Mapped[int] = mapped_column(Integer, default=0)
    pages_deskewed: Mapped[int] = mapped_column(Integer, default=0)
    pages_cropped: Mapped[int] = mapped_column(Integer, default=0)
    pages_border_cleaned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileOcrSettings(Base):
    __tablename__ = "profile_ocr_settings"
    __table_args__ = (UniqueConstraint("profile_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("scan_profiles.id", ondelete="CASCADE"))
    language: Mapped[str] = mapped_column(String(80), default="deu")


class JobOcrResult(Base):
    __tablename__ = "job_ocr_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("job_documents.id"))
    language: Mapped[str] = mapped_column(String(80), default="deu")
    text: Mapped[str] = mapped_column(Text, default="")
    characters: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
