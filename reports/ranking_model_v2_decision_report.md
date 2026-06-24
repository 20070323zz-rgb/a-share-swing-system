# Ranking Model v2 决策报告 2026-06-19 00:51:29

本报告用于决定 Phase 4B-1 研究结论是否进入下一阶段影子跟踪，不改变执行层。

## 明确结论

```text
best_candidate = top10_diversified_filter_v2
strategy_quality_label = low_drawdown_candidate_not_alpha_proven
candidate_ready_for_shadow_tracking = true
candidate_ready_for_execution = false
expand_pool_now = false
next_step = Phase 4B-2 shadow tracking for ranking_model_v2 best candidate
```

## 策略定位

- `top10_diversified_filter_v2` 当前不是优秀收益策略，也不是 alpha 已验证模型。
- 它的价值主要是：相对 original / adjusted baseline 降低回撤、降低换手、结构更健康。
- 它没有跑赢 510300 buy-and-hold：best total_return=11.31%，510300 total_return=19.94%。
- 因此只能进入 shadow tracking，不能接入 `paper_trade_engine.py` 正式执行层。
- 当前不扩池，不真实交易，不替代 current adjusted preview。

## 必答问题

1. 哪个 ranking_model_v2 候选最好？
   - `top10_diversified_filter_v2`，按 Calmar、收益和换手惩罚综合排序。

2. 最好策略是否跑赢 510300？
   - `false`。best total_return=11.31%，510300 total_return=19.94%。

3. 最好策略是否降低最大回撤？
   - `true`。best max_drawdown=-4.86%，original max_drawdown=-9.63%。

4. Top10 candidate + diversified filter 是否有效？
   - `true`。top10 total_return=11.31%，top10 max_drawdown=-4.86%。

5. relative_strength 是否应该进入主模型？
   - 可以进入 shadow tracking 候选。它能区分“跟随市场上涨”和“跑赢基准/同组”的 ETF。

6. momentum_20d 是否应该进入主模型？
   - 可以作为核心候选因子，但必须搭配趋势确认和换手控制。

7. risk_adjusted_momentum 是否优于简单 momentum？
   - 适合作为二级排序或风险调整，是否优于简单 momentum 取决于本轮回测结果，暂不直接执行。

8. volume/liquidity 是否应作为约束而不是 alpha？
   - 是。成交额/成交量更适合作为交易约束和数据质量过滤。

9. 成熟 ETF 轮动框架中哪些思想有效？
   - 中期动量、相对强弱、趋势确认、TopN 二次筛选、同 group 分散、最小持仓和 cooldown。

10. 哪些成熟框架不适合直接迁移到 A 股 ETF？
   - 美股低成本高流动性假设、全球多资产 ETF 配置口径、QDII 无折溢价/汇率风险假设、日内高频执行。

11. 是否应该进入 Phase 4B-2？
   - `true`。

12. 是否可以把某个 v2 模型接入 shadow tracking？
   - `true`，候选为 `top10_diversified_filter_v2`。

13. 是否暂不应接入真实 paper_trade_engine？
   - 是，`candidate_ready_for_execution = false`。收益率仍不够理想，且未跑赢 510300，不能标记为 live-ready 或 profitable enough。

14. 是否仍不建议扩池？
   - 是，`expand_pool_now = false`；先修复模型与执行口径，再谈扩池。

## 安全边界

- 未修改 paper_trades.csv。
- 未修改 paper_positions.csv。
- 未修改 paper_trade_engine.py。
- 不接券商 API，不真实下单，不读取真实账户。
