import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Boolean
from app.database import Base


class ResearchWorkspaceEntity(Base):
    """Model entitas ruang kerja riset hadis (Research Workspace Entity)."""
    __tablename__ = "research_workspaces_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), nullable=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="ACTIVE", index=True)  # ACTIVE, ARCHIVED, DELETED
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class WorkspaceMemberEntity(Base):
    """Model anggota kolaborasi workspace riset."""
    __tablename__ = "workspace_members_v2"

    workspace_id = Column(String(36), ForeignKey("research_workspaces_v2.id"), primary_key=True)
    user_id = Column(String(36), primary_key=True)
    role = Column(String(30), default="RESEARCHER", nullable=False)  # OWNER, RESEARCHER, REVIEWER, VIEWER
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class WorkspaceItemEntity(Base):
    """Model entitas item yang tersimpan di workspace."""
    __tablename__ = "workspace_items_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("research_workspaces_v2.id"), nullable=False, index=True)
    item_type = Column(String(40), nullable=False)  # HADITH, SHARH_CHUNK, SOURCE_PAGE, NOTE, FINDING
    entity_id = Column(String(36), nullable=False)
    position = Column(Integer, default=1)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SourceHighlightEntity(Base):
    """Model entitas highlight penandaan teks sumber."""
    __tablename__ = "source_highlights_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("research_workspaces_v2.id"), nullable=False, index=True)
    page_id = Column(String(36), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=True)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    selected_text = Column(Text, nullable=False)
    color = Column(String(30), default="yellow")
    note_id = Column(String(36), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class ResearchNoteEntity(Base):
    """Model catatan riset berbasis Markdown."""
    __tablename__ = "research_notes_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("research_workspaces_v2.id"), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("research_notes_v2.id"), nullable=True)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="markdown")
    note_type = Column(String(30), default="OBSERVATION")  # OBSERVATION, QUESTION, FINDING, QUOTE, SUMMARY
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ResearchFindingEntity(Base):
    """Model entitas temuan (*finding*) riset yang diverifikasi."""
    __tablename__ = "research_findings_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("research_workspaces_v2.id"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    statement = Column(Text, nullable=False)
    status = Column(String(30), default="DRAFT", index=True)  # DRAFT, SUPPORTED, REVIEW_REQUIRED, FINAL
    confidence = Column(Float, default=0.96)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class FindingEvidenceLink(Base):
    """Model relasi temuan riset dengan bukti sumber terverifikasi."""
    __tablename__ = "finding_evidence_links_v2"

    finding_id = Column(String(36), ForeignKey("research_findings_v2.id"), primary_key=True)
    evidence_id = Column(String(36), primary_key=True)
    support_type = Column(String(30), default="PRIMARY")  # PRIMARY, SECONDARY, CORROBORATING
