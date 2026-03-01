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

JUDGE_TRAINING_SELECT_SQL = """
SELECT
    d.intent_id,
    d.client_quality_score,
    d.transcript_json
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
ORDER BY d.created_at, d.id
"""


def export_judge_training_csv(dsn: str, after_dialogue_id: str, output_csv: Path) -> int:
    anchor_uuid = parse_anchor_uuid(after_dialogue_id)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(dsn, future=True)
    anchor = resolve_anchor_dialogue(engine, anchor_uuid)

    rows = iter_dialogues_after_anchor(
        engine,
        anchor_created_at=anchor["created_at"],
        anchor_id=str(anchor_uuid),
        select_sql=JUDGE_TRAINING_SELECT_SQL,
    )

    count = 0
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["intent", "client_quality_score", "transcript"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "intent": row["intent_id"],
                    "client_quality_score": row["client_quality_score"],
                    "transcript": json_text(row["transcript_json"]),
                }
            )
            count += 1
    return count
