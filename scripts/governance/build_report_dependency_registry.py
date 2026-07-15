#!/usr/bin/env python3
"""Build a deterministic report dependency registry without changing reports."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        dependency_payload,
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        render_dependency_markdown,
        scan_dependencies,
        stable_report_id,
        write_csv,
        write_json,
    )
except ModuleNotFoundError:  # Direct script execution.
    from report_governance_common import (  # type: ignore
        dependency_payload,
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        render_dependency_markdown,
        scan_dependencies,
        stable_report_id,
        write_csv,
        write_json,
    )


FIELDS = [
    "reference_id",
    "source_file",
    "source_line_start",
    "source_line_end",
    "normalized_target",
    "reference_type",
    "direction",
    "parser_type",
    "confidence",
    "source_excerpt_hash",
    "generator_version",
    "source_tree_commit",
    "scope_id",
    "scope_type",
    "scope_qualified_name",
    "binding_id",
    "binding_name",
    "binding_version",
    "binding_scope_id",
    "binding_origin_scope_id",
    "binding_confidence",
    "dynamic_path_pattern",
    "dynamic_pattern_kind",
    "producer_entrypoint",
    # Compatibility fields.
    "source_line",
    "referenced_report_path",
    "consumer_or_producer",
    "static_or_dynamic",
    "migration_impact",
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
    rows = scan_dependencies(root)
    date = args.business_date
    stem = f"report_dependency_registry_{date}"
    metadata = artifact_metadata(root, date, stable_report_id(f"reports/{stem}.json"), len(rows))
    payload = dependency_payload(rows, metadata)
    write_json(root / f"reports/{stem}.json", payload)
    write_csv(root / f"reports/{stem}.csv", rows, FIELDS)
    summary_path = f"reports/report_dependency_summary_{date}.md"
    front_matter = markdown_front_matter(
        report_id=stable_report_id(summary_path),
        report_type="DEPENDENCY_SUMMARY",
        business_date=date,
        created_at=metadata["generated_at"],
        status="REMEDIATED_PENDING_RE_QC",
        producer="scripts/governance/build_report_dependency_registry.py",
        source_run_id=f"reports-governance-phase-a-remediation-{date}",
    )
    (root / summary_path).write_text(
        render_dependency_markdown(payload, front_matter), encoding="utf-8"
    )
    print(
        "report dependency registry built: "
        f"records={payload['record_count']} dynamic={payload['summary']['dynamic_pattern_count']}"
    )


if __name__ == "__main__":
    main()
