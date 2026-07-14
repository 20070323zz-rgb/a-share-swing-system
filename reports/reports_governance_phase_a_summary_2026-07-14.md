---
report_id: report_12c4ab4294b5c6ac
report_type: GOVERNANCE_PHASE_SUMMARY
business_date: 2026-07-14
created_at: 2026-07-14T19:28:32+08:00
status: REMEDIATED_PENDING_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-remediation-2026-07-14
retention_class: PERMANENT
schema_version: 2
---
# Reports Governance Phase A Summary

## State

- Engineering: `REMEDIATED`
- PR #4: `DRAFT_AWAITING_INDEPENDENT_RE_QC`
- Report Catalog: `REBUILT`
- Dependency Registry: `REMEDIATED_PENDING_QC`
- Naming Standard: `PROPOSED_ACTIVE_ON_MERGE`
- Path Registry Design: `COMPLETE_PENDING_QC`
- Runtime Path Registry: `NOT_STARTED`
- Migration Phase B: `BLOCKED`
- Existing historical reports: `UNCHANGED`
- ETF Availability Audit: `ACTIVE_COLLECTING`

## Dated immutable deliverables

- `reports/report_catalog_2026-07-14.csv`
- `reports/report_catalog_2026-07-14.json`
- `reports/report_catalog_2026-07-14.md`
- `reports/report_dependency_registry_2026-07-14.csv`
- `reports/report_dependency_summary_2026-07-14.md`
- `reports/report_naming_compliance_audit_2026-07-14.csv`
- `reports/reports_governance_phase_a_summary_2026-07-14.md`

No undated Catalog, Registry or Phase A summary is retained as a unique artifact. No runtime alias is required for these governance snapshots, so alias mapping is `NOT_APPLICABLE`.

## Recomputed inventory

- Catalog records: 645
- Dependency records: 6172
- Distinct targets/patterns: 787
- Dynamic patterns: 40
- Runtime locked: 107
- Current aliases: 36
- Low-risk archive candidates: 10
- Unknown roles: 148
- Naming compliant: 15
- Naming non-compliant: 318

## Human stratified sample

The sample uses 20 evenly spaced rows from each sorted type. Each row was reviewed against the current source excerpt, parser semantics, direction and target. Golden fixtures are separate committed test evidence.

| Reference type | Correct | Accuracy |
| --- | ---: | ---: |
| `APP_RUNTIME_READ` | 17/17 | 100.0% |
| `DASHBOARD_RUNTIME_READ` | 20/20 | 100.0% |
| `PRODUCER_WRITE` | 20/20 | 100.0% |
| `DOCUMENTATION_LINK` | 20/20 | 100.0% |
| `DYNAMIC_PATH_PATTERN` | 3/3 | 100.0% |
| `TEST_REFERENCE` | 20/20 | 100.0% |
| **Overall** | **100/100** | **100.0%** |

No high-impact App/Dashboard runtime misclassification was found in the sampled rows. `PRODUCER_WRITE` met the 90% target. Overall accuracy met the 95% target.

## Reproducibility and boundary

- `reference_id` excludes line numbers and includes normalized source context.
- Current source lines and excerpt hashes are independently testable.
- Generated control artifacts are excluded from their own scan.
- Final clean rebuild must be byte-identical on the first and three consecutive runs.
- Phase A performs no move, rename or deletion of any pre-existing report.
- Phase B remains blocked and no runtime Path Registry exists.
