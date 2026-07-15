---
report_id: report_d11b85e8df37d51c
report_type: GOVERNANCE_PHASE_SUMMARY
business_date: 2026-07-15
created_at: 2026-07-15T12:12:06+08:00
status: REMEDIATED_PENDING_FINAL_SEMANTIC_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-semantic-v2-2026-07-15
retention_class: PERMANENT
schema_version: 2
snapshot_revision: v2
immutable: true
supersedes: reports/reports_governance_phase_a_summary_2026-07-15.md
---
# Reports Governance Phase A Summary

## State

- PR #4: `DRAFT_AWAITING_FINAL_SEMANTIC_RE_QC`
- Reports Governance Phase A: `REMEDIATED`
- Date Pattern Validation: `IMPLEMENTED_PENDING_QC`
- Python Scope Semantics: `IMPLEMENTED_PENDING_QC`
- Migration Eligibility: `REBUILT_PENDING_QC`
- Deletion Eligibility: `REBUILT_PENDING_QC`
- Snapshot Immutability: `ENFORCED_PENDING_QC`
- Phase B Contract: `COMPLETE_PENDING_QC`
- PR #3 Authority Preservation: `REMEDIATED_PENDING_QC`
- Reports Migration Phase B: `BLOCKED`
- Runtime Path Registry: `NOT_STARTED`
- Availability Audit: `ACTIVE_COLLECTING`
- Availability temporary data: `RETAIN_UNTIL_MIGRATION_VALIDATED`

## Inventory

- Catalog records: 645
- Dependency records: 6370
- Dynamic patterns: 120
- Runtime locked: 108
- Current aliases: 36
- Unknown roles: 148
- Concrete active dynamic Producer matches: 12
- Deprecated Archive Candidate true count: 0
- Safe to delete after authorization: 0

### Dependency safety

- `ACTIVE_PRODUCER`: 262
- `NO_ACTIVE_DEPENDENCY`: 275
- `RUNTIME_LOCKED`: 108

### Naming status

- `COMPLIANT_DATED`: 12
- `LEGACY_STABLE_ALIAS`: 36
- `NEEDS_DATE_NORMALIZATION`: 317
- `NOT_APPLICABLE`: 132
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
- `SAFE_TO_MIGRATE`: 50
- `SAFE_TO_MIGRATE_RENAME_REQUIRED`: 87

### Deletion eligibility

- `DELETION_BLOCKED`: 450
- `DELETION_REVIEW_REQUIRED`: 92
- `NOT_DELETION_CANDIDATE`: 103

### Classification reasons

- `ACTIVE_AUDIT_ARTIFACT`: 50
- `ACTIVE_DYNAMIC_PRODUCER`: 12
- `ACTIVE_STATIC_PRODUCER`: 332
- `CURRENT_ALIAS`: 36
- `NEEDS_DATE_NORMALIZATION`: 317
- `NO_ACTIVE_DEPENDENCY`: 275
- `RETENTION_BLOCKED`: 244
- `RUNTIME_CONSUMER`: 108
- `STATE_OR_GOVERNANCE_LOCKED`: 75
- `UNKNOWN_ROLE`: 148

## Governance meaning

The deprecated single `archive_candidate` flag is retained only as a compatibility field and is always false. Migration eligibility and deletion eligibility are independent. A naming defect can require a rename without fabricating an active dependency, while active static or dynamic Producers still block migration. Phase A never grants automatic deletion safety.

The complete App, Dashboard, automation, Work/Codex, deprecated-path, compatibility-period, consumer-completeness and rollback contract is stored in repository governance documents. This summary does not start Phase B or a runtime Path Registry.
