# 模拟盘持仓报告 2026-06-10

本报告只读取本地模拟盘记录，不接券商 API，不下单，不读取账号密码。

## 账户摘要
- 初始模拟本金：10000.00 元
- 当前现金：7124.30 元
- 当前持仓市值：2811.10 元
- 当前总资产：9935.40 元
- 当前持仓数：3
- 浮动盈亏：-64.60 元
- 浮动盈亏率：-2.25%
- 已实现盈亏：0.00 元
- 总盈亏：-64.60 元
- 模拟交易流水数：3
- 风险提醒数量：0

## 当前持仓
| symbol | name | strategy_source | position_type | entry_date | entry_price | quantity | cost | current_price | market_value | unrealized_pnl | unrealized_return | holding_days | stop_loss | risk_alert |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 515220 | 煤炭ETF | resonance | core | 2026-06-09 | 1.36 | 1100 | 1496 | 1.305 | 1435.5 | -60.5 | -0.040441 | 1 | 1.258 |  |
| 512800 | 银行ETF | resonance | core | 2026-06-09 | 0.792 | 1100 | 871.2 | 0.806 | 886.6 | 15.4 | 0.017677 | 1 | 0.7326 |  |
| 515880 | 证券公司ETF | resonance | core | 2026-06-09 | 1.695 | 300 | 508.5 | 1.63 | 489 | -19.5 | -0.038348 | 1 | 1.567875 |  |

## 已实现盈亏
- realized_pnl：0.00 元
- realized_pnl 仅来自 data/paper_trades.csv 的本地模拟 BUY/SELL 流水，不代表真实账户。
| trade_date | symbol | name | action | price | quantity | amount | realized_pnl | execution_price_type | order_type | source | simulated_cash | position_value | total_equity | reason |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-06-09 | 515220 | 煤炭ETF | BUY | 1.36 | 1100 | 1496 | 0 | close_price | paper_buy | buy_signal_ranking | 8504 | 1496 | 10000 | rank_score=93.244634; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-09 | 512800 | 银行ETF | BUY | 0.792 | 1100 | 871.2 | 0 | close_price | paper_buy | buy_signal_ranking | 7632.8 | 2367.2 | 10000 | rank_score=90.914761; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |
| 2026-06-09 | 515880 | 证券公司ETF | BUY | 1.695 | 300 | 508.5 | 0 | close_price | paper_buy | buy_signal_ranking | 7124.3 | 2875.7 | 10000 | rank_score=90.247897; mid_trend=BUY; short_swing=BUY; source=buy_signal_ranking |

## 记录说明
- 如需新增模拟持仓，手动填写 data/paper_positions.csv。
- data/paper_trades.csv 只用于模拟流水备查，不代表任何真实交易。
- 系统只做本地估值和报告，不会自动写入真实交易或下单。