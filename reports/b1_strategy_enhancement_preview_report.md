# B1 执行层渐进优化第一版报告

- 生成时间：2026-07-04 00:00:54
- 阶段：B1 strategy_enhancement_preview_v1。
- 目标：预览 market_state、ETF 类型、组合暴露、数据健康对 BUY ranking 和 sell review 的影响。

## 是否新增 adjusted_rank_score_preview
- 已新增，仅写入 `reports/strategy_enhancement_preview.csv` 和 `reports/strategy_enhancement_preview.md`。
- 不修改原始 BUY ranking。
- 不修改 paper_trade_engine 真实买入排序。

## Top 3 对照
### Original Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=94.493
3. 159929 医药ETF：rank=3，score=79.4343

### Adjusted Preview Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=90.493
3. 588000 科创50ETF：rank=3，score=79.6456

- Top 3 是否变化：是。

## 变化原因
- 512760 芯片ETF：delta=-5；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3
- 512880 证券ETF：delta=-4；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 588000 科创50ETF：delta=3；组合缺少宽基，broad_index_balance_bonus +3
- 510180 上证180ETF：delta=3；组合缺少宽基，broad_index_balance_bonus +3
- 515070 AIETF：delta=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 159819 人工智能ETF：delta=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 159995 芯片ETF：delta=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 515000 科技ETF：delta=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2

## 当前是否用于真实模拟买入
- 否。`adjusted_rank_score_execution_enabled = false`。
- paper_trade_engine 仍使用原始规则和原始 BUY ranking。
- 本轮只观察增强分对排序的理论影响，避免未经验证的参数直接进入执行层。

## 当前持仓类型化 REVIEW
- 详见 `reports/sell_signal_review.md` 与 dashboard 的 Type-aware Review 模块。

## 是否修改模拟盘文件
- 未修改 `data/paper_trades.csv`。
- 未修改 `data/paper_positions.csv`。

## 安全边界
- 本轮只做 preview，不改变真实模拟盘成交结果。
- 不修改 paper_trade_engine 核心执行规则。
- 不启用 market_state 仓位控制。
- 不启用 adjusted_rank_score 作为真实买入排序。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
