# Strategy Preview Tracking Report 2026-07-10 16:28:08

本报告追踪 original BUY ranking 与 adjusted preview ranking 的后续表现，只作研究，不影响 paper_trade_engine。

## 摘要
- latest_snapshot_date：2026-07-09
- tracking rows：126
- inserted / updated：7 / 0
- forward filled cells：26
- completed / partial / pending / missing：55 / 64 / 7 / 0
- Top 3 是否变化：否
- 样本是否足够：是
- 结论：样本已开始积累，但仍需结合周/月度复盘后再判断是否接入执行层。

## 今日 Original Top 3
1. 516510 云计算ETF：rank=1，score=88.861
2. 159929 医药ETF：rank=2，score=86.2162
3. 515000 科技ETF：rank=3，score=77.0373

## 今日 Adjusted Preview Top 3
1. 516510 云计算ETF：rank=1，score=86.861
2. 159929 医药ETF：rank=2，score=84.2162
3. 515000 科技ETF：rank=3，score=75.0373

## Forward Return Comparison
| group | sample | 1d mean | 1d n | 3d mean | 3d n | 5d mean | 5d n | 10d mean | 10d n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original_top3 | 48 | 0.15% | 45 | 0.07% | 39 | -1.89% | 33 | -3.70% | 24 |
| adjusted_top3 | 48 | -0.35% | 45 | -0.63% | 39 | -3.31% | 33 | -5.09% | 24 |
| only_original_top3 | 7 | 3.29% | 7 | 3.47% | 7 | 3.13% | 6 | 1.34% | 4 |
| only_adjusted_top3 | 7 | 0.08% | 7 | -0.45% | 7 | -4.71% | 6 | -6.98% | 4 |
| high_beta_penalty | 28 | -0.08% | 28 | 0.44% | 27 | -1.05% | 25 | 1.69% | 18 |
| data_health_penalty | 18 | -0.07% | 17 | 0.17% | 17 | -5.36% | 15 | -5.12% | 11 |
| concentration_penalty | 72 | -1.10% | 67 | -2.10% | 63 | -3.50% | 54 | -3.04% | 36 |
| broad_index_bonus | 19 | 0.60% | 18 | 1.19% | 16 | -2.16% | 11 | -2.10% | 7 |
| defensive_bonus | 0 | N/A | 0 | N/A | 0 | N/A | 0 | N/A | 0 |

## Penalty / Bonus Review
- high_beta penalty ETF 后续表现：sample=28, 1d=-0.08%, 3d=0.44%, 5d=-1.05%, 10d=1.69%
- data_health penalty ETF 后续表现：sample=18, 1d=-0.07%, 3d=0.17%, 5d=-5.36%, 10d=-5.12%
- concentration penalty ETF 后续表现：sample=72, 1d=-1.10%, 3d=-2.10%, 5d=-3.50%, 10d=-3.04%
- broad_index bonus ETF 后续表现：sample=19, 1d=0.60%, 3d=1.19%, 5d=-2.16%, 10d=-2.10%
- defensive bonus ETF 后续表现：sample=0, 1d=N/A, 3d=N/A, 5d=N/A, 10d=N/A

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
