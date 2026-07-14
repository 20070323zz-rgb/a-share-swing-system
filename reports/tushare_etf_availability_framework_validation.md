# Tushare ETF Availability Audit Framework Validation

## Verdict

`PASS / ACTIVE_COLLECTING`

The observation framework is implemented and installed. The timing study is not complete and no primary-source recommendation is authorized.

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
| Observation days started / completed | 1 / 0 |
| Timing evidence | `COLLECTING_INSUFFICIENT_DAYS` |

The 15:05 result means the target-date daily table was not yet published through the tested call. It is valid first-slot timing evidence, not a network failure, and it did not trigger BaoStock fallback or any SSOT write.

## Same-Day Progress Through 16:30

| Item | Current result |
|---|---|
| Tushare slots recorded | 7 / 10 |
| Empty Tushare slots | 15:05, 15:15, 15:30, 15:45, 16:00 |
| Provisional first available | 16:15 |
| Provisional first complete | 16:15 |
| Provisional first field-quality complete | 16:15 |
| 16:15 / 16:30 snapshot relationship | deterministic hashes equal |
| FIRST_STABLE_TIME | unresolved until all later slots complete |
| SH / SZ first complete | 16:15 / 16:15 |
| Individually delayed codes after first availability | none; all 183 arrived together |
| BaoStock 15:30 / 16:30 | 0 / 183 at both slots |

No stability verdict is inferred from only the 16:15 and 16:30 pair because the remaining 17:00, 17:30, and 18:00 observations can still reveal a revision.

## Call Budgets

- Tushare calendar refresh: at most one `trade_cal` request per explicit refresh.
- Tushare timing slot: exactly one whole-date `fund_daily` request, then local filtering.
- BaoStock comparator slot: at most the dynamically discovered required ETF count, currently 183 per-symbol requests.
- Duplicate slot: zero vendor requests and an append-only `DUPLICATE_ATTEMPT_SKIPPED` manifest.
- Early slot: zero vendor requests and an append-only `BLOCKED_EARLY_PROBE` manifest.

## Scheduling Validation

The LaunchAgent `com.dayin.a-share.tushare-etf-availability` is installed with ten Asia/Shanghai Tushare triggers. BaoStock runs only at the four configured comparator slots through the same wrapper.

The first launchd kickstart exposed that macOS launchd selected `/usr/bin/python3` without pandas. It exited before any vendor request. The wrapper was changed to select only an existing interpreter that imports both pandas and yaml. A second launchd run exited `0` and produced only `DUPLICATE_ATTEMPT_SKIPPED`, proving the installed entry and slot idempotency without making a second Tushare call. The original local traceback remains in the append-only operational log as pre-fix evidence.

## Boundary Validation

| Boundary | Result |
|---|---|
| `data/etf_daily/` aggregate SHA-256 | `21702d2d2760c9c10ac62708c45fcaff35fb53aabfec13c8e474458b319d8855` unchanged |
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

- Availability-audit targeted tests: `16 passed`.
- Full project suite: `69 passed`, `8 subtests passed`.
- Existing pytest collection warnings: 2 (`TestResult` helper classes in the JQData and QMT diagnostic scripts).
- Project context: `VALID_WITH_WARNINGS`.
- Only context warning: existing stale Regime snapshot warning.
- Python compile, shell syntax, plist lint, and Git diff check: pass.
- Installed LaunchAgent: loaded; latest run exit code `0`.

## Current Decision

```text
ETF Daily Availability Timing Audit = ACTIVE_COLLECTING
Timing Evidence = COLLECTING_INSUFFICIENT_DAYS
Tushare = SHADOW_PRIMARY_CANDIDATE
BaoStock = COMPARATOR_ONLY
data/etf_daily = CANONICAL_SSOT
Tushare Primary Upstream Migration = NOT_STARTED
Formal Execution Logic = UNCHANGED
```

The next automatic real Tushare observation is 2026-07-14 17:00 CST, followed by 17:30 and 18:00. Five completed valid trading days are required for a preliminary verdict; ten are required before a supported candidate can be submitted to Main.
