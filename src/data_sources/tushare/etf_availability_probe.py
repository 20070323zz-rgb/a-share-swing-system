"""Read-only, append-only ETF daily availability probes."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable
import uuid
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from .availability_models import AuditPaths, SNAPSHOT_FIELDS, UniverseRecord, iso_time
from .availability_validators import (
    build_universe_mapping,
    canonical_hash,
    compare_snapshots,
    mapping_frame,
    normalize_vendor_frame,
    validate_snapshot,
)
from .client import TushareMinimalClient


TZ = ZoneInfo("Asia/Shanghai")
BaoStockFetcher = Callable[[list[UniverseRecord], str, dict[str, Any]], tuple[pd.DataFrame, int, str, str]]


def load_audit_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def refresh_trade_calendar(
    project_root: Path,
    config: dict[str, Any],
    *,
    client_factory: Callable[..., TushareMinimalClient] = TushareMinimalClient,
    anchor_date: date | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    paths = AuditPaths.from_config(root, config)
    anchor = anchor_date or datetime.now(TZ).date()
    client = _client(root, config, client_factory, max_requests=1)
    start = (anchor - timedelta(days=14)).strftime("%Y%m%d")
    end = (anchor + timedelta(days=31)).strftime("%Y%m%d")
    call = client.request(
        config["calendar"]["interface"],
        {"exchange": config["calendar"]["exchange"], "start_date": start, "end_date": end},
        "exchange,cal_date,is_open,pretrade_date",
    )
    rows = []
    if call.response_status == "ACCESS_PASS":
        for row in call.frame.to_dict(orient="records"):
            rows.append({
                "exchange": str(row.get("exchange", "")),
                "cal_date": _iso_date(row.get("cal_date")),
                "is_open": int(float(row.get("is_open", 0) or 0)),
                "pretrade_date": _iso_date(row.get("pretrade_date")),
            })
    payload = {
        "schema_version": 1,
        "source": "tushare",
        "interface": "trade_cal",
        "retrieved_at": call.retrieved_at,
        "response_status": call.response_status,
        "permission_status": call.permission_status,
        "request_count": client.request_count,
        "query_hash": call.query_hash,
        "raw_payload_hash": call.raw_payload_hash,
        "date_min": min((row["cal_date"] for row in rows), default=""),
        "date_max": max((row["cal_date"] for row in rows), default=""),
        "rows": rows,
        "token_exposed": False,
        "wrote_to_ssot": False,
    }
    paths.calendar_cache.parent.mkdir(parents=True, exist_ok=True)
    paths.calendar_history.mkdir(parents=True, exist_ok=True)
    history_name = f"trade_calendar__{call.retrieved_at.replace(':', '').replace('+', '_')}.json"
    with (paths.calendar_history / history_name).open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    paths.calendar_cache.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def run_availability_probe(
    project_root: Path,
    config: dict[str, Any],
    *,
    source: str,
    trade_date: str,
    scheduled_time: str,
    client_factory: Callable[..., TushareMinimalClient] = TushareMinimalClient,
    baostock_fetcher: BaoStockFetcher | None = None,
    now: datetime | None = None,
    evidence_mode: str = "real",
) -> dict[str, Any]:
    root = project_root.resolve()
    paths = AuditPaths.from_config(root, config)
    current = now or datetime.now(TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TZ)
    scheduled_at = datetime.fromisoformat(f"{trade_date}T{scheduled_time}:00").replace(tzinfo=TZ)
    audit_id = str(config["audit_id"])
    probe_id = f"{trade_date}T{scheduled_time.replace(':', '')}_{source}"
    universe, mapping = build_universe_mapping(root, config)
    if not mapping["mapping_complete"]:
        raise ValueError(f"Universe mapping incomplete: {mapping}")

    if current < scheduled_at:
        manifest = _base_manifest(audit_id, probe_id, source, trade_date, scheduled_at, current, universe, mapping, evidence_mode)
        manifest.update({
            "response_status": "BLOCKED_EARLY_PROBE",
            "error_class": "EARLY_PROBE",
            "error_message_sanitized": "Probe invocation preceded its scheduled observation time; no vendor call was made.",
        })
        return _persist_manifest(paths, manifest)

    duplicate = _find_completed_probe(paths, trade_date, source, probe_id)
    if duplicate:
        manifest = _base_manifest(audit_id, probe_id, source, trade_date, scheduled_at, current, universe, mapping, evidence_mode)
        manifest.update({
            "response_status": "DUPLICATE_ATTEMPT_SKIPPED",
            "original_manifest": duplicate,
            "error_class": "DUPLICATE_ATTEMPT",
            "error_message_sanitized": "A completed attempt already exists for this source and scheduled slot.",
        })
        return _persist_manifest(paths, manifest)

    calendar = _calendar_decision(paths, trade_date)
    if calendar != "TRADING_DAY_CONFIRMED":
        manifest = _base_manifest(audit_id, probe_id, source, trade_date, scheduled_at, current, universe, mapping, evidence_mode)
        manifest.update({
            "response_status": "SKIPPED_NON_TRADING_DAY" if calendar == "NON_TRADING_DAY_CONFIRMED" else "BLOCKED_CALENDAR_UNCONFIRMED",
            "calendar_decision": calendar,
            "error_class": "" if calendar == "NON_TRADING_DAY_CONFIRMED" else "CALENDAR_UNCONFIRMED",
            "error_message_sanitized": "" if calendar == "NON_TRADING_DAY_CONFIRMED" else "Trade date is absent from the cached Tushare trade calendar.",
        })
        return _persist_manifest(paths, manifest)

    started = datetime.now(TZ)
    response_status = "NETWORK_FAILED"
    permission_status = "UNKNOWN"
    request_count = 0
    total_source_rows = 0
    error_class = ""
    error_message = ""
    query_hash = ""
    raw_hash = ""
    frame = pd.DataFrame(columns=SNAPSHOT_FIELDS)
    if source == "tushare":
        client = _client(root, config, client_factory, max_requests=int(config["tushare"]["max_calls_per_probe"]))
        call = client.request(
            config["tushare"]["interface"],
            {"trade_date": trade_date.replace("-", "")},
            config["tushare"]["fields"],
        )
        response_status = call.response_status
        permission_status = call.permission_status
        request_count = client.request_count
        total_source_rows = call.row_count
        error_class = call.error_class
        error_message = call.error_message_sanitized
        query_hash = call.query_hash
        raw_hash = call.raw_payload_hash
        frame = normalize_vendor_frame(call.frame, trade_date, source)
    elif source == "baostock":
        fetcher = baostock_fetcher or fetch_baostock_daily
        try:
            raw, request_count, response_status, error_message = fetcher(universe, trade_date, config)
            permission_status = "NOT_APPLICABLE"
            total_source_rows = len(raw)
            frame = normalize_vendor_frame(raw, trade_date, source)
            query_hash = canonical_hash({"source": source, "trade_date": trade_date, "required_codes": [item.etf_code for item in universe]})
            raw_hash = canonical_hash(raw.fillna("").astype(str).to_dict(orient="records")) if not raw.empty else ""
        except Exception as exc:  # noqa: BLE001 - sanitized in evidence
            response_status = "NETWORK_FAILED"
            error_class = type(exc).__name__
            error_message = str(exc).replace("\n", " ")[:500]
    else:
        raise ValueError(f"unsupported source: {source}")

    normalized, quality = validate_snapshot(frame, universe, trade_date)
    previous, previous_manifest = _load_previous_snapshot(paths, trade_date, source, scheduled_at)
    revision = compare_snapshots(previous, normalized)
    completed = datetime.now(TZ)
    manifest = _base_manifest(audit_id, probe_id, source, trade_date, scheduled_at, current, universe, mapping, evidence_mode)
    manifest.update({
        "started_at": iso_time(started),
        "completed_at": iso_time(completed),
        "retrieved_at": iso_time(completed),
        "interface": config[source]["interface"],
        "request_count": request_count,
        "response_status": response_status,
        "permission_status": permission_status,
        "total_source_rows": total_source_rows,
        **quality,
        **revision,
        "query_hash": query_hash,
        "raw_payload_hash": raw_hash,
        "required_universe_snapshot_hash": mapping["mapping_hash"],
        "previous_manifest": previous_manifest,
        "error_class": error_class,
        "error_message_sanitized": error_message,
    })
    if manifest["material_revision"]:
        manifest["last_revision_time"] = iso_time(completed)
    if response_status == "ACCESS_PASS" and normalized.empty:
        manifest["response_status"] = "EMPTY_UNEXPECTED"
    return _persist_manifest(paths, manifest, normalized)


def record_missed_probe(
    project_root: Path,
    config: dict[str, Any],
    *,
    source: str,
    trade_date: str,
    scheduled_time: str,
    reason: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    paths = AuditPaths.from_config(root, config)
    current = now or datetime.now(TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TZ)
    universe, mapping = build_universe_mapping(root, config)
    probe_id = f"{trade_date}T{scheduled_time.replace(':', '')}_{source}"
    if _find_completed_probe(paths, trade_date, source, probe_id):
        return {"response_status": "ALREADY_RECORDED", "probe_id": probe_id}
    scheduled_at = datetime.fromisoformat(f"{trade_date}T{scheduled_time}:00").replace(tzinfo=TZ)
    manifest = _base_manifest(config["audit_id"], probe_id, source, trade_date, scheduled_at, current, universe, mapping, "real")
    manifest.update({
        "response_status": "MISSED_PROBE",
        "error_class": "MISSED_PROBE",
        "error_message_sanitized": reason,
    })
    return _persist_manifest(paths, manifest)


def fetch_baostock_daily(universe: list[UniverseRecord], trade_date: str, config: dict[str, Any]) -> tuple[pd.DataFrame, int, str, str]:
    if len(universe) > int(config["baostock"]["max_calls_per_probe"]):
        raise RuntimeError("BaoStock request budget would be exceeded; no comparator calls were made.")
    try:
        import baostock as bs
    except ModuleNotFoundError:
        return _fetch_baostock_subprocess(universe, trade_date, config)

    login = bs.login()
    if str(login.error_code) != "0":
        return pd.DataFrame(), 0, "NETWORK_FAILED", f"BaoStock login failed: {login.error_code} {login.error_msg}"
    rows: list[list[str]] = []
    fields = config["baostock"]["fields"]
    request_count = 0
    try:
        for item in universe:
            bs_code = f"{item.exchange.lower()}.{item.etf_code}"
            result = bs.query_history_k_data_plus(
                bs_code,
                fields,
                start_date=trade_date,
                end_date=trade_date,
                frequency="d",
                adjustflag=str(config["baostock"]["adjustflag"]),
            )
            request_count += 1
            if str(result.error_code) != "0":
                continue
            while result.next():
                rows.append(result.get_row_data())
            time.sleep(float(config["baostock"]["request_interval_seconds"]))
    finally:
        bs.logout()
    frame = pd.DataFrame(rows, columns=fields.split(",")) if rows else pd.DataFrame(columns=fields.split(","))
    return frame, request_count, "ACCESS_PASS" if not frame.empty else "EMPTY_UNEXPECTED", ""


def _fetch_baostock_subprocess(universe: list[UniverseRecord], trade_date: str, config: dict[str, Any]) -> tuple[pd.DataFrame, int, str, str]:
    interpreter = _baostock_interpreter(Path(__file__).resolve().parents[3])
    helper = Path(__file__).with_name("baostock_availability_helper.py")
    request = {
        "trade_date": trade_date,
        "codes": [f"{item.exchange.lower()}.{item.etf_code}" for item in universe],
        "fields": config["baostock"]["fields"],
        "adjustflag": str(config["baostock"]["adjustflag"]),
        "request_interval_seconds": float(config["baostock"]["request_interval_seconds"]),
    }
    try:
        completed = subprocess.run(
            [str(interpreter), str(helper)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            timeout=max(60, len(universe) * 3),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return pd.DataFrame(), 0, "NETWORK_FAILED", "BaoStock helper exceeded its bounded timeout."
    if completed.returncode != 0:
        return pd.DataFrame(), 0, "NETWORK_FAILED", f"BaoStock helper failed with exit code {completed.returncode}."
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return pd.DataFrame(), 0, "NETWORK_FAILED", "BaoStock helper returned invalid sanitized output."
    fields = str(config["baostock"]["fields"]).split(",")
    frame = pd.DataFrame(payload.get("rows", []), columns=fields)
    return frame, int(payload.get("request_count", 0)), str(payload.get("status", "NETWORK_FAILED")), str(payload.get("error", ""))[:500]


def _baostock_interpreter(project_root: Path) -> Path:
    configured = os.environ.get("A_SHARE_BAOSTOCK_PYTHON", "")
    candidates = [
        Path(configured).expanduser() if configured else None,
        project_root / ".venv/bin/python",
        project_root.parent / "a-share-swing-system" / ".venv/bin/python",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("No existing BaoStock-capable Python interpreter was found; no package installation was attempted.")


def write_universe_mapping_report(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    root = project_root.resolve()
    paths = AuditPaths.from_config(root, config)
    records, payload = build_universe_mapping(root, config)
    paths.universe_mapping.parent.mkdir(parents=True, exist_ok=True)
    frame = mapping_frame(records)
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)):
            frame[key] = value
    frame.to_csv(paths.universe_mapping, index=False, lineterminator="\n")
    return payload


def _client(project_root: Path, config: dict[str, Any], factory: Callable[..., TushareMinimalClient], *, max_requests: int) -> TushareMinimalClient:
    settings = config["tushare"]
    return factory(
        project_root=project_root,
        max_requests=max_requests,
        timeout_seconds=int(settings["timeout_seconds"]),
        request_interval_seconds=float(settings["request_interval_seconds"]),
        max_network_retries=int(settings["max_network_retries"]),
    )


def _base_manifest(
    audit_id: str,
    probe_id: str,
    source: str,
    trade_date: str,
    scheduled_at: datetime,
    current: datetime,
    universe: list[UniverseRecord],
    mapping: dict[str, Any],
    evidence_mode: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "audit_id": audit_id,
        "probe_id": probe_id,
        "attempt_id": uuid.uuid4().hex,
        "source": source,
        "trade_date": trade_date,
        "scheduled_at": iso_time(scheduled_at),
        "started_at": iso_time(current),
        "completed_at": iso_time(current),
        "retrieved_at": "",
        "evidence_mode": evidence_mode,
        "interface": "",
        "request_count": 0,
        "response_status": "NOT_STARTED",
        "permission_status": "NOT_TESTED",
        "calendar_decision": "TRADING_DAY_CONFIRMED",
        "total_source_rows": 0,
        "required_etf_count": len(universe),
        "matched_etf_count": 0,
        "coverage_ratio": 0.0,
        "sh_count": 0,
        "sz_count": 0,
        "sh_coverage_ratio": 0.0,
        "sz_coverage_ratio": 0.0,
        "missing_codes": [],
        "duplicate_codes": [],
        "invalid_codes": [],
        "null_field_counts": {},
        "invalid_ohlc_count": 0,
        "invalid_volume_count": 0,
        "invalid_amount_count": 0,
        "legal_zero_volume_count": 0,
        "critical_field_error_count": 0,
        "field_complete": False,
        "quality_complete": False,
        "source_snapshot_hash": "",
        "required_universe_snapshot_hash": mapping["mapping_hash"],
        "revision_count": 0,
        "revised_code_count": 0,
        "revised_fields": [],
        "last_revision_time": "",
        "material_revision": False,
        "error_class": "",
        "error_message_sanitized": "",
        "token_exposed": False,
        "wrote_to_ssot": False,
        "paper_engine_invoked": False,
    }


def _persist_manifest(paths: AuditPaths, manifest: dict[str, Any], snapshot: pd.DataFrame | None = None) -> dict[str, Any]:
    source = str(manifest["source"])
    trade_date = str(manifest["trade_date"])
    base = paths.staging_root / trade_date / source
    manifest_dir = base / "manifests"
    snapshot_dir = base / "snapshots"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{manifest['probe_id']}__{manifest['attempt_id']}"
    if snapshot is not None:
        snapshot_path = snapshot_dir / f"{stem}.csv"
        snapshot.to_csv(snapshot_path, index=False, lineterminator="\n")
        manifest["snapshot_path"] = str(snapshot_path.relative_to(paths.project_root))
    else:
        manifest["snapshot_path"] = ""
    manifest_path = manifest_dir / f"{stem}.json"
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    manifest["manifest_path"] = str(manifest_path.relative_to(paths.project_root))
    return manifest


def _find_completed_probe(paths: AuditPaths, trade_date: str, source: str, probe_id: str) -> str:
    directory = paths.staging_root / trade_date / source / "manifests"
    for path in sorted(directory.glob(f"{probe_id}__*.json")) if directory.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("response_status") not in {"DUPLICATE_ATTEMPT_SKIPPED", "BLOCKED_EARLY_PROBE"}:
            return str(path.relative_to(paths.project_root))
    return ""


def _load_previous_snapshot(paths: AuditPaths, trade_date: str, source: str, scheduled_at: datetime) -> tuple[pd.DataFrame | None, str]:
    directory = paths.staging_root / trade_date / source / "manifests"
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for path in directory.glob("*.json") if directory.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("snapshot_path") and str(payload.get("scheduled_at", "")) < iso_time(scheduled_at):
            candidates.append((str(payload["scheduled_at"]), path, payload))
    if not candidates:
        return None, ""
    _, path, payload = max(candidates, key=lambda item: item[0])
    snapshot_path = paths.project_root / payload["snapshot_path"]
    return pd.read_csv(snapshot_path), str(path.relative_to(paths.project_root))


def _calendar_decision(paths: AuditPaths, trade_date: str) -> str:
    if not paths.calendar_cache.exists():
        return "CALENDAR_UNCONFIRMED"
    try:
        payload = json.loads(paths.calendar_cache.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "CALENDAR_UNCONFIRMED"
    for row in payload.get("rows", []):
        if row.get("cal_date") == trade_date:
            return "TRADING_DAY_CONFIRMED" if int(row.get("is_open", 0)) == 1 else "NON_TRADING_DAY_CONFIRMED"
    return "CALENDAR_UNCONFIRMED"


def _iso_date(value: Any) -> str:
    parsed = pd.to_datetime(str(value or ""), errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")
