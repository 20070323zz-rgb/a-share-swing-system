# ChatGPT 分析用：当前报告摘要（截至 2026-06-26）

生成时间：2026-06-27 23:34:46

> 本摘要只用于把当前 A 股 ETF 双周期模拟盘状态交给 ChatGPT / Main 做研究分析，不是交易指令。项目安全边界：不接券商 API、不真实下单、不读取真实账户、不保存密码/token。

## 1. 数据与系统状态
- ETF 正式数据文件：183 个；总日线行数：59994。
- 最新数据日分布：{'2026-06-26': 183}。
- 最近一次数据更新：2026-06-26 21:59:26，状态 OK / updated，新增 183 行，失败 0，BaoStock 调用 183 次。
- dashboard 快照：2026-06-26 22:00:36，latest_data_date=2026-06-26。
- 数据健康：正常 72 / 提醒 4 / 异常 0 / 缺失 2（缺失主要为个股观察，不属于 ETF 主数据下载范围）。

## 2. 当前信号结论
- mid_trend：BUY 7 / WATCH 56 / SELL 0 / RISK 0。
- short_swing：BUY 7 / WATCH 56 / SELL 0 / RISK 0。
- 双周期强共振：159915 创业板ETF、588000 科创50ETF、512880 证券ETF、515000 科技ETF、159819 人工智能ETF、515070 AIETF。
- 短期试探：515050 5GETF。
- RISK_ALERT：无。

## 3. BUY Ranking 与增强预览
| 原排名 | 代码 | 名称 | 组别 | 原分 | 调整后排名 | 调整后分 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 512880 | 证券ETF | 金融地产 | 94.77 | 2 | 90.77 | preview_only_not_executed |
| 2 | 515000 | 科技ETF | 科技成长 | 91.95 | 4 | 89.95 | preview_only_not_executed |
| 3 | 588000 | 科创50ETF | 宽基 | 90.32 | 1 | 93.32 | preview_only_not_executed |
| 4 | 159915 | 创业板ETF | 宽基 | 87.76 | 3 | 90.76 | preview_only_not_executed |
| 5 | 515070 | AIETF | 科技成长 | 86.83 | 5 | 84.83 | preview_only_not_executed |
| 6 | 159819 | 人工智能ETF | 科技成长 | 86.82 | 6 | 84.82 | preview_only_not_executed |
| 7 | 515880 | 证券公司ETF | 金融地产 | 74.16 | 7 | 67.16 | preview_only_not_executed |
| 8 | 515050 | 5GETF | 科技成长 | 71.95 | 8 | 66.95 | preview_only_not_executed |

解读：原始排名偏向证券/科技/科创；增强预览因组合缺少宽基，给 588000、159915 加分，同时对已持有金融/科技同组和 high_beta 做降权。当前增强预览仍是 preview_only_not_executed，不接正式执行层。

## 4. 模拟盘账户与持仓
- 当前现金：7,058.11 元。
- 当前持仓市值：3,008.10 元。
- 当前总资产：10,066.21 元。
- 总盈亏：66.21 元，总收益率 0.66%。
- 已实现盈亏：-73.59 元；未实现盈亏：206.50 元。
- 最大回撤：-1.03%；交易次数 7；胜率 50.00%。

## 5. 卖出复核状态
| 代码 | 名称 | 类型 | mid/short | 状态 | 动作 |
| --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | BUY/WATCH | REVIEW | 触发人工复核条件；不自动卖出，dashboard 标黄。 |
| 515000 | 科技ETF | unknown | BUY/BUY | HOLD | mid_trend / short_swing 和风控未触发退出条件，继续持有。 |
| 512880 | 证券ETF | high_beta | BUY/BUY | HOLD | 保护期内未触发硬风控，继续持有。 |

重点：512800 银行ETF 为 REVIEW，原因包括 short_swing 从 BUY 转 WATCH、浮亏超过阈值、rank 连续下降。515000 科技ETF与512880证券ETF为 HOLD。

