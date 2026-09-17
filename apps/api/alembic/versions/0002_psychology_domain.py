"""Add psychology domain metadata and safety fields.

Revision ID: 0002_psychology_domain
Revises: 0001_initial
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_psychology_domain"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "domain",
            sa.String(length=32),
            nullable=False,
            server_default="general",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "doc_type",
            sa.String(length=32),
            nullable=False,
            server_default="reference",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "audience",
            sa.String(length=32),
            nullable=False,
            server_default="public",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("assessment_code", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("assessment_version", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "access_level",
            sa.String(length=32),
            nullable=False,
            server_default="public",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "review_status",
            sa.String(length=32),
            nullable=False,
            server_default="draft",
        ),
    )
    op.create_index("ix_documents_domain", "documents", ["domain"])
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])
    op.create_index("ix_documents_audience", "documents", ["audience"])
    op.create_index("ix_documents_assessment_code", "documents", ["assessment_code"])
    op.create_index("ix_documents_access_level", "documents", ["access_level"])
    op.create_index("ix_documents_review_status", "documents", ["review_status"])
    op.create_index(
        "ix_documents_domain_audience_review",
        "documents",
        ["domain", "audience", "review_status", "created_at"],
    )
    op.create_index(
        "ix_documents_assessment_version",
        "documents",
        ["assessment_code", "assessment_version"],
    )

    op.add_column(
        "conversations",
        sa.Column(
            "mode",
            sa.String(length=32),
            nullable=False,
            server_default="psychoeducation",
        ),
    )
    op.create_index("ix_conversations_mode", "conversations", ["mode"])

    op.add_column(
        "messages",
        sa.Column(
            "safety_level",
            sa.String(length=32),
            nullable=False,
            server_default="normal",
        ),
    )

    op.add_column(
        "retrieval_events",
        sa.Column(
            "mode",
            sa.String(length=32),
            nullable=False,
            server_default="psychoeducation",
        ),
    )
    op.add_column(
        "retrieval_events",
        sa.Column(
            "filters_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "retrieval_events",
        sa.Column(
            "source_versions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("retrieval_events", "source_versions")
    op.drop_column("retrieval_events", "filters_json")
    op.drop_column("retrieval_events", "mode")
    op.drop_column("messages", "safety_level")
    op.drop_index("ix_conversations_mode", table_name="conversations")
    op.drop_column("conversations", "mode")
    op.drop_index("ix_documents_assessment_version", table_name="documents")
    op.drop_index("ix_documents_domain_audience_review", table_name="documents")
    op.drop_index("ix_documents_review_status", table_name="documents")
    op.drop_index("ix_documents_access_level", table_name="documents")
    op.drop_index("ix_documents_assessment_code", table_name="documents")
    op.drop_index("ix_documents_audience", table_name="documents")
    op.drop_index("ix_documents_doc_type", table_name="documents")
    op.drop_index("ix_documents_domain", table_name="documents")
    op.drop_column("documents", "review_status")
    op.drop_column("documents", "access_level")
    op.drop_column("documents", "assessment_version")
    op.drop_column("documents", "assessment_code")
    op.drop_column("documents", "audience")
    op.drop_column("documents", "doc_type")
    op.drop_column("documents", "domain")
