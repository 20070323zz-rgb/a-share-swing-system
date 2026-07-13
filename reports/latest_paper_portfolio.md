# 模拟盘持仓报告 2026-07-09

本报告只读取本地模拟盘记录，不接券商 API，不下单，不读取账号密码。

## 账户摘要
- 初始模拟本金：10000.00 元
- 当前现金：7040.47 元
- 当前持仓市值：3011.40 元
- 当前总资产：10051.87 元
- 当前持仓数：3
- 浮动盈亏：185.15 元
- 浮动盈亏率：6.55%
- 已实现盈亏：-133.27 元
- 总盈亏：51.88 元
- 模拟交易流水数：11
- 风险提醒数量：0

## 当前持仓
| symbol | name | etf_type | type_risk | type_max_days | type_severity | type_review_note | strategy_source | entry_date | entry_price | quantity | cost | current_price | market_value | unrealized_pnl | unrealized_return | holding_days | stop_loss | distance_to_stop | risk_alert |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 515000 | 科技ETF | unknown | medium | 30 | normal | ETF 类型证据不足，保持人工复核提示。 | resonance | 2026-06-16 | 1.42643 | 1000 | 1426.43 | 1.622 | 1622 | 195.57 | 0.137105 | 23 | 1.42643 | 12.06% |  |
| 516510 | 云计算ETF | theme | theme_beta | 20 |  |  | resonance | 2026-07-10 | 1.812686 | 700 | 1268.88 | 1.805 | 1263.5 | -5.38 | -0.00424 | -1 | 1.722051 | 4.60% |  |
| 159929 | 医药ETF | sector | sector_beta | 30 |  |  | resonance | 2026-07-10 | 1.3094 | 100 | 130.94 | 1.259 | 125.9 | -5.04 | -0.038491 | -1 | 1.230836 | 2.24% |  |

## 已实现盈亏
- realized_pnl：-133.27 元
- realized_pnl 仅来自 data/paper_trades.csv 的本地模拟 BUY/SELL 流水，不代表真实账户。
| trade_date | symbol | name | action | price | quantity | amount | realized_pnl | execution_price_type | order_type | source | simulated_cash | position_value | total_equity | reason |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-06-09 | 512800 | 银行ETF | BUY | 0.792 | 1100 | 871.2 | 0 | close_price | paper_buy | buy_signal_ranking | 7632.8 | 2367.2 | 10000 | rank_score=90.914761; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-09 | 515880 | 证券公司ETF | BUY | 1.695 | 300 | 508.5 | 0 | close_price | paper_buy | buy_signal_ranking | 7124.3 | 2875.7 | 10000 | rank_score=90.247897; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-16 | 515220 | 煤炭ETF | SELL | 1.257623 | 1100 | 1383.38 | -117.62 | close_price_with_slippage | paper_sell | paper_trade_engine | 8502.68 | 1388.9 | 9891.58 | stop_loss_break |
| 2026-06-16 | 515000 | 科技ETF | BUY | 1.421426 | 1000 | 1421.43 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7076.25 | 2809.9 | 9886.15 | paper_rule_validation; rank=1; rank_score=91.770799; mid_trend=BUY; short_swing=BUY; amount=1421.43 |
| 2026-06-23 | 515880 | 证券公司ETF | SELL | 1.858442 | 300 | 557.53 | 44.03 | close_price_with_slippage | paper_sell | paper_trade_engine | 7628.78 | 2446.1 | 10074.88 | REDUCE two consecutive days |
| 2026-06-23 | 512880 | 证券ETF | BUY | 1.131339 | 500 | 565.67 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7058.11 | 3011.6 | 10069.71 | paper_rule_validation; rank=1; rank_score=91.306916; mid_trend=BUY; short_swing=BUY; amount=565.67 |
| 2026-07-09 | 512880 | 证券ETF | SELL | 1.110667 | 500 | 555.33 | -20.34 | close_price_with_slippage | paper_sell | paper_trade_engine | 7608.44 | 2357 | 9965.44 | REDUCE two consecutive days |
| 2026-07-10 | 512800 | 银行ETF | SELL | 0.760772 | 1100 | 836.85 | -39.35 | close_price_with_slippage | paper_sell | paper_trade_engine | 8440.29 | 1622 | 10062.29 | max_holding_days reached without signal recovery |
| 2026-07-10 | 516510 | 云计算ETF | BUY | 1.805541 | 700 | 1263.88 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7171.41 | 2885.5 | 10056.91 | paper_rule_validation; rank=1; rank_score=88.861036; mid_trend=BUY; short_swing=BUY; amount=1263.88 |
| 2026-07-10 | 159929 | 医药ETF | BUY | 1.259378 | 100 | 125.94 | 0 | close_price_with_slippage | paper_buy | paper_trade_engine | 7040.47 | 3011.4 | 10051.87 | paper_rule_validation; rank=2; rank_score=86.216237; mid_trend=BUY; short_swing=BUY; amount=125.94 |

## 记录说明
- 如需新增模拟持仓，手动填写 data/paper_positions.csv。
- data/paper_trades.csv 只用于模拟流水备查，不代表任何真实交易。
- 系统只做本地估值和报告，不会自动写入真实交易或下单。