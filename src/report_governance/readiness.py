from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext, canonical_json, sha256_bytes
from .evidence import evidence_ids_by_report


RUNTIME_ROLES = {
    "FORMAL_EXECUTION_INPUT",
    "APP_DASHBOARD_ENTRYPOINT",
    "AVAILABILITY_ACTIVE_ARTIFACT",
    "RUNTIME_STATUS",
}
QUERY_FIELD_MAP = {
    "EXACT_RELATIVE_PATH": "exact_path_query",
    "EXACT_BASENAME": "basename_query",
    "EXACT_STEM": "stem_query",
    "DYNAMIC_PREFIX_EXTENSION": "dynamic_prefix_query",
    "CONFIG_KEY_VALUE": "config_query",
    "SHELL_TOKEN": "shell_token_query",
}


def _evidence_maps(evidence: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    structured: dict[str, str] = {}
    backstop: dict[str, str] = {}
    zero_by_report: dict[str, list[str]] = defaultdict(list)
    for item in evidence:
        result = item["result"]
        if not isinstance(result, dict):
            continue
        if result.get("reference_id"):
            structured[result["reference_id"]] = item["evidence_id"]
        if result.get("scan_id"):
            backstop[result["scan_id"]] = item["evidence_id"]
        if item["evidence_type"] == "BACKSTOP_ZERO_RESULT":
            zero_by_report[item["report_id"]].append(item["evidence_id"])
    return structured, backstop, zero_by_report


def _query_review(scan: dict[str, Any], evidence_id: str) -> dict[str, Any]:
    return {
        "query": scan["query"],
        "result_status": scan["result_status"],
        "result_count": scan["result_count"],
        "evidence_ids": [evidence_id],
    }


def build_migration_readiness(
    context: RunContext,
    inventory: list[dict[str, Any]],
    reference_index: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    references = {item["report_id"]: item for item in reference_index}
    evidence_map = evidence_ids_by_report(evidence)
    structured_evidence, backstop_evidence, zero_by_report = _evidence_maps(evidence)
    structured_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backstop_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in structured:
        structured_by_report[item["report_id"]].append(item)
    for item in backstop:
        backstop_by_report[item["report_id"]].append(item)

    output: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    allowed_retention = set(context.config["retention_migration_allowed"])
    for report in inventory:
        ref = references[report["report_id"]]
        gates = {
            "no_structured_producer": ref["structured_producer_count"] == 0,
            "no_structured_consumer": ref["structured_consumer_count"] == 0,
            "no_backstop_reference": ref["backstop_active_query_count"] == 0,
            "no_runtime_lock": report["role"] not in RUNTIME_ROLES,
            "no_alias": report["role"] != "CURRENT_ALIAS" and report["naming_status"] != "CURRENT_ALIAS",
            "role_known": report["role"] != "UNKNOWN",
            "retention_allowed": report["retention_status"] in allowed_retention,
            "not_archived": report["location_status"] != "ALREADY_ARCHIVED",
            "not_control_artifact": report["location_status"] != "GOVERNANCE_CONTROL",
            "no_scanner_disagreement": not ref["reference_disagreement"],
        }
        machine_provisional = all(gates.values())
        review: dict[str, Any] | None = None
        if machine_provisional:
            scans = {item["query_type"]: item for item in backstop_by_report[report["report_id"]]}
            review = {
                "report_id": report["report_id"],
                "report_path": report["relative_path"],
                "reviewer": "Codex Phase A-R bounded remediation",
                "reviewed_at": context.generated_at,
                "source_tree_commit": context.source_tree_commit,
                "structured_evidence_ids": sorted(
                    structured_evidence[item["reference_id"]] for item in structured_by_report[report["report_id"]]
                ),
                "backstop_evidence_ids": sorted(
                    backstop_evidence[item["scan_id"]] for item in backstop_by_report[report["report_id"]]
                ),
                "zero_result_evidence_ids": sorted(zero_by_report[report["report_id"]]),
                "producer_verdict": "NO_ACTIVE_PRODUCER",
                "consumer_verdict": "NO_ACTIVE_CONSUMER",
                "alias_verdict": "NO_ACTIVE_ALIAS",
                "runtime_verdict": "NO_RUNTIME_LOCK",
                "retention_verdict": "HISTORICAL_SNAPSHOT_ELIGIBLE",
                "naming_verdict": (
                    "RENAME_REQUIRED"
                    if report["naming_status"] == "NEEDS_DATE_NORMALIZATION"
                    else report["naming_status"]
                ),
                "final_reviewer_verdict": "PASS",
                "review_schema_version": context.config["review_schema_version"],
            }
            for query_type, field in QUERY_FIELD_MAP.items():
                review[field] = _query_review(scans[query_type], backstop_evidence[scans[query_type]["scan_id"]])
            review["string_concat_query"] = _query_review(
                scans["STRING_CONCAT"], backstop_evidence[scans["STRING_CONCAT"]["scan_id"]]
            )
            review["path_construct_query"] = _query_review(
                scans["PATH_CONSTRUCT"], backstop_evidence[scans["PATH_CONSTRUCT"]["scan_id"]]
            )
            if not review["zero_result_evidence_ids"]:
                raise ValueError(f"candidate lacks BACKSTOP_ZERO_RESULT evidence: {report['relative_path']}")
            review["review_evidence_hash"] = sha256_bytes(canonical_json(review))
            reviews.append(review)

        if report["location_status"] == "ALREADY_ARCHIVED":
            status = "NOT_APPLICABLE_ALREADY_ARCHIVED"
        elif not gates["no_runtime_lock"]:
            status = "BLOCKED_RUNTIME"
        elif not gates["no_alias"]:
            status = "BLOCKED_ALIAS"
        elif not gates["no_structured_producer"]:
            status = "BLOCKED_ACTIVE_PRODUCER"
        elif not gates["no_structured_consumer"]:
            status = "BLOCKED_ACTIVE_CONSUMER"
        elif not gates["no_backstop_reference"]:
            status = "BLOCKED_BACKSTOP_REFERENCE"
        elif not gates["role_known"]:
            status = "BLOCKED_UNKNOWN"
        elif not gates["retention_allowed"]:
            status = "BLOCKED_RETENTION"
        elif not gates["no_scanner_disagreement"]:
            status = "MANUAL_REVIEW_REQUIRED"
        elif review is None or review["final_reviewer_verdict"] != "PASS":
            status = "MANUAL_REVIEW_REQUIRED"
        elif report["naming_status"] == "NEEDS_DATE_NORMALIZATION":
            status = "PROVISIONALLY_SAFE_RENAME_REQUIRED"
        else:
            status = "PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN"

        output.append(
            {
                "report_id": report["report_id"],
                "relative_path": report["relative_path"],
                "migration_readiness": status,
                "deletion_readiness": "DELETION_REVIEW_REQUIRED" if machine_provisional else "DELETION_BLOCKED",
                "machine_provisional_before_review": machine_provisional,
                "candidate_evidence_matrix": gates,
                "decision_evidence_ids": list(evidence_map[report["report_id"]]),
                "reviewer": review["reviewer"] if review else None,
                "reviewed_at": review["reviewed_at"] if review else None,
                "review_evidence_hash": review["review_evidence_hash"] if review else None,
                "manual_review_evidence_id": None,
                "classification_version": context.config["classification_version"],
            }
        )
    return output, sorted(reviews, key=lambda item: item["report_path"])
