from __future__ import annotations

import random
from pathlib import Path

import yaml

from engine.state import IntentCard


INTENTS_DIR = Path(__file__).resolve().parent / "intents"


def _normalize_string_list(values: list) -> list[str]:
    normalized: list[str] = []
    for item in values:
        if isinstance(item, str):
            normalized.append(item)
            continue
        if isinstance(item, dict):
            # YAML lines with ":" may parse into one-key mapping; flatten back to string.
            for key, value in item.items():
                normalized.append(f"{key}: {value}")
            continue
        normalized.append(str(item))
    return normalized


def load_intents() -> list[IntentCard]:
    intents: list[IntentCard] = []
    for path in sorted(INTENTS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for field in (
            "symptoms",
            "hidden_root_causes",
            "required_questions",
            "resolution_paths",
            "forbidden_actions",
            "escalation_rules",
            "common_agent_mistakes",
        ):
            if field in data and isinstance(data[field], list):
                data[field] = _normalize_string_list(data[field])
        intents.append(IntentCard.model_validate(data))
    if not intents:
        raise RuntimeError("No intent cards found in scenarios/intents")
    return intents


def sample_intent(intents: list[IntentCard], rng: random.Random) -> IntentCard:
    return intents[rng.randrange(0, len(intents))]


def build_support_view(intent: IntentCard) -> dict:
    return {
        "intent_id": intent.intent_id,
        "title": intent.title,
        "description": intent.description,
        "symptoms": intent.symptoms,
        "required_questions": intent.required_questions,
        "resolution_paths": intent.resolution_paths,
        "forbidden_actions": intent.forbidden_actions,
        "escalation_rules": intent.escalation_rules,
        "common_agent_mistakes": intent.common_agent_mistakes,
    }


def build_customer_view(intent: IntentCard, root_cause: str) -> dict:
    return {
        "intent_id": intent.intent_id,
        "title": intent.title,
        "symptoms": intent.symptoms,
        "hidden_root_cause": root_cause,
    }
