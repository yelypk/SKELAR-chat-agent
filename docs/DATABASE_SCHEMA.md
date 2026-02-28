# Database Schema

This document defines the canonical Postgres schema for synthetic dialogue storage.

## Principles

- Dialogue labels are stored as explicit relational columns.
- Full transcript and flexible metadata are stored as JSONB.
- Judge evaluation and judge-validation are separated into dedicated tables.
- Every dialogue row must exist even when a run fails.

## Tables

## `dialogues`

Primary record for each simulated dialogue.

Columns:

- `id` UUID PK
- `run_id` VARCHAR(64), indexed
- `intent_id` VARCHAR(128), indexed
- `hidden_root_cause` VARCHAR(1024)
- `chaos_level` VARCHAR(16), indexed (`low|medium|high`)
- `support_seniority` VARCHAR(16) (`junior|middle|senior|lead`)
- `entropy_params` JSONB
- `planned_mistakes` JSONB (string array)
- `observed_mistakes` JSONB (string array)
- `resolved_gt` BOOLEAN
- `termination_reason_gt` VARCHAR(64)
- `client_quality_score` INTEGER NULL (1..5 or null)
- `transcript_json` JSONB
- `created_at` TIMESTAMPTZ

## `judge_evaluations`

Raw and structured output from judge model.

Columns:

- `id` UUID PK
- `dialogue_id` UUID FK -> `dialogues.id`
- `resolved` BOOLEAN
- `satisfaction` VARCHAR(32)
- `quality_score` INTEGER (1..5)
- `agent_mistakes` JSONB (string array)
- `termination_reason` VARCHAR(64)
- `rationale` VARCHAR(4096)
- `judge_raw_json` JSONB
- `created_at` TIMESTAMPTZ

## `judge_validations`

Deterministic comparison between judge output and orchestrator ground truth.

Columns:

- `id` UUID PK
- `dialogue_id` UUID FK -> `dialogues.id`
- `resolved_match` BOOLEAN
- `termination_match` BOOLEAN
- `validated_mistakes` JSONB (intersection set)
- `precision` FLOAT
- `recall` FLOAT
- `notes` VARCHAR(4096)
- `created_at` TIMESTAMPTZ

## Migration source of truth

- Runtime SQLAlchemy metadata: `dataset/db.py`
- Alembic migration: `alembic/versions/0001_initial_dataset_schema.py`

Both must evolve together.
