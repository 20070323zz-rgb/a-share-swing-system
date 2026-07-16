# Reports Governance Phase A-R Summary v2

- snapshot_revision: `phase-ar-v2-2026-07-16`
- supersedes: `phase-ar-v1-2026-07-15`
- source_tree_commit: `ecef39d7ca11be874cee36d381d7f684af1253e3`
- generated_at: `2026-07-16T15:32:22+08:00`
- run_id: `phase-ar-run_83d02c66ce437dfd0671ef85`
- immutable: `true`
- superseded_snapshot_status: `VALID_HISTORICAL_SNAPSHOT / SUPERSEDED`
- phase_b: `BLOCKED`
- zero_move: `PASS`
- deletion_authorized: `false`

## Inventory

- reports: `651`
- content_hash_mismatches: `0`
- archived: `45`
- unknown_role: `0`

## Independent scanners

- structured_references: `2593`
- structured_producers: `433`
- structured_consumers: `632`
- markdown_references: `123`
- markdown_runtime_misclassifications: `0`
- backstop_query_records: `5208`
- backstop_found_queries: `1523`
- backstop_ambiguous_queries: `18`
- backstop_zero_result_proofs: `3667`
- scanner_disagreements: `9`

### Disagreement distribution

| type | count |
| --- | ---: |
| REFERENCE_CLASS_DISAGREEMENT | 9 |

## Evidence and readiness

- evidence_records: `12416`
- unresolved_evidence: `0`
- orphan_evidence: `0`
- duplicate_evidence_ids: `0`
- machine_provisional_before_review: `49`
- candidate_reviews: `49`
- candidate_reviews_passed: `49`
- structured_precision_review_records: `100`
- final_provisional: `49`
- safe_to_delete_after_authorization: `0`

### Migration readiness distribution

| status | count |
| --- | ---: |
| BLOCKED_ACTIVE_CONSUMER | 12 |
| BLOCKED_ACTIVE_PRODUCER | 387 |
| BLOCKED_ALIAS | 18 |
| BLOCKED_BACKSTOP_REFERENCE | 67 |
| BLOCKED_RETENTION | 44 |
| BLOCKED_RUNTIME | 29 |
| NOT_APPLICABLE_ALREADY_ARCHIVED | 45 |
| PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN | 13 |
| PROVISIONALLY_SAFE_RENAME_REQUIRED | 36 |

Phase A-R v2 only establishes provisional dry-run readiness. It does not move, rename, delete, or rewrite reports, implement a Runtime Path Registry, or start Phase B.
