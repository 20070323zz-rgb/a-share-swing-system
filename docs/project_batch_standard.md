# Project Batch Standard V1

## Purpose

This document defines the standard structure for future project batches. It is a governance artifact, not a research result, strategy change, replay instruction, preview authorization, or formal execution approval.

Batch Standard V1 reduces repeated prompt work by giving Main and Codex a shared structure for batch type, header fields, validation, and state transition.

## Batch Lifecycle

Every batch follows this lifecycle:

1. Main defines the batch with the standard header and nine-section structure.
2. Codex reads repository context before acting.
3. Codex executes only the approved scope.
4. Codex creates the requested deliverables.
5. Codex validates outputs and protected boundaries.
6. Codex updates project state only if the batch requested a state transition.
7. Codex reports a Chinese summary and stops without auto-advancing unless Main approved the next phase.

## Batch Types

| Batch Type | Purpose | May Add Code | May Change Research State | May Change Execution Behavior |
| --- | --- | --- | --- | --- |
| Research | Analyze evidence and produce research conclusions. | No, except small helper scripts if explicitly approved. | Yes, only research status and reports. | No. |
| Engineering | Build or fix implementation within approved boundaries. | Yes. | Only if explicitly required. | No, unless the batch explicitly approves activation. |
| Validation | Verify existing outputs, consistency, coverage, or readiness. | No. | Yes, validation/readiness status only. | No. |
| Governance | Establish standards, templates, versioning, context, or process infrastructure. | No, except documentation/tooling support if approved. | Only governance/infrastructure status. | No. |

## Standard Batch Header

Each batch must begin with:

```text
Batch Name: <name>
Batch Type: Research | Engineering | Validation | Governance
Current Phase: <phase name or N/A>
Current Batch: <batch name>
Objective: <one sentence>
Scope: <allowed boundary and protected boundary>
```

The header is the first parse surface for Codex. If the header conflicts with later text, Codex must prefer the stricter boundary and ask Main only when the conflict blocks execution.

## Standard Nine-Section Structure

Every batch should use these sections:

1. Context
2. Objective
3. Scope
4. Inputs
5. Method
6. Deliverables
7. Validation
8. State Transition
9. Chinese Summary

Sections may be short, but should not be omitted. If a section is not applicable, write `N/A` and explain why.

## Template Registry

Use these templates:

- Research: `docs/templates/research_batch_template.md`
- Engineering: `docs/templates/engineering_batch_template.md`
- Validation: `docs/templates/validation_batch_template.md`
- Governance: `docs/templates/governance_batch_template.md`

## Naming Standard

Recommended naming:

```text
<Project Area> Phase <N or Letter> - <Objective>
```

For infrastructure work:

```text
Project Infrastructure - <Standard or Governance Objective> V<N>
```

For validation work:

```text
<Artifact or Phase> - <Validation Objective>
```

Avoid names that imply activation unless the batch explicitly authorizes activation.

## Scope Standard

Every batch must distinguish:

- Allowed work.
- Forbidden work.
- Protected files or systems.
- Whether state files may be updated.
- Whether the next phase may start.

Research, Validation, and Governance batches default to no execution behavior changes. Engineering batches default to implementation only, not activation.

## Validation Standard

Every batch validation section should confirm:

- Deliverables exist.
- Outputs are internally consistent.
- Protected boundaries were not crossed.
- State files match the deliverables.
- `scripts/context/validate_project_context.py` passes, or only documented existing warnings remain.

If validation cannot be completed, Codex must mark the batch incomplete or explicitly state the residual risk.

## State Transition Standard

State transitions must be explicit. A completed batch may update:

- `docs/current_phase_status.json`
- `docs/current_project_state.md`
- `PROJECT_INDEX.md`

State transitions must not imply:

- Preview has started.
- Formal execution is unblocked.
- Ranking, scoring, strategy, shadow, replay, universe, or exposure formulas changed.
- The next phase has started.

Unless Main explicitly approves the next phase, status should end with a Main review or authorization gate.

## Codex Recognition Rules

Codex should identify a batch by:

1. `Batch Type`.
2. `Objective`.
3. `Scope`.
4. `Forbidden` or `禁止` clauses.
5. `State Transition`.

Codex must treat repository state files and project index entries as recovery surfaces, not as permission to exceed the current batch scope.

## Versioning

This standard is V1. Future changes should create a new governance batch and update this file with a new version section instead of silently changing the rules.

## Report-path migration batch requirements

A report-path migration batch must declare every report-family Producer and Consumer, including Backend API, Dashboard consumer, App consumer, App补齐数据按钮, launchd/shell automation, daily/weekly generation, tests and Work/Codex. The batch inputs must include the Report Path Registry or approved migration mapping plus a deprecated-path inventory, compatibility period, `consumer-completeness` result and rollback plan.

The App backfill validation must cover button -> Backend API -> generator -> immutable dated artifact -> schema validation -> atomic alias update -> Dashboard/App reread -> displayed business date. `DATA_NOT_READY`, partial artifacts, Freshness Gate bypass, Availability staging writes and silent deprecated fallback are failures.

State rules:

- all file, Producer, Consumer, App, Dashboard, automation, Work/Codex and rollback gates pass: `MIGRATION_COMPLETE`;
- any gate missing or unverified: `MIGRATION_PARTIAL`;
- no migration batch may start while Reports Migration Phase B is `BLOCKED`;
- Formal Execution inputs migrate last or stay `RUNTIME_LOCKED`.

The standard validation stack includes a `deprecated-path` scan and `consumer-completeness` check for each authorized migration family.

## V1 Status

```text
Project Infrastructure = ACTIVE
Batch Standardization V1 = COMPLETE
Batch Standard Version = V1
Templates = DESIGNED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```
