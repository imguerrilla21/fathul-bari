import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentChunk(Base):
    """
    Model chunk dokumen untuk Hybrid Search Engine (Leksikal BM25 & Vektor Semantik).
    Mendukung teks Arab (Hadis/Syarah) dan terjemahan Bahasa Indonesia.
    """
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sharh_section_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sharh_sections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    hadith_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("hadiths.id", ondelete="CASCADE"), nullable=True, index=True
    )
    chunk_type: Mapped[str] = mapped_column(String(50), index=True, default="sharh_section")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ar", index=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    pdf_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    printed_page: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class RetrievalLog(Base):
    """
    Model log retrieval pencarian untuk evaluasi metrik (Recall@k, MRR, latency).
    """
    __tablename__ = "retrieval_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_language: Mapped[str] = mapped_column(String(20), default="id", index=True)
    retrieval_mode: Mapped[str] = mapped_column(String(30), default="research", index=True)
    retrieved_chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    retrieved_chunks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reranked_chunks: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
