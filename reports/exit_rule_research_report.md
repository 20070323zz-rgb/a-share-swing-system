# 退出规则离线研究报告

本报告只研究候选退出规则，不上线、不自动卖出、不修改仓位。

## 候选规则说明
| 规则 | 逻辑 | 适用 ETF 类型 | 优点 | 风险 |
| --- | --- | --- | --- | --- |
| A1 rank_score 连续 2 天下滑 | proxy_score 连续 2 天下滑 | 行业/主题/宽基 | 更早识别走弱 | 易被震荡噪声误伤 |
| A2 rank_score 连续 3 天下滑 | proxy_score 连续 3 天下滑 | 行业/主题 | 减少短噪声 | 可能退出偏晚 |
| A3 rank_score 跌破 70 | proxy_score 分位跌破 70% | 全部 ETF | 简单清晰 | proxy 与真实 rank_score 不完全一致 |
| A4 Top3 跌出 Top10 | ETF 内 proxy top3 转非 top10 | 强势轮动 | 适合热点退潮 | 需要横截面真实历史排名 |
| B1 short_swing BUY 转 WATCH | 5 日动量从强转弱 | 主题/行业 | 与短周期风险匹配 | 可能错过中期趋势 |
| B2 short_swing BUY 转 SELL | 5 日动量转负且跌破 ma10 | 主题/行业 | 风险更明确 | 触发较晚 |
| C 类型化止损 | 按 ETF 类型设不同止损 | 全部 ETF | 匹配波动差异 | 阈值需回测验证 |
| D 热度衰减代理 | 成交量下降 + proxy_score 下降 | 主题 ETF | 无新闻数据时可代理热度 | 不能替代真实新闻情绪 |

