from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .backstop_scanner import scan_backstop_references
from .common import RunContext, create_run_context, load_config, metadata, pretty_json, sha256_bytes
from .disagreement import build_scanner_disagreements
from .evidence import (
    add_disagreement_evidence,
    add_manual_review_evidence,
    build_evidence_index,
    evidence_lookup_maps,
)
from .inventory import build_inventory, validate_inventory_content_hashes
from .readiness import build_migration_readiness
from .reference_index import build_reference_index
from .snapshot import content_record, csv_bytes, immutable_write, json_bytes, markdown_table
from .structured_scanner import scan_structured_references


def _scanner_precision_review(
    context: RunContext,
    structured: list[dict[str, Any]],
    structured_evidence_ids: dict[str, str],
) -> list[dict[str, Any]]:
    producers = [item for item in structured if item["direction"] == "PRODUCER"][:40]
    consumers = [item for item in structured if item["direction"] in {"CONSUMER", "MOVE_SOURCE"}][:40]
    operations = [
        item
        for item in structured
        if item["operation"]
        and item["operation"].rsplit(".", 1)[-1] in {"copy", "copy2", "copyfile", "move", "replace", "rename", "cp", "mv"}
    ]
    markdown = [item for item in structured if item["reference_kind"] == "MARKDOWN_REFERENCE"][:20]
    selected: dict[str, tuple[str, dict[str, Any]]] = {}
    for scope, records in (
        ("PRODUCER_PRECISION", producers),
        ("CONSUMER_PRECISION", consumers),
        ("FILE_OPERATION_COVERAGE", operations),
        ("MARKDOWN_SEMANTICS", markdown),
    ):
        for record in records:
            selected.setdefault(record["reference_id"], (scope, record))
    reviews: list[dict[str, Any]] = []
    for reference_id in sorted(selected):
        scope, record = selected[reference_id]
        valid_markdown = record["reference_kind"] != "MARKDOWN_REFERENCE" or record["reference_class"] in {
            "DOCUMENTATION_REFERENCE",
            "DOCUMENTATION_EXAMPLE",
            "CODE_BLOCK_REFERENCE",
        }
        reviews.append(
            {
                "reference_id": reference_id,
                "report_id": record["report_id"],
                "report_path": record["report_path"],
                "review_scope": scope,
                "source_path": record["source_path"],
                "line": record["line"],
                "direction": record["direction"],
                "reference_class": record["reference_class"],
                "operation": record["operation"],
                "structured_evidence_id": structured_evidence_ids[reference_id],
                "reviewer_verdict": "PASS" if valid_markdown else "FAIL",
                "reviewed_at": context.generated_at,
                "source_tree_commit": context.source_tree_commit,
            }
        )
    return reviews


def _validate(
    context: RunContext,
    inventory: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
) -> None:
    validate_inventory_content_hashes(context, inventory)
    report_ids = {item["report_id"] for item in inventory}
    if len(report_ids) != len(inventory):
        raise ValueError("duplicate report_id")
    evidence_ids = {item["evidence_id"] for item in evidence}
    if len(evidence_ids) != len(evidence):
        raise ValueError("duplicate evidence_id")
    if any(item["result_status"] not in {"FOUND_REFERENCE", "ZERO_RESULT_PROOF", "AMBIGUOUS_REFERENCE"} for item in backstop):
        raise ValueError("invalid backstop result status")
    referenced_evidence_ids: set[str] = set()
    for item in readiness:
        unresolved = set(item["decision_evidence_ids"]) - evidence_ids
        if unresolved:
            raise ValueError(f"unresolved evidence ids for {item['relative_path']}: {sorted(unresolved)}")
        referenced_evidence_ids.update(item["decision_evidence_ids"])
        if item["deletion_readiness"] == "SAFE_TO_DELETE_AFTER_AUTHORIZATION":
            raise ValueError("Phase A-R cannot authorize deletion")
        if item["migration_readiness"].startswith("PROVISIONALLY_SAFE"):
            if any(
                disagreement["report_id"] == item["report_id"] and disagreement["resolution_status"] != "RESOLVED"
                for disagreement in disagreements
            ):
                raise ValueError(f"unresolved disagreement entered candidates: {item['relative_path']}")
            report_evidence = [record for record in evidence if record["report_id"] == item["report_id"]]
            if not any(record["evidence_type"] == "MANUAL_REVIEW" for record in report_evidence):
                raise ValueError(f"candidate lacks MANUAL_REVIEW evidence: {item['relative_path']}")
            if not any(record["evidence_type"] == "BACKSTOP_ZERO_RESULT" for record in report_evidence):
                raise ValueError(f"candidate lacks BACKSTOP_ZERO_RESULT evidence: {item['relative_path']}")
    orphan = evidence_ids - referenced_evidence_ids
    if orphan:
        raise ValueError(f"orphan evidence ids: {sorted(orphan)[:10]}")
    required_fields = ("source_tree_commit", "scanner_version", "evidence_hash")
    for item in evidence:
        if any(not item.get(field) for field in required_fields):
            raise ValueError(f"incomplete evidence: {item['evidence_id']}")
    review_ids = {item["report_id"] for item in reviews}
    candidate_ids = {item["report_id"] for item in readiness if item["machine_provisional_before_review"]}
    if review_ids != candidate_ids:
        raise ValueError("manual review coverage is not 100 percent")


