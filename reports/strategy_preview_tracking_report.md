# Strategy Preview Tracking Report 2026-06-24 23:04:54

本报告追踪 original BUY ranking 与 adjusted preview ranking 的后续表现，只作研究，不影响 paper_trade_engine。

## 摘要
- latest_snapshot_date：2026-06-24
- tracking rows：48
- inserted / updated：0 / 10
- forward filled cells：0
- completed / partial / pending / missing：0 / 38 / 10 / 0
- Top 3 是否变化：否
- 样本是否足够：否
- 结论：当前样本不足，不能证明 adjusted preview 优于 original ranking。

## 今日 Original Top 3
1. 512880 证券ETF：rank=1，score=91.8274
2. 159819 人工智能ETF：rank=2，score=88.4364
3. 515070 AIETF：rank=3，score=88.3806

## 今日 Adjusted Preview Top 3
1. 512880 证券ETF：rank=1，score=87.8274
2. 159819 人工智能ETF：rank=2，score=86.4364
3. 515070 AIETF：rank=3，score=86.3806

## Forward Return Comparison
| group | sample | 1d mean | 1d n | 3d mean | 3d n | 5d mean | 5d n | 10d mean | 10d n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original_top3 | 21 | 0.39% | 18 | 3.15% | 12 | 3.98% | 6 | N/A | 0 |
| adjusted_top3 | 21 | -0.42% | 18 | 1.04% | 12 | 0.94% | 6 | N/A | 0 |
| only_original_top3 | 4 | 3.85% | 4 | 5.81% | 4 | 5.94% | 2 | N/A | 0 |
| only_adjusted_top3 | 4 | 0.20% | 4 | -0.52% | 4 | -3.18% | 2 | N/A | 0 |
| high_beta_penalty | 16 | 0.26% | 14 | 2.97% | 10 | 3.37% | 6 | N/A | 0 |
| data_health_penalty | 9 | 2.39% | 7 | 7.08% | 5 | 6.27% | 4 | N/A | 0 |
| concentration_penalty | 31 | 0.29% | 25 | 2.37% | 19 | 2.48% | 13 | N/A | 0 |
| broad_index_bonus | 6 | -0.60% | 4 | -0.05% | 2 | N/A | 0 | N/A | 0 |
| defensive_bonus | 0 | N/A | 0 | N/A | 0 | N/A | 0 | N/A | 0 |

## Penalty / Bonus Review
- high_beta penalty ETF 后续表现：sample=16, 1d=0.26%, 3d=2.97%, 5d=3.37%, 10d=N/A
- data_health penalty ETF 后续表现：sample=9, 1d=2.39%, 3d=7.08%, 5d=6.27%, 10d=N/A
- concentration penalty ETF 后续表现：sample=31, 1d=0.29%, 3d=2.37%, 5d=2.48%, 10d=N/A
- broad_index bonus ETF 后续表现：sample=6, 1d=-0.60%, 3d=-0.05%, 5d=N/A, 10d=N/A
- defensive bonus ETF 后续表现：sample=0, 1d=N/A, 3d=N/A, 5d=N/A, 10d=N/A

## 安全边界
- research only / preview only。
- 不改变 paper_trade_engine 执行排序。
- 不启用 adjusted_rank_score 执行。
- 不启用 market_state 仓位控制。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
