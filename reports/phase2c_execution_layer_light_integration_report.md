# Phase 2C 执行层轻量接入报告

- 生成时间：2026-06-24 23:04:51
- 本报告说明 Phase 2B 高置信度研究结论如何轻量进入模拟交易计划和看板。

## 本轮接入字段
- `market_state`
- `market_score`
- `suggested_position_pct`
- `current_position_pct`
- `position_alignment`
- `etf_type`
- `risk_profile`
- `holding_profile`
- `max_holding_days`
- `stop_loss_pct`
- `distance_to_stop_pct`
- `portfolio_exposure_status`
- `portfolio_balance_suggestion`
- `concentration_warning`
- `research_confidence`
- `execution_layer_note`

## 只展示不执行的结论
- market_state 只展示建议仓位，不改变买入金额、目标仓位或 max_holdings。
- portfolio_exposure 只提示组合平衡和集中度，不阻断买入、不强制卖出。
- etf_type 的 max_holding_days / stop_loss_pct 先用于计划解释和风险展示，不新增硬卖出规则。

## 是否改变买卖结果
- buy_count：0
- sell_count：0
- dry_run：True
- 本轮新增字段不参与 amount、slots、can_buy、sell_reason 的核心判断。

## 是否改变核心逻辑
- 未改变 PAPER_MAX_HOLDINGS。
- 未改变 rank 权重分配。
- 未启用 market_state 仓位控制。
- 未启用 portfolio_exposure 硬阻断。

## paper 文件
- 本报告生成时不直接修改 paper_trades.csv。
- dry-run 不修改 paper_positions.csv。
- execute 模式仍保留原有防重复交易机制。

## 计划字段覆盖
- paper_trade_plan 行数：6
- 新增字段存在数量：16 / 16
- 执行前仓位：29.84%
- 执行后仓位：29.84%
- PAPER_USE_MARKET_STATE_POSITION：False

## L2 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不添加真实交易按钮。