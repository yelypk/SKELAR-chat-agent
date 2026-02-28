from __future__ import annotations


def validate_judge_output(
    judge_output: dict,
    observed_mistakes: list[str],
    resolved_gt: bool,
    termination_reason_gt: str,
) -> dict:
    judged_mistakes = set(judge_output.get("agent_mistakes", []))
    observed = set(observed_mistakes)
    tp = len(judged_mistakes & observed)
    precision = tp / len(judged_mistakes) if judged_mistakes else 0.0
    recall = tp / len(observed) if observed else 0.0
    resolved_match = judge_output.get("resolved") == resolved_gt
    termination_match = judge_output.get("termination_reason") == termination_reason_gt
    reasons: list[str] = []
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
        "precision": precision,
        "recall": recall,
        "notes": notes,
    }
