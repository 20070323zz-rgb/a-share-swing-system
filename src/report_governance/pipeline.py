from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .backstop_scanner import scan_backstop_references
from .common import RunContext, create_run_context, load_config, metadata, pretty_json, sha256_bytes
from .evidence import build_evidence_index
from .inventory import build_inventory
from .readiness import build_migration_readiness
from .reference_index import build_reference_index
from .snapshot import content_record, csv_bytes, immutable_write, json_bytes, markdown_table
from .structured_scanner import scan_structured_references


def _validate(
    inventory: list[dict[str, Any]],
    active_index: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
) -> None:
    report_ids = {item["report_id"] for item in inventory}
    if len(report_ids) != len(inventory):
        raise ValueError("duplicate report_id")
    evidence_ids = {item["evidence_id"] for item in evidence}
    if len(evidence_ids) != len(evidence):
        raise ValueError("duplicate evidence_id")
    if {item["report_id"] for item in active_index} != report_ids:
        raise ValueError("active reference index does not cover inventory")
    for item in readiness:
        unresolved = set(item["decision_evidence_ids"]) - evidence_ids
        if unresolved:
            raise ValueError(f"unresolved evidence ids for {item['relative_path']}: {sorted(unresolved)}")
        if item["deletion_readiness"] == "SAFE_TO_DELETE_AFTER_AUTHORIZATION":
            raise ValueError("Phase A-R cannot authorize deletion")


