# Alpha 因子增强研究 2026-06-21 21:17:52

本研究限制在少量有经济逻辑的 alpha 因子，不做大规模网格，不用未来收益。

- 最佳 alpha 候选：persistence_breakout_v2
- total_return：20.19%
- max_drawdown：-3.43%

| strategy | return | max_drawdown | calmar | trades | cost | beat_v2 | shadow |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| relative_strength_plus_trend_v2 | 1.94% | -13.68% | 0.13 | 128 | 790.49 | False | False |
| risk_adjusted_momentum_v2 | 6.54% | -8.54% | 0.73 | 46 | 284.81 | False | False |
| persistence_breakout_v2 | 20.19% | -3.43% | 5.58 | 76 | 469.96 | True | True |
| alpha_blend_simple_v2 | 1.54% | -5.42% | 0.27 | 36 | 222.57 | False | False |

所有 alpha 候选 ready_for_execution=false。