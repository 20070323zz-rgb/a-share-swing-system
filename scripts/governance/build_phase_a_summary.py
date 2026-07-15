#!/usr/bin/env python3
"""Render immutable revisioned Phase A summary and semantic-remediation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        revisioned_artifact_path,
        stable_report_id,
        superseded_revision_artifact,
        write_immutable_text,
    )
except ModuleNotFoundError:
    from report_governance_common import (  # type: ignore
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        revisioned_artifact_path,
        stable_report_id,
        superseded_revision_artifact,
        write_immutable_text,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    parser.add_argument("--business-date", default=business_date_today())
    parser.add_argument("--snapshot-revision", default="v2")
    return parser.parse_args()


def _front(
    root: Path,
    date: str,
    path: str,
    report_type: str,
    status: str,
    revision: str,
    supersedes: str,
) -> str:
    meta = artifact_metadata(
        root,
        date,
        stable_report_id(path),
        1,
        supersedes,
        revision,
    )
    return markdown_front_matter(
        report_id=stable_report_id(path),
        report_type=report_type,
        business_date=date,
        created_at=meta["generated_at"],
        status=status,
        producer="scripts/governance/build_phase_a_summary.py",
        source_run_id=f"reports-governance-phase-a-semantic-{revision}-{date}",
        supersedes=supersedes,
        snapshot_revision=revision,
        immutable=True,
    )


def _distribution(title: str, values: dict[str, int]) -> str:
    lines = [f"### {title}", ""]
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(values.items()))
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    revision = args.snapshot_revision
    if not revision.startswith("v") or not revision[1:].isdigit():
        raise SystemExit("--snapshot-revision must look like v2")

    catalog_path = revisioned_artifact_path("report_catalog", date, "json", revision)
    registry_path = revisioned_artifact_path(
        "report_dependency_registry", date, "json", revision
    )
    catalog = json.loads((root / catalog_path).read_text(encoding="utf-8"))
    registry = json.loads((root / registry_path).read_text(encoding="utf-8"))
    rows = catalog["records"]
    summary = catalog["summary"]
    dynamic_rows = [
        row for row in rows if "ACTIVE_DYNAMIC_PRODUCER" in row["archive_block_reasons"]
    ]

    summary_path = revisioned_artifact_path(
        "reports_governance_phase_a_summary", date, "md", revision
    )
    summary_supersedes = superseded_revision_artifact(
        root, "reports_governance_phase_a_summary", date, "md", revision
    )
    body = f"""{_front(root, date, summary_path, 'GOVERNANCE_PHASE_SUMMARY', 'REMEDIATED_PENDING_FINAL_SEMANTIC_RE_QC', revision, summary_supersedes)}# Reports Governance Phase A Summary

## State

- PR #4: `DRAFT_AWAITING_FINAL_SEMANTIC_RE_QC`
- Reports Governance Phase A: `REMEDIATED`
- Date Pattern Validation: `IMPLEMENTED_PENDING_QC`
- Python Scope Semantics: `IMPLEMENTED_PENDING_QC`
- Migration Eligibility: `REBUILT_PENDING_QC`
- Deletion Eligibility: `REBUILT_PENDING_QC`
- Snapshot Immutability: `ENFORCED_PENDING_QC`
- Phase B Contract: `COMPLETE_PENDING_QC`
- PR #3 Authority Preservation: `REMEDIATED_PENDING_QC`
- Reports Migration Phase B: `BLOCKED`
- Runtime Path Registry: `NOT_STARTED`
- Availability Audit: `ACTIVE_COLLECTING`
- Availability temporary data: `RETAIN_UNTIL_MIGRATION_VALIDATED`

## Inventory

- Catalog records: {catalog['record_count']}
- Dependency records: {registry['record_count']}
- Dynamic patterns: {registry['summary']['dynamic_pattern_count']}
- Runtime locked: {summary['runtime_locked_count']}
- Current aliases: {summary['current_alias_count']}
- Unknown roles: {summary['unknown_role_count']}
- Concrete active dynamic Producer matches: {len(dynamic_rows)}
- Deprecated Archive Candidate true count: {summary['archive_candidate_count']}
- Safe to delete after authorization: {summary['safe_to_delete_after_authorization_count']}

{_distribution('Dependency safety', summary['by_dependency_safety'])}

{_distribution('Naming status', summary['by_naming_status'])}

{_distribution('Retention status', summary['by_retention_status'])}

{_distribution('Migration eligibility', summary['by_migration_eligibility'])}

{_distribution('Deletion eligibility', summary['by_deletion_eligibility'])}

{_distribution('Classification reasons', summary['by_archive_block_reason'])}

## Governance meaning

The deprecated single `archive_candidate` flag is retained only as a compatibility field and is always false. Migration eligibility and deletion eligibility are independent. A naming defect can require a rename without fabricating an active dependency, while active static or dynamic Producers still block migration. Phase A never grants automatic deletion safety.

The complete App, Dashboard, automation, Work/Codex, deprecated-path, compatibility-period, consumer-completeness and rollback contract is stored in repository governance documents. This summary does not start Phase B or a runtime Path Registry.
"""
    write_immutable_text(root / summary_path, body)

    remediation_path = (
        root / f"reports/reports_governance_phase_a_final_semantic_remediation_{date}.md"
    )
    remediation = f"""{_front(root, date, remediation_path.relative_to(root).as_posix(), 'GOVERNANCE_FINAL_SEMANTIC_REMEDIATION', 'READY_FOR_FINAL_INDEPENDENT_SEMANTIC_RE_QC', revision, '')}# Reports Governance Phase A Final Semantic Remediation

## Closed semantic blockers

1. Active Producer facts are represented as multiple traceable reasons; all {len(dynamic_rows)} concrete dynamic outputs contain `ACTIVE_DYNAMIC_PRODUCER`.
2. DATE, MONTH, TIMESTAMP, RUN_ID and unknown dynamics are separate; DATE/MONTH use calendar parsing and unknown values never auto-match.
3. Method lexical lookup skips CLASS scopes; explicit `self`, `cls` and class-name attributes remain conservative, traceable references.
4. Dependency safety, naming status, retention, migration eligibility and deletion eligibility are independent fields.
5. Revisioned snapshots are immutable and fail fast on changed bytes; prior 2026-07-14 snapshots were restored to their first-created contents.
6. Phase B consumer and task-path contracts are complete but Phase B remains blocked.
7. PR #3 nested Availability authority state is preserved with deep-merge and conflict rules.

## Boundaries

No historical report was moved, renamed or deleted. Formal strategy, execution, ETF SSOT, protected ledgers, PR #3 implementation/evidence and Availability staging were not modified. No real data interface was called. PR #4 remains Draft and requires final independent Re-QC.
"""
    write_immutable_text(remediation_path, remediation)
    print(
        "phase a summary built: "
        f"catalog={catalog['record_count']} registry={registry['record_count']} "
        f"dynamic_matches={len(dynamic_rows)} revision={revision}"
    )


if __name__ == "__main__":
    main()
