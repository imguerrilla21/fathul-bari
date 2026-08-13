import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class PublicationEntity(Base):
    __tablename__ = "publications_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=True)
    title = Column(Text, nullable=False)
    slug = Column(Text, unique=True, nullable=False)
    content_type = Column(String(50), nullable=True)
    status = Column(String(30), default='DRAFT')
    language = Column(String(10), default='id')
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class PublicationVersionEntity(Base):
    __tablename__ = "publication_versions_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    change_summary = Column(Text, nullable=True)

class PublicationBlockEntity(Base):
    __tablename__ = "publication_blocks_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_version_id = Column(String(36), nullable=False)
    block_order = Column(Integer, nullable=True)
    block_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

class PublicationEvidenceEntity(Base):
    __tablename__ = "publication_evidence_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_block_id = Column(String(36), nullable=True)
    evidence_type = Column(String(50), nullable=True)
    evidence_id = Column(String(36), nullable=True)
    relation = Column(String(50), nullable=True)

class PublicationReferenceEntity(Base):
    __tablename__ = "publication_references_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), nullable=True)
    source_id = Column(String(36), nullable=True)
    citation_key = Column(Text, nullable=True)
    citation_text = Column(Text, nullable=True)
    order_number = Column(Integer, nullable=True)

class EditorialIssueEntity(Base):
    __tablename__ = "editorial_issues_v3"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), nullable=True)
    block_id = Column(String(36), nullable=True)
    issue_type = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=True)
    created_by = Column(String(36), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
