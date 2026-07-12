# 卖出复核报告 2026-07-10 16:28:05

本报告只做模拟盘持仓复核，不自动卖出、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。

## 摘要
- 当前持仓数：2
- 状态分布：{'REVIEW': 2}
- 买入后 1-2 个交易日为保护期：除止损/趋势破坏/严重数据异常外，不因单日评分下降直接 SELL。
- 研究性止损只用于复核提示，不是正式交易规则。

## 当前持仓复核
| ETF | 名称 | 类型 | type_risk | type_max_days | type_stop_loss | 持仓进度 | 距离止损状态 | type_severity | rank_score | rank变化 | mid | short | data_health | 状态 | 类型化说明 | 动作说明 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | medium | 30 | 6.00% | 100.00% | watch_within_5pct | elevated | N/A | N/A | BUY | WATCH | 正常  | REVIEW | 行业 ETF 按中等敏感度复核，重点看同 group 暴露和 short_swing 是否转弱。 持仓天数已超过类型化最大持有期的 80%，进入持有期复核区。 | 触发人工复核条件；不自动卖出，dashboard 标黄。 |
| 515000 | 科技ETF | unknown | medium | 30 | 0.00% | 76.67% | comfortable | normal | 77.0373 | -14.7335 | BUY | WATCH | 正常  | REVIEW | ETF 类型证据不足，保持人工复核提示。 | 触发人工复核条件；不自动卖出，dashboard 标黄。 |

## 触发条件明细
| ETF | type_review_severity | condition_flags | safety_note |
| --- | --- | --- | --- |
| 512800 | elevated | short_swing_buy_to_watch; floating_loss_over_3_5pct; rank_decline_2d | review_only_no_trade |
| 515000 | normal | rank_score_single_day_drop; rank_score_large_drop; rank_score_drop_pct_over_12; short_swing_buy_to_watch | review_only_no_trade |

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不自动卖出或减仓。
- 不新增模拟交易。
- 不修改当前模拟持仓。