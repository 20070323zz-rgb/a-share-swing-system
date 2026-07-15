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
        dependency_payload,
        artifact_metadata,
        business_date_today,
        markdown_front_matter,
        project_root_from_script,
        render_dependency_markdown,
        revisioned_artifact_path,
        scan_dependencies,
        stable_report_id,
        superseded_revision_artifact,
        write_csv,
        write_immutable_text,
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
    "parent_scope_id",
    "syntactic_parent_scope_id",
    "lexical_resolution_parent_scope_id",
    "scope_type",
    "scope_qualified_name",
    "scope_source_start_line",
    "scope_source_end_line",
    "binding_id",
    "binding_name",
    "binding_version",
    "binding_scope_id",
    "binding_origin_scope_id",
    "binding_confidence",
    "binding_assignment_line",
    "binding_assignment_kind",
    "binding_normalized_expression",
    "binding_source_excerpt_hash",
    "dynamic_path_pattern",
    "dynamic_pattern_kind",
    "pattern_variables",
    "resolved_static_path",
    "static_prefix",
    "static_suffix",
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
    parser.add_argument("--snapshot-revision", default="v3")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.project_root.resolve()
    rows = scan_dependencies(root)
    date = args.business_date
    revision = args.snapshot_revision
    if not revision.startswith("v") or not revision[1:].isdigit():
        raise SystemExit("--snapshot-revision must look like v2")
    registry_json = revisioned_artifact_path(
        "report_dependency_registry", date, "json", revision
    )
    registry_csv = revisioned_artifact_path(
        "report_dependency_registry", date, "csv", revision
    )
    metadata = artifact_metadata(
        root,
        date,
        stable_report_id(registry_json),
        len(rows),
        superseded_revision_artifact(
            root, "report_dependency_registry", date, "json", revision
        ),
        revision,
    )
    payload = dependency_payload(rows, metadata)
    write_json(root / registry_json, payload, immutable=True)
    write_csv(root / registry_csv, rows, FIELDS, immutable=True)
    summary_path = revisioned_artifact_path(
        "report_dependency_summary", date, "md", revision
    )
    front_matter = markdown_front_matter(
        report_id=stable_report_id(summary_path),
        report_type="DEPENDENCY_SUMMARY",
        business_date=date,
        created_at=metadata["generated_at"],
        status="REMEDIATED_PENDING_RE_QC",
        producer="scripts/governance/build_report_dependency_registry.py",
        source_run_id=f"reports-governance-phase-a-remediation-{date}",
        supersedes=superseded_revision_artifact(
            root, "report_dependency_summary", date, "md", revision
        ),
        snapshot_revision=revision,
    )
    write_immutable_text(root / summary_path, render_dependency_markdown(payload, front_matter))
    print(
        "report dependency registry built: "
        f"records={payload['record_count']} dynamic={payload['summary']['dynamic_pattern_count']}"
    )


if __name__ == "__main__":
    main()
