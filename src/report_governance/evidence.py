from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext, canonical_json, sha256_bytes, stable_id


RUNTIME_ROLES = {
    "FORMAL_EXECUTION_INPUT",
    "APP_DASHBOARD_ENTRYPOINT",
    "AVAILABILITY_ACTIVE_ARTIFACT",
    "RUNTIME_STATUS",
}


def _finalize(context: RunContext, record: dict[str, Any]) -> dict[str, Any]:
    complete = {
        **record,
        "run_id": context.run_id,
        "source_tree_commit": context.source_tree_commit,
        "evidence_schema_version": context.config["evidence_schema_version"],
    }
    complete["evidence_hash"] = sha256_bytes(canonical_json(complete))
    return complete


def _classification_evidence(
    context: RunContext,
    report: dict[str, Any],
    evidence_type: str,
    result: Any,
) -> dict[str, Any]:
    evidence_id = stable_id("evidence", report["report_id"], evidence_type, canonical_json(result))
    return _finalize(
        context,
        {
            "evidence_id": evidence_id,
            "report_id": report["report_id"],
            "report_path": report["relative_path"],
            "evidence_type": evidence_type,
            "result": result,
            "source_path": report["relative_path"],
            "source_line": None,
            "source_excerpt_sha256": report["content_sha256"],
            "scanner_version": context.config["catalog_version"],
            "scanned_source_roots": context.config["report_roots"],
            "excluded_roots": context.config["governance_control_roots"],
            "search_keys": [report["relative_path"]],
            "result_count": 1,
        },
    )


def _structured_evidence(context: RunContext, reference: dict[str, Any]) -> dict[str, Any]:
    if reference["direction"] == "PRODUCER":
        evidence_type = "STRUCTURED_PRODUCER"
    elif reference["direction"] in {"CONSUMER", "MOVE_SOURCE"}:
        evidence_type = "STRUCTURED_CONSUMER"
    else:
        evidence_type = "STRUCTURED_REFERENCE"
    evidence_id = stable_id("evidence", "STRUCTURED", reference["reference_id"])
    return _finalize(
        context,
        {
            "evidence_id": evidence_id,
            "report_id": reference["report_id"],
            "report_path": reference["report_path"],
            "evidence_type": evidence_type,
            "result": {
                "reference_id": reference["reference_id"],
                "reference_kind": reference["reference_kind"],
                "reference_class": reference["reference_class"],
                "direction": reference["direction"],
                "access_mode": reference["access_mode"],
                "dynamic_pattern": reference["dynamic_pattern"],
                "confidence": reference["confidence"],
                "operation": reference["operation"],
            },
            "source_path": reference["source_path"],
            "source_line": reference["line"],
            "source_excerpt_sha256": reference["excerpt_sha256"],
            "scanner_version": reference["scanner_version"],
            "scanned_source_roots": context.config["active_source_roots"],
            "excluded_roots": context.config["excluded_source_roots"],
            "search_keys": [reference["search_value"]],
            "result_count": 1,
        },
    )


def _backstop_evidence(context: RunContext, scan: dict[str, Any]) -> dict[str, Any]:
    evidence_type = "BACKSTOP_ZERO_RESULT" if scan["result_status"] == "ZERO_RESULT_PROOF" else "BACKSTOP_REFERENCE"
    evidence_id = stable_id("evidence", "BACKSTOP", scan["scan_id"])
    return _finalize(
        context,
        {
            "evidence_id": evidence_id,
            "report_id": scan["report_id"],
            "report_path": scan["report_path"],
            "evidence_type": evidence_type,
            "result": {
                "scan_id": scan["scan_id"],
                "query_type": scan["query_type"],
                "result_status": scan["result_status"],
                "result_count": scan["result_count"],
                "matches": scan["matches"],
            },
            "source_path": None,
            "source_line": None,
            "source_excerpt_sha256": None,
            "scanner_version": scan["scanner_version"],
            "scanned_source_roots": context.config["active_source_roots"],
            "excluded_roots": context.config["excluded_source_roots"],
            "search_keys": [scan["query_type"], scan["query"]],
            "result_count": scan["result_count"],
        },
    )


