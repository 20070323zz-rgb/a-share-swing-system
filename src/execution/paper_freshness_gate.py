"""Preflight freshness checks for the existing paper trade engine.

This module is deliberately independent from strategy and execution logic. It
reads the engine's current inputs, decides whether execution may proceed, and
writes append-only audit evidence. It never writes paper trades or positions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
import uuid
from zoneinfo import ZoneInfo


PASS = "PASS"
BLOCKED_STALE_MARKET_DATA = "BLOCKED_STALE_MARKET_DATA"
BLOCKED_UPDATE_FAILURE = "BLOCKED_UPDATE_FAILURE"
BLOCKED_PENDING_DATA = "BLOCKED_PENDING_DATA"
BLOCKED_INCOMPLETE_COVERAGE = "BLOCKED_INCOMPLETE_COVERAGE"
BLOCKED_STALE_SIGNAL = "BLOCKED_STALE_SIGNAL"
BLOCKED_STALE_RANKING = "BLOCKED_STALE_RANKING"
BLOCKED_MISSING_SYMBOL_BAR = "BLOCKED_MISSING_SYMBOL_BAR"
BLOCKED_INVALID_INPUT = "BLOCKED_INVALID_INPUT"
SKIPPED_NON_TRADING_DAY = "SKIPPED_NON_TRADING_DAY"

GATE_STATUSES = {
    PASS,
    BLOCKED_STALE_MARKET_DATA,
    BLOCKED_UPDATE_FAILURE,
    BLOCKED_PENDING_DATA,
    BLOCKED_INCOMPLETE_COVERAGE,
    BLOCKED_STALE_SIGNAL,
    BLOCKED_STALE_RANKING,
    BLOCKED_MISSING_SYMBOL_BAR,
    BLOCKED_INVALID_INPUT,
    SKIPPED_NON_TRADING_DAY,
}

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


@dataclass(frozen=True)
class GatePaths:
    project_root: Path
    data_update_status: Path
    data_coverage_report: Path
    data_health_report: Path
    signal_file: Path
    ranking_file: Path
    sell_review_file: Path
    watchlist_file: Path
    positions_file: Path
    trades_file: Path
    etf_daily_dir: Path
    calendar_file: Path
    preflight_json: Path
    preflight_md: Path
    audit_jsonl: Path

    @classmethod
    def from_root(cls, project_root: Path) -> "GatePaths":
        root = project_root.resolve()
        return cls(
            project_root=root,
            data_update_status=root / "reports" / "data_update_status.json",
            data_coverage_report=root / "reports" / "data_coverage_report.md",
            data_health_report=root / "reports" / "latest_data_health.md",
            signal_file=root / "reports" / "signals.csv",
            ranking_file=root / "reports" / "buy_signal_ranking.md",
            sell_review_file=root / "reports" / "sell_signal_review.csv",
            watchlist_file=root / "watchlist.csv",
            positions_file=root / "data" / "paper_positions.csv",
            trades_file=root / "data" / "paper_trades.csv",
            etf_daily_dir=root / "data" / "etf_daily",
            calendar_file=root / "data" / "etf_daily" / "sh_510300.csv",
            preflight_json=root / "reports" / "paper_execution_preflight.json",
            preflight_md=root / "reports" / "paper_execution_preflight.md",
            audit_jsonl=root / "data" / "audit" / "paper_execution_audit.jsonl",
        )


def evaluate_freshness_gate(paths: GatePaths, expected_trade_date: date) -> dict[str, Any]:
    """Evaluate all preflight conditions without writing execution files."""
    timestamp = datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds")
    run_id = str(uuid.uuid4())
    expected = expected_trade_date.isoformat()
    payload: dict[str, Any] = {
        "schema_version": 1,
        "audit_type": "paper_execution_preflight",
        "run_id": run_id,
        "execution_timestamp": timestamp,
        "expected_trade_date": expected,
        "latest_data_date": "",
        "signal_date": "",
        "ranking_date": "",
        "required_symbol_count": 0,
        "covered_symbol_count": 0,
        "failed_count": 0,
        "pending_count": 0,
        "gate_status": BLOCKED_INVALID_INPUT,
        "blocking_reasons": [],
        "engine_invoked": False,
        "engine_mode": "not_requested",
        "engine_exit_code": None,
        "calendar_source": _relative(paths.calendar_file, paths.project_root),
        "calendar_last_date": "",
        "calendar_decision": "",
        "required_symbols": [],
        "proposed_trade_symbols": [],
        "covered_symbols": [],
        "missing_required_symbols": [],
        "missing_proposed_trade_symbols": [],
        "signal_sources": {},
        "input_errors": [],
        "checks": {},
        "safety": {
            "paper_trade_engine_changed": False,
            "paper_trades_changed": False,
            "paper_positions_changed": False,
            "broker_api": False,
            "real_order": False,
            "stale_data_fallback": False,
        },
    }

    calendar_dates, calendar_errors = _load_calendar_dates(paths.calendar_file)
    if calendar_errors:
        return _finish_invalid(payload, calendar_errors)
    calendar_last = max(calendar_dates)
    payload["calendar_last_date"] = calendar_last.isoformat()
    is_trading_day, calendar_decision = _is_expected_trading_day(expected_trade_date, calendar_dates)
    payload["calendar_decision"] = calendar_decision
    payload["checks"]["trading_day"] = is_trading_day
    if not is_trading_day:
        payload["gate_status"] = SKIPPED_NON_TRADING_DAY
        payload["blocking_reasons"] = [f"{expected} is not a trading day according to the local benchmark calendar"]
        return payload

    input_errors: list[str] = []
    update_status = _read_json(paths.data_update_status, input_errors, "data_update_status")
    watchlist_rows = _read_csv(paths.watchlist_file, input_errors, "watchlist")
    signal_rows = _read_csv(paths.signal_file, input_errors, "signals")
    sell_review_rows = _read_csv(paths.sell_review_file, input_errors, "sell_review")
    position_rows = _read_csv(paths.positions_file, input_errors, "paper_positions")
    trade_rows = _read_csv(paths.trades_file, input_errors, "paper_trades")
    ranking_date, ranking_rows, ranking_errors = _read_ranking(paths.ranking_file)
    input_errors.extend(ranking_errors)
    input_errors.extend(_validate_markdown_input(paths.data_coverage_report, "data_coverage_report"))
    input_errors.extend(_validate_markdown_input(paths.data_health_report, "data_health_report"))
    if not paths.etf_daily_dir.is_dir():
        input_errors.append(f"etf_daily directory missing: {paths.etf_daily_dir}")

    input_errors.extend(_require_columns(watchlist_rows, {"code", "type", "enabled", "role"}, "watchlist"))
    input_errors.extend(_require_columns(signal_rows, {"date", "code", "signal"}, "signals"))
    input_errors.extend(_require_columns(sell_review_rows, {"review_date", "symbol", "sell_review_status"}, "sell_review"))
    input_errors.extend(_require_columns(position_rows, {"symbol", "quantity"}, "paper_positions"))
    input_errors.extend(_require_columns(trade_rows, {"date", "symbol", "action"}, "paper_trades"))

    latest_data_date = str(update_status.get("latest_data_date") or update_status.get("latest_local_date") or "")
    failed_count = _safe_nonnegative_int(update_status.get("failed_count"), "failed_count", input_errors)
    pending_count = _safe_nonnegative_int(update_status.get("pending_count"), "pending_count", input_errors)
    if not _is_iso_date(latest_data_date):
        input_errors.append("data_update_status latest_data_date/latest_local_date is missing or invalid")
    payload["latest_data_date"] = latest_data_date
    payload["failed_count"] = failed_count
    payload["pending_count"] = pending_count

    signal_sources = {
        "signals_csv": _max_iso_date(row.get("date", "") for row in signal_rows),
        "sell_review_csv": _max_iso_date(row.get("review_date", "") for row in sell_review_rows),
    }
    active_signal_dates = [value for value in signal_sources.values() if value]
    signal_date = min(active_signal_dates) if active_signal_dates else ""
    if not signal_date:
        input_errors.append("no valid signal date found in signals.csv or sell_signal_review.csv")
    if any(str(row.get("symbol", "")).strip() for row in position_rows) and not signal_sources["sell_review_csv"]:
        input_errors.append("positions exist but sell_signal_review.csv has no dated rows")
    payload["signal_sources"] = signal_sources
    payload["signal_date"] = signal_date
    payload["ranking_date"] = ranking_date

    formal_universe = _formal_execution_universe(watchlist_rows)
    held_symbols = _unique_codes(row.get("symbol", "") for row in position_rows)
    ranked_symbols = _ranking_symbols(ranking_rows, limit=3)
    proposed_symbols = sorted(set(held_symbols) | set(ranked_symbols))
    required_symbols = sorted(set(formal_universe) | set(proposed_symbols))
    payload["required_symbols"] = required_symbols
    payload["proposed_trade_symbols"] = proposed_symbols
    payload["required_symbol_count"] = len(required_symbols)
    if not formal_universe:
        input_errors.append("formal execution universe resolved to zero ETF symbols")

    covered_symbols: list[str] = []
    missing_symbols: list[str] = []
    bar_errors: list[str] = []
    for symbol in required_symbols:
        has_bar, error = _has_valid_bar(paths.etf_daily_dir, symbol, expected)
        if has_bar:
            covered_symbols.append(symbol)
        else:
            missing_symbols.append(symbol)
            if error:
                bar_errors.append(error)
    missing_proposed = sorted(set(missing_symbols) & set(proposed_symbols))
    missing_required = sorted(set(missing_symbols) - set(missing_proposed))
    payload["covered_symbols"] = covered_symbols
    payload["covered_symbol_count"] = len(covered_symbols)
    payload["missing_required_symbols"] = missing_required
    payload["missing_proposed_trade_symbols"] = missing_proposed
    payload["bar_errors"] = bar_errors

    if input_errors:
        return _finish_invalid(payload, input_errors)

    checks = {
        "trading_day": True,
        "latest_data_date_matches": latest_data_date == expected,
        "failed_count_zero": failed_count == 0,
        "pending_count_zero": pending_count == 0,
        "required_universe_coverage_complete": not missing_required and not missing_proposed and len(covered_symbols) == len(required_symbols),
        "signal_date_matches": signal_date == expected and all(value == expected for value in active_signal_dates),
        "ranking_date_matches": ranking_date == expected,
        "proposed_trade_bars_complete": not missing_proposed,
        "critical_inputs_valid": True,
    }
    payload["checks"] = checks

    failures: list[tuple[str, str]] = []
    if failed_count:
        failures.append((BLOCKED_UPDATE_FAILURE, f"data update failed_count={failed_count}"))
    if pending_count:
        failures.append((BLOCKED_PENDING_DATA, f"data update pending_count={pending_count}"))
    if latest_data_date != expected:
        failures.append((BLOCKED_STALE_MARKET_DATA, f"latest_data_date={latest_data_date}, expected={expected}"))
    if missing_proposed:
        failures.append((BLOCKED_MISSING_SYMBOL_BAR, f"proposed symbols missing valid {expected} bars: {', '.join(missing_proposed)}"))
    if missing_required:
        failures.append((BLOCKED_INCOMPLETE_COVERAGE, f"formal universe symbols missing valid {expected} bars: {', '.join(missing_required)}"))
    if signal_date != expected or any(value != expected for value in active_signal_dates):
        detail = ", ".join(f"{key}={value or 'missing'}" for key, value in signal_sources.items())
        failures.append((BLOCKED_STALE_SIGNAL, f"signal sources do not match {expected}: {detail}"))
    if ranking_date != expected:
        failures.append((BLOCKED_STALE_RANKING, f"ranking_date={ranking_date}, expected={expected}"))

    if failures:
        payload["gate_status"] = failures[0][0]
        payload["blocking_reasons"] = [reason for _, reason in failures]
    else:
        payload["gate_status"] = PASS
        payload["blocking_reasons"] = []
    return payload


def write_preflight_outputs(payload: dict[str, Any], paths: GatePaths, *, append_audit: bool = True) -> None:
    """Write current preflight snapshots and one append-only audit record."""
    paths.preflight_json.parent.mkdir(parents=True, exist_ok=True)
    paths.audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
    paths.preflight_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths.preflight_md.write_text(render_preflight_markdown(payload), encoding="utf-8")
    if append_audit:
        _append_jsonl(paths.audit_jsonl, payload)


def render_preflight_markdown(payload: dict[str, Any]) -> str:
    reasons = payload.get("blocking_reasons") or []
    checks = payload.get("checks") or {}
    lines = [
        "# Paper Execution Preflight",
        "",
        f"- run_id: `{payload.get('run_id', '')}`",
        f"- execution_timestamp: `{payload.get('execution_timestamp', '')}`",
        f"- expected_trade_date: `{payload.get('expected_trade_date', '')}`",
        f"- gate_status: `{payload.get('gate_status', '')}`",
        f"- engine_invoked: `{str(bool(payload.get('engine_invoked'))).lower()}`",
        f"- engine_mode: `{payload.get('engine_mode', '')}`",
        "",
        "## Freshness Snapshot",
        "",
        f"- latest_data_date: `{payload.get('latest_data_date') or 'N/A'}`",
        f"- signal_date: `{payload.get('signal_date') or 'N/A'}`",
        f"- ranking_date: `{payload.get('ranking_date') or 'N/A'}`",
        f"- failed_count: `{payload.get('failed_count', 0)}`",
        f"- pending_count: `{payload.get('pending_count', 0)}`",
        f"- coverage: `{payload.get('covered_symbol_count', 0)}/{payload.get('required_symbol_count', 0)}`",
        f"- calendar: `{payload.get('calendar_decision', '')}` via `{payload.get('calendar_source', '')}`",
        "",
        "## Checks",
        "",
    ]
    if checks:
        for name, passed in checks.items():
            lines.append(f"- {name}: `{'PASS' if passed else 'FAIL'}`")
    else:
        lines.append("- No condition checks were required after the calendar decision.")
    lines.extend(["", "## Blocking Reasons", ""])
    lines.extend(f"- {reason}" for reason in reasons)
    if not reasons:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Missing Coverage",
            "",
            f"- formal universe: `{', '.join(payload.get('missing_required_symbols') or []) or 'none'}`",
            f"- proposed trades: `{', '.join(payload.get('missing_proposed_trade_symbols') or []) or 'none'}`",
            "",
            "## Safety Boundary",
            "",
            "- A non-PASS result never invokes the paper trade engine.",
            "- Prior-day market data is never used as an automatic fallback.",
            "- This preflight does not modify paper trades, positions, strategy, ranking, or score.",
        ]
    )
    return "\n".join(lines) + "\n"


def audit_historical_stale_trades(paths: GatePaths, audit_date: date) -> list[dict[str, Any]]:
    """Append idempotent, non-destructive stale-price audit records."""
    trade_date = audit_date.isoformat()
    errors: list[str] = []
    trades = _read_csv(paths.trades_file, errors, "paper_trades")
    if errors:
        raise ValueError("; ".join(errors))
    existing_ids = _existing_audit_ids(paths.audit_jsonl)
    records: list[dict[str, Any]] = []
    for row in trades:
        row_date = str(row.get("trade_date") or row.get("date") or "")[:10]
        if row_date != trade_date or str(row.get("source", "")) != "paper_trade_engine":
            continue
        symbol = str(row.get("symbol", "")).strip()
        raw_close = _safe_float(row.get("raw_close"))
        actual_close = _close_for_date(paths.etf_daily_dir, symbol, trade_date)
        if not symbol or raw_close <= 0 or actual_close <= 0 or abs(raw_close - actual_close) < 1e-12:
            continue
        audit_id = _audit_id(trade_date, symbol, str(row.get("action", "")), str(row.get("created_at", "")), raw_close)
        record = {
            "schema_version": 1,
            "audit_type": "historical_stale_trade",
            "audit_id": audit_id,
            "execution_timestamp": datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds"),
            "trade_date": trade_date,
            "symbol": symbol,
            "name": str(row.get("name", "")),
            "action": str(row.get("action", "")),
            "quantity": _safe_int(row.get("quantity")),
            "original_execution_price": _safe_float(row.get("execution_price") or row.get("price")),
            "original_raw_close": raw_close,
            "official_close": actual_close,
            "raw_close_difference_ratio": raw_close / actual_close - 1.0,
            "audit_status": "AUDITED_STALE_PRICE_NON_DESTRUCTIVE",
            "reason": f"paper execution used raw_close from before the unified ETF database contained the {trade_date} bar",
            "replacement_execution_written": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
            "source_trade_created_at": str(row.get("created_at", "")),
        }
        records.append(record)
        if audit_id not in existing_ids:
            paths.audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
            _append_jsonl(paths.audit_jsonl, record)
            existing_ids.add(audit_id)
    return records


def write_historical_audit_report(records: list[dict[str, Any]], paths: GatePaths, audit_date: date) -> tuple[Path, Path]:
    report_json = paths.project_root / "reports" / f"paper_execution_stale_trade_audit_{audit_date.isoformat()}.json"
    report_md = paths.project_root / "reports" / f"paper_execution_stale_trade_audit_{audit_date.isoformat()}.md"
    report_payload = {
        "schema_version": 1,
        "audit_date": audit_date.isoformat(),
        "audit_status": "AUDITED_NON_DESTRUCTIVELY",
        "record_count": len(records),
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "replacement_execution_written": False,
        "records": records,
    }
    report_json.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Paper Execution Stale Trade Audit {audit_date.isoformat()}",
        "",
        "Audit mode: non-destructive. Original paper trades and positions are unchanged.",
        "",
        "| symbol | action | quantity | original raw_close | official close | difference | status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in records:
        lines.append(
            f"| {row['symbol']} | {row['action']} | {row['quantity']} | {row['original_raw_close']:.6f} | "
            f"{row['official_close']:.6f} | {row['raw_close_difference_ratio']:.2%} | {row['audit_status']} |"
        )
    if not records:
        lines.append("|  |  | 0 | 0 | 0 | 0 | NO_STALE_TRADES_FOUND |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No replacement execution was calculated or written.",
            "- `data/paper_trades.csv` was not modified.",
            "- `data/paper_positions.csv` was not modified.",
            "- A future correction policy requires separate Main approval.",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_json, report_md


def _finish_invalid(payload: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    payload["input_errors"] = errors
    payload["gate_status"] = BLOCKED_INVALID_INPUT
    payload["blocking_reasons"] = errors
    payload["checks"]["critical_inputs_valid"] = False
    return payload


def _load_calendar_dates(path: Path) -> tuple[set[date], list[str]]:
    errors: list[str] = []
    rows = _read_csv(path, errors, "trading_calendar")
    if errors:
        return set(), errors
    if not rows or "date" not in rows[0]:
        return set(), [f"trading calendar has no date column: {path}"]
    dates = {_parse_iso_date(str(row.get("date", ""))) for row in rows}
    valid_dates = {value for value in dates if value is not None}
    if not valid_dates:
        errors.append(f"trading calendar contains no valid dates: {path}")
    return valid_dates, errors


def _is_expected_trading_day(target: date, calendar_dates: set[date]) -> tuple[bool, str]:
    if target in calendar_dates:
        return True, "confirmed_by_local_510300_calendar"
    latest = max(calendar_dates)
    if target <= latest:
        return False, "absent_from_historical_local_510300_calendar"
    if target.weekday() >= 5:
        return False, "future_weekend_after_local_calendar"
    return True, "conservative_future_weekday_requires_fresh_data"


def _formal_execution_universe(rows: list[dict[str, str]]) -> list[str]:
    symbols = []
    for row in rows:
        if str(row.get("type", "")).upper() != "ETF":
            continue
        if str(row.get("role", "")).strip() != "trade_pool":
            continue
        if not _truthy(row.get("enabled", "")):
            continue
        code = str(row.get("code", "")).strip()
        if code:
            symbols.append(code)
    return sorted(set(symbols))


def _ranking_symbols(rows: list[dict[str, str]], limit: int) -> list[str]:
    ranked: list[tuple[int, str]] = []
    for row in rows:
        symbol = str(row.get("code", "")).strip()
        if not symbol:
            continue
        rank = _safe_int(row.get("rank")) or 999999
        ranked.append((rank, symbol))
    return [symbol for _, symbol in sorted(ranked)[:limit]]


def _read_ranking(path: Path) -> tuple[str, list[dict[str, str]], list[str]]:
    if not path.exists():
        return "", [], [f"ranking file missing: {path}"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return "", [], [f"ranking file unreadable: {path}: {exc}"]
    title_date = ""
    for line in lines:
        if line.startswith("# "):
            match = DATE_RE.search(line)
            if match:
                title_date = match.group(1)
                break
    headers, rows = _markdown_table(lines, "Top BUY Ranking")
    errors: list[str] = []
    if not _is_iso_date(title_date):
        errors.append(f"ranking title has no valid data date: {path}")
    if not headers:
        errors.append(f"ranking Top BUY Ranking table is missing: {path}")
    elif not {"rank", "code", "mid", "short"}.issubset(headers):
        errors.append(f"ranking table missing required columns: {path}")
    return title_date, rows, errors


def _markdown_table(lines: list[str], section_title: str) -> tuple[set[str], list[dict[str, str]]]:
    in_section = False
    table_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section and table_lines:
                break
            in_section = section_title in line
            continue
        if in_section and line.strip().startswith("|"):
            table_lines.append(line.strip())
        elif in_section and table_lines:
            break
    if len(table_lines) < 3:
        if len(table_lines) == 2:
            headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
            return set(headers), []
        return set(), []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        values = [cell.strip() for cell in line.strip("|").split("|")]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return set(headers), rows


def _has_valid_bar(etf_daily_dir: Path, symbol: str, target: str) -> tuple[bool, str]:
    path = _symbol_path(etf_daily_dir, symbol)
    errors: list[str] = []
    rows = _read_csv(path, errors, f"bar:{symbol}")
    if errors:
        return False, errors[0]
    for row in rows:
        if str(row.get("date", "")) == target and _safe_float(row.get("close")) > 0:
            return True, ""
    return False, f"{symbol} has no valid close for {target} in {path}"


def _close_for_date(etf_daily_dir: Path, symbol: str, target: str) -> float:
    rows = _read_csv(_symbol_path(etf_daily_dir, symbol), [], f"bar:{symbol}")
    for row in rows:
        if str(row.get("date", "")) == target:
            return _safe_float(row.get("close"))
    return 0.0


def _symbol_path(etf_daily_dir: Path, symbol: str) -> Path:
    prefix = "sh" if symbol.startswith(("5", "6")) else "sz"
    return etf_daily_dir / f"{prefix}_{symbol}.csv"


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label} missing: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{label} unreadable: {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object: {path}")
        return {}
    return value


def _read_csv(path: Path, errors: list[str], label: str) -> list[dict[str, str]]:
    if not path.exists():
        errors.append(f"{label} missing: {path}")
        return []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    errors.append(f"{label} has no CSV header: {path}")
                    return []
                rows = [dict(row) for row in reader]
                if not rows:
                    return [{name: "" for name in reader.fieldnames}]
                return rows
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            errors.append(f"{label} unreadable: {path}: {exc}")
            return []
    errors.append(f"{label} encoding unsupported: {path}")
    return []


def _require_columns(rows: list[dict[str, str]], required: set[str], label: str) -> list[str]:
    if not rows:
        return [f"{label} has no readable header"]
    missing = sorted(required - set(rows[0]))
    return [f"{label} missing columns: {', '.join(missing)}"] if missing else []


def _validate_markdown_input(path: Path, label: str) -> list[str]:
    if not path.exists():
        return [f"{label} missing: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"{label} unreadable: {path}: {exc}"]
    if not text.lstrip().startswith("#"):
        return [f"{label} has no Markdown title: {path}"]
    return []


def _safe_nonnegative_int(value: Any, label: str, errors: list[str]) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"data_update_status {label} is missing or invalid")
        return 0
    if parsed < 0:
        errors.append(f"data_update_status {label} cannot be negative")
        return 0
    return parsed


def _max_iso_date(values: Iterable[Any]) -> str:
    valid = [str(value)[:10] for value in values if _is_iso_date(str(value)[:10])]
    return max(valid) if valid else ""


def _is_iso_date(value: str) -> bool:
    return _parse_iso_date(value) is not None


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _unique_codes(values: Iterable[Any]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _existing_audit_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        audit_id = str(payload.get("audit_id", ""))
        if audit_id:
            result.add(audit_id)
    return result


def _audit_id(trade_date: str, symbol: str, action: str, created_at: str, raw_close: float) -> str:
    value = f"{trade_date}|{symbol}|{action}|{created_at}|{raw_close:.10f}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
