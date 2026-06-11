# 卖出复核报告 2026-06-10 21:29:54

本报告只做模拟盘持仓复核，不自动卖出、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。

## 摘要
- 当前持仓数：3
- 状态分布：{'REVIEW': 2, 'HOLD': 1}
- 买入后 1-2 个交易日为保护期：除止损/趋势破坏/严重数据异常外，不因单日评分下降直接 SELL。
- 研究性止损只用于复核提示，不是正式交易规则。

## 当前持仓复核
| ETF | 名称 | 类型 | 持仓天数 | 保护期 | rank_score | rank变化 | 连续下降天数 | mid | short | 止损价 | 距离止损 | data_health | 状态 | 动作说明 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 515220 | 煤炭ETF | commodity_resource | 1 | yes | 78.0385 | -15.2061 | 1 | BUY | WATCH | 1.258 | 3.60% | 正常  | REVIEW | 买入后 1-2 日保护期：不因单日评分下降直接卖出；人工复核，禁止加仓。 |
| 512800 | 银行ETF | sector | 1 | yes | 94.2614 | 3.3466 | 0 | BUY | BUY | 0.7326 | 9.11% | 正常  | HOLD | 保护期内未触发硬风控，继续持有。 |
| 515880 | 证券公司ETF | high_beta | 1 | yes | 74.9006 | -15.3473 | 1 | BUY | WATCH | 1.5679 | 3.81% | 提醒 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 | REVIEW | 买入后 1-2 日保护期：不因单日评分下降直接卖出；人工复核，禁止加仓。 |

## 触发条件明细
| ETF | condition_flags | safety_note |
| --- | --- | --- |
| 515220 | rank_score_single_day_drop; rank_score_large_drop; rank_score_drop_pct_over_12; short_swing_buy_to_watch; floating_loss_over_3_5pct | review_only_no_trade |
| 512800 |  | review_only_no_trade |
| 515880 | rank_score_single_day_drop; rank_score_large_drop; rank_score_drop_pct_over_12; short_swing_buy_to_watch; data_health_caution; floating_loss_over_3_5pct; high_beta_large_rank_decay; 515880_caution_min_review | review_only_no_trade |

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不自动卖出或减仓。
- 不新增模拟交易。
- 不修改当前模拟持仓。