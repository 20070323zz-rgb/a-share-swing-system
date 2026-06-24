# App Data Update Task Fix Report

Generated at: 2026-06-18 15:27 CST

## Issue

The dynamic App "一键补齐数据" task was shown as failed when BaoStock had not yet published the requested trading day's ETF daily bars.

This was a task-status logic issue, not a broker/trading issue.

## Root Cause

1. BaoStock returned empty rows for 2026-06-18 on probe symbols.
2. The daily update script correctly marked this as `CAUTION / pending_source_update`.
3. The source router propagated the raw internal exit code `2`, so the App task runner marked the safe task as `failed`.
4. The old `backfill_recent_data` task also continued into broader report refresh commands, including `paper_portfolio.py`, which could rewrite `data/paper_positions.csv`. That was too broad for a button named "补齐数据".

## Fix

1. `src/data_sources/source_router.py`
   - Normalizes BaoStock `pending_source_update` and `stale_no_new_rows` to task exit code `0` when `--strict-exit` is not requested.
   - Preserves the raw source exit code as `raw_source_exit_code`.
   - Keeps `severity=CAUTION` and `status=pending_source_update` in machine-readable reports.

2. `app/backend/safe_tasks.py`
   - Adds `--source-ready-probe` to App data update tasks.
   - This checks a small anchor set first and avoids a full 183-ETF empty run when BaoStock has not published today's data.
   - Narrows `backfill_recent_data` to data update, data coverage, data health, and dashboard sync only.

3. `app/frontend/src/components/TaskPanel.jsx`
   - Updates the button note to clarify that "一键补齐数据" only updates行情和数据报告.

## Current 2026-06-18 Result

- BaoStock status: `PENDING_SOURCE_UPDATE`
- Latest local ETF date: `2026-06-17`
- Requested date: `2026-06-18`
- Added rows: `0`
- BaoStock probe calls: `5`
- Full ETF empty run: skipped
- App task status: `success`
- Dashboard status: `DATA_UPDATE_CAUTION`

## Safety Check

- No broker API.
- No real order.
- No real account access.
- No password/token printed or saved.
- No fake 2026-06-18 rows were written.
- `paper_trades.csv` unchanged during the final verification run.
- `paper_positions.csv` unchanged during the final verification run after narrowing the task.

