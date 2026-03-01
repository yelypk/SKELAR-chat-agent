from __future__ import annotations

import unittest
from typing import Any

from engine.orchestrator.escalation_policy import should_allow_escalation
from engine.orchestrator.judge_validation import validate_judge_output
from engine.orchestrator.mistake_detection import detect_observed_mistakes


def _base_state() -> dict[str, Any]:
    return {
        "turns": [
            {"speaker": "customer", "utterance": "I have an issue", "payload": {}},
            {"speaker": "support", "utterance": "Let me help", "payload": {}},
        ],
        "support_view": {
            "required_questions": [],
            "forbidden_actions": [],
            "escalation_rules": [],
        },
        "asked_questions": [],
        "support_proposed_actions": [],
        "termination_reason": None,
        "turn_index": 1,
        "max_turns": 8,
        "customer_confusion_events": [],
    }


class EscalationPolicyTests(unittest.TestCase):
    def test_allows_high_risk_when_no_rules_and_short_dialogue(self) -> None:
        state = _base_state()
        state["turns"].append(
            {
                "speaker": "customer",
                "utterance": "This may be fraud with my account",
                "payload": {},
            }
        )
        self.assertTrue(should_allow_escalation(state))

    def test_disallows_when_no_rules_short_dialogue_no_risk(self) -> None:
        state = _base_state()
        self.assertFalse(should_allow_escalation(state))


class MistakeDetectionTests(unittest.TestCase):
    def test_required_questions_are_matched_individually(self) -> None:
        state = _base_state()
        state["support_view"]["required_questions"] = [
            "What exact error code do you see?",
            "When did the issue start?",
        ]
        state["asked_questions"] = [
            "Could you share the exact error code you see now?",
            "When exactly did this issue start for you?",
        ]
        observed = detect_observed_mistakes(state)
        self.assertNotIn("ignored_question", observed)

    def test_no_asked_questions_marks_ignored_question(self) -> None:
        state = _base_state()
        state["support_view"]["required_questions"] = ["What exact error code do you see?"]
        observed = detect_observed_mistakes(state)
        self.assertIn("ignored_question", observed)

    def test_neutral_obvious_word_is_not_rude_tone(self) -> None:
        state = _base_state()
        state["turns"].append(
            {
                "speaker": "support",
                "utterance": "The most obvious next step is to re-login.",
                "payload": {},
            }
        )
        observed = detect_observed_mistakes(state)
        self.assertNotIn("rude_tone", observed)


class JudgeValidationTests(unittest.TestCase):
    def test_invalid_agent_mistakes_type_is_handled(self) -> None:
        result = validate_judge_output(
            judge_output={
                "agent_mistakes": "ignored_question",
                "resolved": False,
                "termination_reason": "deadlock",
            },
            observed_mistakes=["ignored_question"],
            resolved_gt=False,
            termination_reason_gt="deadlock",
        )
        self.assertEqual(result["precision"], 0.0)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["f1"], 0.0)
        self.assertIn("invalid type", result["notes"])

    def test_returns_missed_extra_and_f1(self) -> None:
        result = validate_judge_output(
            judge_output={
                "agent_mistakes": ["ignored_question", "rude_tone"],
                "resolved": True,
                "termination_reason": "resolved",
            },
            observed_mistakes=["ignored_question", "incorrect_info"],
            resolved_gt=True,
            termination_reason_gt="resolved",
        )
        self.assertEqual(result["validated_mistakes"], ["ignored_question"])
        self.assertEqual(result["missed_mistakes"], ["incorrect_info"])
        self.assertEqual(result["extra_mistakes"], ["rude_tone"])
        self.assertGreater(result["f1"], 0.0)


if __name__ == "__main__":
    unittest.main()
