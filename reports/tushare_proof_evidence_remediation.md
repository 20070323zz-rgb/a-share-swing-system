# Tushare Proof Evidence Isolation And PIT Contract Remediation

## Decision

```text
Implementation status = COMPLETE
Evidence Isolation = COMPLETE
PR #2 = DRAFT_AWAITING_RE_QC
Merge Readiness QC = READY_FOR_INDEPENDENT_RE_QC
Formal Staging Architecture = NOT_STARTED
```

This batch fixes PR #2 forward without rebasing, force-pushing, squashing, dropping commits, moving historical run directories, modifying historical raw payloads, or calling the real Tushare API.

## Original Defects

The original runner used the production `TushareMinimalClient` for both real and mock runs and only replaced its transport in mock tests. A mock fixture token therefore made `token_configured=true`; mock responses could emit `ACCESS_PASS`, reach the unqualified `COMPLETE` status, use a `real-*` run ID, overwrite the global real reports, and enter the directory-scanned aggregate request count. Real and mock output paths were distinguished only by user-chosen run ID text. Shibor documentation also conflated the project noon lag with the official release time, historical real runs lacked per-run commit-safe attestations, and the 1350-to-900 `index_weight` reduction lacked a durable reason record.

## Remediation Mechanism

- `evidence_mode` is required by the runner API and CLI and accepts only `real` or `mock`; the config declares exact allowed modes, requires explicit selection, and maps distinct output namespaces.
- Run IDs are generated or strictly validated. A real run requires `real-<date-or-timestamp>-<suffix>` and a mock run requires `mock-<date-or-timestamp>-<suffix>`.
- Real mode loads a Token from the secure provider before creating output directories and uses the production client. Mock mode uses a separate fixture-only client that has no Token-provider or network-transport path.
- New output roots are `data/staging/tushare_minimal_proof/real/<run_id>/` and `data/staging/tushare_minimal_proof/mock/<run_id>/`. Each contains separate raw, normalized, PIT, validation, manifest, and report-evidence directories.
- Mock statuses are limited to `MOCK_VALIDATION_PASS` and `MOCK_VALIDATION_FAILED`; real statuses are limited to `REAL_PROOF_COMPLETE`, `REAL_PROOF_PARTIAL`, `REAL_PROOF_FAILED`, and `REAL_PROOF_BLOCKED`.
- Mock permission is always `NOT_APPLICABLE_MOCK`; mock reports cannot contain real permission conclusions and cannot overwrite global real reports.
- Call fields are split into `real_api_call_count`, `mock_call_count`, `per_run_real_call_count`, `batch_aggregate_real_call_count`, `configured_real_budget`, and `budget_status`. The aggregate real count is sourced from committed real-run attestations, not by scanning mixed run directories.

## Existing Real Results

The existing real conclusion did not change. The final real run remains `real-20260713-minimal-proof-v3`, with eight accessible interfaces, `17/30` calls, and remediated status `REAL_PROOF_COMPLETE`. The three retained real manifests each record 17 calls, explaining `17 + 17 + 17 = 51` and preserving `AGGREGATE_BUDGET_WARNING`.

The first two run-specific proof reports were not retained by the historical global-report workflow. Their attestations use retained immutable manifest hashes and explicitly mark the missing report hashes `UNAVAILABLE / AVAILABLE_EVIDENCE_LIMITED`. No missing hash or line-level evidence was fabricated. The final run has both its local manifest hash and a hash of the remediated commit-safe proof report.

## `index_weight` Reduction

The final real queries each covered `2026-04-01` through `2026-07-10` and exposed snapshots dated `2026-04-30`, `2026-05-29`, and `2026-06-30`. Policy `PROOF_DATE_WINDOW_V1` retains the latest two dates and excludes the earlier date:

| Index | Raw | Proof | Excluded |
|---|---:|---:|---:|
| 000300.SH | 900 | 600 | 300 |
| 399006.SZ | 300 | 200 | 100 |
| 000688.SH | 150 | 100 | 50 |
| Total | 1350 | 900 | 450 |

The reason is `PROOF_SAMPLE_DATE_WINDOW_REDUCTION`, not deduplication, corruption, weight normalization, null removal, or unexplained loss. Future normalized manifests store raw/proof/excluded counts, visible/selected/excluded dates, query range, reason, and policy version.

## Shibor Contract

The official release time is `11:00 Asia/Shanghai`. The project applies a 60-minute conservative lag and uses `12:00 Asia/Shanghai`, with `pit_basis = OFFICIAL_11AM_PLUS_PROJECT_LAG`; actual `retrieved_at` remains a separate field. Shibor remains `EXPLANATION_ONLY / INTEREST_RATE_CONTEXT` and is not ETF duration exposure.

## State Boundary

```text
Tushare Minimal Staging Proof = COMPLETE
PIT Contract = COMPLETE_WITH_LIMITATIONS
Evidence Isolation = COMPLETE
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

PIT Contract completion is not evidence that Formal Staging Architecture has started.

## Validation

- Tushare/evidence/PIT regression tests: `30 passed`.
- Real-mode dry run: `estimated_real_api_calls=17/30`; no Token read and no API call.
- Mock run: `MOCK_VALIDATION_PASS`, `real_api_call_count=0`, `mock_call_count=16`, aggregate real calls unchanged at 51.
- Mock overwrite check: the real proof report, real manifest, and permission audit hashes were identical before and after the mock run.
- Full test suite: `53 passed`, `8 subtests passed`; the only two warnings are the existing non-collectable helper dataclasses.
- Evidence-isolation selection: `9 passed`; PIT selection: `8 passed`; complete Tushare test file: `30 passed`.
- Secret-like credential scan: `0` changed-file hits. Private absolute-path scan: `0` changed-file hits. Tracked Tushare proof raw payload files: `0`.
- `git diff --check`: `PASS`.
- ETF SSOT: `183` CSV files; aggregate hash `21702d2d2760c9c10ac62708c45fcaff35fb53aabfec13c8e474458b319d8855`, unchanged.
- Protected-file incremental diff: `0`. Model, Replay, Ranking, Score, Exposure, and Formal Execution incremental path diff: `0`.
- Context validation/bootstrap: `VALID_WITH_WARNINGS`; the only warning is the pre-existing stale Regime snapshot dated 2026-07-06.
- `.envTAB`: content was not read; exact `.gitignore` and local exclude rules remove it from `git status`, and it is not tracked or staged.
- GitHub PR #2 was initially `MERGEABLE / CLEAN` and remains Draft; final mergeability is rechecked after the remediation commits are pushed.

## Remaining Limitations

The first two real run-specific proof reports remain unavailable. Historical real run directories retain the legacy flat layout by explicit non-migration requirement; only new runs use mode namespaces. Taxonomy publication history and snapshot publication times remain incomplete, so the PIT limitations and Data Promotion block remain unchanged. Independent second-round QC is still required before PR #2 can be moved out of Draft.
