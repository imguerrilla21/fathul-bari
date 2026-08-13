import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, JSON, Numeric, DateTime, ForeignKey
from app.database import Base


class ArabicTokenEntity(Base):
    """Model token bahasa Arab untuk kebutuhan NLP (Arabic NLP Token Entity)."""
    __tablename__ = "arabic_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False, index=True)
    page_id = Column(String(36), nullable=True)
    chunk_id = Column(String(36), nullable=True, index=True)
    token_index = Column(Integer, nullable=False)
    
    surface = Column(Text, nullable=False)
    normalized = Column(Text, nullable=False, index=True)
    lemma = Column(Text, nullable=True, index=True)
    root = Column(Text, nullable=True, index=True)
    pos = Column(String(40), nullable=True)
    
    morphology = Column(JSON, default=dict)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)


class ArabicLexemeEntity(Base):
    """Model leksikal akar kata bahasa Arab (Arabic Lexeme Entity)."""
    __tablename__ = "arabic_lexemes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lemma = Column(Text, nullable=False, index=True)
    root = Column(Text, nullable=True, index=True)
    language = Column(String(10), default="ar")
    metadata_json = Column("metadata", JSON, default=dict)


class TextEntity(Base):
    """Model identitas entitas teks NLP (Named Entity)."""
    __tablename__ = "text_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(40), nullable=False, index=True) # PERSON, SCHOLAR, BOOK, TERM
    canonical_name = Column(Text, nullable=False)
    arabic_name = Column(Text, nullable=True)
    normalized_name = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)


class EntityMentionEntity(Base):
    """Model penyebutan entitas di dalam teks (Entity Mention)."""
    __tablename__ = "entity_mentions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String(36), ForeignKey("text_entities.id"), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=False, index=True)
    
    surface = Column(Text, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    confidence = Column(Numeric(6, 5), nullable=True)


class ArabicPhraseEntity(Base):
    """Model frasa Arab untuk Exact Search indexing."""
    __tablename__ = "arabic_phrases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(36), nullable=False, index=True)
    phrase = Column(Text, nullable=False)
    normalized_phrase = Column(Text, nullable=False, index=True)
    token_start = Column(Integer, nullable=True)
    token_end = Column(Integer, nullable=True)


class NLPJobEntity(Base):
    """Model pelacakan job NLP asynchronous."""
    __tablename__ = "nlp_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=True)
    job_type = Column(String(40), nullable=False) # NORMALIZE, TOKENIZE, NER
    status = Column(String(30), nullable=False, default="QUEUED") # QUEUED, RUNNING, COMPLETED, FAILED
    
    progress = Column(Numeric(6, 3), default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
