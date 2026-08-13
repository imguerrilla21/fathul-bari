import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Numeric, Boolean, DateTime, JSON, Text
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class ScholarlyWorkEntity(Base):
    __tablename__ = "corpus_works"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title_ar = Column(String(255), nullable=False)
    title_id = Column(String(255), nullable=True)
    author = Column(String(255), nullable=False)
    work_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ScholarlyEditionEntity(Base):
    __tablename__ = "corpus_editions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_id = Column(String(36), nullable=False)
    publisher = Column(String(255), nullable=True)
    editor = Column(String(255), nullable=True)
    edition_number = Column(String(50), nullable=True)
    publication_year = Column(Integer, nullable=True)
    publication_place = Column(String(255), nullable=True)
    isbn = Column(String(50), nullable=True)
    total_volumes = Column(Integer, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ScholarlyVolumeEntity(Base):
    __tablename__ = "corpus_volumes"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    edition_id = Column(String(36), nullable=False)
    volume_number = Column(Integer, nullable=False)
    label = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    file_id = Column(String(36), nullable=True)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class SourceFileEntity(Base):
    __tablename__ = "corpus_source_files"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    storage_path = Column(Text, nullable=True)
    storage_provider = Column(String(50), nullable=True)
    uploaded_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class SourcePageEntity(Base):
    __tablename__ = "corpus_source_pages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volume_id = Column(String(36), nullable=False)
    page_number = Column(Integer, nullable=True)
    printed_page_number = Column(String(50), nullable=True)
    image_path = Column(Text, nullable=True)
    image_checksum = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class PageOcrEntity(Base):
    __tablename__ = "corpus_page_ocr"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), nullable=False)
    engine = Column(String(100), nullable=True)
    engine_version = Column(String(50), nullable=True)
    language = Column(String(20), nullable=True)
    raw_text = Column(Text, nullable=True)
    confidence = Column(Numeric, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class OcrCorrectionEntity(Base):
    __tablename__ = "corpus_ocr_corrections"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), nullable=False)
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    corrected_by = Column(String(36), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class SourcePassageEntity(Base):
    __tablename__ = "corpus_source_passages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), nullable=False)
    parent_id = Column(String(36), nullable=True)
    passage_type = Column(String(40), nullable=True)
    sequence_number = Column(Integer, nullable=True)
    display_text = Column(Text, nullable=True)
    search_text = Column(Text, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    verification_status = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class HadithSourceMappingEntity(Base):
    __tablename__ = "corpus_hadith_source_mappings"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), nullable=False)
    passage_id = Column(String(36), nullable=False)
    mapping_type = Column(String(40), nullable=True)
    confidence = Column(Numeric, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class TextualVariantEntity(Base):
    __tablename__ = "corpus_textual_variants"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    passage_a = Column(String(36), nullable=True)
    passage_b = Column(String(36), nullable=True)
    variant_type = Column(String(40), nullable=True)
    difference = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)

class SourceChunkEntity(Base):
    __tablename__ = "corpus_source_chunks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    passage_id = Column(String(36), nullable=False)
    chunk_index = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=True)
    chunk_type = Column(String(40), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
