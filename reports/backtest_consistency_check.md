# Backtest Consistency Check 2026-06-19 00:51:42

- 状态：CAUTION

## 策略口径
| strategy | start_date | end_date | trading_days | first_trade_date | reported_total_return | return_from_initial_cash | return_delta | cost_total | commission_plus_slippage | cost_delta | trade_count_reported | buy_sell_rows | round_trip_sells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adjusted_preview_baseline | 2022-04-07 | 2026-06-18 | 1018 | 2022-04-08 | 0.107791 | 0.105999 | 0.001792 | 1454.925000 | 1454.925000 | 0.000000 | 236 | 236 | 118 |
| buy_and_hold_510300 | 2022-04-08 | 2026-06-18 | 1017 | 2022-04-08 | 0.164320 | 0.163825 | 0.000495 | 8.500100 | 8.500100 | 0.000000 | 1 | 1 | 0 |
| cash_baseline | 2022-04-08 | 2026-06-18 | 1017 |  | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| original_ranking_baseline | 2022-04-07 | 2026-06-18 | 1018 | 2022-04-08 | 0.061492 | 0.059774 | 0.001718 | 1454.911500 | 1454.911500 | 0.000000 | 236 | 236 | 118 |

## 发现的问题
- adjusted_preview_baseline: total_return uses first equity rather than initial cash; delta=0.1792%
- adjusted_preview_baseline: equity curve starts before first trade (2022-04-07 vs 2022-04-08)
- original_ranking_baseline: total_return uses first equity rather than initial cash; delta=0.1718%
- original_ranking_baseline: equity curve starts before first trade (2022-04-07 vs 2022-04-08)
- strategies do not share identical equity date ranges/trading day counts

## 说明
- 交易数定义：single-side BUY/SELL rows; round trips are SELL rows
- 最大回撤计算：daily equity curve
- 成交假设：next_close
- 本报告不覆盖旧回测结果；如要修复口径，应生成 v2 文件。
