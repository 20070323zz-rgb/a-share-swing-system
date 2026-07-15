from __future__ import annotations

from typing import Any

from .common import RunContext
from .evidence import evidence_ids_by_report


RUNTIME_ROLES = {
    "FORMAL_EXECUTION_INPUT",
    "APP_DASHBOARD_ENTRYPOINT",
    "AVAILABILITY_ACTIVE_ARTIFACT",
    "RUNTIME_STATUS",
}


def load_reviews(root, path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    import json

    review_path = root / path
    if not review_path.exists():
        return {}
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    return {item["report_path"]: item for item in payload.get("reviews", [])}


def build_migration_readiness(
    context: RunContext,
    inventory: list[dict[str, Any]],
    reference_index: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    review_path: str | None = "configs/report_governance_phase_ar_reviews.json",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    references = {item["report_id"]: item for item in reference_index}
    evidence_map = evidence_ids_by_report(evidence)
    reviews = load_reviews(context.root, review_path)
    output: list[dict[str, Any]] = []
    review_matrix: list[dict[str, Any]] = []
    allowed_retention = set(context.config["retention_migration_allowed"])
    for report in inventory:
        ref = references[report["report_id"]]
        review = reviews.get(report["relative_path"], {})
        manual_review_passed = review.get("reviewer_verdict") == "PASS"
        gates = {
            "no_structured_producer": ref["structured_producer_count"] == 0,
            "no_structured_consumer": ref["structured_consumer_count"] == 0,
            "no_backstop_reference": ref["backstop_reference_count"] == 0,
            "no_runtime_lock": report["role"] not in RUNTIME_ROLES,
            "no_alias": report["role"] != "CURRENT_ALIAS" and report["naming_status"] != "CURRENT_ALIAS",
            "role_known": report["role"] != "UNKNOWN",
            "retention_allowed": report["retention_status"] in allowed_retention,
            "not_archived": report["location_status"] != "ALREADY_ARCHIVED",
            "not_control_artifact": report["location_status"] != "GOVERNANCE_CONTROL",
            "no_scanner_disagreement": not ref["reference_disagreement"],
            "manual_review_passed": manual_review_passed,
        }
        machine_gate_names = [key for key in gates if key != "manual_review_passed"]
        machine_provisional = all(gates[key] for key in machine_gate_names)
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
        elif not manual_review_passed:
            status = "MANUAL_REVIEW_REQUIRED"
        elif report["naming_status"] == "COMPLIANT_DATED":
            status = "PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN"
        else:
            status = "PROVISIONALLY_SAFE_RENAME_REQUIRED"
        output.append(
            {
                "report_id": report["report_id"],
                "relative_path": report["relative_path"],
                "migration_readiness": status,
                "deletion_readiness": "DELETION_REVIEW_REQUIRED" if machine_provisional else "DELETION_BLOCKED",
                "machine_provisional_before_review": machine_provisional,
                "candidate_evidence_matrix": gates,
                "decision_evidence_ids": evidence_map[report["report_id"]],
                "reviewer": review.get("reviewer"),
                "reviewed_at": review.get("reviewed_at"),
                "review_evidence": review.get("review_evidence"),
                "classification_version": context.config["classification_version"],
            }
        )
        if machine_provisional:
            review_matrix.append(
                {
                    "report_path": report["relative_path"],
                    "structured_scanner_result": ref["structured_reference_count"],
                    "backstop_scanner_result": ref["backstop_reference_count"],
                    "exact_source_search": review.get("exact_source_search", "PENDING"),
                    "basename_search": review.get("basename_search", "PENDING"),
                    "dynamic_prefix_search": review.get("dynamic_prefix_search", "PENDING"),
                    "config_search": review.get("config_search", "PENDING"),
                    "producer_check": review.get("producer_check", "PENDING"),
                    "consumer_check": review.get("consumer_check", "PENDING"),
                    "reviewer_verdict": review.get("reviewer_verdict", "PENDING"),
                    "review_evidence": review.get("review_evidence", []),
                }
            )
    return output, review_matrix
