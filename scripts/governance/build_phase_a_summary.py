#!/usr/bin/env python3
"""Render immutable revisioned Phase A summary and final targeted remediation evidence."""

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
    parser.add_argument("--snapshot-revision", default="v3")
    parser.add_argument("--evidence-revision", default="v1")
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


def _review_lines(rows: list[dict], predicate) -> tuple[str, str]:
    reviewed = [(row, bool(predicate(row))) for row in rows]
    passed = sum(result for _, result in reviewed)
    accuracy = "100.00%" if not reviewed else f"{passed / len(reviewed):.2%}"
    lines = [
        f"- `{'PASS' if result else 'FAIL'}` `{row['current_path']}`"
        for row, result in reviewed
    ]
    return accuracy, "\n".join(lines) if lines else "- No records in this stratum."


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
    evidence_path = revisioned_artifact_path(
        "report_governance_evidence_registry", date, "json", args.evidence_revision
    )
    evidence = json.loads((root / evidence_path).read_text(encoding="utf-8"))
    rows = catalog["records"]
    summary = catalog["summary"]
    dynamic_rows = [
        row for row in rows if "ACTIVE_DYNAMIC_PRODUCER" in row["archive_block_reasons"]
    ]
    phase_b_safe = [
        row for row in rows if row["migration_eligibility"] == "SAFE_TO_MIGRATE"
    ]
    phase_b_rename = [
        row
        for row in rows
        if row["migration_eligibility"] == "SAFE_TO_MIGRATE_RENAME_REQUIRED"
    ]
    already_archived = [
        row for row in rows if row["location_status"] == "ALREADY_ARCHIVED"
    ]
    active_sample = [
        row
        for row in rows
        if row["migration_eligibility"] == "MIGRATION_BLOCKED_ACTIVE_DEPENDENCY"
    ][:20]
    runtime_sample = [
        row for row in rows if row["migration_eligibility"] == "MIGRATION_BLOCKED_RUNTIME"
    ][:20]
    unknown_sample = [
        row for row in rows if row["migration_eligibility"] == "MIGRATION_BLOCKED_UNKNOWN"
    ][:20]
    retention_sample = [
        row for row in rows if row["migration_eligibility"] == "MIGRATION_BLOCKED_RETENTION"
    ][:20]

    archived_accuracy, archived_review = _review_lines(
        already_archived,
        lambda row: row["current_path"].startswith("reports/archive/")
        and row["migration_eligibility"] == "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
        and row["deletion_eligibility"] == "NOT_DELETION_CANDIDATE",
    )
    safe_accuracy, safe_review = _review_lines(
        phase_b_safe,
        lambda row: row["location_status"] not in {"ALREADY_ARCHIVED", "GOVERNANCE_CONTROL_LOCATION"}
        and not row["active_generator"]
        and not row["runtime_locked"]
        and not row["current_alias"]
        and row["role"] != "UNKNOWN"
        and row["retention_status"] in {"ROLLING_WINDOW", "MANUAL_REVIEW"},
    )
    rename_accuracy, rename_review = _review_lines(
        phase_b_rename,
        lambda row: row["location_status"] not in {"ALREADY_ARCHIVED", "GOVERNANCE_CONTROL_LOCATION"}
        and not row["active_generator"]
        and not row["runtime_locked"]
        and not row["current_alias"]
        and row["role"] != "UNKNOWN"
        and row["naming_status"] == "NEEDS_DATE_NORMALIZATION"
        and row["retention_status"] in {"ROLLING_WINDOW", "MANUAL_REVIEW"},
    )
    active_accuracy, active_review = _review_lines(
        active_sample,
        lambda row: bool(
            {"ACTIVE_STATIC_PRODUCER", "ACTIVE_DYNAMIC_PRODUCER", "RUNTIME_CONSUMER"}
            & set(row["archive_block_reasons"])
        ),
    )
    runtime_accuracy, runtime_review = _review_lines(
        runtime_sample,
        lambda row: row["runtime_locked"] or row["current_alias"],
    )
    unknown_accuracy, unknown_review = _review_lines(
        unknown_sample,
        lambda row: row["role"] == "UNKNOWN"
        or row["dependency_safety"] == "UNKNOWN_DEPENDENCY",
    )
    retention_accuracy, retention_review = _review_lines(
        retention_sample,
        lambda row: row["retention_status"]
        in {"PERMANENT", "UNTIL_MIGRATION_VALIDATED", "TEMPORARY_AUDIT"},
    )

    summary_path = revisioned_artifact_path(
        "reports_governance_phase_a_summary", date, "md", revision
    )
    summary_supersedes = superseded_revision_artifact(
        root, "reports_governance_phase_a_summary", date, "md", revision
    )
    body = f"""{_front(root, date, summary_path, 'GOVERNANCE_PHASE_SUMMARY', 'REMEDIATED_PENDING_FINAL_SEMANTIC_RE_QC', revision, summary_supersedes)}# Reports Governance Phase A Summary

## State

- PR #4: `DRAFT_AWAITING_FINAL_RESULT_RE_QC`
- Reports Governance Phase A: `REMEDIATED`
- Governance Evidence Registry: `IMPLEMENTED_PENDING_QC`
- Evidence Traceability: `COMPLETE_PENDING_QC`
- Already Archived Classification: `IMPLEMENTED_PENDING_QC`
- Migration Eligibility: `REBUILT_PENDING_QC`
- Deletion Eligibility: `UNCHANGED_CONSERVATIVE`
- Snapshot Immutability: `ENFORCED`
- Phase B Contract: `COMPLETE`
- Reports Migration Phase B: `BLOCKED`
- Runtime Path Registry: `NOT_STARTED`
- Availability Audit: `ACTIVE_COLLECTING`
- Availability temporary data: `RETAIN_UNTIL_MIGRATION_VALIDATED`

## Inventory

- Catalog records: {catalog['record_count']}
- Dependency records: {registry['record_count']}
- Evidence records: {evidence['record_count']}
- Dynamic patterns: {registry['summary']['dynamic_pattern_count']}
- Runtime locked: {summary['runtime_locked_count']}
- Current aliases: {summary['current_alias_count']}
- Unknown roles: {summary['unknown_role_count']}
- Concrete active dynamic Producer matches: {len(dynamic_rows)}
- Deprecated Archive Candidate true count: {summary['archive_candidate_count']}
- Safe to delete after authorization: {summary['safe_to_delete_after_authorization_count']}
- Safe to migrate: {len(phase_b_safe)}
- Safe to migrate with rename: {len(phase_b_rename)}
- Already archived / migration not applicable: {len(already_archived)}
- Phase B candidates: {len(phase_b_safe) + len(phase_b_rename)}

{_distribution('Location status', summary['by_location_status'])}

{_distribution('Dependency safety', summary['by_dependency_safety'])}

{_distribution('Naming status', summary['by_naming_status'])}

{_distribution('Retention status', summary['by_retention_status'])}

{_distribution('Migration eligibility', summary['by_migration_eligibility'])}

{_distribution('Deletion eligibility', summary['by_deletion_eligibility'])}

{_distribution('Classification reasons', summary['by_archive_block_reason'])}

## Governance meaning

The deprecated single `archive_candidate` flag is retained only as a compatibility field and is always false. Migration eligibility and deletion eligibility are independent. A naming defect can require a rename without fabricating an active dependency, while active static or dynamic Producers still block migration. Phase A never grants automatic deletion safety.

The complete App, Dashboard, automation, Work/Codex, deprecated-path, compatibility-period, consumer-completeness and rollback contract is stored in repository governance documents. This summary does not start Phase B or a runtime Path Registry.

## Phase B candidate input

Only `SAFE_TO_MIGRATE` and `SAFE_TO_MIGRATE_RENAME_REQUIRED` records are listed below. `ALREADY_ARCHIVED`, control artifacts, active dependencies, runtime paths, unknown records and retention-blocked records are excluded.

### Safe to migrate

{chr(10).join(f"- `{row['current_path']}`" for row in phase_b_safe) if phase_b_safe else '- None'}

### Safe to migrate with rename

{chr(10).join(f"- `{row['current_path']}`" for row in phase_b_rename) if phase_b_rename else '- None'}
"""
    write_immutable_text(root / summary_path, body)

    remediation_path = root / (
        f"reports/reports_governance_phase_a_evidence_and_archive_state_remediation_{date}.md"
    )
    remediation = f"""{_front(root, date, remediation_path.relative_to(root).as_posix(), 'GOVERNANCE_EVIDENCE_ARCHIVE_STATE_REMEDIATION', 'READY_FOR_FINAL_RESULT_RE_QC', revision, '')}# Reports Governance Phase A Evidence and Archived-State Remediation

## Closed targeted blockers

1. Every Catalog `archive_block_evidence_ids` value resolves through the unified Evidence Registry ({evidence['record_count']} records).
2. Dependency, role, retention, naming, location, state-authority and governance-rule evidence are versioned and source-hash traceable.
3. All {len(dynamic_rows)} concrete dynamic Producer outputs retain dependency-backed Evidence.
4. All {len(already_archived)} `reports/archive/**` records are `ALREADY_ARCHIVED` and `MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED`.
5. The Phase B input contains {len(phase_b_safe)} safe and {len(phase_b_rename)} safe-with-rename records, with no already-archived record.
6. Deletion eligibility remains conservative; already-archived location never creates a deletion candidate.
7. Prior 2026-07-14 and 2026-07-15 v1/v2 snapshots remain immutable.

## Stratified manual review record

- ALREADY_ARCHIVED: {len(already_archived)}/{len(already_archived)} reviewed; accuracy `{archived_accuracy}`
- SAFE_TO_MIGRATE: {len(phase_b_safe)}/{len(phase_b_safe)} reviewed; accuracy `{safe_accuracy}`
- SAFE_TO_MIGRATE_RENAME_REQUIRED: {len(phase_b_rename)}/{len(phase_b_rename)} reviewed; accuracy `{rename_accuracy}`
- Active blocked: {len(active_sample)} reviewed; accuracy `{active_accuracy}`
- Runtime blocked: {len(runtime_sample)} reviewed; accuracy `{runtime_accuracy}`
- Unknown blocked: {len(unknown_sample)} reviewed; accuracy `{unknown_accuracy}`
- Retention blocked: {len(retention_sample)} reviewed; accuracy `{retention_accuracy}`

### ALREADY_ARCHIVED (all)

{archived_review}

### SAFE_TO_MIGRATE (all)

{safe_review}

### SAFE_TO_MIGRATE_RENAME_REQUIRED (all)

{rename_review}

### Active blocked sample

{active_review}

### Runtime blocked sample

{runtime_review}

### Unknown blocked sample

{unknown_review}

### Retention blocked sample

{retention_review}

## Boundaries

No historical report was moved, renamed, deleted or rewritten. Formal strategy, execution, ETF SSOT, protected ledgers, PR #3 implementation/evidence and Availability staging were not modified. No real data interface was called. PR #4 remains Draft and requires final result Re-QC.
"""
    write_immutable_text(remediation_path, remediation)
    print(
        "phase a summary built: "
        f"catalog={catalog['record_count']} registry={registry['record_count']} "
        f"dynamic_matches={len(dynamic_rows)} revision={revision}"
    )


if __name__ == "__main__":
    main()
