"""Add support seniority to dialogues.

Revision ID: 0002_add_support_seniority
Revises: 0001_initial_dataset_schema
Create Date: 2026-02-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_support_seniority"
down_revision = "0001_initial_dataset_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dialogues",
        sa.Column("support_seniority", sa.String(length=16), nullable=True),
    )
    op.execute("UPDATE dialogues SET support_seniority = 'unknown' WHERE support_seniority IS NULL")
    op.alter_column("dialogues", "support_seniority", nullable=False)


def downgrade() -> None:
    op.drop_column("dialogues", "support_seniority")
