from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import urllib.error

import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.client import TushareMinimalClient  # noqa: E402
import data_sources.tushare.probe as probe_module  # noqa: E402
from data_sources.tushare.pit_contract import build_pit_records  # noqa: E402
from data_sources.tushare.probe import (  # noqa: E402
    limit_sample_frame,
    load_config,
    resolve_run_directory,
    run_probe,
    validate_evidence_manifest,
)
from data_sources.tushare.validators import normalize_frame, validate_interface_frame  # noqa: E402
from data_sources.tushare.schemas import INTERFACE_SCHEMAS  # noqa: E402


FIXTURE = json.loads((ROOT / "tests/fixtures/tushare_minimal_proof/mock_api_responses.json").read_text(encoding="utf-8"))


def response(interface: str, *, items=None, fields=None, code=0, msg="") -> bytes:
    table = FIXTURE.get(interface, {"fields": [], "items": []})
    payload = {"code": code, "msg": msg, "data": {"fields": fields or table["fields"], "items": table["items"] if items is None else items}}
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def make_project(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    for path in ("configs/universe_versions", "src/exposure", "data/etf_daily", "reports"):
        (root / path).mkdir(parents=True, exist_ok=True)
    (root / "src/exposure/market_exposure_vector.py").write_text(
        "BENCHMARK_BASKET=(\n"
        "{'benchmark_code':'510300','benchmark_family':'core_market'},\n"
        "{'benchmark_code':'159915','benchmark_family':'growth'},\n"
        "{'benchmark_code':'588000','benchmark_family':'technology'},\n)\n", encoding="utf-8"
    )
    registry = {"records": [{"etf_code": code} for code in ("510300", "159915", "588000")]}
    (root / "configs/universe_versions/universe_v2_registry.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")
    for market, code in (("sh", "510300"), ("sz", "159915"), ("sh", "588000")):
        pd.DataFrame({"date": pd.date_range("2026-01-01", "2026-07-10", freq="B").strftime("%Y-%m-%d")}).to_csv(root / f"data/etf_daily/{market}_{code}.csv", index=False)
    config = yaml.safe_load((ROOT / "configs/tushare_minimal_proof.yaml").read_text(encoding="utf-8"))
    config["runtime"].update({"request_interval_seconds": 0, "max_network_retries": 0})
    config_path = root / "configs/tushare_minimal_proof.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    pd.DataFrame(
        [
            {"run_id": "real-20260713-proof-a", "evidence_mode": "real", "real_call_count": 17},
            {"run_id": "real-20260713-proof-b", "evidence_mode": "real", "real_call_count": 17},
            {"run_id": "real-20260713-proof-c", "evidence_mode": "real", "real_call_count": 17},
        ]
    ).to_csv(root / "reports/tushare_real_run_attestations.csv", index=False)
    return root, config_path


def test_full_mock_probe_is_run_scoped_and_bounded(tmp_path):
    root, config = make_project(tmp_path)
    manifest = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-run-a")
    assert manifest["status"] == "MOCK_VALIDATION_PASS"
    assert manifest["mock_call_count"] <= 30
    assert manifest["real_api_call_count"] == 0
    assert len(manifest["selected_etfs"]) == 3
    assert (root / "data/staging/tushare_minimal_proof/mock/mock-20260713-run-a/raw").is_dir()
    assert not (root / "reports/tushare_interface_probe_matrix.csv").exists()


def test_second_run_does_not_overwrite_first(tmp_path):
    root, config = make_project(tmp_path)
    first_dir = root / "data/staging/tushare_minimal_proof/mock/mock-20260713-first"
    run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-first")
    first_files = sorted(str(path.relative_to(root)) for path in first_dir.rglob("*"))
    run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-second")
    assert first_files == sorted(str(path.relative_to(root)) for path in first_dir.rglob("*"))


def test_permission_error_is_sanitized_and_classified():
    client = TushareMinimalClient(project_root=ROOT, max_requests=2, token="secret", request_interval_seconds=0, max_network_retries=0, transport=lambda p, t: response("shibor", code=40203, msg="权限不足 token=secret"))
    result = client.request("shibor", {}, "date")
    assert result.response_status == "PERMISSION_BLOCKED"
    assert "secret" not in result.error_message_sanitized


def test_network_failure_is_classified():
    client = TushareMinimalClient(project_root=ROOT, max_requests=2, token="x", request_interval_seconds=0, max_network_retries=0, transport=lambda p, t: (_ for _ in ()).throw(urllib.error.URLError("offline")))
    assert client.request("shibor", {}, "date").response_status == "NETWORK_FAILED"


