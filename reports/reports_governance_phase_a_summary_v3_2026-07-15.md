---
report_id: report_74b85c27586468f6
report_type: GOVERNANCE_PHASE_SUMMARY
business_date: 2026-07-15
created_at: 2026-07-15T17:57:57+08:00
status: REMEDIATED_PENDING_FINAL_RESULT_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-evidence-archive-v3-2026-07-15
retention_class: PERMANENT
schema_version: 3
snapshot_revision: v3
immutable: true
evidence_registry_version: v1
classification_schema_version: 3
supersedes: reports/reports_governance_phase_a_summary_v2_2026-07-15.md
---
# Reports Governance Phase A Summary

## State

- PR #4: `DRAFT_AWAITING_FINAL_RESULT_RE_QC`
- Reports Governance Phase A: `REMEDIATED`
- Governance Evidence Registry: `IMPLEMENTED_PENDING_QC`
- Evidence Traceability: `COMPLETE_PENDING_QC`
- Already Archived Classification: `IMPLEMENTED_PENDING_QC`
- Migration Eligibility: `REBUILT_PENDING_QC`
- Deletion Eligibility: `UNCHANGED_CONSERVATIVE`
- Snapshot Immutability: `ENFORCED`
- Phase B Contract: `COMPLETE`
- Reports Migration Phase B: `BLOCKED`
- Runtime Path Registry: `NOT_STARTED`
- Availability Audit: `ACTIVE_COLLECTING`
- Availability temporary data: `RETAIN_UNTIL_MIGRATION_VALIDATED`

## Inventory

- Catalog records: 645
- Dependency records: 6390
- Evidence records: 2151
- Dynamic patterns: 126
- Runtime locked: 108
- Current aliases: 36
- Unknown roles: 148
- Concrete active dynamic Producer matches: 12
- Deprecated Archive Candidate true count: 0
- Safe to delete after authorization: 0
- Safe to migrate: 5
- Safe to migrate with rename: 87
- Already archived / migration not applicable: 45
- Phase B candidates: 92

### Location status

- `ACTIVE_ROOT`: 534
- `ACTIVE_SUBDIRECTORY`: 30
- `ALREADY_ARCHIVED`: 45
- `RUNTIME_ALIAS_LOCATION`: 36

### Dependency safety

- `ACTIVE_PRODUCER`: 262
- `NO_ACTIVE_DEPENDENCY`: 275
- `RUNTIME_LOCKED`: 108

### Naming status

- `COMPLIANT_DATED`: 12
- `LEGACY_STABLE_ALIAS`: 36
- `NEEDS_DATE_NORMALIZATION`: 323
- `NOT_APPLICABLE`: 126
- `UNKNOWN`: 148

### Retention status

- `MANUAL_REVIEW`: 389
- `PERMANENT`: 75
- `PROJECT_LIFETIME`: 169
- `ROLLING_WINDOW`: 12

### Migration eligibility

- `MIGRATION_BLOCKED_ACTIVE_DEPENDENCY`: 250
- `MIGRATION_BLOCKED_RETENTION`: 58
- `MIGRATION_BLOCKED_RUNTIME`: 128
- `MIGRATION_BLOCKED_UNKNOWN`: 72
- `MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED`: 45
- `SAFE_TO_MIGRATE`: 5
- `SAFE_TO_MIGRATE_RENAME_REQUIRED`: 87

### Deletion eligibility

- `DELETION_BLOCKED`: 450
- `DELETION_REVIEW_REQUIRED`: 92
- `NOT_DELETION_CANDIDATE`: 103

### Classification reasons

- `ACTIVE_AUDIT_ARTIFACT`: 50
- `ACTIVE_DYNAMIC_PRODUCER`: 12
- `ACTIVE_STATIC_PRODUCER`: 332
- `ALREADY_ARCHIVED_LOCATION`: 45
- `CURRENT_ALIAS`: 36
- `NEEDS_DATE_NORMALIZATION`: 323
- `NO_ACTIVE_DEPENDENCY`: 275
- `RETENTION_BLOCKED`: 244
- `RETENTION_REVIEW_REQUIRED`: 401
- `RUNTIME_CONSUMER`: 108
- `STATE_OR_GOVERNANCE_LOCKED`: 75
- `UNKNOWN_ROLE`: 148

## Governance meaning

The deprecated single `archive_candidate` flag is retained only as a compatibility field and is always false. Migration eligibility and deletion eligibility are independent. A naming defect can require a rename without fabricating an active dependency, while active static or dynamic Producers still block migration. Phase A never grants automatic deletion safety.

The complete App, Dashboard, automation, Work/Codex, deprecated-path, compatibility-period, consumer-completeness and rollback contract is stored in repository governance documents. This summary does not start Phase B or a runtime Path Registry.

## Phase B candidate input

Only `SAFE_TO_MIGRATE` and `SAFE_TO_MIGRATE_RENAME_REQUIRED` records are listed below. `ALREADY_ARCHIVED`, control artifacts, active dependencies, runtime paths, unknown records and retention-blocked records are excluded.

### Safe to migrate

