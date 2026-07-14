# Report Dependency Registry

本文件由 `scripts/governance/build_report_dependency_registry.py` 生成。扫描只读取可识别的静态/动态路径表达式；动态模式不会被伪造成具体文件依赖。

## Summary

- Registry records: 5999
- Distinct referenced paths/patterns: 719
- Dynamic patterns: 23
- Registry SHA-256: `a815a079f5ef50ce04cdc38ced445556976d0e6a0b0fcad7b7506ef0f5cadf53`

### Reference types

- `APP_RUNTIME_READ`: 43
- `CONSUMER_READ`: 624
- `DASHBOARD_RUNTIME_READ`: 369
- `DOCUMENTATION_LINK`: 3618
- `DYNAMIC_PATH_PATTERN`: 23
- `PRODUCER_WRITE`: 1015
- `STATE_INDEX_REFERENCE`: 213
- `TEST_REFERENCE`: 23
- `UNKNOWN_REFERENCE`: 71

### Migration impact

- `CRITICAL`: 412
- `HIGH`: 1639
- `LOW`: 3689
- `MEDIUM`: 259

## Critical and high-impact references

| Referenced report | Source | Line | Type | Impact |
| --- | --- | ---: | --- | --- |
| `reports/account_status.csv` | `src/config.py` | 19 | `CONSUMER_READ` | `HIGH` |
| `reports/adjusted_preview.csv` | `dashboard/index.html` | 768 | `PRODUCER_WRITE` | `HIGH` |
| `reports/adjusted_preview.csv` | `src/chatgpt_weekly_packet.py` | 50 | `CONSUMER_READ` | `HIGH` |
| `reports/afternoon_open_check.json` | `src/automation_nodes.py` | 44 | `CONSUMER_READ` | `HIGH` |
| `reports/afternoon_open_check.md` | `dashboard/build_dashboard.py` | 3299 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/afternoon_open_check.md` | `dashboard/index.html` | 652 | `PRODUCER_WRITE` | `HIGH` |
| `reports/afternoon_open_check.md` | `reports/path_dependency_audit.json` | 2742 | `PRODUCER_WRITE` | `HIGH` |
| `reports/afternoon_open_check.md` | `src/automation_nodes.py` | 43 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.json` | `dashboard/build_dashboard.py` | 4530 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/akshare_connectivity_check.json` | `src/akshare_connectivity_check.py` | 23 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.json` | `src/data_provider_status.py` | 52 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.json` | `src/data_source_architecture_audit.py` | 56 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `dashboard/build_dashboard.py` | 2310 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `dashboard/build_dashboard.py` | 3710 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/akshare_connectivity_check.md` | `dashboard/build_dashboard.py` | 4543 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/akshare_connectivity_check.md` | `dashboard/index.html` | 708 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `dashboard/index.html` | 919 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `dashboard/index.html` | 922 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `reports/path_dependency_audit.json` | 3042 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `reports/path_dependency_audit.json` | 3048 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `reports/path_dependency_audit.json` | 4392 | `PRODUCER_WRITE` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `src/akshare_connectivity_check.py` | 24 | `CONSUMER_READ` | `HIGH` |
| `reports/akshare_connectivity_check.md` | `src/data_source_architecture_audit.py` | 146 | `CONSUMER_READ` | `HIGH` |
| `reports/alpha_factor_enhancement_metrics.json` | `src/alpha_factor_enhancement_research.py` | 21 | `CONSUMER_READ` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/build_dashboard.py` | 2378 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/build_dashboard.py` | 3724 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/build_dashboard.py` | 4596 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/build_dashboard.py` | 4617 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/index.html` | 728 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/index.html` | 975 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `dashboard/index.html` | 978 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `reports/path_dependency_audit.json` | 3210 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `reports/path_dependency_audit.json` | 3216 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `reports/path_dependency_audit.json` | 4464 | `PRODUCER_WRITE` | `HIGH` |
| `reports/alpha_factor_enhancement_research.md` | `src/alpha_factor_enhancement_research.py` | 19 | `CONSUMER_READ` | `HIGH` |
| `reports/alpha_factor_enhancement_summary.csv` | `src/alpha_factor_enhancement_research.py` | 20 | `CONSUMER_READ` | `HIGH` |
| `reports/app_launch_diagnostics.json` | `app/backend/readers.py` | 232 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_launch_diagnostics.json` | `dashboard/build_dashboard.py` | 3681 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/app_launch_diagnostics.json` | `scripts/diagnose_app_launch.sh` | 22 | `PRODUCER_WRITE` | `HIGH` |
| `reports/app_launch_diagnostics.json` | `tests/test_report_governance.py` | 49 | `PRODUCER_WRITE` | `HIGH` |
| `reports/app_launch_diagnostics.md` | `scripts/diagnose_app_launch.sh` | 23 | `PRODUCER_WRITE` | `HIGH` |
| `reports/app_task_status.json` | `app/backend/readers.py` | 224 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_task_status.json` | `app/backend/task_runner.py` | 18 | `APP_RUNTIME_READ` | `CRITICAL` |
| `reports/app_task_status.json` | `dashboard/build_dashboard.py` | 175 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/archive/` | `scripts/archive_low_risk_reports.py` | 3 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/` | `scripts/archive_low_risk_reports.py` | 359 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/` | `scripts/project_hygiene_audit.py` | 281 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/` | `scripts/project_hygiene_audit.py` | 651 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/audit_history/` | `scripts/archive_low_risk_reports.py` | 440 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/chatgpt_packets/` | `scripts/archive_low_risk_reports.py` | 362 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/chatgpt_packets/` | `scripts/archive_low_risk_reports.py` | 438 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/daily/` | `scripts/archive_low_risk_reports.py` | 360 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/daily/` | `scripts/archive_low_risk_reports.py` | 436 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/legacy_misc/` | `scripts/archive_low_risk_reports.py` | 364 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/legacy_misc/` | `scripts/archive_low_risk_reports.py` | 441 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/research_phases/` | `scripts/archive_low_risk_reports.py` | 363 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/research_phases/` | `scripts/archive_low_risk_reports.py` | 439 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/weekly/` | `scripts/archive_low_risk_reports.py` | 361 | `CONSUMER_READ` | `HIGH` |
| `reports/archive/weekly/` | `scripts/archive_low_risk_reports.py` | 437 | `CONSUMER_READ` | `HIGH` |
| `reports/archive_candidate_list.csv` | `scripts/archive_low_risk_reports.py` | 289 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_candidate_list.json` | `scripts/archive_low_risk_reports.py` | 291 | `CONSUMER_READ` | `HIGH` |
| `reports/archive_candidate_list.md` | `dashboard/build_dashboard.py` | 3702 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/archive_candidate_list.md` | `dashboard/index.html` | 887 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_candidate_list.md` | `dashboard/index.html` | 890 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_candidate_list.md` | `scripts/archive_low_risk_reports.py` | 303 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_after.json` | `scripts/archive_low_risk_reports.py` | 467 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_after.md` | `dashboard/build_dashboard.py` | 3704 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/archive_manifest_after.md` | `dashboard/index.html` | 895 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_after.md` | `dashboard/index.html` | 898 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_after.md` | `scripts/archive_low_risk_reports.py` | 468 | `CONSUMER_READ` | `HIGH` |
| `reports/archive_manifest_before.json` | `scripts/archive_low_risk_reports.py` | 459 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_before.md` | `dashboard/build_dashboard.py` | 3703 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/archive_manifest_before.md` | `dashboard/index.html` | 891 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_before.md` | `dashboard/index.html` | 894 | `PRODUCER_WRITE` | `HIGH` |
| `reports/archive_manifest_before.md` | `scripts/archive_low_risk_reports.py` | 460 | `CONSUMER_READ` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `dashboard/build_dashboard.py` | 2685 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `dashboard/build_dashboard.py` | 3801 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/automation_four_node_sync_report.md` | `dashboard/index.html` | 840 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `dashboard/index.html` | 1283 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `dashboard/index.html` | 1286 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `reports/path_dependency_audit.json` | 2916 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `reports/path_dependency_audit.json` | 3786 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `reports/path_dependency_audit.json` | 3792 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `reports/path_dependency_audit.json` | 4662 | `PRODUCER_WRITE` | `HIGH` |
| `reports/automation_four_node_sync_report.md` | `src/automation_nodes.py` | 346 | `CONSUMER_READ` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `dashboard/build_dashboard.py` | 1645 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `dashboard/build_dashboard.py` | 3778 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/b1_strategy_enhancement_preview_report.md` | `dashboard/index.html` | 507 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `dashboard/index.html` | 1191 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `dashboard/index.html` | 1194 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `reports/path_dependency_audit.json` | 3498 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `reports/path_dependency_audit.json` | 3504 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `reports/path_dependency_audit.json` | 4266 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b1_strategy_enhancement_preview_report.md` | `src/strategy_enhancement_preview.py` | 29 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report` | `reports/path_dependency_audit.json` | 4290 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `dashboard/build_dashboard.py` | 1763 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `dashboard/build_dashboard.py` | 3781 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/b2_strategy_preview_tracking_report.md` | `dashboard/index.html` | 527 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `dashboard/index.html` | 1203 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `dashboard/index.html` | 1206 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `reports/path_dependency_audit.json` | 3534 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `reports/path_dependency_audit.json` | 3540 | `PRODUCER_WRITE` | `HIGH` |
| `reports/b2_strategy_preview_tracking_report.md` | `src/strategy_preview_tracking.py` | 31 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_capital_sensitivity.csv` | `src/backtest_diagnostics.py` | 41 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_capital_sensitivity.md` | `dashboard/build_dashboard.py` | 5018 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_capital_sensitivity.md` | `dashboard/build_dashboard.py` | 5050 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_capital_sensitivity.md` | `dashboard/index.html` | 605 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_capital_sensitivity.md` | `reports/path_dependency_audit.json` | 6144 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_capital_sensitivity.md` | `src/backtest_diagnostics.py` | 40 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_consistency_check.json` | `src/backtest_diagnostics.py` | 39 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_consistency_check.md` | `dashboard/build_dashboard.py` | 5017 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_consistency_check.md` | `dashboard/build_dashboard.py` | 5049 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_consistency_check.md` | `dashboard/index.html` | 605 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_consistency_check.md` | `reports/path_dependency_audit.json` | 6138 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_consistency_check.md` | `src/backtest_diagnostics.py` | 38 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_cost_diagnostics.csv` | `src/backtest_diagnostics.py` | 43 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_cost_diagnostics.md` | `dashboard/build_dashboard.py` | 5019 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_cost_diagnostics.md` | `dashboard/build_dashboard.py` | 5051 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_cost_diagnostics.md` | `dashboard/index.html` | 605 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_cost_diagnostics.md` | `reports/path_dependency_audit.json` | 6150 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_cost_diagnostics.md` | `src/backtest_diagnostics.py` | 42 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_diagnostics_summary.json` | `dashboard/build_dashboard.py` | 4988 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_diagnostics_summary.json` | `src/backtest_diagnostics.py` | 56 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_drawdown_diagnostics.csv` | `src/backtest_diagnostics.py` | 54 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_drawdown_diagnostics.md` | `src/backtest_diagnostics.py` | 53 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `dashboard/build_dashboard.py` | 4945 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_equity_curve.csv` | `dashboard/build_dashboard.py` | 4982 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `dashboard/index.html` | 602 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `reports/path_dependency_audit.json` | 6102 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `src/backtest_diagnostics.py` | 118 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_equity_curve.csv` | `src/backtest_engine.py` | 33 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_execution_timing_sensitivity.csv` | `src/ranking_factor_diagnostics.py` | 36 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_execution_timing_sensitivity.md` | `dashboard/build_dashboard.py` | 5096 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_execution_timing_sensitivity.md` | `src/ranking_factor_diagnostics.py` | 37 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_exit_reason_summary.csv` | `src/backtest_diagnostics.py` | 46 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_expand_pool_decision.md` | `dashboard/build_dashboard.py` | 5016 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_expand_pool_decision.md` | `dashboard/build_dashboard.py` | 5053 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_expand_pool_decision.md` | `dashboard/index.html` | 605 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_expand_pool_decision.md` | `reports/path_dependency_audit.json` | 6162 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_expand_pool_decision.md` | `src/backtest_diagnostics.py` | 55 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_metrics.json` | `dashboard/build_dashboard.py` | 4899 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_metrics.json` | `src/backtest_diagnostics.py` | 122 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_metrics.json` | `src/backtest_engine.py` | 35 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_phase4a_report.md` | `dashboard/build_dashboard.py` | 4943 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_phase4a_report.md` | `dashboard/build_dashboard.py` | 4980 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_phase4a_report.md` | `dashboard/index.html` | 602 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_phase4a_report.md` | `reports/path_dependency_audit.json` | 6090 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_phase4a_report.md` | `src/backtest_engine.py` | 30 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_positions.csv` | `src/backtest_diagnostics.py` | 120 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_positions.csv` | `src/backtest_engine.py` | 34 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_ranking_effectiveness.csv` | `src/backtest_diagnostics.py` | 52 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_ranking_effectiveness.md` | `dashboard/build_dashboard.py` | 5020 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_ranking_effectiveness.md` | `dashboard/build_dashboard.py` | 5052 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_ranking_effectiveness.md` | `dashboard/index.html` | 605 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_ranking_effectiveness.md` | `reports/path_dependency_audit.json` | 6156 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_ranking_effectiveness.md` | `src/backtest_diagnostics.py` | 51 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_readiness_report.md` | `dashboard/build_dashboard.py` | 2282 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_readiness_report.md` | `dashboard/build_dashboard.py` | 4472 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_readiness_report.md` | `dashboard/build_dashboard.py` | 4522 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_readiness_report.md` | `dashboard/index.html` | 596 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_readiness_report.md` | `reports/path_dependency_audit.json` | 4380 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_readiness_report.md` | `src/universe_quality_review.py` | 28 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_result.csv` | `src/config.py` | 22 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_summary.csv` | `dashboard/build_dashboard.py` | 4900 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_summary.csv` | `dashboard/build_dashboard.py` | 4944 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/backtest_summary.csv` | `dashboard/build_dashboard.py` | 4981 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_summary.csv` | `dashboard/index.html` | 602 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_summary.csv` | `reports/path_dependency_audit.json` | 6096 | `PRODUCER_WRITE` | `HIGH` |
| `reports/backtest_summary.csv` | `src/backtest_diagnostics.py` | 117 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_summary.csv` | `src/backtest_engine.py` | 31 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_summary.md` | `src/config.py` | 23 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_symbol_contribution.csv` | `src/backtest_diagnostics.py` | 50 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_symbol_contribution.md` | `src/backtest_diagnostics.py` | 49 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trade_distribution.csv` | `src/backtest_diagnostics.py` | 48 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trade_distribution.md` | `src/backtest_diagnostics.py` | 47 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trade_pool_report.md` | `src/backtest_engine.py` | 28 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trades.csv` | `src/backtest_diagnostics.py` | 119 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_trades.csv` | `src/backtest_engine.py` | 32 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_turnover_by_month.csv` | `src/backtest_diagnostics.py` | 45 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_turnover_diagnostics.md` | `src/backtest_diagnostics.py` | 44 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_yearly_summary.csv` | `src/backtest_diagnostics.py` | 121 | `CONSUMER_READ` | `HIGH` |
| `reports/backtest_yearly_summary.csv` | `src/backtest_engine.py` | 36 | `CONSUMER_READ` | `HIGH` |
| `reports/benchmark_redundancy_analysis.md` | `src/exposure/market_exposure_vector.py` | 76 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `dashboard/build_dashboard.py` | 1689 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `dashboard/build_dashboard.py` | 4406 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.csv` | `dashboard/index.html` | 517 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `reports/path_dependency_audit.json` | 4278 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `reports/path_dependency_audit.json` | 4284 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.csv` | `src/broad_base_balance_preview.py` | 26 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `dashboard/build_dashboard.py` | 4402 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.json` | `scripts/project_hygiene_audit.py` | 516 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `src/broad_base_balance_preview.py` | 27 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `src/chatgpt_weekly_packet.py` | 37 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `src/chatgpt_weekly_packet.py` | 161 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.json` | `src/etf_risk_profile.py` | 894 | `CONSUMER_READ` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `dashboard/build_dashboard.py` | 1689 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `dashboard/build_dashboard.py` | 3777 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.md` | `dashboard/build_dashboard.py` | 4404 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.md` | `dashboard/build_dashboard.py` | 4423 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.md` | `dashboard/build_dashboard.py` | 4443 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/broad_base_balance_preview.md` | `dashboard/index.html` | 517 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `dashboard/index.html` | 1187 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `dashboard/index.html` | 1190 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 3474 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 3480 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 3486 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 3492 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 4278 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `reports/path_dependency_audit.json` | 4284 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `src/broad_base_balance_preview.py` | 28 | `PRODUCER_WRITE` | `HIGH` |
| `reports/broad_base_balance_preview.md` | `src/chatgpt_weekly_packet.py` | 38 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_ranking_report.md` | `src/buy_ranking.py` | 18 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.json` | `src/etf_risk_profile.py` | 41 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/build_dashboard.py` | 3740 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/build_dashboard.py` | 5368 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/build_dashboard.py` | 5395 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/index.html` | 614 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/index.html` | 1039 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `dashboard/index.html` | 1042 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_ranking_risk_profile_analysis.md` | `src/etf_risk_profile.py` | 40 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `dashboard/app.py` | 88 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_signal_ranking.md` | `dashboard/build_dashboard.py` | 2823 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_signal_ranking.md` | `dashboard/build_dashboard.py` | 3772 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/buy_signal_ranking.md` | `dashboard/index.html` | 1167 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `dashboard/index.html` | 1170 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `reports/app_task_status.json` | 183 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `reports/dashboard_data.json` | 269 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `reports/path_dependency_audit.json` | 3414 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `reports/path_dependency_audit.json` | 3420 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `scripts/project_hygiene_audit.py` | 737 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/automation_nodes.py` | 417 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/broad_base_balance_preview.py` | 20 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/buy_ranking.py` | 17 | `PRODUCER_WRITE` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/etf_risk_profile.py` | 1450 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/market_state.py` | 16 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/paper_trade_engine.py` | 55 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/sell_signal_review.py` | 22 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/strategy_enhancement_preview.py` | 20 | `CONSUMER_READ` | `HIGH` |
| `reports/buy_signal_ranking.md` | `src/style_regime_fit.py` | 662 | `CONSUMER_READ` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `dashboard/build_dashboard.py` | 3296 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/catchup_scheduler_status.md` | `dashboard/build_dashboard.py` | 3802 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |
| `reports/catchup_scheduler_status.md` | `dashboard/index.html` | 631 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `dashboard/index.html` | 1287 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `dashboard/index.html` | 1290 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `reports/path_dependency_audit.json` | 2724 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `reports/path_dependency_audit.json` | 3798 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `reports/path_dependency_audit.json` | 3804 | `PRODUCER_WRITE` | `HIGH` |
| `reports/catchup_scheduler_status.md` | `src/automation_scheduler.py` | 22 | `PRODUCER_WRITE` | `HIGH` |
| `reports/chatgpt_weekly_analysis_packet_latest.json` | `dashboard/build_dashboard.py` | 2518 | `PRODUCER_WRITE` | `HIGH` |
| `reports/chatgpt_weekly_analysis_packet_latest.json` | `dashboard/build_dashboard.py` | 4729 | `DASHBOARD_RUNTIME_READ` | `CRITICAL` |

完整逐行 registry 见 `reports/report_dependency_registry.csv` 和 `reports/report_dependency_registry.json`。
