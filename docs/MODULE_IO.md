# Module I/O and Operational Notes

This document describes module responsibilities, input contracts, and output contracts.

## `scenarios/intent_loader.py`

Input:
- YAML files from `scenarios/intents/*.yaml`

Output:
- `IntentCard` objects (validated)
- `support_view` (safe subset for support simulator)
- `customer_view` (contains hidden root cause for customer simulator)

Notes:
- Intent schema violations must fail fast at load time.

## `scenarios/persona/generator.py`

Input:
- Deterministic `random.Random` seed source

Output:
- `PersonaSeed` (prompt seed text and attributes)
- `entropy_params` dict

Notes:
- Persona generation is deterministic for the same seed.
- Persona card files are not required; generation is on-the-fly.

## `agents/providers.py`, `agents/prompts.py`, `agents/json_protocol.py`

Input:
- Provider config and model name
- Prompt text and structured payload
- Target pydantic model schema

Output:
- Chat/embeddings clients and strictly validated model instances

Notes:
- `providers.py` builds chat and embeddings clients.
- `prompts.py` loads prompt files and renders final LLM request text.
- `json_protocol.py` extracts JSON payload, validates schema, and retries on errors.

## `agents/support.py`

Input:
- Intent support view
- Transcript
- Planned mistake for current turn
- Current tolerance state (`patience`, `trust`)

Output:
- `SupportTurn` with:
  - `questions`
  - `proposed_action`
  - `mistake_applied`
  - `should_end`
  - `should_escalate`
  - `utterance`

Notes:
- `mistake_applied` must be from controlled vocabulary.

## `agents/customer.py`

Input:
- Persona seed prompt
- Customer view with hidden truth
- Transcript
- Current tolerance state

Output:
- `CustomerTurn` with emotional shift, patience/trust deltas, quit flag, utterance
- `CustomerRatingOutput` in final rating step (`1..5` or `null`)

Notes:
- Customer reveals hidden facts only when appropriately prompted.

## `engine/orchestrator/stop_conditions.py`

Input:
- Mutable dialogue state
- Embeddings client
- Deadlock params

Output:
- Updated flags:
  - `resolved`
  - `deadlock_detected`
  - `max_turns_reached`
  - `termination_reason`

Notes:
- Deadlock uses semantic similarity + no-progress checks.
- Resolved uses rule-based match between support action and intent resolution paths.

## `engine/runner.py`

Input:
- Initial `DialogueSession`
- Agent bundle and runtime bundle (config + embeddings)

Output:
- Final `DialogueSession` with:
  - full transcript
  - terminal reason
  - judge output
  - judge-validation output

Notes:
- Runner executes a deterministic while-loop.
- Stop checks run after each speaker turn via `finalize_turn`.

## `engine/orchestrator/judge_validation.py`

Input:
- Judge output
- Planned mistakes
- Ground-truth resolved + termination reason

Output:
- Validation artifact:
  - match booleans
  - validated mistakes
  - precision/recall

## `dataset/db.py`

Input:
- Final state-derived payloads

Output:
- Persistent rows in:
  - `dialogues`
  - `judge_evaluations`
  - `judge_validations`

Notes:
- Dialogue row is the canonical anchor; others reference `dialogue_id`.
- Database schema is managed by Alembic migrations, not by runtime `create_all`.

## `dataset/metrics.py`

Input:
- Postgres DSN
- Optional `run_id`

Output:
- Aggregated balance report:
  - intent distribution
  - chaos distribution
  - resolved/unresolved distribution
  - termination reason distribution
  - satisfaction and score distribution
  - planned/observed/validated mistakes frequency
