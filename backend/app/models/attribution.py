import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class ScholarEntity(Base):
    __tablename__ = "scholars"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(Text, nullable=False)
    arabic_name = Column(Text, nullable=True)
    kunyah = Column(Text, nullable=True)
    nisbah = Column(Text, nullable=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ScholarAliasEntity(Base):
    __tablename__ = "scholar_aliases"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scholar_id = Column(String(36), nullable=False)
    alias = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)
    alias_type = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ScholarlyWorkEntity(Base):
    __tablename__ = "scholarly_works"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=False)
    arabic_title = Column(Text, nullable=True)
    author_id = Column(String(36), nullable=True)
    work_type = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class AttributedClaimEntity(Base):
    __tablename__ = "attributed_claims"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    passage_id = Column(String(36), nullable=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), nullable=True)
    speaker_id = Column(String(36), nullable=True) # Actual author of the claim
    reporter_id = Column(String(36), nullable=True) # Who reported it (e.g. Ibn Hajar quoting al-Nawawi)
    relation = Column(String(50), nullable=True) # QUOTES, PARAPHRASES, etc
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class AttributionAuditEntity(Base):
    __tablename__ = "attribution_audits"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), nullable=True)
    detected_speaker_id = Column(String(36), nullable=True)
    expected_speaker_id = Column(String(36), nullable=True)
    status = Column(String(30), nullable=True)
    confidence = Column(Float, nullable=True)
    evidence = Column(JSON, nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
