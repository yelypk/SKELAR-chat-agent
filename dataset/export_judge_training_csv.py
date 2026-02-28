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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export two CSV files for judge training/evaluation using dialogues after "
            "a specific dialogue_id and excluding max_turns terminations."
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
        "--output-dir",
        default="dataset_outputs",
        help="Directory where output CSV files will be written.",
    )
    parser.add_argument(
        "--judge-input-csv",
        default="judge_training_dataset.csv",
        help="Filename for judge-visible input dataset CSV.",
    )
    parser.add_argument(
        "--judge-results-csv",
        default="judge_results_and_eval.csv",
        help="Filename for judge outputs + evaluation CSV.",
    )
    return parser.parse_args()


def _load_dsn(explicit_dsn: str | None) -> str:
    if explicit_dsn:
        return explicit_dsn
    load_dotenv()
    return os.getenv("POSTGRES_DSN", DEFAULT_DSN)


def export_judge_csvs(
    dsn: str,
    after_dialogue_id: str,
    output_dir: Path,
    judge_input_csv: str,
    judge_results_csv: str,
) -> tuple[Path, Path, int]:
    try:
        anchor_uuid = UUID(after_dialogue_id)
    except ValueError as exc:
        raise ValueError("--after-dialogue-id must be a valid UUID.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    judge_input_path = output_dir / judge_input_csv
    judge_results_path = output_dir / judge_results_csv

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
                WITH filtered_dialogues AS (
                    SELECT
                        d.id,
                        d.intent_id,
                        d.client_quality_score,
                        d.transcript_json,
                        d.created_at
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
                    fd.intent_id,
                    fd.client_quality_score,
                    fd.transcript_json,
                    fd.created_at,
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
            ),
            {
                "anchor_created_at": anchor_row["created_at"],
                "anchor_id": str(anchor_uuid),
            },
        ).mappings().all()

    with judge_input_path.open("w", encoding="utf-8", newline="") as f:
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

    with judge_results_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
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
                    "agent_mistakes": _json_text(row["agent_mistakes"]),
                    "termination_reason": row["termination_reason"],
                    "rationale": row["rationale"],
                    "resolved_match": row["resolved_match"],
                    "termination_match": row["termination_match"],
                    "validated_mistakes": _json_text(row["validated_mistakes"]),
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "validation_notes": row["notes"],
                }
            )

    return judge_input_path, judge_results_path, len(rows)


def main() -> None:
    args = _parse_args()
    dsn = _load_dsn(args.dsn)
    input_path, results_path, row_count = export_judge_csvs(
        dsn=dsn,
        after_dialogue_id=args.after_dialogue_id,
        output_dir=Path(args.output_dir),
        judge_input_csv=args.judge_input_csv,
        judge_results_csv=args.judge_results_csv,
    )
    print(f"Exported {row_count} dialogues.")
    print(f"Judge-visible training CSV: {input_path}")
    print(f"Judge results/evaluation CSV: {results_path}")


if __name__ == "__main__":
    main()
