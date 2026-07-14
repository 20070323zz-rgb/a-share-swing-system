# Tushare ETF Daily Availability Timing Audit

## Purpose

This observer measures when Tushare `fund_daily` becomes available, complete, field-complete, and stable after the A-share close. It also records BaoStock availability at lower frequency as a comparator. The observer is research-only and append-only.

It does not write `data/etf_daily/`, call the daily-close chain, invoke paper execution, promote a vendor to primary upstream, or provide fallback data to any formal workflow.

## Universe And Calendar

- Universe source: every CSV currently present in `data/etf_daily/`.
- Role source: `data/etf_classification.csv`.
- Mapping: local six-digit code to Tushare `ts_code`, exchange, role, and canonical file path.
- Required count: dynamically discovered from the current canonical ETF file inventory; the initial activation mapping resolves to 183.
- Trading-day authority: cached Tushare `trade_cal`; a weekday guess is never accepted.
- Time zone: `Asia/Shanghai`.

The committed mapping report is `reports/tushare_etf_universe_mapping_validation.csv`. The local calendar cache and its immutable retrieval history are under the ignored audit staging directory.

## Observation Schedule

Tushare runs at `15:05`, `15:15`, `15:30`, `15:45`, `16:00`, `16:15`, `16:30`, `17:00`, `17:30`, and `18:00` CST. Each slot permits one `fund_daily(trade_date=...)` call; the returned daily table is filtered to the 183 required codes locally.

BaoStock runs at `15:30`, `16:30`, `17:30`, and `18:00`. It is a comparator only and may make up to 183 rate-limited per-symbol queries because that interface does not expose an equivalent whole-market daily call. It can never write to the canonical database or become an automatic fallback.

If the scheduler's Python environment does not contain BaoStock, the observer delegates only the BaoStock calls to an already existing BaoStock-capable project interpreter. It does not install packages; `A_SHARE_BAOSTOCK_PYTHON` may explicitly identify that interpreter. The helper returns an in-memory sanitized response to the parent observer and does not persist a separate price store.

## Evidence Model

Each attempt writes a unique manifest using `trade_date`, `probe_id`, and `attempt_id`. A completed slot is never overwritten. A repeated invocation writes `DUPLICATE_ATTEMPT_SKIPPED`. A slot missed because the computer was asleep or unavailable writes `MISSED_PROBE`; it is not interpreted as vendor unavailability.

Local normalized snapshots are retained only in the Git-ignored staging directory. Committed outputs contain counts, hashes, timing, missing codes, field-quality statistics, and sanitized errors. They never contain the Tushare token or raw authenticated payload.

The three timing definitions are:

- `FIRST_AVAILABLE_TIME`: first slot containing at least one required ETF.
- `FIRST_COMPLETE_TIME`: first slot with 100% required coverage, no duplicates, and no critical OHLC/volume/amount errors.
- `FIRST_STABLE_TIME`: first complete snapshot that matches a later snapshot at least 15 minutes away and every remaining daily snapshot.

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
- `MISSED_PROBE`: repair local scheduling or wake behavior; do not backfill a historical vendor result.
- `DUPLICATE_ATTEMPT_SKIPPED`: the original completed manifest remains authoritative for that slot.

## Decision Gate

Five valid trading days can produce only `PRELIMINARY` timing evidence. If those days are unstable, collection extends to ten valid days. A supported verdict and a safety-time recommendation require ten valid days and Main review. The eventual safety candidate must be based on at least P90 `FIRST_STABLE_TIME` plus the configured safety buffer, not an average.

This audit cannot start Tushare primary migration, Data Foundation Upgrade, Preview, or Formal Execution.

## Interface References

- Tushare `fund_daily`: <https://tushare.pro/document/2?doc_id=127>
- Tushare `trade_cal`: <https://tushare.pro/document/2?doc_id=26>

The interface documentation defines fields and access shape; this audit measures actual post-close availability independently rather than assuming a publication time from documentation.
