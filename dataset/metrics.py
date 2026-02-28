from __future__ import annotations

import json
from collections import Counter

from sqlalchemy import create_engine, text


def compute_balance_report(dsn: str, run_id: str | None = None) -> dict:
    engine = create_engine(dsn, future=True)
    where = "WHERE d.run_id = :run_id" if run_id else ""
    params = {"run_id": run_id} if run_id else {}

    report = {
        "dialogues_total": 0,
        "by_intent": {},
        "by_chaos_level": {},
        "by_resolved_gt": {},
        "by_termination_reason_gt": {},
        "by_client_quality_score": {},
        "by_judge_satisfaction": {},
        "mistake_frequency_planned": {},
        "mistake_frequency_observed": {},
        "mistake_frequency_validated": {},
    }

    with engine.begin() as conn:
        report["dialogues_total"] = conn.execute(
            text(f"SELECT COUNT(*) FROM dialogues d {where}"),
            params,
        ).scalar_one()

        for key, sql in (
            ("by_intent", f"SELECT intent_id, COUNT(*) FROM dialogues d {where} GROUP BY intent_id"),
            (
                "by_chaos_level",
                f"SELECT chaos_level, COUNT(*) FROM dialogues d {where} GROUP BY chaos_level",
            ),
            (
                "by_resolved_gt",
                f"SELECT resolved_gt::text, COUNT(*) FROM dialogues d {where} GROUP BY resolved_gt::text",
            ),
            (
                "by_termination_reason_gt",
                f"SELECT termination_reason_gt, COUNT(*) FROM dialogues d {where} GROUP BY termination_reason_gt",
            ),
            (
                "by_client_quality_score",
                f"SELECT COALESCE(client_quality_score::text, 'null'), COUNT(*) "
                f"FROM dialogues d {where} GROUP BY COALESCE(client_quality_score::text, 'null')",
            ),
            (
                "by_judge_satisfaction",
                "SELECT j.satisfaction, COUNT(*) "
                "FROM judge_evaluations j JOIN dialogues d ON d.id=j.dialogue_id "
                f"{where} GROUP BY j.satisfaction",
            ),
        ):
            rows = conn.execute(text(sql), params).all()
            report[key] = {str(k): int(v) for k, v in rows}

        planned_rows = conn.execute(
            text(f"SELECT planned_mistakes FROM dialogues d {where}"),
            params,
        ).all()
        observed_rows = conn.execute(
            text(f"SELECT observed_mistakes FROM dialogues d {where}"),
            params,
        ).all()
        validated_rows = conn.execute(
            text(
                "SELECT v.validated_mistakes "
                "FROM judge_validations v JOIN dialogues d ON d.id=v.dialogue_id "
                f"{where}"
            ),
            params,
        ).all()

    def _count_json_arrays(rows: list[tuple]) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for (value,) in rows:
            items = value
            if isinstance(items, str):
                items = json.loads(items)
            if isinstance(items, list):
                counter.update(str(item) for item in items)
        return dict(counter)

    report["mistake_frequency_planned"] = _count_json_arrays(planned_rows)
    report["mistake_frequency_observed"] = _count_json_arrays(observed_rows)
    report["mistake_frequency_validated"] = _count_json_arrays(validated_rows)
    return report
