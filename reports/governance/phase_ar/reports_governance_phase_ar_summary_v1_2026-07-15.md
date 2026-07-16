# Reports Governance Phase A-R Summary v1

- source_tree_commit: `5d7c3d753a50f8b047f188a22177828c5efdd2c4`
- generated_at: `2026-07-15T15:33:15+00:00`
- run_id: `phase-ar-run_6a475018620c44bce838701d`
- immutable: `true`
- phase_b: `BLOCKED`
- zero_move: `PASS`
- deletion_authorized: `false`

## Inventory

- reports: `644`
- duplicate_report_ids: `0`
- archived: `45`
- unknown_role: `0`

## Independent reference engines

- structured_references: `1961`
- structured_producer_reports: `408`
- structured_consumer_reports: `214`
- backstop_references: `4104`
- scanner_disagreements: `35`

## Evidence and readiness

- evidence_records: `6946`
- unresolved_evidence: `0`
- machine_provisional_before_review: `52`
- candidate_reviews: `52`
- candidate_reviews_passed: `52`
- final_provisional: `52`
- safe_to_delete_after_authorization: `0`

### Migration readiness distribution

| status | count |
| --- | ---: |
| BLOCKED_ACTIVE_CONSUMER | 18 |
| BLOCKED_ACTIVE_PRODUCER | 379 |
| BLOCKED_ALIAS | 18 |
| BLOCKED_BACKSTOP_REFERENCE | 70 |
| BLOCKED_RETENTION | 39 |
| BLOCKED_RUNTIME | 23 |
| NOT_APPLICABLE_ALREADY_ARCHIVED | 45 |
| PROVISIONALLY_SAFE_RENAME_REQUIRED | 52 |

Phase A-R only establishes dry-run readiness. It does not move, rename, delete, or rewrite reports, implement a runtime Path Registry, or start Phase B.
