from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys

import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.availability_models import AuditPaths, SNAPSHOT_FIELDS, UniverseRecord  # noqa: E402
from data_sources.tushare.availability_summary import build_availability_reports  # noqa: E402
from data_sources.tushare.availability_validators import (  # noqa: E402
    build_universe_mapping,
    compare_snapshots,
    normalize_vendor_frame,
    snapshot_content_hash,
    validate_snapshot,
)
from data_sources.tushare.client import TushareMinimalClient  # noqa: E402
from data_sources.tushare.etf_availability_probe import (  # noqa: E402
    fetch_baostock_daily,
    record_missed_probe,
    run_availability_probe,
)


FIXTURE = json.loads((ROOT / "tests/fixtures/tushare_etf_availability/mock_fund_daily.json").read_text(encoding="utf-8"))


def make_project(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    for path in ("data/etf_daily", "data/staging", "reports"):
        (root / path).mkdir(parents=True, exist_ok=True)
    symbols = [("sh", "510300", "trade_pool"), ("sz", "159915", "observe_pool"), ("sh", "588000", "observe_pool")]
    for market, code, _ in symbols:
        pd.DataFrame({"date": ["2026-07-10"]}).to_csv(root / f"data/etf_daily/{market}_{code}.csv", index=False)
    pd.DataFrame([{"symbol": code, "pool": role} for _, code, role in symbols]).to_csv(root / "data/etf_classification.csv", index=False)
    config = yaml.safe_load((ROOT / "configs/tushare_etf_availability_audit.yaml").read_text(encoding="utf-8"))
    config["universe"]["expected_count"] = 3
    config["schedule"]["tushare_times"] = ["15:05", "15:30", "16:00"]
    config["schedule"]["baostock_times"] = ["15:30", "16:00"]
    paths = AuditPaths.from_config(root, config)
    paths.calendar_cache.parent.mkdir(parents=True, exist_ok=True)
    paths.calendar_cache.write_text(json.dumps({"rows": [{"cal_date": "2026-07-14", "is_open": 1}]}), encoding="utf-8")
    return root, config


def universe() -> list[UniverseRecord]:
    return [
        UniverseRecord("510300", "510300.SH", "SH", "trade_pool", "data/etf_daily/sh_510300.csv"),
        UniverseRecord("159915", "159915.SZ", "SZ", "observe_pool", "data/etf_daily/sz_159915.csv"),
        UniverseRecord("588000", "588000.SH", "SH", "observe_pool", "data/etf_daily/sh_588000.csv"),
    ]


def frame(items=None) -> pd.DataFrame:
    return pd.DataFrame(FIXTURE["items"] if items is None else items, columns=FIXTURE["fields"])


def transport(items=None, *, code=0, msg=""):
    def send(_payload, _timeout):
        return json.dumps({"code": code, "msg": msg, "data": {"fields": FIXTURE["fields"], "items": FIXTURE["items"] if items is None else items}}).encode()
    return send


def factory(items=None, *, code=0, msg="", network_error: Exception | None = None):
    def create(**kwargs):
        send = transport(items, code=code, msg=msg)
        if network_error is not None:
            send = lambda _payload, _timeout: (_ for _ in ()).throw(network_error)
        return TushareMinimalClient(
            project_root=kwargs["project_root"], max_requests=kwargs["max_requests"],
            token="fixture-token", request_interval_seconds=0, max_network_retries=0, transport=send,
        )
    return create


def test_repository_universe_maps_all_183_etfs():
    config = yaml.safe_load((ROOT / "configs/tushare_etf_availability_audit.yaml").read_text(encoding="utf-8"))
    records, result = build_universe_mapping(ROOT, config)
    assert result["mapping_complete"] is True
    assert result["mapped_count"] == 183
    assert result["sh_count"] + result["sz_count"] == 183
    assert not result["duplicate_ts_codes"]
    assert all(item.ts_code.endswith((".SH", ".SZ")) for item in records)


@pytest.mark.parametrize(("items", "expected"), [([], 0), (FIXTURE["items"][:1], 1), (FIXTURE["items"], 3)])
def test_zero_partial_and_full_coverage(items, expected):
    normalized = normalize_vendor_frame(frame(items), "2026-07-14", "tushare")
    _, quality = validate_snapshot(normalized, universe(), "2026-07-14")
    assert quality["matched_etf_count"] == expected
    assert quality["quality_complete"] is (expected == 3)


def test_exchange_delay_is_visible_separately():
    sz_only = normalize_vendor_frame(frame(FIXTURE["items"][:1]), "2026-07-14", "tushare")
    _, quality = validate_snapshot(sz_only, universe(), "2026-07-14")
    assert quality["sz_coverage_ratio"] == 1.0
    assert quality["sh_coverage_ratio"] == 0.0
    sh_only = normalize_vendor_frame(frame(FIXTURE["items"][1:]), "2026-07-14", "tushare")
    _, quality = validate_snapshot(sh_only, universe(), "2026-07-14")
    assert quality["sh_coverage_ratio"] == 1.0
    assert quality["sz_coverage_ratio"] == 0.0


def test_legal_zero_volume_is_not_quality_error():
    normalized = normalize_vendor_frame(frame(), "2026-07-14", "tushare")
    _, quality = validate_snapshot(normalized, universe(), "2026-07-14")
    assert quality["legal_zero_volume_count"] == 1
    assert quality["quality_complete"] is True


def test_duplicates_missing_fields_and_bad_ohlc_fail_quality():
    items = FIXTURE["items"] + [FIXTURE["items"][0]]
    items[1] = list(items[1])
    items[1][3] = 3.5
    raw = frame(items).drop(columns=["amount"])
    normalized = normalize_vendor_frame(raw, "2026-07-14", "tushare")
    _, quality = validate_snapshot(normalized, universe(), "2026-07-14")
    assert quality["duplicate_codes"] == ["159915.SZ"]
    assert quality["invalid_ohlc_count"] > 0
    assert quality["null_field_counts"]["amount"] == 3
    assert quality["quality_complete"] is False


def test_hash_ignores_row_order_and_revision_detects_changes():
    first = normalize_vendor_frame(frame(), "2026-07-14", "tushare")
    shuffled = first.sample(frac=1, random_state=4)
    assert snapshot_content_hash(first) == snapshot_content_hash(shuffled)
    revised = first.copy()
    revised.loc[revised["ts_code"] == "510300.SH", "amount"] += 1
    comparison = compare_snapshots(first, revised)
    assert comparison["material_revision"] is True
    assert comparison["revised_code_count"] == 1
    assert comparison["revised_fields"] == ["amount"]


def test_real_probe_is_one_call_append_only_and_duplicate_is_explicit(tmp_path):
    root, config = make_project(tmp_path)
    first = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:05", client_factory=factory(), now=datetime.fromisoformat("2026-07-14T15:05:00+08:00"), evidence_mode="real")
    second = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:05", client_factory=factory(), now=datetime.fromisoformat("2026-07-14T15:06:00+08:00"), evidence_mode="real")
    assert first["request_count"] == 1
    assert first["quality_complete"] is True
    assert second["response_status"] == "DUPLICATE_ATTEMPT_SKIPPED"
    manifests = list((root / "data/staging/tushare_etf_availability/2026-07-14/tushare/manifests").glob("*.json"))
    assert len(manifests) == 2
    assert all("fixture-token" not in path.read_text(encoding="utf-8") for path in manifests)


def test_network_permission_and_missed_probe_are_classified(tmp_path):
    root, config = make_project(tmp_path)
    network = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:05", client_factory=factory(network_error=TimeoutError("offline")), now=datetime.fromisoformat("2026-07-14T15:05:00+08:00"), evidence_mode="real")
    permission = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:30", client_factory=factory(code=40203, msg="permission denied"), now=datetime.fromisoformat("2026-07-14T15:30:00+08:00"), evidence_mode="real")
    missed = record_missed_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="16:00", reason="machine asleep")
    assert network["response_status"] == "NETWORK_FAILED"
    assert permission["response_status"] == "PERMISSION_BLOCKED"
    assert missed["response_status"] == "MISSED_PROBE"
    assert all(item["paper_engine_invoked"] is False for item in (network, permission, missed))


