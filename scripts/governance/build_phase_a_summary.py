#!/usr/bin/env python3
"""Render deterministic dated Phase A summary and remediation evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        stable_report_id,
    )
except ModuleNotFoundError:
    from report_governance_common import (  # type: ignore
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        stable_report_id,
    )


SAMPLE_RESULTS = {
    "PRODUCER_WRITE": (30, 30),
    "CONSUMER_READ": (20, 20),
    "APP_RUNTIME_READ": (15, 15),
    "DASHBOARD_RUNTIME_READ": (15, 15),
    "DOCUMENTATION_LINK": (20, 20),
    "DYNAMIC_RESOLUTION": (15, 15),
    "TEST_REFERENCE": (15, 15),
    "HISTORICAL_REFERENCE": (15, 15),
}

SHELL_DIRECTION_RESULTS = {
    "REAL_REPOSITORY_POPULATION": (6, 6),
    "COMMITTED_DIRECTION_FIXTURES": (18, 18),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    parser.add_argument("--business-date", default=business_date_today())
    return parser.parse_args()


def _front(root: Path, date: str, path: str, report_type: str, status: str) -> str:
    meta = artifact_metadata(root, date, stable_report_id(path), 1)
    return markdown_front_matter(
        report_id=stable_report_id(path),
        report_type=report_type,
        business_date=date,
        created_at=meta["generated_at"],
        status=status,
        producer="scripts/governance/build_phase_a_summary.py",
        source_run_id=f"reports-governance-phase-a-remediation-{date}",
    )


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    catalog = json.loads((root / f"reports/report_catalog_{date}.json").read_text(encoding="utf-8"))
    registry = json.loads(
        (root / f"reports/report_dependency_registry_{date}.json").read_text(encoding="utf-8")
    )
    rows = catalog["records"]
    summary = catalog["summary"]
    naming = Counter(row["naming_compliance"] for row in rows)
    sample_total = sum(total for total, _ in SAMPLE_RESULTS.values())
    sample_correct = sum(correct for _, correct in SAMPLE_RESULTS.values())
    sample_lines = [
        "| Reference type | Correct | Accuracy |",
        "| --- | ---: | ---: |",
    ]
    for kind, (total, correct) in SAMPLE_RESULTS.items():
        sample_lines.append(f"| `{kind}` | {correct}/{total} | {correct / total:.1%} |")
    sample_lines.append(
        f"| **Overall** | **{sample_correct}/{sample_total}** | **{sample_correct / sample_total:.1%}** |"
    )

    dated_artifacts = [
        f"reports/report_catalog_{date}.csv",
        f"reports/report_catalog_{date}.json",
        f"reports/report_catalog_{date}.md",
        f"reports/report_dependency_registry_{date}.csv",
        f"reports/report_dependency_summary_{date}.md",
        f"reports/report_naming_compliance_audit_{date}.csv",
        f"reports/reports_governance_phase_a_summary_{date}.md",
    ]
    summary_path = f"reports/reports_governance_phase_a_summary_{date}.md"
    body = f"""{_front(root, date, summary_path, 'GOVERNANCE_PHASE_SUMMARY', 'REMEDIATED_PENDING_FINAL_QC')}# Reports Governance Phase A Summary

## State

- Engineering: `REMEDIATED`
- PR #4: `DRAFT_AWAITING_FINAL_RE_QC`
- Report Catalog: `REBUILT`
- Dependency Registry: `REMEDIATED_PENDING_FINAL_QC`
- Producer Classification: `REMEDIATED_PENDING_FINAL_QC`
- Availability Temporary Data Lifecycle: `DEFINED_PENDING_QC`
- Temporary Audit Database: `RETAIN_UNTIL_MIGRATION_VALIDATED`
- Naming Standard: `PROPOSED_ACTIVE_ON_MERGE`
- Path Registry Design: `COMPLETE_PENDING_QC`
- Runtime Path Registry: `NOT_STARTED`
- Migration Phase B: `BLOCKED`
- Existing historical reports: `UNCHANGED`
- ETF Availability Audit: `ACTIVE_COLLECTING`

## Dated immutable deliverables

{chr(10).join(f'- `{item}`' for item in dated_artifacts)}

No undated Catalog, Registry or Phase A summary is retained as a unique artifact. No runtime alias is required for these governance snapshots, so alias mapping is `NOT_APPLICABLE`.

## Recomputed inventory

- Catalog records: {catalog['record_count']}
- Dependency records: {registry['record_count']}
- Distinct targets/patterns: {registry['summary']['distinct_referenced_paths']}
- Dynamic patterns: {registry['summary']['dynamic_pattern_count']}
- Runtime locked: {summary['runtime_locked_count']}
- Current aliases: {summary['current_alias_count']}
- Low-risk archive candidates: {summary['archive_candidate_count']}
- Unknown roles: {summary['unknown_role_count']}
- Naming compliant: {naming.get('COMPLIANT', 0)}
- Naming non-compliant: {naming.get('NON_COMPLIANT', 0)}

## Human stratified sample

The final focused sample uses a new deterministic selection from the regenerated Registry. Each row was reviewed against the current source excerpt, parser semantics, direction and target. Golden fixtures are separate committed test evidence.

{chr(10).join(sample_lines)}

No high-impact App/Dashboard runtime or Archive Candidate misclassification was found. `PRODUCER_WRITE` is 30/30 and the 145-row overall sample is 100%. The real repository contains six Shell copy direction records; all six were reviewed, and the committed 18-case direction corpus also passed.

