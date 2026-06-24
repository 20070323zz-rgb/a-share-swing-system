# ETF type-aware 模型研究 2026-06-21 21:17:49

本研究只使用现有合格 trade_pool 和 ETF 分类，不扩池，不接执行层。

- 最佳候选：single_score_v2_baseline
- total_return：14.03%
- max_drawdown：-4.61%

| strategy | return | max_drawdown | calmar | trades | avg_exposure | beat_v2 | shadow |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| single_score_v2_baseline | 14.03% | -4.61% | 2.88 | 68 | 37.74% | False | False |
| type_weighted_score_v2 | 8.67% | -8.39% | 0.98 | 68 | 39.22% | False | False |
| type_regime_combined_v2 | 6.95% | -10.37% | 0.64 | 58 | 38.19% | False | False |

## 类型贡献
不同 ETF 类型使用不同权重可以改善模型解释性，但样本仍短，不能直接接执行层。
- single_score_v2_baseline / broad_index: pnl=355.30, trades=4, avg_holding_days=14.2
- single_score_v2_baseline / commodity_resource: pnl=2011.25, trades=14, avg_holding_days=14.3
- single_score_v2_baseline / high_beta: pnl=261.35, trades=1, avg_holding_days=16.0
- single_score_v2_baseline / sector: pnl=-353.31, trades=14, avg_holding_days=18.1
- single_score_v2_baseline / theme: pnl=531.46, trades=1, avg_holding_days=14.0
- type_regime_combined_v2 / bond_cash: pnl=53.78, trades=1, avg_holding_days=23.0
- type_regime_combined_v2 / commodity_resource: pnl=1607.09, trades=14, avg_holding_days=16.1
- type_regime_combined_v2 / high_beta: pnl=317.95, trades=2, avg_holding_days=23.5
- type_regime_combined_v2 / sector: pnl=-226.94, trades=3, avg_holding_days=25.7
- type_regime_combined_v2 / theme: pnl=-361.02, trades=9, avg_holding_days=20.9
- type_weighted_score_v2 / commodity_resource: pnl=1735.70, trades=16, avg_holding_days=14.6
- type_weighted_score_v2 / high_beta: pnl=29.74, trades=2, avg_holding_days=18.5
- type_weighted_score_v2 / sector: pnl=-712.16, trades=11, avg_holding_days=19.7
- type_weighted_score_v2 / theme: pnl=681.40, trades=5, avg_holding_days=15.2