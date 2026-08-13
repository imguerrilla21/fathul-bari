import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResearchProject(Base):
    """
    Model Proyek Penelitian Fathul Bari.
    Mengelompokkan catatan, anotasi teks, sitasi ilmiah, dan subgraf riset.
    """
    __tablename__ = "research_projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), default="Peneliti Hadis", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    notes: Mapped[list["ResearchNote"]] = relationship(
        "ResearchNote",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ResearchNote.created_at)",
    )
    annotations: Mapped[list["ResearchAnnotation"]] = relationship(
        "ResearchAnnotation",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ResearchAnnotation.created_at)",
    )
    citations: Mapped[list["ResearchCitation"]] = relationship(
        "ResearchCitation",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ResearchCitation.created_at)",
    )


class ResearchNote(Base):
    """
    Model Catatan Ilmiah / Analisis Riset dalam format Markdown.
    """
    __tablename__ = "research_notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hadith_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True)
    sharh_section_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True)
    source_page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="notes")


class ResearchAnnotation(Base):
    """
    Model Anotasi & Highlight Teks langsung pada matan hadis atau syarah Fathul Bari.
    Tipe: 'NOTE', 'QUESTION', 'IMPORTANT', 'CROSS_REFERENCE', 'QUOTE', 'TODO'.
    """
    __tablename__ = "research_annotations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sharh_section_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True)
    hadith_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True)
    selected_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    anchor_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    anchor_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(32), default="NOTE", nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="annotations")


class ResearchCitation(Base):
    """
    Model Koleksi Sitasi Akademik Turats yang tersimpan dalam Proyek Riset.
    """
    __tablename__ = "research_citations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    hadith_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True)
    sharh_section_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True)
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    work_title: Mapped[str] = mapped_column(String(255), default="Fathul Bari Syarah Shahih al-Bukhari", nullable=False)
    author: Mapped[str] = mapped_column(String(255), default="Al-Hafizh Ibnu Hajar al-Asqalani", nullable=False)
    edition: Mapped[str | None] = mapped_column(String(255), default="Dar al-Ma'rifah, Beirut", nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    printed_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="citations")

class ResearchBookmark(Base):
    """
    Model Bookmark / Tandai halaman atau bagian teks.
    """
    __tablename__ = "research_bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
