# Governance Batch Template

## Batch Header

- Batch Name: `<governance topic> - <standardization objective>`
- Batch Type: `Governance`
- Current Phase: `<current phase>`
- Current Batch: `<current batch>`
- Objective: `<one sentence governance objective>`
- Scope: `Project governance, documentation, templates, status, and infrastructure only.`

## 1. Context

Describe the project process issue, repeated pain point, or governance gap this batch addresses.

## 2. Objective

State the standard, policy, template, versioning, or context artifact to establish.

## 3. Scope

Allowed:

- Add or update governance docs, templates, indexes, and project state files.
- Register new infrastructure artifacts.

Forbidden unless explicitly approved:

- Modify Strategy, Ranking, Score, Preview, Shadow, Formal Execution, Replay, Universe, Exposure formulas, or model logic.
- Change research conclusions or activate any research output.

## 4. Inputs

List existing governance docs, templates, state files, project index entries, and validation scripts.

## 5. Method

Describe the standardization method, naming rules, lifecycle rules, and compatibility expectations.

## 6. Deliverables

List new or updated governance docs, templates, and status files.

## 7. Validation

Confirm:

- Templates can be used directly by Main.
- Header fields and validation fields are consistent across templates.
- Project index and state files are updated.
- `scripts/context/validate_project_context.py` passes or only reports documented existing warnings.

## 8. State Transition

Define the infrastructure status after completion. Do not change research, strategy, or execution readiness unless explicitly requested.

## 9. Chinese Summary

Summarize in Chinese:

1. What governance artifact was created.
2. What standard is now in force.
3. How Main should use it.
4. How Codex should recognize it.
5. What remains unchanged.