def _summary_markdown(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    active_index: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
) -> bytes:
    roles = Counter(item["role"] for item in inventory)
    statuses = Counter(item["migration_readiness"] for item in readiness)
    producer_reports = {item["report_id"] for item in structured if item["direction"] == "PRODUCER"}
    consumer_reports = {item["report_id"] for item in structured if item["direction"] == "CONSUMER"}
    lines = [
        "# Reports Governance Phase A-R Summary v1",
        "",
        f"- source_tree_commit: `{context.source_tree_commit}`",
        f"- generated_at: `{context.generated_at}`",
        f"- run_id: `{context.run_id}`",
        "- immutable: `true`",
        "- phase_b: `BLOCKED`",
        "- zero_move: `PASS`",
        "- deletion_authorized: `false`",
        "",
        "## Inventory",
        "",
        f"- reports: `{len(inventory)}`",
        f"- duplicate_report_ids: `0`",
        f"- archived: `{sum(item['location_status'] == 'ALREADY_ARCHIVED' for item in inventory)}`",
        f"- unknown_role: `{roles.get('UNKNOWN', 0)}`",
        "",
        "## Independent reference engines",
        "",
        f"- structured_references: `{len(structured)}`",
        f"- structured_producer_reports: `{len(producer_reports)}`",
        f"- structured_consumer_reports: `{len(consumer_reports)}`",
        f"- backstop_references: `{len(backstop)}`",
        f"- scanner_disagreements: `{sum(item['reference_disagreement'] for item in active_index)}`",
        "",
        "## Evidence and readiness",
        "",
        f"- evidence_records: `{len(evidence)}`",
        "- unresolved_evidence: `0`",
        f"- machine_provisional_before_review: `{sum(item['machine_provisional_before_review'] for item in readiness)}`",
        f"- candidate_reviews: `{len(reviews)}`",
        f"- candidate_reviews_passed: `{sum(item['reviewer_verdict'] == 'PASS' for item in reviews)}`",
        f"- final_provisional: `{statuses.get('PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN', 0) + statuses.get('PROVISIONALLY_SAFE_RENAME_REQUIRED', 0)}`",
        "- safe_to_delete_after_authorization: `0`",
        "",
        "### Migration readiness distribution",
        "",
        "| status | count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {statuses[key]} |" for key in sorted(statuses))
    lines.extend(
        [
            "",
            "Phase A-R only establishes dry-run readiness. It does not move, rename, delete, or rewrite reports, implement a runtime Path Registry, or start Phase B.",
        ]
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write_artifacts(
    context: RunContext,
    snapshot_date: str,
    output_root: Path,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    active_index: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    artifacts: list[tuple[str, bytes]] = []

    def add(name: str, content: bytes) -> None:
        artifacts.append((name, content))

    inv_meta = metadata(context, "REPORT_INVENTORY", context.config["catalog_version"], len(inventory))
    add(f"report_inventory_v1_{snapshot_date}.json", json_bytes(inv_meta, inventory))
    add(f"report_inventory_v1_{snapshot_date}.csv", csv_bytes(inventory))
    add(
        f"report_inventory_v1_{snapshot_date}.md",
        markdown_table("Report Inventory v1", inventory, ["report_id", "relative_path", "role", "naming_status", "retention_status", "location_status"], inv_meta),
    )
    structured_meta = metadata(context, "STRUCTURED_REFERENCE_INDEX", context.config["structured_scanner_version"], len(structured))
    backstop_meta = metadata(context, "INDEPENDENT_BACKSTOP_INDEX", context.config["backstop_scanner_version"], len(backstop))
    active_meta = metadata(context, "ACTIVE_REFERENCE_INDEX", "active-reference-index-v1", len(active_index))
    add(f"structured_reference_index_v1_{snapshot_date}.json", json_bytes(structured_meta, structured))
    add(f"structured_reference_index_v1_{snapshot_date}.csv", csv_bytes(structured))
    add(f"backstop_reference_index_v1_{snapshot_date}.json", json_bytes(backstop_meta, backstop))
    add(f"backstop_reference_index_v1_{snapshot_date}.csv", csv_bytes(backstop))
    add(f"active_reference_index_v1_{snapshot_date}.json", json_bytes(active_meta, active_index))
    add(f"active_reference_index_v1_{snapshot_date}.csv", csv_bytes(active_index))
    evidence_meta = metadata(context, "GOVERNANCE_EVIDENCE_INDEX", context.config["evidence_version"], len(evidence))
    add(f"governance_evidence_index_v1_{snapshot_date}.json", json_bytes(evidence_meta, evidence))
    add(f"governance_evidence_index_v1_{snapshot_date}.csv", csv_bytes(evidence))
    readiness_meta = metadata(context, "MIGRATION_READINESS", context.config["classification_version"], len(readiness))
    add(f"migration_readiness_v1_{snapshot_date}.json", json_bytes(readiness_meta, readiness))
    add(f"migration_readiness_v1_{snapshot_date}.csv", csv_bytes(readiness))
    add(
        f"migration_readiness_v1_{snapshot_date}.md",
        markdown_table("Migration Readiness v1", readiness, ["relative_path", "migration_readiness", "deletion_readiness", "machine_provisional_before_review"], readiness_meta),
    )
    review_meta = metadata(context, "CANDIDATE_FULL_REVIEW", "candidate-full-review-v1", len(reviews))
    add(f"candidate_full_review_v1_{snapshot_date}.json", json_bytes(review_meta, reviews))
    add(
        f"candidate_full_review_v1_{snapshot_date}.md",
        markdown_table("Candidate 100 Percent Review", reviews, ["report_path", "structured_scanner_result", "backstop_scanner_result", "producer_check", "consumer_check", "reviewer_verdict"], review_meta),
    )
    add(
        f"reports_governance_phase_ar_summary_v1_{snapshot_date}.md",
        _summary_markdown(context, inventory, structured, backstop, active_index, evidence, readiness, reviews),
    )
    results: dict[str, str] = {}
    for relative_path, content in artifacts:
        results[relative_path] = immutable_write(output_root / relative_path, content)
    manifest_records = [content_record(output_root / relative_path, output_root) for relative_path, _ in artifacts]
    manifest_records.sort(key=lambda item: item["relative_path"])
    group_hash = sha256_bytes(
        "".join(f"{item['relative_path']}\t{item['content_sha256']}\n" for item in manifest_records).encode("utf-8")
    )
    manifest = {
        "metadata": metadata(context, "IMMUTABLE_GOVERNANCE_SNAPSHOT", "phase-ar-snapshot-manifest-v1", len(manifest_records)),
        "snapshot_date": snapshot_date,
        "group_manifest_sha256": group_hash,
        "files": manifest_records,
    }
    manifest_name = f"immutable_governance_snapshot_manifest_v1_{snapshot_date}.json"
    results[manifest_name] = immutable_write(output_root / manifest_name, pretty_json(manifest))
    return {"write_results": results, "group_manifest_sha256": group_hash, "files": manifest_records}


def build_phase_ar(
    root: Path,
    snapshot_date: str,
    output_root: Path | None = None,
    review_path: str | None = "configs/report_governance_phase_ar_reviews.json",
) -> dict[str, Any]:
    root = root.resolve()
    config = load_config(root)
    context = create_run_context(root, config)
    inventory = build_inventory(context)
    structured = scan_structured_references(context, inventory)
    backstop = scan_backstop_references(context, inventory)
    active_index = build_reference_index(context, inventory, structured, backstop)
    evidence = build_evidence_index(context, inventory, structured, backstop)
    readiness, reviews = build_migration_readiness(context, inventory, active_index, evidence, review_path)
    _validate(inventory, active_index, evidence, readiness)
    destination = output_root or (root / config["snapshot_output_root"])
    snapshot = _write_artifacts(
        context,
        snapshot_date,
        destination,
        inventory,
        structured,
        backstop,
        active_index,
        evidence,
        readiness,
        reviews,
    )
    return {
        "metadata": metadata(context, "PHASE_AR_BUILD_RESULT", "phase-ar-build-result-v1", len(inventory)),
        "counts": {
            "inventory": len(inventory),
            "structured_references": len(structured),
            "backstop_references": len(backstop),
            "evidence": len(evidence),
            "scanner_disagreements": sum(item["reference_disagreement"] for item in active_index),
            "machine_provisional_before_review": sum(item["machine_provisional_before_review"] for item in readiness),
            "manual_reviews": len(reviews),
            "manual_reviews_passed": sum(item["reviewer_verdict"] == "PASS" for item in reviews),
            "final_provisional": sum(item["migration_readiness"].startswith("PROVISIONALLY_SAFE") for item in readiness),
        },
        "snapshot": snapshot,
    }
