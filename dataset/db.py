from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID


metadata = MetaData()

dialogues = Table(
    "dialogues",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("run_id", String(64), nullable=False, index=True),
    Column("intent_id", String(128), nullable=False, index=True),
    Column("hidden_root_cause", String(1024), nullable=False),
    Column("chaos_level", String(16), nullable=False, index=True),
    Column("support_seniority", String(16), nullable=False),
    Column("entropy_params", JSONB().with_variant(JSON(), "sqlite"), nullable=False),
    Column(
        "planned_mistakes",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    ),
    Column(
        "observed_mistakes",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    ),
    Column("resolved_gt", Boolean, nullable=False),
    Column("termination_reason_gt", String(64), nullable=False),
    Column("client_quality_score", Integer, nullable=True),
    Column(
        "transcript_json",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

judge_evaluations = Table(
    "judge_evaluations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("dialogue_id", UUID(as_uuid=True), ForeignKey("dialogues.id"), nullable=False),
    Column("resolved", Boolean, nullable=False),
    Column("satisfaction", String(32), nullable=False),
    Column("quality_score", Integer, nullable=False),
    Column(
        "agent_mistakes",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    ),
    Column("termination_reason", String(64), nullable=False),
    Column("rationale", String(4096), nullable=False),
    Column("judge_raw_json", JSONB().with_variant(JSON(), "sqlite"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

judge_validations = Table(
    "judge_validations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("dialogue_id", UUID(as_uuid=True), ForeignKey("dialogues.id"), nullable=False),
    Column("resolved_match", Boolean, nullable=False),
    Column("termination_match", Boolean, nullable=False),
    Column(
        "validated_mistakes",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    ),
    Column("precision", Float, nullable=False),
    Column("recall", Float, nullable=False),
    Column("notes", String(4096), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


class DatasetWriter:
    def __init__(self, dsn: str) -> None:
        self._engine = create_engine(dsn, future=True)

    def write_dialogue(self, payload: dict) -> uuid.UUID:
        dialogue_id = uuid.UUID(payload["dialogue_id"])
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                dialogues.insert().values(
                    id=dialogue_id,
                    run_id=payload["run_id"],
                    intent_id=payload["intent_id"],
                    hidden_root_cause=payload["hidden_root_cause"],
                    chaos_level=payload["chaos_level"],
                    support_seniority=payload["support_seniority"],
                    entropy_params=payload["entropy_params"],
                    planned_mistakes=payload["planned_mistakes"],
                    observed_mistakes=payload["observed_mistakes"],
                    resolved_gt=payload["resolved_gt"],
                    termination_reason_gt=payload["termination_reason_gt"],
                    client_quality_score=payload.get("client_quality_score"),
                    transcript_json=payload["transcript_json"],
                    created_at=now,
                )
            )
        return dialogue_id

    def write_judge(self, dialogue_id: uuid.UUID, judge_output: dict, validation: dict) -> None:
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                judge_evaluations.insert().values(
                    id=uuid.uuid4(),
                    dialogue_id=dialogue_id,
                    resolved=judge_output["resolved"],
                    satisfaction=judge_output["satisfaction"],
                    quality_score=judge_output["quality_score"],
                    agent_mistakes=judge_output["agent_mistakes"],
                    termination_reason=judge_output["termination_reason"],
                    rationale=judge_output["rationale"],
                    judge_raw_json=judge_output,
                    created_at=now,
                )
            )
            conn.execute(
                judge_validations.insert().values(
                    id=uuid.uuid4(),
                    dialogue_id=dialogue_id,
                    resolved_match=validation["resolved_match"],
                    termination_match=validation["termination_match"],
                    validated_mistakes=validation["validated_mistakes"],
                    precision=validation["precision"],
                    recall=validation["recall"],
                    notes=validation["notes"],
                    created_at=now,
                )
            )
