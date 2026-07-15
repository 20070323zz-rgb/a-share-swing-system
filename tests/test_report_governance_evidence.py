from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.governance.evidence_registry import validate_evidence_integrity
from scripts.governance.report_governance_common import (
    classify_location_status,
    determine_migration_eligibility,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUSINESS_DATE = "2026-07-15"
CATALOG_REVISION = "v3"
DEPENDENCY_REVISION = "v3"
EVIDENCE_REVISION = "v1"


def _payloads() -> tuple[dict, dict, dict]:
    paths = (
        PROJECT_ROOT / f"reports/report_catalog_{CATALOG_REVISION}_{BUSINESS_DATE}.json",
        PROJECT_ROOT
        / f"reports/report_governance_evidence_registry_{EVIDENCE_REVISION}_{BUSINESS_DATE}.json",
        PROJECT_ROOT
        / f"reports/report_dependency_registry_{DEPENDENCY_REVISION}_{BUSINESS_DATE}.json",
    )
    if not all(path.exists() for path in paths):
        pytest.skip("v3/v1 governance snapshots not generated yet")
    return tuple(json.loads(path.read_text(encoding="utf-8")) for path in paths)  # type: ignore[return-value]


def _migration(**overrides: object) -> str:
    values: dict[str, object] = {
        "location_status": "ACTIVE_ROOT",
        "runtime_locked": False,
        "current_alias": False,
        "active_generator": False,
        "active_consumer": False,
        "dependency_safety": "NO_ACTIVE_DEPENDENCY",
        "role": "DATED_DAILY",
        "retention_status": "ROLLING_WINDOW",
        "naming_status": "COMPLIANT_DATED",
    }
    values.update(overrides)
    return determine_migration_eligibility(**values)  # type: ignore[arg-type]


def test_archive_location_classification_is_root_aware_and_configurable() -> None:
    assert classify_location_status("reports/archive/a.md") == "ALREADY_ARCHIVED"
    assert classify_location_status("reports/archive/sub/a.md") == "ALREADY_ARCHIVED"
    assert classify_location_status("reports/archive_notes.md") == "ACTIVE_ROOT"
    assert classify_location_status("reports/active/a.md") == "ACTIVE_SUBDIRECTORY"
    assert (
        classify_location_status(
            "reports/legacy/a.md", archive_roots=("reports/legacy/",)
        )
        == "ALREADY_ARCHIVED"
    )
    assert (
        classify_location_status(
            "reports/archive/a.md", archive_roots=("reports/legacy/",)
        )
        == "ACTIVE_SUBDIRECTORY"
    )


def test_migration_precedence_and_safe_fixtures() -> None:
    assert _migration(location_status="ALREADY_ARCHIVED") == "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
    assert _migration(location_status="ALREADY_ARCHIVED", naming_status="NEEDS_DATE_NORMALIZATION") == "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
    assert _migration(location_status="GOVERNANCE_CONTROL_LOCATION") == "MIGRATION_NOT_APPLICABLE_CONTROL_ARTIFACT"
    assert _migration() == "SAFE_TO_MIGRATE"
    assert _migration(naming_status="NEEDS_DATE_NORMALIZATION") == "SAFE_TO_MIGRATE_RENAME_REQUIRED"
    assert _migration(active_generator=True) == "MIGRATION_BLOCKED_ACTIVE_DEPENDENCY"
    assert _migration(runtime_locked=True) == "MIGRATION_BLOCKED_RUNTIME"
    assert _migration(role="UNKNOWN") == "MIGRATION_BLOCKED_UNKNOWN"
    assert _migration(retention_status="PERMANENT") == "MIGRATION_BLOCKED_RETENTION"


def test_evidence_fixture_matrix_is_complete() -> None:
    fixtures = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/report_governance/evidence_integrity_cases.json"
        ).read_text(encoding="utf-8")
    )
    assert len(fixtures) == 10
    assert {item["kind"] for item in fixtures} == {
        "DEPENDENCY",
        "REPORT_ROLE",
        "RETENTION",
        "STATE_AUTHORITY",
        "UNKNOWN_ROLE",
        "LOCATION",
        "UNRESOLVED_ID",
        "DUPLICATE_ID",
        "BAD_REPORT_ID",
        "MISSING_RULE_VERSION",
    }


