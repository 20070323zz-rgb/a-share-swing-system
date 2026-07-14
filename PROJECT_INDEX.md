# A-share Swing System Project Index

生成时间：2026-07-13 17:03:10

## 当前阶段

项目处于 ETF 双周期模拟盘 + 研究观察层阶段。正式执行层仍保持模拟盘，不接券商 API，不真实下单。

## 核心入口

- App 后端：`app/backend/main.py`
- App 前端：`app/frontend/`
- 静态看板：`dashboard/index.html`
- 看板生成：`dashboard/build_dashboard.py`
- 每日收盘：`scripts/run_daily_close.sh`
- 每周复盘：`scripts/run_weekly_review.sh`
- 本地 App 启动：`打开量化研究控制台.command`

## 核心数据

- ETF 日线：`data/etf_daily/`
- 模拟交易流水：`data/paper_trades.csv`
- 模拟持仓：`data/paper_positions.csv`
- 看板数据：`reports/dashboard_data.json`

## 核心报告

- 每日摘要：`reports/latest_brief.md`
- 模拟盘：`reports/latest_paper_portfolio.md`
- BUY ranking：`reports/buy_signal_ranking.md`
- 卖出复核：`reports/sell_signal_review.md`
- 周报分析包：`reports/chatgpt_weekly_analysis_packet_latest.md`
- 项目周报：`reports/project_weekly_report_2026-07-10.md`
- 模拟交易周报：`reports/trading_weekly_report_2026-07-10.md`
- 数据健康：`reports/latest_data_health.md`
- 数据覆盖：`reports/latest_data_coverage.md`

## Project Context / Codex Continuity

Project Context Persistence Phase: COMPLETE
Regime Layer Phase 3.5 / Style Fit Research Phase: COMPLETE
Universe Evolution Phase 4.1: COMPLETE
Universe Evolution Phase 4.2: COMPLETE
Research Generalization Phase 5.1: COMPLETE
Research Generalization Phase 5.2: COMPLETE
Research Generalization Phase 5.3: COMPLETE
Style Framework 2.0 Phase A: COMPLETE
Exposure Framework Phase B: COMPLETE
Exposure Framework Phase C: COMPLETE
Exposure Framework Phase D: COMPLETE
Exposure Framework Phase E-A: COMPLETE
Exposure Framework Phase E-B: COMPLETE
Exposure Framework Phase F: COMPLETE
Exposure Framework Phase 1: COMPLETE
Project Infrastructure Batch Standardization V1: COMPLETE
Paper Execution Safety Phase 1: COMPLETE
Tushare 5000 Data Foundation Audit: COMPLETE
Reports Governance Phase A: NOT_STARTED
Report File Migration: BLOCKED
PR #1 Hygiene Cleanup: COMPLETE
PR #1 Diff Check: CLEAN
Local Temporary Artifacts: RESOLVED
July 2026 Project Checkpoint: COMPLETE
PR #1: MERGED
Post-Merge Validation: PASS
Main Branch: STABLE
Main Branch Merge: COMPLETE
Tushare Minimal Staging Proof & PIT Contract: COMPLETE
Tushare Staging / PIT: COMPLETE_WITH_LIMITATIONS
Tushare Evidence Isolation: COMPLETE
PR #2: DRAFT_AWAITING_RE_QC
Tushare Formal Staging Architecture: NOT_STARTED
Tushare Primary Upstream Migration: APPROVED_FOR_FUTURE_ENGINEERING / NOT_STARTED
ETF Daily Availability Timing Audit: NOT_STARTED
Data Foundation Upgrade: NOT_STARTED
Data Promotion: BLOCKED
Paper Execution Freshness Gate: ACTIVE
Guarded Paper Execution Entry: ACTIVE
Stale Data Fallback: BLOCKED
2026-07-10 Stale Trades: AUDITED_NON_DESTRUCTIVELY
Universe V2 Candidate: QUALIFIED
Universe V2 Research Universe: READY_FOR_REPLAY_PREPARATION
Universe V2 Replay Planning: COMPLETE
Universe V2 Replay: COMPLETE
V1 vs V2 Generalization Analysis: COMPLETE
Generalization Verdict: FAILED_GENERALIZATION
Failure Attribution: COMPLETE
Style Fit Current Treatment: V1-SPECIFIC_FINDING
Exposure Framework Feasibility: POSITIVE_WITH_DATA_GAPS
Style Framework 2.0 Status: FEASIBILITY_STUDY_COMPLETE
Exposure Taxonomy: DESIGNED
Exposure Data Contract: DESIGNED
Exposure Point-in-Time Rules: DESIGNED
Exposure Prototype: COMPLETE
Exposure Prototype Scope: NARROW_PRICE_LIQUIDITY_ONLY
Exposure Validation: COMPLETE
Exposure Research Readiness: PARTIAL_READY
Market Beta Proxy: RETAINED_AS_SINGLE_BENCHMARK_BASELINE_ONLY
Market Exposure Redesign: COMPLETE
Market Exposure Framework: MULTI_BENCHMARK_RECOMMENDED
Market Exposure Engineering Prototype: COMPLETE
Market Exposure Vector: RESEARCH_ONLY
Market Exposure Benchmark Basket: market_benchmark_basket_v1
Market Exposure Explanatory Verdict: ADDS_EXPLANATORY_DIMENSION
Benchmark Redundancy Verdict: LOCALIZED_HIGH_REDUNDANCY
Exposure Governance: COMPLETE
Price-Derived Exposure Expansion: FROZEN
Portfolio Research Integration: ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research: NOT_STARTED
Signal Integration: BLOCKED
Batch Standard Version: V1
Exposure Framework Development: RESEARCH_ONLY_PROTOTYPE_COMPLETE
Universe V2 Trade Pool Activation: BLOCKED
Preview Research: NOT STARTED
Formal Execution: BLOCKED

