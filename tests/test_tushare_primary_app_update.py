from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pandas as pd
import pytest
import yaml

from app.backend import readers as app_readers
from app.backend import safe_tasks
from app.backend import task_runner
from app.backend.safe_tasks import SAFE_TASKS, get_task, resolve_backfill_target
from scripts import update_etf_data_tushare as production_cli
from src.data_sources.tushare.app_update import (
    FORMAL_COLUMNS,
    directory_manifest,
    parse_formal_promotion_enabled,
    run_tushare_primary_update,
)
from src.data_sources.tushare.client import ProbeCall


TRADE_DATE = "2026-07-16"
PREVIOUS_DATE = "2026-07-15"
FIELDS = [
    "ts_code", "trade_date", "open", "high", "low", "close", "pre_close",
    "change", "pct_chg", "vol", "amount",
]


class FakeClient:
    def __init__(self, call: ProbeCall):
        self.call = call
        self.request_count = 0

    def request(self, interface: str, params: dict, fields: str) -> ProbeCall:
        assert interface == "fund_daily"
        assert params == {"trade_date": "20260716"}
        assert "ts_code" in fields
        self.request_count += 1
        return self.call


def make_project(tmp_path: Path, count: int = 183) -> tuple[Path, dict, list[str]]:
    root = tmp_path / "project"
    daily = root / "data/etf_daily"
    daily.mkdir(parents=True)
    rows = []
    ts_codes = []
    for index in range(count):
        exchange = "SH" if index < 92 else "SZ"
        prefix = exchange.lower()
        code = f"{510000 + index:06d}" if exchange == "SH" else f"{159000 + index:06d}"
        ts_code = f"{code}.{exchange}"
        ts_codes.append(ts_code)
        frame = pd.DataFrame([{
            "date": PREVIOUS_DATE,
            "code": f"{prefix}.{code}",
            "open": 1.0,
            "high": 1.2,
            "low": 0.9,
            "close": 1.1,
            "preclose": 1.0,
            "volume": 10000,
            "amount": 11000,
            "adjustflag": "3",
            "turn": "",
            "tradestatus": "1",
            "pctChg": 10.0,
            "isST": "1",
        }], columns=FORMAL_COLUMNS)
        frame.to_csv(daily / f"{prefix}_{code}.csv", index=False, lineterminator="\n")
        rows.append({"symbol": code, "pool": "research_only"})
    pd.DataFrame(rows).to_csv(root / "data/etf_classification.csv", index=False)
    config = yaml.safe_load((Path(__file__).parents[1] / "configs/tushare_primary_app_update.yaml").read_text(encoding="utf-8"))
    config["universe"]["expected_count"] = 183
    return root, config, ts_codes


def snapshot(ts_codes: list[str], *, trade_date: str = TRADE_DATE) -> pd.DataFrame:
    rows = []
    for index, ts_code in enumerate(ts_codes):
        close = 1.1 + index / 10000
        rows.append([
            ts_code,
            trade_date.replace("-", ""),
            close,
            close + 0.1,
            close - 0.1,
            close,
            close - 0.01,
            0.01,
            0.9,
            1000 + index,
            2000 + index,
        ])
    return pd.DataFrame(rows, columns=FIELDS)


def probe_call(frame: pd.DataFrame, *, status: str = "ACCESS_PASS", error: str = "") -> ProbeCall:
    return ProbeCall(
        interface="fund_daily",
        request_parameters_sanitized={"trade_date": "20260716"},
        request_sequence=1,
        response_status=status,
        permission_status="ACCESS_PASS" if status == "ACCESS_PASS" else "UNKNOWN",
        retrieved_at="2026-07-16T16:30:00+08:00",
        query_hash="query",
        raw_payload_hash="raw",
        frame=frame,
        raw_payload={},
        error_class="",
        error_message_sanitized=error,
    )


def factory(call: ProbeCall):
    return lambda **_: FakeClient(call)


def no_half_transaction_dirs(root: Path) -> bool:
    runs = root / "data/staging/tushare_primary_app_update/runs"
    return not runs.exists() or not any(runs.iterdir())


def assert_public_reason_sanitized(result: dict, root: Path, token: str = "qc-secret-token") -> None:
    reason = str(result.get("reason", ""))
    assert str(root) not in reason
    assert token not in reason
    assert "Traceback" not in reason
    assert "most recent call last" not in reason


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (False, False),
        ("false", False),
        (True, True),
        ("true", True),
        (None, False),
        ("", False),
        ("invalid", False),
        ("TRUE", False),
        (1, False),
    ],
)
def test_formal_promotion_enabled_uses_strict_fail_closed_parsing(value, expected):
    assert parse_formal_promotion_enabled(value) is expected


