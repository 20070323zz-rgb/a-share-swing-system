"""Data source router for daily ETF updates."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd

from data_loader import read_watchlist
from config import ETF_DAILY_DIR, REPORT_DIR, WATCHLIST_FILE
from data_sources.jqdata_source import run_jqdata_update


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_SOURCE_STATUS_FILE = REPORT_DIR / "data_source_status.json"
DATA_SOURCE_STATUS_REPORT = REPORT_DIR / "data_source_status_report.md"


def run_source_update(args: Any, items: pd.DataFrame, start: str, end: str) -> int:
    source = str(args.source)
    primary = str(getattr(args, "primary", "jqdata"))
    fallback = str(getattr(args, "fallback", "baostock"))
    no_fallback = bool(getattr(args, "no_fallback", False))
    validate_only = bool(getattr(args, "validate_only", False))
    dry_run = bool(getattr(args, "dry_run", False))

    if source == "tushare":
        source_status = _base_source_status(actual_source_used="", jqdata_status="SKIPPED", baostock_status="SKIPPED")
        source_status["tushare_status"] = "NOT_IMPLEMENTED"
        _write_source_outputs(source_status)
        return 2

    jq_result: dict[str, Any] | None = None
    fallback_result: dict[str, Any] | None = None
    fallback_triggered = False
    actual_source_used = ""
    exit_code = 0

    if source == "auto" and primary == "baostock":
        fallback_result = _run_baostock_subprocess(args, start, end)
        actual_source_used = "baostock"
        exit_code = _normalized_baostock_exit_code(fallback_result, strict_exit=bool(getattr(args, "strict_exit", False)))
    elif source in {"auto", "jqdata"}:
        jq_result = run_jqdata_update(items, start, end, dry_run=dry_run, validate_only=validate_only, skip_backfill=bool(getattr(args, "skip_backfill", False)))
        if jq_result.get("status") == "OK":
            actual_source_used = "jqdata"
            exit_code = 0
        elif source == "jqdata" or no_fallback:
            actual_source_used = "jqdata"
            exit_code = 2 if jq_result.get("status") == "PARTIAL" else 3
        else:
            fallback_triggered = True

    if ((source == "auto" and fallback_triggered and fallback == "baostock") or source == "baostock") and fallback_result is None:
        fallback_result = _run_baostock_subprocess(args, start, end)
        actual_source_used = "baostock"
        exit_code = _normalized_baostock_exit_code(fallback_result, strict_exit=bool(getattr(args, "strict_exit", False)))

    source_status = _build_source_status(
        source=source,
        primary=primary,
        fallback=fallback,
        actual_source_used=actual_source_used,
        fallback_triggered=fallback_triggered,
        jq_result=jq_result,
        fallback_result=fallback_result,
        validate_only=validate_only,
        exit_code=exit_code,
    )
    _write_source_outputs(source_status)
    _write_update_status(source_status, jq_result, fallback_result, args.status_json)
    return exit_code


def _run_baostock_subprocess(args: Any, start: str, end: str) -> dict[str, Any]:
    status_json = REPORT_DIR / "data_update_status.baostock_fallback.json"
    cmd = [
        sys.executable,
        "scripts/update_etf_data.py",
        "--source",
        "baostock",
        "--all-etf",
        "--skip-existing",
        "--max-api-calls",
        str(args.max_api_calls),
        "--start",
        start,
        "--end",
        end,
        "--adjustflag",
        str(args.adjustflag),
        "--request-timeout",
        str(args.request_timeout),
        "--login-retries",
        str(args.login_retries),
        "--login-retry-delay",
        str(args.login_retry_delay),
        "--retries",
        str(args.retries),
        "--retry-delay",
        str(args.retry_delay),
        "--request-interval",
        str(args.request_interval),
        "--relogin-every",
        str(args.relogin_every),
        "--max-consecutive-failures",
        str(args.max_consecutive_failures),
        "--status-json",
        str(status_json),
    ]
    if getattr(args, "source_ready_probe", False):
        cmd.append("--source-ready-probe")
    if getattr(args, "isolated_queries", False):
        cmd.append("--isolated-queries")
    if args.symbols:
        cmd = [
            sys.executable,
            "scripts/update_etf_data.py",
            "--source",
            "baostock",
            "--symbols",
            *args.symbols,
            "--skip-existing",
            "--max-api-calls",
            str(args.max_api_calls),
            "--start",
            start,
            "--end",
            end,
            "--adjustflag",
            str(args.adjustflag),
            "--request-timeout",
            str(args.request_timeout),
            "--login-retries",
            str(args.login_retries),
            "--login-retry-delay",
            str(args.login_retry_delay),
            "--retries",
            str(args.retries),
            "--retry-delay",
            str(args.retry_delay),
            "--request-interval",
            str(args.request_interval),
            "--relogin-every",
            str(args.relogin_every),
            "--max-consecutive-failures",
            str(args.max_consecutive_failures),
            "--status-json",
            str(status_json),
        ]
        if getattr(args, "source_ready_probe", False):
            cmd.append("--source-ready-probe")
        if getattr(args, "isolated_queries", False):
            cmd.append("--isolated-queries")
    if getattr(args, "skip_backfill", False):
        cmd.append("--skip-backfill")
    if getattr(args, "dry_run", False) or getattr(args, "validate_only", False):
        cmd.append("--dry-run")
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True)
    payload = _read_json(status_json, {})
    payload["exit_code"] = completed.returncode if completed.returncode != 0 else payload.get("exit_code", 0)
    payload["stdout_tail"] = _tail(completed.stdout)
    payload["stderr_tail"] = _tail(completed.stderr)
    return payload


def _normalized_baostock_exit_code(result: dict[str, Any], *, strict_exit: bool) -> int:
    raw_exit_code = int(result.get("exit_code", 0) or 0)
    status = str(result.get("status", "") or "")
    severity = str(result.get("severity", "") or "")
    if not strict_exit and raw_exit_code == 2 and status in {"pending_source_update", "stale_no_new_rows"} and severity == "CAUTION":
        return 0
    return raw_exit_code


def _build_source_status(
    *,
    source: str,
    primary: str,
    fallback: str,
    actual_source_used: str,
    fallback_triggered: bool,
    jq_result: dict[str, Any] | None,
    fallback_result: dict[str, Any] | None,
    validate_only: bool,
    exit_code: int,
) -> dict[str, Any]:
    jq_status = str((jq_result or {}).get("status", "SKIPPED"))
    baostock_status = "SKIPPED"
    if fallback_result:
        baostock_status = "FALLBACK_USED" if fallback_triggered else str(fallback_result.get("status", "OK")).upper()
    latest_date = (fallback_result or {}).get("latest_local_date") or (jq_result or {}).get("latest_data_date") or _latest_local_data_date()
    new_rows = int((fallback_result or {}).get("added_rows", (jq_result or {}).get("new_rows", 0)) or 0)
    failed_symbols = list((jq_result or {}).get("failed_symbols", []))
    pending_symbols = list((jq_result or {}).get("pending_symbols", []))
    if fallback_result and fallback_result.get("pending_symbols"):
        pending_symbols.extend(fallback_result.get("pending_symbols", []))
    fallback_pending_count = int((fallback_result or {}).get("pending_count", 0) or 0)
    unresolved_symbols = list((jq_result or {}).get("unresolved_symbols", []))
    if fallback_result and fallback_result.get("failed_symbols"):
        failed_symbols.extend(fallback_result.get("failed_symbols", []))
    source_priority = _source_priority(primary, fallback)
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_priority": source_priority,
        "requested_source": source,
        "primary_source": primary,
        "fallback_source": fallback,
        "actual_source_used": actual_source_used or "none",
        "fallback_triggered": fallback_triggered,
        "jqdata_status": jq_status,
        "jqdata_message": (jq_result or {}).get("message", ""),
        "baostock_status": baostock_status,
        "baostock_message": (fallback_result or {}).get("reason", ""),
        "latest_data_date": latest_date,
        "new_rows": new_rows,
        "failed_count": len(set(failed_symbols)),
        "failed_symbols": sorted(set(str(x) for x in failed_symbols if str(x))),
        "pending_count": max(len(set(pending_symbols)), fallback_pending_count),
        "pending_symbols": sorted(set(str(x) for x in pending_symbols if str(x))),
        "updated_symbols": (jq_result or {}).get("updated_symbols", []),
        "skipped_symbols": (jq_result or {}).get("skipped_symbols", []),
        "unresolved_symbols": sorted(set(str(x) for x in unresolved_symbols if str(x))),
        "validate_only": validate_only,
        "exit_code": exit_code,
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "credentials_logged": False,
            "credentials_saved_to_code": False,
            "staging_first": True,
            "local_existing_rows_priority": True,
        },
    }


def _write_update_status(source_status: dict[str, Any], jq_result: dict[str, Any] | None, fallback_result: dict[str, Any] | None, status_json: str) -> None:
    if fallback_result:
        update = dict(fallback_result)
        update["raw_source_exit_code"] = update.get("exit_code", 0)
    else:
        update = {
            "generated_at": source_status["generated_at"],
            "source": "jqdata",
            "mode": "validate-only" if source_status.get("validate_only") else "formal update",
            "status": "updated" if source_status.get("jqdata_status") == "OK" else "failed",
            "severity": "OK" if source_status.get("jqdata_status") == "OK" else "ERROR",
            "reason": source_status.get("jqdata_message", ""),
            "latest_local_date": source_status.get("latest_data_date"),
            "added_rows": source_status.get("new_rows", 0),
            "failed_count": source_status.get("failed_count", 0),
            "status_counts": {},
            "baostock_api_calls": 0,
        }
    final_pending_symbols = list(update.get("pending_symbols", []))
    jqdata_pending_symbols = list(source_status.get("pending_symbols", []))
    update.update({
        "latest_data_date": source_status.get("latest_data_date"),
        "new_rows": source_status.get("new_rows", update.get("added_rows", 0)),
        "failed_symbols": source_status.get("failed_symbols", []),
        "pending_symbols": final_pending_symbols,
        "jqdata_pending_symbols": jqdata_pending_symbols,
        "jqdata_pending_count": len(jqdata_pending_symbols),
        "updated_symbols": source_status.get("updated_symbols", []),
        "skipped_symbols": source_status.get("skipped_symbols", []),
        "source_used": source_status.get("actual_source_used"),
        "actual_source_used": source_status.get("actual_source_used"),
        "fallback_triggered": source_status.get("fallback_triggered"),
        "jqdata_status": source_status.get("jqdata_status"),
        "baostock_status": source_status.get("baostock_status"),
        "unresolved_symbols": source_status.get("unresolved_symbols", []),
        "data_sources": source_status,
        "exit_code": source_status.get("exit_code", update.get("exit_code", 0)),
    })
    Path(status_json).parent.mkdir(parents=True, exist_ok=True)
    Path(status_json).write_text(json.dumps(update, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_source_outputs(source_status: dict[str, Any]) -> None:
    DATA_SOURCE_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_SOURCE_STATUS_FILE.write_text(json.dumps(source_status, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# 数据源状态报告 {source_status.get('generated_at', '')}",
        "",
        "本报告只记录行情数据源状态，不包含任何账号密码/token，不接券商 API，不真实下单。",
        "",
        f"- primary_source: {source_status.get('primary_source')}",
        f"- fallback_source: {source_status.get('fallback_source')}",
        f"- actual_source_used: {source_status.get('actual_source_used')}",
        f"- jqdata_status: {source_status.get('jqdata_status')}",
        f"- baostock_status: {source_status.get('baostock_status')}",
        f"- fallback_triggered: {source_status.get('fallback_triggered')}",
        f"- latest_data_date: {source_status.get('latest_data_date')}",
        f"- new_rows: {source_status.get('new_rows')}",
        f"- pending_symbols: {', '.join(source_status.get('pending_symbols', [])) or 'none'}",
        f"- failed_symbols: {', '.join(source_status.get('failed_symbols', [])) or 'none'}",
        f"- unresolved_symbols: {', '.join(source_status.get('unresolved_symbols', [])) or 'none'}",
        "",
        "## 安全边界",
        "",
        "- 不打印 JQData 密码/token",
        "- 不保存账号密码到代码或报告",
        "- staging-first",
        "- 本地原行优先",
    ]
    DATA_SOURCE_STATUS_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _base_source_status(actual_source_used: str, jqdata_status: str, baostock_status: str) -> dict[str, Any]:
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_priority": ["baostock", "jqdata", "tushare"],
        "primary_source": "jqdata",
        "fallback_source": "baostock",
        "actual_source_used": actual_source_used,
        "jqdata_status": jqdata_status,
        "baostock_status": baostock_status,
        "fallback_triggered": False,
        "latest_data_date": _latest_local_data_date(),
        "new_rows": 0,
        "failed_symbols": [],
        "unresolved_symbols": [],
    }


def _source_priority(primary: str, fallback: str) -> list[str]:
    values: list[str] = []
    for value in [primary, fallback, "tushare"]:
        value = str(value or "").strip()
        if value and value != "none" and value not in values:
            values.append(value)
    return values or ["baostock", "jqdata", "tushare"]


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _tail(text: str, limit: int = 1800) -> str:
    return text[-limit:] if len(text) > limit else text


def _latest_local_data_date() -> str:
    latest = ""
    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if dates.empty:
            continue
        candidate = dates.max().strftime("%Y-%m-%d")
        if not latest or candidate > latest:
            latest = candidate
    return latest or "unknown"
