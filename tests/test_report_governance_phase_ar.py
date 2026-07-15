from __future__ import annotations

import json
import ast
from pathlib import Path

import pytest

from src.report_governance.backstop_scanner import scan_backstop_references
from src.report_governance.authority_merge import AuthorityMergeError, apply_owned_overlay
from src.report_governance.common import create_run_context, load_config, source_files
from src.report_governance.evidence import build_evidence_index
from src.report_governance.inventory import build_inventory, infer_business_date
from src.report_governance.pipeline import build_phase_ar
from src.report_governance.readiness import build_migration_readiness
from src.report_governance.reference_index import build_reference_index
from src.report_governance.snapshot import immutable_write
from src.report_governance.structured_scanner import ExpressionResolver, scan_structured_references
from src.report_governance.temporal import valid_date_token, valid_month_token


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def governance_state():
    context = create_run_context(ROOT, load_config(ROOT))
    inventory = build_inventory(context)
    structured = scan_structured_references(context, inventory)
    backstop = scan_backstop_references(context, inventory)
    active = build_reference_index(context, inventory, structured, backstop)
    evidence = build_evidence_index(context, inventory, structured, backstop)
    readiness, reviews = build_migration_readiness(context, inventory, active, evidence)
    return {
        "context": context,
        "inventory": inventory,
        "structured": structured,
        "backstop": backstop,
        "active": active,
        "evidence": evidence,
        "readiness": readiness,
        "reviews": reviews,
    }


def test_inventory_is_deterministic_and_excludes_control_artifacts(governance_state):
    context = governance_state["context"]
    assert governance_state["inventory"] == build_inventory(context)
    assert len({item["report_id"] for item in governance_state["inventory"]}) == len(governance_state["inventory"])
    assert not any(item["relative_path"].startswith("reports/governance/phase_ar/") for item in governance_state["inventory"])


def test_business_date_never_uses_mtime(tmp_path):
    path = tmp_path / "report_without_date.md"
    path.write_text("# no business date\n", encoding="utf-8")
    assert infer_business_date(path) == (None, False)
    path.write_text("generated_at: 2026-07-15 12:00:00\n", encoding="utf-8")
    assert infer_business_date(path) == ("2026-07-15", True)


def test_date_and_month_tokens_are_strict():
    assert valid_date_token("2026-07-15")
    assert valid_date_token("20260715")
    assert not valid_date_token("2026-02-29")
    assert not valid_date_token("2026-99-99")
    assert not valid_date_token("2026-07")
    assert valid_month_token("2026-07")
    assert not valid_month_token("202607")
    assert valid_month_token("202607", allow_compact=True)


def test_known_43_active_reference_regressions_are_fail_closed(governance_state):
    fixture = json.loads((ROOT / "tests/fixtures/report_governance/known_active_reference_regressions.json").read_text())
    records = fixture["records"]
    assert len(records) == 43
    active = {item["relative_path"]: item for item in governance_state["active"]}
    readiness = {item["relative_path"]: item for item in governance_state["readiness"]}
    for case in records:
        path = case["report_path"]
        assert active[path]["structured_reference_count"] + active[path]["backstop_reference_count"] > 0, path
        assert active[path]["backstop_reference_count"] > 0, path
        assert readiness[path]["migration_readiness"] == case["expected_status"], path
        assert not readiness[path]["migration_readiness"].startswith("PROVISIONALLY_SAFE"), path
        if case["producer_or_consumer"] == "PRODUCER":
            assert active[path]["structured_producer_count"] > 0, path


def test_dryrun_status_has_parseable_producer_evidence(governance_state):
    path = "reports/data_update_status.dryrun.json"
    structured = [item for item in governance_state["structured"] if item["report_path"] == path]
    producers = [item for item in structured if item["direction"] == "PRODUCER"]
    assert producers
    assert all(item["source_path"] and item["line"] and item["excerpt_sha256"] for item in producers)


def test_archive_and_deletion_boundaries(governance_state):
    readiness = governance_state["readiness"]
    archived = [item for item in readiness if "/archive/" in item["relative_path"]]
    assert archived
    assert all(item["migration_readiness"] == "NOT_APPLICABLE_ALREADY_ARCHIVED" for item in archived)
    assert not any(item["migration_readiness"].startswith("PROVISIONALLY_SAFE") for item in archived)
    assert not any(item["deletion_readiness"] == "SAFE_TO_DELETE_AFTER_AUTHORIZATION" for item in readiness)


