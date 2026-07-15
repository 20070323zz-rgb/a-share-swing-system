from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext, canonical_json, sha256_bytes, stable_id


def _inventory_evidence(context: RunContext, report: dict[str, Any]) -> dict[str, Any]:
    evaluated = {
        key: report[key]
        for key in ("business_date", "role", "naming_status", "retention_status", "location_status")
    }
    evidence_id = stable_id("evidence", report["report_id"], "INVENTORY_CLASSIFICATION", canonical_json(evaluated))
    return {
        "evidence_id": evidence_id,
        "report_id": report["report_id"],
        "report_path": report["relative_path"],
        "evidence_type": "INVENTORY_CLASSIFICATION",
        "result": evaluated,
        "source_path": report["relative_path"],
        "source_line": None,
        "source_excerpt_sha256": report["content_sha256"],
        "scanner_version": context.config["catalog_version"],
        "scanned_source_roots": context.config["report_roots"],
        "excluded_roots": context.config["governance_control_roots"],
        "search_keys": [report["relative_path"]],
        "run_id": context.run_id,
        "source_tree_commit": context.source_tree_commit,
        "result_count": 1,
    }


def _reference_evidence(context: RunContext, reference: dict[str, Any]) -> dict[str, Any]:
    evidence_id = stable_id("evidence", reference["scanner"], reference["reference_id"])
    return {
        "evidence_id": evidence_id,
        "report_id": reference["report_id"],
        "report_path": reference["report_path"],
        "evidence_type": f"{reference['scanner']}_REFERENCE",
        "result": {
            "reference_id": reference["reference_id"],
            "reference_kind": reference["reference_kind"],
            "direction": reference["direction"],
        },
        "source_path": reference["source_path"],
        "source_line": reference["line"],
        "source_excerpt_sha256": reference["excerpt_sha256"],
        "scanner_version": reference["scanner_version"],
        "scanned_source_roots": context.config["active_source_roots"],
        "excluded_roots": context.config["excluded_source_roots"],
        "search_keys": [reference.get("search_key") or reference.get("search_value") or reference["report_path"]],
        "run_id": context.run_id,
        "source_tree_commit": context.source_tree_commit,
        "result_count": 1,
    }


def _absence_evidence(context: RunContext, report: dict[str, Any], scanner: str) -> dict[str, Any]:
    if scanner == "STRUCTURED":
        version = context.config["structured_scanner_version"]
        keys = [report["relative_path"], report["filename"], "AST/path-flow/dynamic-template"]
    else:
        version = context.config["backstop_scanner_version"]
        keys = [report["relative_path"], report["filename"], "basename/prefix/config/shell"]
    proof = {
        "scanner_version": version,
        "scanned_source_roots": context.config["active_source_roots"],
        "excluded_roots": context.config["excluded_source_roots"],
        "search_keys": keys,
        "run_id": context.run_id,
        "source_tree_commit": context.source_tree_commit,
        "result_count": 0,
    }
    evidence_id = stable_id("evidence", report["report_id"], scanner, canonical_json(proof))
    return {
        "evidence_id": evidence_id,
        "report_id": report["report_id"],
        "report_path": report["relative_path"],
        "evidence_type": f"NO_{scanner}_REFERENCE",
        "result": {"reference_count": 0, "evidence_hash": sha256_bytes(canonical_json(proof))},
        "source_path": None,
        "source_line": None,
        "source_excerpt_sha256": None,
        **proof,
    }


def build_evidence_index(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    structured_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backstop_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in structured:
        structured_by_report[item["report_id"]].append(item)
    for item in backstop:
        backstop_by_report[item["report_id"]].append(item)
    evidence: list[dict[str, Any]] = []
    for report in inventory:
        evidence.append(_inventory_evidence(context, report))
        structured_records = structured_by_report[report["report_id"]]
        backstop_records = backstop_by_report[report["report_id"]]
        if structured_records:
            evidence.extend(_reference_evidence(context, item) for item in structured_records)
        else:
            evidence.append(_absence_evidence(context, report, "STRUCTURED"))
        if backstop_records:
            evidence.extend(_reference_evidence(context, item) for item in backstop_records)
        else:
            evidence.append(_absence_evidence(context, report, "BACKSTOP"))
    unique = {item["evidence_id"]: item for item in evidence}
    if len(unique) != len(evidence):
        raise ValueError("duplicate governance evidence id")
    return [unique[key] for key in sorted(unique)]


def evidence_ids_by_report(evidence: list[dict[str, Any]]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = defaultdict(list)
    for item in evidence:
        output[item["report_id"]].append(item["evidence_id"])
    return {key: sorted(value) for key, value in output.items()}
