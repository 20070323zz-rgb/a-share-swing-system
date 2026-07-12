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
| bond_cash | rank_score_below_70_proxy | 2499 | 63.32% | 0.06% | 0.15% | -7.88% | 3.58 | 18 | 8 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_2d_proxy | 876 | 62.70% | 0.06% | 0.12% | -7.88% | 1.68 | 9 | 3 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_3d_proxy | 385 | 64.56% | 0.03% | 0.08% | -6.58% | 1.56 | 3 | 1 | evidence_supported | research_only_not_online |
| bond_cash | short_swing_buy_to_sell_proxy | 1 | 0.00% | -0.00% | -0.01% | -0.01% |  | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | short_swing_buy_to_watch_proxy | 6 | 30.00% | -0.41% | -0.53% | -5.15% | 0.73 | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | top_decile_drop_proxy | 172 | 52.67% | 0.09% | 0.12% | -3.64% | 3.15 | 1 | 0 | sample_limited | research_only_not_online |
| bond_cash | type_stop_loss_proxy | 187 | 50.95% | 0.17% | 0.39% | -6.58% | 0.96 | 9 | 2 | sample_limited | risk_control_candidate_requires_backtest |
| bond_cash | volume_heat_decay_proxy | 266 | 61.18% | 0.05% | 0.12% | -7.88% | 1.87 | 3 | 1 | evidence_supported | research_only_not_online |
| broad_index | rank_score_below_70_proxy | 4659 | 59.52% | 1.28% | 2.70% | -43.51% | 1.44 | 1247 | 821 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_2d_proxy | 1888 | 60.32% | 1.31% | 2.54% | -42.81% | 1.37 | 578 | 340 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_3d_proxy | 797 | 64.69% | 1.72% | 2.89% | -40.56% | 1.87 | 260 | 119 | evidence_supported | research_only_not_online |
| broad_index | short_swing_buy_to_sell_proxy | 42 | 27.05% | -0.53% | 1.33% | -41.87% | 2.15 | 6 | 20 | sample_limited | candidate_for_simulation_review |
| broad_index | short_swing_buy_to_watch_proxy | 453 | 57.77% | 1.58% | 3.09% | -43.33% | 2.07 | 144 | 68 | evidence_supported | research_only_not_online |
| broad_index | top_decile_drop_proxy | 285 | 61.84% | 1.81% | 4.16% | -13.98% | 2.44 | 95 | 27 | evidence_supported | research_only_not_online |
| broad_index | type_stop_loss_proxy | 625 | 87.73% | 3.72% | 6.46% | -40.27% | 2.95 | 303 | 108 | evidence_supported | risk_control_candidate_requires_backtest |
| broad_index | volume_heat_decay_proxy | 647 | 62.31% | 1.66% | 2.20% | -41.42% | 1.85 | 199 | 110 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_below_70_proxy | 4081 | 61.31% | 1.08% | 2.28% | -54.20% | 1.02 | 1376 | 862 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_2d_proxy | 1515 | 60.20% | 1.04% | 2.06% | -56.48% | 1.10 | 517 | 394 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_3d_proxy | 718 | 60.07% | 0.81% | 1.71% | -55.08% | 1.14 | 227 | 198 | evidence_supported | research_only_not_online |
| commodity_resource | short_swing_buy_to_sell_proxy | 67 | 43.78% | 0.21% | 3.26% | -48.60% | 0.93 | 21 | 22 | sample_limited | research_only_not_online |
| commodity_resource | short_swing_buy_to_watch_proxy | 418 | 58.12% | 1.75% | 3.36% | -55.08% | 2.04 | 157 | 90 | evidence_supported | research_only_not_online |
| commodity_resource | top_decile_drop_proxy | 270 | 56.89% | 1.53% | 3.28% | -56.48% | 1.71 | 98 | 41 | evidence_supported | research_only_not_online |
| commodity_resource | type_stop_loss_proxy | 1852 | 60.33% | 0.78% | 1.54% | -53.21% | 0.95 | 620 | 410 | evidence_supported | risk_control_candidate_requires_backtest |
| commodity_resource | volume_heat_decay_proxy | 485 | 65.93% | 1.72% | 2.56% | -22.26% | 1.43 | 171 | 87 | evidence_supported | research_only_not_online |
| high_beta | rank_score_below_70_proxy | 441 | 60.87% | 1.64% | 2.88% | -55.34% | 1.04 | 118 | 96 | evidence_supported | research_only_not_online |
| high_beta | rank_score_decline_2d_proxy | 185 | 62.70% | 0.93% | 0.27% | -67.85% | 0.77 | 58 | 48 | sample_limited | research_only_not_online |
| high_beta | rank_score_decline_3d_proxy | 84 | 66.15% | 4.08% | 1.48% | -52.72% | 1.38 | 28 | 18 | sample_limited | research_only_not_online |
| high_beta | short_swing_buy_to_sell_proxy | 7 | 22.22% | -0.07% | -6.53% | -53.56% | 10.01 | 2 | 3 | hypothesis_only | need_more_data |
| high_beta | short_swing_buy_to_watch_proxy | 45 | 52.83% | -0.34% | 1.69% | -67.82% | 0.90 | 10 | 7 | sample_limited | candidate_for_simulation_review |
| high_beta | top_decile_drop_proxy | 32 | 71.89% | -0.93% | 4.17% | -8.73% | 0.76 | 12 | 4 | hypothesis_only | candidate_for_simulation_review |
| high_beta | type_stop_loss_proxy | 264 | 60.43% | 1.89% | 2.17% | -53.56% | 1.77 | 72 | 57 | evidence_supported | risk_control_candidate_requires_backtest |
| high_beta | volume_heat_decay_proxy | 47 | 45.41% | -18.11% | 2.51% | -12.07% | 1.08 | 15 | 9 | sample_limited | candidate_for_simulation_review |
| qdii | rank_score_below_70_proxy | 3017 | 53.32% | 0.57% | 0.78% | -19.80% | 1.31 | 804 | 699 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_2d_proxy | 1218 | 53.99% | 0.80% | 1.32% | -21.22% | 1.36 | 358 | 336 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_3d_proxy | 599 | 55.97% | 1.24% | 1.96% | -19.72% | 1.62 | 196 | 155 | evidence_supported | research_only_not_online |
| qdii | short_swing_buy_to_sell_proxy | 10 | 37.50% | -2.71% | -1.05% | -19.32% |  | 1 | 5 | hypothesis_only | need_more_data |
| qdii | short_swing_buy_to_watch_proxy | 281 | 48.92% | 0.17% | 0.59% | -21.32% | 1.17 | 73 | 80 | evidence_supported | research_only_not_online |
| qdii | top_decile_drop_proxy | 156 | 49.41% | 0.65% | 0.76% | -16.91% | 1.66 | 31 | 36 | sample_limited | research_only_not_online |
| qdii | type_stop_loss_proxy | 999 | 58.87% | 1.03% | 3.15% | -19.64% | 2.56 | 304 | 345 | evidence_supported | risk_control_candidate_requires_backtest |
| qdii | volume_heat_decay_proxy | 374 | 54.79% | 0.59% | 1.42% | -19.71% | 1.22 | 103 | 86 | evidence_supported | research_only_not_online |
| sector | rank_score_below_70_proxy | 3987 | 44.37% | -0.44% | -0.86% | -17.50% | 0.87 | 484 | 717 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_2d_proxy | 1486 | 44.11% | -0.49% | -0.62% | -14.95% | 0.85 | 203 | 273 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_3d_proxy | 700 | 42.75% | -0.60% | -0.44% | -13.39% | 0.85 | 96 | 125 | evidence_supported | candidate_for_simulation_review |
| sector | short_swing_buy_to_sell_proxy | 9 | 30.00% | -5.67% | -3.10% | -13.42% | 1.58 | 2 | 5 | hypothesis_only | need_more_data |
| sector | short_swing_buy_to_watch_proxy | 192 | 43.08% | -0.36% | -0.11% | -15.36% | 1.03 | 30 | 33 | sample_limited | candidate_for_simulation_review |
| sector | top_decile_drop_proxy | 195 | 52.33% | -0.14% | -0.14% | -13.46% | 0.82 | 26 | 26 | sample_limited | candidate_for_simulation_review |
| sector | type_stop_loss_proxy | 932 | 54.47% | -0.03% | -0.17% | -15.10% | 1.04 | 132 | 227 | evidence_supported | candidate_for_simulation_review |
| sector | volume_heat_decay_proxy | 423 | 40.91% | -0.64% | -0.93% | -14.36% | 0.88 | 50 | 83 | evidence_supported | candidate_for_simulation_review |
| theme | rank_score_below_70_proxy | 3384 | 53.07% | 1.04% | 1.83% | -56.72% | 1.33 | 1089 | 1054 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_2d_proxy | 1380 | 56.06% | 1.02% | 2.29% | -63.07% | 1.20 | 501 | 444 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_3d_proxy | 643 | 57.75% | 1.07% | 2.75% | -56.05% | 1.27 | 246 | 184 | evidence_supported | research_only_not_online |
| theme | short_swing_buy_to_sell_proxy | 52 | 27.78% | -2.09% | 3.62% | -23.21% | 1.38 | 8 | 19 | sample_limited | candidate_for_simulation_review |
| theme | short_swing_buy_to_watch_proxy | 326 | 52.32% | 1.24% | 4.10% | -63.07% | 1.51 | 122 | 102 | evidence_supported | research_only_not_online |
| theme | top_decile_drop_proxy | 227 | 70.06% | 3.90% | 7.42% | -17.63% | 2.66 | 116 | 42 | evidence_supported | research_only_not_online |
| theme | type_stop_loss_proxy | 2236 | 55.02% | 1.30% | 1.92% | -56.07% | 1.31 | 706 | 731 | evidence_supported | risk_control_candidate_requires_backtest |
| theme | volume_heat_decay_proxy | 483 | 54.36% | 1.06% | 1.51% | -55.04% | 1.42 | 162 | 175 | evidence_supported | research_only_not_online |
| unknown | rank_score_below_70_proxy | 14694 | 57.27% | 1.06% | 2.24% | -67.80% | 1.30 | 3748 | 2578 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_2d_proxy | 5968 | 56.37% | 0.74% | 1.88% | -67.76% | 1.13 | 1563 | 1346 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_3d_proxy | 2855 | 55.23% | 0.64% | 1.98% | -66.52% | 1.16 | 730 | 655 | evidence_supported | research_only_not_online |
| unknown | short_swing_buy_to_sell_proxy | 147 | 39.05% | -1.44% | 0.47% | -66.42% | 2.05 | 28 | 56 | sample_limited | candidate_for_simulation_review |
| unknown | short_swing_buy_to_watch_proxy | 1132 | 53.20% | 1.00% | 2.73% | -66.93% | 1.59 | 355 | 247 | evidence_supported | research_only_not_online |
| unknown | top_decile_drop_proxy | 971 | 60.19% | 1.82% | 2.71% | -66.52% | 1.82 | 306 | 160 | evidence_supported | research_only_not_online |
| unknown | type_stop_loss_proxy | 5164 | 60.26% | 1.25% | 3.06% | -65.97% | 1.28 | 1683 | 1298 | evidence_supported | risk_control_candidate_requires_backtest |
| unknown | volume_heat_decay_proxy | 1998 | 60.90% | 1.31% | 2.39% | -53.52% | 1.72 | 558 | 350 | evidence_supported | research_only_not_online |

## 研究结论边界
- 单日评分下降不能直接卖出，容易被震荡噪声误伤。
- short_swing 转弱更适合作为 REVIEW/禁止加仓，而不是立即 SELL。
- 类型化止损、连续下降和热度衰减需要后续回测验证后才能进入执行层。
- 本报告不修改 sell_signal_review.py 的当前复核逻辑，也不写交易流水。