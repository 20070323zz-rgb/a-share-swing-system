# Tushare Minimal Staging Proof

- Evidence mode: `real`
- Final real run: `real-20260713-minimal-proof-v3`
- Final status: `REAL_PROOF_COMPLETE`
- Final-run real API calls: `17 / 30`
- Attested aggregate real API calls: `51`
- Aggregate budget status: `AGGREGATE_BUDGET_WARNING`
- Mock calls included in either real count: `NO`
- ETF daily SSOT write: `NONE`
- Formal / Strategy / Replay integration: `NONE`

## Interface Results

The permission verdicts below come only from the retained real run. A mock run uses `NOT_APPLICABLE_MOCK`, cannot emit `ACCESS_PASS`, and cannot overwrite this report.

| Interface | Access | Permission | Raw rows | Proof rows | Schema | PIT |
|---|---|---|---:|---:|---|---|
| index_basic | ACCESS_PASS | ACCESS_PASS | 693 | 693 | ACCESS_PASS | PIT_UNRESOLVED |
| index_daily | ACCESS_PASS | ACCESS_PASS | 6 | 6 | ACCESS_PASS | PIT_CONSERVATIVE / PIT_PARTIAL |
| index_weight | ACCESS_PASS | ACCESS_PASS | 1350 | 900 | ACCESS_PASS | PIT_PARTIAL |
| index_classify | ACCESS_PASS | ACCESS_PASS | 31 | 31 | ACCESS_PASS | PIT_UNRESOLVED |
| index_member_all | ACCESS_PASS | ACCESS_PASS | 517 | 517 | ACCESS_PASS | PIT_PARTIAL |
| daily_basic | ACCESS_PASS | ACCESS_PASS | 3 | 3 | ACCESS_PASS | PIT_PARTIAL |
| fund_portfolio | ACCESS_PASS | ACCESS_PASS | 538 | 538 | ACCESS_PASS | PIT_RESOLVED |
| shibor | ACCESS_PASS | ACCESS_PASS | 11 | 11 | ACCESS_PASS | PIT_CONSERVATIVE |

## Real Run Attestation And Call Budget

Three immutable local real runs each recorded 17 calls, explaining the attested aggregate of 51. The final run remained within its configured per-run cap at 17/30. The aggregate exceeded the suggested 30-call batch target, so the retained status remains `AGGREGATE_BUDGET_WARNING`. Counts are sourced from `reports/tushare_real_run_attestations.csv`; mock manifests and mock directories are never scanned into the real total.

The first two run-specific proof reports were overwritten by the historical global-report workflow and cannot be reconstructed line by line. Their retained manifests and local artifact hashes support call-count attestation, but the attestation marks their report evidence `AVAILABLE_EVIDENCE_LIMITED` rather than inventing missing hashes.

## `index_weight` 1350 To 900 Reduction

The three real queries covered `2026-04-01` through `2026-07-10` and exposed three snapshots per index: `2026-04-30`, `2026-05-29`, and `2026-06-30`. Policy `PROOF_DATE_WINDOW_V1` retained the most recent two snapshots and excluded the earlier snapshot.

| Index | Raw | Proof | Excluded | Selected dates | Excluded date |
|---|---:|---:|---:|---|---|
| 000300.SH | 900 | 600 | 300 | 2026-05-29, 2026-06-30 | 2026-04-30 |
| 399006.SZ | 300 | 200 | 100 | 2026-05-29, 2026-06-30 | 2026-04-30 |
| 000688.SH | 150 | 100 | 50 | 2026-05-29, 2026-06-30 | 2026-04-30 |
| Total | 1350 | 900 | 450 | latest two snapshots | earlier snapshot |

The reduction reason is `PROOF_SAMPLE_DATE_WINDOW_REDUCTION`. It is not deduplication, data corruption, weight-normalization deletion, null deletion, or unexplained row loss. Per-index evidence is committed in `reports/tushare_index_weight_reduction_evidence.csv`, and future per-call normalized manifests retain raw/proof/excluded counts and selected/excluded dates.

## Shibor PIT Contract

- Official release time: `11:00 Asia/Shanghai`
- Project conservative available time: `12:00 Asia/Shanghai`
- Conservative lag: `60 minutes`
- PIT basis: `OFFICIAL_11AM_PLUS_PROJECT_LAG`
- `retrieved_at`: recorded separately for every call
- Usage: `EXPLANATION_ONLY / INTEREST_RATE_CONTEXT`

The project noon timestamp is a conservative project rule, not the official release time. Shibor is not described as ETF duration exposure.

## Evidence And Phase Boundaries

```text
Tushare Minimal Staging Proof = COMPLETE
PIT Contract = COMPLETE_WITH_LIMITATIONS
Evidence Isolation = COMPLETE
PR #2 = DRAFT_AWAITING_RE_QC
Formal Staging Architecture = NOT_STARTED
Tushare Primary Upstream Migration = APPROVED_FOR_FUTURE_ENGINEERING / NOT_STARTED
ETF Daily Availability Timing Audit = NOT_STARTED
Data Foundation Upgrade = NOT_STARTED
Data Promotion = BLOCKED
Exposure Phase 2 = NOT_STARTED
Regime 2.0 = NOT_STARTED
Universe V3 = NOT_STARTED
Exit Logic = NOT_STARTED
Style Fit 1.0 = CLOSED
```

PIT Contract completion does not start Formal Staging Architecture. Real raw responses and row-level artifacts remain Git-ignored in their historical directories; they were not moved, renamed, overwritten, or committed. New real and mock runs are separated under `real/<run_id>/` and `mock/<run_id>/` respectively, including their report-evidence directories.

## Remaining Limitations

Taxonomy publication history and index snapshot publication timestamps remain unavailable. `index_weight` and `index_member_all` stay `PIT_PARTIAL`; `index_classify` and `index_basic` stay unresolved for historical publication time. The latest daily rows remain partial when the local calendar snapshot has no next trading day. These limitations block data promotion and do not authorize any next phase.
