# TopN Selection Diagnostics 2026-06-18 20:28:13

## 10 日 TopN 对比
| selection_method | horizon | sample_count | avg_forward_return | median_forward_return | volatility | max_drawdown_proxy | positive_ratio | comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Top1 | 10 | 997 | 0.004641 | -0.004130 | 0.058980 | -0.984688 | 0.468405 | research_only |
| Top10 diversified | 10 | 997 | 0.003917 | -0.004199 | 0.052538 | -0.988241 | 0.467402 | candidate_pool_research |
| Top3 | 10 | 997 | 0.003785 | -0.004607 | 0.052648 | -0.988241 | 0.466399 | concentrated_and_noisy |
| Top5 | 10 | 997 | 0.003331 | -0.003884 | 0.051203 | -0.988241 | 0.471414 | research_only |
| Top10 | 10 | 997 | 0.002922 | -0.003951 | 0.049643 | -0.988241 | 0.467402 | candidate_pool_research |
| Top10 risk-filtered | 10 | 997 | 0.002854 | 0.000130 | 0.048954 | -0.988241 | 0.503511 | candidate_pool_research |

## 结论
- 如果 Top3 不稳定优于 Top10，应改成 Top10 candidate + 二次风险/分散筛选。
- Top10 risk-filtered 和 diversified 只作为研究方案，不接入执行层。
