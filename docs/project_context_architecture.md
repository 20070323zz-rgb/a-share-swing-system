# Project Context Architecture

This document defines how repository context is persisted for new Codex threads.

Core principle:

```text
Conversation is disposable.
Repository context is authoritative.
```

中文：

```text
对话可以更换。
项目记忆必须落盘。
```

## Files And Responsibilities

| File | Responsibility |
| --- | --- |
| `AGENTS.md` | Long-lived project rules, safety boundary, protected files, Codex workflow, source-of-truth priority. Low-frequency updates only. |
| `PROJECT_INDEX.md` | Root index for project entrypoints, core data, reports, and context bootstrap links. |
| `docs/current_project_state.md` | Human-readable latest known project facts: current research track, completed phases, selected shadow regime, current conclusions, bottlenecks, next work. |
| `docs/current_phase_status.json` | Machine-readable execution state: main phase, current batch, completed/pending batches, resume point, readiness flags, protected files. |
| Phase reports | Evidence and narrative details for each research phase. |
| Decision JSON | Explicit readiness and phase decision state. Prefer these over narrative summaries for booleans. |

## Batch Internal Checkpoints

An Execution Batch may contain internal checkpoints when the Batch itself is intentionally larger than one Codex turn.

For `Context Phase D`:

```text
Context Phase D
├── Context Phase D1
├── Context Phase D2
├── Context Phase D3
└── Context Phase D4
```

`resume_from` is the Execution Batch resume point.

`phase_d_resume_checkpoint` is the internal resume checkpoint inside the current Batch.

Therefore:

```text
resume_from = Context Phase D
phase_d_resume_checkpoint = Context Phase D3
```

means a new thread should resume the `Context Phase D` Batch at its D3 checkpoint, not repeat D1 or D2.

## Conflict Resolution

Long-lived safety rule conflicts:

```text
AGENTS.md wins
```

Current execution state conflicts:

```text
current code/data + docs/current_phase_status.json
```

If these disagree, perform a context audit before modifying behavior.

Research conclusion conflicts:

```text
newer decision JSON > older Phase report
```

Do not judge recency only by file modified time. Prefer:

1. phase number;
2. snapshot metadata;
3. explicit decision state.

## Staleness

Snapshot information means:

```text
latest known
```

It does not mean:

```text
current live
```

Example:

```text
latest_known_shadow_regime = NEUTRAL
date = 2026-07-06
```

If the current data date is later than 2026-07-06, do not claim the old snapshot is the current market state. First run or read the latest regime outputs.

Required staleness flags:

- `regime_snapshot_stale`
- `project_state_snapshot_stale`
- `phase_status_stale`
- `decision_state_conflict`
- `context_consistency_unknown`

## Current Project State Update Responsibility

`docs/current_project_state.md` records current project facts that still hold.

It must not become a detailed Batch operation log.

Must update when any of these change:

- formal model state;
- Main Phase;
- selected shadow candidate;
- research architecture;
- important decision;
- readiness;
- major bottleneck;
- next research direction.

Usually no update is needed for:

- a single report file addition;
- one `npm run build`;
- one compile run;
- small UI styling;
- log archive;
- bug fix that does not change research conclusions.

Snapshot fields such as current regime, BUY Top10 conflict count, current portfolio fit, and latest data date must carry:

```text
as of YYYY-MM-DD
```

and a source where practical. Do not write `current`, `now`, or `latest` without date/source context.

## New Thread Bootstrap

Before substantive work, read:

```text
AGENTS.md
PROJECT_INDEX.md
docs/current_project_state.md
docs/current_phase_status.json
```

Then read `current_phase_report` and `current_phase_decision` from `docs/current_phase_status.json`.

If a file is missing, stale, or contradictory, perform a context audit and do not guess.
