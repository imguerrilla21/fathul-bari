import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SharhSection(Base):
    __tablename__ = "sharh_sections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="fathul_bari")
    volume: Mapped[int | None] = mapped_column(Integer)
    pdf_page: Mapped[int | None] = mapped_column(Integer)
    printed_page: Mapped[int | None] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer)
    section_order: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text)
    arabic_text: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(Text)
    source_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    source_document_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(30), default="raw", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class HadithSharhLink(Base):
    __tablename__ = "hadith_sharh_links"

    __table_args__ = (
        UniqueConstraint("hadith_id", "sharh_section_id", name="uq_hadith_sharh_link"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hadith_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hadiths.id"), nullable=False, index=True)
    sharh_section_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sharh_sections.id"), nullable=False, index=True)
    match_method: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
