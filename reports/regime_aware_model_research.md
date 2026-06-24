# Regime-aware 模型研究 2026-06-21 21:17:19

本研究只使用市场内部日线数据，不使用未来数据，不接执行层。

- 最佳候选：risk_off_defensive_v2
- total_return：16.54%
- max_drawdown：-4.07%
- ready_for_execution：false

| strategy | return | max_drawdown | calmar | sharpe | trades | avg_exposure | risk_on | neutral | risk_off | shadow |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| static_v2_baseline | 14.03% | -4.61% | 2.88 | 1.70 | 68 | 37.74% | 16.98% | 2.37% | -4.78% | False |
| risk_on_relaxed_filter_v2 | 7.65% | -8.34% | 0.87 | 1.03 | 68 | 45.82% | 11.25% | 2.14% | -4.91% | False |
| risk_off_defensive_v2 | 16.54% | -4.07% | 3.85 | 1.95 | 64 | 35.97% | 17.70% | 2.80% | -3.68% | True |
| regime_switching_v2 | 10.37% | -6.86% | 1.44 | 1.34 | 66 | 45.67% | 12.58% | 3.02% | -4.49% | False |

## 结论
- 如果 risk-on relaxed 版本收益改善，说明 v2 可能过度防守。
- 如果 risk-off defensive 回撤改善但收益下降，说明防御层更适合作风控展示而非收益主模型。
- 所有候选仍为 research-only，不能接入 paper_trade_engine。