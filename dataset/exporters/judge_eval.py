from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import create_engine

from dataset.exporters.base import (
    iter_dialogues_after_anchor,
    json_text,
    parse_anchor_uuid,
    resolve_anchor_dialogue,
)

JUDGE_EVAL_SELECT_SQL = """
WITH filtered_dialogues AS (
    SELECT d.id, d.created_at
    FROM dialogues AS d
    WHERE
        d.termination_reason_gt <> 'max_turns'
        AND (
            d.created_at > :anchor_created_at
            OR (
                d.created_at = :anchor_created_at
                AND CAST(d.id AS TEXT) > :anchor_id
            )
        )
)
SELECT
    fd.id AS dialogue_id,
    je.resolved,
    je.satisfaction,
    je.quality_score,
    je.agent_mistakes,
    je.termination_reason,
    je.rationale,
    jv.resolved_match,
    jv.termination_match,
    jv.validated_mistakes,
    jv.precision,
    jv.recall,
    jv.notes
FROM filtered_dialogues AS fd
LEFT JOIN judge_evaluations AS je ON je.dialogue_id = fd.id
LEFT JOIN judge_validations AS jv ON jv.dialogue_id = fd.id
ORDER BY fd.created_at, fd.id
"""


def export_judge_results_csv(dsn: str, after_dialogue_id: str, output_csv: Path) -> int:
    anchor_uuid = parse_anchor_uuid(after_dialogue_id)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(dsn, future=True)
    anchor = resolve_anchor_dialogue(engine, anchor_uuid)

    rows = iter_dialogues_after_anchor(
        engine,
        anchor_created_at=anchor["created_at"],
        anchor_id=str(anchor_uuid),
        select_sql=JUDGE_EVAL_SELECT_SQL,
    )

    count = 0
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dialogue_id",
                "resolved",
                "satisfaction",
                "quality_score",
                "agent_mistakes",
                "termination_reason",
                "rationale",
                "resolved_match",
                "termination_match",
                "validated_mistakes",
                "precision",
                "recall",
                "validation_notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "dialogue_id": row["dialogue_id"],
                    "resolved": row["resolved"],
                    "satisfaction": row["satisfaction"],
                    "quality_score": row["quality_score"],
                    "agent_mistakes": json_text(row["agent_mistakes"]),
                    "termination_reason": row["termination_reason"],
                    "rationale": row["rationale"],
                    "resolved_match": row["resolved_match"],
                    "termination_match": row["termination_match"],
                    "validated_mistakes": json_text(row["validated_mistakes"]),
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "validation_notes": row["notes"],
                }
            )
            count += 1
    return count
