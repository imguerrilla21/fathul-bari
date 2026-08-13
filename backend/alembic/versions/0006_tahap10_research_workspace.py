"""tahap10 research workspace

Revision ID: 0006_tahap10_research_workspace
Revises: 0005_tahap9_knowledge_graph
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_tahap10_research_workspace"
down_revision = "0005_tahap9_knowledge_graph"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create research_projects table
    op.create_table(
        "research_projects",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=False, server_default="Peneliti Hadis"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_projects_status", "research_projects", ["status"])

    # 2. Create research_notes table
    op.create_table(
        "research_notes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hadith_id", sa.Uuid(as_uuid=True), sa.ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sharh_section_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_page_id", sa.String(length=64), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_notes_project_id", "research_notes", ["project_id"])

    # 3. Create research_annotations table
    op.create_table(
        "research_annotations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sharh_section_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hadith_id", sa.Uuid(as_uuid=True), sa.ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True),
        sa.Column("selected_text", sa.Text(), nullable=False),
        sa.Column("annotation_type", sa.String(length=32), nullable=False, server_default="NOTE"),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_annotations_project_id", "research_annotations", ["project_id"])

    # 4. Create research_citations table
    op.create_table(
        "research_citations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hadith_id", sa.Uuid(as_uuid=True), sa.ForeignKey("hadiths.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sharh_section_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sharh_sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("citation_text", sa.Text(), nullable=False),
        sa.Column("work_title", sa.String(length=255), nullable=False, server_default="Fathul Bari Syarah Shahih al-Bukhari"),
        sa.Column("author", sa.String(length=255), nullable=False, server_default="Al-Hafizh Ibnu Hajar al-Asqalani"),
        sa.Column("edition", sa.String(length=255), nullable=True, server_default="Dar al-Ma'rifah, Beirut"),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("printed_page", sa.Integer(), nullable=True),
        sa.Column("pdf_page", sa.Integer(), nullable=True),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_citations_project_id", "research_citations", ["project_id"])


def downgrade():
    op.drop_table("research_citations")
    op.drop_table("research_annotations")
    op.drop_table("research_notes")
    op.drop_table("research_projects")
