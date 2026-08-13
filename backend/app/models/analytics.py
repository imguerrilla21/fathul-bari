import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON
from app.database import Base


class EvaluationQuery(Base):
    """Dataset query standar (Golden Dataset) untuk pengujian retrieval dan RAG."""
    __tablename__ = "evaluation_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    category = Column(String, default="General")  # Direct Hadith, Conceptual, Arabic, Cross-reference, etc.
    expected_hadith_ids = Column(JSON, default=list)  # List[int] ID hadis yang diharapkan
    expected_sharh_ids = Column(JSON, default=list)   # List[int] ID section syarah yang diharapkan
    expected_source_ids = Column(JSON, default=list)  # List[int] ID source yang diharapkan
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EvaluationRun(Base):
    """Hasil eksekusi benchmark pengujian retrieval & RAG."""
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    query_count = Column(Integer, default=0)
    recall_at_1 = Column(Float, default=0.0)
    recall_at_5 = Column(Float, default=0.0)
    recall_at_10 = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)
    ndcg = Column(Float, default=0.0)
    precision_k = Column(Float, default=0.0)
    groundedness_score = Column(Float, default=0.0)
    citation_integrity_score = Column(Float, default=0.0)
    details_json = Column(JSON, default=dict)


class QualityIssue(Base):
    """Isu & bendera kualitas otomatis (Data Quality Flags)."""
    __tablename__ = "quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_type = Column(String, index=True)  # missing_source_page, low_confidence, conflicting_review, duplicate_section, etc.
    severity = Column(String, default="warning")  # critical, warning, review
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String, nullable=True)  # hadith, sharh, source, citation, link
    target_id = Column(Integer, nullable=True)
    status = Column(String, default="open")  # open, resolved, ignored
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