def test_183_of_183_builds_complete_candidate_with_promotion_disabled(tmp_path):
    root, config, codes = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(probe_call(snapshot(codes))))

    assert result["result_code"] == "CANDIDATE_READY"
    assert result["provider"] == "TUSHARE"
    assert result["candidate_file_count"] == 183
    assert result["up_to_date_count"] == 183
    assert result["business_date"] == TRADE_DATE
    assert result["updated_count"] == 183
    assert result["ssot_manifest_hash"] == before["manifest_hash"]
    assert result["promotion_enabled"] is False
    assert result["promotion_attempted"] is False
    assert directory_manifest(root / "data/etf_daily") == before
    candidate = root / result["candidate_directory"]
    assert len(list(candidate.glob("*.csv"))) == 183
    assert os.stat(candidate).st_dev == os.stat(root / "data/etf_daily").st_dev
    assert all(TRADE_DATE in set(pd.read_csv(path, dtype=str)["date"]) for path in candidate.glob("*.csv"))


def test_explicit_test_promotion_swaps_complete_directory(tmp_path):
    root, config, codes = make_project(tmp_path)
    config["promotion"]["formal_promotion_enabled"] = True
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(probe_call(snapshot(codes))))

    assert result["result_code"] == "PROMOTED"
    assert result["provider"] == "TUSHARE"
    assert result["ssot_changed"] is True
    assert result["before_manifest_hash"] != result["after_manifest_hash"]
    assert result["business_date"] == TRADE_DATE
    assert result["updated_count"] == 183
    assert result["ssot_manifest_hash"] == result["after_manifest_hash"]
    assert (root / result["manifest_paths"]["before"]).is_file()
    assert (root / result["manifest_paths"]["candidate"]).is_file()
    assert (root / result["manifest_paths"]["after"]).is_file()
    assert len(list((root / "data/etf_daily").glob("*.csv"))) == 183
    assert all(TRADE_DATE in set(pd.read_csv(path, dtype=str)["date"]) for path in (root / "data/etf_daily").glob("*.csv"))


