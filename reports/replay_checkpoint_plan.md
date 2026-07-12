# Replay Checkpoint Plan

Generated at: 2026-07-08 19:05:00 CST

Scope: checkpoint and recovery design for future Universe V2 Replay execution. This plan does not run replay.

## Checkpoint Philosophy

Universe V2 Replay must use a small-batch checkpoint model. The goal is to avoid long, fragile replay runs where a late failure forces a full rerun. Each batch should leave enough state to answer:

- Which exact symbols were intended?
- Which inputs were read?
- Which outputs were produced?
- Did validation pass?
- Is the batch safe to aggregate?
- If interrupted, what is the nearest safe restart point?

## Batch Checkpoint Contract

Each replay batch should have this checkpoint contract:

| Checkpoint | Purpose | Required before next step |
| --- | --- | --- |
| `input_manifest` | Freezes symbols, registry version, data source, date window, and excluded classes | yes |
| `data_coverage_check` | Confirms all batch symbols exist in `data/etf_daily/`, share required date coverage, and have no duplicate dates | yes |
| `feature_build_check` | Confirms regime/style/replay features are computable for the batch | yes |
| `replay_output_check` | Confirms replay output row counts, symbol counts, and date ranges | yes |
| `label_maturity_check` | Confirms forward-label windows are mature and not forward-filled incorrectly | yes |
| `batch_validation_summary` | Human/machine-readable pass/fail summary | yes |
| `completion_marker` | Final marker that this batch may be included in aggregate V2 evaluation | yes |

## Planned Batch Artifacts

No artifacts below are created in Phase 5.1. They are future paths for the actual replay batch.

For each batch id, use:

```text
reports/universe_v2_replay/<batch_id>/input_manifest.json
reports/universe_v2_replay/<batch_id>/data_coverage_check.json
reports/universe_v2_replay/<batch_id>/feature_build_check.json
reports/universe_v2_replay/<batch_id>/replay_output_check.json
reports/universe_v2_replay/<batch_id>/label_maturity_check.json
reports/universe_v2_replay/<batch_id>/batch_validation_summary.md
reports/universe_v2_replay/<batch_id>/completion_marker.json
```

## Batch Definitions

### V2-RP-01

Input symbols:

```text
159593, 159531, 561560, 159516
```

Expected validation:

- 4 symbols only.
- No QDII symbols.
- No `OBSERVE` or `REJECT` symbols.
- Data source paths all under `data/etf_daily/`.
- Completion marker may be written only after data, feature, replay, and label checks pass.

### V2-RP-02

Input symbols:

```text
510050, 588220, 562550, 588200
```

Expected validation:

- 4 symbols only.
- No QDII symbols.
- No `OBSERVE` or `REJECT` symbols.
- Data source paths all under `data/etf_daily/`.
- Completion marker may be written only after data, feature, replay, and label checks pass.

### V2-RP-03

Input symbols:

```text
515630, 159732, 561360, 159638
```

Expected validation:

- 4 symbols only.
- No QDII symbols.
- No `OBSERVE` or `REJECT` symbols.
- Data source paths all under `data/etf_daily/`.
- Completion marker may be written only after data, feature, replay, and label checks pass.

### V2-RP-04

Input symbols:

```text
159547, 159608, 159667, 515260
```

Expected validation:

- 4 symbols only.
- No QDII symbols.
- No `OBSERVE` or `REJECT` symbols.
- Data source paths all under `data/etf_daily/`.
- Completion marker may be written only after data, feature, replay, and label checks pass.

## Recovery Rules

If a batch is interrupted:

1. Read `input_manifest.json`.
2. Read the latest completed checkpoint in the batch directory.
3. Resume from the first missing or failed checkpoint.
4. Do not rerun earlier passed checkpoints unless their upstream input changed.
5. Do not aggregate partial batch outputs.
6. Do not rerun all V2 replay batches unless a shared upstream dependency changed.

If a checkpoint fails:

- Mark the batch as `FAILED_VALIDATION`.
- Preserve existing artifacts for diagnosis.
- Do not write `completion_marker.json`.
- Do not proceed to aggregate V2 comparison.

## Aggregate Checkpoint

Aggregate V2 evaluation should begin only after all completion markers exist:

```text
reports/universe_v2_replay/batch_v2_rp_01/completion_marker.json
reports/universe_v2_replay/batch_v2_rp_02/completion_marker.json
reports/universe_v2_replay/batch_v2_rp_03/completion_marker.json
reports/universe_v2_replay/batch_v2_rp_04/completion_marker.json
```

Aggregate should then create:

```text
reports/universe_v2_replay/aggregate/aggregate_manifest.json
reports/universe_v2_replay/aggregate/v1_vs_v2_input_alignment.json
reports/universe_v2_replay/aggregate/generalization_validation_summary.md
```

## Non-Negotiable Guards

- Never write to `data/backtest_trade_pool.csv`.
- Never write to Universe V1 version files.
- Never write to Formal Execution files.
- Never include `OBSERVE`, `REJECT`, or QDII in this V2 replay path.
- Never treat `READY_FOR_REPLAY_PREPARATION` as `READY_FOR_REPLAY`.