def test_stability_requires_complete_day_and_unchanged_future_hashes(tmp_path):
    root, config = make_project(tmp_path)
    for value in config["schedule"]["tushare_times"]:
        run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time=value, client_factory=factory(), now=datetime.fromisoformat(f"2026-07-14T{value}:00+08:00"), evidence_mode="real")
    result = build_availability_reports(root, config)
    row = result["tushare_rows"][0]
    assert row["day_status"] == "COMPLETE"
    assert row["first_complete_time"] == "15:05"
    assert row["first_stable_time"] == "15:05"
    assert result["valid_observation_days"] == 1


def test_manifest_contains_required_safety_flags(tmp_path):
    root, config = make_project(tmp_path)
    result = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:05", client_factory=factory(), now=datetime.fromisoformat("2026-07-14T15:05:00+08:00"), evidence_mode="real")
    assert result["token_exposed"] is False
    assert result["wrote_to_ssot"] is False
    assert result["paper_engine_invoked"] is False
    assert result["required_etf_count"] == 3
    assert result["required_universe_snapshot_hash"]


def test_early_probe_is_blocked_without_api_call(tmp_path):
    root, config = make_project(tmp_path)
    result = run_availability_probe(root, config, source="tushare", trade_date="2026-07-14", scheduled_time="15:05", client_factory=lambda **_: (_ for _ in ()).throw(AssertionError("client must not be created")), now=datetime.fromisoformat("2026-07-14T15:04:59+08:00"), evidence_mode="real")
    assert result["response_status"] == "BLOCKED_EARLY_PROBE"
    assert result["request_count"] == 0


def test_baostock_budget_blocks_before_import_or_network(tmp_path):
    _, config = make_project(tmp_path)
    config["baostock"]["max_calls_per_probe"] = 2
    with pytest.raises(RuntimeError, match="budget"):
        fetch_baostock_daily(universe(), "2026-07-14", config)
