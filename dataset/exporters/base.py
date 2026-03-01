from __future__ import annotations

import json
import os
from typing import Any, Iterator
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import Engine, text

DEFAULT_DSN = "postgresql+psycopg://app:app@localhost:5432/skelar_chat_agent"


def json_text(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return json.dumps(parsed, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def load_dsn(explicit_dsn: str | None) -> str:
    if explicit_dsn:
        return explicit_dsn
    load_dotenv()
    return os.getenv("POSTGRES_DSN", DEFAULT_DSN)


def parse_anchor_uuid(anchor_dialogue_id: str) -> UUID:
    try:
        return UUID(anchor_dialogue_id)
    except ValueError as exc:
        raise ValueError("--after-dialogue-id must be a valid UUID.") from exc


def resolve_anchor_dialogue(engine: Engine, anchor_uuid: UUID) -> dict[str, Any]:
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, created_at
                FROM dialogues
                WHERE CAST(id AS TEXT) = :anchor_id
                """
            ),
            {"anchor_id": str(anchor_uuid)},
        ).mappings().first()
    if row is None:
        raise ValueError(f"Anchor dialogue_id not found: {str(anchor_uuid)}")
    return {"id": row["id"], "created_at": row["created_at"]}


def iter_dialogues_after_anchor(
    engine: Engine,
    *,
    anchor_created_at: Any,
    anchor_id: str,
    select_sql: str,
) -> Iterator[dict[str, Any]]:
    with engine.begin() as conn:
        rows = conn.execute(
            text(select_sql),
            {
                "anchor_created_at": anchor_created_at,
                "anchor_id": anchor_id,
            },
        ).mappings().all()
    for row in rows:
        yield dict(row)
