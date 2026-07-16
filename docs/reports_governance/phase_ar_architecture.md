# Reports Governance Phase A-R Architecture

Phase A-R contains exactly five modules:

1. Report Inventory describes what each report file is. It does not infer Producers, Consumers, migration safety, or deletion safety.
2. Active Reference Index combines a Python/shell/config/frontend structured engine with an independently implemented text backstop. Both keep their own IDs and counts.
3. Governance Evidence Index materializes every positive reference and every zero-reference proof with scanner version, roots, exclusions, search keys, run ID, source commit, result count, and evidence hash.
4. Migration Readiness Classification evaluates fail-closed dry-run gates. `PROVISIONALLY_SAFE_*` never authorizes movement.
5. Immutable Governance Snapshot writes same-byte idempotently, rejects different bytes at an occupied path, and requires a new revision for changed content.

Inventory and dependency discovery are deliberately separate. Governance control artifacts are excluded through `artifact_type: GOVERNANCE_CONTROL` or a configured governance-control root, not through an expected file count.

## Dual-engine rule

A report can reach a machine-provisional set only when Structured has no Producer or Consumer, Backstop has no active source/config hit, it is not an alias/runtime/formal/App/Availability/control/archive artifact, its role is known, retention allows migration, and the engines do not disagree. Every machine-provisional record then requires an explicit full-review record before it can remain provisionally safe.

Scanner disagreement is never silently reconciled. It sets `reference_disagreement=true` and requires review.

## Authority ownership

Reports fields belong to Phase A-R. Availability fields remain owned by current PR #3 until that PR is merged or otherwise superseded. Final status synchronization must be an authority-aware deep merge: preserve all unknown PR #3 keys and values, update only Reports-owned fields, and fail on unowned type/value conflicts.

## Out of scope

No move, rename, delete, runtime Path Registry, App/Dashboard path switch, deprecated-path activation, Availability cleanup, automatic log cleanup, or Phase B migration is implemented here.
