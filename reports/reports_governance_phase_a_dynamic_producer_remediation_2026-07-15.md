---
report_id: report_f2b883f2ffec3c95
report_type: GOVERNANCE_DYNAMIC_PRODUCER_REMEDIATION
business_date: 2026-07-15
created_at: 2026-07-15T11:24:56+08:00
status: READY_FOR_INDEPENDENT_DYNAMIC_PRODUCER_RE_QC
phase: reports_governance_phase_a
producer: scripts/governance/build_phase_a_summary.py
source_run_id: reports-governance-phase-a-remediation-2026-07-15
retention_class: PERMANENT
schema_version: 2
---
# Reports Governance Phase A Dynamic Producer Remediation

## Remediation result

- Root cause: the previous analyzer merged same-named variables across all functions, so `path` in daily and weekly generators lost its lexical origin and dynamic write direction.
- Python bindings are keyed by stable lexical `scope_id` plus name and version.
- Module, class, function, async-function, lambda and comprehension scopes are isolated; closures resolve through lexical parents without sibling leakage.
- Dynamic writes emit `PRODUCER_WRITE / WRITE` with scope, binding, structured pattern and Producer entrypoint metadata.
- Trusted `<DATE>`, `<TIMESTAMP>` and `<RUN_ID>` templates use anchored full-path matching. `<DYNAMIC>` is retained for review and never auto-matched.
- Each binding records assignment line/kind, normalized expression, static resolution or dynamic template, pattern variables, confidence, version and excerpt hash.
- Committed scope/dynamic fixture cases: 29/29 pass; positive dynamic Producer cases: 28/28.
- Reports blocked by active dynamic Producers: 10.
- Remaining Archive Candidates: 0.

## Real producer linkage

- `src/reporting.py:203` scope `scope_c1a0a4a4a82eb1d1` -> `reports/daily_signal_<DATE>.md` (MEDIUM)
- `src/execution/paper_freshness_gate.py:386` scope `scope_89b2b8834ab92d6e` -> `reports/paper_execution_stale_trade_audit_<DATE>.json` (MEDIUM)
- `src/execution/paper_freshness_gate.py:413` scope `scope_89b2b8834ab92d6e` -> `reports/paper_execution_stale_trade_audit_<DATE>.md` (MEDIUM)
- `src/reporting.py:658` scope `scope_de7324c94eb244c2` -> `reports/weekly_review_<DATE>.md` (MEDIUM)

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

All 10 prior Archive Candidates are now matched and blocked with `ACTIVE_DYNAMIC_PRODUCER`; real-path recall is 10/10 and precision is 10/10. Deterministic matcher fixtures cover 20/20 positive concrete dates and 20/20 negative paths, including wrong prefixes/extensions and unknown broad templates. The focused Catalog review also sampled 20/20 static-Producer files and 20/20 historical/unknown files without an active Producer; no high-impact false lock was found.

## Rebuild and remaining limits

- First clean rebuild: byte-identical, zero diff.
- Three consecutive rebuilds: byte-identical; Catalog/Registry aggregate hashes stable.
- Source lines, excerpt hashes, scope IDs and binding IDs: reproducible against the current source commit.
- Complex call-return propagation, deletion paths and unresolved control flow remain conservative: no concrete binding is fabricated; branch alternatives become low-confidence multi-bindings.
- `<DYNAMIC>` does not auto-lock reports and remains a manual-review signal.

## Boundary

No pre-existing report was moved, renamed, deleted or overwritten. Runtime Path Registry remains `NOT_STARTED`; Report Migration Phase B remains `BLOCKED`; Availability Temporary Data Lifecycle remains `DEFINED`; the temporary audit database remains `RETAIN_UNTIL_MIGRATION_VALIDATED`; ETF Daily Availability Timing Audit remains `ACTIVE_COLLECTING`. PR #4 remains Draft and awaits independent dynamic Producer Re-QC.
