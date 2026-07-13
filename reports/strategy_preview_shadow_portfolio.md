# Strategy Preview Shadow Portfolio 2026-07-10 16:28:08

本影子组合只记录 adjusted Top 3 的理论观察收益，不写 paper_trades，不写 paper_positions，不影响真实模拟盘。

- rows：48
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
| 2026-07-06 | 1 | 512010 | 医药ETF | 33.33% | 4000.0 | partial | -3.54% | -3.00% | N/A | N/A |
| 2026-07-06 | 2 | 512880 | 证券ETF | 33.33% | 4000.0 | partial | -3.19% | -2.41% | N/A | N/A |
| 2026-07-06 | 3 | 159929 | 医药ETF | 33.33% | 4000.0 | partial | -3.76% | -3.45% | N/A | N/A |
| 2026-07-07 | 1 | 512010 | 医药ETF | 33.33% | 4000.0 | partial | -1.41% | N/A | N/A | N/A |
| 2026-07-07 | 2 | 159865 | 养殖ETF | 33.33% | 4000.0 | partial | -2.83% | N/A | N/A | N/A |
| 2026-07-07 | 3 | 159869 | 游戏ETF | 33.33% | 4000.0 | partial | -1.69% | N/A | N/A | N/A |
| 2026-07-08 | 1 | 588000 | 科创50ETF | 33.33% | 4000.0 | partial | 8.53% | N/A | N/A | N/A |
| 2026-07-08 | 2 | 588080 | 科创创业50ETF | 33.33% | 4000.0 | partial | 8.71% | N/A | N/A | N/A |
| 2026-07-08 | 3 | 159865 | 养殖ETF | 33.33% | 4000.0 | partial | -0.39% | N/A | N/A | N/A |
| 2026-07-09 | 1 | 516510 | 云计算ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-07-09 | 2 | 159929 | 医药ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |
| 2026-07-09 | 3 | 515000 | 科技ETF | 33.33% | 4000.0 | pending | N/A | N/A | N/A | N/A |

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
