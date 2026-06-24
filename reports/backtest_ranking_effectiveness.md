# Backtest Ranking Effectiveness 2026-06-19 00:53:15

| strategy | rank_bucket | market_regime | sample_count | avg_forward_1d_return | avg_forward_3d_return | avg_forward_5d_return | avg_forward_10d_return | avg_forward_20d_return | rank_score_corr_10d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adjusted_preview_baseline | 1-3 | down | 233 | 0.001598 | 0.004409 | 0.007054 | 0.018757 | 0.017172 | -0.091832 |
| adjusted_preview_baseline | 1-3 | range | 1627 | -0.000207 | -0.000174 | 0.000005 | -0.001418 | 0.004703 | 0.031134 |
| adjusted_preview_baseline | 1-3 | up | 372 | 0.004222 | 0.010120 | 0.014973 | 0.026097 | 0.030140 | 0.080242 |
| adjusted_preview_baseline | 11-20 | down | 90 | 0.009070 | 0.008925 | 0.011837 | 0.021430 | 0.033732 | 0.117987 |
| adjusted_preview_baseline | 11-20 | range | 1710 | 0.000667 | 0.002930 | 0.005432 | 0.011935 | 0.020874 | 0.102134 |
| adjusted_preview_baseline | 11-20 | up | 560 | 0.001398 | 0.001710 | 0.002592 | 0.006268 | 0.007253 | 0.017865 |
| adjusted_preview_baseline | 21-39 | down | 171 | 0.014780 | 0.018638 | 0.024806 | 0.033469 | 0.039976 | -0.242174 |
| adjusted_preview_baseline | 21-39 | range | 3249 | -0.000300 | 0.001016 | 0.001851 | 0.004512 | 0.012220 | 0.122827 |
| adjusted_preview_baseline | 21-39 | up | 1064 | 0.000327 | 0.000149 | 0.000219 | -0.003795 | -0.006611 | 0.192654 |
| adjusted_preview_baseline | 4-10 | down | 63 | 0.003930 | 0.002178 | 0.004973 | 0.003632 | 0.011632 | 0.083786 |
| adjusted_preview_baseline | 4-10 | range | 1197 | 0.000499 | 0.003262 | 0.003915 | 0.009070 | 0.018742 | 0.071077 |
| adjusted_preview_baseline | 4-10 | up | 392 | 0.001270 | 0.001682 | 0.005895 | 0.013929 | 0.021115 | -0.012405 |
| original_ranking_baseline | 1-3 | down | 233 | 0.001597 | 0.004382 | 0.007005 | 0.018740 | 0.016872 | -0.092406 |
| original_ranking_baseline | 1-3 | range | 1627 | -0.000212 | -0.000301 | -0.000294 | -0.001882 | 0.004136 | 0.021625 |
| original_ranking_baseline | 1-3 | up | 372 | 0.004101 | 0.009505 | 0.014597 | 0.026241 | 0.029699 | 0.086401 |
| original_ranking_baseline | 11-20 | down | 90 | 0.008254 | 0.007827 | 0.010472 | 0.019069 | 0.030457 | 0.195545 |
| original_ranking_baseline | 11-20 | range | 1710 | 0.000629 | 0.002821 | 0.005268 | 0.011976 | 0.021344 | 0.121698 |
| original_ranking_baseline | 11-20 | up | 560 | 0.001410 | 0.001726 | 0.002860 | 0.006156 | 0.008186 | 0.041383 |
| original_ranking_baseline | 21-39 | down | 171 | 0.015210 | 0.019216 | 0.025524 | 0.034712 | 0.041699 | -0.228663 |
| original_ranking_baseline | 21-39 | range | 3249 | -0.000303 | 0.001088 | 0.001959 | 0.004566 | 0.012388 | 0.118003 |
| original_ranking_baseline | 21-39 | up | 1064 | 0.000350 | 0.000339 | 0.000365 | -0.003639 | -0.005975 | 0.195282 |
| original_ranking_baseline | 4-10 | down | 63 | 0.003931 | 0.002279 | 0.005153 | 0.003696 | 0.012742 | 0.085093 |
| original_ranking_baseline | 4-10 | range | 1197 | 0.000569 | 0.003395 | 0.004261 | 0.009495 | 0.018387 | 0.070919 |
| original_ranking_baseline | 4-10 | up | 392 | 0.001305 | 0.001724 | 0.005473 | 0.013530 | 0.018474 | -0.057349 |

## 诊断
- 若 1-3 桶未来收益没有明显高于 4-10/11-20，说明 Top3 信号优势不足。
- 若 adjusted 的 rank_score_corr_10d 更高，说明 preview 可能改善排序；否则收益改善可能来自偶然 ETF 替换。
- ranking 若无预测力，应先优化信号层，而不是增加复杂退出规则。