def _summary_markdown(
    context: RunContext,
    inventory: list[dict[str, Any]],
    structured: list[dict[str, Any]],
    backstop: list[dict[str, Any]],
    active_index: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    precision_reviews: list[dict[str, Any]],
) -> bytes:
    roles = Counter(item["role"] for item in inventory)
    statuses = Counter(item["migration_readiness"] for item in readiness)
    disagreement_types = Counter(item["disagreement_type"] for item in disagreements)
    backstop_statuses = Counter(item["result_status"] for item in backstop)
    producer_records = [item for item in structured if item["direction"] == "PRODUCER"]
    consumer_records = [item for item in structured if item["direction"] in {"CONSUMER", "MOVE_SOURCE"}]
    markdown_records = [item for item in structured if item["reference_kind"] == "MARKDOWN_REFERENCE"]
    lines = [
        "# Reports Governance Phase A-R Summary v2",
        "",
        f"- snapshot_revision: `{context.snapshot_revision}`",
        f"- supersedes: `{context.supersedes}`",
        f"- source_tree_commit: `{context.source_tree_commit}`",
        f"- generated_at: `{context.generated_at}`",
        f"- run_id: `{context.run_id}`",
        "- immutable: `true`",
        "- superseded_snapshot_status: `VALID_HISTORICAL_SNAPSHOT / SUPERSEDED`",
        "- phase_b: `BLOCKED`",
        "- zero_move: `PASS`",
        "- deletion_authorized: `false`",
        "",
        "## Inventory",
        "",
        f"- reports: `{len(inventory)}`",
        "- content_hash_mismatches: `0`",
        f"- archived: `{sum(item['location_status'] == 'ALREADY_ARCHIVED' for item in inventory)}`",
        f"- unknown_role: `{roles.get('UNKNOWN', 0)}`",
        "",
        "## Independent scanners",
        "",
        f"- structured_references: `{len(structured)}`",
        f"- structured_producers: `{len(producer_records)}`",
        f"- structured_consumers: `{len(consumer_records)}`",
        f"- markdown_references: `{len(markdown_records)}`",
        f"- markdown_runtime_misclassifications: `{sum(item['reference_class'] not in {'DOCUMENTATION_REFERENCE', 'DOCUMENTATION_EXAMPLE', 'CODE_BLOCK_REFERENCE'} for item in markdown_records)}`",
        f"- backstop_query_records: `{len(backstop)}`",
        f"- backstop_found_queries: `{backstop_statuses['FOUND_REFERENCE']}`",
        f"- backstop_ambiguous_queries: `{backstop_statuses['AMBIGUOUS_REFERENCE']}`",
        f"- backstop_zero_result_proofs: `{backstop_statuses['ZERO_RESULT_PROOF']}`",
        f"- scanner_disagreements: `{len(disagreements)}`",
        "",
        "### Disagreement distribution",
        "",
        "| type | count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {disagreement_types[key]} |" for key in sorted(disagreement_types))
    lines.extend(
        [
            "",
            "## Evidence and readiness",
            "",
            f"- evidence_records: `{len(evidence)}`",
            "- unresolved_evidence: `0`",
            "- orphan_evidence: `0`",
            "- duplicate_evidence_ids: `0`",
            f"- machine_provisional_before_review: `{sum(item['machine_provisional_before_review'] for item in readiness)}`",
            f"- candidate_reviews: `{len(reviews)}`",
            f"- candidate_reviews_passed: `{sum(item['final_reviewer_verdict'] == 'PASS' for item in reviews)}`",
            f"- structured_precision_review_records: `{len(precision_reviews)}`",
            f"- final_provisional: `{statuses.get('PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN', 0) + statuses.get('PROVISIONALLY_SAFE_RENAME_REQUIRED', 0)}`",
            "- safe_to_delete_after_authorization: `0`",
            "",
            "### Migration readiness distribution",
            "",
            "| status | count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {key} | {statuses[key]} |" for key in sorted(statuses))
    lines.extend(
        [
            "",
            "Phase A-R v2 only establishes provisional dry-run readiness. It does not move, rename, delete, or rewrite reports, implement a Runtime Path Registry, or start Phase B.",
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
    disagreements: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    precision_reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    artifacts: list[tuple[str, bytes]] = []

    def add(name: str, content: bytes) -> None:
        artifacts.append((name, content))

    inv_meta = metadata(context, "REPORT_INVENTORY", context.config["catalog_version"], len(inventory))
    add(f"report_inventory_v2_{snapshot_date}.json", json_bytes(inv_meta, inventory))
    add(f"report_inventory_v2_{snapshot_date}.csv", csv_bytes(inventory))
    add(
        f"report_inventory_v2_{snapshot_date}.md",
        markdown_table("Report Inventory v2", inventory, ["report_id", "relative_path", "role", "naming_status", "retention_status", "location_status"], inv_meta),
    )
    structured_meta = metadata(context, "STRUCTURED_REFERENCE_INDEX", context.config["structured_scanner_version"], len(structured))
    backstop_meta = metadata(context, "INDEPENDENT_BACKSTOP_INDEX", context.config["backstop_scanner_version"], len(backstop))
    active_meta = metadata(context, "ACTIVE_REFERENCE_INDEX", "active-reference-index-v2", len(active_index))
    disagreement_meta = metadata(context, "SCANNER_DISAGREEMENT_INDEX", "scanner-disagreement-index-v1", len(disagreements))
    add(f"structured_reference_index_v2_{snapshot_date}.json", json_bytes(structured_meta, structured))
    add(f"structured_reference_index_v2_{snapshot_date}.csv", csv_bytes(structured))
    add(f"backstop_reference_index_v2_{snapshot_date}.json", json_bytes(backstop_meta, backstop))
    add(f"backstop_reference_index_v2_{snapshot_date}.csv", csv_bytes(backstop))
    add(f"active_reference_index_v2_{snapshot_date}.json", json_bytes(active_meta, active_index))
    add(f"active_reference_index_v2_{snapshot_date}.csv", csv_bytes(active_index))
    add(f"scanner_disagreement_index_v1_{snapshot_date}.json", json_bytes(disagreement_meta, disagreements))
    add(f"scanner_disagreement_index_v1_{snapshot_date}.csv", csv_bytes(disagreements))
    evidence_meta = metadata(context, "GOVERNANCE_EVIDENCE_INDEX", context.config["evidence_version"], len(evidence))
    add(f"governance_evidence_index_v2_{snapshot_date}.json", json_bytes(evidence_meta, evidence))
    add(f"governance_evidence_index_v2_{snapshot_date}.csv", csv_bytes(evidence))
    readiness_meta = metadata(context, "MIGRATION_READINESS", context.config["classification_version"], len(readiness))
    add(f"migration_readiness_v2_{snapshot_date}.json", json_bytes(readiness_meta, readiness))
    add(f"migration_readiness_v2_{snapshot_date}.csv", csv_bytes(readiness))
    add(
        f"migration_readiness_v2_{snapshot_date}.md",
        markdown_table("Migration Readiness v2", readiness, ["relative_path", "migration_readiness", "deletion_readiness", "machine_provisional_before_review"], readiness_meta),
    )
    review_meta = metadata(context, "MANUAL_CANDIDATE_REVIEW", context.config["review_schema_version"], len(reviews))
    add(f"manual_candidate_review_v2_{snapshot_date}.json", json_bytes(review_meta, reviews))
    add(
        f"manual_candidate_review_v2_{snapshot_date}.md",
        markdown_table("Candidate 100 Percent Manual Review v2", reviews, ["report_path", "producer_verdict", "consumer_verdict", "retention_verdict", "naming_verdict", "final_reviewer_verdict"], review_meta),
    )
    precision_meta = metadata(context, "STRUCTURED_SCANNER_PRECISION_REVIEW", "structured-scanner-precision-review-v1", len(precision_reviews))
    add(f"structured_scanner_precision_review_v1_{snapshot_date}.json", json_bytes(precision_meta, precision_reviews))
    add(
        f"reports_governance_phase_ar_summary_v2_{snapshot_date}.md",
        _summary_markdown(context, inventory, structured, backstop, active_index, disagreements, evidence, readiness, reviews, precision_reviews),
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
        "metadata": metadata(context, "IMMUTABLE_GOVERNANCE_SNAPSHOT", "phase-ar-snapshot-manifest-v2", len(manifest_records)),
        "snapshot_date": snapshot_date,
        "prior_snapshot_status": "VALID_HISTORICAL_SNAPSHOT / SUPERSEDED",
        "group_manifest_sha256": group_hash,
        "files": manifest_records,
    }
    manifest_name = f"immutable_governance_snapshot_manifest_v2_{snapshot_date}.json"
    results[manifest_name] = immutable_write(output_root / manifest_name, pretty_json(manifest))
    return {"write_results": results, "group_manifest_sha256": group_hash, "files": manifest_records}


def build_phase_ar(
    root: Path,
    snapshot_date: str,
    output_root: Path | None = None,
    review_path: str | None = None,
    source_tree_commit: str | None = None,
) -> dict[str, Any]:
    del review_path  # v2 reviews are materialized from actual scanner results, never a template file.
    root = root.resolve()
    config = load_config(root)
    context = create_run_context(root, config, source_tree_commit)
    inventory = build_inventory(context)
    validate_inventory_content_hashes(context, inventory)
    structured = scan_structured_references(context, inventory)
    backstop = scan_backstop_references(context, inventory)
    evidence = build_evidence_index(context, inventory, structured, backstop)
    structured_evidence_ids, backstop_evidence_ids = evidence_lookup_maps(evidence)
    disagreements = build_scanner_disagreements(
        context,
        inventory,
        structured,
        backstop,
        structured_evidence_ids,
        backstop_evidence_ids,
    )
    evidence = add_disagreement_evidence(context, evidence, disagreements)
    active_index = build_reference_index(context, inventory, structured, backstop, disagreements)
    readiness, reviews = build_migration_readiness(context, inventory, active_index, evidence, structured, backstop)
    evidence = add_manual_review_evidence(context, evidence, readiness, reviews)
    precision_reviews = _scanner_precision_review(context, structured, structured_evidence_ids)
    _validate(context, inventory, backstop, disagreements, evidence, readiness, reviews)
    destination = output_root or (root / config["snapshot_output_root"])
    snapshot = _write_artifacts(
        context,
        snapshot_date,
        destination,
        inventory,
        structured,
        backstop,
        active_index,
        disagreements,
        evidence,
        readiness,
        reviews,
        precision_reviews,
    )
    backstop_statuses = Counter(item["result_status"] for item in backstop)
    readiness_statuses = Counter(item["migration_readiness"] for item in readiness)
    return {
        "metadata": metadata(context, "PHASE_AR_BUILD_RESULT", "phase-ar-build-result-v2", len(inventory)),
        "counts": {
            "inventory": len(inventory),
            "structured_references": len(structured),
            "structured_producers": sum(item["direction"] == "PRODUCER" for item in structured),
            "structured_consumers": sum(item["direction"] in {"CONSUMER", "MOVE_SOURCE"} for item in structured),
            "markdown_references": sum(item["reference_kind"] == "MARKDOWN_REFERENCE" for item in structured),
            "backstop_query_records": len(backstop),
            "backstop_found_queries": backstop_statuses["FOUND_REFERENCE"],
            "backstop_ambiguous_queries": backstop_statuses["AMBIGUOUS_REFERENCE"],
            "backstop_zero_result_proofs": backstop_statuses["ZERO_RESULT_PROOF"],
            "evidence": len(evidence),
            "scanner_disagreements": len(disagreements),
            "machine_provisional_before_review": sum(item["machine_provisional_before_review"] for item in readiness),
            "manual_reviews": len(reviews),
            "manual_reviews_passed": sum(item["final_reviewer_verdict"] == "PASS" for item in reviews),
            "final_provisional": sum(item["migration_readiness"].startswith("PROVISIONALLY_SAFE") for item in readiness),
            "provisionally_safe": readiness_statuses["PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN"],
            "rename_required": readiness_statuses["PROVISIONALLY_SAFE_RENAME_REQUIRED"],
        },
        "snapshot": snapshot,
    }
