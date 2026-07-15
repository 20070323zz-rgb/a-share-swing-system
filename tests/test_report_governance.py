from __future__ import annotations

import json
import os
import subprocess
import hashlib
from pathlib import Path

from scripts.governance.dependency_classifier import GENERATOR_VERSION, classify_source_text
from scripts.governance.report_governance_common import (
    MIGRATION_RISK_VALUES,
    REFERENCE_TYPE_VALUES,
    ROLE_VALUES,
    dynamic_producer_matches_path,
    extract_business_date,
    extract_report_references,
    is_control_report_path,
    naming_compliance,
    stable_report_id,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUSINESS_DATE = "2026-07-15"
REVISION = "v3"


def test_report_id_is_stable_and_path_derived() -> None:
    path = "reports/dashboard_data.json"
    assert stable_report_id(path) == stable_report_id(path)
    assert stable_report_id(path) != stable_report_id("reports/latest_brief.md")
    assert stable_report_id(path).startswith("report_")


def test_business_date_never_uses_filesystem_mtime(tmp_path: Path) -> None:
    report = tmp_path / "undated_summary.md"
    report.write_text("生成日期：2026-07-14\n", encoding="utf-8")
    os.utime(report, (1_700_000_000, 1_700_000_000))
    assert extract_business_date(report) == "UNKNOWN"
    report.write_text("business_date: 2026-07-13\n", encoding="utf-8")
    assert extract_business_date(report) == "2026-07-13"


def test_reference_extraction_covers_static_computed_and_dynamic() -> None:
    assert extract_report_references('read("reports/latest_brief.md")') == [
        ("reports/latest_brief.md", "STATIC")
    ]
    assert extract_report_references('path = REPORT_DIR / "paper_summary.json"') == [
        ("reports/paper_summary.json", "STATIC_COMPUTED")
    ]
    assert extract_report_references('path = REPORT_DIR / f"daily_{run_date}.md"') == [
        ("reports/daily_{run_date}.md", "DYNAMIC")
    ]
    assert extract_report_references('STATUS_JSON="$REPORT_DIR/app_launch_diagnostics.json"') == [
        ("reports/app_launch_diagnostics.json", "STATIC_COMPUTED")
    ]


def test_naming_standard_accepts_terminal_iso_dates() -> None:
    assert naming_compliance("reports/daily_signal_2026-07-14.md", "DATED_DAILY", False) == "COMPLIANT"
    assert naming_compliance("reports/monthly_model_review_2026-07.md", "DATED_MONTHLY", False) == "COMPLIANT"
    assert naming_compliance("reports/daily_signal_final2.md", "DATED_DAILY", False) == "NON_COMPLIANT"
    assert naming_compliance("reports/latest_brief.md", "CURRENT_ALIAS", True) == "LEGACY_STABLE_ALIAS"


def test_generated_catalog_and_registry_contracts() -> None:
    catalog = json.loads(
        (PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (PROJECT_ROOT / f"reports/report_dependency_registry_{REVISION}_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
    )

    assert catalog["record_count"] == len(catalog["records"])
    assert registry["record_count"] == len(registry["records"])
    assert not any(is_control_report_path(row["current_path"]) for row in catalog["records"])
    assert all(row["role"] in ROLE_VALUES for row in catalog["records"])
    assert all(row["migration_risk"] in MIGRATION_RISK_VALUES for row in catalog["records"])
    assert all(row["reference_type"] in REFERENCE_TYPE_VALUES for row in registry["records"])

    by_path = {row["current_path"]: row for row in catalog["records"]}
    dashboard = by_path["reports/dashboard_data.json"]
    assert dashboard["runtime_locked"] is True
    assert dashboard["archive_candidate"] is False
    assert dashboard["migration_risk"] == "RUNTIME_LOCKED"

    dynamic = [row for row in registry["records"] if row["static_or_dynamic"] == "DYNAMIC"]
    assert dynamic
    assert all(row["confidence"] != "HIGH" for row in dynamic)

    expected_dynamic_blocks = {
        row["current_path"]
        for row in catalog["records"]
        if row["matched_dynamic_producer_count"] > 0
    }
    assert len(expected_dynamic_blocks) == 12
    for path in expected_dynamic_blocks:
        assert by_path[path]["archive_candidate"] is False
        assert by_path[path]["active_generator"] is True
        assert by_path[path]["producer_match_type"] == "DYNAMIC_PATTERN"
        assert "ACTIVE_DYNAMIC_PRODUCER" in by_path[path]["archive_block_reasons"]
        assert by_path[path]["archive_block_evidence"]["ACTIVE_DYNAMIC_PRODUCER"]
        assert by_path[path]["matched_dynamic_producer_count"] >= 1


def test_golden_reference_classification_is_exact() -> None:
    fixtures = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/report_governance/reference_classification_golden.json"
        ).read_text(encoding="utf-8")
    )
    assert len([item for item in fixtures if item["direction"] == "PRODUCER"]) >= 20
    assert len([item for item in fixtures if item["direction"] == "CONSUMER"]) >= 20
    for item in fixtures:
        rows = classify_source_text(item["source_file"], item["source"])
        assert any(
            row["normalized_target"] == item["target"]
            and row["reference_type"] == item["reference_type"]
            and row["direction"] == item["direction"]
            for row in rows
        ), item["name"]


def test_scoped_dynamic_producer_fixtures_are_exact() -> None:
    fixtures = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/report_governance/scoped_dynamic_producers.json"
        ).read_text(encoding="utf-8")
    )
    assert len(fixtures) >= 20
    assert {item["scope_type"] for item in fixtures} >= {
        "MODULE",
        "FUNCTION",
        "ASYNC_FUNCTION",
        "LAMBDA",
        "COMPREHENSION",
    }
    for item in fixtures:
        rows = classify_source_text("src/scoped_fixture.py", item["source"])
        repeated = classify_source_text("src/scoped_fixture.py", item["source"])
        matches = [
            row
            for row in rows
            if row["normalized_target"] == item["target"]
            and row["reference_type"] == "PRODUCER_WRITE"
            and row["direction"] == "WRITE"
            and row["scope_type"] == item["scope_type"]
            and row["scope_qualified_name"] == item["scope_name"]
            and row["dynamic_path_pattern"] == item["pattern"]
            and row["binding_name"] == item["binding_name"]
        ]
        if not item.get("expect_producer", True):
            assert not matches, item["name"]
            assert not any(
                row["normalized_target"] == item["target"]
                and row["reference_type"] == "PRODUCER_WRITE"
                for row in rows
            ), item["name"]
            continue
        assert matches, item["name"]
        row = matches[0]
        repeated_row = next(
            candidate
            for candidate in repeated
            if candidate["reference_id"] == row["reference_id"]
        )
        assert row["scope_id"] == repeated_row["scope_id"], item["name"]
        assert row["binding_id"] == repeated_row["binding_id"], item["name"]
        assert row["scope_source_start_line"] > 0, item["name"]
        assert row["scope_source_end_line"] >= row["scope_source_start_line"], item["name"]
        if row["scope_type"] != "MODULE":
            assert row["parent_scope_id"], item["name"]
        if item["binding_name"]:
            assert row["binding_assignment_line"] > 0, item["name"]
            assert row["binding_assignment_kind"], item["name"]
            assert row["binding_normalized_expression"], item["name"]
            assert row["binding_source_excerpt_hash"], item["name"]
        assert row["dynamic_pattern_kind"] == item.get("pattern_kind", "DATE_TEMPLATE"), item["name"]
        if "binding_version" in item:
            assert row["binding_version"] == item["binding_version"], item["name"]
        if "binding_confidence" in item:
            assert row["binding_confidence"] == item["binding_confidence"], item["name"]


