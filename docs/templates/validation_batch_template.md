# Validation Batch Template

## Batch Header

- Batch Name: `<artifact_or_phase> - <validation objective>`
- Batch Type: `Validation`
- Current Phase: `<current phase>`
- Current Batch: `<current batch>`
- Objective: `<one sentence validation goal>`
- Scope: `Validate existing outputs only; do not create new model behavior or improve results.`

## 1. Context

Describe what has already been produced, what needs validation, and which prior conclusions are in scope.

## 2. Objective

State the exact validation questions and the verdict options that must be returned.

## 3. Scope

Allowed:

- Read existing outputs and source artifacts.
- Produce validation reports and consistency matrices.
- Update project state only after validation is complete.

Forbidden unless explicitly approved:

- Rerun experiments to improve results.
- Modify formulas, strategy, ranking, score, preview, shadow, formal execution, universe, or protected data.
- Treat validation as approval for activation.

## 4. Inputs

List reports, JSON/CSV outputs, configs, manifests, and state files to validate.

## 5. Method

Describe coverage checks, consistency checks, sensitivity checks, or replay-independent audit methods.

## 6. Deliverables

List validation summaries, metrics, matrices, and status updates.

## 7. Validation

Confirm:

- Validation uses only approved inputs.
- Findings are traceable to repository artifacts.
- No formulas, experiments, model behavior, or execution logic were changed.
- `scripts/context/validate_project_context.py` passes or only reports documented existing warnings.

## 8. State Transition

Define validation status and downstream readiness. Do not automatically start the next research or engineering phase.

## 9. Chinese Summary

Summarize in Chinese:

1. What was validated.
2. Whether outputs are internally consistent.
3. What passed and what did not.
4. What remains blocked or pending Main review.
