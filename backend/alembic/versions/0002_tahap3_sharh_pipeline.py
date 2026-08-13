"""tahap3 sharh pipeline upgrade

Revision ID: 0002_tahap3_sharh_pipeline
Revises: 0001_initial
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_tahap3_sharh_pipeline"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Columns for sharh_sections
    op.add_column("sharh_sections", sa.Column("pdf_page", sa.Integer(), nullable=True))
    op.add_column("sharh_sections", sa.Column("printed_page", sa.Integer(), nullable=True))
    op.add_column("sharh_sections", sa.Column("normalized_text", sa.Text(), nullable=True))
    op.add_column("sharh_sections", sa.Column("source_file", sa.Text(), nullable=True))
    op.add_column("sharh_sections", sa.Column("source_hash", sa.String(64), nullable=True))
    op.create_index("ix_sharh_sections_source_hash", "sharh_sections", ["source_hash"])

    # Columns for hadith_sharh_links
    op.add_column("hadith_sharh_links", sa.Column("review_status", sa.String(30), server_default="pending", nullable=False))
    op.add_column("hadith_sharh_links", sa.Column("evidence", sa.Text(), nullable=True))
    op.add_column("hadith_sharh_links", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_hadith_sharh_links_review_status", "hadith_sharh_links", ["review_status"])


def downgrade():
    op.drop_index("ix_hadith_sharh_links_review_status", table_name="hadith_sharh_links")
    op.drop_column("hadith_sharh_links", "created_at")
    op.drop_column("hadith_sharh_links", "evidence")
    op.drop_column("hadith_sharh_links", "review_status")

    op.drop_index("ix_sharh_sections_source_hash", table_name="sharh_sections")
    op.drop_column("sharh_sections", "source_hash")
    op.drop_column("sharh_sections", "source_file")
    op.drop_column("sharh_sections", "normalized_text")
    op.drop_column("sharh_sections", "printed_page")
    op.drop_column("sharh_sections", "pdf_page")
