# 当前模型与数据成熟度诊断报告

生成时间：2026-06-24 00:54:08  
权限边界：L2 本地工程权限。本报告只读取本地文件，不修改模型、不修改交易逻辑、不接券商、不真实下单。

## 1. 摘要结论

当前项目已经具备较完整的 ETF 历史行情池和历史回测研究材料，但真实日更观察、模拟仓闭环、shadow forward return 成熟样本仍处于早期。

- 当前模型阶段：**Shadow Observation Period / 影子观察期**。
- 正式模型状态：**未改变，仍锁定**。
- 当前 ETF 日线文件数：**183**。
- 最新本地数据日：**2026-06-23**。
- 历史回测交易日：**256**，区间约 **2025-05-30 至 2026-06-18**。
- 模拟仓真实交易起点：**2026-06-09**。
- 模拟交易记录：**7** 条；当前持仓 **3** 只；已平仓闭环 **2** 个。
- 原始权益曲线：**9** 条；回填权益曲线：**15** 条，回填数据属于估算派生数据。
- persistence shadow tracking：**1** 条；missed opportunity tracking：**20** 条。
- 成熟 forward return 样本：1d=10，3d=0，5d=0，10d=0，20d=0。

核心判断：**当前模拟仓数据主要用于观察执行链路和风险，不足以证明策略稳定盈利。** 当前不应修改正式模型，不应进入 preview，不应接入 `paper_trade_engine.py`。

## 2. 文件完整性检查

|文件|状态|
|---|---|
|reports/dashboard_data.json|exists|
|reports/latest_data_coverage.md|exists|
|reports/latest_data_health.md|exists|
|reports/data_download_report.md|exists|
|data/etf_daily/|exists|
|data/paper_trades.csv|exists|
|data/paper_positions.csv|exists|
|data/paper_equity_curve.csv|exists|
|data/paper_equity_curve_backfilled.csv|exists|
|reports/paper_performance_summary.json|exists|
|reports/paper_performance_summary.md|exists|
|reports/paper_trade_pnl.csv|exists|
|reports/paper_equity_curve.md|exists|
|reports/paper_equity_curve_backfilled.md|exists|
|reports/ranking_model_v2_backtest_report.md|exists|
|reports/ranking_model_v2_decision_report.md|exists|
|reports/v2_underperformance_attribution.md|exists|
|reports/alpha_factor_enhancement_research.md|exists|
|reports/phase4c_alpha_model_comparison.md|exists|
|reports/phase4c_alpha_model_decision.md|exists|
|data/persistence_breakout_shadow_tracking.csv|exists|
|data/missed_opportunity_tracking.csv|exists|
|reports/persistence_breakout_shadow_signal.csv|exists|
|reports/persistence_breakout_shadow_portfolio.csv|exists|
|reports/model_shadow_comparison.csv|exists|
|reports/shadow_observation_weekly.json|exists|
|reports/shadow_observation_weekly.md|exists|
|reports/missed_opportunity_tracker.md|exists|
|reports/risk_on_empty_signal_analysis.md|exists|

缺失文件：

无

## 3. ETF 历史行情数据统计

- ETF 日线文件数：183
- 最早数据日期：2022-01-04
- 最新数据日期：2026-06-23
- 最新日期分布：{'2026-06-23': 183}
- 数据最新日期落后 ETF 数：0
- 起始晚于 2022-01-01 的 ETF 数：183

数据用途判断：

|用途|判断|说明|
|---|---|---|
|历史回测|可用|ETF 文件数量和历史长度足够支撑第一版轮动回测，但仍需处理幸存者偏差和新基金样本不足。|
|ranking 因子研究|可用|横截面样本足够，适合继续做历史因子对比和稳定性检查。|
|shadow 观察|可用|日更数据可支持 shadow 追踪，但真实观察天数仍少。|
|正式模拟盘日更|可用|当前 183 只 ETF 均已更新到 2026-06-23。|

### 数据覆盖最差的 20 个 ETF

