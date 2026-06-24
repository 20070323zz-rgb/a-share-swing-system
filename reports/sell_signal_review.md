# 卖出复核报告 2026-06-24 23:04:51

本报告只做模拟盘持仓复核，不自动卖出、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。

## 摘要
- 当前持仓数：3
- 状态分布：{'REVIEW': 2, 'HOLD': 1}
- 买入后 1-2 个交易日为保护期：除止损/趋势破坏/严重数据异常外，不因单日评分下降直接 SELL。
- 研究性止损只用于复核提示，不是正式交易规则。

## 当前持仓复核
| ETF | 名称 | 类型 | type_risk | type_max_days | type_stop_loss | 持仓进度 | 距离止损状态 | type_severity | rank_score | rank变化 | mid | short | data_health | 状态 | 类型化说明 | 动作说明 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | medium | 30 | 6.00% | 46.67% | comfortable | elevated | N/A | N/A | BUY | WATCH | 正常  | REVIEW | 行业 ETF 按中等敏感度复核，重点看同 group 暴露和 short_swing 是否转弱。 | 触发人工复核条件；不自动卖出，dashboard 标黄。 |
| 515000 | 科技ETF | unknown | medium | 30 | 0.00% | 23.33% | comfortable | normal | 80.3898 | -11.381 | BUY | WATCH | 正常  | REVIEW | ETF 类型证据不足，保持人工复核提示。 | 触发人工复核条件；不自动卖出，dashboard 标黄。 |
| 512880 | 证券ETF | high_beta | very_high | 20 | 5.00% | 0.00% | watch_within_5pct | normal | 91.8274 | 0.5205 | BUY | BUY | 正常  | HOLD | high_beta 对情绪和成交额敏感，评分转弱时优先人工复核。 | 保护期内未触发硬风控，继续持有。 |

## 触发条件明细
| ETF | type_review_severity | condition_flags | safety_note |
| --- | --- | --- | --- |
| 512800 | elevated | short_swing_buy_to_watch; rank_decline_2d | review_only_no_trade |
| 515000 | normal | rank_score_single_day_drop; rank_score_drop_pct_over_12; short_swing_buy_to_watch; rank_decline_2d | review_only_no_trade |
| 512880 | normal |  | review_only_no_trade |

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不自动卖出或减仓。
- 不新增模拟交易。
- 不修改当前模拟持仓。