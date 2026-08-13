from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
import uuid
from datetime import datetime, timezone
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class VerificationRecordEntity(Base):
    __tablename__ = "verification_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String(40), nullable=False) # CLAIM, EVIDENCE, ISNAD, ENTITY
    target_id = Column(String(36), nullable=False)
    reviewer_id = Column(String(36), nullable=False)
    decision = Column(String(40), nullable=False) # VERIFY, REJECT, CORRECT
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ReviewAssignmentEntity(Base):
    __tablename__ = "review_assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String(40), nullable=False)
    target_id = Column(String(36), nullable=False)
    reviewer_id = Column(String(36), nullable=True)
    priority = Column(String(20), nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ClaimVersionEntity(Base):
    __tablename__ = "claim_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), nullable=False)
    version = Column(Integer, nullable=False)
    claim_text = Column(Text, nullable=False)
    author_id = Column(String(36), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class ReviewDiscussionEntity(Base):
    __tablename__ = "review_discussions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String(40), nullable=False)
    target_id = Column(String(36), nullable=False)
    author_id = Column(String(36), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class SourceAnnotationEntity(Base):
    __tablename__ = "source_annotations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=True)
    page_id = Column(String(36), nullable=True)
    chunk_id = Column(String(36), nullable=True)
    annotation_type = Column(String(40), nullable=True) # OCR_ERROR, IMPORTANT
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    reviewer_id = Column(String(36), nullable=True)
    status = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
