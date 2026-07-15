#!/usr/bin/env python3
"""Validate Catalog, Dependency Registry, and Evidence Registry integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.governance.evidence_registry import validate_evidence_integrity
    from scripts.governance.report_governance_common import (
        business_date_today,
        project_root_from_script,
        revisioned_artifact_path,
    )
except ModuleNotFoundError:  # Direct script execution.
    from evidence_registry import validate_evidence_integrity  # type: ignore
    from report_governance_common import business_date_today, project_root_from_script, revisioned_artifact_path  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    parser.add_argument("--business-date", default=business_date_today())
    parser.add_argument("--catalog-revision", default="v3")
    parser.add_argument("--dependency-revision", default="v3")
    parser.add_argument("--evidence-revision", default="v1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    date = args.business_date
    paths = {
        "catalog": revisioned_artifact_path("report_catalog", date, "json", args.catalog_revision),
        "dependency": revisioned_artifact_path("report_dependency_registry", date, "json", args.dependency_revision),
        "evidence": revisioned_artifact_path("report_governance_evidence_registry", date, "json", args.evidence_revision),
    }
    payloads = {
        key: json.loads((root / value).read_text(encoding="utf-8"))
        for key, value in paths.items()
    }
    result = validate_evidence_integrity(
        root,
        payloads["catalog"],
        payloads["evidence"],
        payloads["dependency"],
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
