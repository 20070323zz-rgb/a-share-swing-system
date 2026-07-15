---
report_id: report_ac2629571da014cd
report_type: DEPENDENCY_SUMMARY
business_date: 2026-07-15
created_at: 2026-07-15T12:12:06+08:00
status: REMEDIATED_PENDING_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_report_dependency_registry.py
source_run_id: reports-governance-phase-a-remediation-2026-07-15
retention_class: PERMANENT
schema_version: 2
snapshot_revision: v2
immutable: true
supersedes: reports/report_dependency_summary_2026-07-15.md
---
# Report Dependency Summary

本文件由 `scripts/governance/build_report_dependency_registry.py` 生成。扫描只读取可识别的静态/动态路径表达式；动态模式不会被伪造成具体文件依赖。

## Summary

- Registry records: 6370
- Distinct referenced paths/patterns: 905
- Dynamic patterns: 120
- Registry SHA-256: `a8dc01041a2c0e17b7795e8b18d790d199e53a328b640a4bf8e7e861bd987c89`

### Reference types

- `APP_RUNTIME_READ`: 17
- `CONSUMER_READ`: 98
- `DASHBOARD_RUNTIME_READ`: 81
- `DOCUMENTATION_LINK`: 139
- `DYNAMIC_PATH_PATTERN`: 3
- `EXAMPLE_REFERENCE`: 121
- `FILE_COPY_SOURCE`: 3
- `HISTORICAL_REFERENCE`: 3747
- `PATH_DECLARATION`: 842
- `PRODUCER_WRITE`: 342
- `STATE_INDEX_REFERENCE`: 206
- `STATIC_LINK`: 504
- `TEST_REFERENCE`: 267

### Migration impact

- `CRITICAL`: 98
- `HIGH`: 443
- `LOW`: 5353
- `MEDIUM`: 476

## Critical and high-impact references

