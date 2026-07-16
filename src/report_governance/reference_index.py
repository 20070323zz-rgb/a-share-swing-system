from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext


DOCUMENTATION_CLASSES = {
    "DOCUMENTATION_REFERENCE",
    "DOCUMENTATION_EXAMPLE",
    "CODE_BLOCK_REFERENCE",
}


def build_reference_index(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    disagreements: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    structured_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backstop_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    disagreements_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in structured:
        structured_by_report[record["report_id"]].append(record)
    for record in backstop:
        backstop_by_report[record["report_id"]].append(record)
    for record in disagreements or []:
        disagreements_by_report[record["report_id"]].append(record)

    output: list[dict[str, Any]] = []
    for report in inventory:
        structured_records = sorted(structured_by_report[report["report_id"]], key=lambda item: item["reference_id"])
        backstop_records = sorted(backstop_by_report[report["report_id"]], key=lambda item: item["scan_id"])
        report_disagreements = sorted(
            disagreements_by_report[report["report_id"]], key=lambda item: item["disagreement_id"]
        )
        structured_runtime = [item for item in structured_records if item["reference_class"] not in DOCUMENTATION_CLASSES]
        backstop_positive = [item for item in backstop_records if item["result_status"] != "ZERO_RESULT_PROOF"]
        backstop_active = [
            item
            for item in backstop_positive
            if any(match["source_class"] == "ACTIVE_SOURCE" for match in item["matches"])
        ]
        unresolved = [item for item in report_disagreements if item["resolution_status"] != "RESOLVED"]
        output.append(
            {
                "report_id": report["report_id"],
                "relative_path": report["relative_path"],
                "structured_reference_count": len(structured_records),
                "structured_runtime_reference_count": len(structured_runtime),
                "structured_documentation_reference_count": len(structured_records) - len(structured_runtime),
                "structured_reference_ids": [item["reference_id"] for item in structured_records],
                "structured_producer_count": sum(item["direction"] == "PRODUCER" for item in structured_runtime),
                "structured_consumer_count": sum(item["direction"] in {"CONSUMER", "MOVE_SOURCE"} for item in structured_runtime),
                "structured_move_source_count": sum(item["direction"] == "MOVE_SOURCE" for item in structured_runtime),
                "structured_declaration_count": sum(item["direction"] == "DECLARATION" for item in structured_runtime),
                "backstop_scan_count": len(backstop_records),
                "backstop_found_query_count": sum(item["result_status"] == "FOUND_REFERENCE" for item in backstop_records),
                "backstop_ambiguous_query_count": sum(item["result_status"] == "AMBIGUOUS_REFERENCE" for item in backstop_records),
                "backstop_zero_result_count": sum(item["result_status"] == "ZERO_RESULT_PROOF" for item in backstop_records),
                "backstop_match_count": sum(item["result_count"] for item in backstop_positive),
                "backstop_active_query_count": len(backstop_active),
                "backstop_scan_ids": [item["scan_id"] for item in backstop_records],
                "reference_disagreement": bool(unresolved),
                "disagreement_ids": [item["disagreement_id"] for item in report_disagreements],
                "unresolved_disagreement_ids": [item["disagreement_id"] for item in unresolved],
                "manual_review_required": bool(unresolved),
                "structured_scanner_version": context.config["structured_scanner_version"],
                "backstop_scanner_version": context.config["backstop_scanner_version"],
            }
        )
    return output
