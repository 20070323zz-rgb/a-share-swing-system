# Operational Playbook

Created at: 2026-07-08

This playbook records project practices that have proven useful in this repository. It is practical memory, not strategy theory.

## 1. ETF Data Single Source Of Truth

The project maintains one ETF daily data source:

```text
data/etf_daily/*.csv
```

All universes, research phases, replay, robustness, shadow, preview, and formal systems must reference this shared source. Universe versions may store configuration, metadata, selection decisions, and qualification state. They must not store copied daily bars or create a second ETF database.

## 2. Universe Versioning Preserves History

Universe V1 remains a locked historical baseline for Phase 3 and Phase 3.5.

Universe V2 is stored separately as candidate and registry metadata. New universe work must not overwrite prior universe definitions. Research reports should identify the universe version they use.

## 3. Large Replay Uses Small Batches And Checkpoints

Large replay should not be run as one long all-or-nothing job.

Preferred pattern:

```text
small batch -> checkpoint -> validate -> completion marker -> next batch
```

This supports interruption recovery and avoids blind reruns.

## 4. One Batch, One Core Objective

Each batch should have one primary goal:

- design;
- qualification;
- replay preparation;
- replay execution;
- recovery validation;
- governance.

Avoid mixing research conclusions, strategy changes, data downloads, and execution changes in the same batch unless explicitly approved.

## 5. Phase Completion Should Leave A Research Journal Or Durable Summary

Important research phases should leave a durable artifact that explains:

- what question was answered;
- what evidence was used;
- what conclusion was reached;
- what remains blocked;
- what future work is allowed or forbidden.

This avoids losing reasoning when a long conversation becomes unavailable.

## 6. Long Threads Need Early Checkpoints

Do not wait for context failure before writing checkpoints.

For long work:

- write status files or reports early;
- record current input and output paths;
- make partial completion explicit;
- keep restart points clear.

## 7. Recovery Validation Comes Before Rerun

After interruption or response loss, do not assume failure and do not blindly rerun.

First inspect:

- worktree state;
- expected output files;
- validation state;
- checkpoint state;
- duplication risk.

Only resume missing work after the repository state says what is actually missing.

## 8. Execution Boundaries Stay Explicit

Research readiness is not execution readiness.

Keep these states separate:

```text
READY_FOR_REPLAY_PREPARATION
READY_FOR_REPLAY
READY_FOR_PREVIEW
READY_FOR_EXECUTION
```

A research artifact must not imply trade-pool activation, preview creation, score changes, ranking changes, or formal execution unless a batch explicitly authorizes that transition.

## 9. Warnings Should Stay Dated

If a state snapshot is stale, keep the date attached.

Example:

```text
latest_known_regime_date = 2026-07-06
latest_data_date = 2026-07-08
```

Do not describe stale regime state as live current regime.

## 10. Protected Files Require Extra Care

Protected execution files should not be touched during research batches:

```text
src/paper_trade_engine.py
data/paper_trades.csv
data/paper_positions.csv
```

If they are already dirty before a research batch, report that fact separately from the current batch changes.

## 11. Paper Execution Requires A Freshness Gate

Paper execution must not infer that a calendar date has current market data.

Before invoking the paper engine, require all of the following:

- expected trade date confirmed or conservatively classified;
- market data date equals the expected trade date;
- failed and pending update counts are zero;
- formal execution universe coverage is complete;
- signal and ranking dates equal the expected trade date;
- every held or ranked candidate symbol has an expected-date bar;
- all critical files are readable and structurally valid.

Any failure blocks the whole engine run. Do not partially execute, use a prior-day fallback, or rewrite historical paper trades. Historical execution issues belong in append-only audit records until Main approves a correction policy.
