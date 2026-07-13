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
