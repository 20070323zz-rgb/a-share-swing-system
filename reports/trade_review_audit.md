# 交易复盘数据审计 2026-07-04 00:02:01

本审计只读取本地模拟盘文件，不修改 `paper_trades.csv` / `paper_positions.csv`。

## 当前交易记录字段
- `paper_trades.csv` 字段：date, symbol, name, action, price, raw_close, execution_price, execution_price_type, quantity, gross_amount, commission, stamp_tax, transfer_fee, net_cash_change, slippage_rate, reason, source, created_at, holding_days, realized_pnl, realized_pnl_pct, cash_after_trade, position_value_after_trade, total_equity_after_trade, trade_date, strategy_source, position_type, amount, fee, order_type, simulated_cash, position_value, total_equity, is_simulated
- `paper_positions.csv` 字段：symbol, name, quantity, avg_cost, raw_cost, total_cost, commission_paid, entry_date, last_price, etf_type, risk_profile, holding_profile, group, max_holding_days, stop_loss_pct, classification_reason, stop_loss_price, sell_review_status, data_health_status, protection_period, updated_at, strategy_source, position_type, entry_price, cost, stop_loss, reason, market_value, unrealized_pnl, unrealized_pnl_pct, holding_days, distance_to_stop_pct, current_price, unrealized_return, risk_alert

## 可用性判断
- 是否有买入/卖出理由字段：是，存在 reason/source/strategy_source
- 是否有信号快照：部分有，可从 reason 中解析 rank_score/mid_trend/short_swing
- 是否能推导持仓周期：是，可由买入日期、卖出日期或最新数据日推导。
- 是否能推导最大浮盈/最大浮亏：是，若本地 ETF 日线存在 high/low 字段。
- 是否能配对完整交易闭环：已平仓 2 条；未平仓 3 条；采用 FIFO 配对。

## 精确值
- 交易日期、代码、方向、数量、成交价、成交金额、交易来源字段来自模拟交易流水。
- 当前持仓数量、持仓市值、未实现盈亏来自模拟持仓文件。

## 估算值
- 最大浮盈/最大浮亏使用本地日线 high/low 估算。
- 未平仓交易 PnL 使用最新本地 close/positions current_price 估算。
- 510300 对比收益使用本地 510300 ETF close 估算。

## 暂不能判断
- 当前样本过少，不能判断策略稳定盈利。
- 没有完整入场时刻分时数据，不能评估日内执行优劣。
- 新闻/情绪/宏观触发原因未写入交易流水，不能做精确事件归因。