def test_empty_and_missing_schema_are_distinct():
    empty = validate_interface_frame("index_daily", pd.DataFrame(columns=FIXTURE["index_daily"]["fields"]))
    expected_empty = validate_interface_frame("fund_portfolio", pd.DataFrame(columns=FIXTURE["fund_portfolio"]["fields"]))
    missing = validate_interface_frame("index_daily", pd.DataFrame({"ts_code": ["000300.SH"]}))
    assert empty.status == "EMPTY_UNEXPECTED"
    assert expected_empty.status == "EMPTY_EXPECTED"
    assert missing.status == "SCHEMA_MISMATCH"


def test_duplicate_key_and_unit_anomaly_fail_validation():
    duplicate = pd.DataFrame(FIXTURE["index_weight"]["items"] * 2, columns=FIXTURE["index_weight"]["fields"])
    duplicate.loc[0, "weight"] = 101
    result = validate_interface_frame("index_weight", duplicate)
    assert result.status == "VALIDATION_FAILED"
    assert result.duplicate_keys > 0


def test_fund_portfolio_versions_retained_and_pit_resolved():
    frame = pd.DataFrame(FIXTURE["fund_portfolio"]["items"], columns=FIXTURE["fund_portfolio"]["fields"])
    result = validate_interface_frame("fund_portfolio", frame)
    assert len(result.normalized) == 2
    assert any("multiple announcement versions" in item for item in result.validation_warnings)
    pit = build_pit_records("fund_portfolio", result.normalized, retrieved_at="2026-07-13T10:00:00+08:00", query_hash="q", raw_payload_hash="r", local_trading_dates=["2026-07-10"], evidence_mode="mock")
    assert set(pit["pit_status"]) == {"PIT_RESOLVED"}
    assert (pit["available_date"] == pit["announcement_date"]).all()


def test_taxonomy_without_publication_time_is_pit_unresolved():
    frame = pd.DataFrame(FIXTURE["index_classify"]["items"], columns=FIXTURE["index_classify"]["fields"])
    pit = build_pit_records("index_classify", frame, retrieved_at="2026-07-13T10:00:00+08:00", query_hash="q", raw_payload_hash="r", local_trading_dates=[], evidence_mode="mock")
    assert set(pit["pit_status"]) == {"PIT_UNRESOLVED"}


def test_normalization_is_deterministic():
    frame = pd.DataFrame(FIXTURE["daily_basic"]["items"], columns=FIXTURE["daily_basic"]["fields"])
    second_row = frame.iloc[0].copy()
    second_row["ts_code"] = "000001.SZ"
    frame = pd.concat([frame, second_row.to_frame().T], ignore_index=True)
    first = normalize_frame(frame.sample(frac=1, random_state=1), INTERFACE_SCHEMAS["daily_basic"]).to_csv(index=False, lineterminator="\n")
    second = normalize_frame(frame.sample(frac=1, random_state=2), INTERFACE_SCHEMAS["daily_basic"]).to_csv(index=False, lineterminator="\n")
    assert hashlib.sha256(first.encode()).hexdigest() == hashlib.sha256(second.encode()).hexdigest()


def test_request_budget_counts_retries():
    client = TushareMinimalClient(project_root=ROOT, max_requests=1, token="x", request_interval_seconds=0, max_network_retries=1, transport=lambda p, t: (_ for _ in ()).throw(urllib.error.URLError("offline")))
    with pytest.raises(RuntimeError, match="budget exceeded"):
        client.request("shibor", {}, "date")


def test_evidence_mode_is_required_and_invalid_values_fail_fast(tmp_path):
    root, config = make_project(tmp_path)
    with pytest.raises(TypeError, match="evidence_mode"):
        run_probe(root, config, mock_responses=FIXTURE)
    with pytest.raises(ValueError, match="evidence_mode"):
        run_probe(root, config, evidence_mode="fixture", mock_responses=FIXTURE)


def test_mock_mode_rejects_real_run_id_before_creating_output(tmp_path):
    root, config = make_project(tmp_path)
    with pytest.raises(ValueError, match=r"mock-\*"):
        run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="real-20260713-invalid")
    assert not (root / "data/staging").exists()


def test_real_mode_rejects_mock_run_id_before_token_lookup(tmp_path, monkeypatch):
    root, config = make_project(tmp_path)
    monkeypatch.setattr(probe_module, "load_token", lambda _: (_ for _ in ()).throw(AssertionError("token lookup must not run")))
    with pytest.raises(ValueError, match=r"real-\*"):
        run_probe(root, config, evidence_mode="real", run_id="mock-20260713-invalid")


