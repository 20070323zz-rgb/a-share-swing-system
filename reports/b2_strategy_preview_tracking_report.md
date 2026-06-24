# B2 Original vs Adjusted Preview Tracking 报告

- 生成时间：2026-06-24 23:04:54
- 阶段：B2 strategy_preview_tracking_v1。
- 目标：长期跟踪 original ranking 与 adjusted preview ranking 的 forward returns。

## 今日 Top 3
### Original Top 3
1. 512880 证券ETF：rank=1，score=91.8274
2. 159819 人工智能ETF：rank=2，score=88.4364
3. 515070 AIETF：rank=3，score=88.3806

### Adjusted Preview Top 3
1. 512880 证券ETF：rank=1，score=87.8274
2. 159819 人工智能ETF：rank=2，score=86.4364
3. 515070 AIETF：rank=3，score=86.3806

- Top 3 是否变化：否。

## Tracking 写入
- 新增：0 条。
- 更新：10 条。
- forward return 回填 cell：0。
- completed / partial / pending / missing：0 / 38 / 10 / 0。

## 当前样本结论
- 样本是否足够：否。
- 是否可以证明 adjusted preview 更优：否。当前样本不足，不能证明 adjusted preview 优于 original ranking。

## 影子组合
- shadow rows：21。
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
