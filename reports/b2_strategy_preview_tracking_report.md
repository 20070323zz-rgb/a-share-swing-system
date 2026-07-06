# B2 Original vs Adjusted Preview Tracking 报告

- 生成时间：2026-07-04 00:00:55
- 阶段：B2 strategy_preview_tracking_v1。
- 目标：长期跟踪 original ranking 与 adjusted preview ranking 的 forward returns。

## 今日 Top 3
### Original Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=94.493
3. 159929 医药ETF：rank=3，score=79.4343

### Adjusted Preview Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=90.493
3. 588000 科创50ETF：rank=3，score=79.6456

- Top 3 是否变化：是。

## Tracking 写入
- 新增：11 条。
- 更新：0 条。
- forward return 回填 cell：46。
- completed / partial / pending / missing：26 / 57 / 11 / 0。

## 当前样本结论
- 样本是否足够：否。
- 是否可以证明 adjusted preview 更优：否。当前样本不足，不能证明 adjusted preview 优于 original ranking。

## 影子组合
- shadow rows：36。
- initial_cash_assumption：20000.00。
- single_position_target：20%；total_target_position：60%；min_trade_value：3000.00。
- shadow_model_enabled：true。
- shadow_model_execution_enabled：false。
- paper_trade_engine_enabled：false。
- real_trade_enabled：false。
- 仅作 research only，不影响真实模拟盘。

## 是否影响真实模拟交易
- 不影响 paper_trade_engine。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
