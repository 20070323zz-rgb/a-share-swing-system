# REVIEW 状态审计报告 2026-07-04 00:03:53

## 当前 REVIEW 逻辑来源
- src/sell_signal_review.py produces HOLD/WATCH/REVIEW/REDUCE/SELL review-only status; src/position_review_state.py adds layered REVIEW_1/REVIEW_2/REDUCE_CANDIDATE observation state.
- 当前 HOLD / REVIEW / REDUCE / SELL 来自 sell_signal_review.csv。
- 本轮新增 position_review_state 只做展示和复核分层，不接执行层。

## 当前 512800 进入 REVIEW 的具体原因
- review_state：REDUCE_CANDIDATE / 减仓候选
- short_swing：WATCH
- mid_trend：BUY
- rank_decay_days：2
- unrealized_pnl_pct：-5.68%
- reasons：short_swing 从 BUY 转 WATCH，短周期动能转弱。；浮亏超过 3.5% 观察阈值。；rank_score 连续 2 日下降。；浮亏超过 5% 重点复核阈值。；类型化复核 severity=elevated。；触发人工复核条件；不自动卖出，dashboard 标黄。；估值价格状态正常。

## 是否会自动卖出
- 否。
- REVIEW_1 / REVIEW_2 / REDUCE_CANDIDATE 都是观察状态，不触发 paper_trade_engine。

## 当前 REVIEW 的不足
- 旧 REVIEW 只有单一标黄状态，无法区分轻度观察、重点复核和减仓候选观察。

## 推荐分层方案
- HOLD = 继续持有
- REVIEW_1 = 轻度观察
- REVIEW_2 = 重点复核
- REDUCE_CANDIDATE = 减仓候选
- REDUCE = 减仓信号
- SELL = 卖出信号

## 安全边界
- 未修改 paper_trade_engine.py。
- 未修改 paper_trades.csv。
- 未修改 paper_positions.csv。
- 未接券商 API，未真实下单。