def test_dynamic_producer_matching_is_strict_and_unknown_patterns_do_not_match() -> None:
    trusted = {
        "reference_type": "PRODUCER_WRITE",
        "consumer_or_producer": "PRODUCER",
        "static_or_dynamic": "DYNAMIC",
        "dynamic_path_pattern": "reports/daily_signal_<DATE>.md",
        "dynamic_pattern_kind": "DATE_TEMPLATE",
    }
    assert dynamic_producer_matches_path(trusted, "reports/daily_signal_2026-07-15.md")
    assert not dynamic_producer_matches_path(trusted, "reports/daily_signal_latest.md")
    assert not dynamic_producer_matches_path(trusted, "reports/prefix_daily_signal_2026-07-15.md")
    assert not dynamic_producer_matches_path(trusted, "reports/daily_signal_2026-07-15.csv")
    unknown = dict(
        trusted,
        dynamic_path_pattern="reports/daily_signal_<DYNAMIC>.md",
        dynamic_pattern_kind="UNKNOWN_DYNAMIC",
    )
    assert not dynamic_producer_matches_path(unknown, "reports/daily_signal_2026-07-15.md")
    weekly = dict(
        trusted,
        dynamic_path_pattern="reports/weekly_review_<DATE>.md",
    )
    assert dynamic_producer_matches_path(weekly, "reports/weekly_review_2026-07-15.md")
    positives = [f"reports/daily_signal_2026-07-{day:02d}.md" for day in range(1, 21)]
    negatives = [f"reports/daily_signal_summary_{index:03d}.md" for index in range(1, 91)]
    assert all(dynamic_producer_matches_path(trusted, path) for path in positives)
    assert not any(dynamic_producer_matches_path(trusted, path) for path in negatives)


