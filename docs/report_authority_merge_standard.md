# Reports and Availability Authority Merge Standard

## Purpose

PR #4 and PR #3 share `PROJECT_INDEX.md`, `docs/current_project_state.md`, and `docs/current_phase_status.json`. Coordination uses field-level deep merge; an older object must never replace a newer object wholesale.

## Ownership

- Reports Governance fields: PR #4 / `reports_governance` authority.
- ETF Availability Audit fields, nested deliverables, observation metadata, progress and source ownership: PR #3 / `availability_audit` authority.
- Shared global fields: latest `main` plus an explicit path-level authority rule. An unowned conflict fails fast.

Reports prefixes include `reports_governance_*`, `report_catalog_*`, `report_dependency_*`, `report_classification_*`, `report_producer_*`, `report_dynamic_*`, `report_archive_*`, `report_naming_*`, `report_metadata_*`, `report_path_registry_*`, `report_file_migration_*`, and `report_migration_*`.

Availability prefixes include `etf_daily_availability_*`, `availability_temporary_*`, `draft_pr_3_*`, `tushare_data_source_role`, `baostock_data_source_role`, `canonical_etf_data_source`, and `data_promotion_status`. `phase_deliverables.tushare_etf_daily_availability_timing_audit` is Availability-owned.

While the audit is active, its main-phase timing/status, current-batch, required/final batch, next-phase, report/decision and context-update pointers are Availability-owned. Reports Governance state remains a parallel governance batch and must not reset those pointers.

## Deep merge rules

1. Recurse into mappings; do not replace a mapping as one scalar value.
2. Preserve unknown legal nested keys from both sides.
3. Add a key that exists on only one side.
4. Preserve equal scalar values without a decision.
5. Resolve a differing scalar only through the longest matching authority rule.
6. Type conflicts fail fast.
7. Unowned scalar conflicts fail fast and require Main review.
8. PR #3 updates must not remove Reports fields; PR #4 updates must not remove Availability fields.
9. After merge, JSON/schema validation and Context validation are mandatory.

The executable reference is `scripts/governance/authority_merge.py`; regression tests cover nested retention, Reports preservation, Availability updates, unknown legal keys, type conflicts, and unowned conflicts.

## Merge order

The recommended order remains:

```text
PR #4 merge after final independent Re-QC
-> PR #3 sync main
-> PR #3 retains its newest Availability evidence
-> Reports Governance state remains preserved
```

This standard does not authorize merging either PR.