def test_committed_evidence_registry_resolves_every_catalog_reference() -> None:
    catalog, evidence, dependency = _payloads()
    result = validate_evidence_integrity(PROJECT_ROOT, catalog, evidence, dependency)
    assert result["valid"], result["errors"]
    assert result["unresolved_evidence_ids"] == 0
    assert result["duplicate_evidence_ids"] == 0
    assert result["missing_report_ids"] == 0
    assert result["missing_rule_versions"] == 0
    assert result["orphan_evidence_ids"] == 0
    assert not any(
        evidence_id.startswith("rule_")
        for report in catalog["records"]
        for evidence_id in report["archive_block_evidence_ids"]
    )


def test_stale_audits_and_dynamic_producers_have_traceable_evidence() -> None:
    catalog, evidence, _ = _payloads()
    evidence_ids = {row["evidence_id"] for row in evidence["records"]}
    audit_rows = [
        row
        for row in catalog["records"]
        if "ACTIVE_AUDIT_ARTIFACT" in row["archive_block_reasons"]
    ]
    assert len(audit_rows) >= 2
    for row in audit_rows:
        ids = row["archive_block_evidence"]["ACTIVE_AUDIT_ARTIFACT"]
        assert ids and set(ids) <= evidence_ids
    dynamic = [row for row in catalog["records"] if row["matched_dynamic_producer_count"]]
    assert len(dynamic) == 12
    for row in dynamic:
        ids = row["archive_block_evidence"]["ACTIVE_DYNAMIC_PRODUCER"]
        assert ids and set(ids) <= evidence_ids
        assert all(
            next(item for item in evidence["records"] if item["evidence_id"] == evidence_id)[
                "evidence_namespace"
            ]
            == "DEPENDENCY"
            for evidence_id in ids
        )


def test_integrity_validator_rejects_required_failure_fixtures() -> None:
    catalog, evidence, dependency = _payloads()

    unresolved_catalog = copy.deepcopy(catalog)
    target = unresolved_catalog["records"][0]
    target["archive_block_evidence_ids"].append("evidence_missing_fixture")
    target["archive_block_evidence"].setdefault("NO_ACTIVE_DEPENDENCY", []).append(
        "evidence_missing_fixture"
    )
    assert not validate_evidence_integrity(
        PROJECT_ROOT, unresolved_catalog, evidence, dependency
    )["valid"]

    duplicate_registry = copy.deepcopy(evidence)
    duplicate_registry["records"].append(copy.deepcopy(duplicate_registry["records"][0]))
    assert validate_evidence_integrity(
        PROJECT_ROOT, catalog, duplicate_registry, dependency
    )["duplicate_evidence_ids"] == 1

    bad_report_registry = copy.deepcopy(evidence)
    bad_report_registry["records"][0]["report_id"] = "report_missing_fixture"
    assert validate_evidence_integrity(
        PROJECT_ROOT, catalog, bad_report_registry, dependency
    )["missing_report_ids"] == 1

    missing_version_registry = copy.deepcopy(evidence)
    missing_version_registry["records"][0]["rule_version"] = ""
    assert validate_evidence_integrity(
        PROJECT_ROOT, catalog, missing_version_registry, dependency
    )["missing_rule_versions"] == 1


def test_already_archived_records_are_not_phase_b_or_deletion_candidates() -> None:
    catalog, _, _ = _payloads()
    archived = [
        row for row in catalog["records"] if row["location_status"] == "ALREADY_ARCHIVED"
    ]
    assert archived
    assert all(
        row["migration_eligibility"] == "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
        for row in archived
    )
    assert all(row["deletion_eligibility"] == "NOT_DELETION_CANDIDATE" for row in archived)
    assert not ({row["current_path"] for row in archived} & set(catalog["phase_b_candidate_paths"]))


def test_original_safe_candidates_are_reclassified_by_real_location() -> None:
    catalog, _, _ = _payloads()
    previous = json.loads(
        (PROJECT_ROOT / f"reports/report_catalog_v2_{BUSINESS_DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    previous_safe = {
        row["current_path"]
        for row in previous["records"]
        if row["migration_eligibility"] == "SAFE_TO_MIGRATE"
    }
    archived_previous_safe = {
        path for path in previous_safe if path.startswith("reports/archive/")
    }
    assert len(previous_safe) == 50
    assert len(archived_previous_safe) == 45
    current = {row["current_path"]: row for row in catalog["records"]}
    assert all(
        current[path]["migration_eligibility"]
        == "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
        for path in archived_previous_safe
    )
    for row in catalog["records"]:
        if row["active_generator"] or row["runtime_locked"] or row["role"] == "UNKNOWN":
            assert row["migration_eligibility"] not in {
                "SAFE_TO_MIGRATE",
                "SAFE_TO_MIGRATE_RENAME_REQUIRED",
            }
