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
from data_sources.tushare.pit_contract import build_pit_records  # noqa: E402
from data_sources.tushare.probe import run_probe  # noqa: E402
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
    return root, config_path


class MockFactory:
    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.client = None

    def __call__(self, **kwargs):
        def transport(payload, timeout):
            interface = payload["api_name"]
            override = self.overrides.get(interface)
            if isinstance(override, Exception):
                raise override
            if override is not None:
                return override
            return response(interface)

        self.client = TushareMinimalClient(token="mock-token", transport=transport, **kwargs)
        return self.client


def test_full_mock_probe_is_run_scoped_and_bounded(tmp_path):
    root, config = make_project(tmp_path)
    factory = MockFactory()
    manifest = run_probe(root, config, client_factory=factory, run_id="mock-run-a")
    assert manifest["status"] == "COMPLETE"
    assert manifest["api_request_count"] <= 30
    assert len(manifest["selected_etfs"]) == 3
    assert (root / "data/staging/tushare_minimal_proof/mock-run-a/raw").is_dir()
    assert (root / "reports/tushare_interface_probe_matrix.csv").is_file()


def test_second_run_does_not_overwrite_first(tmp_path):
    root, config = make_project(tmp_path)
    factory = MockFactory()
    run_probe(root, config, client_factory=factory, run_id="first")
    first_files = sorted(str(path.relative_to(root)) for path in (root / "data/staging/tushare_minimal_proof/first").rglob("*"))
    run_probe(root, config, client_factory=factory, run_id="second")
    assert first_files == sorted(str(path.relative_to(root)) for path in (root / "data/staging/tushare_minimal_proof/first").rglob("*"))


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
    pit = build_pit_records("fund_portfolio", result.normalized, retrieved_at="2026-07-13T10:00:00+08:00", query_hash="q", raw_payload_hash="r", local_trading_dates=["2026-07-10"])
    assert set(pit["pit_status"]) == {"PIT_RESOLVED"}
    assert (pit["available_date"] == pit["announcement_date"]).all()


def test_taxonomy_without_publication_time_is_pit_unresolved():
    frame = pd.DataFrame(FIXTURE["index_classify"]["items"], columns=FIXTURE["index_classify"]["fields"])
    pit = build_pit_records("index_classify", frame, retrieved_at="2026-07-13T10:00:00+08:00", query_hash="q", raw_payload_hash="r", local_trading_dates=[])
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