def test_shell_copy_move_directional_fixtures_are_exact() -> None:
    fixtures = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/report_governance/reference_classification_golden.json"
        ).read_text(encoding="utf-8")
    )
    directional = [item for item in fixtures if item.get("kind") == "shell_direction"]
    assert len(directional) >= 15
    assert len([item for item in directional if item["direction"] == "READ"]) >= 6
    assert len([item for item in directional if item["direction"] == "MOVE_SOURCE"]) >= 4
    assert len([item for item in directional if item["direction"] in {"WRITE", "PRODUCER"}]) >= 3
    for item in directional:
        rows = classify_source_text(item["source_file"], item["source"])
        target_rows = [row for row in rows if row["normalized_target"] == item["target"]]
        assert any(
            row["reference_type"] == item["reference_type"]
            and row["direction"] == item["direction"]
            for row in target_rows
        ), item["name"]
        forbidden = item.get("forbidden_reference_type")
        if forbidden:
            assert not any(row["reference_type"] == forbidden for row in target_rows), item["name"]


def test_run_daily_close_backup_and_restore_directions() -> None:
    script = PROJECT_ROOT / "scripts/run_daily_close.sh"
    rows = classify_source_text(
        "scripts/run_daily_close.sh", script.read_text(encoding="utf-8")
    )
    backup_targets = {
        86: "reports/data_source_status.json",
        87: "reports/data_source_status_report.md",
        88: "reports/data_update_status.json",
    }
    for line, target in backup_targets.items():
        target_rows = [
            row
            for row in rows
            if row["source_line_start"] == line and row["normalized_target"] == target
        ]
        assert any(
            row["reference_type"] == "FILE_COPY_SOURCE" and row["direction"] == "READ"
            for row in target_rows
        )
        assert not any(row["reference_type"] == "PRODUCER_WRITE" for row in target_rows)

    restore_targets = {
        123: "reports/data_source_status.json",
        124: "reports/data_source_status_report.md",
        125: "reports/data_update_status.json",
    }
    for line, target in restore_targets.items():
        target_rows = [
            row
            for row in rows
            if row["source_line_start"] == line and row["normalized_target"] == target
        ]
        assert any(
            row["reference_type"] == "PRODUCER_WRITE" and row["direction"] == "WRITE"
            for row in target_rows
        )