def test_ordinary_docs_are_not_scanned_as_runtime_sources(governance_state):
    scanned = {path.relative_to(ROOT).as_posix() for path in source_files(governance_state["context"])}
    assert "docs/operational_playbook.md" not in scanned
    assert "docs/current_project_state.md" in scanned
    assert "docs/current_phase_status.json" in scanned


def test_evidence_is_complete_and_resolvable(governance_state):
    evidence_ids = {item["evidence_id"] for item in governance_state["evidence"]}
    assert len(evidence_ids) == len(governance_state["evidence"])
    for decision in governance_state["readiness"]:
        assert decision["decision_evidence_ids"]
        assert set(decision["decision_evidence_ids"]) <= evidence_ids
    absence = [item for item in governance_state["evidence"] if item["evidence_type"].startswith("NO_")]
    assert absence
    assert all(item["scanner_version"] and item["scanned_source_roots"] and item["search_keys"] for item in absence)
    assert all(item["result_count"] == 0 and item["result"]["evidence_hash"] for item in absence)


def test_scanner_disagreement_is_explicit(governance_state):
    for item in governance_state["active"]:
        expected = (item["structured_reference_count"] == 0) != (item["backstop_reference_count"] == 0)
        assert item["reference_disagreement"] is expected
        if expected:
            assert item["manual_review_required"]


def test_dynamic_report_templates_are_materialized(governance_state):
    daily = [item for item in governance_state["structured"] if "daily_signal_" in item["report_path"]]
    weekly = [item for item in governance_state["structured"] if "weekly_review_" in item["report_path"]]
    assert any(item["direction"] == "PRODUCER" for item in daily)
    assert any(item["direction"] == "PRODUCER" for item in weekly)


def test_class_method_path_lookup_requires_explicit_scope():
    resolver = ExpressionResolver(
        {
            "self.OUTPUT": "reports/class_output.md",
            "cls.OUTPUT": "reports/class_output.md",
            "Writer.OUTPUT": "reports/class_output.md",
        }
    )
    assert resolver.resolve(ast.parse("OUTPUT", mode="eval").body) is None
    assert resolver.resolve(ast.parse("self.OUTPUT", mode="eval").body) == "reports/class_output.md"
    assert resolver.resolve(ast.parse("cls.OUTPUT", mode="eval").body) == "reports/class_output.md"
    assert resolver.resolve(ast.parse("Writer.OUTPUT", mode="eval").body) == "reports/class_output.md"


def test_immutable_writer_is_idempotent_and_fail_fast(tmp_path):
    path = tmp_path / "snapshot.json"
    assert immutable_write(path, b"same\n") == "CREATED"
    assert immutable_write(path, b"same\n") == "IDEMPOTENT"
    with pytest.raises(FileExistsError):
        immutable_write(path, b"different\n")


def test_authority_merge_preserves_availability_and_unknown_nested_fields():
    authority = {"availability": {"status": "ACTIVE", "unknown": {"keep": 1}}, "report_status": "OLD"}
    overlay = {"availability": {"status": "WRONG"}, "report_status": "ACTIVE"}
    with pytest.raises(AuthorityMergeError):
        apply_owned_overlay(authority, overlay, {"report_status"})
    merged = apply_owned_overlay(authority, {"report_status": "ACTIVE"}, {"report_status"})
    assert merged["availability"] == authority["availability"]
    assert merged["report_status"] == "ACTIVE"


def test_three_clean_rebuilds_are_byte_stable(tmp_path):
    roots = [tmp_path / f"run-{index}" for index in range(3)]
    results = [build_phase_ar(ROOT, "2026-07-15", root) for root in roots]
    hashes = [result["snapshot"]["group_manifest_sha256"] for result in results]
    assert len(set(hashes)) == 1
    relative_files = [item["relative_path"] for item in results[0]["snapshot"]["files"]]
    for relative in relative_files:
        assert len({(root / relative).read_bytes() for root in roots}) == 1
