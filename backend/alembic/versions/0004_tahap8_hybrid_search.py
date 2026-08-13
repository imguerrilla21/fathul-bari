"""tahap8 hybrid search engine

Revision ID: 0004_tahap8_hybrid_search
Revises: 0003_tahap6_source_audit
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_tahap8_hybrid_search"
down_revision = "0003_tahap6_source_audit"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("sharh_section_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sharh_sections.id", ondelete="CASCADE"), nullable=True),
        sa.Column("hadith_id", sa.Uuid(as_uuid=True), sa.ForeignKey("hadiths.id", ondelete="CASCADE"), nullable=True),
        sa.Column("chunk_type", sa.String(length=50), nullable=False, server_default="sharh_section"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="ar"),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("pdf_page", sa.Integer(), nullable=True),
        sa.Column("printed_page", sa.Integer(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_chunks_sharh_section_id", "document_chunks", ["sharh_section_id"])
    op.create_index("ix_document_chunks_hadith_id", "document_chunks", ["hadith_id"])
    op.create_index("ix_document_chunks_chunk_type", "document_chunks", ["chunk_type"])
    op.create_index("ix_document_chunks_language", "document_chunks", ["language"])
    op.create_index("ix_document_chunks_volume", "document_chunks", ["volume"])
    op.create_index("ix_document_chunks_printed_page", "document_chunks", ["printed_page"])
    op.create_index("ix_document_chunks_verified", "document_chunks", ["verified"])

    # 2. Create retrieval_logs table
    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("query_language", sa.String(length=20), server_default="id", nullable=False),
        sa.Column("retrieval_mode", sa.String(length=30), server_default="research", nullable=False),
        sa.Column("retrieved_chunks_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("retrieved_chunks", sa.Text(), nullable=True),
        sa.Column("reranked_chunks", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_retrieval_logs_query_language", "retrieval_logs", ["query_language"])
    op.create_index("ix_retrieval_logs_retrieval_mode", "retrieval_logs", ["retrieval_mode"])
    op.create_index("ix_retrieval_logs_created_at", "retrieval_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_retrieval_logs_created_at", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_retrieval_mode", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_query_language", table_name="retrieval_logs")
    op.drop_table("retrieval_logs")

    op.drop_index("ix_document_chunks_verified", table_name="document_chunks")
    op.drop_index("ix_document_chunks_printed_page", table_name="document_chunks")
    op.drop_index("ix_document_chunks_volume", table_name="document_chunks")
    op.drop_index("ix_document_chunks_language", table_name="document_chunks")
    op.drop_index("ix_document_chunks_chunk_type", table_name="document_chunks")
    op.drop_index("ix_document_chunks_hadith_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_sharh_section_id", table_name="document_chunks")
    op.drop_table("document_chunks")
