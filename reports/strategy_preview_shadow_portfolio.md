# Strategy Preview Shadow Portfolio 2026-07-04 00:00:55

本影子组合只记录 adjusted Top 3 的理论观察收益，不写 paper_trades，不写 paper_positions，不影响真实模拟盘。

- rows：36
- initial_cash_assumption：20000.00
- max_holdings：3
- single_position_target：20%
- total_target_position：60%
- min_trade_value：3000.00
- shadow_model_enabled：true
- shadow_model_execution_enabled：false
- paper_trade_engine_enabled：false
- real_trade_enabled：false
- research_only：true
- 20000 是 shadow/research 观察基准，不代表用户需要真实投入。

## 最近影子组合
| snapshot_date | rank | symbol | name | weight | target_value | status | fwd1 | fwd3 | fwd5 | fwd10 |
| --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-06-26 | 1 | 588000 | 科创50ETF | 33.33% | 4000.0 | partial | 5.39% | 7.36% | -1.45% | N/A |
| 2026-06-26 | 2 | 512880 | 证券ETF | 33.33% | 4000.0 | partial | 1.45% | 6.23% | 4.34% | N/A |
| 2026-06-26 | 3 | 159915 | 创业板ETF | 33.33% | 4000.0 | partial | 0.50% | 1.40% | -4.22% | N/A |
| 2026-06-30 | 1 | 159901 | 深100ETF | 33.33% | 4000.0 | partial | -1.40% | -4.48% | N/A | N/A |
| 2026-06-30 | 2 | 515070 | AIETF | 33.33% | 4000.0 | partial | -2.24% | -8.14% | N/A | N/A |
| 2026-06-30 | 3 | 159819 | 人工智能ETF | 33.33% | 4000.0 | partial | -2.51% | -8.60% | N/A | N/A |
| 2026-07-01 | 1 | 512010 | 医药ETF | 33.33% | 4000.0 | partial | -0.56% | N/A | N/A | N/A |
| 2026-07-01 | 2 | 515000 | 科技ETF | 33.33% | 4000.0 | partial | -7.78% | N/A | N/A | N/A |
| 2026-07-01 | 3 | 512880 | 证券ETF | 33.33% | 4000.0 | partial | -2.21% | N/A | N/A | N/A |
| 2026-07-03 | 1 | 512010 | 医药ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-07-03 | 2 | 512880 | 证券ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-07-03 | 3 | 588000 | 科创50ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
