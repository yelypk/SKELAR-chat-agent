# AGENTS.md

## Project Overview

This project generates synthetic technical support dialogues
for evaluation model training.

Two role simulators:
- Customer
- Support Agent

One evaluator:
- Judge

## Architecture

Dialogue is controlled by a deterministic Python runner.
LLMs generate language only.

Ground truth is private to the customer simulator
and must never leak to the support agent.

## Workflow

1. Sample scenario
2. Initialize private states
3. Dialogue loop (agent ↔ customer)
4. Stop condition
5. Judge evaluation
6. Save dataset entry

## Design Constraints

- Deterministic flow
- Structured JSON outputs
- No uncontrolled improvisation
- No long-term memory

## When Editing Code

AI assistants must:

- Preserve state machine integrity
- Avoid mixing prompt logic with control logic
- Validate stop conditions
- Prefer explicit over implicit behavior
- Consult `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, and `docs/MODULE_IO.md` before implementing changes