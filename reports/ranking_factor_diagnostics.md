# Ranking Factor Diagnostics 2026-06-18 20:28:05

仅使用 39 只 backtest_trade_pool，不扩池。

## 10 日预测力较强因子
| factor | horizon | rank_ic | rank_ic_mean | rank_ic_std | rank_ic_ir | top_quantile_return | bottom_quantile_return | spread | positive_ic_ratio | market_state | etf_type | stability_score | comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| momentum_20d | 10 | 0.138789 | 0.138789 | 0.374867 | 0.370236 | 0.015923 | -0.000930 | 0.016854 | 0.680851 | all | all | 0.094495 | positive_candidate |
| relative_strength_vs_510300 | 10 | 0.138789 | 0.138789 | 0.374867 | 0.370236 | 0.015923 | -0.000930 | 0.016854 | 0.680851 | all | all | 0.094495 | positive_candidate |
| trend_slope_20 | 10 | 0.133210 | 0.133210 | 0.376074 | 0.354213 | 0.015709 | -0.000602 | 0.016311 | 0.672340 | all | all | 0.089563 | positive_candidate |
| ma_distance_20 | 10 | 0.125563 | 0.125563 | 0.347581 | 0.361249 | 0.013445 | 0.000656 | 0.012789 | 0.676596 | all | all | 0.084956 | positive_candidate |
| risk_adjusted_momentum | 10 | 0.116620 | 0.116620 | 0.355082 | 0.328432 | 0.010638 | -0.000614 | 0.011252 | 0.655319 | all | all | 0.076423 | positive_candidate |
| ma_distance_60 | 10 | 0.114845 | 0.114845 | 0.367687 | 0.312345 | 0.014372 | 0.001621 | 0.012752 | 0.689362 | all | all | 0.079170 | positive_candidate |
| momentum_10d | 10 | 0.093997 | 0.093997 | 0.327402 | 0.287098 | 0.012971 | 0.003884 | 0.009087 | 0.625532 | all | all | 0.058798 | positive_candidate |
| volatility_20 | 10 | 0.092519 | 0.092519 | 0.396309 | 0.233452 | 0.015006 | 0.000067 | 0.014939 | 0.608511 | all | all | 0.056299 | positive_candidate |
| atr_pct | 10 | 0.086080 | 0.086080 | 0.400073 | 0.215161 | 0.014048 | 0.000471 | 0.013577 | 0.595745 | all | all | 0.051282 | positive_candidate |
| volatility_60 | 10 | 0.078606 | 0.078606 | 0.394473 | 0.199269 | 0.012960 | 0.000117 | 0.012843 | 0.600000 | all | all | 0.047164 | positive_candidate |
| momentum_60d | 10 | 0.069879 | 0.069879 | 0.362875 | 0.192571 | 0.012870 | 0.004688 | 0.008182 | 0.604255 | all | all | 0.042225 | positive_candidate |
| trend_slope_60 | 10 | 0.059936 | 0.059936 | 0.357679 | 0.167570 | 0.013846 | 0.006045 | 0.007801 | 0.610619 | all | all | 0.036598 | positive_candidate |
| momentum_5d | 10 | 0.046684 | 0.046684 | 0.368476 | 0.126695 | 0.011477 | 0.005212 | 0.006265 | 0.600000 | all | all | 0.028010 | positive_candidate |
| relative_strength_vs_group | 10 | 0.045976 | 0.045976 | 0.255334 | 0.180062 | 0.013084 | 0.005649 | 0.007435 | 0.629787 | all | all | 0.028955 | positive_candidate |
| drawdown_20 | 10 | 0.029690 | 0.029690 | 0.341206 | 0.087014 | 0.008169 | 0.005918 | 0.002251 | 0.557447 | all | all | 0.016551 | weak_or_context_dependent |

