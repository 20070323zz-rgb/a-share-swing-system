# 持仓 REVIEW 分层报告 2026-07-04 00:03:53

本报告只做模拟仓观察分层，不自动交易，不写入 paper_trades.csv，不修改 paper_positions.csv。

## 摘要
- 持仓数量：3
- 状态分布：{'REDUCE_CANDIDATE': 1, 'REVIEW_2': 1, 'HOLD': 1}
- REDUCE_CANDIDATE 数量：1
- REVIEW_2 数量：1
- high_beta 观察数量：1
- 浮盈保护观察数量：1
- 估值日期：2026-07-03
- execution_allowed：false
- 安全说明：以下为模拟仓观察状态，不会自动交易。

## 状态定义
- HOLD = 继续持有
- REVIEW_1 = 轻度观察
- REVIEW_2 = 重点复核
- REDUCE_CANDIDATE = 减仓候选（观察状态，不是交易指令）
- REDUCE = 减仓信号（本轮不接执行层）
- SELL = 卖出信号（本轮不接执行层）

## 持仓复核明细
| symbol | name | current_action | review_state | mid | short | PnL | rank | rank_change | rank_decay_days | group | type | high_beta | execution_allowed | reasons | action |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | REVIEW | REDUCE_CANDIDATE / 减仓候选 | BUY | WATCH | -5.68% | 90.9148 | N/A | 2 | 金融地产 | sector | False | false | short_swing 从 BUY 转 WATCH，短周期动能转弱。；浮亏超过 3.5% 观察阈值。；rank_score 连续 2 日下降。；浮亏超过 5% 重点复核阈值。；类型化复核 severity=elevated。；触发人工复核条件；不自动卖出，dashboard 标黄。；估值价格状态正常。 | 减仓候选观察：条件叠加，但不触发自动交易。 |
| 515000 | 科技ETF | REVIEW | REVIEW_2 / 重点复核 | BUY | WATCH | 8.38% | 70.4155 | -21.3553 | 1 | 科技成长 | unknown | False | false | short_swing 从 BUY 转 WATCH，短周期动能转弱。；rank_score 单日下降。；触发人工复核条件；不自动卖出，dashboard 标黄。；估值价格状态正常。 | 重点复核：禁止加仓，次日继续观察。 |
| 512880 | 证券ETF | HOLD | HOLD / 继续持有 | BUY | BUY | 1.20% | 94.493 | 3.186 | 0 | 金融地产 | high_beta | True | false | mid_trend / short_swing 和风控未触发退出条件，继续持有。；估值价格状态正常。；高 beta/情绪型 ETF，继续持有但保持风险观察。 | 继续持有；未触发分层复核条件。 |

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不修改 paper_trade_engine.py。
- 不修改正式买入/卖出规则。
- 不修改 paper_trades.csv / paper_positions.csv。
- REDUCE_CANDIDATE 只是观察状态。