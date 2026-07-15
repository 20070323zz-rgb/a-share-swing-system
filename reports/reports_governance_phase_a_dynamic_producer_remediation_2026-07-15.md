---
report_id: report_f2b883f2ffec3c95
report_type: GOVERNANCE_DYNAMIC_PRODUCER_REMEDIATION
business_date: 2026-07-15
created_at: 2026-07-15T11:07:49+08:00
status: READY_FOR_INDEPENDENT_DYNAMIC_PRODUCER_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-remediation-2026-07-15
retention_class: PERMANENT
schema_version: 2
---
# Reports Governance Phase A Dynamic Producer Remediation

## Remediation result

- Python bindings are keyed by stable lexical `scope_id` plus name and version.
- Module, class, function, async-function, lambda and comprehension scopes are isolated; closures resolve through lexical parents without sibling leakage.
- Dynamic writes emit `PRODUCER_WRITE / WRITE` with scope, binding, structured pattern and Producer entrypoint metadata.
- Trusted `<DATE>`, `<TIMESTAMP>` and `<RUN_ID>` templates use anchored full-path matching. `<DYNAMIC>` is retained for review and never auto-matched.
- Committed scope/dynamic fixture cases: 24/24 pass.
- Reports blocked by active dynamic Producers: 10.
- Remaining Archive Candidates: 0.

## Dynamically protected reports

- `reports/daily_signal_2026-06-29.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-06-30.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-01.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-03.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-06.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-07.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-08.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/daily_signal_2026-07-09.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/weekly_review_2026-07-03.md` via `DYNAMIC_PATTERN` (MEDIUM)
- `reports/weekly_review_2026-07-09.md` via `DYNAMIC_PATTERN` (MEDIUM)

## Boundary

No existing report was moved, renamed, deleted or overwritten. Runtime Path Registry remains `NOT_STARTED`; Report Migration Phase B remains `BLOCKED`; Availability Temporary Data Lifecycle remains `DEFINED`; the temporary audit database remains `RETAIN_UNTIL_MIGRATION_VALIDATED`; ETF Daily Availability Timing Audit remains `ACTIVE_COLLECTING`. PR #4 remains Draft and awaits independent dynamic Producer Re-QC.
