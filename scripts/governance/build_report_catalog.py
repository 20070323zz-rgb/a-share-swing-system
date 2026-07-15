#!/usr/bin/env python3
"""Build the Reports Governance Phase A catalog without moving any report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        build_catalog_records,
        catalog_payload,
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        render_catalog_markdown,
        revisioned_artifact_path,
        scan_dependencies,
        stable_report_id,
        superseded_revision_artifact,
        write_csv,
        write_immutable_text,
        write_json,
    )
except ModuleNotFoundError:  # Direct script execution.
    from report_governance_common import (  # type: ignore
        build_catalog_records,
        catalog_payload,
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        render_catalog_markdown,
        revisioned_artifact_path,
        scan_dependencies,
        stable_report_id,
        superseded_revision_artifact,
        write_csv,
        write_immutable_text,
        write_json,
    )


FIELDS = [
    "report_id",
    "current_path",
    "filename",
    "extension",
    "role",
    "cadence",
    "topic",
    "status",
    "business_date",
    "created_date",
    "modified_at",
    "producer_candidates",
    "consumer_candidates",
    "reference_count",
    "matched_dynamic_producer_count",
    "matched_dynamic_producer_ids",
    "dynamic_producer_match_confidence",
    "active_generator",
    "producer_match_type",
    "archive_block_reason",
    "archive_block_reasons",
    "primary_archive_block_reason",
    "archive_block_evidence_ids",
    "archive_block_evidence",
    "dependency_safety",
    "naming_status",
    "retention_status",
    "migration_eligibility",
    "deletion_eligibility",
    "runtime_locked",
    "current_alias",
    "dated_artifact",
    "archive_candidate",
    "migration_risk",
    "naming_compliance",
    "metadata_compliance",
    "confidence",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    parser.add_argument("--business-date", default=business_date_today())
    parser.add_argument("--snapshot-revision", default="v2")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    revision = args.snapshot_revision
    if not revision.startswith("v") or not revision[1:].isdigit():
        raise SystemExit("--snapshot-revision must look like v2")
    registry_json = revisioned_artifact_path(
        "report_dependency_registry", date, "json", revision
    )
    registry_path = root / registry_json
    if registry_path.exists():
        dependencies = json.loads(registry_path.read_text(encoding="utf-8"))["records"]
    else:
        dependencies = scan_dependencies(root)
    records = build_catalog_records(root, dependencies)
    catalog_json = revisioned_artifact_path("report_catalog", date, "json", revision)
    catalog_csv = revisioned_artifact_path("report_catalog", date, "csv", revision)
    catalog_md = revisioned_artifact_path("report_catalog", date, "md", revision)
    metadata = artifact_metadata(
        root,
        date,
        stable_report_id(catalog_json),
        len(records),
        superseded_revision_artifact(root, "report_catalog", date, "json", revision),
        revision,
    )
    exclusions = [
        catalog_csv,
        catalog_json,
        catalog_md,
        revisioned_artifact_path("report_dependency_registry", date, "csv", revision),
        registry_json,
        revisioned_artifact_path("report_dependency_summary", date, "md", revision),
        revisioned_artifact_path("report_naming_compliance_audit", date, "csv", revision),
        revisioned_artifact_path(
            "report_naming_compliance_audit", date, "metadata.json", revision
        ),
        revisioned_artifact_path("reports_governance_phase_a_summary", date, "md", revision),
    ]
    payload = catalog_payload(records, metadata, exclusions)
    write_json(root / catalog_json, payload, immutable=True)
    csv_rows = []
    for row in records:
        csv_row = dict(row)
        csv_row["producer_candidates"] = "|".join(row["producer_candidates"])
        csv_row["consumer_candidates"] = "|".join(row["consumer_candidates"])
        csv_row["matched_dynamic_producer_ids"] = "|".join(row["matched_dynamic_producer_ids"])
        csv_row["archive_block_reasons"] = "|".join(row["archive_block_reasons"])
        csv_row["archive_block_evidence_ids"] = "|".join(row["archive_block_evidence_ids"])
        csv_row["archive_block_evidence"] = json.dumps(
            row["archive_block_evidence"], ensure_ascii=False, sort_keys=True
        )
        csv_rows.append(csv_row)
    write_csv(root / catalog_csv, csv_rows, FIELDS, immutable=True)
    catalog_path = catalog_md
    catalog_front_matter = markdown_front_matter(
        report_id=stable_report_id(catalog_path),
        report_type="REPORT_CATALOG",
        business_date=date,
        created_at=metadata["generated_at"],
        status="REBUILT_PENDING_RE_QC",
        producer="scripts/governance/build_report_catalog.py",
        source_run_id=f"reports-governance-phase-a-remediation-{date}",
        supersedes=superseded_revision_artifact(
            root, "report_catalog", date, "md", revision
        ),
        snapshot_revision=revision,
    )
    write_immutable_text(
        root / catalog_path, render_catalog_markdown(payload, catalog_front_matter)
    )

    naming_fields = [
        "report_id",
        "current_path",
        "role",
        "business_date",
        "current_alias",
        "runtime_locked",
        "naming_compliance",
        "metadata_compliance",
        "notes",
    ]
    naming_rows = [{field: row[field] for field in naming_fields} for row in records]
    naming_path = revisioned_artifact_path(
        "report_naming_compliance_audit", date, "csv", revision
    )
    write_csv(root / naming_path, naming_rows, naming_fields, immutable=True)
    naming_meta = artifact_metadata(
        root,
        date,
        stable_report_id(naming_path),
        len(naming_rows),
        superseded_revision_artifact(
            root, "report_naming_compliance_audit", date, "metadata.json", revision
        ),
        revision,
    )
    naming_meta["artifact_path"] = naming_path
    naming_meta["retention_class"] = "PERMANENT"
    naming_metadata_path = revisioned_artifact_path(
        "report_naming_compliance_audit", date, "metadata.json", revision
    )
    write_json(root / naming_metadata_path, naming_meta, immutable=True)
    print(
        "report catalog built: "
        f"records={payload['record_count']} runtime_locked={payload['summary']['runtime_locked_count']} "
        f"archive_candidates={payload['summary']['archive_candidate_count']}"
    )


if __name__ == "__main__":
    main()
