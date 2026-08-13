import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, JSON, Numeric, DateTime, ForeignKey
from app.database import Base


class CanonicalHadithEntity(Base):
    """Model master untuk Hadis kanonikal (induk)."""
    __tablename__ = "canonical_hadiths_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_key = Column(String(255), unique=True, index=True)
    title = Column(Text, nullable=True)
    language = Column(String(10), default="ar")
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class HadithVariantEntity(Base):
    """Model riwayat hadis (varian) dengan matan dan sanad spesifik."""
    __tablename__ = "hadith_variants_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("canonical_hadiths_v2.id"), nullable=False, index=True)
    source_id = Column(String(36), nullable=True, index=True)
    
    arabic_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    variant_type = Column(String(40), nullable=True) # FULL, PARTIAL, MATN_VARIANT
    
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IsnadEntity(Base):
    """Model sanad yang menghubungkan urutan perawi."""
    __tablename__ = "isnads_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_variant_id = Column(String(36), ForeignKey("hadith_variants_v2.id"), nullable=False, index=True)
    
    extraction_method = Column(String(40), nullable=True)
    confidence = Column(Numeric(6, 5), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IsnadNodeEntity(Base):
    """Model node (perawi) di dalam sebuah sanad."""
    __tablename__ = "isnad_nodes_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    isnad_id = Column(String(36), ForeignKey("isnads_v2.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    
    narrator_entity_id = Column(String(36), nullable=True, index=True)
    surface_name = Column(Text, nullable=False)
    normalized_name = Column(Text, nullable=True)
    role = Column(String(30), nullable=True) # NARRATOR, COMPANION, PROPHET
    
    confidence = Column(Numeric(6, 5), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")


class IsnadEdgeEntity(Base):
    """Model edge relasi (guru-murid) antar node dalam sanad."""
    __tablename__ = "isnad_edges_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    isnad_id = Column(String(36), ForeignKey("isnads_v2.id"), nullable=False, index=True)
    
    from_node_id = Column(String(36), ForeignKey("isnad_nodes_v2.id"), nullable=False)
    to_node_id = Column(String(36), ForeignKey("isnad_nodes_v2.id"), nullable=False)
    
    transmission_term = Column(Text, nullable=True)
    edge_type = Column(String(30), nullable=True) # TEACHER_OF
    
    confidence = Column(Numeric(6, 5), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")


class NarratorAuthorityEntity(Base):
    """Model kanonikal untuk profil perawi."""
    __tablename__ = "narrator_authority_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(Text, nullable=False)
    arabic_name = Column(Text, nullable=True)
    kunya = Column(Text, nullable=True)
    nasab = Column(Text, nullable=True)
    nisbah = Column(Text, nullable=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    metadata_json = Column("metadata", JSON, default=dict)


class NarratorAliasEntity(Base):
    """Model alias variasi sebutan nama perawi."""
    __tablename__ = "narrator_aliases_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    narrator_id = Column(String(36), ForeignKey("narrator_authority_v2.id"), nullable=False, index=True)
    alias = Column(Text, nullable=False)
    normalized_alias = Column(Text, nullable=False)
    source = Column(String(50), nullable=True)
    confidence = Column(Numeric(6, 5), nullable=True)


class HadithReferenceEntity(Base):
    """Pemetaan referensi hadis ke koleksi spesifik (Bukhari, Muslim, dsb)."""
    __tablename__ = "hadith_cross_references_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("canonical_hadiths_v2.id"), nullable=False, index=True)
    collection_id = Column(String(36), nullable=False)
    book_id = Column(String(36), nullable=True)
    chapter_id = Column(String(36), nullable=True)
    
    hadith_number = Column(Text, nullable=True)
    edition = Column(Text, nullable=True)
    page = Column(Text, nullable=True)
    reference_label = Column(Text, nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")


class HadithGradingEntity(Base):
    """Model penilaian status hadis (Sahih, Hasan, dll)."""
    __tablename__ = "hadith_gradings_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("canonical_hadiths_v2.id"), nullable=False, index=True)
    grader_entity_id = Column(String(36), nullable=True)
    
    grading = Column(Text, nullable=False)
    grading_scope = Column(String(40), nullable=True)
    source_id = Column(String(36), nullable=True)
    evidence = Column(Text, nullable=True)
    
    confidence = Column(Numeric(6, 5), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")


class HadithCommentaryLinkEntity(Base):
    """Relasi antara Hadis dan Syarah (Fathul Bari)."""
    __tablename__ = "hadith_commentary_links_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hadith_id = Column(String(36), ForeignKey("canonical_hadiths_v2.id"), nullable=False, index=True)
    commentary_source_id = Column(String(36), nullable=False)
    chunk_id = Column(String(36), nullable=True)
    
    relation_type = Column(String(40), nullable=True) # DIRECT_COMMENTARY, LINGUISTIC_DISCUSSION
    evidence = Column(Text, nullable=True)
    confidence = Column(Numeric(6, 5), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED")


class SourceRawRecordEntity(Base):
    """Penyimpanan raw JSON dari sumber eksternal (Ahmad Sanusi API)."""
    __tablename__ = "source_raw_records_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=False, index=True)
    external_id = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    content_hash = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)


class SourceVersionEntity(Base):
    """Manajemen versi data source jika ada perubahan dari sumber asal."""
    __tablename__ = "source_versions_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=False, index=True)
    version_label = Column(Text, nullable=True)
    content_hash = Column(Text, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow)
