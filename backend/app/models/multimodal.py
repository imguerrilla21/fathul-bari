import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class SourcePageEntity(Base):
    __tablename__ = "multimodal_source_pages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False)
    volume_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    image_uri = Column(String, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    checksum = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class PageRegionEntity(Base):
    __tablename__ = "multimodal_page_regions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), nullable=False)
    region_type = Column(String(40), nullable=True) # MAIN_TEXT, FOOTNOTE, MARGIN
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    reading_order = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class OCRBlockEntity(Base):
    __tablename__ = "multimodal_ocr_blocks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    region_id = Column(String(36), nullable=False)
    raw_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_engine = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class SourceCorrectionEntity(Base):
    __tablename__ = "multimodal_source_corrections"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    block_id = Column(String(36), nullable=True)
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    method = Column(String(50), nullable=True)
    reviewer_id = Column(String(36), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
