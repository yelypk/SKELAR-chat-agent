from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


DEFAULT_DSN = "postgresql+psycopg://app:app@localhost:5432/skelar_chat_agent"


def _json_text(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return json.dumps(parsed, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def _load_dsn(explicit_dsn: str | None) -> str:
    if explicit_dsn:
        return explicit_dsn
    load_dotenv()
    return os.getenv("POSTGRES_DSN", DEFAULT_DSN)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate judge-visible training CSV for dialogues after a given dialogue_id "
            "excluding max_turns terminations."
        )
    )
    parser.add_argument(
        "--after-dialogue-id",
        required=True,
        help="Anchor dialogue UUID. Export includes dialogues strictly after this one.",
    )
    parser.add_argument(
        "--dsn",
        default=None,
        help="SQLAlchemy DSN. If omitted, uses POSTGRES_DSN from .env.",
    )
    parser.add_argument(
        "--output-csv",
        default="dataset_outputs/judge_training_dataset.csv",
        help="Output CSV path.",
    )
    return parser.parse_args()


def export_judge_training_csv(dsn: str, after_dialogue_id: str, output_csv: Path) -> int:
    try:
        anchor_uuid = UUID(after_dialogue_id)
    except ValueError as exc:
        raise ValueError("--after-dialogue-id must be a valid UUID.") from exc

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(dsn, future=True)

    with engine.begin() as conn:
        anchor_row = conn.execute(
            text(
                """
                SELECT id, created_at
                FROM dialogues
                WHERE CAST(id AS TEXT) = :anchor_id
                """
            ),
            {"anchor_id": str(anchor_uuid)},
        ).mappings().first()
        if anchor_row is None:
            raise ValueError(f"Anchor dialogue_id not found: {after_dialogue_id}")

        rows = conn.execute(
            text(
                """
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
            ),
            {
                "anchor_created_at": anchor_row["created_at"],
                "anchor_id": str(anchor_uuid),
            },
        ).mappings().all()

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["intent", "client_quality_score", "transcript"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "intent": row["intent_id"],
                    "client_quality_score": row["client_quality_score"],
                    "transcript": _json_text(row["transcript_json"]),
                }
            )
    return len(rows)


def main() -> None:
    args = _parse_args()
    dsn = _load_dsn(args.dsn)
    count = export_judge_training_csv(
        dsn=dsn,
        after_dialogue_id=args.after_dialogue_id,
        output_csv=Path(args.output_csv),
    )
    print(f"Exported {count} rows to: {args.output_csv}")


if __name__ == "__main__":
    main()
