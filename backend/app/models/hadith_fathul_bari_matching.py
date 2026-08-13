import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class HadithSharhMatchEntity(Base):
    """Model entitas kandidat pencocokan Hadis dengan Syarah Fathul Bari (Hadith ↔ Fathul Bari Match Entity)."""
    __tablename__ = "hadith_sharh_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("hadith_entities.id"), nullable=False, index=True)
    sharh_chunk_id = Column(String(36), ForeignKey("sharh_sections.id"), nullable=True, index=True)
    
    match_type = Column(String(50), default="HYBRID")  # EXACT_REFERENCE, EXACT_TEXT, LEXICAL, SEMANTIC, HYBRID, MANUAL
    
    lexical_score = Column(Float, default=0.95)
    semantic_score = Column(Float, default=0.92)
    reference_score = Column(Float, default=1.00)
    context_score = Column(Float, default=0.90)
    
    confidence_score = Column(Float, default=0.96)
    confidence_band = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW, VERY_LOW
    
    status = Column(String(30), default="PENDING", index=True)  # PENDING, VERIFIED, REJECTED, NEEDS_REVIEW, RELATED
    matcher_version = Column(String(30), default="20.1.0")
    
    rejection_reason = Column(String(100), nullable=True)  # WRONG_HADITH, WRONG_MATN, FALSE_DETECTION, DUPLICATE
    explanation_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
