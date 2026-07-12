# Paper Execution Preflight

- run_id: `66d205f5-c52c-402d-9484-2ece666c05ea`
- execution_timestamp: `2026-07-11T16:21:07+08:00`
- expected_trade_date: `2026-07-10`
- gate_status: `BLOCKED_STALE_SIGNAL`
- engine_invoked: `false`
- engine_mode: `dry_run`

## Freshness Snapshot

- latest_data_date: `2026-07-10`
- signal_date: `2026-07-09`
- ranking_date: `2026-07-09`
- failed_count: `0`
- pending_count: `0`
- coverage: `63/63`
- calendar: `confirmed_by_local_510300_calendar` via `data/etf_daily/sh_510300.csv`

## Checks

- trading_day: `PASS`
- latest_data_date_matches: `PASS`
- failed_count_zero: `PASS`
- pending_count_zero: `PASS`
- required_universe_coverage_complete: `PASS`
- signal_date_matches: `FAIL`
- ranking_date_matches: `FAIL`
- proposed_trade_bars_complete: `PASS`
- critical_inputs_valid: `PASS`

## Blocking Reasons

- signal sources do not match 2026-07-10: signals_csv=2026-07-09, sell_review_csv=2026-07-09
- ranking_date=2026-07-09, expected=2026-07-10

## Missing Coverage

- formal universe: `none`
- proposed trades: `none`

## Safety Boundary

- A non-PASS result never invokes the paper trade engine.
- Prior-day market data is never used as an automatic fallback.
- This preflight does not modify paper trades, positions, strategy, ranking, or score.
