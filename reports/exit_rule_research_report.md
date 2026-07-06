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
| bond_cash | rank_score_below_70_proxy | 2458 | 63.22% | 0.06% | 0.15% | -7.88% | 3.58 | 18 | 8 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_2d_proxy | 870 | 62.68% | 0.07% | 0.12% | -7.88% | 1.70 | 9 | 3 | evidence_supported | research_only_not_online |
| bond_cash | rank_score_decline_3d_proxy | 385 | 64.27% | 0.03% | 0.08% | -6.58% | 1.56 | 3 | 1 | evidence_supported | research_only_not_online |
| bond_cash | short_swing_buy_to_sell_proxy | 1 | 0.00% | -0.00% | -0.01% | -0.01% |  | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | short_swing_buy_to_watch_proxy | 6 | 30.00% | -0.41% | -0.53% | -5.15% | 0.73 | 0 | 0 | hypothesis_only | need_more_data |
| bond_cash | top_decile_drop_proxy | 167 | 52.50% | 0.09% | 0.12% | -3.64% | 3.16 | 1 | 0 | sample_limited | research_only_not_online |
| bond_cash | type_stop_loss_proxy | 185 | 51.01% | 0.17% | 0.40% | -6.58% | 0.96 | 9 | 2 | sample_limited | risk_control_candidate_requires_backtest |
| bond_cash | volume_heat_decay_proxy | 263 | 61.18% | 0.06% | 0.13% | -7.88% | 1.86 | 3 | 1 | evidence_supported | research_only_not_online |
| broad_index | rank_score_below_70_proxy | 4591 | 60.17% | 1.34% | 2.63% | -42.81% | 1.47 | 1245 | 817 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_2d_proxy | 1875 | 60.58% | 1.37% | 2.45% | -42.81% | 1.41 | 578 | 338 | evidence_supported | research_only_not_online |
| broad_index | rank_score_decline_3d_proxy | 791 | 64.77% | 1.73% | 2.75% | -40.56% | 1.87 | 260 | 118 | evidence_supported | research_only_not_online |
| broad_index | short_swing_buy_to_sell_proxy | 42 | 30.00% | -0.40% | 1.33% | -41.87% | 2.16 | 6 | 20 | sample_limited | candidate_for_simulation_review |
| broad_index | short_swing_buy_to_watch_proxy | 453 | 59.61% | 1.68% | 3.18% | -43.33% | 2.30 | 144 | 67 | evidence_supported | research_only_not_online |
| broad_index | top_decile_drop_proxy | 285 | 62.55% | 1.85% | 4.16% | -13.98% | 2.79 | 95 | 27 | evidence_supported | research_only_not_online |
| broad_index | type_stop_loss_proxy | 601 | 87.80% | 3.73% | 6.44% | -39.94% | 2.96 | 303 | 107 | evidence_supported | risk_control_candidate_requires_backtest |
| broad_index | volume_heat_decay_proxy | 644 | 62.58% | 1.68% | 1.98% | -17.79% | 1.85 | 199 | 108 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_below_70_proxy | 4002 | 62.21% | 1.22% | 2.37% | -54.20% | 1.05 | 1366 | 836 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_2d_proxy | 1493 | 60.45% | 1.10% | 2.15% | -56.48% | 1.13 | 515 | 384 | evidence_supported | research_only_not_online |
| commodity_resource | rank_score_decline_3d_proxy | 706 | 60.07% | 0.84% | 1.84% | -55.08% | 1.16 | 226 | 191 | evidence_supported | research_only_not_online |
| commodity_resource | short_swing_buy_to_sell_proxy | 66 | 56.80% | 1.28% | 3.14% | -48.60% | 0.93 | 21 | 22 | sample_limited | research_only_not_online |
| commodity_resource | short_swing_buy_to_watch_proxy | 411 | 58.84% | 1.83% | 3.48% | -55.08% | 2.09 | 157 | 88 | evidence_supported | research_only_not_online |
| commodity_resource | top_decile_drop_proxy | 269 | 56.89% | 1.53% | 3.34% | -56.48% | 1.71 | 98 | 40 | evidence_supported | research_only_not_online |
| commodity_resource | type_stop_loss_proxy | 1787 | 60.60% | 0.83% | 1.69% | -53.21% | 0.96 | 610 | 387 | evidence_supported | risk_control_candidate_requires_backtest |
| commodity_resource | volume_heat_decay_proxy | 481 | 65.83% | 1.77% | 2.69% | -22.26% | 1.50 | 170 | 84 | evidence_supported | research_only_not_online |
| high_beta | rank_score_below_70_proxy | 437 | 61.48% | 2.21% | 4.84% | -12.13% | 1.82 | 118 | 93 | evidence_supported | research_only_not_online |
| high_beta | rank_score_decline_2d_proxy | 183 | 64.37% | 2.10% | 2.62% | -67.85% | 0.77 | 58 | 46 | sample_limited | research_only_not_online |
| high_beta | rank_score_decline_3d_proxy | 84 | 66.15% | 4.08% | 4.84% | -14.05% | 1.38 | 28 | 17 | sample_limited | research_only_not_online |
| high_beta | short_swing_buy_to_sell_proxy | 6 | 22.22% | -0.07% | 0.72% | -7.54% | 10.01 | 2 | 2 | hypothesis_only | need_more_data |
| high_beta | short_swing_buy_to_watch_proxy | 44 | 55.05% | -0.31% | 1.69% | -67.82% | 0.87 | 10 | 7 | sample_limited | candidate_for_simulation_review |
| high_beta | top_decile_drop_proxy | 30 | 80.05% | 3.46% | 4.17% | -8.73% | 1.07 | 12 | 4 | hypothesis_only | research_only_not_online |
| high_beta | type_stop_loss_proxy | 259 | 60.43% | 1.89% | 3.29% | -11.06% | 1.77 | 72 | 55 | evidence_supported | risk_control_candidate_requires_backtest |
| high_beta | volume_heat_decay_proxy | 45 | 68.12% | 1.62% | 2.06% | -12.07% | 1.08 | 15 | 9 | sample_limited | research_only_not_online |
| qdii | rank_score_below_70_proxy | 2980 | 53.06% | 0.51% | 0.78% | -19.80% | 1.29 | 781 | 671 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_2d_proxy | 1213 | 53.79% | 0.77% | 1.36% | -21.22% | 1.36 | 353 | 317 | evidence_supported | research_only_not_online |
| qdii | rank_score_decline_3d_proxy | 598 | 55.64% | 1.23% | 2.10% | -19.72% | 1.61 | 195 | 136 | evidence_supported | research_only_not_online |
| qdii | short_swing_buy_to_sell_proxy | 10 | 50.00% | -3.53% | -1.05% | -19.32% |  | 1 | 5 | hypothesis_only | need_more_data |
| qdii | short_swing_buy_to_watch_proxy | 275 | 49.15% | 0.18% | 0.57% | -21.32% | 1.15 | 73 | 80 | evidence_supported | research_only_not_online |
| qdii | top_decile_drop_proxy | 155 | 49.96% | 0.68% | 0.75% | -16.91% | 1.64 | 31 | 36 | sample_limited | research_only_not_online |
| qdii | type_stop_loss_proxy | 988 | 59.95% | 1.07% | 3.28% | -19.64% | 1.10 | 282 | 329 | evidence_supported | risk_control_candidate_requires_backtest |
| qdii | volume_heat_decay_proxy | 373 | 55.17% | 0.62% | 1.59% | -19.71% | 1.25 | 102 | 76 | evidence_supported | research_only_not_online |
| sector | rank_score_below_70_proxy | 3933 | 44.19% | -0.46% | -0.82% | -17.50% | 0.87 | 475 | 682 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_2d_proxy | 1463 | 43.63% | -0.50% | -0.55% | -14.95% | 0.86 | 202 | 258 | evidence_supported | candidate_for_simulation_review |
| sector | rank_score_decline_3d_proxy | 690 | 42.65% | -0.60% | -0.33% | -13.39% | 0.86 | 96 | 112 | evidence_supported | candidate_for_simulation_review |
| sector | short_swing_buy_to_sell_proxy | 8 | 30.00% | -5.67% | -3.10% | -13.42% | 1.58 | 2 | 5 | hypothesis_only | need_more_data |
| sector | short_swing_buy_to_watch_proxy | 181 | 42.92% | -0.36% | -0.04% | -15.36% | 1.04 | 30 | 32 | sample_limited | candidate_for_simulation_review |
| sector | top_decile_drop_proxy | 192 | 52.33% | -0.14% | -0.14% | -13.46% | 0.82 | 26 | 26 | sample_limited | candidate_for_simulation_review |
| sector | type_stop_loss_proxy | 904 | 49.39% | -0.26% | -0.14% | -15.10% | 1.08 | 129 | 204 | evidence_supported | candidate_for_simulation_review |
| sector | volume_heat_decay_proxy | 414 | 40.80% | -0.64% | -0.81% | -14.36% | 0.88 | 50 | 72 | evidence_supported | candidate_for_simulation_review |
| theme | rank_score_below_70_proxy | 3345 | 53.18% | 1.09% | 1.84% | -56.72% | 1.36 | 1075 | 1027 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_2d_proxy | 1364 | 56.33% | 1.08% | 2.35% | -63.07% | 1.22 | 501 | 439 | evidence_supported | research_only_not_online |
| theme | rank_score_decline_3d_proxy | 636 | 57.75% | 1.07% | 2.76% | -56.05% | 1.27 | 246 | 182 | evidence_supported | research_only_not_online |
| theme | short_swing_buy_to_sell_proxy | 46 | 27.78% | -2.09% | 3.62% | -23.21% | 1.38 | 8 | 19 | sample_limited | candidate_for_simulation_review |
| theme | short_swing_buy_to_watch_proxy | 325 | 53.01% | 1.29% | 4.16% | -63.07% | 1.50 | 122 | 102 | evidence_supported | research_only_not_online |
| theme | top_decile_drop_proxy | 227 | 70.43% | 3.98% | 7.42% | -17.63% | 2.77 | 116 | 42 | evidence_supported | research_only_not_online |
| theme | type_stop_loss_proxy | 2190 | 55.14% | 1.30% | 1.89% | -56.07% | 1.31 | 704 | 711 | evidence_supported | risk_control_candidate_requires_backtest |
| theme | volume_heat_decay_proxy | 483 | 54.36% | 1.06% | 1.48% | -55.04% | 1.42 | 162 | 173 | evidence_supported | research_only_not_online |
| unknown | rank_score_below_70_proxy | 14437 | 57.77% | 1.11% | 2.27% | -67.22% | 1.33 | 3732 | 2449 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_2d_proxy | 5907 | 56.76% | 0.79% | 1.92% | -67.76% | 1.14 | 1561 | 1285 | evidence_supported | research_only_not_online |
| unknown | rank_score_decline_3d_proxy | 2830 | 55.58% | 0.67% | 2.11% | -66.52% | 1.16 | 729 | 603 | evidence_supported | research_only_not_online |
| unknown | short_swing_buy_to_sell_proxy | 145 | 40.13% | -1.45% | 0.19% | -66.42% | 2.04 | 27 | 55 | sample_limited | candidate_for_simulation_review |
| unknown | short_swing_buy_to_watch_proxy | 1111 | 53.99% | 1.06% | 2.79% | -66.93% | 1.63 | 355 | 244 | evidence_supported | research_only_not_online |
| unknown | top_decile_drop_proxy | 967 | 60.71% | 1.85% | 2.71% | -66.52% | 2.37 | 306 | 160 | evidence_supported | research_only_not_online |
| unknown | type_stop_loss_proxy | 4988 | 61.87% | 1.39% | 3.25% | -65.97% | 1.30 | 1672 | 1217 | evidence_supported | risk_control_candidate_requires_backtest |
| unknown | volume_heat_decay_proxy | 1980 | 61.55% | 1.41% | 2.39% | -53.52% | 1.77 | 558 | 331 | evidence_supported | research_only_not_online |

## 研究结论边界
- 单日评分下降不能直接卖出，容易被震荡噪声误伤。
- short_swing 转弱更适合作为 REVIEW/禁止加仓，而不是立即 SELL。
- 类型化止损、连续下降和热度衰减需要后续回测验证后才能进入执行层。
- 本报告不修改 sell_signal_review.py 的当前复核逻辑，也不写交易流水。