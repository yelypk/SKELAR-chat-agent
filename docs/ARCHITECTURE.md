# Architecture

This project is a controlled self-play simulator, not a production chatbot.

## High-level components

- **Customer simulator**: knows hidden root cause, reveals facts only when asked.
- **Support simulator**: does not know root cause, reasons via intent card hints.
- **Judge**: evaluates transcript after dialogue completion.
- **Orchestrator (LangGraph + Python logic)**: owns all transitions and stop decisions.

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

1. Support turn (LLM JSON output)
2. Orchestrator validation + stop check
3. Customer turn (LLM JSON output)
4. Orchestrator validation + stop check
5. Repeat until stop condition
6. Customer final rating step
7. Judge evaluation
8. Judge-validation against deterministic labels
9. Dataset persistence

## Layer boundaries

- `engine/state`: typed schemas and session state.
- `engine/orchestrator`: stop conditions, resolved rules, judge validation.
- `engine/graph`: node wiring and routing.
- `agents`: LLM wrappers and strict JSON parsing.
- `scenarios`: intent loading and persona generation.
- `dataset`: Postgres persistence and dataset metrics.
- `prompts`: role behavior instructions only (no control flow).

## Control-flow ownership

- LLMs do not decide transitions.
- LLM booleans (`should_quit`, `should_end`, `should_escalate`) are treated as inputs.
- Orchestrator translates those inputs into explicit state flags and terminal reasons.
