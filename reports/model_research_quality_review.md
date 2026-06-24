# Phase 2B 模型研究结果质量审查

本报告只做研究质量审查，不修改 paper_trade_engine，不修改模拟持仓，不新增交易记录。

## 总结结论
- holding_period_research：MEDIUM，可作为 ETF 类型化持有期的研究依据，但不应直接强制卖出。
- exit_rule_research：LOW_MEDIUM，规则可复现，但未纳入成本/滑点，暂不建议改执行引擎。
- parameter_sweep：LOW_MEDIUM，最多持仓数量比较不完整，第一阶段继续保持最多 3 只。
- market_state：MEDIUM，当前 market_neutral / 51.72，建议先展示，不自动控仓。
- ETF 分类：MEDIUM，unknown 75/185，当前三只持仓分类合理。
- 组合暴露：MEDIUM，当前 CAUTION，提示缺少宽基和 515880 data_health caution。

## 未来函数与样本审查
- holding_period/exit_rule 中的 forward return 使用 `shift(-window)`，这是离线评估所需，不得进入当天信号或执行层。
- market_state、classification、portfolio_exposure 不使用未来收益。
- parameter_sweep 使用 next_return 做离线代理回测，未纳入交易成本、100 份单位和现金约束。

## holding_period_research 审查
| etf_type | total_sample | proxy_buy_sample | best_window | best_signal | best_avg_return | best_r/dd | execution_ready |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| bond_cash | 49000 | 8295 | 60 | proxy_buy | 0.37% | 9.34 | True |
| broad_index | 100284 | 17651 | 60 | proxy_buy | 22.38% | 1.73 | True |
| commodity_resource | 90440 | 17804 | 45 | proxy_buy | 15.12% | 1.22 | True |
| high_beta | 8217 | 1068 | 20 | proxy_buy | 3.08% | 0.32 | True |
| qdii | 58094 | 9144 | 45 | proxy_buy | 11.23% | 0.65 | True |
| sector | 64530 | 7947 | 30 | proxy_buy | 2.60% | 0.30 | True |
| theme | 69470 | 10995 | 20 | proxy_buy | 7.98% | 0.56 | True |
| unknown | 306152 | 53742 | 60 | proxy_buy | 27.12% | 1.83 | True |

- 结论：可将 etf_type 对应 max_holding_days 作为研究性配置候选，但建议先以 dashboard/复核提示展示，不直接强制卖出。
- 不确定性：新增 ETF 历史较短，proxy_buy 信号不是正式 BUY ranking 历史，样本存在截面扩容后的幸存者偏差。

## exit_rule_research 审查
| rule | event_count | avg_forward_10d | max_drawdown_after_exit | false_exit | late_exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| short_swing_buy_to_sell_proxy | 272 | -1.52% | -48.60% | 61 | 107 |
| rank_score_decline_2d_proxy | 13865 | 0.75% | -67.85% | 3574 | 2641 |
| rank_score_decline_3d_proxy | 6508 | 0.78% | -56.05% | 1670 | 1134 |
| rank_score_below_70_proxy | 34142 | 0.78% | -56.72% | 8063 | 5500 |
| short_swing_buy_to_watch_proxy | 2704 | 1.01% | -67.82% | 871 | 579 |
| volume_heat_decay_proxy | 4526 | 1.03% | -55.04% | 1184 | 756 |
| type_stop_loss_proxy | 10844 | 1.47% | -56.07% | 3323 | 2305 |
| top_decile_drop_proxy | 2229 | 1.67% | -56.48% | 680 | 294 |
| all_rules | 0 |  |  | 0 | 0 |

- REDUCE 连续 2 日卖出支持：False
- short_swing SELL：insufficient as direct SELL; usable as REVIEW/SELL candidate filter only
- rank_score 连续下降：rank_score_decline_3d_proxy is more stable than 2d, but still proxy-only
- 止损规则：type_stop_loss_proxy is useful for hard-risk research, but thresholds need cost-aware replay before execution
- 是否建议修改 paper_trade_engine：否。暂不建议修改 paper_trade_engine；可先把 short_swing SELL、类型化止损、连续降分作为 sell_signal_review 的复核输入。

## parameter_sweep 审查
| max_holdings | configs | sample_days | best_sharpe | median_sharpe | best_max_drawdown | median_turnover |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 260 | 1.41 | -0.32 | -26.62% | 32.43% |
| 3 | 12 | 260 | 1.18 | 0.41 | -25.04% | 36.43% |
| 5 | 12 | 260 | 1.52 | 0.75 | -22.51% | 33.83% |
| 8 | 12 | 260 | 1.43 | 1.15 | -18.20% | 29.85% |

- max_holdings 是否可比：partially; same proxy universe but no costs, lot size, cash, position caps, or execution constraints
- 当前最多 3 只：继续保持。理由：第一阶段继续最多 3 只；5 只只作为后续成本约束回测候选。

## market_state 审查
- 当前状态：market_neutral，score=51.72，组件数量=10。
- 是否过度依赖单一指标：False。
- 是否建议接入仓位：先只展示；如接入，增加 `PAPER_USE_MARKET_STATE_POSITION = False`。

## ETF 分类与组合暴露审查
- unknown ETF：75/185（40.54%）。
- 当前持仓分类合理：True。
- 组合暴露状态：CAUTION。
- 组合暴露提示：组合暂无宽基 ETF，波动可能更依赖行业/主题轮动。; 515880 data_health=提醒，需保留复核标签。

## 可信结论
- etf_type 适合进入风控和研究提示层。
- market_state 适合展示和人工复核。
- portfolio_exposure 适合做风险提示、禁止盲目同向加仓的辅助信息。

## 不可信或暂不足以执行的结论
- parameter_sweep 不能证明 5/8 只优于 3 只，因为未纳入真实交易约束。
- exit_rule 中任何连续 2 日下降直接卖出都证据不足。
- 新闻情绪、机器学习主策略、动态持仓数量暂不应接入执行层。

## 安全边界
- 未接券商 API，未真实下单，未读取真实账户。
- 未修改 paper_trades.csv / paper_positions.csv。
- 未改变第一阶段模拟买卖闭环。