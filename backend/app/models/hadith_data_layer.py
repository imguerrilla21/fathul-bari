import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class HadithSource(Base):
    """Model entitas penyedia sumber asal data hadis (Source Metadata Entity)."""
    __tablename__ = "hadith_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    provider = Column(String(100), default="ahmad_sanusi", nullable=False)
    source_type = Column(String(50), default="API", nullable=False)
    base_url = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class HadithCollection(Base):
    """Model entitas koleksi kitab hadis (e.g. Sahih al-Bukhari, Sahih Muslim)."""
    __tablename__ = "hadith_collections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("hadith_sources.id"), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    name_ar = Column(Text, nullable=True)
    name_id = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class HadithBook(Base):
    """Model entitas kitab/bab internal dalam koleksi (Book Entity)."""
    __tablename__ = "hadith_books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String(36), ForeignKey("hadith_collections.id"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)
    number = Column(Integer, nullable=True)
    name_ar = Column(Text, nullable=True)
    name_id = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)


class HadithEntity(Base):
    """Tabel utama indeks hadis lokal terverifikasi (Local Research Index Canonical Hadith Entity)."""
    __tablename__ = "hadith_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String(36), ForeignKey("hadith_books.id"), nullable=True, index=True)
    external_id = Column(String(255), unique=True, index=True, nullable=False)  # ahmad-sanusi:bukhari:1
    hadith_number = Column(String(100), nullable=True, index=True)
    arabic_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True, index=True)
    search_text = Column(Text, nullable=True)
    narrator_text = Column(Text, nullable=True)
    grade = Column(String(100), default="Sahih")
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    source_url = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class HadithVariantEntity(Base):
    """Model variasi riwayah/lafaz hadis (Hadith Variant Entity)."""
    __tablename__ = "hadith_variant_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("hadith_entities.id"), nullable=False, index=True)
    variant_type = Column(String(50), default="RIWAYAH")
    arabic_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True)
    source_collection = Column(String(100), nullable=True)
    source_reference = Column(String(100), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class HadithReferenceEntity(Base):
    """Model rujukan silang antar hadis (Hadith Cross Reference Entity)."""
    __tablename__ = "hadith_reference_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("hadith_entities.id"), nullable=False, index=True)
    target_collection = Column(String(100), nullable=False)
    target_hadith_number = Column(String(100), nullable=False)
    reference_type = Column(String(50), default="EXPLICIT")  # EXPLICIT, INFERRED, MANUAL, MODEL_SUGGESTED
    confidence = Column(Float, default=1.0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class HadithIngestionJob(Base):
    """Model entitas pelacak job batch ingestion (Ingestion Job Tracking Entity)."""
    __tablename__ = "hadith_ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(100), default="ahmad_sanusi", nullable=False)
    collection = Column(String(100), nullable=False, index=True)
    status = Column(String(30), default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
