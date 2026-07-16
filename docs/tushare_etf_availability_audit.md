# Tushare ETF Daily Availability Timing Audit

## Purpose

This observer measures when Tushare `fund_daily` becomes available, complete, field-complete, and stable after the A-share close. Tushare is now the user-authorized primary upstream at the architecture level; the observer remains append-only and is used to optimize the formal publication window and safety buffer.

It does not write `data/etf_daily/`, call the daily-close chain, invoke paper execution, perform formal promotion, or provide fallback data to any formal workflow. Architecture approval is not evidence that migration or promotion has been implemented.

## Universe And Calendar

- Universe source: every CSV currently present in `data/etf_daily/`.
- Role source: `data/etf_classification.csv`.
- Mapping: local six-digit code to Tushare `ts_code`, exchange, role, and canonical file path.
- Required count: dynamically discovered from the current canonical ETF file inventory; the initial activation mapping resolves to 183.
- Trading-day authority: cached Tushare `trade_cal`; a weekday guess is never accepted.
- Time zone: `Asia/Shanghai`.

The committed mapping report is `reports/tushare_etf_universe_mapping_validation.csv`. The local calendar cache and its immutable retrieval history are under the ignored audit staging directory.

## Observation Schedule

From 2026-07-16, the daily core Tushare slots are `16:00`, `16:05`, `16:10`, `16:15`, `16:30`, and `17:00` CST. `17:30` and `18:00` are conditional late slots. Each executed slot permits one `fund_daily(trade_date=...)` call; the returned daily table is filtered to the 183 required codes locally.

The `15:30` slot is removed from the daily Availability timing window. It remains available only as an explicit, low-frequency interface health check and never contributes to `FIRST_AVAILABLE`, `FIRST_COMPLETE`, or `FIRST_STABLE`. Historical 15:05/15:15/15:30/15:45 observations through 2026-07-15 remain immutable and continue to support the original two-day evidence.

BaoStock remains `RECONCILIATION_ONLY`. Its configured observations are isolated reconciliation evidence, may make up to 183 rate-limited per-symbol queries, and can never write to the canonical database or become an automatic fallback.

### Adaptive stopping

- Core slots always execute when the trading calendar and local runtime permit.
- A conditional 17:30 or 18:00 slot executes when the latest effective observation is `NOT_AVAILABLE`, `PARTIAL`, `COMPLETE_UNCONFIRMED`, `REVISION_DETECTED`, missed, or failed.
- A conditional slot is recorded as `SKIPPED_STABLE_CONFIRMED` with zero vendor calls when the latest two effective complete snapshots are hash-identical and no later failure or revision invalidates that state.
- A revision after an earlier stable pair invalidates the earlier `FIRST_STABLE`; a later unchanged pair may establish a new confirmation time.

If the scheduler's Python environment does not contain BaoStock, the observer delegates only the BaoStock calls to an already existing BaoStock-capable project interpreter. It does not install packages; `A_SHARE_BAOSTOCK_PYTHON` may explicitly identify that interpreter. The helper returns an in-memory sanitized response to the parent observer and does not persist a separate price store.

## Evidence Model

Each attempt writes a unique manifest using `trade_date`, `probe_id`, and `attempt_id`. A completed slot is never overwritten. A repeated invocation writes `DUPLICATE_ATTEMPT_SKIPPED`. A slot missed because the computer was asleep or unavailable writes `MISSED_PROBE`; it is not interpreted as vendor unavailability.

Local normalized snapshots are retained only in the Git-ignored staging directory. Committed outputs contain counts, hashes, timing, missing codes, field-quality statistics, and sanitized errors. They never contain the Tushare token or raw authenticated payload.

The three timing definitions are:

- `FIRST_AVAILABLE_TIME`: first timing-eligible slot containing at least one required ETF; health checks are excluded.
- `FIRST_COMPLETE_TIME`: first slot with 100% required coverage, no duplicates, and no critical OHLC/volume/amount errors.
- `FIRST_STABLE_TIME`: the confirming time of two consecutive effective 183/183, field-quality-passing snapshots with the same deterministic manifest content hash. It is not the first-complete time.

