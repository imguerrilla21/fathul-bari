import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class BibliographicSourceEntity(Base):
    """Model sumber bibliografi fisik/digital (Bibliographic Source Entity)."""
    __tablename__ = "bibliographic_sources_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String(40), default="SHARH", nullable=False)  # BOOK, HADITH, SHARH, ARTICLE
    title = Column(Text, nullable=False)
    subtitle = Column(Text, nullable=True)
    language = Column(String(20), default="ar")
    publisher = Column(Text, default="Dar al-Ma'rifah")
    publication_place = Column(Text, default="Beirut")
    publication_year = Column(String(30), default="1379 H")
    edition = Column(Text, default="Dar al-Ma'rifah Edition")
    isbn = Column(String(50), nullable=True)
    doi = Column(String(100), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class AuthorEntity(Base):
    """Model pengarang/ulama sumber (Author Authority Entity)."""
    __tablename__ = "authors_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(Text, nullable=False)  # Ibn Hajar al-'Asqalani
    arabic_name = Column(Text, nullable=True)      # أحمد بن علي بن حجر العسقلاني
    transliterated_name = Column(Text, nullable=True)
    nisbah = Column(Text, default="al-Asqalani")
    birth_year = Column(String(30), default="773 H")
    death_year = Column(String(30), default="852 H")
    metadata_json = Column(JSON, default=dict)


class BibliographicSourceAuthorLink(Base):
    """Model relasi sumber bibliografi dengan penulis."""
    __tablename__ = "bibliographic_source_authors_v2"

    source_id = Column(String(36), ForeignKey("bibliographic_sources_v2.id"), primary_key=True)
    author_id = Column(String(36), ForeignKey("authors_v2.id"), primary_key=True)
    role = Column(String(40), default="author", primary_key=True)  # author, editor, translator, commentator
    author_order = Column(Integer, default=1)


class SourceEditionEntity(Base):
    """Model edisi cetakan fisik sumber (Source Edition Entity)."""
    __tablename__ = "source_editions_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bibliographic_source_id = Column(String(36), ForeignKey("bibliographic_sources_v2.id"), nullable=False, index=True)
    edition_label = Column(Text, default="Dar al-Ma'rifah 1379 H Edition")
    publisher = Column(Text, default="Dar al-Ma'rifah")
    publication_place = Column(Text, default="Beirut")
    publication_year = Column(String(30), default="1379 H")
    total_volumes = Column(Integer, default=13)
    metadata_json = Column(JSON, default=dict)


class ScholarlyCitationEntity(Base):
    """Model rekod sitasi ilmiah (Scholarly Citation Entity)."""
    __tablename__ = "scholarly_citations_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), nullable=True, index=True)
    bibliographic_source_id = Column(String(36), ForeignKey("bibliographic_sources_v2.id"), nullable=False, index=True)
    edition_id = Column(String(36), ForeignKey("source_editions_v2.id"), nullable=True)
    page_id = Column(String(36), nullable=True)
    chunk_id = Column(String(36), nullable=True)
    locator_json = Column(JSON, default=dict)  # {"volume": 1, "printed_page": 45, "pdf_page": 67}
    citation_label = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class ResearchDocumentEntity(Base):
    """Model dokumen ilmiah hasil riset (Research Document Entity)."""
    __tablename__ = "research_documents_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), nullable=False, index=True)
    title = Column(Text, nullable=False)
    content_json = Column(JSON, default=dict)
    citation_style = Column(String(50), default="ISLAMIC_TRADITIONAL")  # ISLAMIC_TRADITIONAL, CHICAGO, APA
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
