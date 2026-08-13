import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class SourceDocument(Base):
    """Model registri dokumen sumber fisik/digital Fathul Bari (Source Document Registry)."""
    __tablename__ = "source_documents_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=False)
    author = Column(Text, default="أحمد بن علي بن حجر العسقلاني")
    language = Column(String(20), default="ar")
    edition = Column(Text, default="Dar al-Ma'rifah Edition")
    publisher = Column(Text, default="Dar al-Ma'rifah")
    publication_year = Column(Integer, default=1379)
    source_type = Column(String(30), default="PDF", nullable=False)
    file_name = Column(Text, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    page_count = Column(Integer, default=520)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SourceVolume(Base):
    """Model entitas jilid fisik dokumen (Source Volume Entity)."""
    __tablename__ = "source_volumes_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("source_documents_v2.id"), nullable=False, index=True)
    volume_number = Column(Integer, nullable=False, index=True)
    title = Column(Text, nullable=True)
    page_count = Column(Integer, default=520)
    metadata_json = Column(JSON, default=dict)


class SourcePageEntity(Base):
    """Model entitas halaman fisik dengan dual page numbers & 3 lapisan teks."""
    __tablename__ = "source_pages_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volume_id = Column(String(36), ForeignKey("source_volumes_v2.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    pdf_page_number = Column(Integer, nullable=False)      # Digital PDF page e.g. 67
    printed_page_number = Column(Integer, nullable=False)  # Printed book page e.g. 45
    image_path = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)           # Raw extracted text
    ocr_text = Column(Text, nullable=True)                 # OCR fallback text
    normalized_text = Column(Text, nullable=True)          # Arabic Normalizer v2 text
    extraction_method = Column(String(30), default="TEXT_LAYER")  # TEXT_LAYER, OCR, HYBRID
    ocr_confidence = Column(Float, default=0.98)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SourceSectionEntity(Base):
    """Model node struktur hierarki (Kitab ➔ Bab ➔ Fasl)."""
    __tablename__ = "source_sections_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volume_id = Column(String(36), ForeignKey("source_volumes_v2.id"), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("source_sections_v2.id"), nullable=True, index=True)
    section_type = Column(String(30), default="BAB", nullable=False)  # KITAB, BAB, FASL, SHARH
    title_ar = Column(Text, nullable=False)
    title_normalized = Column(Text, nullable=True)
    start_page = Column(Integer, default=1)
    end_page = Column(Integer, default=1)
    start_offset = Column(Integer, default=0)
    end_offset = Column(Integer, default=1000)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SharhChunkEntity(Base):
    """Model entitas potongan chunk syarah dengan Kode Sitasi Universal (FB-V1-P45-C003)."""
    __tablename__ = "sharh_chunks_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volume_id = Column(String(36), ForeignKey("source_volumes_v2.id"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("source_sections_v2.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("source_pages_v2.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    citation_code = Column(String(50), nullable=False, index=True)  # FB-V1-P45-C003
    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True)
    start_offset = Column(Integer, default=0)
    end_offset = Column(Integer, default=800)
    token_count = Column(Integer, default=350)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SharhHadithReferenceEntity(Base):
    """Model entitas rujukan hadis terhubung dari chunk syarah Fathul Bari."""
    __tablename__ = "sharh_hadith_references_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sharh_chunk_id = Column(String(36), ForeignKey("sharh_chunks_v2.id"), nullable=False, index=True)
    hadith_id = Column(String(36), ForeignKey("hadith_entities.id"), nullable=True, index=True)
    reference_text = Column(Text, nullable=True)
    reference_type = Column(String(30), default="EXACT")  # EXACT, PATTERN, LEXICAL, SEMANTIC
    confidence = Column(Float, default=0.96)
    detection_method = Column(String(30), default="PATTERN")
    verified = Column(Boolean, default=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
