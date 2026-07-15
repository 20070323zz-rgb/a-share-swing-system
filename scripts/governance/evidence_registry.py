"""Materialize and validate traceable Reports Governance evidence records."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

try:
    from scripts.governance.report_governance_common import (
        CLASSIFICATION_SCHEMA_VERSION,
        EVIDENCE_REGISTRY_VERSION,
        RULE_DEFINITIONS,
        governance_evidence_id,
    )
except ModuleNotFoundError:  # Direct script execution.
    from report_governance_common import (  # type: ignore
        CLASSIFICATION_SCHEMA_VERSION,
        EVIDENCE_REGISTRY_VERSION,
        RULE_DEFINITIONS,
        governance_evidence_id,
    )


EVIDENCE_FIELDS = [
    "evidence_id",
    "evidence_namespace",
    "evidence_type",
    "reason",
    "report_id",
    "report_path",
    "source_registry",
    "source_record_id",
    "source_file",
    "source_line_start",
    "source_line_end",
    "source_excerpt_hash",
    "rule_id",
    "rule_version",
    "evaluated_field",
    "evaluated_value",
    "confidence",
    "generated_from",
    "source_tree_commit",
    "schema_version",
]


def normalized_excerpt_hash(text: str) -> str:
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@lru_cache(maxsize=None)
def _rule_source(root: Path, reason: str) -> tuple[str, int, int, str]:
    source_file = "scripts/governance/report_governance_common.py"
    lines = (root / source_file).read_text(encoding="utf-8").splitlines()
    marker = f'"{reason}": {{'
    matches = [index for index, line in enumerate(lines, start=1) if marker in line]
    if len(matches) != 1:
        raise ValueError(f"rule definition marker must be unique for {reason}: {matches}")
    line_number = matches[0]
    return source_file, line_number, line_number, normalized_excerpt_hash(lines[line_number - 1])


def build_evidence_records(
    root: Path,
    catalog: dict,
    dependency_registry: dict,
    *,
    catalog_path: str,
    dependency_registry_path: str,
) -> list[dict]:
    dependencies = {row["reference_id"]: row for row in dependency_registry["records"]}
    dependencies_by_target: dict[str, list[dict]] = defaultdict(list)
    for dependency in dependencies.values():
        dependencies_by_target[dependency["normalized_target"]].append(dependency)
    source_commit = catalog["metadata"]["source_tree_commit"]
    records: list[dict] = []

    for report in catalog["records"]:
        report_id = report["report_id"]
        candidate_dependencies = list(dependencies_by_target[report["current_path"]])
        candidate_dependencies.extend(
            dependencies[reference_id]
            for reference_id in report.get("matched_dynamic_producer_ids", [])
            if reference_id in dependencies
        )
        candidate_dependencies = list(
            {row["reference_id"]: row for row in candidate_dependencies}.values()
        )
        for reason, evidence_ids in sorted(report["archive_block_evidence"].items()):
            definition = RULE_DEFINITIONS[reason]
            for evidence_id in evidence_ids:
                dependency = next(
                    (
                        row
                        for row in candidate_dependencies
                        if governance_evidence_id(report_id, reason, row["reference_id"])
                        == evidence_id
                    ),
                    None,
                )
                if dependency is not None:
                    namespace = "DEPENDENCY"
                    evidence_type = definition["evidence_type"]
                    source_registry = dependency_registry_path
                    source_record_id = dependency["reference_id"]
                    source_file = dependency["source_file"]
                    line_start = dependency["source_line_start"]
                    line_end = dependency["source_line_end"]
                    excerpt_hash = dependency["source_excerpt_hash"]
                    confidence = dependency["confidence"]
                    dependency_value = {
                        "direction": dependency["direction"],
                        "normalized_target": dependency["normalized_target"],
                        "reference_type": dependency["reference_type"],
                    }
                    evaluated_value = json.dumps(
                        dependency_value,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    record_source_commit = dependency["source_tree_commit"]
                else:
                    namespace = definition["namespace"]
                    evidence_type = definition["evidence_type"]
                    source_registry = catalog_path
                    source_record_id = report_id
                    source_file, line_start, line_end, excerpt_hash = _rule_source(root, reason)
                    confidence = report["confidence"]
                    value = report.get(definition["evaluated_field"], "")
                    evaluated_value = (
                        value
                        if isinstance(value, str)
                        else json.dumps(value, ensure_ascii=False, sort_keys=True)
                    )
                    record_source_commit = source_commit

                records.append(
                    {
                        "evidence_id": evidence_id,
                        "evidence_namespace": namespace,
                        "evidence_type": evidence_type,
                        "reason": reason,
                        "report_id": report_id,
                        "report_path": report["current_path"],
                        "source_registry": source_registry,
                        "source_record_id": source_record_id,
                        "source_file": source_file,
                        "source_line_start": line_start,
                        "source_line_end": line_end,
                        "source_excerpt_hash": excerpt_hash,
                        "rule_id": definition["rule_id"],
                        "rule_version": definition["rule_version"],
                        "evaluated_field": definition["evaluated_field"],
                        "evaluated_value": evaluated_value,
                        "confidence": confidence,
                        "generated_from": "scripts/governance/build_report_governance_evidence_registry.py",
                        "source_tree_commit": record_source_commit,
                        "schema_version": 1,
                    }
                )
    return sorted(records, key=lambda row: row["evidence_id"])


def evidence_payload(records: list[dict], metadata: dict) -> dict:
    fingerprint = hashlib.sha256(
        json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return {
        "schema_version": 1,
        "registry_id": "a_share_swing_system_report_governance_evidence_registry_v1",
        "evidence_registry_version": EVIDENCE_REGISTRY_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "repository_root": "<project_root>",
        "metadata": metadata,
        "record_count": len(records),
        "registry_sha256": fingerprint,
        "summary": {
            "by_namespace": dict(
                sorted(Counter(row["evidence_namespace"] for row in records).items())
            ),
            "by_reason": dict(sorted(Counter(row["reason"] for row in records).items())),
        },
        "records": records,
    }


def validate_evidence_integrity(
    root: Path,
    catalog: dict,
    evidence_registry: dict,
    dependency_registry: dict,
) -> dict:
    errors: list[str] = []
    evidence_records = evidence_registry.get("records", [])
    ids = [row.get("evidence_id", "") for row in evidence_records]
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.extend(f"duplicate evidence_id: {item}" for item in duplicate_ids)
    evidence_by_id = {row.get("evidence_id", ""): row for row in evidence_records}
    catalog_reports = {row["report_id"]: row for row in catalog.get("records", [])}
    dependency_ids = {
        row["reference_id"] for row in dependency_registry.get("records", [])
    }
    referenced_ids: set[str] = set()

    for report in catalog_reports.values():
        reason_ids = report.get("archive_block_evidence", {})
        flattened = sorted({item for values in reason_ids.values() for item in values})
        if flattened != sorted(report.get("archive_block_evidence_ids", [])):
            errors.append(f"flattened evidence mismatch: {report['report_id']}")
        for reason in report.get("archive_block_reasons", []):
            if not reason_ids.get(reason):
                errors.append(f"reason without evidence: {report['report_id']}:{reason}")
        if report["migration_eligibility"] not in {
            "SAFE_TO_MIGRATE",
            "SAFE_TO_MIGRATE_RENAME_REQUIRED",
        } and not flattened:
            errors.append(f"migration decision without evidence: {report['report_id']}")
        if report["deletion_eligibility"] != "SAFE_TO_DELETE_AFTER_AUTHORIZATION" and not flattened:
            errors.append(f"deletion decision without evidence: {report['report_id']}")
        for evidence_id in flattened:
            referenced_ids.add(evidence_id)
            if evidence_id not in evidence_by_id:
                errors.append(f"unresolved evidence_id: {evidence_id}")

    orphan_ids = sorted(set(evidence_by_id) - referenced_ids)
    errors.extend(f"orphan evidence_id: {item}" for item in orphan_ids)

    for row in evidence_records:
        evidence_id = row.get("evidence_id", "")
        if row.get("report_id") not in catalog_reports:
            errors.append(f"missing report_id: {evidence_id}:{row.get('report_id', '')}")
        if not row.get("rule_version"):
            errors.append(f"missing rule_version: {evidence_id}")
        source_file = root / row.get("source_file", "")
        try:
            lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
            start = int(row["source_line_start"])
            end = int(row["source_line_end"])
            excerpt = "\n".join(lines[start - 1 : end])
            if normalized_excerpt_hash(excerpt) != row.get("source_excerpt_hash"):
                errors.append(f"source hash mismatch: {evidence_id}")
        except (OSError, ValueError, KeyError):
            errors.append(f"invalid evidence source: {evidence_id}")
        if row.get("evidence_namespace") == "DEPENDENCY":
            if row.get("source_record_id") not in dependency_ids:
                errors.append(f"missing dependency source_record_id: {evidence_id}")

    return {
        "valid": not errors,
        "errors": errors,
        "unresolved_evidence_ids": sum(
            error.startswith("unresolved evidence_id:") for error in errors
        ),
        "duplicate_evidence_ids": len(duplicate_ids),
        "missing_report_ids": sum(error.startswith("missing report_id:") for error in errors),
        "missing_rule_versions": sum(
            error.startswith("missing rule_version:") for error in errors
        ),
        "orphan_evidence_ids": len(orphan_ids),
        "record_count": len(evidence_records),
        "referenced_evidence_count": len(referenced_ids),
    }
