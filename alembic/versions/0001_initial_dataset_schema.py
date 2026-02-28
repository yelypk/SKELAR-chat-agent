"""Initial dataset schema.

Revision ID: 0001_initial_dataset_schema
Revises:
Create Date: 2026-02-27
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_dataset_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dialogues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("intent_id", sa.String(length=128), nullable=False),
        sa.Column("hidden_root_cause", sa.String(length=1024), nullable=False),
        sa.Column("chaos_level", sa.String(length=16), nullable=False),
        sa.Column("support_seniority", sa.String(length=16), nullable=False),
        sa.Column("entropy_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("planned_mistakes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_mistakes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resolved_gt", sa.Boolean(), nullable=False),
        sa.Column("termination_reason_gt", sa.String(length=64), nullable=False),
        sa.Column("client_quality_score", sa.Integer(), nullable=True),
        sa.Column("transcript_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dialogues_run_id", "dialogues", ["run_id"], unique=False)
    op.create_index("ix_dialogues_intent_id", "dialogues", ["intent_id"], unique=False)
    op.create_index("ix_dialogues_chaos_level", "dialogues", ["chaos_level"], unique=False)

    op.create_table(
        "judge_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dialogue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("satisfaction", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("agent_mistakes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("termination_reason", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.String(length=4096), nullable=False),
        sa.Column("judge_raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dialogue_id"], ["dialogues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "judge_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dialogue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resolved_match", sa.Boolean(), nullable=False),
        sa.Column("termination_match", sa.Boolean(), nullable=False),
        sa.Column("validated_mistakes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("precision", sa.Float(), nullable=False),
        sa.Column("recall", sa.Float(), nullable=False),
        sa.Column("notes", sa.String(length=4096), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dialogue_id"], ["dialogues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("judge_validations")
    op.drop_table("judge_evaluations")
    op.drop_index("ix_dialogues_chaos_level", table_name="dialogues")
    op.drop_index("ix_dialogues_intent_id", table_name="dialogues")
    op.drop_index("ix_dialogues_run_id", table_name="dialogues")
    op.drop_table("dialogues")
