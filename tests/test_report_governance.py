from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from scripts.governance.report_governance_common import (
    CONTROL_REPORT_PATHS,
    MIGRATION_RISK_VALUES,
    REFERENCE_TYPE_VALUES,
    ROLE_VALUES,
    extract_business_date,
    extract_report_references,
    naming_compliance,
    stable_report_id,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    catalog = json.loads((PROJECT_ROOT / "reports/report_catalog.json").read_text(encoding="utf-8"))
    registry = json.loads((PROJECT_ROOT / "reports/report_dependency_registry.json").read_text(encoding="utf-8"))

    assert catalog["record_count"] == len(catalog["records"])
    assert registry["record_count"] == len(registry["records"])
    assert not (CONTROL_REPORT_PATHS & {row["current_path"] for row in catalog["records"]})
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
    assert all(row["reference_type"] == "DYNAMIC_PATH_PATTERN" for row in dynamic)


def test_generators_are_byte_stable_on_repeated_runs() -> None:
    commands = [
        ["python3", "scripts/governance/build_report_dependency_registry.py"],
        ["python3", "scripts/governance/build_report_catalog.py"],
    ]
    outputs = [
        PROJECT_ROOT / "reports/report_dependency_registry.json",
        PROJECT_ROOT / "reports/report_dependency_registry.csv",
        PROJECT_ROOT / "reports/report_dependency_registry.md",
        PROJECT_ROOT / "reports/report_catalog.json",
        PROJECT_ROOT / "reports/report_catalog.csv",
        PROJECT_ROOT / "reports/report_catalog.md",
    ]
    for command in commands:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    first = {path: path.read_bytes() for path in outputs}
    for command in commands:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    second = {path: path.read_bytes() for path in outputs}
    assert first == second
