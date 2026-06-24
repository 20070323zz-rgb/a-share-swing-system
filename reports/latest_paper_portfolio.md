# 模拟盘持仓报告 2026-06-24

本报告只读取本地模拟盘记录，不接券商 API，不下单，不读取账号密码。

## 账户摘要
- 初始模拟本金：10000.00 元
- 当前现金：7058.11 元
- 当前持仓市值：3001.60 元
- 当前总资产：10059.71 元
- 当前持仓数：3
- 浮动盈亏：133.30 元
- 浮动盈亏率：4.65%
- 已实现盈亏：-73.58 元
- 总盈亏：59.72 元
- 模拟交易流水数：7
- 风险提醒数量：0

## 当前持仓
| symbol | name | etf_type | type_risk | type_max_days | type_severity | type_review_note | strategy_source | entry_date | entry_price | quantity | cost | current_price | market_value | unrealized_pnl | unrealized_return | holding_days | stop_loss | distance_to_stop | risk_alert |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 512800 | 银行ETF | sector | medium | 30 | elevated | 行业 ETF 按中等敏感度复核，重点看同 group 暴露和 short_swing 是否转弱。 | resonance | 2026-06-09 | 0.792 | 1100 | 871.2 | 0.761 | 837.1 | -34.1 | -0.039141 | 15 | 0.7326 | 3.73% |  |
| 515000 | 科技ETF | unknown | medium | 30 | normal | ETF 类型证据不足，保持人工复核提示。 | resonance | 2026-06-16 | 1.42643 | 1000 | 1426.43 | 1.609 | 1609 | 182.57 | 0.127991 | 8 | 1.42643 | 11.35% |  |
| 512880 | 证券ETF | high_beta | very_high | 20 | normal | high_beta 对情绪和成交额敏感，评分转弱时优先人工复核。 | resonance | 2026-06-23 | 1.14134 | 500 | 570.67 | 1.111 | 555.5 | -15.17 | -0.026583 | 1 | 1.084273 | 2.41% |  |

## 已实现盈亏
- realized_pnl：-73.58 元
- realized_pnl 仅来自 data/paper_trades.csv 的本地模拟 BUY/SELL 流水，不代表真实账户。
| trade_date | symbol | name | action | price | quantity | amount | realized_pnl | execution_price_type | order_type | source | simulated_cash | position_value | total_equity | reason |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-06-09 | 515220 | 煤炭ETF | BUY | 1.36 | 1100 | 1496 | 0 | close_price | paper_buy | buy_signal_ranking | 8504 | 1496 | 10000 | rank_score=93.244634; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-09 | 512800 | 银行ETF | BUY | 0.792 | 1100 | 871.2 | 0 | close_price | paper_buy | buy_signal_ranking | 7632.8 | 2367.2 | 10000 | rank_score=90.914761; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-09 | 515880 | 证券公司ETF | BUY | 1.695 | 300 | 508.5 | 0 | close_price | paper_buy | buy_signal_ranking | 7124.3 | 2875.7 | 10000 | rank_score=90.247897; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-16 | 515220 | 煤炭ETF | SELL | 1.257623 | 1100 | 1383.38 | -117.62 | close_price_with_slippage | paper_sell | paper_trade_engine | 8502.68 | 1388.9 | 9891.58 | stop_loss_break |
| 2026-06-16 | 515000 | 科技ETF | BUY | 1.421426 | 1000 | 1421.43 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7076.25 | 2809.9 | 9886.15 | paper_rule_validation; rank=1; rank_score=91.770799; mid_trend=BUY; short_swing=BUY; amount=1421.43 |
| 2026-06-23 | 515880 | 证券公司ETF | SELL | 1.858442 | 300 | 557.53 | 44.03 | close_price_with_slippage | paper_sell | paper_trade_engine | 7628.78 | 2446.1 | 10074.88 | REDUCE two consecutive days |
| 2026-06-23 | 512880 | 证券ETF | BUY | 1.131339 | 500 | 565.67 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7058.11 | 3011.6 | 10069.71 | paper_rule_validation; rank=1; rank_score=91.306916; mid_trend=BUY; short_swing=BUY; amount=565.67 |

## 记录说明
- 如需新增模拟持仓，手动填写 data/paper_positions.csv。
- data/paper_trades.csv 只用于模拟流水备查，不代表任何真实交易。
- 系统只做本地估值和报告，不会自动写入真实交易或下单。