from __future__ import annotations

from engine.config import AppConfig
from engine.state import JudgeOutput

from agents.json_protocol import invoke_json
from agents.prompts import load_prompt
from agents.providers import build_chat_client


class JudgeAgent:
    def __init__(self, config: AppConfig) -> None:
        self._client = build_chat_client(config, config.judge_model)
        self._prompt = load_prompt("judge.md")
        self._retries = config.retries_per_llm_call

    def evaluate(self, payload: dict) -> JudgeOutput:
        return invoke_json(
            self._client,
            self._prompt,
            payload,
            JudgeOutput,
            max_attempts=self._retries,
        )
