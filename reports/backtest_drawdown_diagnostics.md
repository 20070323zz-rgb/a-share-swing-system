# Backtest Drawdown Diagnostics 2026-06-19 00:53:15

| strategy | drawdown_start | drawdown_end | drawdown_trading_days | max_drawdown | start_equity | end_equity | trade_count_in_drawdown | avg_exposure_in_drawdown | holding_symbols_in_drawdown | worst_symbols_json | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adjusted_preview_baseline | 2022-07-04 | 2024-09-18 | 539 | -0.197083 | 20684.339900 | 16607.801500 | 104 | 0.412158 | 159915,510300 | {"159915": -2052.3631, "510300": -1055.9953} | high trading activity during drawdown; portfolio exposed during adverse market; adjusted preview did not materially reduce common market beta |
| buy_and_hold_510300 | 2022-07-04 | 2024-02-02 | 390 | -0.172616 | 20855.499900 | 17255.499900 | 0 | 0.563312 |  | {} | mark-to-market drawdown without closed trades |
| cash_baseline | 2022-04-08 | 2022-04-08 | 1 | 0.000000 | 20000.000000 | 20000.000000 | 0 | 0.000000 |  | {} | cash has no drawdown |
| original_ranking_baseline | 2022-07-04 | 2024-09-18 | 539 | -0.197083 | 20684.339900 | 16607.801500 | 104 | 0.412158 | 159915,510300 | {"159915": -2052.3631, "510300": -1055.9953} | high trading activity during drawdown; portfolio exposed during adverse market |

## 诊断
- adjusted preview 没降低最大回撤，说明它未显著降低共同市场 beta 或回撤期暴露。
- 后续可测试 market_state review、降低仓位、ETF type-aware 风险约束，但不能直接上线。
