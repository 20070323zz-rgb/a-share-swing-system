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
        scan_dependencies,
        stable_report_id,
        superseded_artifact,
        write_csv,
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
        scan_dependencies,
        stable_report_id,
        superseded_artifact,
        write_csv,
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    registry_path = root / f"reports/report_dependency_registry_{date}.json"
    if registry_path.exists():
        dependencies = json.loads(registry_path.read_text(encoding="utf-8"))["records"]
    else:
        dependencies = scan_dependencies(root)
    records = build_catalog_records(root, dependencies)
    catalog_stem = f"report_catalog_{date}"
    catalog_json = f"reports/{catalog_stem}.json"
    metadata = artifact_metadata(
        root,
        date,
        stable_report_id(catalog_json),
        len(records),
        superseded_artifact(root, date, "reports/report_catalog_{date}.json"),
    )
    exclusions = [
        f"reports/report_catalog_{date}.csv",
        f"reports/report_catalog_{date}.json",
        f"reports/report_catalog_{date}.md",
        f"reports/report_dependency_registry_{date}.csv",
        f"reports/report_dependency_registry_{date}.json",
        f"reports/report_dependency_summary_{date}.md",
        f"reports/report_naming_compliance_audit_{date}.csv",
        f"reports/report_naming_compliance_audit_{date}.metadata.json",
        f"reports/reports_governance_phase_a_summary_{date}.md",
        f"reports/reports_governance_phase_a_remediation_{date}.md",
        f"reports/reports_governance_phase_a_final_blocker_remediation_{date}.md",
        f"reports/reports_governance_phase_a_dynamic_producer_remediation_{date}.md",
    ]
    payload = catalog_payload(records, metadata, exclusions)
    write_json(root / f"reports/{catalog_stem}.json", payload)
    csv_rows = []
    for row in records:
        csv_row = dict(row)
        csv_row["producer_candidates"] = "|".join(row["producer_candidates"])
        csv_row["consumer_candidates"] = "|".join(row["consumer_candidates"])
        csv_row["matched_dynamic_producer_ids"] = "|".join(row["matched_dynamic_producer_ids"])
        csv_rows.append(csv_row)
    write_csv(root / f"reports/{catalog_stem}.csv", csv_rows, FIELDS)
    catalog_path = f"reports/{catalog_stem}.md"
    catalog_front_matter = markdown_front_matter(
        report_id=stable_report_id(catalog_path),
        report_type="REPORT_CATALOG",
        business_date=date,
        created_at=metadata["generated_at"],
        status="REBUILT_PENDING_RE_QC",
        producer="scripts/governance/build_report_catalog.py",
        source_run_id=f"reports-governance-phase-a-remediation-{date}",
        supersedes=superseded_artifact(root, date, "reports/report_catalog_{date}.md"),
    )
    (root / catalog_path).write_text(
        render_catalog_markdown(payload, catalog_front_matter), encoding="utf-8"
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
    naming_path = f"reports/report_naming_compliance_audit_{date}.csv"
    write_csv(root / naming_path, naming_rows, naming_fields)
    naming_meta = artifact_metadata(
        root,
        date,
        stable_report_id(naming_path),
        len(naming_rows),
        superseded_artifact(root, date, "reports/report_naming_compliance_audit_{date}.metadata.json"),
    )
    naming_meta["artifact_path"] = naming_path
    naming_meta["retention_class"] = "PERMANENT"
    write_json(root / f"reports/report_naming_compliance_audit_{date}.metadata.json", naming_meta)
    print(
        "report catalog built: "
        f"records={payload['record_count']} runtime_locked={payload['summary']['runtime_locked_count']} "
        f"archive_candidates={payload['summary']['archive_candidate_count']}"
    )


if __name__ == "__main__":
    main()
