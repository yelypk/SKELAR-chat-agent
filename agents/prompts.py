from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT_DIR / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def render_prompt_request(prompt: str, payload: dict) -> str:
    payload_for_input = dict(payload)
    persona_prefixes: list[str] = []
    customer_persona = payload_for_input.pop("persona_seed_prompt", None)
    support_persona = payload_for_input.pop("support_persona_seed_prompt", None)
    if customer_persona:
        persona_prefixes.append(f"Imagine you are this customer persona:\n{customer_persona}")
    if support_persona:
        persona_prefixes.append(f"Imagine you are this support persona:\n{support_persona}")
    persona_block = "\n\n".join(persona_prefixes) + "\n\n" if persona_prefixes else ""
    return (
        f"{persona_block}{prompt}\n\n"
        "Return strictly valid JSON and nothing else.\n"
        f"INPUT:\n{json.dumps(payload_for_input, ensure_ascii=True)}"
    )
