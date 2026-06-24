# Model Enhancement Decision Report 2026-06-18 20:28:15

## 结论

- model_enhancement_needed = true
- next_step = Phase 4B-1: ranking_model_v2 historical backtest with Top10 candidate + risk/diversification filter
- reason = Current Phase 4A ranking is a simplified proxy with weak Top3 edge; improve signal layer before tuning exits or expanding pool.

## 诊断回答

1. 当前基础模型偏低级：是。Phase 4A 只重建了 simplified ranking。
2. 跑不赢 510300 的主因：成本 + 换手 + ranking 因子弱 + 市场 beta 暴露。
3. 应先增强模型，而不是继续调止盈止损。
4. 应先复现 full daily signal historical replay。
5. 建议从 Top3 直接买入，改为 Top10 candidate + risk/diversification filter 研究。
6. market_state 应作为仓位/风格过滤研究，但暂不强制执行。
7. ETF type-aware ranking 有必要。
8. 建议启动 Phase 4B-1：ranking_model_v2 historical backtest。

## 数据源现实约束

- 不应使用 same_day_close 作为正式可执行口径。
- 应以 confirmed close 生成次日计划。
- BaoStock 晚更新会让正式信号延迟，回测应纳入该现实。

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不改变 paper_trade_engine.py。
