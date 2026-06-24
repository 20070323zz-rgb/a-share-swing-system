# Strategy Preview Shadow Portfolio 2026-06-24 23:04:54

本影子组合只记录 adjusted Top 3 的理论观察收益，不写 paper_trades，不写 paper_positions，不影响真实模拟盘。

- rows：21
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
| 2026-06-18 | 1 | 512400 | 有色ETF | 33.33% | 4000.0 | partial | 5.12% | -3.41% | N/A | N/A |
| 2026-06-18 | 2 | 510050 | 上证50ETF | 33.33% | 4000.0 | partial | 2.65% | 0.23% | N/A | N/A |
| 2026-06-18 | 3 | 159876 | 有色金属ETF | 33.33% | 4000.0 | partial | 5.52% | -2.38% | N/A | N/A |
| 2026-06-22 | 1 | 512880 | 证券ETF | 33.33% | 4000.0 | partial | 0.00% | N/A | N/A | N/A |
| 2026-06-22 | 2 | 512400 | 有色ETF | 33.33% | 4000.0 | partial | -8.31% | N/A | N/A | N/A |
| 2026-06-22 | 3 | 512070 | 非银ETF | 33.33% | 4000.0 | partial | -1.23% | N/A | N/A | N/A |
| 2026-06-23 | 1 | 515000 | 科技ETF | 33.33% | 4000.0 | partial | 3.67% | N/A | N/A | N/A |
| 2026-06-23 | 2 | 512880 | 证券ETF | 33.33% | 4000.0 | partial | -1.77% | N/A | N/A | N/A |
| 2026-06-23 | 3 | 512070 | 非银ETF | 33.33% | 4000.0 | partial | -2.12% | N/A | N/A | N/A |
| 2026-06-24 | 1 | 512880 | 证券ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-06-24 | 2 | 159819 | 人工智能ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-06-24 | 3 | 515070 | AIETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
