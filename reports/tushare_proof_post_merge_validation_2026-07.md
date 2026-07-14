# Tushare Proof Post-Merge Validation — 2026-07

## Outcome

- PR: `#2 Tushare minimal staging proof and PIT contract`
- PR state: `MERGED`
- PR head reviewed and merged: `9701a3ed42be268f83ff3f9b28dcb888e0e05618`
- GitHub merge commit: `47d129bfa7a055b7af81f4c57fea3a95d41287c6`
- Merged at: `2026-07-14 14:00:33 CST`
- Post-merge validation base: `main@47d129bfa7a055b7af81f4c57fea3a95d41287c6`
- Result: `PASS`
- Main status: `STABLE`
- Real Tushare API calls during this batch: `0`

## Live Pre-Merge Gate

Immediately before merge, GitHub reported `OPEN`, Ready for review, `MERGEABLE`, and `CLEAN`; base was `main`, head was `9701a3ed42be268f83ff3f9b28dcb888e0e05618`, and no checks were configured. The range remained 7 commits and 28 files with no unreviewed commit. `git diff --check` passed. Token/raw/private-path, protected-file, ETF SSOT, and architecture-boundary checks all remained clean.

The PR was merged with `gh pr merge 2 --merge`. No squash, rebase, admin merge, force-push, or branch-content change was used.

## Validation Results

| Check | Result |
|---|---|
| Full pytest | `53 passed`, `8 subtests passed`, 2 existing collection warnings |
| Tushare test file | `30 passed` |
| Evidence-isolation selection | `10 passed`, 20 deselected |
| PIT selection | `8 passed`, 22 deselected |
| Mock proof execution | `MOCK_VALIDATION_PASS`, 16 mock calls, 0 real calls |
| Dashboard build | PASS |
| Frontend production build | PASS, 1,835 modules transformed |
| App release check | PASS |
| Manual-import validation | `52 valid, 0 failed` |
| `git diff --check` | PASS |
| Context validation/bootstrap | `VALID_WITH_WARNINGS`; no errors or blocking conflict |

The two pytest warnings are the existing non-collectable helper dataclasses in `scripts/test_jqdata_etf_daily.py` and `scripts/test_qmt_xtdata.py`. The only Context warning is the existing stale Regime snapshot dated `2026-07-06`.

## Evidence Isolation and PIT

The post-merge mock run recorded:

```text
evidence_mode = mock
status = MOCK_VALIDATION_PASS
real_api_call_count = 0
mock_call_count = 16
per_run_real_call_count = 0
batch_aggregate_real_call_count = 51
budget_status = NOT_APPLICABLE_MOCK
token_configured = false
```

The committed real proof report, real manifest, and real permission-audit hashes were identical before and after the mock run. Mock evidence did not overwrite or enter the real proof conclusion or cumulative real-call count.

The PIT Contract remains `COMPLETE_WITH_LIMITATIONS`: `fund_portfolio` retains announcement-date versions; `daily_basic` and `index_daily` use the next-trading-day conservative rule; `index_weight` and membership remain partial without historical publication time; taxonomy remains unresolved for historical backfill; Shibor remains official 11:00 plus the project's 60-minute conservative lag to 12:00 and is `EXPLANATION_ONLY`.

## Secret, Raw Payload, and Path Governance

- Exact credential literal hits across reachable Git history: `0`.
- Tracked `.env`, `.env.*`, or `.envTAB`: `0`.
- Tracked files under `data/staging/tushare_minimal_proof/`: `0`.
- Tracked real raw proof payloads: `0`.
- New private absolute-path additions in the merge range: `0`.
- `git diff --check`: PASS.

## ETF SSOT and Protected Files

The canonical Git-tree ETF algorithm sorts repository-relative `data/etf_daily/*.csv` paths, hashes each exact blob, emits `<sha256><two spaces><relative_path><LF>`, and hashes the complete manifest.

```text
ETF CSV count = 183
ETF canonical SHA-256 = 21702d2d2760c9c10ac62708c45fcaff35fb53aabfec13c8e474458b319d8855
PR merge-range ETF paths changed = 0
```

Protected Git-tree hashes:

```text
src/paper_trade_engine.py = 93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926
data/paper_trades.csv      = db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5
data/paper_positions.csv   = a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906
```

Model, Replay, Ranking, Score, Exposure, Formal Execution, protected files, and ETF SSOT merge-range diffs are all `0`. The user's existing local runtime snapshots, including ETF and paper-position working-tree updates, were preserved and excluded from the governance commit.

## Final State and Remaining Limitations

```text
PR #2 = MERGED
Post-Merge Validation = PASS
Main = STABLE
Tushare Proof Evidence = ACCEPTED
Tushare Minimal Staging Proof = COMPLETE
PIT Contract = COMPLETE_WITH_LIMITATIONS
Formal Staging Architecture = NOT_STARTED
ETF Daily Availability Timing Audit = NEXT / NOT_STARTED
Tushare Primary Upstream Migration = APPROVED_IN_PRINCIPLE_BUT_NOT_STARTED
Data Foundation Upgrade = NOT_STARTED
Data Promotion = BLOCKED
Exposure Phase 2 = NOT_STARTED
```

The first two real run-specific proof reports remain unavailable and honestly attested as limited evidence. Historical publication timestamps remain incomplete for index weights and taxonomy. These limitations continue to block data promotion.

`ETF Daily Availability Timing Audit` is the next eligible research batch, but this closeout does not start it. A separate authorized Batch instruction is required. Formal staging, primary-source migration, Data Foundation Upgrade, data promotion, and Exposure Phase 2 remain outside this batch.
