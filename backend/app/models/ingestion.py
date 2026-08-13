import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey
from app.database import Base


class SourceDocument(Base):
    """Dokumen fisik sumber (PDF / Teks) Fathul Bari."""
    __tablename__ = "source_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_slug = Column(String(100), default="fathul_bari", nullable=False, index=True)
    edition_id = Column(String(100), default="edition-001")
    volume = Column(Integer, default=1, index=True)
    filename = Column(String(255), nullable=False)
    object_key = Column(String(255), nullable=True)
    file_size = Column(Integer, default=0)
    sha256 = Column(String(64), unique=True, index=True, nullable=False)
    page_count = Column(Integer, default=0)
    language = Column(String(10), default="ar")
    extraction_status = Column(String(30), default="uploaded")  # uploaded, extracted, normalized, completed
    ocr_status = Column(String(30), default="pending")        # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class SourcePage(Base):
    """Halaman individual dari dokumen sumber dengan representasi ganda (raw vs normalized)."""
    __tablename__ = "source_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_document_id = Column(String(36), ForeignKey("source_documents.id"), nullable=False, index=True)
    pdf_page_number = Column(Integer, nullable=False)
    printed_page_number = Column(Integer, nullable=True)
    image_object_key = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)         # Asli dari OCR/Teks tanpa modifikasi
    normalized_text = Column(Text, nullable=True)   # Teks Arab ternormalisasi untuk search/matching
    ocr_confidence = Column(Float, default=0.95)
    status = Column(String(30), default="processed")


class TextBlock(Base):
    """Blok teks terpisah (MAIN_TEXT, HEADER, FOOTNOTE, PAGE_NUMBER) dengan koordinat layout."""
    __tablename__ = "text_blocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), ForeignKey("source_pages.id"), nullable=False, index=True)
    block_type = Column(String(30), default="MAIN_TEXT")  # MAIN_TEXT, HEADER, FOOTNOTE, PAGE_NUMBER
    sequence = Column(Integer, default=1)
    bbox_json = Column(JSON, nullable=True)  # {"x": 100, "y": 200, "width": 800, "height": 300}
    raw_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    confidence = Column(Float, default=0.95)


class IngestionJob(Base):
    """Job pipeline penyerapan data (Pipeline State Machine berulang/resumable)."""
    __tablename__ = "ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_document_id = Column(String(36), ForeignKey("source_documents.id"), nullable=False, index=True)
    volume = Column(Integer, default=1)
    status = Column(String(30), default="pending", index=True)  # pending, running, completed, failed
    progress_pct = Column(Integer, default=0)
    current_stage = Column(String(50), default="VALIDATE")
    pipeline_version = Column(String(30), default="13.0")
    error_message = Column(Text, nullable=True)
    checkpoint_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CorpusManifest(Base):
    """Manifest reproduksibilitas korpus Fathul Bari per volume."""
    __tablename__ = "corpus_manifests"

    id = Column(Integer, primary_key=True, index=True)
    work_slug = Column(String(100), default="fathul_bari")
    edition = Column(String(100), default="edition-001")
    volume = Column(Integer, nullable=False, index=True)
    source_sha256 = Column(String(64), nullable=False)
    processed_pages = Column(Integer, default=0)
    sections_count = Column(Integer, default=0)
    hadith_candidates_count = Column(Integer, default=0)
    verified_links_count = Column(Integer, default=0)
    chunks_count = Column(Integer, default=0)
    embeddings_count = Column(Integer, default=0)
    pipeline_version = Column(String(30), default="13.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IngestionJobEntity(Base):
    __tablename__ = "stage34_ingestion_jobs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_file_id = Column(String(36), nullable=True)
    job_type = Column(String(50), nullable=True)
    status = Column(String(30), nullable=True)
    progress = Column(Integer, default=0)
    total_units = Column(Integer, nullable=True)
    processed_units = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, default=dict)

class CorpusAuditEventEntity(Base):
    __tablename__ = "corpus_audit_events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=True)
    event_type = Column(String(50), nullable=True)
    actor_type = Column(String(30), nullable=True)
    actor_id = Column(String(36), nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
