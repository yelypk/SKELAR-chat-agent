from __future__ import annotations

from engine.config import AppConfig
from engine.state import SupportTurn

from agents.json_protocol import invoke_json
from agents.prompts import load_prompt
from agents.providers import build_chat_client


class SupportAgent:
    def __init__(self, config: AppConfig) -> None:
        self._client = build_chat_client(config, config.support_model)
        self._prompt = load_prompt("support.md")
        self._retries = config.retries_per_llm_call

    def run_turn(self, payload: dict) -> SupportTurn:
        return invoke_json(
            self._client,
            self._prompt,
            payload,
            SupportTurn,
            max_attempts=self._retries,
        )
