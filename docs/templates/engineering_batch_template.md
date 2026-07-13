# Engineering Batch Template

## Batch Header

- Batch Name: `<phase_or_feature> - <short implementation objective>`
- Batch Type: `Engineering`
- Current Phase: `<current phase>`
- Current Batch: `<current batch>`
- Objective: `<one sentence implementation goal>`
- Scope: `Implementation work only within approved files and behavior boundaries.`

## 1. Context

Describe the operational problem, existing implementation surface, protected boundaries, and current project state.

## 2. Objective

State what must be built, fixed, or refactored. Include expected user-visible or artifact-visible behavior.

## 3. Scope

Allowed:

- Modify approved source files, scripts, configs, tests, or docs.
- Add focused tests or validation scripts when useful.
- Update project state after verification.

Forbidden unless explicitly approved:

- Change Strategy, Ranking, Score, Preview, Shadow, Formal Execution, Universe, or research conclusions.
- Rewrite unrelated modules.
- Delete or overwrite historical artifacts.

## 4. Inputs

List relevant source files, configs, test fixtures, reports, and state files.

## 5. Method

Describe the implementation approach, compatibility rules, migration strategy, and rollback/recovery expectations.

## 6. Deliverables

List exact code, config, doc, report, or test outputs.

## 7. Validation

Confirm:

- Implementation behaves as intended.
- Existing protected behavior remains unchanged.
- Relevant tests or scripts were run.
- `scripts/context/validate_project_context.py` passes or only reports documented existing warnings.

## 8. State Transition

Define the exact status changes after successful completion. Keep activation or promotion as a separate Main approval gate when applicable.

## 9. Chinese Summary

Summarize in Chinese:

1. What was implemented.
2. What files changed.
3. What was verified.
4. What stayed unchanged.
5. Whether Main approval is needed for activation.