## 6. 组合风险与数据口径注意
- 组合当前仍偏行业/主题，缺少宽基 ETF。组合暴露模块给出 CAUTION。
- 515880、512760、515050、516780 有 data_health 提醒（历史极端涨跌幅提示），当前并非严重异常。
- 数据口径复核点：portfolio_exposure 持仓市值 3074.80 vs paper_performance 持仓市值 3008.10，差异 66.70；建议后续检查 exposure 是否使用了最新 close 或旧 position 快照。

## 7. Shadow / 研究模型状态
- 当前阶段：Shadow Observation Period。
- 正式模型状态：LOCKED / unchanged。
- shadow_to_execution：disabled；execution_enabled=false；real_trade_enabled=false。
- persistence_breakout_v2 最新信号日：2026-06-26，selected_symbols=['510300']，ready_for_execution=False。
- Shadow weekly evidence_level=insufficient，ready_for_preview=False，ready_for_execution=False，recommended_action=continue_observation。

## 8. 建议交给 ChatGPT 判断的问题
1. 当前 BUY ranking 是否过度集中在证券、科技、科创，是否需要更强的组合均衡约束？
2. 512800 银行ETF目前 REVIEW，是否应保持观察、触发减仓候选，还是等待 mid_trend 破坏再处理？
3. 515000 科技ETF浮盈较大，是否需要设计移动止盈或分批止盈的研究规则？
4. 512880 证券ETF属于 high_beta，虽然 HOLD，但组合已有金融地产暴露，是否应限制继续加仓同组 ETF？
5. persistence_breakout_v2 只选出 510300，是否说明模型过于保守，还是当前市场适合保守？
6. portfolio_exposure 与 paper_performance 的估值差异是否需要优先修复，以免看板风险判断失真？

## 9. 禁止误读
- 以上不是实盘建议，不应真实下单。
- shadow 模型不能接入执行层。
- 当前盈利主要包含未实现浮盈，不能证明策略已经稳定盈利。


---

# ChatGPT 分析用：本周报告摘要（2026-06-22 至 2026-06-26）

生成时间：2026-06-27 23:34:46

> 本周摘要用于复盘 A 股 ETF 双周期模拟盘与研究模型，不是交易指令。所有交易均为本地模拟盘记录。

## 1. 本周数据状态
- 本周最后数据日：2026-06-26。
- 183 只 ETF 全部更新至 2026-06-26；本周最后一次更新新增 183 行，失败 0。
- 数据健康：正常 72 / 提醒 4 / 异常 0 / 缺失 2。

## 2. 本周模拟盘权益变化
- 周初权益：10,080.05 元；周末权益：10,066.21 元。
- 本周权益变化：-13.84 元；本周收益率：-0.14%。
- 本周最高权益：10,132.91 元；本周最低权益：10,031.41 元。
- 截至周末总收益率：0.66%，总盈亏：66.21 元。
- 已实现盈亏仍为负：-73.59 元；当前正收益主要来自未实现浮盈：206.50 元。

## 3. 本周模拟交易
| 日期 | 代码 | 名称 | 动作 | 数量 | 价格 | 金额 | 原因 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-23 | 515880 | 证券公司ETF | SELL | 300 | 1.8584 | 557.53 | REDUCE two consecutive days |
| 2026-06-23 | 512880 | 证券ETF | BUY | 500 | 1.1313 | 565.67 | paper_rule_validation; rank=1; rank_score=91.306916; mid_trend=BUY; short_swing= |

本周要点：6月23日卖出 515880 证券公司ETF并实现盈利，同时买入 512880 证券ETF。没有真实交易。

## 4. 周末持仓与复核状态
| 代码 | 名称 | 类型 | mid/short | 状态 | 动作 |
| --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | BUY/WATCH | REVIEW | 触发人工复核条件；不自动卖出，dashboard 标黄。 |
| 515000 | 科技ETF | unknown | BUY/BUY | HOLD | mid_trend / short_swing 和风控未触发退出条件，继续持有。 |
| 512880 | 证券ETF | high_beta | BUY/BUY | HOLD | 保护期内未触发硬风控，继续持有。 |

周末重点：512800 银行ETF进入 REVIEW；515000 科技ETF和512880证券ETF仍为 HOLD。当前组合仍以科技成长、金融地产为主，缺少宽基平衡。

