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
        project_root_from_script,
        render_catalog_markdown,
        scan_dependencies,
        write_csv,
        write_json,
    )
except ModuleNotFoundError:  # Direct script execution.
    from report_governance_common import (  # type: ignore
        build_catalog_records,
        catalog_payload,
        project_root_from_script,
        render_catalog_markdown,
        scan_dependencies,
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    registry_path = root / "reports/report_dependency_registry.json"
    if registry_path.exists():
        dependencies = json.loads(registry_path.read_text(encoding="utf-8"))["records"]
    else:
        dependencies = scan_dependencies(root)
    records = build_catalog_records(root, dependencies)
    payload = catalog_payload(records)
    write_json(root / "reports/report_catalog.json", payload)
    csv_rows = []
    for row in records:
        csv_row = dict(row)
        csv_row["producer_candidates"] = "|".join(row["producer_candidates"])
        csv_row["consumer_candidates"] = "|".join(row["consumer_candidates"])
        csv_rows.append(csv_row)
    write_csv(root / "reports/report_catalog.csv", csv_rows, FIELDS)
    (root / "reports/report_catalog.md").write_text(render_catalog_markdown(payload), encoding="utf-8")
    print(
        "report catalog built: "
        f"records={payload['record_count']} runtime_locked={payload['summary']['runtime_locked_count']} "
        f"archive_candidates={payload['summary']['archive_candidate_count']}"
    )


if __name__ == "__main__":
    main()
