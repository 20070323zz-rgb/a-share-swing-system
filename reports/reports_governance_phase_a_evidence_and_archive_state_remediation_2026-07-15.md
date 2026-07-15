---
report_id: report_2c2bc8ca7c63cf0b
report_type: GOVERNANCE_EVIDENCE_ARCHIVE_STATE_REMEDIATION
business_date: 2026-07-15
created_at: 2026-07-15T17:57:57+08:00
status: READY_FOR_FINAL_RESULT_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-evidence-archive-v3-2026-07-15
retention_class: PERMANENT
schema_version: 3
snapshot_revision: v3
immutable: true
evidence_registry_version: v1
classification_schema_version: 3
supersedes: 
---
# Reports Governance Phase A Evidence and Archived-State Remediation

## Closed targeted blockers

1. Every Catalog `archive_block_evidence_ids` value resolves through the unified Evidence Registry (2151 records).
2. Dependency, role, retention, naming, location, state-authority and governance-rule evidence are versioned and source-hash traceable.
3. All 12 concrete dynamic Producer outputs retain dependency-backed Evidence.
4. All 45 `reports/archive/**` records are `ALREADY_ARCHIVED` and `MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED`.
5. The Phase B input contains 5 safe and 87 safe-with-rename records, with no already-archived record.
6. Deletion eligibility remains conservative; already-archived location never creates a deletion candidate.
7. Prior 2026-07-14 and 2026-07-15 v1/v2 snapshots remain immutable.

## Stratified manual review record

- ALREADY_ARCHIVED: 45/45 reviewed; accuracy `100.00%`
- SAFE_TO_MIGRATE: 5/5 reviewed; accuracy `100.00%`
- SAFE_TO_MIGRATE_RENAME_REQUIRED: 87/87 reviewed; accuracy `100.00%`
- Active blocked: 20 reviewed; accuracy `100.00%`
- Runtime blocked: 20 reviewed; accuracy `100.00%`
- Unknown blocked: 20 reviewed; accuracy `100.00%`
- Retention blocked: 20 reviewed; accuracy `100.00%`

### ALREADY_ARCHIVED (all)

