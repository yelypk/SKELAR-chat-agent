from __future__ import annotations

import types
import unittest

from engine.config import AppConfig
from engine.post_turn import finalize_turn
from engine.rules.deadlock import detect_deadlock
from engine.rules.resolution import is_resolved
from engine.rules.termination import compute_termination
from engine.session import DialogueSession, TurnRecord


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "restart app" in lowered or "restart the app" in lowered:
                vectors.append([1.0, 0.0, 0.0])
                continue
            if "loop-support" in lowered:
                vectors.append([0.0, 1.0, 0.0])
                continue
            if "loop-customer" in lowered:
                vectors.append([0.0, 0.0, 1.0])
                continue
            vectors.append([0.2, 0.2, 0.2])
        return vectors


def _base_session() -> DialogueSession:
    intent = types.SimpleNamespace(
        intent_id="intent.sample",
        resolution_paths=["restart app and sign in again"],
    )
    persona = types.SimpleNamespace(persona_seed_prompt="", chaos_level="low")
    support_persona = types.SimpleNamespace(support_persona_seed_prompt="", seniority="junior")
    return DialogueSession(
        run_id="run-1",
        dialogue_id="dlg-1",
        seed=1,
        turn_index=0,
        max_turns=6,
        intent=intent,  # type: ignore[arg-type]
        support_view={
            "required_questions": [],
            "forbidden_actions": [],
            "escalation_rules": [],
        },
        customer_view={},
        root_cause="root",
        persona=persona,  # type: ignore[arg-type]
        support_persona=support_persona,  # type: ignore[arg-type]
        dialogue_phase="greeting",
        entropy_params={},
        planned_mistakes=[],
        observed_mistakes=[],
    )


class ResolutionRuleTests(unittest.TestCase):
    def test_is_resolved_when_action_matches_and_customer_confirms(self) -> None:
        session = _base_session()
        session.support_proposed_actions.append("Please restart app and sign in again")
        session.turns = [
            TurnRecord(speaker="customer", utterance="It is broken", payload={}),
            TurnRecord(speaker="support", utterance="Try this fix", payload={}),
            TurnRecord(speaker="customer", utterance="Thanks, that worked.", payload={}),
        ]
        self.assertTrue(is_resolved(session, FakeEmbeddings()))


class DeadlockRuleTests(unittest.TestCase):
    def test_detect_deadlock_on_repeated_loop(self) -> None:
        session = _base_session()
        session.turns = [
            TurnRecord(speaker="customer", utterance="loop-customer-1", payload={}),
            TurnRecord(speaker="support", utterance="loop-support-1", payload={}),
            TurnRecord(speaker="customer", utterance="loop-customer-2", payload={}),
            TurnRecord(speaker="support", utterance="loop-support-2", payload={}),
        ]
        session.asked_questions = ["q1", "q1"]
        session.support_proposed_actions = ["a1", "a1"]
        self.assertTrue(detect_deadlock(session, FakeEmbeddings(), window=2, threshold=0.9))


class TerminationRuleTests(unittest.TestCase):
    def test_compute_termination_prefers_resolved_with_support_closing(self) -> None:
        session = _base_session()
        session.resolved = True
        session.turns = [
            TurnRecord(speaker="customer", utterance="Issue", payload={}),
            TurnRecord(speaker="support", utterance="Anything else I can help with?", payload={}),
        ]
        self.assertEqual(compute_termination(session), "resolved")


class FinalizeTurnTests(unittest.TestCase):
    def test_finalize_sets_deadlock_without_forced_escalation(self) -> None:
        session = _base_session()
        session.turn_index = 4
        session.turns = [
            TurnRecord(speaker="customer", utterance="loop-customer-1", payload={}),
            TurnRecord(speaker="support", utterance="loop-support-1", payload={}),
            TurnRecord(speaker="customer", utterance="loop-customer-2", payload={}),
            TurnRecord(speaker="support", utterance="loop-support-2", payload={}),
        ]
        session.asked_questions = ["same", "same"]
        session.support_proposed_actions = ["same-action", "same-action"]
        config = AppConfig(
            llm_provider="ollama",
            ollama_base_url="http://localhost:11434",
            openai_base_url=None,
            openai_api_key=None,
            support_model="model",
            customer_model="model",
            judge_model="model",
            embedding_model="embed",
            postgres_dsn="postgresql://localhost/x",
            max_turns=6,
            deadlock_window=2,
            deadlock_similarity_threshold=0.92,
            retries_per_llm_call=2,
            llm_timeout_seconds=60,
            allow_llm_escalation=True,
            escalation_trace_enabled=False,
        )
        finalize_turn(session, FakeEmbeddings(), config)
        self.assertTrue(session.deadlock_detected)
        self.assertFalse(session.escalated)
        self.assertEqual(session.termination_reason, "deadlock")


if __name__ == "__main__":
    unittest.main()