新 Codex thread 应先读取这些文件，再开始实质性修改：

- 项目级长期指令：`AGENTS.md`
- 当前项目事实快照：`docs/current_project_state.md`
- 当前执行状态：`docs/current_phase_status.json`
- 上下文架构说明：`docs/project_context_architecture.md`
- 新 thread 启动协议：`docs/codex_new_thread_bootstrap.md`
- 新 thread 标准提示模板：`docs/codex_new_thread_prompt_template.md`
- 上下文验证器：`scripts/context/validate_project_context.py`
- bootstrap helper：`scripts/context/bootstrap_codex_context.py`
- 最新验证报告：`reports/project_context_validation_latest.md`
- 最终恢复演习决策：`reports/project_context_recovery_drill_decision.md`
- Context Persistence 封版报告：`reports/project_context_persistence_final.md`
- Style Fit 治理框架：`reports/style_fit_governance_framework.md`
- Style Fit 权限矩阵：`reports/style_fit_permission_matrix.md`
- Style Fit 研究日志：`docs/research/phase35_style_fit_research_journal.md`
- Universe V1 版本基线：`configs/universe_versions/universe_v1.yaml`
- Universe V2 候选版本：`configs/universe_versions/universe_v2_candidate.yaml`
- Universe V2 Registry：`configs/universe_versions/universe_v2_registry.yaml`
- Universe V2 候选资格报告：`reports/universe_v2_candidate_qualification.md`
- Universe Registry 报告：`reports/universe_registry.md`
- Universe V2 覆盖缺口分析：`reports/universe_v2_coverage_gap_analysis.md`
- Universe V2 扩容计划：`reports/universe_v2_expansion_plan.md`
- Universe V2 Replay 计划：`reports/universe_v2_replay_plan.md`
- Replay Checkpoint 计划：`reports/replay_checkpoint_plan.md`
- Generalization Evaluation 计划：`reports/generalization_evaluation_plan.md`
- Operational Playbook：`docs/operational_playbook.md`
- Universe V2 Full Replay：`reports/universe_v2_full_replay.md`
- V1 vs V2 Generalization：`reports/v1_vs_v2_generalization.md`
- Generalization Verdict：`reports/generalization_verdict.md`
- Universe V2 Replay artifacts：`reports/universe_v2_replay/`
- Style Fit Failure Attribution：`reports/style_fit_failure_attribution.md`
- Style Fit Failure Tree：`reports/style_fit_failure_tree.md`
- Style Fit Failure Postmortem：`reports/style_fit_failure_postmortem.md`
- Exposure Framework Feasibility Study：`reports/exposure_framework_feasibility_study.md`
- Exposure Candidate Matrix：`reports/exposure_candidate_matrix.md`
- Exposure Gap Analysis：`reports/exposure_gap_analysis.md`
- Exposure Taxonomy Design：`reports/exposure_taxonomy_design.md`
- Exposure Data Contract：`reports/exposure_data_contract.md`
- Exposure Point-in-Time Rules：`reports/exposure_point_in_time_rules.md`
- Exposure Phase C Readiness：`reports/exposure_phase_c_readiness.md`
- Exposure Prototype Summary：`reports/exposure_prototype_summary.md`
- Exposure Prototype Data Quality：`reports/exposure_prototype_data_quality.md`
- Exposure Prototype Values：`data/research/exposure_prototype/exposure_prototype_values.csv`
- Exposure Prototype Manifest：`data/research/exposure_prototype/exposure_prototype_manifest.json`
- Exposure Prototype Calculator：`src/exposure/exposure_calculator.py`
- Exposure Prototype Runner：`scripts/run_exposure_prototype.py`
- Exposure Validation Summary：`reports/exposure_validation_summary.md`
- Exposure Window Stability：`reports/exposure_window_stability.md`
- Exposure Redundancy Analysis：`reports/exposure_redundancy_analysis.md`
- Exposure Research Readiness：`reports/exposure_research_readiness.md`
- Exposure Validation Metrics：`reports/exposure_validation_metrics.json`
- Market Exposure Redesign：`reports/market_exposure_redesign.md`
- Multi-Benchmark Framework：`reports/multi_benchmark_framework.md`
- Market Exposure Data Contract：`reports/market_exposure_data_contract.md`
- Market Exposure Vector Summary：`reports/market_exposure_vector_summary.md`
- Benchmark Redundancy Analysis：`reports/benchmark_redundancy_analysis.md`
- Market Exposure Vector Calculator：`src/exposure/market_exposure_vector.py`
- Market Exposure Vector Runner：`scripts/run_market_exposure_vector.py`
- Market Exposure Vector Values：`data/research/exposure_prototype/market_exposure_vector_values.csv`
- Market Exposure Vector Manifest：`data/research/exposure_prototype/market_exposure_vector_manifest.json`
- Exposure Governance Framework：`reports/exposure_governance_framework.md`
- Exposure Permission Matrix：`reports/exposure_permission_matrix.md`
- Exposure Portfolio Role Definition：`reports/exposure_portfolio_role_definition.md`
- Exposure Framework Phase 1 Research Journal：`docs/research/exposure_framework_phase1_journal.md`
- Project Batch Standard V1：`docs/project_batch_standard.md`
- Research Batch Template：`docs/templates/research_batch_template.md`
- Engineering Batch Template：`docs/templates/engineering_batch_template.md`
- Validation Batch Template：`docs/templates/validation_batch_template.md`
- Governance Batch Template：`docs/templates/governance_batch_template.md`
- Paper Execution Freshness Gate：`src/execution/paper_freshness_gate.py`
- Guarded Paper Execution Runner：`scripts/run_paper_execution_guarded.py`
- Paper Execution Freshness Gate Summary：`reports/paper_execution_freshness_gate_summary.md`
- Paper Execution Preflight JSON：`reports/paper_execution_preflight.json`
- Paper Execution Preflight Report：`reports/paper_execution_preflight.md`
- Paper Execution Append-Only Audit：`data/audit/paper_execution_audit.jsonl`
- 2026-07-10 Stale Trade Audit：`reports/paper_execution_stale_trade_audit_2026-07-10.md`
- Tushare 5000 Capability Gap Audit：`reports/tushare_capability_gap_audit.md`
- Tushare Priority Matrix：`reports/tushare_priority_matrix.csv`
- Tushare Minimal Staging Proof：`reports/tushare_minimal_staging_proof.md`
- Tushare Interface Probe Matrix：`reports/tushare_interface_probe_matrix.csv`
- Tushare PIT Contract Matrix：`reports/tushare_pit_contract_matrix.csv`
- Tushare Index Weight Reduction Evidence：`reports/tushare_index_weight_reduction_evidence.csv`
- Tushare Real Run Attestations：`reports/tushare_real_run_attestations.md`
- Tushare Evidence Remediation：`reports/tushare_proof_evidence_remediation.md`
- Tushare Gap Reassessment：`reports/tushare_gap_reassessment.md`
- Tushare PIT Contract：`docs/tushare_pit_contract.md`
- Tushare Minimal Proof Config：`configs/tushare_minimal_proof.yaml`
- Tushare Minimal Proof Runner：`scripts/run_tushare_minimal_proof.py`

