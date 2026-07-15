---
report_id: report_34429ebfad281f3f
report_type: GOVERNANCE_PHASE_SUMMARY
business_date: 2026-07-15
created_at: 2026-07-15T11:24:56+08:00
status: REMEDIATED_PENDING_FINAL_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-remediation-2026-07-15
retention_class: PERMANENT
schema_version: 2
supersedes: reports/reports_governance_phase_a_summary_2026-07-14.md
---
# Reports Governance Phase A Summary

## State

- Engineering: `REMEDIATED`
- PR #4: `DRAFT_AWAITING_DYNAMIC_PRODUCER_RE_QC`
- Report Catalog: `REBUILT_DYNAMIC_PRODUCERS_BLOCK_ARCHIVE`
- Dependency Registry: `REMEDIATED_PENDING_FINAL_QC`
- Dynamic Producer Linkage: `IMPLEMENTED_PENDING_QC`
- Archive Candidate Classification: `REBUILT_PENDING_QC`
- Availability Temporary Data Lifecycle: `DEFINED`
- Temporary Audit Database: `RETAIN_UNTIL_MIGRATION_VALIDATED`
- Naming Standard: `PROPOSED_ACTIVE_ON_MERGE`
- Path Registry Design: `COMPLETE_PENDING_QC`
- Runtime Path Registry: `NOT_STARTED`
- Migration Phase B: `BLOCKED`
- Existing historical reports: `UNCHANGED`
- ETF Availability Audit: `ACTIVE_COLLECTING`

## Dated immutable deliverables

- `reports/report_catalog_2026-07-15.csv`
- `reports/report_catalog_2026-07-15.json`
- `reports/report_catalog_2026-07-15.md`
- `reports/report_dependency_registry_2026-07-15.csv`
- `reports/report_dependency_summary_2026-07-15.md`
- `reports/report_naming_compliance_audit_2026-07-15.csv`
- `reports/reports_governance_phase_a_summary_2026-07-15.md`
- `reports/reports_governance_phase_a_dynamic_producer_remediation_2026-07-15.md`

No undated Catalog, Registry or Phase A summary is retained as a unique artifact. No runtime alias is required for these governance snapshots, so alias mapping is `NOT_APPLICABLE`.

## Recomputed inventory

- Catalog records: 645
- Dependency records: 6330
- Distinct targets/patterns: 884
- Dynamic patterns: 107
- Runtime locked: 108
- Current aliases: 36
- Low-risk archive candidates: 0
- Reports matched to active dynamic Producers: 12
- Unknown roles: 148
- Naming compliant: 15
- Naming non-compliant: 318

## Human stratified sample

The final focused sample uses a new deterministic selection from the regenerated Registry. Each row was reviewed against the current source excerpt, parser semantics, direction and target. Golden fixtures are separate committed test evidence.

| Reference type | Correct | Accuracy |
| --- | ---: | ---: |
| `PRODUCER_WRITE` | 30/30 | 100.0% |
| `CONSUMER_READ` | 20/20 | 100.0% |
| `APP_RUNTIME_READ` | 15/15 | 100.0% |
| `DASHBOARD_RUNTIME_READ` | 15/15 | 100.0% |
| `DOCUMENTATION_LINK` | 20/20 | 100.0% |
| `DYNAMIC_RESOLUTION` | 14/15 | 93.3% |
| `TEST_REFERENCE` | 15/15 | 100.0% |
| `HISTORICAL_REFERENCE` | 15/15 | 100.0% |
| `SCOPED_DYNAMIC_PRODUCER` | 29/29 | 100.0% |
| **Overall** | **173/174** | **99.4%** |

No high-impact App/Dashboard runtime or Archive Candidate misclassification was found. `PRODUCER_WRITE` is 30/30 and the 145-row overall sample exceeds the 95% threshold. One low-severity dynamic documentation example retained a trailing delimiter in its normalized target; it has no runtime or archive-candidate effect. The real repository contains six Shell copy direction records; all six were reviewed, and the committed 18-case direction corpus also passed.

## Reproducibility and boundary

- `reference_id` excludes line numbers and includes normalized source context.
- Current source lines and excerpt hashes are independently testable.
- Generated control artifacts are excluded from their own scan.
- Final clean rebuild must be byte-identical on the first and three consecutive runs.
- Phase A performs no move, rename or deletion of any pre-existing report.
- Phase B remains blocked and no runtime Path Registry exists.