def test_mock_mode_never_reads_token_provider(tmp_path, monkeypatch):
    root, config = make_project(tmp_path)
    monkeypatch.setattr(probe_module, "load_token", lambda _: (_ for _ in ()).throw(AssertionError("token provider accessed")))
    manifest = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-no-token")
    assert manifest["status"] == "MOCK_VALIDATION_PASS"
    assert manifest["token_configured"] is False


def test_mock_mode_never_instantiates_real_client(tmp_path, monkeypatch):
    root, config = make_project(tmp_path)
    monkeypatch.setattr(probe_module, "TushareMinimalClient", lambda **_: (_ for _ in ()).throw(AssertionError("real client created")))
    manifest = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-no-real-client")
    assert manifest["mock_call_count"] > 0


def test_mock_manifest_has_zero_real_calls_and_no_real_status(tmp_path):
    root, config = make_project(tmp_path)
    manifest = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-counts")
    assert manifest["real_api_call_count"] == 0
    assert manifest["per_run_real_call_count"] == 0
    assert manifest["mock_call_count"] == manifest["total_call_count"]
    assert manifest["status"] in {"MOCK_VALIDATION_PASS", "MOCK_VALIDATION_FAILED"}
    assert manifest["status"] != "REAL_PROOF_COMPLETE"


def test_mock_report_cannot_claim_real_or_permission_evidence(tmp_path):
    root, config = make_project(tmp_path)
    run_id = "mock-20260713-report"
    run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id=run_id)
    report = (root / f"data/staging/tushare_minimal_proof/mock/{run_id}/report_evidence/tushare_minimal_staging_proof.md").read_text(encoding="utf-8")
    assert "Real API evidence" not in report
    assert "Permission confirmed" not in report
    assert "ACCESS_PASS" not in report
    run_dir = root / f"data/staging/tushare_minimal_proof/mock/{run_id}"
    for path in run_dir.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".md", ".csv"}:
            assert "ACCESS_PASS" not in path.read_text(encoding="utf-8")


def test_real_and_mock_output_directories_are_isolated(tmp_path):
    root, config_path = make_project(tmp_path)
    config = load_config(config_path)
    real_dir = resolve_run_directory(root, config, "real", "real-20260713-isolated")
    mock_dir = resolve_run_directory(root, config, "mock", "mock-20260713-isolated")
    assert real_dir != mock_dir
    assert real_dir.relative_to(root).parts[-2] == "real"
    assert mock_dir.relative_to(root).parts[-2] == "mock"


def test_real_and_mock_manifest_schema_is_mode_specific(tmp_path):
    committed_real = json.loads((ROOT / "reports/tushare_minimal_proof_run_manifest.json").read_text(encoding="utf-8"))
    validate_evidence_manifest(committed_real)
    root, config = make_project(tmp_path)
    mock_manifest = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-schema")
    validate_evidence_manifest(mock_manifest)
    assert committed_real["evidence_mode"] == "real"
    assert mock_manifest["evidence_mode"] == "mock"


def test_aggregate_real_budget_comes_only_from_real_attestations(tmp_path):
    root, config = make_project(tmp_path)
    first = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-budget-a")
    second = run_probe(root, config, evidence_mode="mock", mock_responses=FIXTURE, run_id="mock-20260713-budget-b")
    assert first["batch_aggregate_real_call_count"] == 51
    assert second["batch_aggregate_real_call_count"] == 51
    assert second["budget_status"] == "NOT_APPLICABLE_MOCK"


def test_fund_portfolio_primary_key_contains_announcement_date():
    assert "ann_date" in INTERFACE_SCHEMAS["fund_portfolio"].primary_key


def test_same_fund_period_with_multiple_announcements_is_not_overwritten():
    frame = pd.DataFrame(FIXTURE["fund_portfolio"]["items"], columns=FIXTURE["fund_portfolio"]["fields"])
    result = validate_interface_frame("fund_portfolio", frame)
    assert len(result.normalized) == 2
    assert result.duplicate_keys == 0
    assert result.normalized["ann_date"].nunique() == 2


def _pit(interface: str, frame: pd.DataFrame, trading_dates: list[str]) -> pd.DataFrame:
    return build_pit_records(
        interface,
        frame,
        retrieved_at="2026-07-13T10:00:00+08:00",
        query_hash="query-hash",
        raw_payload_hash="raw-hash",
        local_trading_dates=trading_dates,
        evidence_mode="mock",
    )


