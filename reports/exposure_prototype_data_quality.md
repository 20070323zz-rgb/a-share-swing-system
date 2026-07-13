# Exposure Prototype Data Quality

## Summary

- Universe Version: universe_v2_qualified_research
- Calculation Date: 2026-07-08
- ETF Count: 16
- Missing Rows: 0
- Single ETF Data Source: True
- ETF Daily Copied: False

## Missing Data By Exposure

| exposure_name | missing_rows | reasons |
| --- | --- | --- |
| NONE | 0 |  |

## Coverage By ETF

| symbol | name | price_rows | data_start | data_end | current_for_calculation_date |
| --- | --- | --- | --- | --- | --- |
| 159516 | 半导体设备ETF国泰 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159531 | 中证2000ETF南方 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159547 | 红利低波ETF华夏 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159593 | 中证A50ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 159608 | 稀有金属ETF广发 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159638 | 高端装备ETF嘉实 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159667 | 工业母机ETF国泰 | 329 | 2025-03-03 | 2026-07-08 | True |
| 159732 | 消费电子ETF华夏 | 329 | 2025-03-03 | 2026-07-08 | True |
| 510050 | 上证50ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 515260 | 电子ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 515630 | 保险证券 | 329 | 2025-03-03 | 2026-07-08 | True |
| 561360 | 石油ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 561560 | 电力ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 562550 | 绿电ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 588200 | 科创芯片ETF | 329 | 2025-03-03 | 2026-07-08 | True |
| 588220 | 科创100ETF基金 | 329 | 2025-03-03 | 2026-07-08 | True |

## Metric Quality Notes

- `market_beta` uses `510300` as a default A-share broad-market proxy and is marked `PIT_SAFE_WITH_PROXY`.
- `realized_volatility`, `downside_drawdown_risk`, `trading_liquidity`, and `return_momentum` are calculated from each ETF's own historical daily data ending at calculation date.
- Missing data is explicit; no forward fill is used for unavailable rolling windows.
- This prototype does not use future returns, future classifications, holdings, constituents, strategy outputs, preview outputs, or execution data.
