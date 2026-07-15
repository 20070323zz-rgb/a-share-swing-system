# Reports Migration Phase B End-to-End Contract

Status: `DESIGN_ONLY / PHASE_B_BLOCKED`.

This contract was independently reconciled with current `origin/main` and the latest PR #3 authority surface. It carries no PR #4 candidate data.

## Vertical migration unit

Each report family is migrated vertically as one reviewed unit: Producer, immutable dated destination, runtime Registry/alias, Backend API/file read, Dashboard, App, backfill button, automation, daily/weekly entrypoints, tests, Work/Codex authority read order, deprecated-path scan, compatibility window, rollback, and Formal Execution consumers. Partial consumer migration is `MIGRATION_PARTIAL`, never success.

## App and Dashboard

- The App backfill button must complete the Producer write and then refresh the Backend read surface end to end.
- Dashboard reads only through the approved Registry/alias/API after its family is migrated.
- Missing Registry entries, stale aliases, or incomplete consumer graphs fail closed.
- No App or Dashboard path is switched during Phase A-R.

## Work and Codex

Authority reads follow `AGENTS.md`, current code/data, `docs/current_phase_status.json`, `docs/current_project_state.md`, current decision/report, then `PROJECT_INDEX.md`. A report move cannot complete until these readers and referenced paths are updated and verified.

## Deprecated paths and compatibility

- Before migration: scan every active source/config/authority surface for the old exact path, basename, dynamic prefix, and configuration key.
- During compatibility: emit a dated warning with owner and expiry.
- At expiry: old paths fail fast; silent fallback is forbidden.
- Completion requires consumer completeness and zero unauthorized old-path hits.

## Rollback and states

- `MIGRATION_PARTIAL`: any Producer or Consumer remains on the old path, any evidence is unresolved, or compatibility cannot be expired.
- `MIGRATION_COMPLETE`: Producer and every Consumer use the new contract, checks pass, rollback evidence exists, and old paths are disabled as authorized.
- Rollback restores the full vertical family, not only the Producer.

## Formal Execution

Formal Execution inputs migrate last, under separate Main authorization, after dry-run and consumer-completeness evidence. Phase A-R does not authorize or perform that migration.

## Availability temporary data

Availability observer data remains `TEMPORARY_AUDIT_DATA / SHADOW_EVIDENCE_ONLY / NONCANONICAL / NONPROMOTION`. While PR #3 is `ACTIVE_COLLECTING`, deletion is prohibited. Retirement requires all lifecycle prerequisites, named authority approval, dated pre/post reports, reconstructability assessment, staging-independent rollback, and no impact on canonical `data/etf_daily`. Report migration and Availability cleanup are separate decisions.

## Noise and logs

Log/noise/duplicate cleanup belongs to a separate `Noise & Log Retention Audit`. No report migration candidate is deletion evidence.
