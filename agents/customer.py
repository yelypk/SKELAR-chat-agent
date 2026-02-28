from __future__ import annotations

from engine.config import AppConfig
from engine.state import CustomerRatingOutput, CustomerTurn

from agents.llm import build_chat_client, invoke_json, load_prompt


class CustomerAgent:
    def __init__(self, config: AppConfig) -> None:
        self._client = build_chat_client(config, config.customer_model)
        self._prompt = load_prompt("customer.md")
        self._rating_prompt = load_prompt("customer_rating.md")
        self._retries = config.retries_per_llm_call

    def run_turn(self, payload: dict) -> CustomerTurn:
        return invoke_json(
            self._client,
            self._prompt,
            payload,
            CustomerTurn,
            max_attempts=self._retries,
        )

    def rate_dialogue(self, payload: dict) -> CustomerRatingOutput:
        return invoke_json(
            self._client,
            self._rating_prompt,
            payload,
            CustomerRatingOutput,
            max_attempts=self._retries,
        )
