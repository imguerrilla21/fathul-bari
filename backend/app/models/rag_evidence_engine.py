import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class RAGQueryLog(Base):
    """Model log audit query RAG (RAG Query Audit Trail Log)."""
    __tablename__ = "rag_queries_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    question = Column(Text, nullable=False)
    language = Column(String(20), default="id")
    intent = Column(String(50), default="SHARH")  # SHARH, HADITH_LOOKUP, COMPARATIVE, FIQH
    query_analysis_json = Column(JSON, default=dict)
    evidence_ids_json = Column(JSON, default=list)
    answer_text = Column(Text, nullable=True)
    validation_result_json = Column(JSON, default=dict)
    model_name = Column(String(50), default="gemini-1.5-pro")
    model_version = Column(String(30), default="22.1.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class RAGEvidenceItem(Base):
    """Model entitas kandidat bukti terambil (RAG Evidence Candidate Item)."""
    __tablename__ = "rag_evidence_items_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rag_query_id = Column(String(36), ForeignKey("rag_queries_v2.id"), nullable=False, index=True)
    source_type = Column(String(50), default="FATH_AL_BARI")  # FATH_AL_BARI, HADITH, GRAPH
    source_id = Column(String(36), nullable=True)
    citation_code = Column(String(50), nullable=True, index=True)  # FB-V1-P45-C003
    rank = Column(Integer, nullable=False)
    retrieval_score = Column(Float, default=0.94)
    lexical_score = Column(Float, default=0.90)
    semantic_score = Column(Float, default=0.95)
    graph_score = Column(Float, default=0.88)
    content_hash = Column(String(64), nullable=True)  # SHA-256
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class RAGClaimItem(Base):
    """Model entitas klaim yang diekstrak dari jawaban AI (Extracted Claim Item)."""
    __tablename__ = "rag_claim_items_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rag_query_id = Column(String(36), ForeignKey("rag_queries_v2.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    validation_status = Column(String(40), default="SUPPORTED")  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED
    confidence = Column(Float, default=0.96)
    citation_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class RAGClaimEvidenceLink(Base):
    """Model relasi klaim dengan bukti pendukung (Claim-Evidence Relation)."""
    __tablename__ = "rag_claim_evidence_links_v2"

    claim_id = Column(String(36), ForeignKey("rag_claim_items_v2.id"), primary_key=True)
    evidence_id = Column(String(36), ForeignKey("rag_evidence_items_v2.id"), primary_key=True)
    support_type = Column(String(30), default="DIRECT")  # DIRECT, INDIRECT, INFERRED
    support_score = Column(Float, default=0.95)