## 5. 本周信号结构变化
- 周末 mid_trend BUY 7、short_swing BUY 7，强共振 6 个。
- 强共振集中在创业板、科创50、证券、科技、AI/人工智能。
- BUY ranking 原始 Top3：512880 证券ETF、515000 科技ETF、588000 科创50ETF。
- 调整预览 Top3：588000 科创50ETF、512880 证券ETF、159915 创业板ETF，体现出宽基平衡倾向。

## 6. 本周轻量回测 / 相对强弱观察
### 20/60/120 日滚动表现 Top
| 代码 | 名称 | 20日收益 | 60日收益 | 120日收益 | 20日回撤 |
| --- | --- | --- | --- | --- | --- |
| 515000 | 科技ETF | 14.59% | 66.23% | 63.07% | -7.98% |
| 515050 | 5GETF | 10.40% | -42.22% | -39.68% | -7.66% |
| 588000 | 科创50ETF | 9.84% | 55.69% | 51.28% | -13.34% |
| 515880 | 证券公司ETF | 8.52% | 64.36% | -44.10% | -7.69% |
| 512880 | 证券ETF | 8.42% | 6.34% | -8.29% | -3.66% |
| 159819 | 人工智能ETF | 1.86% | 41.17% | 37.52% | -9.26% |

### weekly_full_backtest mid_trend Top
| 代码 | 名称 | 策略 | 收益 | 回撤 | 胜率 | 交易数 |
| --- | --- | --- | --- | --- | --- | --- |
| 159915 | 创业板ETF | mid_trend | 17.18% | -6.68% | 40.00% | 10 |
| 516780 | 稀土ETF | mid_trend | 11.15% | -3.20% | 60.00% | 5 |
| 159819 | 人工智能ETF | mid_trend | 9.84% | -5.00% | 66.67% | 6 |
| 515000 | 科技ETF | mid_trend | 8.72% | -9.11% | 20.00% | 20 |
| 515070 | AIETF | mid_trend | 4.47% | -4.70% | 60.00% | 5 |

解读：科技ETF、创业板ETF等在历史片段中表现较强，但样本和参数仍需防过拟合；短期强势不等于可实盘。

## 7. Shadow 观察与 missed opportunity
- persistence_breakout_v2：最新 selected_symbols=['510300']，selected_count=1，仍 research_only。
- Shadow weekly：evidence_level=insufficient；ready_to_relax_filters=False；ready_for_preview=False；ready_for_execution=False。
- missed opportunity candidate_count=49，matured_forward_return_count=0。forward returns 多数 pending，不能据此放宽过滤。

## 8. 本周主要风险
1. 当前组合缺少宽基 ETF，收益更依赖行业/主题轮动。
2. 金融地产 + 科技成长暴露偏集中；512880 属 high_beta。
3. 512800 进入 REVIEW，短周期转弱且浮亏，需要下周重点观察。
4. 515000 浮盈较大但未实现，后续应研究移动止盈或退出规则。
5. 研究模型证据不足，不能接执行层。
6. 组合暴露估值和模拟盘绩效估值存在差异：portfolio_exposure 持仓市值 3074.80 vs paper_performance 持仓市值 3008.10，差异 66.70；建议后续检查 exposure 是否使用了最新 close 或旧 position 快照。

## 9. 建议交给 ChatGPT 的复盘问题
1. 本周卖出 515880、买入 512880 的模拟执行是否符合“降低问题标的、保留金融弹性”的逻辑？
2. 512800 的 REVIEW 是否应该升级为 REDUCE 候选，还是因为银行/红利属性而放宽？
3. 对 515000 的盈利持仓，是否应该加入移动止盈研究，而不是只等 SELL？
4. 下周是否应优先观察宽基 ETF（588000、159915、510300）来改善组合平衡？
5. 当前 BUY ranking 与 adjusted preview 的分歧是否合理？是否需要把 adjusted preview 的组合均衡逻辑进一步量化？
6. shadow 模型 persistence_breakout_v2 选 510300 是否具有实际研究价值，还是过于保守？
7. 哪些报告字段应优先统一口径，避免 dashboard 与研究报告冲突？

## 10. 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 本摘要不修改 paper_trades.csv / paper_positions.csv。
- shadow / preview 模型均不接执行层。
