from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel, ValidationError

from engine.config import AppConfig

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:  # pragma: no cover - optional dependency for OpenAI provider
    ChatOpenAI = None
    OpenAIEmbeddings = None


ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT_DIR / "prompts"
T = TypeVar("T", bound=BaseModel)


class InvalidLLMOutputError(RuntimeError):
    pass


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_chat_client(config: AppConfig, model: str) -> BaseChatModel:
    if config.llm_provider == "openai":
        if ChatOpenAI is None:
            raise RuntimeError(
                "OpenAI provider requires 'langchain-openai'. Install dependencies from requirements-dev.txt."
            )
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=model,
            temperature=0,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            timeout=config.llm_timeout_seconds,
        )
    return ChatOllama(
        base_url=config.ollama_base_url,
        model=model,
        temperature=0,
        top_p=1,
        client_kwargs={"timeout": config.llm_timeout_seconds},
    )


def build_embeddings_client(config: AppConfig) -> Embeddings:
    if config.llm_provider == "openai":
        if OpenAIEmbeddings is None:
            raise RuntimeError(
                "OpenAI provider requires 'langchain-openai'. Install dependencies from requirements-dev.txt."
            )
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIEmbeddings(
            model=config.embedding_model,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            timeout=config.llm_timeout_seconds,
        )
    return OllamaEmbeddings(
        base_url=config.ollama_base_url,
        model=config.embedding_model,
        client_kwargs={"timeout": config.llm_timeout_seconds},
    )


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
            payload_for_input = dict(payload)
            persona_prefixes: list[str] = []
            customer_persona = payload_for_input.pop("persona_seed_prompt", None)
            support_persona = payload_for_input.pop("support_persona_seed_prompt", None)
            if customer_persona:
                persona_prefixes.append(
                    f"Imagine you are this customer persona:\n{customer_persona}"
                )
            if support_persona:
                persona_prefixes.append(
                    f"Imagine you are this support persona:\n{support_persona}"
                )
            persona_block = (
                "\n\n".join(persona_prefixes) + "\n\n" if persona_prefixes else ""
            )
            request = (
                f"{persona_block}{prompt}\n\n"
                "Return strictly valid JSON and nothing else.\n"
                f"INPUT:\n{json.dumps(payload_for_input, ensure_ascii=True)}"
            )
            response = client.invoke(request)
            data = _extract_json(str(response.content))
            return output_model.model_validate(data)
        except (InvalidLLMOutputError, ValidationError) as exc:
            last_error = exc
            continue
    raise InvalidLLMOutputError("LLM failed to return valid schema JSON") from last_error
