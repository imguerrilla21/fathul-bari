"""tahap6 source viewer and audit trail

Revision ID: 0003_tahap6_source_audit
Revises: 0002_tahap3_sharh_pipeline
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_tahap6_source_audit"
down_revision = "0002_tahap3_sharh_pipeline"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add source_document_path and page_image_path to sharh_sections
    op.add_column("sharh_sections", sa.Column("source_document_path", sa.Text(), nullable=True))
    op.add_column("sharh_sections", sa.Column("page_image_path", sa.Text(), nullable=True))

    # 2. Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("actor", sa.String(length=100), server_default="system", nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("before_state", sa.Text(), nullable=True),
        sa.Column("after_state", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_column("sharh_sections", "page_image_path")
    op.drop_column("sharh_sections", "source_document_path")