## 离线统计汇总
| etf_type | rule | event_count | avg_next_10d | negative_next_10d_rate | evidence | suggestion |
| --- | --- | ---: | ---: | ---: | --- | --- |
| bond_cash | rank_drop_top3_to_out_top10_proxy | 25 | 0.26% | 37.86% | hypothesis_only | 需要更多数据 |
| bond_cash | rank_score_below_70_proxy | 1878 | 0.08% | 27.68% | evidence_supported | 暂不建议上线 |
| bond_cash | rank_score_decline_2d | 706 | 0.08% | 28.88% | evidence_supported | 暂不建议上线 |
| bond_cash | rank_score_decline_3d | 325 | 0.04% | 32.49% | evidence_supported | 暂不建议上线 |
| bond_cash | short_swing_buy_to_sell_proxy | 0 |  |  | hypothesis_only | 需要更多数据 |
| bond_cash | short_swing_buy_to_watch_proxy | 6 | -0.41% | 70.00% | hypothesis_only | 需要更多数据 |
| bond_cash | type_stop_loss_proxy_low_vol_or_none | 159 | 0.27% | 42.03% | sample_limited | 暂不建议上线 |
| bond_cash | volume_and_rank_decay_proxy | 96 | 0.04% | 32.68% | sample_limited | 暂不建议上线 |
| broad_index | rank_drop_top3_to_out_top10_proxy | 21 | 1.59% | 27.56% | hypothesis_only | 需要更多数据 |
| broad_index | rank_score_below_70_proxy | 3552 | 0.76% | 41.62% | evidence_supported | 暂不建议上线 |
| broad_index | rank_score_decline_2d | 1458 | 0.88% | 41.38% | evidence_supported | 暂不建议上线 |
| broad_index | rank_score_decline_3d | 623 | 1.12% | 37.20% | evidence_supported | 暂不建议上线 |
| broad_index | short_swing_buy_to_sell_proxy | 15 | -0.45% | 77.14% | hypothesis_only | 需要更多数据 |
| broad_index | short_swing_buy_to_watch_proxy | 314 | 1.33% | 41.72% | evidence_supported | 暂不建议上线 |
| broad_index | type_stop_loss_proxy_7%-10% | 622 | 2.84% | 11.79% | evidence_supported | 暂不建议上线 |
| broad_index | volume_and_rank_decay_proxy | 211 | 0.39% | 40.44% | evidence_supported | 暂不建议上线 |
| commodity_resource | rank_drop_top3_to_out_top10_proxy | 45 | 2.36% | 35.10% | sample_limited | 暂不建议上线 |
| commodity_resource | rank_score_below_70_proxy | 3655 | 1.39% | 35.12% | evidence_supported | 暂不建议上线 |
| commodity_resource | rank_score_decline_2d | 1429 | 1.26% | 36.82% | evidence_supported | 暂不建议上线 |
| commodity_resource | rank_score_decline_3d | 678 | 0.94% | 37.43% | evidence_supported | 暂不建议上线 |
| commodity_resource | short_swing_buy_to_sell_proxy | 55 | 1.54% | 40.45% | sample_limited | 暂不建议上线 |
| commodity_resource | short_swing_buy_to_watch_proxy | 402 | 1.98% | 38.33% | evidence_supported | 暂不建议上线 |
| commodity_resource | type_stop_loss_proxy_5%-8% | 1936 | 0.98% | 37.03% | evidence_supported | 暂不建议上线 |
| commodity_resource | volume_and_rank_decay_proxy | 230 | 2.00% | 29.14% | evidence_supported | 暂不建议上线 |
| hot_theme | rank_drop_top3_to_out_top10_proxy | 4 | 0.36% | 50.00% | hypothesis_only | 需要更多数据 |
| hot_theme | rank_score_below_70_proxy | 333 | 0.85% | 44.80% | evidence_supported | 暂不建议上线 |
| hot_theme | rank_score_decline_2d | 159 | 0.71% | 46.00% | sample_limited | 暂不建议上线 |
| hot_theme | rank_score_decline_3d | 82 | 1.11% | 44.59% | sample_limited | 暂不建议上线 |
| hot_theme | short_swing_buy_to_sell_proxy | 2 | 2.93% | 0.00% | hypothesis_only | 需要更多数据 |
| hot_theme | short_swing_buy_to_watch_proxy | 41 | 1.52% | 36.67% | sample_limited | 暂不建议上线 |
| hot_theme | type_stop_loss_proxy_3%-5% | 309 | 0.14% | 49.31% | evidence_supported | 暂不建议上线 |
| hot_theme | volume_and_rank_decay_proxy | 26 | -1.88% | 66.43% | hypothesis_only | 需要更多数据 |
| qdii | rank_drop_top3_to_out_top10_proxy | 19 | -1.53% | 61.36% | hypothesis_only | 需要更多数据 |
| qdii | rank_score_below_70_proxy | 2766 | 0.70% | 44.50% | evidence_supported | 暂不建议上线 |
| qdii | rank_score_decline_2d | 1153 | 1.05% | 43.34% | evidence_supported | 暂不建议上线 |
| qdii | rank_score_decline_3d | 572 | 1.60% | 41.38% | evidence_supported | 暂不建议上线 |
| qdii | short_swing_buy_to_sell_proxy | 8 | -3.53% | 50.00% | hypothesis_only | 需要更多数据 |
| qdii | short_swing_buy_to_watch_proxy | 271 | 0.24% | 49.00% | evidence_supported | 暂不建议上线 |
| qdii | type_stop_loss_proxy_price+premium+fx | 1050 | 1.16% | 39.95% | evidence_supported | 暂不建议上线 |
| qdii | volume_and_rank_decay_proxy | 158 | 1.71% | 33.09% | sample_limited | 暂不建议上线 |
| sector | rank_drop_top3_to_out_top10_proxy | 32 | -1.14% | 62.50% | hypothesis_only | 需要更多数据 |
| sector | rank_score_below_70_proxy | 4073 | 0.02% | 50.80% | evidence_supported | 暂不建议上线 |
| sector | rank_score_decline_2d | 1560 | -0.07% | 50.28% | evidence_supported | 可进入模拟观察 |
| sector | rank_score_decline_3d | 735 | 0.24% | 50.40% | evidence_supported | 暂不建议上线 |
| sector | short_swing_buy_to_sell_proxy | 11 | -4.75% | 81.25% | hypothesis_only | 需要更多数据 |
| sector | short_swing_buy_to_watch_proxy | 210 | -0.24% | 51.07% | evidence_supported | 可进入模拟观察 |
| sector | type_stop_loss_proxy_5%-8% | 1393 | 0.60% | 40.26% | evidence_supported | 暂不建议上线 |
| sector | volume_and_rank_decay_proxy | 213 | -0.04% | 52.28% | evidence_supported | 可进入模拟观察 |
| theme | rank_drop_top3_to_out_top10_proxy | 20 | 7.00% | 31.67% | hypothesis_only | 需要更多数据 |
| theme | rank_score_below_70_proxy | 2797 | 0.56% | 47.78% | evidence_supported | 暂不建议上线 |
| theme | rank_score_decline_2d | 1168 | 1.04% | 42.65% | evidence_supported | 暂不建议上线 |
| theme | rank_score_decline_3d | 548 | 1.15% | 40.88% | evidence_supported | 暂不建议上线 |
| theme | short_swing_buy_to_sell_proxy | 37 | -2.53% | 78.57% | hypothesis_only | 需要更多数据 |
| theme | short_swing_buy_to_watch_proxy | 264 | 0.87% | 48.80% | evidence_supported | 暂不建议上线 |
| theme | type_stop_loss_proxy_4%-6% | 2188 | 0.35% | 47.76% | evidence_supported | 暂不建议上线 |
| theme | volume_and_rank_decay_proxy | 199 | 0.88% | 39.40% | sample_limited | 暂不建议上线 |
| unknown | rank_drop_top3_to_out_top10_proxy | 5 | 5.52% | 0.00% | hypothesis_only | 需要更多数据 |
| unknown | rank_score_below_70_proxy | 1463 | 1.31% | 43.43% | evidence_supported | 暂不建议上线 |
| unknown | rank_score_decline_2d | 661 | 1.53% | 40.12% | evidence_supported | 暂不建议上线 |
| unknown | rank_score_decline_3d | 295 | 1.26% | 39.35% | evidence_supported | 暂不建议上线 |
| unknown | short_swing_buy_to_sell_proxy | 26 | 0.57% | 76.39% | hypothesis_only | 需要更多数据 |
| unknown | short_swing_buy_to_watch_proxy | 160 | 2.69% | 36.70% | sample_limited | 暂不建议上线 |
| unknown | type_stop_loss_proxy_manual_review | 596 | 2.11% | 37.98% | evidence_supported | 暂不建议上线 |
| unknown | volume_and_rank_decay_proxy | 113 | 1.82% | 32.97% | sample_limited | 暂不建议上线 |

## 是否建议进入模拟观察
- rank_score 连续下降：建议进入模拟观察，但必须使用真实历史 rank_score 后再评估。
- short_swing 转弱：建议先用于 REVIEW/禁止加仓，不直接自动卖出。
- 类型化止损：建议进入离线回测，不建议直接上线。
- 热度衰减：在新闻数据未接入前只能作为代理研究，不建议上线。

## 不建议上线项
- 任何未经过样本验证的主题 ETF 自动减仓规则。
- 新闻/热度直接触发 BUY 或 SELL。
- 对当前模拟持仓自动卖出或自动改仓。

## 数据限制
- 当前 rank_score 没有完整历史序列，本报告使用 proxy_score 代替。
- short_swing 转弱用 5 日收益和 ma10 的代理定义。
- 热度衰减使用成交量和 proxy_score 代理，不能替代真实新闻情绪。
- 所有结论为 research/simulation 层，不进入 live paper trade execution。