|symbol|name|start_date|end_date|rows|comment|
|---|---|---|---|---|---|
|510180|上证180ETF|2026-01-05|2026-06-23|111|起始晚于 2022-01-01，历史较短|
|510500|中证500ETF|2026-01-05|2026-06-23|111|起始晚于 2022-01-01，历史较短|
|510880|红利ETF|2026-01-05|2026-06-23|111|起始晚于 2022-01-01，历史较短|
|512100|中证1000ETF|2026-01-05|2026-06-23|111|起始晚于 2022-01-01，历史较短|
|515880|证券公司ETF|2026-01-05|2026-06-23|111|起始晚于 2022-01-01，历史较短|
|510050|上证50ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|510060|510060|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|510230|金融ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|510270|510270|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|510410|资源ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511010|国债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511030|公司债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511090|30年国债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511260|十年国债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511360|短融ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511380|可转债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511520|政金债ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511600|511600|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511690|511690|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|
|511880|银华日利ETF|2025-03-03|2026-06-23|318|起始晚于 2022-01-01，历史较短|

## 4. 回测数据 vs 真实观察数据

|数据层|样本量|日期/说明|可用于什么|不能说明什么|
|---|---:|---|---|---|
|历史回测数据|256 个交易日|2025-05-30 至 2026-06-18|策略假设筛选、风险收益初筛、成本敏感性研究|不能证明未来稳定盈利，存在过拟合和市场阶段依赖|
|真实日更观察数据|9 条原始权益曲线|模拟仓开始后生成|验证自动化、估值、报告链路|样本太短，不能证明 alpha|
|模拟仓真实运行数据|7 条交易，2 个闭环|起点 2026-06-09|验证执行约束、成本、止损/复核流程|不足以评估胜率、盈亏比和稳定性|
|shadow forward tracking|persistence 1 条；missed 20 条|大量 forward return 未成熟|观察过滤器是否过严、影子模型是否错过机会|不能放宽规则，不能接执行层|
|回填权益曲线|15 条|由本地交易和收盘价估算|补足展示和粗略回看|不是逐日真实账户快照|

当前真正可用于“实时验证模型”的成熟样本约为：成熟 10d forward 样本 0 + 已平仓交易闭环 2 = **2**。这个数量明显不足。

## 5. 模型阶段诊断

|模型/模块|阶段|状态|收益|回撤|交易数|执行接入|证据|主要问题|
|---|---|---|---|---|---|---|---|---|
|original_ranking_baseline|历史回测基线|research_only|1.64%|-9.63%|76|False|historical_backtest_only|未跑赢 510300，且只是历史回测|
|adjusted_preview_baseline|历史回测/预览基线|research_only|5.05%|-8.42%|76|False|historical_backtest_only|收益改善但未证明可实盘化|
|top10_diversified_filter_v2|低回撤候选|shadow_candidate_only|11.31%|-4.86%|62|False|historical_backtest_only|低回撤但未跑赢 510300|
|persistence_breakout_v2|Phase 4C alpha 候选|shadow_tracking|20.19%|-3.43%||False|insufficient|历史研究较强，但真实 shadow 样本刚开始|
|missed_opportunity_tracker|过滤器有效性观察|active_research|暂无|暂无|20|False|insufficient|forward return 大多未成熟|
|shadow_observation_weekly|周度影子观察|active_research|暂无|暂无|0|False|insufficient|证据不足|
|paper_portfolio_monitoring|模拟仓监控|live_paper_observation|暂无|暂无|7|False|live_sample_too_small|样本太少，只能验证执行链路|

重点说明：

- `original_baseline_v2` 和 `adjusted_preview_baseline_v2` 主要来自历史回测，只能作为研究基线。
- `top10_diversified_filter_v2` 是低回撤候选，但未跑赢 510300 buy-and-hold，因此只能 shadow tracking。
- `persistence_breakout_v2` 在 Phase 4C 历史研究中表现较强，但真实 shadow 样本刚开始，不能接执行层。
- missed opportunity tracker 的核心价值是判断过滤器是否过严，但当前 forward return 大多未成熟。
- 当前正式模型未改变，`paper_trade_engine.py` 不应被 shadow 模型替代。

## 6. 模拟仓数据成熟度

|指标|当前值|
|---|---:|
|初始本金|10000.00|
|研究主本金口径|20000.00|
|当前总资产|10080.05|
|现金|7076.25|
|持仓市值|3003.80|
|总盈亏|80.05|
|总收益率|0.80%|
|已实现盈亏|-73.59|
|未实现盈亏|143.30|
|当前持仓数量|3|
|交易次数|7|
|已平仓交易数量|2|
|未平仓持仓数量|3|
|原始权益曲线记录数|9|
|回填权益曲线记录数|15|
|最大回撤|-1.03%|