def build_evidence_index(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for report in inventory:
        evidence.extend(
            [
                _classification_evidence(context, report, "INVENTORY_CONTENT_HASH", {"content_sha256": report["content_sha256"]}),
                _classification_evidence(context, report, "ROLE", {"role": report["role"]}),
                _classification_evidence(context, report, "RETENTION", {"retention_status": report["retention_status"]}),
                _classification_evidence(context, report, "NAMING", {"naming_status": report["naming_status"]}),
                _classification_evidence(context, report, "LOCATION", {"location_status": report["location_status"]}),
                _classification_evidence(
                    context,
                    report,
                    "ALIAS",
                    {"is_alias": report["role"] == "CURRENT_ALIAS" or report["naming_status"] == "CURRENT_ALIAS"},
                ),
                _classification_evidence(context, report, "RUNTIME_LOCK", {"locked": report["role"] in RUNTIME_ROLES}),
            ]
        )
    evidence.extend(_structured_evidence(context, item) for item in structured)
    evidence.extend(_backstop_evidence(context, item) for item in backstop)
    _assert_unique(evidence)
    return sorted(evidence, key=lambda item: item["evidence_id"])


def evidence_lookup_maps(
    evidence: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    structured: dict[str, str] = {}
    backstop: dict[str, str] = {}
    for item in evidence:
        result = item["result"]
        if isinstance(result, dict) and result.get("reference_id"):
            structured[result["reference_id"]] = item["evidence_id"]
        if isinstance(result, dict) and result.get("scan_id"):
            backstop[result["scan_id"]] = item["evidence_id"]
    return structured, backstop


def add_disagreement_evidence(
    context: RunContext,
    evidence: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    additions: list[dict[str, Any]] = []
    for disagreement in disagreements:
        evidence_id = stable_id("evidence", "SCANNER_DISAGREEMENT", disagreement["disagreement_id"])
        disagreement["reviewer_evidence_ids"] = [evidence_id]
        additions.append(
            _finalize(
                context,
                {
                    "evidence_id": evidence_id,
                    "report_id": disagreement["report_id"],
                    "report_path": disagreement["report_path"],
                    "evidence_type": "SCANNER_DISAGREEMENT",
                    "result": disagreement,
                    "source_path": None,
                    "source_line": None,
                    "source_excerpt_sha256": None,
                    "scanner_version": "scanner-disagreement-model-v1",
                    "scanned_source_roots": context.config["active_source_roots"],
                    "excluded_roots": context.config["excluded_source_roots"],
                    "search_keys": [disagreement["disagreement_id"]],
                    "result_count": 1,
                },
            )
        )
    combined = [*evidence, *additions]
    _assert_unique(combined)
    return sorted(combined, key=lambda item: item["evidence_id"])


def add_manual_review_evidence(
    context: RunContext,
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions = {item["report_id"]: item for item in readiness}
    additions: list[dict[str, Any]] = []
    for review in reviews:
        seed_hash = review["review_evidence_hash"]
        evidence_id = stable_id("evidence", "MANUAL_REVIEW", review["report_id"], seed_hash)
        review["manual_review_evidence_id"] = evidence_id
        review_without_hash = {key: value for key, value in review.items() if key != "review_evidence_hash"}
        review["review_evidence_hash"] = sha256_bytes(canonical_json(review_without_hash))
        decisions[review["report_id"]]["decision_evidence_ids"].append(evidence_id)
        decisions[review["report_id"]]["manual_review_evidence_id"] = evidence_id
        decisions[review["report_id"]]["review_evidence_hash"] = review["review_evidence_hash"]
        additions.append(
            _finalize(
                context,
                {
                    "evidence_id": evidence_id,
                    "report_id": review["report_id"],
                    "report_path": review["report_path"],
                    "evidence_type": "MANUAL_REVIEW",
                    "result": review,
                    "source_path": None,
                    "source_line": None,
                    "source_excerpt_sha256": None,
                    "scanner_version": context.config["review_schema_version"],
                    "scanned_source_roots": context.config["active_source_roots"],
                    "excluded_roots": context.config["excluded_source_roots"],
                    "search_keys": [review["report_path"]],
                    "result_count": 1,
                },
            )
        )
    for decision in readiness:
        decision["decision_evidence_ids"] = sorted(set(decision["decision_evidence_ids"]))
    combined = [*evidence, *additions]
    _assert_unique(combined)
    return sorted(combined, key=lambda item: item["evidence_id"])


def evidence_ids_by_report(evidence: list[dict[str, Any]]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = defaultdict(list)
    for item in evidence:
        output[item["report_id"]].append(item["evidence_id"])
    return {key: sorted(value) for key, value in output.items()}


def _assert_unique(evidence: list[dict[str, Any]]) -> None:
    unique = {item["evidence_id"] for item in evidence}
    if len(unique) != len(evidence):
        raise ValueError("duplicate governance evidence id")
