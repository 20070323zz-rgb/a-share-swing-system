# Strategy Preview Tracking Report 2026-07-04 00:00:55

本报告追踪 original BUY ranking 与 adjusted preview ranking 的后续表现，只作研究，不影响 paper_trade_engine。

## 摘要
- latest_snapshot_date：2026-07-03
- tracking rows：94
- inserted / updated：11 / 0
- forward filled cells：46
- completed / partial / pending / missing：26 / 57 / 11 / 0
- Top 3 是否变化：是
- 样本是否足够：否
- 结论：当前样本不足，不能证明 adjusted preview 优于 original ranking。

## 今日 Original Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=94.493
3. 159929 医药ETF：rank=3，score=79.4343

## 今日 Adjusted Preview Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=90.493
3. 588000 科创50ETF：rank=3，score=79.6456

## Forward Return Comparison
| group | sample | 1d mean | 1d n | 3d mean | 3d n | 5d mean | 5d n | 10d mean | 10d n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original_top3 | 36 | 0.12% | 33 | 1.00% | 30 | 0.75% | 27 | 3.14% | 12 |
| adjusted_top3 | 36 | -0.55% | 33 | -0.11% | 30 | -0.77% | 27 | 0.37% | 12 |
| only_original_top3 | 7 | 3.68% | 6 | 4.67% | 6 | 3.81% | 5 | 1.34% | 4 |
| only_adjusted_top3 | 7 | -0.01% | 6 | -0.86% | 6 | -4.39% | 5 | -6.98% | 4 |
| high_beta_penalty | 26 | 0.06% | 25 | 0.85% | 23 | 1.97% | 20 | 2.98% | 10 |
| data_health_penalty | 16 | -0.09% | 15 | -0.50% | 15 | -0.66% | 13 | 1.76% | 5 |
| concentration_penalty | 58 | -0.40% | 54 | 0.53% | 48 | 0.55% | 42 | 1.94% | 19 |
| broad_index_bonus | 13 | -0.65% | 11 | 0.60% | 10 | -1.24% | 9 | -0.10% | 2 |
| defensive_bonus | 0 | N/A | 0 | N/A | 0 | N/A | 0 | N/A | 0 |

## Penalty / Bonus Review
- high_beta penalty ETF 后续表现：sample=26, 1d=0.06%, 3d=0.85%, 5d=1.97%, 10d=2.98%
- data_health penalty ETF 后续表现：sample=16, 1d=-0.09%, 3d=-0.50%, 5d=-0.66%, 10d=1.76%
- concentration penalty ETF 后续表现：sample=58, 1d=-0.40%, 3d=0.53%, 5d=0.55%, 10d=1.94%
- broad_index bonus ETF 后续表现：sample=13, 1d=-0.65%, 3d=0.60%, 5d=-1.24%, 10d=-0.10%
- defensive bonus ETF 后续表现：sample=0, 1d=N/A, 3d=N/A, 5d=N/A, 10d=N/A

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
