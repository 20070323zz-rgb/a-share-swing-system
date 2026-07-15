from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext


def build_reference_index(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    structured_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backstop_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in structured:
        structured_by_report[record["report_id"]].append(record)
    for record in backstop:
        backstop_by_report[record["report_id"]].append(record)
    output: list[dict[str, Any]] = []
    for report in inventory:
        structured_records = sorted(structured_by_report[report["report_id"]], key=lambda item: item["reference_id"])
        backstop_records = sorted(backstop_by_report[report["report_id"]], key=lambda item: item["reference_id"])
        structured_count = len(structured_records)
        backstop_count = len(backstop_records)
        disagreement = (structured_count == 0) != (backstop_count == 0)
        output.append(
            {
                "report_id": report["report_id"],
                "relative_path": report["relative_path"],
                "structured_reference_count": structured_count,
                "backstop_reference_count": backstop_count,
                "structured_reference_ids": [item["reference_id"] for item in structured_records],
                "backstop_reference_ids": [item["reference_id"] for item in backstop_records],
                "structured_producer_count": sum(item["direction"] == "PRODUCER" for item in structured_records),
                "structured_consumer_count": sum(item["direction"] == "CONSUMER" for item in structured_records),
                "structured_declaration_count": sum(item["direction"] == "DECLARATION" for item in structured_records),
                "reference_disagreement": disagreement,
                "manual_review_required": disagreement,
                "structured_scanner_version": context.config["structured_scanner_version"],
                "backstop_scanner_version": context.config["backstop_scanner_version"],
            }
        )
    return output