def test_daily_basic_defaults_to_next_trading_day():
    frame = pd.DataFrame(FIXTURE["daily_basic"]["items"], columns=FIXTURE["daily_basic"]["fields"])
    pit = _pit("daily_basic", frame, ["2026-07-10", "2026-07-13"])
    assert pit.iloc[0]["available_date"] == "2026-07-13"
    assert pit.iloc[0]["pit_status"] == "PIT_CONSERVATIVE"


def test_index_daily_defaults_to_next_trading_day():
    frame = pd.DataFrame(FIXTURE["index_daily"]["items"], columns=FIXTURE["index_daily"]["fields"])
    pit = _pit("index_daily", frame, ["2026-07-10", "2026-07-13"])
    assert pit.iloc[0]["available_date"] == "2026-07-13"
    assert pit.iloc[0]["pit_status"] == "PIT_CONSERVATIVE"


def test_latest_daily_date_without_next_trading_day_is_partial():
    frame = pd.DataFrame(FIXTURE["daily_basic"]["items"], columns=FIXTURE["daily_basic"]["fields"])
    pit = _pit("daily_basic", frame, ["2026-07-10"])
    assert pit.iloc[0]["available_date"] == ""
    assert pit.iloc[0]["pit_status"] == "PIT_PARTIAL"


def test_index_weight_remains_pit_partial():
    frame = pd.DataFrame(FIXTURE["index_weight"]["items"], columns=FIXTURE["index_weight"]["fields"])
    assert set(_pit("index_weight", frame, ["2026-07-10"])["pit_status"]) == {"PIT_PARTIAL"}


def test_index_membership_and_classification_never_upgrade_to_resolved():
    member = pd.DataFrame(FIXTURE["index_member_all"]["items"], columns=FIXTURE["index_member_all"]["fields"])
    classify = pd.DataFrame(FIXTURE["index_classify"]["items"], columns=FIXTURE["index_classify"]["fields"])
    assert "PIT_RESOLVED" not in set(_pit("index_member_all", member, ["2026-07-10"])["pit_status"])
    assert "PIT_RESOLVED" not in set(_pit("index_classify", classify, ["2026-07-10"])["pit_status"])


def test_shibor_distinguishes_official_release_project_lag_and_retrieval():
    frame = pd.DataFrame(FIXTURE["shibor"]["items"], columns=FIXTURE["shibor"]["fields"])
    row = _pit("shibor", frame, ["2026-07-10"]).iloc[0]
    assert row["official_release_time"] == "11:00 Asia/Shanghai"
    assert row["project_conservative_available_time"] == "12:00 Asia/Shanghai"
    assert row["conservative_lag_minutes"] == 60
    assert row["pit_basis"] == "OFFICIAL_11AM_PLUS_PROJECT_LAG"
    assert row["available_at"] == "2026-07-10T12:00:00+08:00"
    assert row["retrieved_at"] == "2026-07-13T10:00:00+08:00"


def test_index_weight_reduction_keeps_latest_two_dates_and_counts():
    config = load_config(ROOT / "configs/tushare_minimal_proof.yaml")
    frame = pd.DataFrame(
        [
            {"index_code": "000300.SH", "con_code": code, "trade_date": date, "weight": 50.0}
            for date in ("20260430", "20260529", "20260630")
            for code in ("600000.SH", "600519.SH")
        ]
    )
    limited, evidence = limit_sample_frame("index_weight", frame, config)
    assert set(pd.to_datetime(limited["trade_date"]).dt.strftime("%Y-%m-%d")) == {"2026-05-29", "2026-06-30"}
    assert evidence["raw_count"] == 6
    assert evidence["proof_count"] == 4
    assert evidence["excluded_count"] == 2
    assert evidence["excluded_trade_dates"] == ["2026-04-30"]
    assert evidence["reduction_reason"] == "PROOF_SAMPLE_DATE_WINDOW_REDUCTION"
    assert limited["weight"].notna().all()
    assert len(limited) == len(frame[frame["trade_date"].isin({"20260529", "20260630"})])


def test_formal_staging_architecture_remains_not_started():
    status = json.loads((ROOT / "docs/current_phase_status.json").read_text(encoding="utf-8"))
    assert status["tushare_formal_staging_architecture_status"] == "NOT_STARTED"
    assert status["tushare_primary_upstream_migration_status"] == "NOT_STARTED"
    assert status["etf_daily_availability_timing_audit_status"] == "NOT_STARTED"
