# A-Share Swing System 项目周报

报告周期：2026-07-06 至 2026-07-10  
生成时间：2026-07-10 21:41 CST  
报告性质：项目研究、工程与治理进展汇总；不构成交易建议。

## 一、本周结论

本周完成了 Style Fit 跨 Universe 泛化检验、失败归因、Exposure Framework 第一阶段闭环以及 Batch Standardization V1。最重要的研究结论是：Style Fit 1.0 未能通过 Universe V2 泛化验证，应继续作为 `V1-SPECIFIC_FINDING` 保存，不能进入 Preview、Ranking、Score 或 Formal Execution。

项目已转向可测、PIT-aware 的 Exposure Framework。第一代 price-derived exposure 已完成窄范围原型、验证、多 Benchmark Market Exposure 改造和治理封版；Exposure 被正式定义为风险与市场驱动描述层，不是 Alpha 或交易信号层。

## 二、研究与工程进展

### 1. Universe V2 泛化与失败归因

- Universe V2 Replay 工程执行成功：16 个 `QUALIFIED_RESEARCH` ETF，20,880 条 forward rows，4,272 条 robustness base rows。
- Generalization Verdict：`FAILED_GENERALIZATION`。
- 失败是研究结论，不是工程故障；Engineering Risk 为 LOW。
- 主要归因：Universe Shift、Horizon Conflict、Methodology Limitation、Style Instability。
- Style Fit 1.0 当前处理：保留为 Universe V1 特定的历史发现，不继续调参修补。

### 2. Exposure Framework Phase A-F

- Phase A/B：完成 Exposure 可行性、taxonomy、data contract 和 point-in-time 规则设计。
- Phase C：在 Universe V2 的 16 个 ETF 上计算 5 类 exposure，共 240 条结果，缺失 0 条。
- Phase D：`realized_volatility`、`downside_drawdown_risk`、`trading_liquidity`、`return_momentum` 获得研究观察资格；single-benchmark `market_beta` 需要改进。
- Phase E-A/E-B：完成六 Benchmark Market Exposure Vector；16 个 ETF、60d/120d 两个窗口、192 条结果、缺失 0 条。
- Multi-Benchmark 相对单一 510300 的结论：`ADDS_EXPLANATORY_DIMENSION`。
- Benchmark 冗余结论：`LOCALIZED_HIGH_REDUNDANCY`，主要集中在 510500 与 512100。
- Phase F：Exposure Governance 完成；第一代 Price-Derived Exposure Expansion 已阶段性 `FROZEN`。

当前 readiness：

- `READY_FOR_PORTFOLIO_RESEARCH`：market_exposure_vector、realized_volatility、downside_drawdown_risk、trading_liquidity。
- `READY_FOR_RESEARCH_OBSERVATION`：return_momentum。
- Signal Integration：`BLOCKED`。

### 3. 项目治理

- Batch Standardization V1 已完成。
- Research、Engineering、Validation、Governance 四类 Batch 已建立统一 Header、九段结构、Validation 和 State Transition 规范。
- 后续 Main Batch 应默认使用标准模板，并继续坚持单一目标、显式边界和保守状态迁移。

## 三、今日数据更新

- 数据源：BaoStock；统一 ETF 数据库保持单一来源。
- ETF 文件：183 个。
- 最新交易日：183/183 已补至 `2026-07-10`。
- 本次实际追加：183 个 ETF 各 1 条，共 183 条日线记录。
- 最终状态：failed 0，pending 0，ETF 数据过期 0。
- 完整性校验：重复日期 0，日期乱序 0，ETF 缺失 0。
- Pool 覆盖：trade_pool 76/76，research_only 77/77。
- 数据健康：ETF 硬异常 0；12 个历史极端涨跌幅提醒保留为 warning，不自动删除数据。
- 观察池仍缺少 300750、600519 两个个股文件；二者不是 ETF，不影响 183 个 ETF 的本次完成状态。

本次数据更新未运行 paper trade engine，未修改交易逻辑，也未生成新的 BUY/SELL 执行结果。

数据更新后的交易时点复核发现：paper trade engine 曾于 2026-07-10 16:28、全库行情补齐之前运行。当天三笔模拟交易使用了 2026-07-09 的 `raw_close`，已在 `reports/trading_weekly_report_2026-07-10.md` 标记为 `NEEDS_REVIEW`；原始流水未改写。

## 四、当前项目边界

- Exposure Framework Phase 1：`COMPLETE`。
- Price-Derived Exposure Expansion：`FROZEN`。
- Portfolio Research Integration：`ELIGIBLE_FOR_RESEARCH_DESIGN`，但 Portfolio Research 尚未开始。
- Preview Research：`NOT_STARTED`。
- Formal Execution：`BLOCKED`。
- Regime 最新已知日期仍为 `2026-07-06`，相对 `2026-07-10` 行情数据已 stale，不能描述为当前实时 Regime。

## 五、主要风险与未决问题

- Methodology Risk：Style Fit 跨 Universe 泛化失败，不能恢复为通用结论。
- Research Risk：Exposure 尚缺长期、跨期和 out-of-sample 观察。
- Data Risk：结构化 holdings、AUM、benchmark methodology、fundamental exposure 等数据缺口仍未解决。
- Benchmark Risk：510500/512100 局部高度冗余；resource/cyclical benchmark 仍不足。
- Strategy Risk：正式 Exit Logic 仍是主线瓶颈；Exposure 不得代替 Exit Signal。
- Paper Execution Data Timing Risk：2026-07-10 模拟流水暴露出执行前数据日校验缺口，需要独立 Engineering Batch 处理。
- Context Warning：项目验证为 `VALID_WITH_WARNINGS`，唯一 warning 为 stale regime snapshot。

## 六、下周建议

1. 优先建立 paper execution 数据 freshness gate，阻止数据日落后于执行日时继续生成模拟成交。
2. 由 Main 决定下一研究主线，建议优先启动独立的 Exit Logic Research 设计 Batch。
3. 保持 Exposure 第一阶段冻结，仅允许确定性刷新、研究观察和经批准的恢复验证。
4. 在任何市场判断或后续研究前，单独刷新 Regime snapshot；不要把 2026-07-06 状态写成当前状态。
5. Portfolio Research 如启动，应先做权限内的诊断设计，不开发权重分配、优化器或正式仓位逻辑。
6. Preview、Ranking、Score、Formal Execution 继续保持阻断，等待独立批准与研究证据。

## 七、依据文件

- `docs/current_project_state.md`
- `docs/current_phase_status.json`
- `reports/generalization_verdict.md`
- `reports/style_fit_failure_attribution.md`
- `reports/exposure_validation_summary.md`
- `reports/market_exposure_vector_summary.md`
- `reports/exposure_governance_framework.md`
- `reports/data_update_status.json`
- `reports/data_coverage_report.md`
- `reports/data_health_report.md`
- `reports/trading_weekly_report_2026-07-10.md`
