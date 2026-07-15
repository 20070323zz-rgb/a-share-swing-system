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

## DATA_NOT_READY

- `DATA_NOT_READY` is a fail-closed terminal result for the current run; it is never permission to read an arbitrary older dated file.
- A Producer, Consumer, backfill task, or automation entrypoint must not silently fall back to a deprecated path when current data is unavailable.
- `DATA_NOT_READY` must not update a runtime alias, switch a Registry entry, or leave a half-completed migration state.
- Recovery requires the current business-date input to pass the same schema, coverage, and freshness gates as a normal run.

## Freshness Gate and staging isolation

- Data completion, report generation, and runtime alias switching must all pass the Freshness Gate; no migration step may bypass it.
- If the Freshness Gate fails, the previous formal state and previous stable alias remain unchanged.
- A failed staging write or schema validation must not contaminate Canonical SSOT, the formal report path, or its active alias.
- Staging output is noncanonical until validation succeeds and the atomic alias switch completes.

## launchd, shell, and scheduler surface

Every migrated report family must synchronously inspect and test all of the following before completion:

- launchd plist program arguments and environment;
- shell wrappers and cron-compatible scripts;
- environment variables and working directory assumptions;
- stdout and stderr paths;
- every deprecated-path reference in those surfaces.

Any missed scheduler or shell consumer is `MIGRATION_PARTIAL` and fails closed.

## Immutable dated artifacts and stable aliases

- Every successful generation writes a new immutable dated artifact; the dated path is never overwritten.
- The dated path business-date component must equal the validated `business_date` in the artifact.
- Only after schema and freshness validation may the stable alias be updated atomically.
- App and Dashboard consumers read the approved Registry/stable alias and must not guess the newest dated filename.
- If alias replacement fails, the previous alias remains intact and the new dated artifact stays nonactive for investigation.

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