## 10 日负向/噪音因子
| factor | horizon | rank_ic | rank_ic_mean | rank_ic_std | rank_ic_ir | top_quantile_return | bottom_quantile_return | spread | positive_ic_ratio | market_state | etf_type | stability_score | comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| volume_ratio_20 | 10 | 0.007170 | 0.007170 | 0.201465 | 0.035591 | 0.007682 | 0.006512 | 0.001170 | 0.523404 | all | all | 0.003753 | weak_or_context_dependent |
| amount_liquidity_20 | 10 | 0.019290 | 0.019290 | 0.212107 | 0.090942 | 0.003789 | 0.007386 | -0.003597 | 0.553191 | all | all | 0.010671 | likely_trading_constraint_more_than_alpha |
| amount_liquidity_60 | 10 | 0.021963 | 0.021963 | 0.214838 | 0.102233 | 0.002417 | 0.007772 | -0.005355 | 0.544681 | all | all | 0.011963 | likely_trading_constraint_more_than_alpha |
| drawdown_60 | 10 | 0.023275 | 0.023275 | 0.346833 | 0.067108 | 0.006989 | 0.007949 | -0.000960 | 0.531915 | all | all | 0.012380 | weak_or_context_dependent |
| drawdown_20 | 10 | 0.029690 | 0.029690 | 0.341206 | 0.087014 | 0.008169 | 0.005918 | 0.002251 | 0.557447 | all | all | 0.016551 | weak_or_context_dependent |
| relative_strength_vs_group | 10 | 0.045976 | 0.045976 | 0.255334 | 0.180062 | 0.013084 | 0.005649 | 0.007435 | 0.629787 | all | all | 0.028955 | positive_candidate |
| momentum_5d | 10 | 0.046684 | 0.046684 | 0.368476 | 0.126695 | 0.011477 | 0.005212 | 0.006265 | 0.600000 | all | all | 0.028010 | positive_candidate |
| trend_slope_60 | 10 | 0.059936 | 0.059936 | 0.357679 | 0.167570 | 0.013846 | 0.006045 | 0.007801 | 0.610619 | all | all | 0.036598 | positive_candidate |
| momentum_60d | 10 | 0.069879 | 0.069879 | 0.362875 | 0.192571 | 0.012870 | 0.004688 | 0.008182 | 0.604255 | all | all | 0.042225 | positive_candidate |
| volatility_60 | 10 | 0.078606 | 0.078606 | 0.394473 | 0.199269 | 0.012960 | 0.000117 | 0.012843 | 0.600000 | all | all | 0.047164 | positive_candidate |
| atr_pct | 10 | 0.086080 | 0.086080 | 0.400073 | 0.215161 | 0.014048 | 0.000471 | 0.013577 | 0.595745 | all | all | 0.051282 | positive_candidate |
| volatility_20 | 10 | 0.092519 | 0.092519 | 0.396309 | 0.233452 | 0.015006 | 0.000067 | 0.014939 | 0.608511 | all | all | 0.056299 | positive_candidate |
| momentum_10d | 10 | 0.093997 | 0.093997 | 0.327402 | 0.287098 | 0.012971 | 0.003884 | 0.009087 | 0.625532 | all | all | 0.058798 | positive_candidate |
| ma_distance_60 | 10 | 0.114845 | 0.114845 | 0.367687 | 0.312345 | 0.014372 | 0.001621 | 0.012752 | 0.689362 | all | all | 0.079170 | positive_candidate |
| risk_adjusted_momentum | 10 | 0.116620 | 0.116620 | 0.355082 | 0.328432 | 0.010638 | -0.000614 | 0.011252 | 0.655319 | all | all | 0.076423 | positive_candidate |

## 结论
- 单因子 IC 普遍不强，说明 Top3 不稳定不是单靠执行规则能解决。
- 流动性更适合作为交易约束，不宜作为收益预测主因子。
- 相对强弱、风险调整动量、趋势确认应进入 Phase 4B-1 候选回测。