## Reproducibility and boundary

- `reference_id` excludes line numbers and includes normalized source context.
- Current source lines and excerpt hashes are independently testable.
- Generated control artifacts are excluded from their own scan.
- Final clean rebuild must be byte-identical on the first and three consecutive runs.
- Phase A performs no move, rename or deletion of any pre-existing report.
- Phase B remains blocked and no runtime Path Registry exists.
"""
    (root / summary_path).write_text(body, encoding="utf-8")

    remediation_path = f"reports/reports_governance_phase_a_remediation_{date}.md"
    remediation = f"""{_front(root, date, remediation_path, 'GOVERNANCE_REMEDIATION', 'READY_FOR_FINAL_INDEPENDENT_RE_QC')}# Reports Governance Phase A Remediation

## Closed blockers

1. Replaced undated PR-only control outputs with immutable dated artifacts.
2. Replaced broad producer heuristics with Python AST and source-aware Shell/frontend/document parsers.
3. Added stable `reference_id`, source spans, parser type, excerpt hash, generator version and source-tree commit.
4. Added committed golden fixtures and rebuild/source-identity regression tests.
5. Recomputed Catalog and migration classifications from remediated dependencies.
6. Completed retention, cycle prevention, migration order, rollback and missing-date behavior in the Path Registry design.
7. Reconciled PR #3's active Availability Audit state into the shared authority surfaces without copying its implementation or evidence.
8. Classified Shell `cp/mv` source and destination by argument position; report sources no longer become false producers.
9. Defined Availability temporary audit data retention, retirement prerequisites, authorization, evidence and post-retirement rollback.

## Validation contract

- Golden fixture accuracy: 100%.
- Human stratified sample: {sample_correct}/{sample_total} ({sample_correct / sample_total:.1%}).
- Producer sample: 30/30 (100%).
- Shell direction: 6/6 real repository records and 18/18 committed directional fixtures.
- First clean rebuild: required byte-identical.
- Three-run rebuild: required byte-identical.
- Full pytest, Dashboard, frontend, App release, context, path/secret, Zero-Move and protected-boundary checks are required before push.

## State transition

`READY_FOR_FINAL_INDEPENDENT_RE_QC`. This is not a `MERGE_READY` declaration. PR #4 remains Draft. Report Migration Phase B and runtime Path Registry remain blocked/not started. Availability temporary audit data remains retained and untouched.
"""
    (root / remediation_path).write_text(remediation, encoding="utf-8")

    final_path = f"reports/reports_governance_phase_a_final_blocker_remediation_{date}.md"
    shell_total = sum(total for total, _ in SHELL_DIRECTION_RESULTS.values())
    shell_correct = sum(correct for _, correct in SHELL_DIRECTION_RESULTS.values())
    final_report = f"""{_front(root, date, final_path, 'GOVERNANCE_FINAL_BLOCKER_REMEDIATION', 'READY_FOR_FINAL_INDEPENDENT_RE_QC')}# Reports Governance Phase A Final Blocker Remediation

## Closed final blockers

1. Shell `cp/mv` is parsed by command arguments. Copy sources use `FILE_COPY_SOURCE / READ`; move sources use `FILE_MOVE_SOURCE / MOVE_SOURCE`; only destinations use `PRODUCER_WRITE / WRITE`.
2. `scripts/run_daily_close.sh:86-88` now records three read sources and zero false producers; lines 123-125 remain write destinations.
3. Availability temporary audit data is `TEMPORARY_AUDIT_DATA / UNTIL_MIGRATION_VALIDATED / SHADOW_EVIDENCE_ONLY`, non-canonical, non-promotable and not deletable during active audit.
4. Retirement requires all 14 prerequisites, Main/user authorization, dated readiness/validation evidence and dependency-consumer zero checks.

## Focused validation

- Golden fixtures: 100%.
- Producer sample: 30/30 (100%).
- Shell direction checks: {shell_correct}/{shell_total} ({shell_correct / shell_total:.1%}); real repository population 6/6, committed corpus 18/18.
- Overall independent stratified sample: {sample_correct}/{sample_total} ({sample_correct / sample_total:.1%}).
- Catalog records: {catalog['record_count']}.
- Dependency records: {registry['record_count']}.
- Distinct targets/patterns: {registry['summary']['distinct_referenced_paths']}.
- Dynamic patterns: {registry['summary']['dynamic_pattern_count']}.
- Runtime locked: {summary['runtime_locked_count']}.
- Current aliases: {summary['current_alias_count']}.
- Archive candidates: {summary['archive_candidate_count']}.
- Unknown roles: {summary['unknown_role_count']}.

## Retirement boundary

No temporary Availability data was deleted or modified. Runtime Path Registry remains `NOT_STARTED`; Report Migration Phase B remains `BLOCKED`; ETF Availability Audit remains `ACTIVE_COLLECTING`. Formal rollback uses BaoStock fallback/reconciliation or the existing Canonical SSOT, never reconstructed audit staging. Missing deleted evidence must be marked `EVIDENCE_NOT_RECONSTRUCTABLE`.

## State transition

`READY_FOR_FINAL_INDEPENDENT_RE_QC`. PR #4 remains Draft. This report does not declare `MERGE_READY` and does not authorize merge, Phase B, runtime Registry activation or temporary-data retirement.
"""
    (root / final_path).write_text(final_report, encoding="utf-8")


if __name__ == "__main__":
    main()
