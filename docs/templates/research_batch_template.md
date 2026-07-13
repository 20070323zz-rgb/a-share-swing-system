# Research Batch Template

## Batch Header

- Batch Name: `<phase_or_topic> - <short objective>`
- Batch Type: `Research`
- Current Phase: `<current phase>`
- Current Batch: `<current batch>`
- Objective: `<one sentence research question>`
- Scope: `Research analysis only; no model, strategy, ranking, preview, shadow, or formal execution changes unless explicitly approved.`

## 1. Context

Describe the repository-authoritative background, prior completed phases, current known constraints, and why this research question exists.

## 2. Objective

State the research question(s) this batch must answer. Keep the objective evaluable.

## 3. Scope

Allowed:

- Read existing repository artifacts.
- Produce research reports and decision artifacts.
- Update project state only after the batch is complete.

Forbidden unless explicitly approved:

- Modify Formal Execution, Shadow, Preview, Strategy, Ranking, Score, Universe, Replay, or model logic.
- Download data or rerun prior research to improve results.
- Convert research conclusions into execution behavior.

## 4. Inputs

List required repository files, reports, configs, datasets, or prior decision documents.

## 5. Method

Explain the research method, comparison dimensions, evidence rules, and uncertainty handling. Mark unrecoverable or unsupported claims explicitly.

## 6. Deliverables

List exact output files and whether each is a report, matrix, journal, or machine-readable artifact.

## 7. Validation

Confirm:

- Research conclusions are traceable to repository inputs.
- No forbidden execution, strategy, ranking, score, preview, shadow, universe, or replay changes were made.
- New reports do not contradict current state files.
- `scripts/context/validate_project_context.py` passes or only reports documented existing warnings.

## 8. State Transition

Define the exact status changes after successful completion. Do not auto-advance the next phase unless Main explicitly requested it.

## 9. Chinese Summary

Summarize in Chinese:

1. What question was answered.
2. What evidence was preserved.
3. What remains uncertain.
4. Whether the project can proceed, pause, or needs Main review.