def test_availability_audit_data_retirement_contract_is_complete() -> None:
    design = (PROJECT_ROOT / "docs/report_path_registry_design.md").read_text(encoding="utf-8")
    required_tokens = {
        "data/staging/tushare_etf_availability/",
        "TEMPORARY_AUDIT_DATA",
        "UNTIL_MIGRATION_VALIDATED",
        "TEMPORARY_AUDIT",
        "SHADOW_EVIDENCE_ONLY",
        "RETIREMENT_PENDING_AUTHORIZATION",
        "RETIREMENT_APPROVED",
        "TEMPORARY_AUDIT_DATA_RETIRED",
        "RETIREMENT_VALIDATION_FAILED",
        "availability_audit_data_retirement_readiness_<YYYY-MM-DD>.md",
        "availability_audit_data_retirement_validation_<YYYY-MM-DD>.md",
        "EVIDENCE_NOT_RECONSTRUCTABLE",
    }
    assert not {token for token in required_tokens if token not in design}
    assert all(f"RETIREMENT-PRE-{index:02d}" in design for index in range(1, 15))
    lifecycle = [
        "ACTIVE_COLLECTING",
        "AUDIT_COMPLETE",
        "MAIN_DECISION_RECORDED",
        "PRIMARY_SOURCE_MIGRATION_COMPLETE",
        "POST_MIGRATION_VALIDATION_PASS",
        "FINAL_AUDIT_ARCHIVE_COMPLETE",
        "RETIREMENT_AUTHORIZED",
        "TEMPORARY_DATA_DELETED",
        "DELETION_AUDIT_PASS",
    ]
    positions = [design.index(state) for state in lifecycle]
    assert positions == sorted(positions)


def test_reference_identity_and_excerpt_hash_survive_unrelated_blank_line() -> None:
    source = 'payload = (REPORT_DIR / "identity.json").read_text()'
    first = classify_source_text("src/example.py", source)[0]
    shifted = classify_source_text("src/example.py", "\n" + source)[0]
    assert first["reference_id"] == shifted["reference_id"]
    assert first["source_line_start"] + 1 == shifted["source_line_start"]
    normalized = " ".join(source.strip().split())
    assert first["source_excerpt_hash"] == hashlib.sha256(normalized.encode()).hexdigest()
    assert first["generator_version"] == GENERATOR_VERSION


def test_committed_registry_lines_and_excerpt_hashes_match_source() -> None:
    registry = json.loads(
        (PROJECT_ROOT / f"reports/report_dependency_registry_{REVISION}_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
    )
    for row in registry["records"]:
        source_path = PROJECT_ROOT / row["source_file"]
        lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
        excerpt = "\n".join(lines[row["source_line_start"] - 1 : row["source_line_end"]])
        normalized = " ".join(excerpt.strip().split())
        assert row["source_excerpt_hash"] == hashlib.sha256(normalized.encode()).hexdigest(), row[
            "reference_id"
        ]


def test_generators_are_byte_stable_on_repeated_runs() -> None:
    commands = [
        ["python3", "scripts/governance/build_report_dependency_registry.py", "--business-date", BUSINESS_DATE, "--snapshot-revision", REVISION],
        ["python3", "scripts/governance/build_report_catalog.py", "--business-date", BUSINESS_DATE, "--snapshot-revision", REVISION],
        ["python3", "scripts/governance/build_report_governance_evidence_registry.py", "--business-date", BUSINESS_DATE],
        ["python3", "scripts/governance/build_phase_a_summary.py", "--business-date", BUSINESS_DATE, "--snapshot-revision", REVISION],
    ]
    outputs = [
        PROJECT_ROOT / f"reports/report_dependency_registry_{REVISION}_{BUSINESS_DATE}.json",
        PROJECT_ROOT / f"reports/report_dependency_registry_{REVISION}_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_dependency_summary_{REVISION}_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.json",
        PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/report_naming_compliance_audit_{REVISION}_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_naming_compliance_audit_{REVISION}_{BUSINESS_DATE}.metadata.json",
        PROJECT_ROOT / f"reports/report_governance_evidence_registry_v1_{BUSINESS_DATE}.json",
        PROJECT_ROOT / f"reports/report_governance_evidence_registry_v1_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/reports_governance_phase_a_summary_{REVISION}_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/reports_governance_phase_a_evidence_and_archive_state_remediation_{BUSINESS_DATE}.md",
    ]
    committed = {path: path.read_bytes() for path in outputs}
    for command in commands:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    first = {path: path.read_bytes() for path in outputs}
    assert committed == first
    for command in commands:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    second = {path: path.read_bytes() for path in outputs}
    assert first == second
