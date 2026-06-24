# Missed Opportunity Observation Rules

当前阶段不允许马上放宽过滤规则。

只有满足以下条件，未来才可以进入“规则放宽研究”：

1. 至少积累 20 个交易日。
2. risk_on 空仓样本足够多。
3. 被 trend_not_confirmed 过滤的候选，forward 10d 明显跑赢 510300。
4. 被 breakout_not_confirmed 过滤的候选，forward 10d 明显跑赢 510300。
5. missed_opportunity_rate 持续偏高。
6. 放宽过滤的模拟回测不显著增加回撤。
7. 仍保持 ready_for_execution = false。

当前结论：

- ready_to_relax_filters = false
- ready_for_preview = false
- ready_for_execution = false
- execution_enabled = false
- paper_trade_engine_enabled = false
- real_trade_enabled = false
