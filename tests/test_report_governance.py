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
    extract_business_date,
    extract_report_references,
    is_control_report_path,
    naming_compliance,
    stable_report_id,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUSINESS_DATE = "2026-07-14"


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
        (PROJECT_ROOT / f"reports/report_catalog_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (PROJECT_ROOT / f"reports/report_dependency_registry_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
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
        (PROJECT_ROOT / f"reports/report_dependency_registry_{BUSINESS_DATE}.json").read_text(encoding="utf-8")
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
        ["python3", "scripts/governance/build_report_dependency_registry.py", "--business-date", BUSINESS_DATE],
        ["python3", "scripts/governance/build_report_catalog.py", "--business-date", BUSINESS_DATE],
        ["python3", "scripts/governance/build_phase_a_summary.py", "--business-date", BUSINESS_DATE],
    ]
    outputs = [
        PROJECT_ROOT / f"reports/report_dependency_registry_{BUSINESS_DATE}.json",
        PROJECT_ROOT / f"reports/report_dependency_registry_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_dependency_summary_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/report_catalog_{BUSINESS_DATE}.json",
        PROJECT_ROOT / f"reports/report_catalog_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_catalog_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/report_naming_compliance_audit_{BUSINESS_DATE}.csv",
        PROJECT_ROOT / f"reports/report_naming_compliance_audit_{BUSINESS_DATE}.metadata.json",
        PROJECT_ROOT / f"reports/reports_governance_phase_a_summary_{BUSINESS_DATE}.md",
        PROJECT_ROOT / f"reports/reports_governance_phase_a_remediation_{BUSINESS_DATE}.md",
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