def test_182_of_183_is_data_not_ready_and_preserves_ssot(tmp_path):
    root, config, codes = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(probe_call(snapshot(codes[:-1]))))

    assert result["result_code"] == "DATA_NOT_READY"
    assert result["matched_etf_count"] == 182
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_incomplete_canonical_universe_stops_before_provider_call(tmp_path):
    root, config, _ = make_project(tmp_path, count=182)
    before = directory_manifest(root / "data/etf_daily")
    result = run_tushare_primary_update(
        root,
        config,
        TRADE_DATE,
        client_factory=lambda **_: (_ for _ in ()).throw(AssertionError("provider must not be called")),
    )
    assert result["result_code"] == "INCOMPLETE_UNIVERSE"
    assert result["actual_api_calls"] == 0
    assert directory_manifest(root / "data/etf_daily") == before


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (probe_call(pd.DataFrame(columns=FIELDS), status="EMPTY_UNEXPECTED"), "DATA_NOT_READY"),
        (probe_call(pd.DataFrame(columns=FIELDS), status="BLOCKED_TOKEN_MISSING", error="token is missing"), "PROVIDER_AUTH_ERROR"),
        (probe_call(pd.DataFrame(columns=FIELDS), status="NETWORK_FAILED", error="connection timed out"), "PROVIDER_NETWORK_ERROR"),
        (probe_call(pd.DataFrame(columns=FIELDS), status="VALIDATION_FAILED", error="rate limit exceeded"), "PROVIDER_RATE_LIMITED"),
    ],
)
def test_provider_failures_are_fail_closed_without_fallback(tmp_path, call, expected):
    root, config, _ = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(call))

    assert result["result_code"] == expected
    assert result["baostock_api_calls"] == 0
    assert result["jqdata_api_calls"] == 0
    assert result["fallback_triggered"] is False
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_provider_exception_returns_stable_sanitized_reason(tmp_path):
    root, config, _ = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")

    class FailingClient:
        request_count = 0

        def request(self, *_):
            raise OSError(f"network failure at {root}; token=qc-secret-token\nTraceback (most recent call last):")

    result = run_tushare_primary_update(
        root,
        config,
        TRADE_DATE,
        client_factory=lambda **_: FailingClient(),
    )
    assert result["result_code"] == "PROVIDER_AUTH_ERROR"
    assert result["reason"] == "Tushare provider authentication failed"
    assert_public_reason_sanitized(result, root)
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_field_validation_failure_preserves_ssot(tmp_path):
    root, config, codes = make_project(tmp_path)
    bad = snapshot(codes)
    bad.loc[0, "open"] = None
    before = directory_manifest(root / "data/etf_daily")
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(probe_call(bad)))

    assert result["result_code"] == "FIELD_VALIDATION_FAILED"
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_freshness_gate_failure_preserves_ssot(tmp_path):
    root, config, codes = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")
    stale = snapshot(codes, trade_date=PREVIOUS_DATE)
    result = run_tushare_primary_update(root, config, TRADE_DATE, client_factory=factory(probe_call(stale)))

    assert result["result_code"] == "FRESHNESS_GATE_FAILED"
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_candidate_generation_failure_preserves_ssot(tmp_path):
    root, config, codes = make_project(tmp_path)
    before = directory_manifest(root / "data/etf_daily")

    def fail_builder(*_):
        raise OSError(f"candidate disk failure at {root}; TUSHARE_TOKEN=qc-secret-token\nTraceback (most recent call last):")

    result = run_tushare_primary_update(
        root,
        config,
        TRADE_DATE,
        client_factory=factory(probe_call(snapshot(codes))),
        candidate_builder=fail_builder,
    )
    assert result["result_code"] == "PROMOTION_FAILED"
    assert result["reason"] == "candidate generation failed; SSOT preserved"
    assert result["failure_stage"] == "candidate_generation"
    assert_public_reason_sanitized(result, root)
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_directory_switch_failure_rolls_back_and_verifies_manifest(tmp_path):
    root, config, codes = make_project(tmp_path)
    config["promotion"]["formal_promotion_enabled"] = True
    before = directory_manifest(root / "data/etf_daily")
    calls = 0

    def fail_candidate_switch(src, dst):
        nonlocal calls
        calls += 1
        if calls == 1:
            before_manifests = list((Path(src).parent / "staging/tushare_primary_app_update/manifests").glob("*/before_manifest.json"))
            assert len(before_manifests) == 1
        if calls == 2:
            raise OSError(f"cannot move {src} to {dst}; token=qc-secret-token\nTraceback (most recent call last):")
        os.replace(src, dst)

    result = run_tushare_primary_update(
        root,
        config,
        TRADE_DATE,
        client_factory=factory(probe_call(snapshot(codes))),
        rename=fail_candidate_switch,
    )
    assert result["result_code"] == "PROMOTION_FAILED"
    assert result["reason"] == "directory promotion failed; rollback restored original SSOT"
    assert result["rollback_verified"] is True
    assert_public_reason_sanitized(result, root)
    assert (root / result["manifest_paths"]["before"]).is_file()
    assert (root / result["manifest_paths"]["candidate"]).is_file()
    assert (root / result["manifest_paths"]["rollback"]).is_file()
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_rollback_failure_raises_explicit_alarm_and_emergency_restores_ssot(tmp_path):
    root, config, codes = make_project(tmp_path)
    config["promotion"]["formal_promotion_enabled"] = True
    before = directory_manifest(root / "data/etf_daily")
    calls = 0

    def fail_switch_and_primary_rollback(src, dst):
        nonlocal calls
        calls += 1
        if calls in {2, 3}:
            raise OSError(f"injected rename failure {calls} at {src}; token=qc-secret-token\nTraceback (most recent call last):")
        os.replace(src, dst)

    result = run_tushare_primary_update(
        root,
        config,
        TRADE_DATE,
        client_factory=factory(probe_call(snapshot(codes))),
        rename=fail_switch_and_primary_rollback,
    )
    assert result["result_code"] == "ROLLBACK_FAILED"
    assert result["reason"] == "directory rollback failed; manual recovery review required"
    assert result["emergency_restore_succeeded"] is True
    assert_public_reason_sanitized(result, root)
    assert directory_manifest(root / "data/etf_daily") == before
    assert no_half_transaction_dirs(root)


