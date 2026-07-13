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
| 1 | 10 | 20 | 5 | 260 | 58.05% | 36.37% | -25.17% | 1.60 | 42.60% | sample_limited | candidate_for_deeper_backtest |
| 2 | 10 | 40 | 5 | 260 | 40.78% | 36.07% | -28.47% | 1.13 | 43.24% | sample_limited | candidate_for_deeper_backtest |
| 3 | 40 | 10 | 5 | 260 | 47.60% | 42.37% | -28.43% | 1.12 | 27.99% | sample_limited | candidate_for_deeper_backtest |
| 4 | 10 | 20 | 3 | 260 | 44.73% | 41.08% | -30.54% | 1.09 | 44.36% | sample_limited | candidate_for_deeper_backtest |
| 5 | 10 | 40 | 3 | 260 | 42.49% | 40.83% | -30.73% | 1.04 | 46.83% | sample_limited | candidate_for_deeper_backtest |
| 6 | 10 | 10 | 3 | 260 | 42.45% | 41.01% | -31.02% | 1.04 | 45.71% | sample_limited | candidate_for_deeper_backtest |
| 7 | 40 | 20 | 5 | 260 | 41.80% | 42.57% | -28.43% | 0.98 | 27.93% | sample_limited | candidate_for_deeper_backtest |
| 8 | 40 | 40 | 5 | 260 | 41.44% | 42.58% | -28.43% | 0.97 | 27.73% | sample_limited | candidate_for_deeper_backtest |
| 9 | 10 | 40 | 8 | 260 | 31.60% | 32.62% | -23.31% | 0.97 | 40.55% | sample_limited | candidate_for_deeper_backtest |
| 10 | 10 | 10 | 5 | 260 | 35.03% | 38.69% | -36.31% | 0.91 | 43.03% | sample_limited | candidate_for_deeper_backtest |
| 11 | 40 | 40 | 8 | 260 | 30.68% | 37.19% | -26.16% | 0.82 | 25.93% | sample_limited | candidate_for_deeper_backtest |
| 12 | 40 | 20 | 8 | 260 | 30.64% | 37.18% | -26.16% | 0.82 | 26.85% | sample_limited | candidate_for_deeper_backtest |

## 解释边界
- 使用价格动量和波动惩罚代理，不等于当前正式 BUY ranking。
- 未纳入交易成本、流动性冲击、新闻情绪和 QDII 溢价。
- 结果只能作为 Main/GPT 评估参数方向的输入，不能直接上线。