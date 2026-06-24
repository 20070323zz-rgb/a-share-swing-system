# 参数扫描研究报告

本报告为 phase2_model_research_v1 研究层，不修改 BUY ranking、不改仓位规则、不写模拟交易。

## 扫描空间
- momentum_windows：[10, 20, 40, 60]
- volatility_windows：[10, 20, 40]
- max_holdings：[1, 3, 5, 8]
- 最近样本天数上限：260

## Top 参数组合
| rank | momentum_window | volatility_window | max_holdings | sample_days | annual_return | annual_volatility | max_drawdown | sharpe_proxy | turnover_proxy | evidence | suggestion |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 10 | 20 | 5 | 260 | 50.92% | 33.42% | -24.95% | 1.52 | 42.59% | sample_limited | candidate_for_deeper_backtest |
| 2 | 10 | 10 | 5 | 260 | 50.86% | 33.45% | -25.89% | 1.52 | 43.22% | sample_limited | candidate_for_deeper_backtest |
| 3 | 10 | 10 | 8 | 260 | 43.51% | 30.41% | -24.01% | 1.43 | 40.60% | sample_limited | candidate_for_deeper_backtest |
| 4 | 20 | 40 | 1 | 260 | 61.07% | 43.34% | -27.97% | 1.41 | 36.29% | sample_limited | candidate_for_deeper_backtest |
| 5 | 10 | 40 | 8 | 260 | 41.80% | 30.47% | -23.30% | 1.37 | 40.36% | sample_limited | candidate_for_deeper_backtest |
| 6 | 20 | 20 | 8 | 260 | 41.35% | 32.58% | -19.24% | 1.27 | 32.12% | sample_limited | candidate_for_deeper_backtest |
| 7 | 20 | 40 | 8 | 260 | 41.16% | 32.64% | -18.20% | 1.26 | 31.68% | sample_limited | candidate_for_deeper_backtest |
| 8 | 20 | 20 | 1 | 260 | 52.98% | 43.74% | -26.62% | 1.21 | 36.29% | sample_limited | candidate_for_deeper_backtest |
| 9 | 10 | 20 | 8 | 260 | 36.72% | 30.50% | -24.04% | 1.20 | 40.94% | sample_limited | candidate_for_deeper_backtest |
| 10 | 20 | 20 | 3 | 260 | 45.66% | 38.63% | -25.04% | 1.18 | 38.07% | sample_limited | candidate_for_deeper_backtest |
| 11 | 40 | 40 | 8 | 260 | 37.70% | 32.23% | -19.10% | 1.17 | 27.16% | sample_limited | candidate_for_deeper_backtest |
| 12 | 40 | 20 | 8 | 260 | 36.66% | 32.22% | -18.87% | 1.14 | 28.02% | sample_limited | candidate_for_deeper_backtest |

## 解释边界
- 使用价格动量和波动惩罚代理，不等于当前正式 BUY ranking。
- 未纳入交易成本、流动性冲击、新闻情绪和 QDII 溢价。
- 结果只能作为 Main/GPT 评估参数方向的输入，不能直接上线。