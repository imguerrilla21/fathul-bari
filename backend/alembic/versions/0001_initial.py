"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text()),
        sa.Column("license", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("total_expected", sa.Integer()),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "hadiths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_number", sa.Integer(), nullable=False),
        sa.Column("arabic_text", sa.Text()),
        sa.Column("translation", sa.Text()),
        sa.Column("api_endpoint", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.UniqueConstraint("collection_id", "external_number", name="uq_hadith_collection_number"),
    )
    op.create_index("ix_hadiths_collection_id", "hadiths", ["collection_id"])
    op.create_index("ix_hadiths_source_id", "hadiths", ["source_id"])
    op.create_index("ix_hadiths_content_hash", "hadiths", ["content_hash"])

    op.create_table(
        "sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("collection_slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )

    op.create_table(
        "sharh_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("work_slug", sa.String(100), nullable=False),
        sa.Column("volume", sa.Integer()),
        sa.Column("page", sa.Integer()),
        sa.Column("section_order", sa.Integer()),
        sa.Column("title", sa.Text()),
        sa.Column("arabic_text", sa.Text()),
        sa.Column("translation", sa.Text()),
        sa.Column("extraction_status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sharh_sections_work_slug", "sharh_sections", ["work_slug"])

    op.create_table(
        "hadith_sharh_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hadith_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sharh_section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_method", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.ForeignKeyConstraint(["sharh_section_id"], ["sharh_sections.id"]),
        sa.UniqueConstraint("hadith_id", "sharh_section_id", name="uq_hadith_sharh_link"),
    )
    op.create_index("ix_hadith_sharh_links_hadith_id", "hadith_sharh_links", ["hadith_id"])
    op.create_index("ix_hadith_sharh_links_sharh_section_id", "hadith_sharh_links", ["sharh_section_id"])


def downgrade():
    op.drop_table("hadith_sharh_links")
    op.drop_table("sharh_sections")
    op.drop_table("sync_runs")
    op.drop_index("ix_hadiths_content_hash", table_name="hadiths")
    op.drop_index("ix_hadiths_source_id", table_name="hadiths")
    op.drop_index("ix_hadiths_collection_id", table_name="hadiths")
    op.drop_table("hadiths")
    op.drop_table("collections")
    op.drop_table("sources")
