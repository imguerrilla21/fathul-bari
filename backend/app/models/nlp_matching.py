import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class Narrator(Base):
    """Model perawi/sanad (Narrator Entity)."""
    __tablename__ = "narrators"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(String(255), nullable=False, index=True)
    arabic_name = Column(String(255), nullable=False, index=True)
    kunya = Column(String(100), nullable=True)
    generation = Column(String(100), nullable=True)  # Sahabat, Tabi'in, Tabi'ut Tabi'in
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class NarratorAlias(Base):
    """Alias variasi penulisan nama perawi (e.g. أبو هريرة vs أبي هريرة vs عن هريرة)."""
    __tablename__ = "narrator_aliases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    narrator_id = Column(String(36), ForeignKey("narrators.id"), nullable=False, index=True)
    alias_arabic = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SanadChainLink(Base):
    """Graf transmisi sanad (narrator_a -> TRANSMITS_TO -> narrator_b)."""
    __tablename__ = "sanad_chain_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_narrator_id = Column(String(36), ForeignKey("narrators.id"), nullable=False, index=True)
    target_narrator_id = Column(String(36), ForeignKey("narrators.id"), nullable=False, index=True)
    transmission_term = Column(String(50), default="حدثنا")  # حدثنا, أخبرنا, عن, قال
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class HadithVariant(Base):
    """Model variasi redaksi/riwayat hadis (e.g. وفي رواية لمسلم)."""
    __tablename__ = "hadith_variants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("hadiths.id"), nullable=False, index=True)
    variant_source = Column(String(100), default="Muslim")  # Bukhari, Muslim, Tirmidhi, Ibn Hajar Quote
    arabic_text = Column(Text, nullable=False)
    translation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MatchExplanation(Base):
    """Model penjelasan rasionalitas pencocokan yang dapat dijelaskan (Explainable Match Rationale)."""
    __tablename__ = "match_explanations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("hadith_candidates.id"), nullable=False, index=True)
    hadith_id = Column(String(36), ForeignKey("hadiths.id"), nullable=True, index=True)
    explanation_json = Column(JSON, nullable=False)  # {"matn_overlap": 0.87, "narrator_match": True, "rationale_summary": "..."}
    mrr_score = Column(Float, default=1.0)
    ndcg_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
