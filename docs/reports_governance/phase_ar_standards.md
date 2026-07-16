# Phase A-R Naming, Metadata, and Evidence Standards

## Naming

- Immutable dated snapshots use calendar-valid `YYYY-MM-DD`; compact DATE is accepted only where explicitly declared.
- MONTH is a separate token and must never satisfy DATE validation.
- `current` and `latest` are aliases and are blocked from migration readiness.
- An undated file with a business date in content is `NEEDS_DATE_NORMALIZATION`, not a dated filename.

## Metadata

Every JSON snapshot carries `artifact_type`, `schema_version`, `source_tree_commit`, deterministic `generated_at`, `immutable=true`, `run_id`, and `record_count`. CSV and Markdown files are covered by the immutable group manifest.

## Evidence

Every report has Inventory evidence and either reference evidence or an explicit zero-reference proof for both scanners. Zero-reference proof includes scanner version, scanned roots, excluded roots, search keys, run ID, source commit, result count, and a canonical evidence hash. IDs are content-addressed and must resolve bidirectionally from readiness decisions.

## Deletion

Migration readiness is never deletion readiness. Phase A-R emits only `DELETION_BLOCKED`, `DELETION_REVIEW_REQUIRED`, or `NOT_DELETION_CANDIDATE`; `SAFE_TO_DELETE_AFTER_AUTHORIZATION` must remain zero.
