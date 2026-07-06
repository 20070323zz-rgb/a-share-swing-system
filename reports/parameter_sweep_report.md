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
| 1 | 10 | 20 | 5 | 260 | 66.47% | 35.73% | -24.95% | 1.86 | 42.70% | sample_limited | candidate_for_deeper_backtest |
| 2 | 10 | 10 | 5 | 260 | 65.66% | 35.74% | -25.89% | 1.84 | 43.24% | sample_limited | candidate_for_deeper_backtest |
| 3 | 10 | 10 | 8 | 260 | 43.84% | 32.32% | -24.01% | 1.36 | 40.01% | sample_limited | candidate_for_deeper_backtest |
| 4 | 10 | 40 | 5 | 260 | 47.78% | 35.44% | -28.36% | 1.35 | 43.35% | sample_limited | candidate_for_deeper_backtest |
| 5 | 10 | 20 | 3 | 260 | 50.07% | 40.52% | -30.25% | 1.24 | 45.02% | sample_limited | candidate_for_deeper_backtest |
| 6 | 10 | 40 | 8 | 260 | 39.58% | 32.34% | -23.30% | 1.22 | 39.91% | sample_limited | candidate_for_deeper_backtest |
| 7 | 10 | 10 | 3 | 260 | 48.29% | 40.35% | -30.73% | 1.20 | 45.56% | sample_limited | candidate_for_deeper_backtest |
| 8 | 10 | 40 | 3 | 260 | 48.02% | 40.13% | -30.44% | 1.20 | 47.26% | sample_limited | candidate_for_deeper_backtest |
| 9 | 40 | 40 | 8 | 260 | 39.47% | 35.28% | -19.10% | 1.12 | 25.53% | sample_limited | candidate_for_deeper_backtest |
| 10 | 40 | 10 | 5 | 260 | 44.85% | 40.49% | -22.51% | 1.11 | 30.17% | sample_limited | candidate_for_deeper_backtest |
| 11 | 40 | 20 | 8 | 260 | 38.33% | 35.27% | -18.87% | 1.09 | 26.38% | sample_limited | candidate_for_deeper_backtest |
| 12 | 10 | 20 | 8 | 260 | 34.79% | 32.38% | -24.04% | 1.07 | 40.65% | sample_limited | candidate_for_deeper_backtest |

## 解释边界
- 使用价格动量和波动惩罚代理，不等于当前正式 BUY ranking。
- 未纳入交易成本、流动性冲击、新闻情绪和 QDII 溢价。
- 结果只能作为 Main/GPT 评估参数方向的输入，不能直接上线。