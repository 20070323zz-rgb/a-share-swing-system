#!/usr/bin/env python3
"""Build the immutable unified Reports Governance Evidence Registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.governance.evidence_registry import (
        EVIDENCE_FIELDS,
        build_evidence_records,
        evidence_payload,
    )
    from scripts.governance.report_governance_common import (
        artifact_metadata,
        business_date_today,
        project_root_from_script,
        revisioned_artifact_path,
        stable_report_id,
        superseded_revision_artifact,
        write_csv,
        write_json,
    )
except ModuleNotFoundError:  # Direct script execution.
    from evidence_registry import EVIDENCE_FIELDS, build_evidence_records, evidence_payload  # type: ignore
    from report_governance_common import (  # type: ignore
        artifact_metadata,
        business_date_today,
        project_root_from_script,
        revisioned_artifact_path,
        stable_report_id,
        superseded_revision_artifact,
        write_csv,
        write_json,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    parser.add_argument("--business-date", default=business_date_today())
    parser.add_argument("--catalog-revision", default="v3")
    parser.add_argument("--dependency-revision", default="v3")
    parser.add_argument("--snapshot-revision", default="v1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    catalog_path = revisioned_artifact_path(
        "report_catalog", date, "json", args.catalog_revision
    )
    dependency_path = revisioned_artifact_path(
        "report_dependency_registry", date, "json", args.dependency_revision
    )
    evidence_json = revisioned_artifact_path(
        "report_governance_evidence_registry", date, "json", args.snapshot_revision
    )
    evidence_csv = revisioned_artifact_path(
        "report_governance_evidence_registry", date, "csv", args.snapshot_revision
    )
    catalog = json.loads((root / catalog_path).read_text(encoding="utf-8"))
    dependency_registry = json.loads((root / dependency_path).read_text(encoding="utf-8"))
    records = build_evidence_records(
        root,
        catalog,
        dependency_registry,
        catalog_path=catalog_path,
        dependency_registry_path=dependency_path,
    )
    metadata = artifact_metadata(
        root,
        date,
        stable_report_id(evidence_json),
        len(records),
        superseded_revision_artifact(
            root,
            "report_governance_evidence_registry",
            date,
            "json",
            args.snapshot_revision,
        ),
        args.snapshot_revision,
    )
    metadata["catalog_snapshot_revision"] = args.catalog_revision
    metadata["dependency_snapshot_revision"] = args.dependency_revision
    payload = evidence_payload(records, metadata)
    write_json(root / evidence_json, payload, immutable=True)
    write_csv(root / evidence_csv, records, EVIDENCE_FIELDS, immutable=True)
    print(f"governance evidence registry built: records={len(records)} revision={args.snapshot_revision}")


if __name__ == "__main__":
    main()
