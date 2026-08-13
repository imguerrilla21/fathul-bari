import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GraphNode(Base):
    """
    Representasi simpul (Node) dalam Knowledge Graph Fathul Bari & Bukhari.
    Tipe: 'hadith', 'collection', 'book', 'chapter', 'sharh_section', 'source_page', 'topic', 'person'.
    """
    __tablename__ = "graph_nodes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke edge
    outgoing_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )


class GraphEdge(Base):
    """
    Representasi sisi berarah (Edge) dalam Knowledge Graph dengan provenance audit lengkap.
    Tipe: 'IN_COLLECTION', 'BELONGS_TO_BOOK', 'BELONGS_TO_CHAPTER', 'EXPLAINED_BY', 
          'REFERENCES', 'RELATED_TO', 'LOCATED_IN', 'ABOUT_TOPIC', 'AUTHORED_BY', 'NEXT_SECTION'.
    """
    __tablename__ = "graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_node_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    relation_type: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    source_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