判断：当前模拟仓数据主要用于观察执行链路、成本约束、估值刷新、风险复核和 App 自动化是否可靠，**不足以判断策略有效，更不足以证明策略稳定盈利**。

最低观察门槛还缺：

- 真实交易日：还缺 11 天到 20 天最低门槛。
- paper trade 记录：还缺 3 条到 10 条最低门槛。
- 完整交易闭环：还缺 8 个到 10 个初步判断门槛。

## 7. Shadow Observation 数据成熟度

|指标|当前值|
|---|---:|
|persistence shadow signal day 数|1|
|selected days|1|
|empty signal days|1|
|risk_on empty days|1|
|missed opportunity candidate count|10|
|pending forward return 数|11|
|成熟 1d forward|10|
|成熟 3d forward|0|
|成熟 5d forward|0|
|成熟 10d forward|0|
|成熟 20d forward|0|
|missed opportunity rate|0.00%|
|filter effective rate|0.00%|
|evidence_level|insufficient|
|ready_to_relax_filters|False|
|ready_for_preview|False|
|ready_for_execution|False|

判断：当前没有足够证据判断 `trend_not_confirmed` 是否过严，没有足够证据放宽规则，没有足够证据进入 preview，更没有足够证据接入 `paper_trade_engine.py`。

## 8. 还需要多少真实数据

### A. 最低观察门槛

需要至少 20 个真实交易日、20 个成熟 10d forward return 样本、若干次 selected/filtered 对比、10 条以上 paper trade 记录。

当前缺口：

- 真实交易日：9 / 20，还缺 11。
- 成熟 10d forward：0 / 20，还缺 20。
- paper trade：7 / 10，还缺 3。

### B. 初步判断门槛

需要 40-60 个真实交易日、30-50 个成熟 10d forward 样本、20 个成熟 20d forward 样本、10-20 个完整交易闭环，且经历上涨和震荡/回撤阶段。

当前缺口：

- 到 40 个真实交易日还缺 31，到 60 个还缺 51。
- 成熟 20d forward：0 / 20，还缺 20。
- 完整交易闭环：2 / 10，还缺 8。

### C. 考虑 Preview 门槛

需要 shadow 模型连续 60 个交易日表现稳定；forward return 相对 510300 有正超额；missed opportunity / filter effective 数据支持规则；回撤不明显扩大；不依赖单一 ETF；交易频率和成本可控。

当前结论：**不满足**。

### D. 考虑 paper_trade_engine 接入门槛

必须先进入 preview，preview 稳定后再小范围 paper integration，并保留明确回滚机制。当前结论：**不满足**。

## 9. 当前数据能支持与不能支持的结论

### 能支持

- ETF 历史数据池已经足够支撑第一版回测、ranking 研究和模型候选筛选。
- `top10_diversified_filter_v2` 属于低回撤候选，但收益不够强，不能直接上线。
- `persistence_breakout_v2` 值得继续 shadow tracking。
- App、数据日更、覆盖/健康报告、模拟仓展示链路已经可以持续观察。

### 不能支持

- 不能证明当前策略稳定盈利。
- 不能证明 shadow 模型优于正式模型。
- 不能证明过滤规则过严。
- 不能放宽 `trend_not_confirmed` 等过滤器。
- 不能进入 preview。
- 不能接入 `paper_trade_engine.py`。
- 不能真实交易。

## 10. 下一步建议

1. 保持正式模型和执行层锁定，不改 `paper_trade_engine.py`。
2. 每个交易日继续日更、生成 ranking、sell review、paper portfolio、shadow tracking。
3. 每周固定生成 shadow observation weekly，等待 10d/20d forward return 成熟。
4. 累积至少 20 个真实交易日和 20 个成熟 10d forward 样本后，再做第一次小复核。
5. 累积 40-60 个真实交易日、20 个成熟 20d 样本、10 个以上完整交易闭环后，再讨论 preview。

## 11. 安全边界确认

本轮只生成诊断报告：

- 未修改模型规则。
- 未修改 `src/paper_trade_engine.py`。
- 未修改 `data/paper_trades.csv`。
- 未修改 `data/paper_positions.csv`。
- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未扩池。
- 未暴露 token / 密码。
- 未把 shadow 接执行层。
