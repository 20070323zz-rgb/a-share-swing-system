---
artifact_type: GOVERNANCE_CONTROL
schema_version: pr4-salvage-assessment-v1
source_pr: 4
source_head: 3da9f038ea46f2e14a35ab0b38aa9b404386e628
---

# PR #4 Portable Asset Assessment

This assessment records design provenance only. Reuse means independent reimplementation or independent validation against `origin/main`; it never means copying PR #4 candidate outputs.

## A. REUSE_AFTER_INDEPENDENT_VALIDATION

| Asset | Source path | PR #4 commit | Reason | Validation requirement | Destination in rebuild | Reuse decision |
| --- | --- | --- | --- | --- | --- | --- |
| Report naming standard | `docs/report_naming_standard.md` | `d84daf0` | Separating dated snapshots from aliases remains useful. | Strict DATE/MONTH tests; no migration inference. | `docs/reports_governance/phase_ar_standards.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Metadata standard | `docs/report_metadata_standard.md` | `d84daf0` | Version, source commit, generated time, and immutability are portable. | Deterministic metadata and content-hash tests. | `docs/reports_governance/phase_ar_standards.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Immutable snapshot design | `scripts/governance/report_governance_common.py` | `3af85d7` | Same-byte idempotence and different-byte fail-fast are required. | Create/idempotent/conflict tests; no force path. | `src/report_governance/snapshot.py` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Phase B end-to-end contract | `docs/report_migration_plan.md` | `7f086cd` | Vertical Producer/Consumer migration and rollback remain valid design constraints. | Reconcile every consumer surface against current main and PR #3. | `docs/reports_governance/phase_b_end_to_end_contract.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Availability temporary-data lifecycle | `docs/operational_playbook.md` | `00666ef` | Active observer evidence must not be cleaned by report governance. | Compare with current PR #3 lifecycle and retain all retirement gates. | `docs/reports_governance/phase_b_end_to_end_contract.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| PR #3 authority/deep-merge contract | `scripts/governance/authority_merge.py` | `593d5c1` | Reports and Availability have separate authority ownership. | Compare remote PR #3 key/value surface; unknown-key and conflict tests. | `docs/reports_governance/phase_ar_architecture.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Evidence Registry schema idea | `scripts/governance/evidence_registry.py` | `5aeabbb` | Decisions require resolvable, parseable provenance. | Reimplement generation; verify zero unresolved and duplicate IDs. | `src/report_governance/evidence.py` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| DATE/MONTH strict validation | `tests/fixtures/report_governance/temporal_token_cases.json` | `0f40a41` | Calendar-valid dates and explicit month formats avoid name collisions. | Independent boundary tests for dashed/compact tokens. | `src/report_governance/temporal.py` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Class/method scope tests | `tests/fixtures/report_governance/class_method_scope_cases.json` | `0f40a41` | Lexical scope is essential for path-flow accuracy. | Bare method names must not inherit class attributes; explicit self/cls/class access may. | `tests/test_report_governance_phase_ar.py` | REUSE_AFTER_INDEPENDENT_VALIDATION |
| Deprecated-path governance rule | `docs/report_migration_plan.md` | `7f086cd` | Compatibility must expire explicitly and fail closed. | Consumer completeness, warning, expiry, and rollback checks. | `docs/reports_governance/phase_b_end_to_end_contract.md` | REUSE_AFTER_INDEPENDENT_VALIDATION |

## B. REIMPLEMENT_FROM_SPEC

| Asset | Source path | PR #4 commit | Reason | Validation requirement | Destination in rebuild | Reuse decision |
| --- | --- | --- | --- | --- | --- | --- |
| Catalog generator | `scripts/governance/build_report_catalog.py` | `cfaa66d` | PR #4 mixed inventory and dependency semantics. | No mtime date inference; control-by-type exclusion; deterministic IDs. | `src/report_governance/inventory.py` | REIMPLEMENT_FROM_SPEC |
| Dependency inventory | `scripts/governance/build_report_dependency_registry.py` | `cfaa66d` | PR #4 missed 43 active references. | Two independent engines; 43/43 recall. | `src/report_governance/structured_scanner.py`, `backstop_scanner.py` | REIMPLEMENT_FROM_SPEC |
| Evidence materialization | `scripts/governance/build_report_governance_evidence_registry.py` | `5aeabbb` | Schema was useful but generation depended on defective classification. | Recompute from current source; zero unresolved evidence. | `src/report_governance/evidence.py` | REIMPLEMENT_FROM_SPEC |
| Location classification | `scripts/governance/report_governance_common.py` | `5aeabbb` | Already-archived contamination required explicit lifecycle handling. | Exact configured-root matching; zero archived candidates. | `src/report_governance/inventory.py` | REIMPLEMENT_FROM_SPEC |
| Migration eligibility | `scripts/governance/report_governance_common.py` | `df6007e` | PR #4 SAFE results were semantically invalid. | Fourteen fail-closed gates plus 100% review. | `src/report_governance/readiness.py` | REIMPLEMENT_FROM_SPEC |
| Deletion eligibility | `scripts/governance/report_governance_common.py` | `df6007e` | Migration and deletion must remain separate. | `SAFE_TO_DELETE_AFTER_AUTHORIZATION=0`. | `src/report_governance/readiness.py` | REIMPLEMENT_FROM_SPEC |

## C. REJECT

| Asset | Source path | PR #4 commit | Reason | Validation requirement | Destination in rebuild | Reuse decision |
| --- | --- | --- | --- | --- | --- | --- |
| `SAFE_TO_MIGRATE` results | `reports/report_catalog_v3_2026-07-15.*` | `3da9f03` | Includes an active Producer and cannot prove zero dependency. | Recompute from current source only. | None | REJECT |
| `SAFE_TO_MIGRATE_RENAME_REQUIRED` results | `reports/report_catalog_v3_2026-07-15.*` | `3da9f03` | 42 records have active source/config references. | Recompute from current source only. | None | REJECT |
| 92 Phase B candidate list | `reports/reports_governance_phase_a_summary_v3_2026-07-15.md` | `3da9f03` | Full review found only 49/92 passing the static screen. | Never ingest as candidate input. | None | REJECT |
| Active-reference completeness conclusion | `reports/report_dependency_registry_v3_2026-07-15.*` | `3da9f03` | The dependency graph omitted direct active references. | Require dual-engine evidence and disagreement flag. | None | REJECT |
| Archive Candidate or migration statistics derived from PR #4 classifier | `reports/reports_governance_phase_a_summary_v3_2026-07-15.md` | `3da9f03` | Counts inherit classifier defects and archived contamination. | Publish new Phase A-R counts only. | None | REJECT |
| Hard-coded `6370`, `120`, `92`, or related historical assertions | PR #4 tests and summaries | `3da9f03` | File/reference counts are not semantic invariants. | Assert properties, recall, uniqueness, and determinism instead. | None | REJECT |

The 43 false negatives are retained only as a regression corpus with provenance `PR4_FINAL_RESULT_QC`; they are not retained as PR #4 migration conclusions.
