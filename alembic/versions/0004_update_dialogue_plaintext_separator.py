"""Update plaintext dialogue view separator.

Revision ID: 0004_dialogue_text_sep
Revises: 0003_add_dialogue_text_view
Create Date: 2026-02-28
"""
from __future__ import annotations

from alembic import op


revision = "0004_dialogue_text_sep"
down_revision = "0003_add_dialogue_text_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW dialogue_plaintext_view AS
        SELECT
            d.id AS dialogue_id,
            d.run_id,
            d.intent_id,
            d.termination_reason_gt,
            d.created_at,
            STRING_AGG(
                CONCAT(turn_item.turn->>'speaker', ': ', turn_item.turn->>'utterance'),
                E'\\n\\n=====\\n\\n'
                ORDER BY turn_item.turn_order
            ) AS dialogue_text
        FROM dialogues AS d
        CROSS JOIN LATERAL JSONB_ARRAY_ELEMENTS(d.transcript_json) WITH ORDINALITY
            AS turn_item(turn, turn_order)
        GROUP BY d.id, d.run_id, d.intent_id, d.termination_reason_gt, d.created_at;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW dialogue_plaintext_view AS
        SELECT
            d.id AS dialogue_id,
            d.run_id,
            d.intent_id,
            d.termination_reason_gt,
            d.created_at,
            STRING_AGG(
                CONCAT(turn_item.turn->>'speaker', ': ', turn_item.turn->>'utterance'),
                E'\\n'
                ORDER BY turn_item.turn_order
            ) AS dialogue_text
        FROM dialogues AS d
        CROSS JOIN LATERAL JSONB_ARRAY_ELEMENTS(d.transcript_json) WITH ORDINALITY
            AS turn_item(turn, turn_order)
        GROUP BY d.id, d.run_id, d.intent_id, d.termination_reason_gt, d.created_at;
        """
    )
