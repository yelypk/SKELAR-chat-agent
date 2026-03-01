# Architecture

This project is a controlled self-play simulator, not a production chatbot.

## High-level components

- **Customer simulator**: knows hidden root cause, reveals facts only when asked.
- **Support simulator**: does not know root cause, reasons via intent card hints.
- **Judge**: evaluates transcript after dialogue completion.
- **Orchestrator (deterministic Python runner + rules)**: owns all transitions and stop decisions.

## Deterministic core vs chaotic surface

- Deterministic (code-controlled):
  - intent
  - hidden root cause selection
  - planned mistake schedule
  - stop conditions
  - final ground-truth labels
- Chaotic (LLM-styled):
  - tone shifts
  - emotional volatility
  - verbosity/noise
  - confrontation and trust fluctuations

## Turn loop

1. Customer turn (LLM JSON output)
2. Orchestrator deterministic post-processing + stop check
3. Support turn (LLM JSON output)
4. Orchestrator deterministic post-processing + stop check
5. Repeat until stop condition
6. Customer final rating step
7. Judge evaluation
8. Judge-validation against deterministic labels
9. Dataset persistence

## Layer boundaries

- `engine/state`: typed schemas and session state.
- `engine/session.py`: explicit session model for runtime mutation.
- `engine/steps`: payload build/call/apply functions per role.
- `engine/rules`: pure deterministic rule solvers.
- `engine/runner.py`: linear dialogue loop and stop checks.
- `engine/orchestrator`: compatibility wrappers + judge validation.
- `agents`: LLM wrappers and strict JSON parsing.
- `scenarios`: intent loading and persona generation.
- `dataset`: Postgres persistence and dataset metrics.
- `prompts`: role behavior instructions only (no control flow).

## Control-flow ownership

- LLMs do not decide transitions.
- LLM booleans (`should_quit`, `should_end`, `should_escalate`) are treated as inputs.
- Orchestrator translates those inputs into explicit state flags and terminal reasons.
