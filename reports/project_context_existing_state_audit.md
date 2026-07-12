# Project Context Existing State Audit

生成时间：2026-07-07

本报告只审计项目上下文现状，不修改模型逻辑、不修改 BUY ranking、不修改 market_regime、不修改交易文件。

## Existing Files

| Item | Status | Notes |
| --- | --- | --- |
| `AGENTS.md` | missing | 当前没有 Codex 项目级长期指令文件。 |
| `PROJECT_INDEX.md` | present | 当前承担项目入口索引、核心文件、核心报告、历史归档说明职责。 |
| `README.md` | present | 包含项目定位、安全边界、双周期策略、模拟盘文件说明和运行方式。 |
| `CHANGELOG.md` | missing | 当前没有统一 changelog；决策历史主要在 reports 与旧记忆文件中。 |
| `docs/` | present | 存放 App 指南、数据 API 评估、交易规则、项目文件图等文档。 |
| `reports/` | present | 存放研究报告、决策 JSON、审计报告和 dashboard 数据。 |
| `reports/project_structure_audit.md` | present | 项目结构审计与目录树摘要。 |
| `reports/project_file_map.md` | missing | 当前只有 `docs/project_file_map.md`。 |
| `docs/project_file_map.md` | present | 说明主要目录职责和归档原则。 |
| `docs/current_project_state.md` | missing | 尚无当前项目事实快照。 |
| `docs/current_phase_status.json` | missing | 尚无机器可读执行状态。 |
| `docs/project_context_architecture.md` | missing | 尚无上下文文件职责说明。 |

## Required Questions

1. 当前是否已有 `AGENTS.md`：没有。
2. 当前 `AGENTS.md` 内容是什么：文件不存在，因此无内容。
3. 是否已有类似 current_project_state 的文件：有旧 `PROJECT_STATE.md`，但最后更新为 2026-06-03，已明显落后于当前 Regime/Risk Phase 3 状态。
4. 是否已有 phase status：没有统一的 `current_phase_status.json`；phase 状态散落在各 phase report 和 decision JSON。
5. 是否已有 handoff 文件：没有固定 handoff 文件；部分 handoff 信息只存在 Codex thread 或用户粘贴任务中。
6. `PROJECT_INDEX.md` 当前承担什么职责：项目入口索引、核心入口/数据/报告列表、不可随意移动文件列表、审计报告入口和归档说明。
7. 哪些长期规则目前只存在 README / reports：不接券商 API、不真实下单、不保存 token/密码、ETF-first、双周期 `mid_trend`/`short_swing`、模拟盘文件说明、future returns label-only、研究层不接执行层等。
8. 哪些当前研究状态散落在 Phase 报告：Phase 2 market regime audit、Phase 2.5 `ASYMMETRIC_CONFIRM` 稳定化选择、Phase 3 style-regime fit 结论、ready flags、BUY Top10/portfolio conflict snapshot。
9. 哪些信息可能只存在 Codex thread 中：Main Phase + Execution Batch 新工作模式、连续 remote compact / stream disconnect 的处理原则、Context Phase A/B/C/D 拆分、近期 Phase 3 resume 断点背景。
10. 新 thread 当前需要读取多少文件才能恢复项目状态：安全恢复至少需要读取 `README.md`、`PROJECT_INDEX.md`、`PROJECT_STATE.md`、`DECISIONS.md`、`docs/trading_rules.md`、`reports/regime_layer_phase2_market_audit.md`、`reports/regime_layer_phase2_5_stabilization.md`、`reports/regime_layer_phase3_style_fit.md`、`reports/style_regime_fit_phase_decision.json` 等 9 个以上文件，且仍可能缺少 thread-only 工作模式信息。
11. 是否存在互相冲突或过期的状态描述：存在。`PROJECT_STATE.md` 和 README 的部分说明仍引用旧路径或早期阶段；`PROJECT_STATE.md` 的当前进展停留在 2026-06-03，与 2026-07 Regime/Risk Phase 3 状态不一致。
12. 当前上下文断档风险：高。缺少根级 `AGENTS.md`、缺少机器可读 phase status、最新研究状态散落于多个报告，且旧记忆文件存在过期路径和阶段描述。

## Information Classification

### A. IMMUTABLE / LONG-LIVED RULES

长期有效、低频变化的项目规则进入 `AGENTS.md`，包括项目定位、正式策略边界、ETF-first、个股总仓位上限、L2 安全边界、protected files、Codex Batch 工作规则和 source-of-truth 优先级。

### B. CURRENT PROJECT STATE

当前项目事实进入 `docs/current_project_state.md`，包括当前主研究阶段、已完成 phase、正式模型状态、shadow 状态、selected stable regime、最新研究结论、主要瓶颈和下一阶段方向。

### C. EXECUTION STATE

当前执行进度进入 `docs/current_phase_status.json`，包括 main phase、phase status、completed/pending batches、resume point、ready flags、protected files。

### D. EVIDENCE / DECISION HISTORY

研究证据与历史决策继续保留在 `reports/*phase*.md`、`reports/*decision*.json`、`DECISIONS.md` 和未来 `CHANGELOG.md`。不把完整历史塞进 `AGENTS.md`。

## Context Gap Summary

当前项目的代码和研究报告已经很丰富，但“新 Codex thread 从哪里开始读、哪些规则永远优先、哪些状态只是 latest known snapshot”还没有工程化。Context Foundation 应补齐项目级长期指令、当前事实快照、机器可读 phase status、上下文架构说明，并把入口挂到 `PROJECT_INDEX.md`。
