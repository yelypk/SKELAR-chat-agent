from __future__ import annotations

import argparse
from pathlib import Path

from dataset.exporters.base import load_dsn
from dataset.exporters.judge_eval import export_judge_results_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export judge outputs and evaluation metrics for dialogues after a given "
            "dialogue_id excluding max_turns terminations."
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
        default="dataset_outputs/judge_results_and_eval.csv",
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    dsn = load_dsn(args.dsn)
    count = export_judge_results_csv(
        dsn=dsn,
        after_dialogue_id=args.after_dialogue_id,
        output_csv=Path(args.output_csv),
    )
    print(f"Exported {count} rows to: {args.output_csv}")


if __name__ == "__main__":
    main()
