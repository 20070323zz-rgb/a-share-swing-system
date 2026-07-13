# Project Context Transition Protocol

This document defines how project context state is synchronized and migrated.

Core rule:

```text
Context files are state infrastructure.
They must not be updated by guesswork.
```

中文：

```text
上下文文件属于状态基础设施。
不得凭猜测更新。
```

## Main Phase

A Main Phase is a complete research or engineering objective.

Examples:

- `Regime Layer Phase 3`
- `Project Context Persistence Phase`
- `Regime Layer Phase 3.5`

Allowed Main Phase states:

- `NOT_STARTED`: not started.
- `IN_PROGRESS`: at least one batch has started or is being executed.
- `BLOCKED`: explicit blocker exists; do not auto-advance.
- `COMPLETE`: all required batches completed or legally skipped, final closeout passed, consistency check passed, and phase decision exists or is explicitly not required.
- `ABORTED`: whole Main Phase explicitly terminated.

Forbidden machine states:

- `DONE`
- `FINISHED`
- `OK`
- `MOSTLY_DONE`
- percentage states such as `80%`

## Execution Batch

An Execution Batch is a small Codex execution unit inside a Main Phase.

Allowed Batch states:

- `PENDING`: not started.
- `IN_PROGRESS`: actively being worked.
- `COMPLETE`: goals and validation passed.
- `BLOCKED`: explicit blocker prevents progress.
- `SKIPPED`: intentionally skipped with an explicit `skip_reason`.

Do not mark a batch `COMPLETE` just because a Codex response was lost.

## Batch Internal Checkpoint

An Execution Batch may contain internal checkpoints when needed for recovery drills or final closeout work. These checkpoints do not replace the Batch state machine.

For example:

```text
Context Phase D
├── Context Phase D1
├── Context Phase D2
├── Context Phase D3
└── Context Phase D4
```

`resume_from` remains the Execution Batch resume point.

`phase_d_resume_checkpoint` records the current internal checkpoint inside `Context Phase D`.

Do not mark internal future checkpoints complete. If D1 and D2 are complete, the valid checkpoint state is:

```text
phase_d_completed_checkpoints = [
  "Context Phase D1",
  "Context Phase D2"
]
phase_d_resume_checkpoint = "Context Phase D3"
```

This means a new thread should resume `Context Phase D` from D3. It does not mean `Context Phase D` is complete.

## Main Phase + Batch Relationship

A Main Phase may be marked `COMPLETE` only when all are true:

1. all required batches are `COMPLETE` or legally `SKIPPED`;
2. the Final Closeout Batch is `COMPLETE`;
3. context consistency check passes;
4. phase decision exists or is explicitly `not_required`.

Otherwise, do not mark the Main Phase `COMPLETE`.

## Batch Completion Protocol

Batch completion must follow this order:

1. Complete the Batch goal.
2. Run Batch-specific validation.
3. Check protected files and safety boundary.
4. Generate or update Batch report.
5. Confirm no blocking conflict.
6. Update `docs/current_project_state.md` only for genuinely changed current project facts.
7. Update `docs/current_phase_status.json`.
8. Mark current batch `COMPLETE`.
9. Append current batch to `completed_batches`.
10. Set `last_completed_batch` to the current batch.
11. Remove current batch from `pending_batches`.
12. Point `current_batch` and `resume_from` to the next batch.
13. Set `current_batch_status = PENDING`.
14. Update `context_updated_at` and `context_update_reason`.
15. Run context consistency check.

## Response-Lost Recovery

If Codex response stream disconnects after files may have changed, do not assume the batch is complete.

First inspect:

- worktree side effects;
- expected outputs;
- validation results.

Recovery classifications:

- `PARTIAL SIDE EFFECT`
- `COMPLETE BUT RESPONSE LOST`
- `VALIDATION MISSING`

These classifications are for recovery analysis only. The final batch state must still be one of:

```text
PENDING
IN_PROGRESS
COMPLETE
BLOCKED
SKIPPED
```

Do not blindly repeat the whole batch. Resume from verified state.

## Decision Promotion

A Phase decision JSON can influence:

- `docs/current_project_state.md`;
- `docs/current_phase_status.json`.

It cannot overwrite context unconditionally.

### Rule A: Explicit Decision Required

Readiness fields may only come from:

- explicit decision JSON; or
- explicit formal authorization.

Do not infer readiness from:

- script existence;
- a report looking good;
- App or dashboard display;
- code being present.

### Rule B: Newest Explicit Phase Wins

A newer explicit decision may advance current research state if phase lineage is clear.

Example:

- Phase 2 decision: `ready_for_regime_fit_phase = true`
- Phase 3 decision: `ready_for_adjusted_preview_research = true`

Do not use modified time alone. Use:

- phase lineage;
- phase id;
- decision metadata;
- explicit supersedes relationship.

### Rule C: False Safety Gate Is Sticky

The following fields are sticky safety gates:

- `ready_for_preview`
- `ready_for_execution`
- `execution_allowed`

If the current authoritative decision is `false`, ordinary research reports or UI state must not turn it `true`.

Only a higher-stage explicit decision or formal authorization may change it.

Especially:

```text
ready_for_execution = false
```

is sticky by default.

### Rule D: Research Permission Is Not Execution Permission

```text
ready_for_adjusted_preview_research = true
```

does not equal:

```text
ready_for_preview = true
```

and never equals:

```text
ready_for_execution = true
```

Similarly, `ready_for_preview = true` would not imply `ready_for_execution = true`.

### Rule E: Decision Conflict Blocks Promotion

If two authoritative decision JSON files conflict on the same readiness field and phase lineage cannot resolve it:

```text
promotion_blocked = true
```

Do not guess. Generate a conflict audit.

## Current Project State Update Protocol

`docs/current_project_state.md` records current project facts that still hold.

It is not a detailed operation log.

Must update when any of these change:

- formal model state;
- Main Phase;
- selected shadow candidate;
- research architecture;
- important decision;
- readiness;
- major bottleneck;
- next research direction.

Usually no update required for:

- a single report file addition;
- one `npm run build`;
- one compile run;
- small UI styling;
- log archive;
- bug fix that does not change research conclusions.

Snapshot fields such as current regime, BUY Top10 conflict count, current portfolio fit, and latest data date must include:

```text
as of YYYY-MM-DD
```

Do not write `current`, `now`, or `latest` without a date and source.

## Staleness Protocol

Latest known does not mean live current.

Example:

```text
latest_known_shadow_regime = NEUTRAL
latest_known_regime_date = 2026-07-06
```

If:

```text
latest_data_date > latest_known_regime_date
```

then:

```text
regime_snapshot_stale = true
```

Do not tell a new thread:

```text
current regime = NEUTRAL
```

Say:

```text
latest known regime as of 2026-07-06 = NEUTRAL
```

Required staleness flags:

- `regime_snapshot_stale`
- `project_state_snapshot_stale`
- `phase_status_stale`
- `decision_state_conflict`
- `context_consistency_unknown`

Phase B defines these fields and rules only. Automatic validation belongs to a later phase.
