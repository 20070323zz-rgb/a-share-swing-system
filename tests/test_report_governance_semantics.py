from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.governance.authority_merge import (
    AuthorityConflictError,
    AuthorityRule,
    AuthorityTypeConflictError,
    authority_rules_for_states,
    deep_merge_authority,
)
from scripts.governance.dependency_classifier import classify_source_text
from scripts.governance.report_governance_common import (
    ImmutableSnapshotError,
    build_catalog_records,
    dynamic_producer_matches_path,
    is_control_report_path,
    write_immutable_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUSINESS_DATE = "2026-07-15"
REVISION = "v3"


def _pattern(token: str, kind: str, extension: str = "md") -> dict:
    return {
        "reference_type": "PRODUCER_WRITE",
        "consumer_or_producer": "PRODUCER",
        "static_or_dynamic": "DYNAMIC",
        "dynamic_path_pattern": f"reports/example_{token}.{extension}",
        "dynamic_pattern_kind": kind,
    }


@pytest.mark.parametrize("value", ["2026-07-15", "20260715"])
def test_date_accepts_complete_valid_calendar_dates(value: str) -> None:
    assert dynamic_producer_matches_path(_pattern("<DATE>", "DATE_TEMPLATE"), f"reports/example_{value}.md")


@pytest.mark.parametrize("value", ["2026-02-29", "2026-99-99", "2026-07", "202607"])
def test_date_rejects_invalid_or_month_only_values(value: str) -> None:
    assert not dynamic_producer_matches_path(_pattern("<DATE>", "DATE_TEMPLATE"), f"reports/example_{value}.md")


def test_month_is_separate_and_compact_requires_explicit_kind() -> None:
    dashed = _pattern("<MONTH>", "MONTH_TEMPLATE")
    compact = _pattern("<MONTH>", "MONTH_COMPACT_TEMPLATE")
    assert dynamic_producer_matches_path(dashed, "reports/example_2026-07.md")
    assert not dynamic_producer_matches_path(dashed, "reports/example_202607.md")
    assert dynamic_producer_matches_path(compact, "reports/example_202607.md")
    assert not dynamic_producer_matches_path(compact, "reports/example_2026-07.md")


def test_candidate_remains_unknown_dynamic_and_never_matches() -> None:
    source = """from pathlib import Path
def build(candidate):
    path = Path('reports') / f'candidate_{candidate}.md'
    path.write_text('x')
"""
    row = next(row for row in classify_source_text("src/example.py", source) if row["reference_type"] == "PRODUCER_WRITE")
    assert row["dynamic_path_pattern"] == "reports/candidate_<DYNAMIC>.md"
    assert row["dynamic_pattern_kind"] == "UNKNOWN_DYNAMIC"
    assert not dynamic_producer_matches_path(row, "reports/candidate_2026-07-15.md")


def test_timestamp_run_id_prefix_and_extension_do_not_cross_match() -> None:
    date = _pattern("<DATE>", "DATE_TEMPLATE")
    assert not dynamic_producer_matches_path(date, "reports/example_2026-07-15.json")
    assert not dynamic_producer_matches_path(date, "reports/prefix_example_2026-07-15.md")
    assert not dynamic_producer_matches_path(_pattern("<TIMESTAMP>", "TIMESTAMP_TEMPLATE"), "reports/example_2026-07-15.md")
    rows = _producer_rows("""from pathlib import Path
def build(timestamp, run_id):
    (Path('reports') / f'ts_{timestamp}.md').write_text('x')
    (Path('reports') / f'run_{run_id}.md').write_text('x')
""")
    assert {row["dynamic_pattern_kind"] for row in rows} == {
        "TIMESTAMP_TEMPLATE",
        "RUN_ID_TEMPLATE",
    }


def test_temporal_token_fixture_matrix() -> None:
    fixtures = json.loads(
        (PROJECT_ROOT / "tests/fixtures/report_governance/temporal_token_cases.json").read_text(
            encoding="utf-8"
        )
    )
    for item in fixtures:
        row = _pattern(item["token"], item["kind"])
        assert dynamic_producer_matches_path(
            row, f"reports/example_{item['value']}.md"
        ) is item["matches"], item["name"]


def _producer_rows(source: str) -> list[dict]:
    return [row for row in classify_source_text("src/class_fixture.py", source) if row["reference_type"] == "PRODUCER_WRITE"]


def test_method_bare_name_skips_class_body_scope() -> None:
    rows = _producer_rows("""from pathlib import Path
class ReportBuilder:
    path = Path('reports') / 'class.md'
    def build(self):
        path.write_text('x')
""")
    assert not rows


@pytest.mark.parametrize("owner", ["self", "cls", "ReportBuilder"])
def test_explicit_class_attribute_is_resolved_conservatively(owner: str) -> None:
    decorator = "    @classmethod\n" if owner == "cls" else ""
    argument = "cls" if owner == "cls" else "self"
    rows = _producer_rows(
        "from pathlib import Path\n"
        "class ReportBuilder:\n"
        "    path = Path('reports') / 'class.md'\n"
        f"{decorator}    def build({argument}):\n"
        f"        {owner}.path.write_text('x')\n"
    )
    assert any(row["normalized_target"] == "reports/class.md" for row in rows)


def test_sibling_methods_keep_same_named_locals_isolated() -> None:
    rows = _producer_rows("""from pathlib import Path
class ReportBuilder:
    def first(self, run_date):
        path = Path('reports') / f'first_{run_date}.md'
        path.write_text('x')
    def second(self, run_date):
        path = Path('reports') / f'second_{run_date}.md'
        path.write_text('x')
""")
    assert {row["dynamic_path_pattern"] for row in rows} == {
        "reports/first_<DATE>.md",
        "reports/second_<DATE>.md",
    }
    assert len({row["scope_id"] for row in rows}) == 2


def test_method_nested_closure_reads_method_binding() -> None:
    rows = _producer_rows("""from pathlib import Path
class ReportBuilder:
    def build(self, run_date):
        path = Path('reports') / f'nested_{run_date}.md'
        def inner():
            path.write_text('x')
""")
    assert len(rows) == 1
    assert rows[0]["scope_qualified_name"] == "ReportBuilder.build.inner"


def test_staticmethod_and_classmethod_do_not_share_class_bare_binding() -> None:
    rows = _producer_rows("""from pathlib import Path
class ReportBuilder:
    path = Path('reports') / 'class.md'
    @staticmethod
    def static():
        path.write_text('x')
    @classmethod
    def classed(cls):
        path.write_text('x')
""")
    assert not rows


def test_class_comprehension_has_class_syntactic_scope() -> None:
    rows = _producer_rows("""from pathlib import Path
class ReportBuilder:
    outputs = [(Path('reports') / f'comp_{run_date}.md').write_text('x') for run_date in run_dates]
""")
    assert len(rows) == 1
    assert rows[0]["scope_type"] == "COMPREHENSION"
    assert rows[0]["syntactic_parent_scope_id"]


def test_method_in_class_inside_function_resolves_outer_function_not_class() -> None:
    rows = _producer_rows("""from pathlib import Path
def outer(run_date):
    path = Path('reports') / f'outer_{run_date}.md'
    class ReportBuilder:
        path = Path('reports') / 'class.md'
        def build(self):
            path.write_text('x')
""")
    assert len(rows) == 1
    assert rows[0]["dynamic_path_pattern"] == "reports/outer_<DATE>.md"


def test_module_name_wins_over_same_named_class_attribute_for_method_bare_name() -> None:
    rows = _producer_rows("""from pathlib import Path
path = Path('reports') / 'module.md'
class ReportBuilder:
    path = Path('reports') / 'class.md'
    def build(self):
        path.write_text('x')
""")
    assert len(rows) == 1
    assert rows[0]["normalized_target"] == "reports/module.md"


def test_class_method_scope_fixture_matrix_and_identity_stability() -> None:
    fixtures = json.loads(
        (PROJECT_ROOT / "tests/fixtures/report_governance/class_method_scope_cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(fixtures) == 10
    for item in fixtures:
        rows = _producer_rows(item["source"])
        repeated = _producer_rows(item["source"])
        matches = [row for row in rows if row["normalized_target"] == item["target"]]
        if not item["expect_producer"]:
            assert not matches, item["name"]
            continue
        assert matches, item["name"]
        repeated_row = next(row for row in repeated if row["reference_id"] == matches[0]["reference_id"])
        assert matches[0]["scope_id"] == repeated_row["scope_id"], item["name"]
        assert matches[0]["binding_id"] == repeated_row["binding_id"], item["name"]


def test_immutable_snapshot_writer_is_idempotent_and_fail_fast(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.md"
    write_immutable_text(path, "same\n")
    original_hash = path.read_bytes()
    write_immutable_text(path, "same\n")
    assert path.read_bytes() == original_hash
    with pytest.raises(ImmutableSnapshotError):
        write_immutable_text(path, "different\n")


def test_revisioned_control_artifacts_are_type_recognized() -> None:
    assert is_control_report_path("reports/report_catalog_v2_2026-07-15.json")
    assert is_control_report_path("reports/reports_governance_phase_a_summary_v2_2026-07-15.md")
    assert is_control_report_path("reports/report_governance_evidence_registry_v1_2026-07-15.json")
    assert not is_control_report_path("reports/unrelated_v2_2026-07-15.md")


def test_authority_merge_preserves_nested_and_unknown_fields() -> None:
    reports = {"reports_governance_phase_a_status": "REMEDIATED", "unknown": {"keep": 1}}
    availability = {
        "reports_governance_phase_a_status": "OLD",
        "phase_deliverables": {"tushare_etf_daily_availability_timing_audit": ["a"]},
        "unknown": {"new": 2},
    }
    rules = authority_rules_for_states(reports, availability)
    merged = deep_merge_authority(
        reports,
        availability,
        base_owner="reports_governance",
        incoming_owner="availability_audit",
        rules=rules + (AuthorityRule(("unknown", "keep"), "reports_governance"),),
    )
    assert merged["reports_governance_phase_a_status"] == "REMEDIATED"
    assert merged["phase_deliverables"]["tushare_etf_daily_availability_timing_audit"] == ["a"]
    assert merged["unknown"] == {"keep": 1, "new": 2}


def test_authority_merge_availability_update_keeps_reports_fields() -> None:
    base = {"reports_governance_phase_a_status": "REMEDIATED", "etf_daily_availability_timing_audit_status": "QUEUED"}
    incoming = {"etf_daily_availability_timing_audit_status": "ACTIVE_COLLECTING"}
    merged = deep_merge_authority(
        base,
        incoming,
        base_owner="reports_governance",
        incoming_owner="availability_audit",
        rules=authority_rules_for_states(base, incoming),
    )
    assert merged == {
        "reports_governance_phase_a_status": "REMEDIATED",
        "etf_daily_availability_timing_audit_status": "ACTIVE_COLLECTING",
    }


def test_authority_type_conflict_fails_fast() -> None:
    with pytest.raises(AuthorityTypeConflictError):
        deep_merge_authority(
            {"nested": {}},
            {"nested": []},
            base_owner="reports_governance",
            incoming_owner="availability_audit",
            rules=(AuthorityRule(("nested",), "availability_audit"),),
        )


def test_unowned_authority_conflict_fails_fast() -> None:
    with pytest.raises(AuthorityConflictError):
        deep_merge_authority(
            {"shared": "a"},
            {"shared": "b"},
            base_owner="reports_governance",
            incoming_owner="availability_audit",
            rules=(),
        )


def test_revisioned_catalog_contract_after_generation() -> None:
    catalog_path = PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.json"
    if not catalog_path.exists():
        pytest.skip("revisioned snapshot not generated yet")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    dynamic = [
        row
        for row in catalog["records"]
        if row["matched_dynamic_producer_count"] > 0
    ]
    assert len(dynamic) == 12
    assert all("ACTIVE_DYNAMIC_PRODUCER" in row["archive_block_reasons"] for row in dynamic)
    assert all(row["archive_block_evidence"]["ACTIVE_DYNAMIC_PRODUCER"] for row in dynamic)
    assert catalog["summary"]["archive_candidate_count"] == 0
    assert catalog["summary"]["safe_to_delete_after_authorization_count"] == 0


def test_removing_dynamic_producer_evidence_recomputes_block_reason() -> None:
    catalog_path = PROJECT_ROOT / f"reports/report_catalog_{REVISION}_{BUSINESS_DATE}.json"
    registry_path = PROJECT_ROOT / f"reports/report_dependency_registry_{REVISION}_{BUSINESS_DATE}.json"
    if not catalog_path.exists() or not registry_path.exists():
        pytest.skip("revisioned snapshot not generated yet")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    target = next(
        row for row in catalog["records"] if row["matched_dynamic_producer_count"] == 1
    )
    removed_id = target["matched_dynamic_producer_ids"][0]
    reduced_rows = [row for row in registry["records"] if row["reference_id"] != removed_id]
    rebuilt = {row["current_path"]: row for row in build_catalog_records(PROJECT_ROOT, reduced_rows)}
    assert "ACTIVE_DYNAMIC_PRODUCER" not in rebuilt[target["current_path"]]["archive_block_reasons"]


def test_phase_b_contract_is_repository_complete() -> None:
    text = "\n".join(
        (PROJECT_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/report_migration_plan.md",
            "docs/report_path_registry_design.md",
            "docs/operational_playbook.md",
            "docs/project_batch_standard.md",
            "PROJECT_INDEX.md",
        )
    )
    required = (
        "MIGRATION_COMPLETE",
        "MIGRATION_PARTIAL",
        "deprecated-path",
        "consumer-completeness",
        "App补齐数据按钮",
        "Backend API",
        "Dashboard consumer",
        "Work/Codex",
        "compatibility period",
        "DATA_NOT_READY",
    )
    assert all(token in text for token in required)
