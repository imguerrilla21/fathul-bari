import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class ResearchRun(Base):
    """Model pencatatan eksekusi riset asisten syarah (Research Assistant Execution Run)."""
    __tablename__ = "research_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    mode = Column(String(30), default="RESEARCH")  # RINGKAS, DEEP, RESEARCH
    source_scope = Column(JSON, default=list)       # ["FATH_AL_BARI", "BUKHARI"]
    status = Column(String(30), default="COMPLETED")
    overall_confidence = Column(String(30), default="HIGH")  # VERY_HIGH, HIGH, MEDIUM, LOW, INSUFFICIENT
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class EvidenceUnit(Base):
    """Unit bukti sumber terverifikasi asli (Evidence Unit EV-001)."""
    __tablename__ = "evidence_units"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id"), nullable=False, index=True)
    evidence_code = Column(String(20), nullable=False)  # EV-001, EV-002
    source = Column(String(100), default="FATH_AL_BARI")
    volume = Column(Integer, default=1)
    page = Column(Integer, default=45)
    section_id = Column(String(36), nullable=True)
    hadith_id = Column(String(36), nullable=True)
    text = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.95)
    evidence_type = Column(String(50), default="PRIMARY_SHARH")  # PRIMARY_SHARH, HADITH_TEXT, CROSS_REF, SCHOLAR_QUOTE
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EvidenceClaim(Base):
    """Klaim faktual jawaban yang terpetakan ke unit bukti (Claim Entity)."""
    __tablename__ = "evidence_claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("research_runs.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    support_score = Column(Float, default=0.96)
    is_supported = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ClaimCitation(Base):
    """Sitasi tervalidasi yang menautkan klaim ke bukti sumber asli (Citation Entity)."""
    __tablename__ = "claim_citations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("evidence_claims.id"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_units.id"), nullable=False, index=True)
    source_volume = Column(Integer, default=1)
    page_number = Column(Integer, default=45)
    citation_badge = Column(String(50), default="[FB Vol 1: Page 45]")
    validated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SharhArgumentNode(Base):
    """Node struktur argumen syarah (Argument Node & Scholar Attribution Graph)."""
    __tablename__ = "sharh_argument_nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id = Column(String(36), ForeignKey("sharh_sections.id"), nullable=True, index=True)
    argument_type = Column(String(50), default="CLAIM")  # DEFINITION, CLAIM, EVIDENCE, OPINION, OBJECTION, RESPONSE, PREFERENCE, CONCLUSION
    scholar_name = Column(String(100), default="Ibnu Hajar al-Asqalani")
    attribution_type = Column(String(30), default="IBN_HAJAR_SAYS")  # IBN_HAJAR_SAYS, IBN_HAJAR_QUOTES
    quoted_scholar = Column(String(100), nullable=True)               # Al-Nawawi, Al-Khattabi, Al-Qurtubi
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.95)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
