# 退出规则离线研究报告

本报告只研究候选退出规则，不上线、不自动卖出、不修改仓位。

## 候选规则
| rule | 说明 | 建议定位 |
| --- | --- | --- |
| rank_score_decline_2d_proxy | 代理评分连续 2 天下滑 | REVIEW 研究候选 |
| rank_score_decline_3d_proxy | 代理评分连续 3 天下滑 | REDUCE 研究候选 |
| rank_score_below_70_proxy | 评分分位跌破 70% | 禁止加仓/复核 |
| top_decile_drop_proxy | 从强势分位掉出 | 热点退潮观察 |
| short_swing_buy_to_watch_proxy | 短周期由强转弱 | REVIEW |
| short_swing_buy_to_sell_proxy | 短周期转弱且跌破均线 | SELL 候选研究 |
| volume_heat_decay_proxy | 成交热度和动量同步衰减 | 主题热度衰减代理 |
| type_stop_loss_proxy | 按 ETF 类型默认止损阈值 | 硬风控研究候选 |

## 汇总统计
| etf_type | rule | event_count | win_rate_after_exit | avg_forward_return_10d | avg_forward_return_20d | max_drawdown_after_exit | profit_loss_ratio | false_exit_count | late_exit_count | evidence | suggestion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| bond_cash | rank_score_below_70_proxy | 2318 | 63.38% | 0.07% | 0.17% | -7.88% | 3.63 | 18 | 8 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_2d_proxy | 839 | 63.85% | 0.07% | 0.14% | -7.88% | 1.78 | 9 | 3 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_3d_proxy | 376 | 65.30% | 0.03% | 0.09% | -6.58% | 1.63 | 3 | 1 | evidence_supported | research_only_not_online |
| bond_cash | short_swing_buy_to_sell_proxy | 1 | 0.00% | -0.00% | -0.01% | -0.01% |  | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | short_swing_buy_to_watch_proxy | 6 | 30.00% | -0.41% | -0.53% | -5.15% | 0.73 | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | top_decile_drop_proxy | 163 | 55.14% | 0.09% | 0.14% | -3.64% | 3.02 | 1 | 0 | sample_limited | research_only_not_online |
| bond_cash | type_stop_loss_proxy | 181 | 50.31% | 0.16% | 0.50% | -6.58% | 0.98 | 9 | 2 | sample_limited | risk_control_candidate_requires_backtest |
| bond_cash | volume_heat_decay_proxy | 253 | 62.13% | 0.06% | 0.14% | -7.88% | 1.89 | 3 | 1 | evidence_supported | research_only_not_online |
| broad_index | rank_score_below_70_proxy | 4389 | 56.92% | 0.87% | 2.51% | -20.08% | 1.34 | 1057 | 804 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_2d_proxy | 1841 | 57.67% | 1.01% | 2.19% | -18.49% | 1.32 | 517 | 321 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_3d_proxy | 788 | 60.86% | 1.15% | 2.59% | -16.42% | 1.59 | 216 | 109 | evidence_supported | research_only_not_online |
| broad_index | short_swing_buy_to_sell_proxy | 32 | 30.00% | -0.24% | -2.18% | -11.63% | 2.16 | 6 | 17 | hypothesis_only | candidate_for_simulation_review |
| broad_index | short_swing_buy_to_watch_proxy | 424 | 58.03% | 1.70% | 3.24% | -14.70% | 2.32 | 138 | 60 | evidence_supported | research_only_not_online |
| broad_index | top_decile_drop_proxy | 273 | 62.45% | 1.86% | 4.17% | -13.98% | 2.81 | 95 | 25 | evidence_supported | research_only_not_online |
| broad_index | type_stop_loss_proxy | 585 | 86.69% | 3.37% | 6.23% | -18.67% | 2.65 | 269 | 102 | evidence_supported | risk_control_candidate_requires_backtest |
| broad_index | volume_heat_decay_proxy | 637 | 59.68% | 1.20% | 1.89% | -17.79% | 1.66 | 173 | 106 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_below_70_proxy | 3718 | 63.06% | 1.29% | 2.95% | -54.20% | 1.09 | 1289 | 619 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_2d_proxy | 1432 | 61.23% | 1.19% | 2.54% | -56.48% | 1.17 | 496 | 324 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_3d_proxy | 679 | 60.99% | 0.92% | 2.44% | -55.08% | 1.22 | 216 | 154 | evidence_supported | research_only_not_online |
| commodity_resource | short_swing_buy_to_sell_proxy | 55 | 56.80% | 1.19% | 3.09% | -48.60% | 0.93 | 20 | 19 | sample_limited | research_only_not_online |
| commodity_resource | short_swing_buy_to_watch_proxy | 402 | 59.09% | 1.93% | 3.51% | -55.08% | 2.16 | 157 | 86 | evidence_supported | research_only_not_online |
| commodity_resource | top_decile_drop_proxy | 268 | 57.09% | 1.58% | 3.34% | -56.48% | 1.74 | 98 | 40 | evidence_supported | research_only_not_online |
| commodity_resource | type_stop_loss_proxy | 1621 | 61.47% | 0.87% | 2.79% | -49.97% | 1.02 | 541 | 214 | evidence_supported | risk_control_candidate_requires_backtest |
| commodity_resource | volume_heat_decay_proxy | 457 | 66.83% | 1.87% | 3.16% | -22.26% | 1.65 | 162 | 63 | evidence_supported | research_only_not_online |
| high_beta | rank_score_below_70_proxy | 426 | 58.76% | 1.75% | 4.13% | -12.13% | 1.61 | 95 | 93 | evidence_supported | research_only_not_online |
| high_beta | rank_score_decline_2d_proxy | 172 | 60.76% | 1.23% | 1.18% | -67.85% | 0.69 | 45 | 46 | sample_limited | research_only_not_online |
| high_beta | rank_score_decline_3d_proxy | 82 | 63.11% | 3.61% | 3.44% | -14.05% | 1.16 | 22 | 17 | sample_limited | research_only_not_online |
| high_beta | short_swing_buy_to_sell_proxy | 5 | 0.00% | -3.22% | -0.10% | -7.54% |  | 0 | 2 | hypothesis_only | need_more_data |
| high_beta | short_swing_buy_to_watch_proxy | 38 | 56.39% | -0.48% | 1.36% | -67.82% | 0.77 | 9 | 7 | hypothesis_only | candidate_for_simulation_review |
| high_beta | top_decile_drop_proxy | 26 | 78.79% | 3.31% | 5.92% | -8.73% | 0.94 | 10 | 3 | hypothesis_only | need_more_data |
| high_beta | type_stop_loss_proxy | 254 | 56.74% | 1.27% | 2.50% | -11.06% | 1.58 | 55 | 55 | evidence_supported | risk_control_candidate_requires_backtest |
| high_beta | volume_heat_decay_proxy | 44 | 64.65% | 1.10% | 1.41% | -12.07% | 0.98 | 12 | 9 | sample_limited | research_only_not_online |
| qdii | rank_score_below_70_proxy | 2810 | 54.33% | 0.66% | 1.06% | -19.80% | 1.34 | 757 | 579 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_2d_proxy | 1164 | 55.46% | 1.00% | 1.59% | -21.22% | 1.40 | 344 | 273 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_3d_proxy | 576 | 58.16% | 1.60% | 2.30% | -19.72% | 1.67 | 189 | 115 | evidence_supported | research_only_not_online |
| qdii | short_swing_buy_to_sell_proxy | 8 | 50.00% | -3.53% | -1.05% | -19.32% |  | 1 | 5 | hypothesis_only | need_more_data |
| qdii | short_swing_buy_to_watch_proxy | 271 | 49.68% | 0.21% | 0.79% | -21.32% | 1.15 | 71 | 75 | evidence_supported | research_only_not_online |
| qdii | top_decile_drop_proxy | 151 | 52.36% | 0.84% | 1.05% | -16.91% | 1.53 | 29 | 31 | sample_limited | research_only_not_online |
| qdii | type_stop_loss_proxy | 870 | 62.55% | 1.43% | 3.56% | -19.64% | 1.11 | 265 | 287 | evidence_supported | risk_control_candidate_requires_backtest |
| qdii | volume_heat_decay_proxy | 351 | 57.25% | 0.92% | 1.96% | -19.71% | 1.32 | 101 | 66 | evidence_supported | research_only_not_online |
| sector | rank_score_below_70_proxy | 3702 | 46.13% | -0.27% | -0.44% | -17.50% | 0.96 | 451 | 521 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_2d_proxy | 1390 | 46.11% | -0.29% | -0.28% | -14.95% | 0.92 | 199 | 202 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_3d_proxy | 654 | 45.74% | -0.32% | -0.06% | -13.39% | 0.93 | 96 | 82 | evidence_supported | candidate_for_simulation_review |
| sector | short_swing_buy_to_sell_proxy | 7 | 30.00% | -5.67% | -3.10% | -13.42% | 1.58 | 2 | 5 | hypothesis_only | need_more_data |
| sector | short_swing_buy_to_watch_proxy | 172 | 44.54% | -0.20% | -0.04% | -15.36% | 1.21 | 30 | 32 | sample_limited | candidate_for_simulation_review |
| sector | top_decile_drop_proxy | 188 | 53.25% | -0.09% | -0.11% | -13.46% | 0.84 | 26 | 25 | sample_limited | candidate_for_simulation_review |
| sector | type_stop_loss_proxy | 756 | 60.30% | 0.39% | 1.38% | -14.95% | 1.10 | 111 | 98 | evidence_supported | risk_control_candidate_requires_backtest |
| sector | volume_heat_decay_proxy | 401 | 42.55% | -0.49% | -0.61% | -14.36% | 0.90 | 48 | 57 | evidence_supported | candidate_for_simulation_review |
| theme | rank_score_below_70_proxy | 3184 | 51.50% | 0.52% | 1.79% | -56.72% | 1.19 | 941 | 907 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_2d_proxy | 1336 | 55.54% | 0.87% | 1.97% | -63.07% | 1.17 | 469 | 386 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_3d_proxy | 632 | 57.08% | 0.98% | 2.12% | -56.05% | 1.26 | 232 | 158 | evidence_supported | research_only_not_online |
| theme | short_swing_buy_to_sell_proxy | 39 | 27.38% | -2.15% | -0.41% | -23.21% | 1.37 | 7 | 15 | hypothesis_only | candidate_for_simulation_review |
| theme | short_swing_buy_to_watch_proxy | 307 | 51.36% | 0.88% | 4.15% | -63.07% | 1.39 | 114 | 94 | evidence_supported | research_only_not_online |
| theme | top_decile_drop_proxy | 221 | 70.43% | 3.98% | 7.41% | -17.63% | 2.77 | 116 | 33 | evidence_supported | research_only_not_online |
| theme | type_stop_loss_proxy | 2086 | 52.68% | 0.54% | 1.70% | -56.07% | 1.09 | 584 | 594 | evidence_supported | risk_control_candidate_requires_backtest |
| theme | volume_heat_decay_proxy | 476 | 52.77% | 0.62% | 1.49% | -55.04% | 1.21 | 150 | 159 | evidence_supported | research_only_not_online |
| unknown | rank_score_below_70_proxy | 13595 | 58.37% | 1.05% | 2.49% | -29.50% | 1.41 | 3455 | 1969 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_2d_proxy | 5691 | 57.29% | 0.82% | 1.93% | -65.71% | 1.17 | 1495 | 1086 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_3d_proxy | 2721 | 56.13% | 0.71% | 1.93% | -52.74% | 1.19 | 696 | 498 | evidence_supported | research_only_not_online |
| unknown | short_swing_buy_to_sell_proxy | 125 | 40.38% | -1.89% | -1.25% | -23.01% | 2.16 | 25 | 44 | sample_limited | candidate_for_simulation_review |
| unknown | short_swing_buy_to_watch_proxy | 1084 | 54.51% | 1.16% | 3.03% | -65.71% | 1.66 | 352 | 225 | evidence_supported | research_only_not_online |
| unknown | top_decile_drop_proxy | 939 | 61.19% | 1.89% | 2.78% | -51.69% | 2.39 | 305 | 137 | evidence_supported | research_only_not_online |
| unknown | type_stop_loss_proxy | 4491 | 66.59% | 1.62% | 3.49% | -53.93% | 1.72 | 1489 | 953 | evidence_supported | risk_control_candidate_requires_backtest |
| unknown | volume_heat_decay_proxy | 1907 | 62.04% | 1.43% | 2.46% | -53.52% | 1.83 | 535 | 295 | evidence_supported | research_only_not_online |

## 研究结论边界
- 单日评分下降不能直接卖出，容易被震荡噪声误伤。
- short_swing 转弱更适合作为 REVIEW/禁止加仓，而不是立即 SELL。
- 类型化止损、连续下降和热度衰减需要后续回测验证后才能进入执行层。
- 本报告不修改 sell_signal_review.py 的当前复核逻辑，也不写交易流水。