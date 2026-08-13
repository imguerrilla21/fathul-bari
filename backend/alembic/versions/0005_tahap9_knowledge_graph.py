"""tahap9 knowledge graph

Revision ID: 0005_tahap9_knowledge_graph
Revises: 0004_tahap8_hybrid_search
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_tahap9_knowledge_graph"
down_revision = "0004_tahap8_hybrid_search"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create graph_nodes table
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_graph_nodes_node_type", "graph_nodes", ["node_type"])
    op.create_index("ix_graph_nodes_entity_id", "graph_nodes", ["entity_id"])

    # 2. Create graph_edges table
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_node_id", sa.Uuid(as_uuid=True), sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_node_id", sa.Uuid(as_uuid=True), sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(length=48), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_graph_edges_source_node_id", "graph_edges", ["source_node_id"])
    op.create_index("ix_graph_edges_target_node_id", "graph_edges", ["target_node_id"])
    op.create_index("ix_graph_edges_relation_type", "graph_edges", ["relation_type"])
    op.create_index("ix_graph_edges_verified", "graph_edges", ["verified"])


def downgrade():
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