- `PASS` `reports/archive/chatgpt_packets/chatgpt_analysis_packet_2026-06-27.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_report_summary_2026-06-27.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-26.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-26.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-29.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-29.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-30.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-30.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-01.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-01.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-03.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-03.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-09.json`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-09.md`
- `PASS` `reports/archive/chatgpt_packets/chatgpt_weekly_report_summary_2026-06-27.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-01.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-02.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-03.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-09.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-10.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-11.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-12.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-15.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-16.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-17.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-18.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-22.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-23.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-24.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-25.md`
- `PASS` `reports/archive/daily/daily_signal_2026-06-26.md`
- `PASS` `reports/archive/legacy_misc/app_backfill_button_fix_20260624.md`
- `PASS` `reports/archive/research_phases/app_polish_phase1_launch_stability_report.md`
- `PASS` `reports/archive/research_phases/app_release_phase2_shortcut_equity_backfill_report.md`
- `PASS` `reports/archive/research_phases/phase3a_fastapi_react_app_report.md`
- `PASS` `reports/archive/research_phases/phase3b_app_control_room_upgrade_report.md`
- `PASS` `reports/archive/research_phases/phase3c_desktop_app_mvp_report.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-01.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-02.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-03.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-09.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-11.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-12.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-25.md`
- `PASS` `reports/archive/weekly/weekly_review_2026-06-26.md`

### SAFE_TO_MIGRATE (all)

- `PASS` `reports/data_update_status.datasource_refresh.json`
- `PASS` `reports/data_update_status.dryrun.json`
- `PASS` `reports/pr_final_hygiene_audit_2026-07-12.md`
- `PASS` `reports/project_weekly_report_2026-07-10.md`
- `PASS` `reports/trading_weekly_report_2026-07-10.md`

### SAFE_TO_MIGRATE_RENAME_REQUIRED (all)

- `PASS` `reports/app_data_backfill_button_audit.md`
- `PASS` `reports/app_launch_diagnostics.md`
- `PASS` `reports/backtest_result.csv`
- `PASS` `reports/backtest_summary.md`
- `PASS` `reports/baostock_diagnosis.md`
- `PASS` `reports/benchmark_redundancy_analysis.md`
- `PASS` `reports/codex_daily_research_prompt.md`
- `PASS` `reports/codex_weekly_research_prompt.md`
- `PASS` `reports/daily_data_update_diagnosis_report.md`
- `PASS` `reports/dashboard_redesign_research.md`
- `PASS` `reports/effective_sample_coverage_audit.md`
- `PASS` `reports/etf_pool_research_matrix.csv`
- `PASS` `reports/etf_pool_research_report.md`
- `PASS` `reports/etf_strategy_news_sentiment_research.md`
- `PASS` `reports/exposure_candidate_matrix.md`
- `PASS` `reports/exposure_data_contract.md`
- `PASS` `reports/exposure_framework_feasibility_study.md`
- `PASS` `reports/exposure_gap_analysis.md`
- `PASS` `reports/exposure_point_in_time_rules.md`
- `PASS` `reports/exposure_portfolio_role_definition.md`
- `PASS` `reports/exposure_prototype_data_quality.md`
- `PASS` `reports/exposure_prototype_summary.md`
- `PASS` `reports/exposure_redundancy_analysis.md`
- `PASS` `reports/exposure_taxonomy_design.md`
- `PASS` `reports/exposure_window_stability.md`
- `PASS` `reports/factor_analysis_report.md`
- `PASS` `reports/frontend_css_cleanup_audit.md`
- `PASS` `reports/industry_etf_diagnosis.md`
- `PASS` `reports/jqdata_connection_diagnosis.md`
- `PASS` `reports/manual_failed_diagnosis_report.md`
- `PASS` `reports/manual_import_integrity_audit.md`
- `PASS` `reports/market_exposure_data_contract.md`
- `PASS` `reports/market_exposure_redesign.md`
- `PASS` `reports/market_exposure_vector_summary.md`
- `PASS` `reports/model_data_maturity_analysis.json`
- `PASS` `reports/model_data_maturity_analysis.md`
- `PASS` `reports/model_data_maturity_tables.csv`
- `PASS` `reports/model_dataset.csv`
- `PASS` `reports/model_research_report.md`
- `PASS` `reports/multi_benchmark_framework.md`
- `PASS` `reports/path_sanitization_audit.md`
- `PASS` `reports/regime_layer_phase3_5b_decision.json`
- `PASS` `reports/shadcn_card_density_audit.md`
- `PASS` `reports/shadcn_ui_compatibility_audit.json`
- `PASS` `reports/shadcn_ui_compatibility_audit.md`
- `PASS` `reports/style_fit_commodity_cyclical_audit.csv`
- `PASS` `reports/style_fit_commodity_cyclical_audit.md`
- `PASS` `reports/style_fit_commodity_cyclical_qualification.json`
- `PASS` `reports/style_fit_etf_level_robustness.csv`
- `PASS` `reports/style_fit_etf_level_robustness.md`
- `PASS` `reports/style_fit_evidence_qualification_summary.json`
- `PASS` `reports/style_fit_failure_attribution.json`
- `PASS` `reports/style_fit_failure_attribution.md`
- `PASS` `reports/style_fit_failure_postmortem.md`
- `PASS` `reports/style_fit_failure_tree.md`
- `PASS` `reports/style_fit_future_preview_research_scope.json`
- `PASS` `reports/style_fit_high_beta_theme_audit.csv`
- `PASS` `reports/style_fit_high_beta_theme_audit.md`
- `PASS` `reports/style_fit_high_beta_theme_qualification.json`
- `PASS` `reports/style_fit_horizon_robustness.csv`
- `PASS` `reports/style_fit_horizon_robustness.md`
- `PASS` `reports/style_fit_incremental_signal_final_decision.json`
- `PASS` `reports/style_fit_incremental_value_robustness.csv`
- `PASS` `reports/style_fit_incremental_value_robustness.md`
- `PASS` `reports/style_fit_regime_segment_robustness.csv`
- `PASS` `reports/style_fit_regime_segment_robustness.md`
- `PASS` `reports/style_fit_robustness_evidence_integrity_audit.json`
- `PASS` `reports/style_fit_time_robustness.csv`
- `PASS` `reports/style_fit_time_robustness.md`
- `PASS` `reports/style_regime_evidence_qualification_matrix.json`
- `PASS` `reports/style_regime_fit_source_audit.json`
- `PASS` `reports/tushare_capability_gap_audit.md`
- `PASS` `reports/universe_v2_candidate_qualification.md`
- `PASS` `reports/universe_v2_coverage_gap_analysis.md`
- `PASS` `reports/universe_v2_expansion_plan.md`
- `PASS` `reports/universe_v2_full_replay.md`
- `PASS` `reports/universe_v2_replay/v2_style_fit_regime_segments.csv`
- `PASS` `reports/universe_v2_replay/v2_style_fit_robustness_base.csv`
- `PASS` `reports/universe_v2_replay/v2_style_fit_robustness_core_summary.json`
- `PASS` `reports/universe_v2_replay/v2_style_fit_robustness_source_audit.json`
- `PASS` `reports/universe_v2_replay/v2_style_regime_differentiation.csv`
- `PASS` `reports/universe_v2_replay/v2_style_regime_differentiation.json`
- `PASS` `reports/universe_v2_replay/v2_style_regime_fit_matrix.csv`
- `PASS` `reports/universe_v2_replay/v2_style_regime_fit_matrix.json`
- `PASS` `reports/universe_v2_replay/v2_style_regime_fit_summary.csv`
- `PASS` `reports/universe_v2_replay/v2_style_regime_fit_summary.json`
- `PASS` `reports/universe_v2_replay_plan.md`

### Active blocked sample

- `PASS` `reports/akshare_connectivity_check.md`
- `PASS` `reports/alpha_factor_enhancement_metrics.json`
- `PASS` `reports/alpha_factor_enhancement_research.md`
- `PASS` `reports/alpha_factor_enhancement_summary.csv`
- `PASS` `reports/archive_candidate_list.csv`
- `PASS` `reports/archive_candidate_list.json`
- `PASS` `reports/archive_candidate_list.md`
- `PASS` `reports/archive_manifest_after.json`
- `PASS` `reports/archive_manifest_before.json`
- `PASS` `reports/automation_four_node_sync_report.md`
- `PASS` `reports/b1_strategy_enhancement_preview_report.md`
- `PASS` `reports/b2_strategy_preview_tracking_report.md`
- `PASS` `reports/backtest_capital_sensitivity.csv`
- `PASS` `reports/backtest_capital_sensitivity.md`
- `PASS` `reports/backtest_consistency_check.json`
- `PASS` `reports/backtest_consistency_check.md`
- `PASS` `reports/backtest_cost_diagnostics.csv`
- `PASS` `reports/backtest_cost_diagnostics.md`
- `PASS` `reports/backtest_drawdown_diagnostics.csv`
- `PASS` `reports/backtest_drawdown_diagnostics.md`

### Runtime blocked sample

- `PASS` `reports/akshare_connectivity_check.json`
- `PASS` `reports/app_launch_diagnostics.json`
- `PASS` `reports/app_task_status.json`
- `PASS` `reports/backtest_diagnostics_summary.json`
- `PASS` `reports/backtest_equity_curve.csv`
- `PASS` `reports/backtest_metrics.json`
- `PASS` `reports/backtest_positions.csv`
- `PASS` `reports/backtest_summary.csv`
- `PASS` `reports/backtest_trades.csv`
- `PASS` `reports/backtest_yearly_summary.csv`
- `PASS` `reports/broad_base_balance_preview.csv`
- `PASS` `reports/broad_base_balance_preview.json`
- `PASS` `reports/broad_base_balance_preview.md`
- `PASS` `reports/buy_signal_ranking.md`
- `PASS` `reports/chatgpt_weekly_analysis_packet_latest.json`
- `PASS` `reports/chatgpt_weekly_analysis_packet_latest.md`
- `PASS` `reports/current_buy_top10_style_regime_fit.csv`
- `PASS` `reports/current_buy_top10_style_regime_fit.json`
- `PASS` `reports/current_buy_top10_style_regime_fit.md`
- `PASS` `reports/current_portfolio_style_regime_fit.json`

### Unknown blocked sample

- `PASS` `reports/.gitkeep`
- `PASS` `reports/account_status.csv`
- `PASS` `reports/app_backfill_button_fix_report.md`
- `PASS` `reports/app_independent_launch_fix_report.md`
- `PASS` `reports/app_launch_fix_report.json`
- `PASS` `reports/app_launch_fix_report.md`
- `PASS` `reports/app_local_release_phase1_report.md`
- `PASS` `reports/archive_manifest_after.md`
- `PASS` `reports/archive_manifest_before.md`
- `PASS` `reports/baostock_app_backfill_fix_report.md`
- `PASS` `reports/baostock_daily_source_optimization_report.md`
- `PASS` `reports/data_download_report.md`
- `PASS` `reports/data_health_report.md`
- `PASS` `reports/data_quality_report.md`
- `PASS` `reports/data_source_proposal.md`
- `PASS` `reports/data_update_app_task_fix_report.md`
- `PASS` `reports/data_update_automation_fix_report.md`
- `PASS` `reports/data_update_log.md`
- `PASS` `reports/data_update_probe_fast.json`
- `PASS` `reports/etf_expansion_cleanup_report.md`

### Retention blocked sample

- `PASS` `reports/afternoon_open_check.json`
- `PASS` `reports/afternoon_open_check.md`
- `PASS` `reports/exposure_governance_framework.md`
- `PASS` `reports/exposure_permission_matrix.md`
- `PASS` `reports/exposure_phase_c_readiness.md`
- `PASS` `reports/exposure_research_readiness.md`
- `PASS` `reports/exposure_validation_metrics.json`
- `PASS` `reports/exposure_validation_summary.md`
- `PASS` `reports/local_validation.md`
- `PASS` `reports/manual_download_validation_report.md`
- `PASS` `reports/midday_check.json`
- `PASS` `reports/midday_check.md`
- `PASS` `reports/open_check.json`
- `PASS` `reports/open_check.md`
- `PASS` `reports/paper_execution_freshness_gate_summary.md`
- `PASS` `reports/phase35b_recovery_validation.md`
- `PASS` `reports/project_checkpoint_post_merge_validation_2026-07.md`
- `PASS` `reports/project_context_bootstrap_audit.json`
- `PASS` `reports/project_context_bootstrap_audit.md`
- `PASS` `reports/project_context_existing_state_audit.json`

## Boundaries

No historical report was moved, renamed, deleted or rewritten. Formal strategy, execution, ETF SSOT, protected ledgers, PR #3 implementation/evidence and Availability staging were not modified. No real data interface was called. PR #4 remains Draft and requires final result Re-QC.