这些入口用于新 Codex thread 恢复项目状态。

新的 Codex thread 必须通过标准 bootstrap protocol 从 repository context 恢复项目状态。

## 不要随意移动

- `data/paper_trades.csv`
- `data/paper_positions.csv`
- `data/etf_daily/`
- `reports/dashboard_data.json`
- `dashboard/index.html`
- `app/backend/main.py`
- `scripts/run_daily_close.sh`
- `scripts/run_weekly_review.sh`
- `src/paper_trade_engine.py`

## 本轮审计报告

- `reports/project_checkpoint_post_merge_validation_2026-07.md`
- `reports/pr_final_hygiene_audit_2026-07-12.md`
- `reports/project_structure_audit.md`
- `reports/path_dependency_audit.md`
- `reports/file_classification_plan.md`
- `reports/recommended_project_layout.md`
- `reports/project_cleanup_roadmap.md`
- `reports/report_index.md`

## 历史报告归档说明

最近一次低风险归档时间：2026-06-29 22:15:43

- 历史报告目录：`reports/archive/`
- daily 历史报告：`reports/archive/daily/`
- weekly 历史报告：`reports/archive/weekly/`
- ChatGPT/Main 历史分析包：`reports/archive/chatgpt_packets/`
- 旧阶段研究/发布报告：`reports/archive/research_phases/`
- 其他日期版历史记录：`reports/archive/legacy_misc/`
- latest/current 活跃报告仍保留在 `reports/` 根目录。
- 本轮归档移动文件数：35
