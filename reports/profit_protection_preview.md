# 持仓浮盈保护 Preview 2026-07-04 00:03:53

本报告只做模拟仓浮盈保护观察，不自动止盈、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。

## 摘要
- 当前持仓数：3
- 有浮盈持仓数：2
- PROFIT_WATCH：0
- PROFIT_PROTECTION_REVIEW：1
- PROFIT_LOCK_CANDIDATE：1
- 当前总未实现盈亏：76.90
- 持仓以来总峰值浮盈：327.10
- 从浮盈峰值回撤合计：250.20
- 估值日期：2026-07-03
- execution_allowed：false

## 状态定义
- NO_PROFIT = 暂无浮盈保护需求
- PROFIT_WATCH = 浮盈观察
- PROFIT_PROTECTION_REVIEW = 浮盈保护复核
- PROFIT_LOCK_CANDIDATE = 浮盈锁定候选（不是卖出信号）

## 持仓明细
| symbol | name | state | entry_date | latest_date | current_pnl | current_pnl_pct | peak_pnl | peak_pnl_pct | peak_date | drawdown_from_peak | drawdown_pct | action |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 512800 | 银行ETF | NO_PROFIT / 暂无浮盈保护需求 | 2026-06-09 | 2026-07-03 | -49.50 | -5.68% | 24.20 | 2.78% | 2026-06-12 | 73.70 | 304.55% | 当前无浮盈，不需要浮盈保护；继续按 REVIEW/止损规则观察。 |
| 515000 | 科技ETF | PROFIT_LOCK_CANDIDATE / 浮盈锁定候选 | 2026-06-16 | 2026-07-03 | 119.57 | 8.38% | 285.57 | 20.02% | 2026-06-30 | 166.00 | 58.13% | 浮盈锁定候选观察；条件叠加但不自动交易。 |
| 512880 | 证券ETF | PROFIT_PROTECTION_REVIEW / 浮盈保护复核 | 2026-06-23 | 2026-07-03 | 6.83 | 1.20% | 17.33 | 3.04% | 2026-07-01 | 10.50 | 60.59% | 浮盈保护复核；观察是否继续回吐，不自动止盈。 |

## 515000 科技ETF 重点观察
- profit_protection_state：PROFIT_LOCK_CANDIDATE / 浮盈锁定候选
- 当前浮盈率：8.38%
- 最高浮盈日期：2026-06-30
- 从最高浮盈回撤：166.00，回撤比例 58.13%
- 复核说明：当前浮盈 119.57，浮盈率 8.38%。；持仓以来最高浮盈 285.57，从峰值回撤 58.13%。；当前浮盈率超过 5% 复核阈值。；浮盈从峰值回撤超过 30%。；浮盈从峰值回撤超过 50%。；short_swing 已转 WATCH。；当前 REVIEW 分层：REVIEW_2。

## 解释
- 当前有浮盈的持仓会进入 PROFIT_WATCH 或更高层级。
- PROFIT_PROTECTION_REVIEW 表示需要关注浮盈是否继续回吐。
- PROFIT_LOCK_CANDIDATE 不是卖出信号，只是提示需要人工复核是否保护浮盈。
- 本模块与 REVIEW / REDUCE_CANDIDATE 的区别：它只观察盈利回吐，不改变原有持仓复核状态。
- 后续至少需要多轮模拟交易样本和不同市场状态验证，才可考虑规则化。

## 安全边界
- 当前是否建议自动止盈：否。
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不修改 paper_trade_engine.py。
- 不修改 paper_trades.csv / paper_positions.csv。