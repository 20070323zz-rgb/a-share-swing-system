#!/usr/bin/env python3
"""Build a deterministic report dependency registry without changing reports."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        dependency_payload,
        project_root_from_script,
        render_dependency_markdown,
        scan_dependencies,
        write_csv,
        write_json,
    )
except ModuleNotFoundError:  # Direct script execution.
    from report_governance_common import (  # type: ignore
        dependency_payload,
        project_root_from_script,
        render_dependency_markdown,
        scan_dependencies,
        write_csv,
        write_json,
    )


FIELDS = [
    "source_file",
    "source_line",
    "referenced_report_path",
    "reference_type",
    "consumer_or_producer",
    "static_or_dynamic",
    "confidence",
    "migration_impact",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=project_root_from_script(__file__))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    rows = scan_dependencies(root)
    payload = dependency_payload(rows)
    write_json(root / "reports/report_dependency_registry.json", payload)
    write_csv(root / "reports/report_dependency_registry.csv", rows, FIELDS)
    (root / "reports/report_dependency_registry.md").write_text(
        render_dependency_markdown(payload), encoding="utf-8"
    )
    print(
        "report dependency registry built: "
        f"records={payload['record_count']} dynamic={payload['summary']['dynamic_pattern_count']}"
    )


if __name__ == "__main__":
    main()
