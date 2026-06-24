# Top10 候选池过滤分析 2026-06-19 00:51:29

本分析只针对 `top10_diversified_filter_v2`，用于判断 Top10 候选池 + 二次筛选是否比机械 Top3 更稳定。

## 过滤统计
- Top10 记录数：2550
- 最终入选记录数：325
- data_health：本轮为历史回测，无法逐日重建历史 data_health；当前交易池已在回测前排除低质量/低流动性/QDII/unknown 标的，历史逐日 data_health 只记录为未触发。
- filter_reason 分布：
| filter_reason | count |
| --- | --- |
| trend_confirmation | 1809 |
| selected | 304 |
| not_selected_lower_priority | 169 |
| already_held | 161 |
| liquidity_trading_constraint | 56 |
| selected_relaxed_group | 21 |
| cooldown | 15 |
| group_concentration | 13 |
| high_beta_exposure | 2 |

## 与 original_baseline_v2 对比
- top10 total_return：11.31%
- top10 max_drawdown：-4.86%
- top10 turnover：11.2300
- original total_return：1.64%
- original max_drawdown：-9.63%
- original turnover：14.4183

## 判断
- top10_diversified_effective：`true`
- 当前定位：低回撤、低换手、组合结构更健康的候选模型，不是收益优秀或 alpha 已验证策略。
- 由于未跑赢 510300 buy-and-hold，只允许进入 shadow tracking，不允许接入执行层。
- 如果收益改善但换手/回撤没有改善，应进入影子跟踪而不是执行层。
- 如果回撤下降但收益不足，可作为风险过滤层继续研究。
- 本轮不把 Top10 diversified 接入 paper_trade_engine。