| Referenced report | Source | Line | Type | Impact |
| --- | --- | ---: | --- | --- |
| `reports/akshare_connectivity_check.json` | `dashboard/build_dashboard.py` | 4530 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/akshare_connectivity_check.json` | `src/akshare_connectivity_check.py` | 33 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.json` | `src/data_provider_status.py` | 52 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.json` | `src/data_source_architecture_audit.py` | 56 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `src/akshare_connectivity_check.py` | 34 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_metrics.json` | `src/alpha_factor_enhancement_research.py` | 50 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `src/alpha_factor_enhancement_research.py` | 51 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_summary.csv` | `src/alpha_factor_enhancement_research.py` | 41 | `PRODUCER_WRITE` | `HIGH` |
| `reports/app_launch_diagnostics.json` | `app/backend/readers.py` | 232 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_launch_diagnostics.json` | `dashboard/build_dashboard.py` | 3681 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/app_task_status.json` | `app/backend/readers.py` | 224 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_task_status.json` | `app/backend/task_runner.py` | 58 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_task_status.json` | `app/backend/task_runner.py` | 82 | `PRODUCER_WRITE` | `HIGH` |
| `reports/app_task_status.json` | `dashboard/build_dashboard.py` | 175 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/archive_candidate_list.csv` | `scripts/archive_low_risk_reports.py` | 289 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_candidate_list.json` | `scripts/archive_low_risk_reports.py` | 290 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_candidate_list.md` | `scripts/archive_low_risk_reports.py` | 303 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_after.json` | `scripts/archive_low_risk_reports.py` | 467 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_before.json` | `scripts/archive_low_risk_reports.py` | 459 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `src/automation_nodes.py` | 347 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `src/strategy_enhancement_preview.py` | 280 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `src/strategy_preview_tracking.py` | 463 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_capital_sensitivity.csv` | `src/backtest_diagnostics.py` | 68 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_capital_sensitivity.md` | `src/backtest_diagnostics.py` | 69 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_consistency_check.json` | `src/backtest_diagnostics.py` | 63 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_consistency_check.md` | `src/backtest_diagnostics.py` | 64 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_cost_diagnostics.csv` | `src/backtest_diagnostics.py` | 73 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_cost_diagnostics.md` | `src/backtest_diagnostics.py` | 74 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_diagnostics_summary.json` | `dashboard/build_dashboard.py` | 4988 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_diagnostics_summary.json` | `src/backtest_diagnostics.py` | 99 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_drawdown_diagnostics.csv` | `src/backtest_diagnostics.py` | 94 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_drawdown_diagnostics.md` | `src/backtest_diagnostics.py` | 95 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `src/backtest_diagnostics.py` | 118 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `src/backtest_engine.py` | 689 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_execution_timing_sensitivity.csv` | `src/ranking_factor_diagnostics.py` | 85 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_execution_timing_sensitivity.md` | `src/ranking_factor_diagnostics.py` | 86 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_exit_reason_summary.csv` | `src/backtest_diagnostics.py` | 78 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_expand_pool_decision.md` | `src/backtest_diagnostics.py` | 98 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_metrics.json` | `dashboard/build_dashboard.py` | 4899 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_metrics.json` | `src/backtest_diagnostics.py` | 122 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_metrics.json` | `src/backtest_engine.py` | 708 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_phase4a_report.md` | `src/backtest_engine.py` | 709 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_positions.csv` | `src/backtest_diagnostics.py` | 120 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_positions.csv` | `src/backtest_engine.py` | 690 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_ranking_effectiveness.csv` | `src/backtest_diagnostics.py` | 90 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_ranking_effectiveness.md` | `src/backtest_diagnostics.py` | 91 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_readiness_report.md` | `src/universe_quality_review.py` | 47 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_summary.csv` | `dashboard/build_dashboard.py` | 4900 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_summary.csv` | `src/backtest_diagnostics.py` | 117 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_summary.csv` | `src/backtest_engine.py` | 687 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_symbol_contribution.csv` | `src/backtest_diagnostics.py` | 86 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_symbol_contribution.md` | `src/backtest_diagnostics.py` | 87 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_trade_distribution.csv` | `src/backtest_diagnostics.py` | 82 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_trade_distribution.md` | `src/backtest_diagnostics.py` | 83 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_trade_pool_report.md` | `src/backtest_engine.py` | 149 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_trades.csv` | `src/backtest_diagnostics.py` | 119 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trades.csv` | `src/backtest_engine.py` | 688 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_turnover_by_month.csv` | `src/backtest_diagnostics.py` | 77 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_turnover_diagnostics.md` | `src/backtest_diagnostics.py` | 79 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_yearly_summary.csv` | `src/backtest_diagnostics.py` | 121 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_yearly_summary.csv` | `src/backtest_engine.py` | 691 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `dashboard/build_dashboard.py` | 4406 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.csv` | `src/broad_base_balance_preview.py` | 44 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `dashboard/build_dashboard.py` | 4402 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.json` | `src/broad_base_balance_preview.py` | 45 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `src/etf_risk_profile.py` | 894 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `src/broad_base_balance_preview.py` | 46 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_report.md` | `src/buy_ranking.py` | 161 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.json` | `src/etf_risk_profile.py` | 88 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `src/etf_risk_profile.py` | 89 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `dashboard/app.py` | 88 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_signal_ranking.md` | `src/automation_nodes.py` | 420 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/buy_ranking.py` | 160 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/buy_ranking.py` | 161 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/buy_ranking.py` | 162 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/etf_risk_profile.py` | 1453 | `CONSUMER_READ` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `src/automation_scheduler.py` | 166 | `PRODUCER_WRITE` | `HIGH` |
| `reports/chatgpt_weekly_analysis_packet_latest.json` | `dashboard/build_dashboard.py` | 4730 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/chatgpt_weekly_analysis_packet_latest.json` | `dashboard/build_dashboard.py` | 4775 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/current_buy_top10_style_regime_fit.csv` | `src/style_regime_fit.py` | 119 | `PRODUCER_WRITE` | `HIGH` |
| `reports/current_buy_top10_style_regime_fit.json` | `dashboard/build_dashboard.py` | 4176 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/current_buy_top10_style_regime_fit.md` | `src/style_regime_fit.py` | 121 | `PRODUCER_WRITE` | `HIGH` |
| `reports/current_portfolio_style_regime_fit.json` | `dashboard/build_dashboard.py` | 4177 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/current_portfolio_style_regime_fit.md` | `src/style_regime_fit.py` | 123 | `PRODUCER_WRITE` | `HIGH` |
| `reports/current_positions_strategy_fit_report.md` | `src/next_stage_strategy_research.py` | 202 | `PRODUCER_WRITE` | `HIGH` |
| `reports/daily_rolling_backtest.csv` | `src/automation_nodes.py` | 187 | `PRODUCER_WRITE` | `HIGH` |
| `reports/daily_rolling_backtest.md` | `src/automation_nodes.py` | 209 | `PRODUCER_WRITE` | `HIGH` |
| `reports/daily_signal_{run_date}.md` | `src/reporting.py` | 203 | `PRODUCER_WRITE` | `HIGH` |
| `reports/daily_signal_{run_date}.md` | `src/reporting.py` | 204 | `CONSUMER_READ` | `HIGH` |
| `reports/dashboard_app_future_plan.md` | `src/paper_trade_engine.py` | 810 | `PRODUCER_WRITE` | `HIGH` |
| `reports/dashboard_data.json` | `app/backend/readers.py` | 151 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/dashboard_data.json` | `dashboard/build_dashboard.py` | 84 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_freshness_execution_reality.md` | `src/ranking_factor_diagnostics.py` | 87 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_provider_design.md` | `src/data_source_architecture_audit.py` | 38 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_provider_status.json` | `dashboard/build_dashboard.py` | 4553 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/data_provider_status.json` | `src/data_provider_status.py` | 39 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_provider_status.md` | `src/data_provider_status.py` | 40 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_architecture_audit.json` | `src/data_source_architecture_audit.py` | 36 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_architecture_audit.md` | `src/data_source_architecture_audit.py` | 37 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_status.json` | `app/backend/readers.py` | 163 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/data_source_status.json` | `dashboard/build_dashboard.py` | 3485 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/data_source_status.json` | `scripts/run_daily_close.sh` | 86 | `FILE_COPY_SOURCE` | `HIGH` |
| `reports/data_source_status.json` | `scripts/run_daily_close.sh` | 123 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_status.json` | `src/data_source_architecture_audit.py` | 54 | `CONSUMER_READ` | `HIGH` |
| `reports/data_source_status.json` | `src/data_sources/source_router.py` | 287 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_status_report.md` | `scripts/run_daily_close.sh` | 87 | `FILE_COPY_SOURCE` | `HIGH` |
| `reports/data_source_status_report.md` | `scripts/run_daily_close.sh` | 124 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_source_status_report.md` | `src/data_sources/source_router.py` | 312 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_update_diagnosis_report.md` | `scripts/update_etf_data.py` | 1176 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_update_status.baostock_fallback.json` | `src/data_sources/source_router.py` | 165 | `CONSUMER_READ` | `HIGH` |
| `reports/data_update_status.json` | `app/backend/readers.py` | 158 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/data_update_status.json` | `app/backend/task_runner.py` | 213 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/data_update_status.json` | `dashboard/build_dashboard.py` | 3465 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/data_update_status.json` | `scripts/run_daily_close.sh` | 88 | `FILE_COPY_SOURCE` | `HIGH` |
| `reports/data_update_status.json` | `scripts/run_daily_close.sh` | 125 | `PRODUCER_WRITE` | `HIGH` |
| `reports/data_update_status.json` | `src/data_source_architecture_audit.py` | 55 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_classification_report.md` | `src/etf_classifier.py` | 165 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_expansion_import_report.md` | `scripts/build_etf_expansion_plan.py` | 323 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_expansion_import_report.md` | `scripts/import_jqdata_staging.py` | 100 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_expansion_import_results.csv` | `dashboard/build_dashboard.py` | 3458 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/etf_expansion_import_results.csv` | `scripts/import_jqdata_staging.py` | 101 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_expansion_import_results.csv` | `scripts/run_etf_expansion_data_pipeline.py` | 154 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_expansion_import_results.csv` | `scripts/run_etf_expansion_data_pipeline.py` | 162 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_expansion_pipeline_report.md` | `scripts/run_etf_expansion_data_pipeline.py` | 253 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_expansion_staging_validation_report.md` | `scripts/build_etf_expansion_plan.py` | 305 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_pool_expansion_plan.md` | `scripts/build_etf_expansion_plan.py` | 282 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/etf_risk_profile.py` | 69 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/etf_style_profile.py` | 269 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/market_regime_replay.py` | 647 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/market_regime_stabilization.py` | 838 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/style_fit_robustness.py` | 150 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_risk_profile.csv` | `src/style_regime_fit.py` | 851 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_risk_profile.json` | `dashboard/build_dashboard.py` | 5390 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/etf_risk_profile.json` | `src/etf_risk_profile.py` | 70 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile.md` | `src/etf_risk_profile.py` | 71 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile_consistency_audit.json` | `src/etf_risk_profile.py` | 92 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile_consistency_audit.md` | `src/etf_risk_profile.py` | 93 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile_source_audit.json` | `src/etf_risk_profile.py` | 84 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_risk_profile_source_audit.md` | `src/etf_risk_profile.py` | 85 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_rotation_exit_rule_research.md` | `src/exit_rule_candidates.py` | 67 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_rotation_mature_model_reference.md` | `src/ranking_model_v2_backtest.py` | 152 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_rotation_strategy_research.md` | `src/universe_quality_review.py` | 46 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_style_unknown_audit.csv` | `src/etf_risk_profile.py` | 75 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_style_unknown_audit.md` | `src/etf_risk_profile.py` | 76 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_type_aware_model_metrics.json` | `src/etf_type_aware_model_research.py` | 43 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_type_aware_model_research.md` | `src/etf_type_aware_model_research.py` | 44 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_type_aware_model_summary.csv` | `src/etf_type_aware_model_research.py` | 33 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_type_classification_report.md` | `src/etf_classifier.py` | 166 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_volatility_profile.csv` | `src/etf_volatility_profile.py` | 56 | `PRODUCER_WRITE` | `HIGH` |
| `reports/etf_volatility_profile.csv` | `src/exit_rule_candidates.py` | 81 | `CONSUMER_READ` | `HIGH` |
| `reports/etf_volatility_profile.md` | `src/etf_volatility_profile.py` | 57 | `PRODUCER_WRITE` | `HIGH` |
| `reports/execution_layer_integration_plan.md` | `src/model_research_quality_review.py` | 36 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_backtest_design.md` | `src/exit_rule_candidates.py` | 69 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_by_etf_type.md` | `src/exit_rule_candidates.py` | 68 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_candidates.json` | `dashboard/build_dashboard.py` | 4842 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/exit_rule_candidates.json` | `src/exit_rule_candidates.py` | 65 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_candidates.md` | `src/exit_rule_candidates.py` | 66 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_research.csv` | `src/exit_rule_research.py` | 39 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_research.csv` | `src/model_research_quality_review.py` | 44 | `CONSUMER_READ` | `HIGH` |
| `reports/exit_rule_research_report.md` | `src/exit_rule_research.py` | 41 | `PRODUCER_WRITE` | `HIGH` |
| `reports/exit_rule_research_results.csv` | `src/exit_rule_research.py` | 40 | `PRODUCER_WRITE` | `HIGH` |
| `reports/file_classification_plan.csv` | `scripts/project_hygiene_audit.py` | 538 | `PRODUCER_WRITE` | `HIGH` |
| `reports/file_classification_plan.json` | `scripts/project_hygiene_audit.py` | 539 | `PRODUCER_WRITE` | `HIGH` |
| `reports/file_classification_plan.md` | `scripts/project_hygiene_audit.py` | 576 | `PRODUCER_WRITE` | `HIGH` |
| `reports/first_paper_buy_plan.md` | `dashboard/app.py` | 72 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/first_paper_buy_plan.md` | `src/buy_ranking.py` | 307 | `PRODUCER_WRITE` | `HIGH` |
| `reports/high_beta_risk_watch.csv` | `dashboard/build_dashboard.py` | 4359 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/high_beta_risk_watch.csv` | `src/high_beta_risk_watch.py` | 47 | `PRODUCER_WRITE` | `HIGH` |
| `reports/high_beta_risk_watch.json` | `dashboard/build_dashboard.py` | 4355 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/high_beta_risk_watch.json` | `src/broad_base_balance_preview.py` | 60 | `CONSUMER_READ` | `HIGH` |
| `reports/high_beta_risk_watch.json` | `src/etf_risk_profile.py` | 893 | `CONSUMER_READ` | `HIGH` |
| `reports/high_beta_risk_watch.json` | `src/high_beta_risk_watch.py` | 48 | `PRODUCER_WRITE` | `HIGH` |
| `reports/high_beta_risk_watch.md` | `src/high_beta_risk_watch.py` | 49 | `PRODUCER_WRITE` | `HIGH` |
| `reports/holding_period_research.csv` | `src/holding_period_research.py` | 29 | `PRODUCER_WRITE` | `HIGH` |
| `reports/holding_period_research.csv` | `src/model_research_quality_review.py` | 43 | `CONSUMER_READ` | `HIGH` |
| `reports/holding_period_research_report.md` | `src/holding_period_research.py` | 31 | `PRODUCER_WRITE` | `HIGH` |
| `reports/holding_period_research_results.csv` | `src/holding_period_research.py` | 30 | `PRODUCER_WRITE` | `HIGH` |
| `reports/intelligence_data_source_plan.md` | `src/data_source_architecture_audit.py` | 39 | `PRODUCER_WRITE` | `HIGH` |
| `reports/jqdata_import_report.md` | `scripts/import_jqdata_staging.py` | 99 | `PRODUCER_WRITE` | `HIGH` |
| `reports/jqdata_local_compare_report.md` | `scripts/compare_jqdata_with_local.py` | 55 | `PRODUCER_WRITE` | `HIGH` |
| `reports/jqdata_unit_diagnosis_report.md` | `scripts/diagnose_jqdata_units.py` | 60 | `PRODUCER_WRITE` | `HIGH` |
| `reports/latest_buy_ranking.md` | `dashboard/app.py` | 88 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_buy_ranking.md` | `src/buy_ranking.py` | 162 | `PRODUCER_WRITE` | `HIGH` |
| `reports/latest_data_coverage.md` | `app/backend/readers.py` | 482 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_data_coverage.md` | `dashboard/app.py` | 64 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_data_health.md` | `app/backend/readers.py` | 483 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_data_health.md` | `dashboard/app.py` | 66 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_data_health.md` | `dashboard/build_dashboard.py` | 3396 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/latest_data_health.md` | `src/automation_nodes.py` | 494 | `CONSUMER_READ` | `HIGH` |
| `reports/latest_data_health.md` | `src/market_state.py` | 189 | `CONSUMER_READ` | `HIGH` |
| `reports/latest_data_health.md` | `src/persistence_breakout_shadow.py` | 442 | `CONSUMER_READ` | `HIGH` |
| `reports/launchd_catchup_upgrade_report.md` | `src/automation_scheduler.py` | 251 | `PRODUCER_WRITE` | `HIGH` |
| `reports/manual_import_report.md` | `scripts/import_manual_csv.py` | 73 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_breadth_regime_analysis.json` | `dashboard/build_dashboard.py` | 4057 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/market_breadth_regime_analysis.json` | `src/market_regime_replay.py` | 105 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_breadth_regime_analysis.md` | `src/market_regime_replay.py` | 106 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_audit_decision.json` | `dashboard/build_dashboard.py` | 4054 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/market_regime_audit_decision.json` | `src/market_regime_replay.py` | 109 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_audit_decision.md` | `src/market_regime_replay.py` | 110 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_distribution.json` | `dashboard/build_dashboard.py` | 4052 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/market_regime_distribution.json` | `src/market_regime_replay.py` | 77 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_distribution.md` | `src/market_regime_replay.py` | 78 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_replay.json` | `src/market_regime_replay.py` | 73 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_replay.md` | `src/market_regime_replay.py` | 74 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_source_audit.json` | `src/market_regime_replay.py` | 116 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_source_audit.md` | `src/market_regime_replay.py` | 117 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_stability.json` | `dashboard/build_dashboard.py` | 4053 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/market_regime_stability.json` | `src/market_regime_replay.py` | 81 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_stability.md` | `src/market_regime_replay.py` | 82 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_stabilization.csv` | `src/market_regime_stabilization.py` | 88 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_stabilization.json` | `src/market_regime_stabilization.py` | 89 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_regime_stabilization.md` | `src/market_regime_stabilization.py` | 90 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_state.csv` | `dashboard/build_dashboard.py` | 4031 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/market_state.csv` | `src/market_state.py` | 37 | `PRODUCER_WRITE` | `HIGH` |
| `reports/market_state.csv` | `src/model_research_quality_review.py` | 46 | `CONSUMER_READ` | `HIGH` |
| `reports/market_state.csv` | `src/paper_trade_engine.py` | 1045 | `CONSUMER_READ` | `HIGH` |
| `reports/market_state.csv` | `src/strategy_enhancement_preview.py` | 378 | `CONSUMER_READ` | `HIGH` |
| `reports/market_state.csv` | `src/strategy_preview_tracking.py` | 573 | `CONSUMER_READ` | `HIGH` |
| `reports/market_state_report.md` | `src/market_state.py` | 38 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_by_filter_reason.csv` | `src/missed_opportunity_tracker.py` | 64 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_by_filter_reason.md` | `src/missed_opportunity_tracker.py` | 70 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_observation_rules.md` | `src/missed_opportunity_tracker.py` | 73 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_tracker.csv` | `src/missed_opportunity_tracker.py` | 62 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_tracker.json` | `dashboard/build_dashboard.py` | 4662 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/missed_opportunity_tracker.json` | `dashboard/build_dashboard.py` | 4692 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/missed_opportunity_tracker.json` | `src/missed_opportunity_tracker.py` | 67 | `PRODUCER_WRITE` | `HIGH` |
| `reports/missed_opportunity_tracker.md` | `src/missed_opportunity_tracker.py` | 69 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_enhancement_decision_report.md` | `src/ranking_factor_diagnostics.py` | 94 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_overfit_guardrails.md` | `src/v2_underperformance_attribution.py` | 36 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_research_quality_review.json` | `dashboard/build_dashboard.py` | 5429 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/model_research_quality_review.json` | `src/model_research_quality_review.py` | 34 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_research_quality_review.json` | `src/paper_trade_engine.py` | 1101 | `CONSUMER_READ` | `HIGH` |
| `reports/model_research_quality_review.json` | `src/strategy_enhancement_preview.py` | 399 | `CONSUMER_READ` | `HIGH` |
| `reports/model_research_quality_review.md` | `src/model_research_quality_review.py` | 35 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_shadow_comparison.csv` | `src/persistence_breakout_shadow.py` | 71 | `PRODUCER_WRITE` | `HIGH` |
| `reports/model_shadow_comparison.csv` | `src/shadow_observation_weekly.py` | 33 | `CONSUMER_READ` | `HIGH` |
| `reports/model_shadow_comparison.md` | `src/persistence_breakout_shadow.py` | 75 | `PRODUCER_WRITE` | `HIGH` |
| `reports/monthly_model_review.md` | `src/automation_nodes.py` | 295 | `PRODUCER_WRITE` | `HIGH` |
| `reports/news_data_source_plan.md` | `src/next_stage_strategy_research.py` | 149 | `PRODUCER_WRITE` | `HIGH` |
| `reports/news_sentiment_framework.md` | `src/next_stage_strategy_research.py` | 124 | `PRODUCER_WRITE` | `HIGH` |
| `reports/next_stage_strategy_optimization_report.md` | `src/next_stage_strategy_research.py` | 302 | `PRODUCER_WRITE` | `HIGH` |
| `reports/no_lookahead_data_rules.md` | `src/data_source_architecture_audit.py` | 40 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_equity_curve.md` | `src/paper_performance.py` | 663 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_equity_curve_backfill_audit.md` | `src/paper_equity_backfill.py` | 384 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_equity_curve_backfilled.md` | `src/paper_equity_backfill.py` | 337 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_equity_curve_gap_explanation.md` | `src/paper_equity_backfill.py` | 295 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_execution_stale_trade_audit_{audit_date.isoformat()}.json` | `src/execution/paper_freshness_gate.py` | 386 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_execution_stale_trade_audit_{audit_date.isoformat()}.md` | `src/execution/paper_freshness_gate.py` | 413 | `PRODUCER_WRITE` | `HIGH` |
| `reports/paper_performance_daily.csv` | `dashboard/build_dashboard.py` | 3098 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/paper_performance_daily.csv` | `src/paper_performance.py` | 61 | `PRODUCER_WRITE` | `HIGH` |

完整逐行 Registry 见同业务日期的 CSV/JSON 机器产物。