Examples: 16:05 complete plus an identical 16:10 snapshot yields `FIRST_STABLE=16:10`; 16:10 complete plus an identical 16:15 snapshot yields `FIRST_STABLE=16:15`; 16:15 complete plus an identical 16:30 snapshot yields `FIRST_STABLE=16:30`.

Per-slot observation states are `NOT_AVAILABLE`, `PARTIAL`, `COMPLETE_UNCONFIRMED`, `STABLE`, and `REVISION_DETECTED`.

`FIRST_QUALITY_COMPLETE_TIME` additionally requires all requested contract fields to be non-null. Row-order changes are removed by deterministic sorting before snapshot hashing.

## Commands

Refresh the calendar without probing ETF data:

```bash
python3 scripts/run_tushare_etf_availability_probe.py --refresh-calendar-only --trade-date YYYY-MM-DD
```

Run one manual Tushare slot:

```bash
python3 scripts/run_tushare_etf_availability_probe.py --source tushare --trade-date YYYY-MM-DD --scheduled-time HH:MM
```

Run one manual BaoStock comparator slot:

```bash
python3 scripts/run_tushare_etf_availability_probe.py --source baostock --trade-date YYYY-MM-DD --scheduled-time HH:MM
```

Rebuild committed summaries from local manifests:

```bash
python3 scripts/build_tushare_etf_availability_report.py
```

## Local Scheduling

Install only after mock tests and a manual real probe pass:

```bash
bash scripts/install_tushare_etf_availability_launchd.sh
```

Inspect status and logs:

```bash
launchctl print "gui/$(id -u)/com.dayin.a-share.tushare-etf-availability"
tail -n 80 logs/tushare_etf_availability.out.log
tail -n 80 logs/tushare_etf_availability.err.log
```

Uninstall:

```bash
bash scripts/uninstall_tushare_etf_availability_launchd.sh
```

The committed plist is a path-neutral template. Installation renders the current checkout path into the local user LaunchAgent. The job calls only `scripts/run_tushare_etf_availability_probe.sh`.
Because `StartCalendarInterval` follows the host clock, installation fails unless `/etc/localtime` resolves to `Asia/Shanghai`; the job environment also sets `TZ=Asia/Shanghai`.
The shell wrapper selects an existing interpreter only after verifying that `pandas` and `yaml` import successfully. `A_SHARE_AUDIT_PYTHON` can provide an explicit interpreter; if no candidate passes, the task exits before any vendor request.

## Failure Handling

- `BLOCKED_CALENDAR_UNCONFIRMED`: refresh the calendar; no vendor timing inference is made.
- `BLOCKED_TOKEN_MISSING` or `PERMISSION_BLOCKED`: restore local credentials or permissions; do not expose the token in logs.
- `NETWORK_FAILED`: retain the sanitized manifest; do not substitute an earlier date or a different vendor.
- `EMPTY_UNEXPECTED`: retain the slot as observed empty data, distinct from `MISSED_PROBE`.
- `SKIPPED_STABLE_CONFIRMED`: retain the conditional-slot stop decision; no vendor call was made.
- `MISSED_PROBE`: repair local scheduling or wake behavior; do not backfill a historical vendor result.
- `DUPLICATE_ATTEMPT_SKIPPED`: the original completed manifest remains authoritative for that slot.

## Decision Gate

The statistical verdict remains `INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION` until at least five valid trading days exist. If those days are unstable, collection extends to ten valid days. Five- and ten-day gates govern only the formal timing window and safety buffer; they do not reopen the user-authorized Tushare source-selection decision.

The initial migration implementation candidate is 16:15 for the first formal staging fetch, 16:30 for confirmation/validation and a future atomic-promotion candidate, and 18:00 for fail-closed manual review. These are design candidates only. Formal promotion remains `BLOCKED_PENDING_IMPLEMENTATION_VALIDATION`; no code in this observer promotes data.

This audit cannot start formal promotion, Data Foundation Upgrade, Preview, or Formal Execution. Migration design and implementation are authorized but remain a separate future batch.

## Interface References

- Tushare `fund_daily`: <https://tushare.pro/document/2?doc_id=127>
- Tushare `trade_cal`: <https://tushare.pro/document/2?doc_id=26>

The interface documentation defines fields and access shape; this audit measures actual post-close availability independently rather than assuming a publication time from documentation.
