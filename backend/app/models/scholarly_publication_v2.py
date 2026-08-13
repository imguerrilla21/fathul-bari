import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class ResearchDocumentRevisionEntity(Base):
    """Model revisi riwayat dokumen riset (Research Document Revision Entity)."""
    __tablename__ = "research_document_revisions_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("research_documents_v2.id"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    content_json = Column(JSON, default=dict)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class DocumentClaimEntity(Base):
    """Model entitas klaim faktual dokumen (Document Claim Entity)."""
    __tablename__ = "document_claims_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("research_documents_v2.id"), nullable=False, index=True)
    block_id = Column(String(64), nullable=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(40), default="FACTUAL")  # FACTUAL, INTERPRETIVE, HISTORICAL, LINGUISTIC
    status = Column(String(30), default="UNVERIFIED", index=True)  # UNVERIFIED, SUPPORTED, REJECTED, PARTIAL
    confidence = Column(Float, default=0.95)
    support_level = Column(String(30), default="DIRECT")  # DIRECT, INDIRECT, PARTIAL, UNSUPPORTED
    evidence_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ReviewCommentEntity(Base):
    """Model komentar penelaah peer review (Review Comment Entity)."""
    __tablename__ = "review_comments_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("research_documents_v2.id"), nullable=False, index=True)
    claim_id = Column(String(36), ForeignKey("document_claims_v2.id"), nullable=True)
    block_id = Column(String(64), nullable=True)
    reviewer_id = Column(String(36), nullable=True)
    comment_text = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN")  # OPEN, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class PublicationEntity(Base):
    """Model publikasi ilmiah terverifikasi (Scholarly Publication Entity)."""
    __tablename__ = "publications_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("research_documents_v2.id"), nullable=False, index=True)
    revision_id = Column(String(36), nullable=True)
    publication_code = Column(String(50), nullable=False, unique=True, index=True)  # PUB-2026-000001
    title = Column(Text, nullable=False)
    status = Column(String(30), default="PUBLISHED", index=True)  # READY, PUBLISHED, ARCHIVED
    snapshot_json = Column(JSON, default=dict)
    copyright_status = Column(String(40), default="PUBLIC_DOMAIN")  # PUBLIC_DOMAIN, LICENSED, RESTRICTED
    quality_score = Column(Float, default=94.0)
    published_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
