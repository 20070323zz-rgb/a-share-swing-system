from __future__ import annotations

from collections import defaultdict
from typing import Any

from .common import RunContext, stable_id


DISAGREEMENT_TYPES = {
    "STRUCTURED_ONLY",
    "BACKSTOP_ONLY",
    "DIRECTION_DISAGREEMENT",
    "DYNAMIC_PATTERN_DISAGREEMENT",
    "REFERENCE_CLASS_DISAGREEMENT",
    "PATH_NORMALIZATION_DISAGREEMENT",
    "OTHER",
}


def build_scanner_disagreements(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    structured_evidence_ids: dict[str, str],
    backstop_evidence_ids: dict[str, str],
) -> list[dict[str, Any]]:
    structured_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backstop_by_report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in structured:
        structured_by_report[item["report_id"]].append(item)
    for item in backstop:
        backstop_by_report[item["report_id"]].append(item)

    disagreements: list[dict[str, Any]] = []
    for report in inventory:
        structured_records = structured_by_report[report["report_id"]]
        backstop_records = backstop_by_report[report["report_id"]]
        structured_runtime = [
            item
            for item in structured_records
            if item["reference_class"] not in {"DOCUMENTATION_REFERENCE", "DOCUMENTATION_EXAMPLE", "CODE_BLOCK_REFERENCE"}
        ]
        backstop_runtime = [
            item
            for item in backstop_records
            if item["result_status"] != "ZERO_RESULT_PROOF"
            and any(match["source_class"] == "ACTIVE_SOURCE" for match in item["matches"])
        ]
        kinds: list[str] = []
        backstop_strong = [item for item in backstop_runtime if item["result_status"] == "FOUND_REFERENCE"]
        backstop_ambiguous = [item for item in backstop_runtime if item["result_status"] == "AMBIGUOUS_REFERENCE"]
        if structured_runtime and not backstop_runtime:
            kinds.append("STRUCTURED_ONLY")
        elif backstop_strong and not structured_runtime:
            kinds.append("BACKSTOP_ONLY")
        elif backstop_ambiguous and not structured_runtime:
            kinds.append("REFERENCE_CLASS_DISAGREEMENT")
        structured_dynamic = any(item["dynamic_pattern"] for item in structured_runtime)
        backstop_dynamic = any(
            item["query_type"] == "DYNAMIC_PREFIX_EXTENSION" and item["result_status"] != "ZERO_RESULT_PROOF"
            for item in backstop_runtime
        )
        if structured_dynamic != backstop_dynamic and (structured_runtime or backstop_runtime):
            kinds.append("DYNAMIC_PATTERN_DISAGREEMENT")
        if backstop_ambiguous and structured_runtime and not backstop_strong:
            kinds.append("REFERENCE_CLASS_DISAGREEMENT")

        for disagreement_type in sorted(set(kinds)):
            assert disagreement_type in DISAGREEMENT_TYPES
            structured_ids = sorted(
                structured_evidence_ids[item["reference_id"]] for item in structured_runtime
            )
            backstop_ids = sorted(backstop_evidence_ids[item["scan_id"]] for item in backstop_runtime)
            disagreement_id = stable_id(
                "scanner-disagreement",
                report["report_id"],
                disagreement_type,
                *structured_ids,
                *backstop_ids,
            )
            disagreements.append(
                {
                    "disagreement_id": disagreement_id,
                    "report_id": report["report_id"],
                    "report_path": report["relative_path"],
                    "disagreement_type": disagreement_type,
                    "structured_result": {
                        "runtime_reference_count": len(structured_runtime),
                        "directions": sorted({item["direction"] for item in structured_runtime}),
                        "dynamic_pattern": structured_dynamic,
                    },
                    "backstop_result": {
                        "active_query_count": len(backstop_runtime),
                        "statuses": sorted({item["result_status"] for item in backstop_runtime}),
                        "dynamic_pattern": backstop_dynamic,
                    },
                    "structured_evidence_ids": structured_ids,
                    "backstop_evidence_ids": backstop_ids,
                    "severity": "HIGH",
                    "resolution_status": "UNRESOLVED",
                    "reviewer_verdict": "PENDING_SCANNER_REMEDIATION",
                    "reviewer_evidence_ids": [],
                    "source_tree_commit": context.source_tree_commit,
                }
            )
    return sorted(disagreements, key=lambda item: item["disagreement_id"])