def test_app_task_keeps_name_and_has_no_baostock_or_jqdata_command():
    task = SAFE_TASKS["backfill_etf_data"]
    command = " ".join(task.commands[0].args).lower()
    assert task.name == "backfill_etf_data"
    assert "update_etf_data_tushare.py" in command
    assert "baostock" not in command
    assert "jqdata" not in command
    assert "--config" not in command
    assert "configs/tushare_primary_app_update.yaml" not in command
    assert len(task.commands) == 6


def test_app_runtime_python_can_import_pyyaml():
    completed = subprocess.run(
        [safe_tasks.PYTHON, "-c", "import yaml; print(yaml.__version__)"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip()


def test_latest_stable_date_drives_backfill_task_date(tmp_path):
    manifests = tmp_path / "data/staging/tushare_etf_availability/2026-07-16/tushare/manifests"
    manifests.mkdir(parents=True)
    for minute in (10, 15, 30):
        payload = {
            "probe_id": f"2026-07-16T16{minute:02d}_tushare",
            "source": "tushare",
            "evidence_mode": "real",
            "trade_date": TRADE_DATE,
            "scheduled_at": f"2026-07-16T16:{minute:02d}:00+08:00",
            "completed_at": f"2026-07-16T16:{minute:02d}:01+08:00",
            "response_status": "ACCESS_PASS",
            "required_etf_count": 183,
            "matched_etf_count": 183,
            "quality_complete": True,
            "field_complete": True,
            "trade_date_valid": True,
            "source_snapshot_hash": "stable-manifest-hash",
        }
        (manifests / f"{minute}.json").write_text(json.dumps(payload), encoding="utf-8")

    observation = resolve_backfill_target(TRADE_DATE, tmp_path)
    task = get_task("backfill_etf_data", observation["business_date"])
    assert task is not None
    assert observation["business_date"] == TRADE_DATE
    assert observation["manifest_hash"] == "stable-manifest-hash"
    assert task.commands[0].args[task.commands[0].args.index("--trade-date") + 1] == TRADE_DATE


def test_target_date_mismatch_is_fail_closed(monkeypatch):
    monkeypatch.setattr(
        task_runner,
        "resolve_backfill_target",
        lambda _: (_ for _ in ()).throw(safe_tasks.TargetDateMismatchError(PREVIOUS_DATE, TRADE_DATE)),
    )
    result = task_runner.start_task("backfill_etf_data", PREVIOUS_DATE)
    assert result == {
        "accepted": False,
        "result_code": "TARGET_DATE_MISMATCH",
        "requested_business_date": PREVIOUS_DATE,
        "latest_stable_business_date": TRADE_DATE,
    }


def test_production_cli_pins_config_and_rejects_config_override():
    root = Path(__file__).parents[1]
    assert production_cli.CONFIG_PATH == root / "configs/tushare_primary_app_update.yaml"
    with pytest.raises(SystemExit):
        production_cli.parse_args([
            "--trade-date",
            TRADE_DATE,
            "--config",
            "configs/unsafe_override.yaml",
        ])
    source = (root / "scripts/update_etf_data_tushare.py").read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "getenv" not in source


def test_app_status_returns_tushare_provider(tmp_path, monkeypatch):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "data_update_status.json").write_text(json.dumps({
        "provider": "TUSHARE",
        "result_code": "CANDIDATE_READY",
        "status": "candidate_ready",
        "processed_symbols": 183,
        "actual_api_calls": 1,
        "business_date": TRADE_DATE,
        "updated_count": 183,
        "ssot_manifest_hash": "manifest-hash",
    }), encoding="utf-8")
    monkeypatch.setattr(task_runner, "REPORT_DIR", report_dir)
    payload = task_runner._task_data_update_status("backfill_etf_data")
    assert payload["provider"] == "TUSHARE"
    assert payload["result_code"] == "CANDIDATE_READY"
    assert payload["business_date"] == TRADE_DATE
    assert payload["updated_count"] == 183
    assert payload["ssot_manifest_hash"] == "manifest-hash"


def test_app_main_status_ignores_legacy_provider_and_fallback(monkeypatch):
    legacy = {
        "primary_source": "baostock",
        "actual_source_used": "baostock",
        "fallback_triggered": True,
        "baostock_status": "UP_TO_DATE",
        "jqdata_status": "FALLBACK_READY",
    }
    update = {
        "provider": "TUSHARE",
        "actual_source_used": "TUSHARE",
        "status": "candidate_ready",
        "fallback_triggered": False,
    }
    monkeypatch.setattr(app_readers, "dashboard_data", lambda: {})
    monkeypatch.setattr(app_readers, "data_update_status", lambda: update)
    monkeypatch.setattr(app_readers, "data_source_status", lambda: legacy)
    monkeypatch.setattr(app_readers, "execution_safety_snapshot", lambda: {})

    payload = app_readers.status_snapshot()
    assert payload["primary_provider"] == "TUSHARE"
    assert payload["actual_source_used"] == "TUSHARE"
    assert payload["fallback_enabled"] is False
    assert payload["fallback_triggered"] is False
    assert payload["baostock_role"] == "RECONCILIATION_ONLY"
    assert payload["jqdata_fallback"] == "DISABLED"
    assert "baostock_status" not in payload
    assert "jqdata_status" not in payload
    assert payload["legacy_reconciliation"]["baostock_status"] == "UP_TO_DATE"


def test_data_health_main_status_ignores_legacy_provider_and_fallback(monkeypatch):
    legacy = {
        "actual_source_used": "baostock",
        "fallback_triggered": True,
        "baostock_status": "UP_TO_DATE",
        "jqdata_status": "FALLBACK_READY",
    }
    update = {
        "provider": "TUSHARE",
        "actual_source_used": "TUSHARE",
        "status": "candidate_ready",
        "fallback_triggered": False,
        "actual_api_calls": 1,
    }
    monkeypatch.setattr(app_readers, "dashboard_data", lambda: {})
    monkeypatch.setattr(app_readers, "data_update_status", lambda: update)
    monkeypatch.setattr(app_readers, "data_source_status", lambda: legacy)
    monkeypatch.setattr(app_readers, "tail_text", lambda *_: "")
    monkeypatch.setattr(app_readers, "etf_inventory_snapshot", lambda: [])

    payload = app_readers.data_health_snapshot()
    assert payload["primary_provider"] == "TUSHARE"
    assert payload["actual_source_used"] == "TUSHARE"
    assert payload["fallback_enabled"] is False
    assert payload["fallback_triggered"] is False
    assert payload["baostock_role"] == "RECONCILIATION_ONLY"
    assert payload["jqdata_fallback"] == "DISABLED"
    assert "baostock_status" not in payload
    assert "jqdata_status" not in payload
    assert payload["legacy_reconciliation"]["jqdata_status"] == "FALLBACK_READY"


def test_config_disables_formal_promotion_and_fallback_by_default():
    config = yaml.safe_load((Path(__file__).parents[1] / "configs/tushare_primary_app_update.yaml").read_text(encoding="utf-8"))
    assert config["promotion"]["formal_promotion_enabled"] is False
    assert config["policy"]["canonical_ssot"] == "data/etf_daily/"
    assert config["policy"]["baostock_role"] == "RECONCILIATION_ONLY"
    assert config["policy"]["jqdata_fallback"] == "DISABLED"
    assert config["policy"]["staging_is_formal_database"] is False
    assert config["cleanup"]["preserve_backup_on_unverified_rollback"] is True
    assert config["cleanup"]["availability_staging_untouched"] is True


def test_app_dashboard_and_models_keep_reading_canonical_ssot():
    root = Path(__file__).parents[1]
    readers = (root / "app/backend/readers.py").read_text(encoding="utf-8")
    dashboard = (root / "dashboard/build_dashboard.py").read_text(encoding="utf-8")
    model_config = (root / "src/config.py").read_text(encoding="utf-8")
    data_center = (root / "app/frontend/src/pages/DataCenter.jsx").read_text(encoding="utf-8")
    data_health_panel = (root / "app/frontend/src/components/DataHealthPanel.jsx").read_text(encoding="utf-8")
    assert 'ETF_DAILY_DIR = DATA_DIR / "etf_daily"' in readers
    assert '(DATA_DIR / "etf_daily").glob("*.csv")' in dashboard
    assert 'ETF_DAILY_DIR = DATA_DIR / "etf_daily"' in model_config
    assert "tushare_primary_app_update" not in dashboard
    assert "tushare_primary_app_update" not in model_config
    assert "primary_provider" in data_center
    assert "fallback_enabled" in data_center
    assert "primary_provider" in data_health_panel
    assert "fallback_enabled" in data_health_panel
    assert "baostock_status" not in data_health_panel
    assert "jqdata_status" not in data_health_panel
    assert "fallback_triggered" not in data_health_panel
