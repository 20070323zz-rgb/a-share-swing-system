---
report_id: report_651ab0b7f69ff3a5
report_type: GOVERNANCE_REMEDIATION
business_date: 2026-07-15
created_at: 2026-07-15T11:07:49+08:00
status: READY_FOR_FINAL_INDEPENDENT_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-remediation-2026-07-15
retention_class: PERMANENT
schema_version: 2
supersedes: reports/reports_governance_phase_a_remediation_2026-07-14.md
---
# Reports Governance Phase A Remediation

## Closed blockers

1. Replaced undated PR-only control outputs with immutable dated artifacts.
2. Replaced broad producer heuristics with Python AST and source-aware Shell/frontend/document parsers.
3. Added stable `reference_id`, source spans, parser type, excerpt hash, generator version and source-tree commit.
4. Added committed golden fixtures and rebuild/source-identity regression tests.
5. Recomputed Catalog and migration classifications from remediated dependencies.
6. Completed retention, cycle prevention, migration order, rollback and missing-date behavior in the Path Registry design.
7. Reconciled PR #3's active Availability Audit state into the shared authority surfaces without copying its implementation or evidence.
8. Classified Shell `cp/mv` source and destination by argument position; report sources no longer become false producers.
9. Defined Availability temporary audit data retention, retirement prerequisites, authorization, evidence and post-retirement rollback.

## Validation contract

- Golden fixture accuracy: 100%.
- Human stratified sample: 168/169 (99.4%).
- Producer sample: 30/30 (100%).
- Shell direction: 6/6 real repository records and 18/18 committed directional fixtures.
- First clean rebuild: required byte-identical.
- Three-run rebuild: required byte-identical.
- Full pytest, Dashboard, frontend, App release, context, path/secret, Zero-Move and protected-boundary checks are required before push.

## State transition

`READY_FOR_FINAL_INDEPENDENT_RE_QC`. This is not a `MERGE_READY` declaration. PR #4 remains Draft. Report Migration Phase B and runtime Path Registry remain blocked/not started. Availability temporary audit data remains retained and untouched.
