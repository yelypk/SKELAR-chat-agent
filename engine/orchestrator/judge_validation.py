from __future__ import annotations

from typing import Any, TypedDict


class JudgeOutputLike(TypedDict, total=False):
    agent_mistakes: list[str] | Any
    resolved: bool
    termination_reason: str


class JudgeValidationResult(TypedDict):
    resolved_match: bool
    termination_match: bool
    validated_mistakes: list[str]
    missed_mistakes: list[str]
    extra_mistakes: list[str]
    precision: float
    recall: float
    f1: float
    notes: str


def _safe_agent_mistakes(value: Any) -> tuple[set[str], list[str]]:
    reasons: list[str] = []
    if not isinstance(value, list):
        reasons.append(
            f"agent_mistakes has invalid type (expected list, got {type(value).__name__})"
        )
        return set(), reasons

    non_string_items = [item for item in value if not isinstance(item, str)]
    if non_string_items:
        reasons.append(
            "agent_mistakes contains non-string items "
            f"(count={len(non_string_items)})"
        )
    return {item for item in value if isinstance(item, str)}, reasons


def validate_judge_output(
    judge_output: JudgeOutputLike,
    observed_mistakes: list[str],
    resolved_gt: bool,
    termination_reason_gt: str,
) -> JudgeValidationResult:
    judged_mistakes, type_reasons = _safe_agent_mistakes(judge_output.get("agent_mistakes", []))
    observed = set(observed_mistakes)
    tp = len(judged_mistakes & observed)
    precision = tp / len(judged_mistakes) if judged_mistakes else 0.0
    recall = tp / len(observed) if observed else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    resolved_match = judge_output.get("resolved") == resolved_gt
    termination_match = judge_output.get("termination_reason") == termination_reason_gt
    reasons: list[str] = list(type_reasons)
    if not resolved_match:
        reasons.append(
            f"resolved mismatch (judge={judge_output.get('resolved')} gt={resolved_gt})"
        )
    if not termination_match:
        reasons.append(
            "termination mismatch "
            f"(judge={judge_output.get('termination_reason')} gt={termination_reason_gt})"
        )
    missed = sorted(observed - judged_mistakes)
    extra = sorted(judged_mistakes - observed)
    if missed:
        reasons.append(f"missed observed mistakes: {missed}")
    if extra:
        reasons.append(f"judge-only mistakes: {extra}")
    notes = "; ".join(reasons) if reasons else "Judge output matches deterministic labels."
    return {
        "resolved_match": resolved_match,
        "termination_match": termination_match,
        "validated_mistakes": sorted(judged_mistakes & observed),
        "missed_mistakes": missed,
        "extra_mistakes": extra,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "notes": notes,
    }
