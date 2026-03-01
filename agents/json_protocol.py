from __future__ import annotations

import json
from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ValidationError

from agents.prompts import render_prompt_request

T = TypeVar("T", bound=BaseModel)


class InvalidLLMOutputError(RuntimeError):
    pass


def _extract_json(raw_content: str) -> dict:
    text = raw_content.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        text = text.replace("json", "", 1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise InvalidLLMOutputError("No JSON object found in LLM response")
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise InvalidLLMOutputError("Invalid JSON payload from LLM") from exc


def invoke_json(
    client: BaseChatModel,
    prompt: str,
    payload: dict,
    output_model: type[T],
    max_attempts: int = 3,
) -> T:
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            request = render_prompt_request(prompt, payload)
            response = client.invoke(request)
            data = _extract_json(str(response.content))
            return output_model.model_validate(data)
        except (InvalidLLMOutputError, ValidationError) as exc:
            last_error = exc
            continue
    raise InvalidLLMOutputError("LLM failed to return valid schema JSON") from last_error
