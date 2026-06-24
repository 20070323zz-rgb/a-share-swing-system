# v2 收益拖累归因 2026-06-21 21:17:07

本报告只做 research/diagnostics，不修改模拟盘、不接执行层。

## 摘要
- Structural exposure cap around 60% makes v2 lag beta buy-and-hold during fast rallies.
- Top10 diversification and high-beta limits reduce drawdown but filter out some upside.
- Trend confirmation avoids weak setups but can buy late or skip early breakouts.
- v2 收益：11.31%
- 510300 buy-and-hold：19.94%
- 平均仓位：38.39%

## 年度归因
| year | v2_return | 510300_return | excess | v2_drawdown |
| --- | ---: | ---: | ---: | ---: |
| 2025 | 8.69% | 14.28% | -5.58% | -4.82% |
| 2026 | 0.95% | 1.90% | -0.96% | -4.86% |

## 月度明显落后月份
| month | v2 | 510300 | excess | fast_up |
| --- | ---: | ---: | ---: | --- |
| 2025-08 | 2.69% | 7.18% | -4.49% | True |
| 2026-04 | -0.13% | 4.12% | -4.24% | True |
| 2026-05 | -1.87% | 0.47% | -2.34% | False |
| 2025-09 | -0.53% | 1.78% | -2.31% | False |
| 2026-06 | 0.00% | 1.57% | -1.57% | False |
| 2025-10 | -1.72% | -0.83% | -0.88% | False |
| 2025-12 | 0.47% | 0.93% | -0.46% | False |
| 2025-05 | 0.00% | 0.00% | 0.00% | False |
| 2025-07 | 2.83% | 2.62% | 0.22% | False |
| 2025-11 | -1.00% | -1.79% | 0.79% | False |

## 仓位归因
- 平均仓位：38.39%
- 低仓位天数 exposure<40%：102
- 目标总仓位：60.00%

## 过滤归因
过滤规则保护了回撤，但在部分 risk-on 阶段也过滤掉后续上涨标的。
- high_beta_exposure: count=2, avg_forward_20d=13.75%, max=13.97%
- liquidity_trading_constraint: count=56, avg_forward_20d=2.16%, max=14.79%
- not_selected_lower_priority: count=169, avg_forward_20d=1.68%, max=24.45%
- already_held: count=161, avg_forward_20d=1.60%, max=15.38%
- group_concentration: count=13, avg_forward_20d=0.83%, max=14.09%
- trend_confirmation: count=1809, avg_forward_20d=0.46%, max=33.61%
- cooldown: count=15, avg_forward_20d=-3.85%, max=-0.82%

## 交易归因
- 交易数：101
- 总成本：384.01
- 交易次数下降降低成本和回撤，但也可能因确认/冷却/最大持有期错过趋势延续。

## 结论
- 是否过度防守：True
- 是否仓位不足：True
- 是否存在过滤错失上涨：True
- 下一步：test regime-aware relaxed filters and simple alpha enhancements; keep execution disabled.