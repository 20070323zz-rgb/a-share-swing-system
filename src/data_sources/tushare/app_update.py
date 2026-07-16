"""Tushare-primary candidate build and directory-transaction promotion.

The pipeline never mutates individual files in the canonical SSOT. It builds a
complete candidate directory, validates it, and only then swaps directories.
Production promotion is controlled exclusively by the checked-in config and is
disabled by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Callable
from zoneinfo import ZoneInfo

import pandas as pd

from .availability_models import SNAPSHOT_FIELDS, UniverseRecord
from .availability_validators import build_universe_mapping, validate_snapshot
from .client import ProbeCall, TushareMinimalClient, sanitize_message


TZ = ZoneInfo("Asia/Shanghai")
FORMAL_COLUMNS = [
    "date", "code", "open", "high", "low", "close", "preclose", "volume",
    "amount", "adjustflag", "turn", "tradestatus", "pctChg", "isST",
]
SUCCESS_CODES = {"CANDIDATE_READY", "PROMOTED"}
FAILURE_CODES = {
    "DATA_NOT_READY",
    "PROVIDER_AUTH_ERROR",
    "PROVIDER_NETWORK_ERROR",
    "PROVIDER_RATE_LIMITED",
    "INCOMPLETE_UNIVERSE",
    "FIELD_VALIDATION_FAILED",
    "FRESHNESS_GATE_FAILED",
    "PROMOTION_FAILED",
    "ROLLBACK_FAILED",
}


@dataclass(frozen=True)
class PromotionResult:
    code: str
    message: str
    before_manifest_hash: str
    after_manifest_hash: str = ""
    rollback_verified: bool = False
    emergency_restore_succeeded: bool = False


def run_tushare_primary_update(
    project_root: Path,
    config: dict[str, Any],
    trade_date: str,
    *,
    client_factory: Callable[..., Any] | None = None,
    candidate_builder: Callable[..., dict[str, Any]] | None = None,
    rename: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
) -> dict[str, Any]:
    """Build a full 183-file candidate and optionally promote it atomically."""
    root = project_root.resolve()
    requested_date = _normalize_trade_date(trade_date)
    ssot_dir = root / config["universe"]["etf_daily_dir"]
    staging_root = root / config["storage"]["staging_root"]
    expected_count = int(config["universe"]["expected_count"])
    promotion_enabled = bool(config["promotion"].get("formal_promotion_enabled", False))
    base = _base_status(requested_date, promotion_enabled)
    initial_ssot_manifest = directory_manifest(ssot_dir)
    base["ssot_manifest_hash"] = initial_ssot_manifest["manifest_hash"]

    universe, mapping = build_universe_mapping(root, config)
    if (
        not mapping.get("mapping_complete")
        or len(universe) != expected_count
        or int(mapping.get("mapped_count", 0)) != expected_count
    ):
        return _failed(
            base,
            "INCOMPLETE_UNIVERSE",
            f"canonical universe mapping must be {expected_count}/{expected_count}; mapped={len(universe)}",
            mapping=mapping,
        )

    run_id = datetime.now(TZ).strftime("%Y%m%dT%H%M%S%f")
    run_root = staging_root / "runs" / run_id
    manifest_dir = staging_root / "manifests" / run_id
    candidate_dir = run_root / "candidate_etf_daily"
    run_root.mkdir(parents=True, exist_ok=False)
    base.update({
        "run_id": run_id,
        "universe_size": len(universe),
        "processed_symbols": len(universe),
        "mapping_hash": mapping.get("mapping_hash", ""),
        "staging_role": str(config["storage"].get("candidate_role", "EPHEMERAL_NON_SSOT")),
    })

    if config["promotion"].get("require_same_filesystem", True):
        if os.stat(run_root).st_dev != os.stat(ssot_dir.parent).st_dev:
            shutil.rmtree(run_root, ignore_errors=True)
            return _failed(base, "PROMOTION_FAILED", "candidate and SSOT are not on the same filesystem", failure_stage="same_filesystem_gate")

    client = _make_client(root, config, client_factory)
    try:
        call: ProbeCall = client.request(
            str(config["provider"]["interface"]),
            {"trade_date": requested_date.replace("-", "")},
            str(config["provider"]["fields"]),
        )
    except Exception as exc:  # provider boundary must be fail-closed
        shutil.rmtree(run_root, ignore_errors=True)
        code = _exception_code(exc)
        return _failed(base, code, _safe_message(exc, root), actual_api_calls=int(getattr(client, "request_count", 0)))

    base["actual_api_calls"] = int(getattr(client, "request_count", 0))
    base["tushare_api_calls"] = base["actual_api_calls"]
    provider_failure = _provider_failure_code(call)
    if provider_failure:
        shutil.rmtree(run_root, ignore_errors=True)
        return _failed(base, provider_failure, _safe_message(call.error_message_sanitized or call.response_status, root))

    raw_path = run_root / "raw_fund_daily.csv"
    call.frame.to_csv(raw_path, index=False, lineterminator="\n")
    normalized = _normalize_fund_daily(call.frame)
    validated, quality = validate_snapshot(normalized, universe, requested_date)
    base.update({
        "matched_etf_count": int(quality.get("matched_etf_count", 0)),
        "coverage_ratio": float(quality.get("coverage_ratio", 0.0)),
        "source_snapshot_hash": str(quality.get("source_snapshot_hash", "")),
        "quality": quality,
    })

    matched = int(quality.get("matched_etf_count", 0))
    if call.frame.empty or matched < expected_count:
        shutil.rmtree(run_root, ignore_errors=True)
        return _failed(base, "DATA_NOT_READY", f"fund_daily coverage is {matched}/{expected_count}; SSOT preserved")
    if not quality.get("quality_complete"):
        shutil.rmtree(run_root, ignore_errors=True)
        return _failed(base, "FIELD_VALIDATION_FAILED", "fund_daily field validation failed; SSOT preserved")
    if config["freshness_gate"].get("require_exact_trade_date", True) and not quality.get("trade_date_valid"):
        shutil.rmtree(run_root, ignore_errors=True)
        return _failed(base, "FRESHNESS_GATE_FAILED", f"fund_daily rows do not all match requested trade date {requested_date}")

    validated.to_csv(run_root / "validated_snapshot.csv", index=False, lineterminator="\n")
    builder = candidate_builder or build_candidate_directory
    try:
        candidate_meta = builder(ssot_dir, candidate_dir, universe, validated, requested_date)
    except Exception as exc:  # candidate creation is part of the promotion boundary
        shutil.rmtree(run_root, ignore_errors=True)
        return _failed(base, "PROMOTION_FAILED", _safe_message(exc, root), failure_stage="candidate_generation")

    base.update({
        "candidate_file_count": candidate_meta["file_count"],
        "candidate_manifest_hash": candidate_meta["manifest_hash"],
        "candidate_added_rows": candidate_meta["added_rows"],
        "candidate_directory": _relative(candidate_dir, root),
        "up_to_date_count": expected_count,
        "updated_count": expected_count,
    })
    _write_json(run_root / "candidate_manifest.json", candidate_meta)
    _write_json(manifest_dir / "candidate_manifest.json", candidate_meta)

    if not promotion_enabled:
        before = directory_manifest(ssot_dir)
        _write_json(manifest_dir / "before_manifest.json", before)
        return {
            **base,
            "status": "candidate_ready",
            "severity": "NORMAL",
            "result_code": "CANDIDATE_READY",
            "reason": "candidate validated; formal promotion remains disabled by default",
            "latest_local_date": _latest_directory_date(ssot_dir),
            "added_rows": 0,
            "promotion_attempted": False,
            "ssot_changed": False,
            "before_manifest_hash": before["manifest_hash"],
            "after_manifest_hash": before["manifest_hash"],
            "ssot_manifest_hash": before["manifest_hash"],
            "manifest_paths": {
                "before": _relative(manifest_dir / "before_manifest.json", root),
                "candidate": _relative(manifest_dir / "candidate_manifest.json", root),
            },
        }

    promotion = promote_candidate_directory(
        ssot_dir,
        candidate_dir,
        run_root,
        expected_files={Path(item.file_path).name for item in universe},
        expected_candidate_hash=str(candidate_meta["manifest_hash"]),
        manifest_dir=manifest_dir,
        rename=rename,
    )
    if promotion.code != "PROMOTED":
        preserve_recovery = promotion.code == "ROLLBACK_FAILED" and not promotion.emergency_restore_succeeded
        if not preserve_recovery:
            shutil.rmtree(run_root, ignore_errors=True)
        return _failed(
            base,
            promotion.code,
            promotion.message,
            failure_stage="directory_transaction",
            promotion_attempted=True,
            before_manifest_hash=promotion.before_manifest_hash,
            after_manifest_hash=promotion.after_manifest_hash,
            rollback_verified=promotion.rollback_verified,
            emergency_restore_succeeded=promotion.emergency_restore_succeeded,
            ssot_manifest_hash=promotion.after_manifest_hash or promotion.before_manifest_hash,
            manifest_paths={
                "before": _relative(manifest_dir / "before_manifest.json", root),
                "candidate": _relative(manifest_dir / "candidate_manifest.json", root),
                "rollback": _relative(manifest_dir / "rollback_manifest.json", root),
            },
            cleanup_status="PRESERVED_FOR_MANUAL_RECOVERY" if preserve_recovery else "VERIFIED_ROLLBACK_CLEANED",
            recovery_directory=_relative(run_root, root) if preserve_recovery else "",
        )

    _cleanup_transaction_artifacts(run_root)
    return {
        **base,
        "status": "updated",
        "severity": "NORMAL",
        "result_code": "PROMOTED",
        "reason": "complete candidate promoted by directory transaction",
        "latest_local_date": requested_date,
        "added_rows": int(candidate_meta["added_rows"]),
        "promotion_attempted": True,
        "ssot_changed": True,
        "before_manifest_hash": promotion.before_manifest_hash,
        "after_manifest_hash": promotion.after_manifest_hash,
        "ssot_manifest_hash": promotion.after_manifest_hash,
        "updated_count": expected_count,
        "rollback_verified": False,
        "manifest_paths": {
            "before": _relative(manifest_dir / "before_manifest.json", root),
            "candidate": _relative(manifest_dir / "candidate_manifest.json", root),
            "after": _relative(manifest_dir / "after_manifest.json", root),
        },
    }


def build_candidate_directory(
    ssot_dir: Path,
    candidate_dir: Path,
    universe: list[UniverseRecord],
    snapshot: pd.DataFrame,
    trade_date: str,
) -> dict[str, Any]:
    """Create a complete candidate copy, then merge one validated daily row per ETF."""
    shutil.copytree(ssot_dir, candidate_dir)
    by_code = snapshot.set_index("ts_code")
    added_rows = 0
    for item in universe:
        path = candidate_dir / Path(item.file_path).name
        local = pd.read_csv(path, dtype={"date": str, "code": str})
        if list(local.columns) != FORMAL_COLUMNS:
            raise ValueError(f"formal CSV schema mismatch: {path.name}")
        row = _formal_row(item, by_code.loc[item.ts_code], trade_date)
        existed = bool((local["date"].astype(str) == trade_date).any())
        local = local[local["date"].astype(str) != trade_date]
        merged = pd.concat([local, pd.DataFrame([row], columns=FORMAL_COLUMNS)], ignore_index=True)
        merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        if merged["date"].isna().any() or merged["date"].duplicated().any():
            raise ValueError(f"candidate date validation failed: {path.name}")
        merged = merged.sort_values("date", kind="mergesort")
        merged.to_csv(path, index=False, lineterminator="\n")
        if not existed:
            added_rows += 1

    expected_files = {Path(item.file_path).name for item in universe}
    manifest = validate_candidate_directory(candidate_dir, expected_files, trade_date)
    manifest["added_rows"] = added_rows
    return manifest


def validate_candidate_directory(candidate_dir: Path, expected_files: set[str], trade_date: str) -> dict[str, Any]:
    actual_files = {path.name for path in candidate_dir.glob("*.csv")}
    if actual_files != expected_files:
        raise ValueError(f"candidate inventory mismatch: actual={len(actual_files)} expected={len(expected_files)}")
    for name in sorted(expected_files):
        frame = pd.read_csv(candidate_dir / name, dtype={"date": str, "code": str})
        if list(frame.columns) != FORMAL_COLUMNS:
            raise ValueError(f"candidate field validation failed: {name}")
        if len(frame) == 0 or frame["date"].duplicated().any() or trade_date not in set(frame["date"].astype(str)):
            raise ValueError(f"candidate freshness validation failed: {name}")
        numeric = frame[["open", "high", "low", "close", "volume", "amount"]].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or (numeric[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError(f"candidate numeric validation failed: {name}")
    return directory_manifest(candidate_dir)


def promote_candidate_directory(
    ssot_dir: Path,
    candidate_dir: Path,
    run_root: Path,
    *,
    expected_files: set[str],
    expected_candidate_hash: str,
    manifest_dir: Path | None = None,
    rename: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
) -> PromotionResult:
    """Swap whole directories and restore the old directory on any failure."""
    before = directory_manifest(ssot_dir)
    evidence_dir = manifest_dir or run_root
    before_path = evidence_dir / "before_manifest.json"
    _write_json(before_path, before)
    if not before_path.is_file():
        return PromotionResult("PROMOTION_FAILED", "before manifest was not persisted", before["manifest_hash"])

    backup_dir = run_root / "ssot_before_backup"
    failed_dir = run_root / "failed_promoted_candidate"
    moved_old = False
    try:
        rename(ssot_dir, backup_dir)
        moved_old = True
        rename(candidate_dir, ssot_dir)
        after = directory_manifest(ssot_dir)
        if after["manifest_hash"] != expected_candidate_hash or set(after["files"]) != expected_files:
            raise RuntimeError("promoted candidate manifest verification failed")
        _write_json(evidence_dir / "after_manifest.json", after)
        shutil.rmtree(backup_dir)
        return PromotionResult("PROMOTED", "directory transaction completed", before["manifest_hash"], after["manifest_hash"])
    except Exception as promotion_exc:  # rollback is mandatory once the old directory moved
        if not moved_old:
            return PromotionResult("PROMOTION_FAILED", sanitize_message(str(promotion_exc)), before["manifest_hash"], before["manifest_hash"])
        try:
            if ssot_dir.exists():
                rename(ssot_dir, failed_dir)
            rename(backup_dir, ssot_dir)
            restored = directory_manifest(ssot_dir)
            _write_json(evidence_dir / "rollback_manifest.json", restored)
            verified = restored["manifest_hash"] == before["manifest_hash"] and set(restored["files"]) == expected_files
            if not verified:
                return PromotionResult("ROLLBACK_FAILED", "rollback manifest verification failed", before["manifest_hash"], restored["manifest_hash"], False)
            if failed_dir.exists():
                shutil.rmtree(failed_dir)
            return PromotionResult("PROMOTION_FAILED", sanitize_message(str(promotion_exc)), before["manifest_hash"], restored["manifest_hash"], True)
        except Exception as rollback_exc:
            emergency_ok, restored_hash = _emergency_restore(backup_dir, ssot_dir, failed_dir, before, expected_files)
            if ssot_dir.exists():
                _write_json(evidence_dir / "rollback_manifest.json", directory_manifest(ssot_dir))
            message = f"rollback failed: {sanitize_message(str(rollback_exc))}"
            return PromotionResult("ROLLBACK_FAILED", message, before["manifest_hash"], restored_hash, emergency_ok, emergency_ok)


def directory_manifest(directory: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in sorted(directory.glob("*.csv")):
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "file_count": len(files),
        "files": files,
        "manifest_hash": hashlib.sha256(canonical).hexdigest(),
    }


def _make_client(project_root: Path, config: dict[str, Any], factory: Callable[..., Any] | None) -> Any:
    provider = config["provider"]
    maker = factory or TushareMinimalClient
    return maker(
        project_root=project_root,
        max_requests=int(provider["max_requests"]),
        timeout_seconds=int(provider["timeout_seconds"]),
        request_interval_seconds=float(provider["request_interval_seconds"]),
        max_network_retries=int(provider["max_network_retries"]),
    )


def _normalize_fund_daily(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for field in SNAPSHOT_FIELDS:
        if field not in normalized:
            normalized[field] = pd.NA
    normalized["ts_code"] = normalized["ts_code"].astype(str).str.strip().str.upper()
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"].astype(str), errors="coerce").dt.strftime("%Y-%m-%d")
    for field in SNAPSHOT_FIELDS[2:]:
        normalized[field] = pd.to_numeric(normalized[field], errors="coerce")
    return normalized[list(SNAPSHOT_FIELDS)]


def _formal_row(item: UniverseRecord, row: pd.Series, trade_date: str) -> dict[str, Any]:
    return {
        "date": trade_date,
        "code": f"{item.exchange.lower()}.{item.etf_code}",
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "preclose": row["pre_close"],
        "volume": float(row["vol"]) * 100.0,
        "amount": float(row["amount"]) * 1000.0,
        "adjustflag": "3",
        "turn": "",
        "tradestatus": "1",
        "pctChg": row["pct_chg"],
        "isST": "1",
    }


def _provider_failure_code(call: ProbeCall) -> str:
    status = str(call.response_status).upper()
    message = str(call.error_message_sanitized).lower()
    if status in {"ACCESS_PASS", "MOCK_RESPONSE_PASS"}:
        return ""
    if status in {"EMPTY_UNEXPECTED", "MOCK_EMPTY"}:
        return "DATA_NOT_READY"
    if status in {"BLOCKED_TOKEN_MISSING", "PERMISSION_BLOCKED"}:
        return "PROVIDER_AUTH_ERROR"
    if status == "NETWORK_FAILED":
        return "PROVIDER_NETWORK_ERROR"
    if any(marker in message for marker in ("rate limit", "too many", "频率", "每分钟", "每小时", "请求次数")):
        return "PROVIDER_RATE_LIMITED"
    if status in {"VALIDATION_FAILED", "MOCK_RESPONSE_MISSING"}:
        return "PROVIDER_AUTH_ERROR" if "token" in message else "PROVIDER_RATE_LIMITED" if "limit" in message else "FIELD_VALIDATION_FAILED"
    return "PROVIDER_NETWORK_ERROR"


def _exception_code(exc: Exception) -> str:
    message = str(exc).lower()
    if any(marker in message for marker in ("rate", "budget", "too many", "频率", "请求次数")):
        return "PROVIDER_RATE_LIMITED"
    if any(marker in message for marker in ("token", "auth", "permission", "权限")):
        return "PROVIDER_AUTH_ERROR"
    return "PROVIDER_NETWORK_ERROR"


def _emergency_restore(
    backup_dir: Path,
    ssot_dir: Path,
    failed_dir: Path,
    before: dict[str, Any],
    expected_files: set[str],
) -> tuple[bool, str]:
    emergency_failed = failed_dir.with_name(f"{failed_dir.name}_emergency")
    try:
        if ssot_dir.exists():
            os.replace(ssot_dir, emergency_failed)
        if backup_dir.exists():
            os.replace(backup_dir, ssot_dir)
        restored = directory_manifest(ssot_dir)
        ok = restored["manifest_hash"] == before["manifest_hash"] and set(restored["files"]) == expected_files
        if ok:
            if emergency_failed.exists():
                shutil.rmtree(emergency_failed)
            if failed_dir.exists():
                shutil.rmtree(failed_dir)
        return ok, restored["manifest_hash"]
    except Exception:
        return False, directory_manifest(ssot_dir)["manifest_hash"] if ssot_dir.exists() else ""


def _cleanup_transaction_artifacts(run_root: Path) -> None:
    for name in ("ssot_before_backup", "failed_promoted_candidate"):
        path = run_root / name
        if path.exists():
            shutil.rmtree(path)


def _base_status(trade_date: str, promotion_enabled: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "provider": "TUSHARE",
        "actual_source_used": "TUSHARE",
        "primary_upstream": "TUSHARE",
        "baostock_role": "RECONCILIATION_ONLY",
        "jqdata_fallback": "DISABLED",
        "fallback_triggered": False,
        "requested_end": trade_date,
        "business_date": trade_date,
        "promotion_enabled": promotion_enabled,
        "promotion_attempted": False,
        "ssot_changed": False,
        "actual_api_calls": 0,
        "tushare_api_calls": 0,
        "baostock_api_calls": 0,
        "jqdata_api_calls": 0,
        "added_rows": 0,
        "updated_count": 0,
        "up_to_date_count": 0,
    }


def _failed(base: dict[str, Any], code: str, reason: str, **extra: Any) -> dict[str, Any]:
    if code not in FAILURE_CODES:
        raise ValueError(f"unsupported failure code: {code}")
    return {
        **base,
        **extra,
        "status": "failed",
        "severity": "ERROR",
        "result_code": code,
        "reason": reason,
        "added_rows": 0,
        "ssot_changed": False,
    }


def _latest_directory_date(directory: Path) -> str:
    latest = ""
    for path in directory.glob("*.csv"):
        try:
            frame = pd.read_csv(path, usecols=["date"], dtype=str)
            if not frame.empty:
                latest = max(latest, str(frame["date"].max()))
        except Exception:
            continue
    return latest


def _normalize_trade_date(value: str) -> str:
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"invalid trade date: {value}")
    return parsed.strftime("%Y-%m-%d")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return "<outside_project_root>"


def _safe_message(value: Any, root: Path) -> str:
    text = sanitize_message(str(value))
    text = text.replace(str(root), "<project_root>")
    return re.sub(r"/Users/[^/\s]+", "<user_home>", text)[:500]
