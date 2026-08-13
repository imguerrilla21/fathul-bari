from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class ResearchSessionEntity(Base):
    __tablename__ = "research_engine_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True) # Optional, if users are implemented
    title = Column(String, nullable=True)
    original_question = Column(String, nullable=False)
    intent = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, default="IN_PROGRESS")
    metadata_json = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    steps = relationship("ResearchStepEntity", back_populates="session", cascade="all, delete-orphan")
    claims = relationship("ResearchClaimEntity", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("ResearchEvidenceEntity", back_populates="session", cascade="all, delete-orphan")

class ResearchStepEntity(Base):
    __tablename__ = "research_engine_steps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_engine_sessions.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    session = relationship("ResearchSessionEntity", back_populates="steps")

class ResearchClaimEntity(Base):
    __tablename__ = "research_engine_claims"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_engine_sessions.id"), nullable=False)
    claim_text = Column(String, nullable=False)
    claim_type = Column(String(40), nullable=True)
    confidence = Column(Float, nullable=True)
    validation_status = Column(String(30), nullable=True) # PASS, REJECT
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    session = relationship("ResearchSessionEntity", back_populates="claims")
    citations = relationship("ResearchCitationEntity", back_populates="claim", cascade="all, delete-orphan")

class ResearchEvidenceEntity(Base):
    __tablename__ = "research_engine_evidence"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_engine_sessions.id"), nullable=False)
    # The actual source being referred to (e.g., a hadith ID or fathul bari chunk ID)
    source_id = Column(String(255), nullable=True)
    document_id = Column(String(255), nullable=True)
    chunk_id = Column(String(255), nullable=True)
    
    evidence_text = Column(String, nullable=True)
    evidence_type = Column(String(50), nullable=True) # PRIMARY_HADITH, etc.
    relevance_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    metadata_json = Column(JSON, default={})
    
    session = relationship("ResearchSessionEntity", back_populates="evidence")

class ResearchCitationEntity(Base):
    __tablename__ = "research_engine_citations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("research_engine_claims.id"), nullable=False)
    source_id = Column(String(255), nullable=False)
    locator = Column(String, nullable=True)
    citation_text = Column(String, nullable=True)
    validation_status = Column(String(30), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    claim = relationship("ResearchClaimEntity", back_populates="citations")

class ResearchConflictEntity(Base):
    __tablename__ = "research_engine_conflicts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_engine_sessions.id"), nullable=False)
    topic = Column(String(100), nullable=False)
    positions = Column(JSON, nullable=False) # e.g. [{"source": "A", "position": "SAHIH"}, {"source": "B", "position": "HASAN"}]
    
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ResearchAnswerEntity(Base):
    __tablename__ = "research_engine_answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("research_engine_sessions.id"), nullable=False)
    title = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    sections_json = Column(JSON, nullable=False) # The structured answer sections
    created_at = Column(DateTime(timezone=True), default=utcnow)
