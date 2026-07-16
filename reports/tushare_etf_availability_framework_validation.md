# Tushare ETF Availability Audit Framework Validation

## Verdict

`PASS / ACTIVE_COLLECTING`

The observation framework is implemented. The timing study remains active. Tushare is approved as primary upstream by user authorization at the architecture level; migration and formal promotion are not implemented.

## Initial Evidence

| Item | Result |
|---|---|
| Branch | `agent/tushare-etf-availability-audit` |
| Draft PR | `#3` |
| Trade calendar | 2026-07-14 confirmed open by Tushare `trade_cal` |
| Dynamic Universe mapping | 183 / 183 |
| Shanghai / Shenzhen | 92 / 91 |
| Unmapped roles / duplicate codes | 0 / 0 |
| First real slot | 2026-07-14 15:05 CST |
| Tushare interface | `fund_daily` |
| Real calls in first slot | 1 |
| Permission | `ACCESS_PASS` |
| Response | `EMPTY_UNEXPECTED` |
| Source rows / matched required ETFs | 0 / 0 |
| Coverage | 0.0% |
| Observation days started / completed | 2 / 2 |
| Timing evidence | `INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION` |

The 15:05 result means the target-date daily table was not yet published through the tested call. It is valid first-slot timing evidence, not a network failure, and it did not trigger BaoStock fallback or any SSOT write.

## Preserved Two-Day Evidence

| Item | Current result |
|---|---|
| Tushare slots recorded | 10 / 10 on both days |
| Empty Tushare slots | 15:05, 15:15, 15:30, 15:45, 16:00 on both days |
| FIRST_AVAILABLE | 16:15 on both days |
| FIRST_COMPLETE | 16:15 on both days |
| FIRST_QUALITY_COMPLETE | 16:15 on both days |
| 16:15 / 16:30 snapshot relationship | deterministic hashes equal |
| FIRST_STABLE_TIME | 16:30 on both days under the confirmation-point definition |
| SH / SZ first complete | 16:15 / 16:15 |
| Individually delayed codes after first availability | none; all 183 arrived together |
| Later Tushare snapshots | unchanged through 18:00 on both days |

The original two-day evidence is retained without deletion. The new definition records the confirmation slot, not the first-complete slot. Any later hash change changes the state to `REVISION_DETECTED` and invalidates the earlier stable time until another consecutive identical pair confirms stability again.

## Call Budgets

- Tushare calendar refresh: at most one `trade_cal` request per explicit refresh.
- Tushare timing slot: exactly one whole-date `fund_daily` request, then local filtering.
- BaoStock comparator slot: at most the dynamically discovered required ETF count, currently 183 per-symbol requests.
- Duplicate slot: zero vendor requests and an append-only `DUPLICATE_ATTEMPT_SKIPPED` manifest.
- Early slot: zero vendor requests and an append-only `BLOCKED_EARLY_PROBE` manifest.

## Scheduling Validation

The committed LaunchAgent template contains eight Asia/Shanghai triggers: core probes at 16:00, 16:05, 16:10, 16:15, 16:30, and 17:00, followed by conditional 17:30 and 18:00 probes. The 15:30 point is excluded from the daily Availability timing window and retained only as an explicit low-frequency health check.

The first launchd kickstart exposed that macOS launchd selected `/usr/bin/python3` without pandas. It exited before any vendor request. The wrapper was changed to select only an existing interpreter that imports both pandas and yaml. A second launchd run exited `0` and produced only `DUPLICATE_ATTEMPT_SKIPPED`, proving the installed entry and slot idempotency without making a second Tushare call. The original local traceback remains in the append-only operational log as pre-fix evidence.

## Boundary Validation

| Boundary | Result |
|---|---|
| `data/etf_daily/` sorted-file aggregate SHA-256 | `c6edaac39416bfc20f335ed8a748bef59226802cf163f8b5ff91ed990110c473` before and after; diff 0 |
| `src/paper_trade_engine.py` SHA-256 | `93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926` unchanged |
| `data/paper_trades.csv` SHA-256 | `db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5` unchanged |
| `data/paper_positions.csv` SHA-256 | `a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906` unchanged |
| Paper engine invoked | false |
| Wrote to ETF SSOT | false |
| Formal automation entry changed | false |
| Token in committed outputs | none |
| Real raw vendor payload committed | none |
| New private absolute path in Git diff | none |

## Test Results

- Availability-audit targeted tests: `22 passed`.
- Availability audit plus minimal-proof regression tests: `52 passed`.
- Full project suite: `75 passed`, `8 subtests passed`.
- Coverage includes the new schedule, confirmation-point stability, revisions, conditional stops, no SSOT writes, no BaoStock fallback, and fail-closed `DATA_NOT_READY`.
- Existing pytest collection warnings: 2 (`TestResult` helper classes in the JQData and QMT diagnostic scripts).
- Project context: `VALID_WITH_WARNINGS`.
- Only context warning: existing stale Regime snapshot warning.
- Python compile, shell syntax, plist lint, and Git diff check: pass.
- Installed LaunchAgent: reloaded from the eight-trigger template; loaded and idle, with no install-time vendor call.

## Current Decision

```text
ETF Daily Availability Timing Audit = ACTIVE_COLLECTING
Statistical Evidence Verdict = INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION
Tushare = APPROVED_PRIMARY_UPSTREAM
Decision Evidence Confidence = LIMITED_TWO_DAY_EVIDENCE
Decision Authority = USER_AUTHORIZED_EARLY_PROMOTION
BaoStock = RECONCILIATION_ONLY
data/etf_daily = CANONICAL_SSOT
Tushare Primary Upstream Migration = AUTHORIZED_NOT_STARTED
Timing Optimization = ACTIVE
Data Promotion = BLOCKED_PENDING_IMPLEMENTATION_VALIDATION
Formal Execution Logic = UNCHANGED
```

Five completed valid trading days are required for a preliminary timing-window review; ten remain the supported timing-candidate gate. These gates do not reopen the primary-source decision. The initial migration design candidate is 16:15 staging, 16:30 confirmation/validation and future atomic-promotion candidate, and 18:00 fail-closed manual review.
