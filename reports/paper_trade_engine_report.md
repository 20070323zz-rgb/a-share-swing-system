# paper_trade_engine 执行报告

- 生成时间：2026-07-04 00:00:52
- 本轮是模拟盘自动交易，不是真实交易。
- launchd/catchup 只负责触发；paper_trade_engine 负责模拟盘规则判断和本地 CSV 写入。
- Codex 只负责开发、修复和优化，不作为每日交易执行器。
- 运行日期 run_date：2026-07-04
- 价格数据日期 price_data_date：2026-07-03
- 当前状态：executed
- dry_run：False
- 买入数量：0
- 卖出数量：0
- 今日佣金：0.00
- 今日滑点成本估算：0.00
- 今日交易成本合计：0.00
- 执行价格口径：close_price_with_slippage
- paper_trades 同日同 symbol/action/source 重复数：0
- 执行后现金：7058.11
- 执行后持仓数：3
- 执行后仓位：29.44%
- PAPER_USE_MARKET_STATE_POSITION：False

## Phase 2C 轻量接入
- 已接入 etf_type / max_holding_days / stop_loss_pct / classification_reason 到交易计划解释字段。
- 已接入 market_state / market_score / suggested_position_pct / position_alignment 到交易计划解释字段。
- 已接入 portfolio_exposure_status / portfolio_balance_suggestion / concentration_warning 到交易计划解释字段。
- 以上字段只用于 REVIEW、风险展示、paper_trade_plan 解释和 dashboard 展示，不改变买卖结果。
- market_state 仓位控制默认关闭，不直接改变目标仓位。

## 交易成本真实化
- 佣金率：0.00012
- 单笔最低佣金：5.00 元
- 滑点率：0.0003
- ETF 模拟暂不计印花税：0.0
- 过户费率：0.0
- 买入现金扣除包含成交金额、佣金和过户费。
- 卖出现金增加扣除佣金、印花税和过户费。

## dashboard 展示
- 顶部状态栏展示 paper mode / auto execute / real trade disabled。
- 今日模拟交易状态展示执行状态、买入/卖出数量、跳过原因。
- 今日模拟交易计划展示执行/跳过记录。
- 当前持仓展示保护期、止损、距离止损、sell review。

## L2 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户/资金/持仓。
- 不保存密码/token。