- `reports/data_update_status.datasource_refresh.json`
- `reports/data_update_status.dryrun.json`
- `reports/pr_final_hygiene_audit_2026-07-12.md`
- `reports/project_weekly_report_2026-07-10.md`
- `reports/trading_weekly_report_2026-07-10.md`

### Safe to migrate with rename

- `reports/app_data_backfill_button_audit.md`
- `reports/app_launch_diagnostics.md`
- `reports/backtest_result.csv`
- `reports/backtest_summary.md`
- `reports/baostock_diagnosis.md`
- `reports/benchmark_redundancy_analysis.md`
- `reports/codex_daily_research_prompt.md`
- `reports/codex_weekly_research_prompt.md`
- `reports/daily_data_update_diagnosis_report.md`
- `reports/dashboard_redesign_research.md`
- `reports/effective_sample_coverage_audit.md`
- `reports/etf_pool_research_matrix.csv`
- `reports/etf_pool_research_report.md`
- `reports/etf_strategy_news_sentiment_research.md`
- `reports/exposure_candidate_matrix.md`
- `reports/exposure_data_contract.md`
- `reports/exposure_framework_feasibility_study.md`
- `reports/exposure_gap_analysis.md`
- `reports/exposure_point_in_time_rules.md`
- `reports/exposure_portfolio_role_definition.md`
- `reports/exposure_prototype_data_quality.md`
- `reports/exposure_prototype_summary.md`
- `reports/exposure_redundancy_analysis.md`
- `reports/exposure_taxonomy_design.md`
- `reports/exposure_window_stability.md`
- `reports/factor_analysis_report.md`
- `reports/frontend_css_cleanup_audit.md`
- `reports/industry_etf_diagnosis.md`
- `reports/jqdata_connection_diagnosis.md`
- `reports/manual_failed_diagnosis_report.md`
- `reports/manual_import_integrity_audit.md`
- `reports/market_exposure_data_contract.md`
- `reports/market_exposure_redesign.md`
- `reports/market_exposure_vector_summary.md`
- `reports/model_data_maturity_analysis.json`
- `reports/model_data_maturity_analysis.md`
- `reports/model_data_maturity_tables.csv`
- `reports/model_dataset.csv`
- `reports/model_research_report.md`
- `reports/multi_benchmark_framework.md`
- `reports/path_sanitization_audit.md`
- `reports/regime_layer_phase3_5b_decision.json`
- `reports/shadcn_card_density_audit.md`
- `reports/shadcn_ui_compatibility_audit.json`
- `reports/shadcn_ui_compatibility_audit.md`
- `reports/style_fit_commodity_cyclical_audit.csv`
- `reports/style_fit_commodity_cyclical_audit.md`
- `reports/style_fit_commodity_cyclical_qualification.json`
- `reports/style_fit_etf_level_robustness.csv`
- `reports/style_fit_etf_level_robustness.md`
- `reports/style_fit_evidence_qualification_summary.json`
- `reports/style_fit_failure_attribution.json`
- `reports/style_fit_failure_attribution.md`
- `reports/style_fit_failure_postmortem.md`
- `reports/style_fit_failure_tree.md`
- `reports/style_fit_future_preview_research_scope.json`
- `reports/style_fit_high_beta_theme_audit.csv`
- `reports/style_fit_high_beta_theme_audit.md`
- `reports/style_fit_high_beta_theme_qualification.json`
- `reports/style_fit_horizon_robustness.csv`
- `reports/style_fit_horizon_robustness.md`
- `reports/style_fit_incremental_signal_final_decision.json`
- `reports/style_fit_incremental_value_robustness.csv`
- `reports/style_fit_incremental_value_robustness.md`
- `reports/style_fit_regime_segment_robustness.csv`
- `reports/style_fit_regime_segment_robustness.md`
- `reports/style_fit_robustness_evidence_integrity_audit.json`
- `reports/style_fit_time_robustness.csv`
- `reports/style_fit_time_robustness.md`
- `reports/style_regime_evidence_qualification_matrix.json`
- `reports/style_regime_fit_source_audit.json`
- `reports/tushare_capability_gap_audit.md`
- `reports/universe_v2_candidate_qualification.md`
- `reports/universe_v2_coverage_gap_analysis.md`
- `reports/universe_v2_expansion_plan.md`
- `reports/universe_v2_full_replay.md`
- `reports/universe_v2_replay/v2_style_fit_regime_segments.csv`
- `reports/universe_v2_replay/v2_style_fit_robustness_base.csv`
- `reports/universe_v2_replay/v2_style_fit_robustness_core_summary.json`
- `reports/universe_v2_replay/v2_style_fit_robustness_source_audit.json`
- `reports/universe_v2_replay/v2_style_regime_differentiation.csv`
- `reports/universe_v2_replay/v2_style_regime_differentiation.json`
- `reports/universe_v2_replay/v2_style_regime_fit_matrix.csv`
- `reports/universe_v2_replay/v2_style_regime_fit_matrix.json`
- `reports/universe_v2_replay/v2_style_regime_fit_summary.csv`
- `reports/universe_v2_replay/v2_style_regime_fit_summary.json`
- `reports/universe_v2_replay_plan.md`
