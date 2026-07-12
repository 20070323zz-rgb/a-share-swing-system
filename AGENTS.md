# AGENTS.md

Project-level instructions for Codex and future AI collaborators.

## 1. Project Identity

Project name: A-Share Swing System.

Positioning: A-share ETF weekly swing research and paper simulation system.

Core goal: learn quantitative research, data engineering, model validation, AI collaboration, and trading discipline.

This project is not a real automated trading system, not a brokerage trading system, and not a high-frequency trading system.

## 2. Repository Root

Canonical repository root:

```text
<project_root>
```

The old path `<deprecated_project_root>` is deprecated and must not be used for new project references.

## 3. Formal Strategy Boundary

The formal paper simulation strategy remains ETF-first and weekly swing oriented.

- `mid_trend = 70%`
- `short_swing = 30%`
- `mid_trend + short_swing` may form resonance only when both are BUY.
- `short_swing` is auxiliary and supplemental; it does not replace `mid_trend`.
- Main assets are broad-based ETFs and sector ETFs.
- Individual stocks are for observation, learning, and small validation only.
- Total individual stock exposure must stay `<= 10%` of total portfolio exposure.
- Market scope is A-share weekly swing. Do not build intraday trading logic.

## 4. Formal vs Research Layers

Layer definitions:

- `FORMAL`: current paper simulation logic.
- `SHADOW`: real-time observation that does not affect formal execution.
- `PREVIEW`: hypothetical portfolio, score, or risk-effect analysis.
- `RESEARCH`: historical replay, candidate models, statistical studies.

Research, Shadow, and Preview must not automatically connect to Formal execution.

## 5. Protected Execution Files

Protected files:

```text
src/paper_trade_engine.py
data/paper_trades.csv
data/paper_positions.csv
```

Default rule: read-only. Do not modify these files unless the current task explicitly grants Formal Execution Change authorization.

`data/paper_positions.csv` may legitimately change through normal paper simulation operation. Dirty does not automatically mean wrong. Do not clean git status by reverting it unless explicitly asked.

## 6. Safety Boundary

Permission level: L2 local engineering.

Forbidden:

- brokerage API connection;
- real orders;
- real account reads;
- leverage;
- saving or printing passwords;
- saving or printing tokens;
- exposing `.env`;
- connecting any real trading execution path.

## 7. Current Codex Working Protocol

The project now uses:

```text
Main Phase + Execution Batch
```

Rules:

1. Split large research tasks into multiple batches.
2. A single batch should focus on one or two core goals.
3. Smaller batch scope does not mean shallower instructions.
4. Every batch still needs background, inputs, target, method, outputs, boundaries, validation, and final summary.
5. Do not carry many large phases in one long thread.
6. If repeated remote compact or stream disconnect errors occur, stop that thread.
7. Start a new thread and restore context from repository files.
8. Do not rely on old thread conversation as the source of project truth.

## 8. Source of Truth Priority

Long-lived safety rules:

```text
AGENTS.md safety rules = highest priority
```

Project state priority:

```text
current code / data
docs/current_phase_status.json
docs/current_project_state.md
current phase decision JSON
current phase report
PROJECT_INDEX.md
thread memory / Codex Memories
```

If thread memory conflicts with repository context, repository context wins.

Code or data existence does not prove a research conclusion is valid. Research readiness must be read from decision and status files.

## 9. Required New Thread Bootstrap

Before substantive edits, a new Codex thread must read:

```text
AGENTS.md
PROJECT_INDEX.md
docs/current_project_state.md
docs/current_phase_status.json
```

Then read the current phase report and current phase decision JSON pointed to by `docs/current_phase_status.json`.

If required files are missing or conflicting, do not guess. Perform a context audit first.

## 9A. Context State Transition Rule

Do not mark a Batch `COMPLETE` before its goals and validation have completed.

Phase status and readiness must not be inferred from code existence, report tone, or UI display. Use authoritative status and decision files.

If a response is lost, first audit side effects and expected outputs, then resume from verified state. Do not directly repeat the entire Batch.

Transition protocol entrypoint:

```text
docs/project_context_transition_protocol.md
```

## 9B. New Thread Bootstrap Requirement

A new Codex thread must complete repository-context bootstrap before substantive edits.

Entry points:

```text
docs/codex_new_thread_bootstrap.md
scripts/context/bootstrap_codex_context.py
```

If the validator reports `INVALID`, do not start the Batch. Report the blocking conflict first.

## 10. Validation Expectations

Run only the validation needed for the current batch. Final closeout batches should run broader phase-level validation.

Python changes:

```bash
python3 -m py_compile ...
```

Research scripts:

- run the target script;
- check JSON for non-finite numbers;
- check CSV key uniqueness when applicable.

Dashboard:

```bash
python3 dashboard/build_dashboard.py
```

Frontend:

```bash
cd app/frontend
npm run build
```

App release:

```bash
bash scripts/check_app_release.sh
```

## 11. Reporting Language

Final summaries default to Chinese. Technical fields may remain in English. User-facing UI should be Chinese-first.
