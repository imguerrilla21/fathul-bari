import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, JSON, Text
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class HadithIdentityEntity(Base):
    __tablename__ = "alignment_hadith_identities"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_source = Column(String(100), nullable=True)
    external_id = Column(Text, nullable=True)
    collection = Column(Text, nullable=True)
    hadith_number = Column(Text, nullable=True)
    kitab = Column(Text, nullable=True)
    bab = Column(Text, nullable=True)
    narrator = Column(Text, nullable=True)
    arabic_matn = Column(Text, nullable=True)
    normalized_matn = Column(Text, nullable=True)
    matn_fingerprint = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class HadithSharhAlignmentEntity(Base):
    __tablename__ = "alignment_hadith_sharh"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), nullable=False)
    passage_id = Column(String(36), nullable=False)
    alignment_type = Column(String(50), nullable=True)
    score = Column(Numeric(6, 5), nullable=True)
    confidence_band = Column(String(30), nullable=True)
    status = Column(String(30), nullable=True)
    matched_features_json = Column(JSON, default=dict)
    explanation_json = Column(JSON, default=dict)
    verified_by = Column(String(36), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class AlignmentEvidenceEntity(Base):
    __tablename__ = "alignment_evidence"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alignment_id = Column(String(36), nullable=False)
    evidence_type = Column(String(40), nullable=True)
    source_text = Column(Text, nullable=True)
    matched_text = Column(Text, nullable=True)
    score = Column(Numeric(6, 5), nullable=True)
    metadata_json = Column(JSON, default=dict)

class AlignmentJobEntity(Base):
    __tablename__ = "alignment_jobs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection = Column(Text, nullable=True)
    total_hadiths = Column(Integer, default=0)
    processed_hadiths = Column(Integer, default=0)
    candidates_generated = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    status = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
