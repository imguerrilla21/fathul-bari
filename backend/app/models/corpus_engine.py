import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class HadithCandidate(Base):
    """Model kandidat hadis yang terdeteksi dari teks Fathul Bari (Hadith Candidate Entity)."""
    __tablename__ = "hadith_candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_page_id = Column(String(36), ForeignKey("source_pages.id"), nullable=True, index=True)
    section_id = Column(String(36), ForeignKey("sharh_sections.id"), nullable=True, index=True)
    reference_text = Column(Text, nullable=True)
    reference_number = Column(Integer, nullable=True, index=True)
    matn_text = Column(Text, nullable=True)
    narrator = Column(String(255), nullable=True)
    detector_confidence = Column(Float, default=0.90)
    status = Column(String(30), default="MATCHED", index=True)  # DETECTED, MATCHED, REVIEW, VERIFIED, REJECTED
    rejection_reason = Column(String(100), nullable=True)      # WRONG_HADITH, WRONG_MATN, WRONG_NARRATOR, FALSE_DETECTION, OCR_ERROR, DUPLICATE
    reviewer_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class CandidateMatchScore(Base):
    """Rincian komponen skor pencocokan multi-faktor (Reference, Lexical, Semantic, Narrator, Chapter)."""
    __tablename__ = "candidate_match_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("hadith_candidates.id"), nullable=False, index=True)
    hadith_id = Column(String(36), ForeignKey("hadiths.id"), nullable=True, index=True)
    hadith_number = Column(Integer, nullable=True)
    reference_score = Column(Float, default=0.0)
    lexical_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    narrator_score = Column(Float, default=0.0)
    chapter_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class GoldenCorpusItem(Base):
    """Item acuan korpus terverifikasi manual untuk pengujian regresi (Golden Corpus)."""
    __tablename__ = "golden_corpus_items"

    id = Column(Integer, primary_key=True, index=True)
    hadith_number = Column(Integer, nullable=False, index=True)
    volume = Column(Integer, default=1, index=True)
    page_number = Column(Integer, nullable=True)
    expected_sharh_title = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
