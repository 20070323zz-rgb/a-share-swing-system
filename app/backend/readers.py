"""Read-only adapters over project CSV/JSON/Markdown reports.

This module intentionally uses only local project files. It never talks to a
broker API, never reads real account data, and never touches credentials.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import subprocess
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
LOG_DIR = PROJECT_ROOT / "logs"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
_ETF_INVENTORY_CACHE: dict[str, Any] = {"signature": None, "rows": []}


def read_json(path: Path, default: Any | None = None) -> Any:
    if default is None:
        default = {}
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"warning": f"读取 {path.name} 失败：{exc}"}


def read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                clean = {k: normalize_value(v) for k, v in row.items() if k is not None}
                rows.append(clean)
                if limit and len(rows) >= limit:
                    break
    except Exception:
        return []
    return rows


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text == "" or text.lower() == "nan":
        return None
    for caster in (int, float):
        try:
            if caster is int and ("." in text or "e" in text.lower()):
                continue
            return caster(text)
        except Exception:
            pass
    return text


def _curve_date(row: dict[str, Any]) -> str:
    value = str(row.get("date") or "").strip()
    return value if len(value) == 10 and value[4:5] == "-" and value[7:8] == "-" else ""


def merge_equity_curves(
    backfilled_rows: list[dict[str, Any]] | None,
    original_rows: list[dict[str, Any]] | None,
    dashboard_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Merge equity history by date, with the formal derived curve authoritative.

    Backfilled rows may add early or non-trading-day continuity. Dashboard rows
    are a cache only. Original paper performance rows always win on overlap.
    """
    by_date: dict[str, dict[str, Any]] = {}
    for rows in (backfilled_rows or [], dashboard_rows or [], original_rows or []):
        for row in rows:
            if not isinstance(row, dict):
                continue
            date_key = _curve_date(row)
            if date_key:
                by_date[date_key] = dict(row)
    return [by_date[key] for key in sorted(by_date)]


def build_equity_curve_meta(
    merged_rows: list[dict[str, Any]],
    original_rows: list[dict[str, Any]],
    backfilled_rows: list[dict[str, Any]],
    valuation_date: Any,
) -> dict[str, Any]:
    merged_dates = [_curve_date(row) for row in merged_rows]
    original_dates = {_curve_date(row) for row in original_rows}
    backfilled_dates = {_curve_date(row) for row in backfilled_rows}
    merged_dates = [value for value in merged_dates if value]
    original_dates.discard("")
    backfilled_dates.discard("")
    curve_end = merged_dates[-1] if merged_dates else ""
    valuation = str(valuation_date or "").strip()
    freshness = "fresh" if curve_end and (not valuation or curve_end >= valuation) else "stale"
    backfill_contributes = bool(backfilled_dates - original_dates)
    if original_dates and backfill_contributes:
        source = "merged_backfill_and_original"
        note = "历史缺口使用估算回填，最新及重叠交易日使用正式绩效曲线。"
    elif original_dates:
        source = "original"
        note = "使用正式模拟仓绩效曲线。"
    elif backfilled_dates:
        source = "backfilled_estimated"
        note = "仅有历史回填估算曲线，等待正式绩效数据。"
    else:
        source = "missing"
        note = "暂无可用绩效曲线。"
    return {
        "status": "active" if merged_rows else "missing",
        "freshness_status": freshness,
        "curve_source": source,
        "curve_start_date": merged_dates[0] if merged_dates else "",
        "curve_end_date": curve_end,
        "valuation_as_of_date": valuation,
        "original_records": len(original_rows),
        "backfilled_records": len(backfilled_rows),
        "merged_records": len(merged_rows),
        "estimated": backfill_contributes or not original_dates,
        "app_uses_backfilled_curve": backfill_contributes,
        "display_note": note,
    }


def tail_text(path: Path, max_lines: int = 200) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return f"读取日志失败：{exc}"
    return "\n".join(lines[-max_lines:])


def dashboard_data() -> dict[str, Any]:
    data = read_json(REPORT_DIR / "dashboard_data.json", {})
    if not data:
        return {"warning": "reports/dashboard_data.json 缺失或为空"}
    return data


def data_update_status() -> dict[str, Any]:
    return read_json(REPORT_DIR / "data_update_status.json", {})


def data_source_status() -> dict[str, Any]:
    data = dashboard_data()
    source_status = read_json(REPORT_DIR / "data_source_status.json", {})
    return source_status or data.get("data_sources", {}) or {}


def etf_inventory_snapshot() -> list[dict[str, Any]]:
    """Return a cached read-only inventory over the existing ETF daily CSV store."""
    files = sorted(ETF_DAILY_DIR.glob("*.csv"))
    signature = tuple((path.name, path.stat().st_mtime_ns, path.stat().st_size) for path in files)
    if signature == _ETF_INVENTORY_CACHE.get("signature"):
        return list(_ETF_INVENTORY_CACHE.get("rows", []))

    classification_rows = read_csv_rows(DATA_DIR / "etf_type_classification.csv")
    classification = {
        str(row.get("symbol") or row.get("code")): row
        for row in classification_rows
        if row.get("symbol") or row.get("code")
    }
    inventory: list[dict[str, Any]] = []
    for path in files:
        symbol = path.stem.split("_", 1)[-1]
        first_row: dict[str, Any] | None = None
        last_row: dict[str, Any] | None = None
        row_count = 0
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for raw in csv.DictReader(handle):
                    row = {key: normalize_value(value) for key, value in raw.items() if key is not None}
                    if first_row is None:
                        first_row = row
                    last_row = row
                    row_count += 1
        except Exception:
            continue
        if last_row is None:
            continue
        meta = classification.get(symbol, {})
        inventory.append(
            {
                "symbol": symbol,
                "name": meta.get("name") or symbol,
                "group": meta.get("group") or "未分类",
                "etf_type": meta.get("etf_type") or "unknown",
                "pool": meta.get("pool") or "research_only",
                "data_start": (first_row or {}).get("date"),
                "price_date": last_row.get("date"),
                "close": last_row.get("close"),
                "change_pct": last_row.get("pctChg"),
                "volume": last_row.get("volume"),
                "row_count": row_count,
                "price_unit": "元",
                "source": "本地 ETF 日线 CSV",
            }
        )

    inventory.sort(key=lambda row: str(row.get("symbol") or ""))
    _ETF_INVENTORY_CACHE["signature"] = signature
    _ETF_INVENTORY_CACHE["rows"] = inventory
    return list(inventory)


def app_task_status() -> dict[str, Any]:
    return read_json(REPORT_DIR / "app_task_status.json", {"running": False, "latest_task": None, "history": []})


def execution_safety_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    safety = data.get("execution_safety", {}) if isinstance(data, dict) else {}
    app_launch = data.get("app_launch", {}) if isinstance(data, dict) else {}
    launch_status = read_json(LOG_DIR / "app_launch_status.json", {})
    launch_diagnostics = read_json(REPORT_DIR / "app_launch_diagnostics.json", {})
    app_shortcut = data.get("app_shortcut", {}) if isinstance(data, dict) else {}
    return {
        "paper_only": True,
        "real_trade_enabled": False,
        "broker_api_enabled": False,
        "real_account_read_enabled": False,
        "real_order_buttons_enabled": False,
        "arbitrary_command_enabled": False,
        "adjusted_rank_score_preview_enabled": bool(safety.get("adjusted_rank_score_preview_enabled", True)),
        "adjusted_rank_score_execution_enabled": False,
        "shadow_model_enabled": bool(safety.get("shadow_model_enabled", True)),
        "shadow_model_execution_enabled": False,
        "paper_use_market_state_position": bool(safety.get("paper_use_market_state_position", False)),
        "jqdata_credential_configured": bool(os.environ.get("JQDATA_USER") and os.environ.get("JQDATA_PASSWORD")),
        "tushare_token_configured": bool(os.environ.get("TUSHARE_TOKEN")),
        "app_launch": app_launch,
        "app_shortcut": app_shortcut,
        "app_launch_status": launch_status,
        "app_launch_diagnostics": launch_diagnostics,
        "forbidden": ["broker_login", "real_buy", "real_sell", "read_real_account", "sync_real_position"],
        "safe_note": "本 App 只允许白名单本地任务；不提供真实交易按钮；不显示或保存账号密码。",
    }


def app_env_snapshot() -> dict[str, Any]:
    script = PROJECT_ROOT / "scripts" / "check_app_env.sh"
    if not script.exists():
        return {"status": "ERROR", "output": "缺少 scripts/check_app_env.sh", "exit_code": 127}
    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            env={**os.environ, "REAL_TRADE_ENABLED": "0", "BROKER_API_ENABLED": "0"},
        )
    except subprocess.TimeoutExpired:
        return {"status": "ERROR", "output": "环境检查超时", "exit_code": 124}
    output = "\n".join(part for part in [proc.stdout, proc.stderr] if part)
    status = "OK" if proc.returncode == 0 else "CAUTION"
    if "\nERROR" in f"\n{output}" or "Result: ERROR" in output:
        status = "ERROR"
    elif ("\nCAUTION" in f"\n{output}" or "Result: CAUTION" in output) and status == "OK":
        status = "CAUTION"
    return {"status": status, "output": output[-12000:], "exit_code": proc.returncode}


def system_status_snapshot(data: dict[str, Any], update: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    risk_alerts = data.get("risk_alerts", []) if isinstance(data, dict) else []
    severity = str(update.get("severity") or update.get("status") or "").upper()
    if update.get("failed_count", 0) or severity in {"ERROR", "FAILED"}:
        system_status = "ERROR"
    elif risk_alerts or sources.get("fallback_triggered") or severity in {"CAUTION", "STALE"}:
        system_status = "CAUTION"
    else:
        system_status = "NORMAL"
    if system_status == "ERROR":
        today_conclusion = "REVIEW_REQUIRED"
    elif any("RISK" in str(alert).upper() for alert in risk_alerts):
        today_conclusion = "RISK_REVIEW"
    else:
        today_conclusion = "HOLD_PLAN"
    return {
        "system_status": system_status,
        "today_conclusion": today_conclusion,
        "risk_count": len(risk_alerts),
        "latest_data_date": data.get("latest_data_date") or update.get("latest_local_date"),
        "generated_at": data.get("generated_at"),
    }


def formal_update_source_policy() -> dict[str, Any]:
    return {
        "primary_provider": "TUSHARE",
        "primary_source": "TUSHARE",
        "actual_source_used": "TUSHARE",
        "fallback_enabled": False,
        "fallback_source": "DISABLED",
        "fallback_triggered": False,
        "source_priority": ["TUSHARE"],
        "baostock_role": "RECONCILIATION_ONLY",
        "jqdata_fallback": "DISABLED",
    }


def legacy_reconciliation_status(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "legacy_actual_source_used": sources.get("actual_source_used"),
        "legacy_fallback_triggered": bool(sources.get("fallback_triggered", False)),
        "baostock_status": sources.get("baostock_status"),
        "jqdata_status": sources.get("jqdata_status"),
    }


def status_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    update = data_update_status()
    sources = data_source_status()
    policy_sources = formal_update_source_policy()
    summary = data.get("paper_summary", {}) if isinstance(data, dict) else {}
    market_state = data.get("market_state", {}) if isinstance(data, dict) else {}
    exposure = data.get("portfolio_exposure", {}) if isinstance(data, dict) else {}
    review_summary = data.get("review_summary", {}) if isinstance(data, dict) else {}
    profit_summary = data.get("profit_protection_summary", {}) if isinstance(data, dict) else {}
    high_beta_summary = data.get("high_beta_risk_summary", {}) if isinstance(data, dict) else {}
    broad_base_summary = data.get("broad_base_balance_summary", {}) if isinstance(data, dict) else {}
    chatgpt_weekly_packet = data.get("chatgpt_weekly_packet", {}) if isinstance(data, dict) else {}
    chatgpt_weekly_packet_summary = data.get("chatgpt_weekly_packet_summary", {}) if isinstance(data, dict) else {}
    engine = data.get("paper_trade_engine", {}) if isinstance(data, dict) else {}
    automation = data.get("automation_status", data.get("automation_nodes", [])) if isinstance(data, dict) else []
    system = system_status_snapshot(data, update, policy_sources)
    safety = execution_safety_snapshot()
    app_control = data.get("app_control_room", {}) if isinstance(data, dict) else {}
    return {
        "system_status": system.get("system_status"),
        "today_conclusion": system.get("today_conclusion"),
        "today_summary": app_control.get("today_summary") or data.get("console", {}).get("decision_reason", ""),
        "key_warnings": app_control.get("key_warnings") or data.get("risk_alerts", []),
        "app_control_room": app_control,
        "execution_safety": safety,
        "app_launch": safety.get("app_launch", {}),
        "latest_data_date": data.get("latest_data_date") or update.get("latest_local_date"),
        "data_update_status": update.get("status") or update.get("severity") or "unknown",
        "data_update_new_rows": update.get("added_rows", 0),
        "data_update_failed_count": update.get("failed_count", 0),
        "data_sources": policy_sources,
        "primary_provider": "TUSHARE",
        "actual_source_used": "TUSHARE",
        "fallback_enabled": False,
        "fallback_triggered": False,
        "baostock_role": "RECONCILIATION_ONLY",
        "jqdata_fallback": "DISABLED",
        "legacy_reconciliation": legacy_reconciliation_status(sources),
        "automation_status": automation,
        "paper_trade_engine_status": engine.get("state", {}).get("status") if isinstance(engine.get("state"), dict) else engine.get("status", "unknown"),
        "market_state": market_state.get("market_state", "unknown") if isinstance(market_state, dict) else "unknown",
        "portfolio_exposure": exposure.get("summary", exposure) if isinstance(exposure, dict) else exposure,
        "review_summary": review_summary,
        "reduce_candidate_count": review_summary.get("reduce_candidate_count", 0) if isinstance(review_summary, dict) else 0,
        "review_2_count": review_summary.get("review_2_count", 0) if isinstance(review_summary, dict) else 0,
        "profit_protection_summary": profit_summary,
        "profit_watch_count": profit_summary.get("profit_watch_count", 0) if isinstance(profit_summary, dict) else 0,
        "profit_protection_review_count": profit_summary.get("profit_protection_review_count", 0) if isinstance(profit_summary, dict) else 0,
        "profit_lock_candidate_count": profit_summary.get("profit_lock_candidate_count", 0) if isinstance(profit_summary, dict) else 0,
        "high_beta_risk_summary": high_beta_summary,
        "high_beta_position_count": high_beta_summary.get("high_beta_position_count", 0) if isinstance(high_beta_summary, dict) else 0,
        "high_beta_weight_of_equity": high_beta_summary.get("high_beta_weight_of_equity", 0) if isinstance(high_beta_summary, dict) else 0,
        "high_beta_weight_of_holdings": high_beta_summary.get("high_beta_weight_of_holdings", 0) if isinstance(high_beta_summary, dict) else 0,
        "high_beta_exposure_state": high_beta_summary.get("high_beta_exposure_state", "HB_NORMAL") if isinstance(high_beta_summary, dict) else "HB_NORMAL",
        "finance_real_estate_weight": high_beta_summary.get("finance_real_estate_weight_of_equity", 0) if isinstance(high_beta_summary, dict) else 0,
        "broad_base_balance_summary": broad_base_summary,
        "broad_base_weight": broad_base_summary.get("broad_base_weight", data.get("broad_base_weight", 0)) if isinstance(broad_base_summary, dict) else 0,
        "theme_weight": broad_base_summary.get("theme_weight", data.get("theme_weight", 0)) if isinstance(broad_base_summary, dict) else 0,
        "tech_growth_weight": broad_base_summary.get("tech_growth_weight", data.get("tech_growth_weight", 0)) if isinstance(broad_base_summary, dict) else 0,
        "broad_base_balance_state": broad_base_summary.get("broad_base_balance_state", "UNKNOWN") if isinstance(broad_base_summary, dict) else "UNKNOWN",
        "balance_candidate_count": broad_base_summary.get("balance_candidate_count", data.get("balance_candidate_count", 0)) if isinstance(broad_base_summary, dict) else 0,
        "top_balance_candidates": data.get("top_balance_candidates", []) if isinstance(data, dict) else [],
        "chatgpt_weekly_packet": chatgpt_weekly_packet,
        "chatgpt_weekly_packet_summary": chatgpt_weekly_packet_summary or chatgpt_weekly_packet.get("summary", {}),
        "total_equity": summary.get("total_equity", summary.get("equity", 0)),
        "cash": summary.get("cash", 0),
        "position_value": summary.get("position_value", summary.get("market_value", 0)),
        "position_pct": summary.get("position_pct", summary.get("position_ratio", 0)),
        "real_trade_enabled": False,
        "broker_api_enabled": False,
        "app_version": "phase3b_app_control_room_upgrade_v1",
        "generated_at": data.get("generated_at"),
    }


def portfolio_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    positions = data.get("positions_enhanced") or data.get("positions") or read_csv_rows(DATA_DIR / "paper_positions.csv")
    summary = data.get("paper_summary", {})
    performance = data.get("paper_performance", {}) if isinstance(data, dict) else {}
    equity_curve = data.get("paper_equity_curve", []) if isinstance(data, dict) else []
    dashboard_curve_meta = data.get("paper_equity_backfill", {}) if isinstance(data, dict) else {}
    trade_pnl = data.get("paper_trade_pnl", []) if isinstance(data, dict) else []
    trade_review = data.get("trade_review", {}) if isinstance(data, dict) else {}
    trade_review_details = data.get("trade_review_details", []) if isinstance(data, dict) else []
    trade_review_open_positions = data.get("trade_review_open_positions", []) if isinstance(data, dict) else []
    position_review_state = data.get("position_review_state", []) if isinstance(data, dict) else []
    review_summary = data.get("review_summary", {}) if isinstance(data, dict) else {}
    profit_protection_preview = data.get("profit_protection_preview", []) if isinstance(data, dict) else []
    profit_protection_summary = data.get("profit_protection_summary", {}) if isinstance(data, dict) else {}
    high_beta_risk_watch = data.get("high_beta_risk_watch", []) if isinstance(data, dict) else []
    high_beta_risk_summary = data.get("high_beta_risk_summary", {}) if isinstance(data, dict) else {}
    broad_base_balance_preview = data.get("broad_base_balance_preview", {}) if isinstance(data, dict) else {}
    broad_base_balance_summary = data.get("broad_base_balance_summary", {}) if isinstance(data, dict) else {}
    if not performance:
        performance = read_json(REPORT_DIR / "paper_performance_summary.json", {})
    backfilled_curve = read_csv_rows(DATA_DIR / "paper_equity_curve_backfilled.csv")
    original_curve = read_csv_rows(DATA_DIR / "paper_equity_curve.csv")
    equity_curve = merge_equity_curves(backfilled_curve, original_curve, equity_curve)[-180:]
    valuation_date = performance.get("valuation_as_of_date") or performance.get("latest_data_date") or summary.get("valuation_as_of_date")
    equity_curve_meta = {
        **(dashboard_curve_meta if isinstance(dashboard_curve_meta, dict) else {}),
        **build_equity_curve_meta(equity_curve, original_curve, backfilled_curve, valuation_date),
    }
    if not trade_pnl:
        trade_pnl = read_csv_rows(REPORT_DIR / "paper_trade_pnl.csv")[-120:]
    if not trade_review:
        trade_review = read_json(REPORT_DIR / "trade_review_summary.json", {})
    if not trade_review_details:
        trade_review_details = read_csv_rows(REPORT_DIR / "trade_review_details.csv")[-120:]
    if not trade_review_open_positions:
        trade_review_open_positions = read_csv_rows(REPORT_DIR / "trade_review_open_positions.csv")[-120:]
    return {
        "summary": summary,
        "positions": positions,
        "performance": performance,
        "equity_curve": equity_curve,
        "equity_curve_meta": equity_curve_meta,
        "trade_pnl": trade_pnl,
        "trade_review": trade_review,
        "trade_review_details": trade_review_details,
        "trade_review_open_positions": trade_review_open_positions,
        "position_review_state": position_review_state,
        "review_summary": review_summary,
        "profit_protection_preview": profit_protection_preview,
        "profit_protection_summary": profit_protection_summary,
        "high_beta_risk_watch": high_beta_risk_watch,
        "high_beta_risk_summary": high_beta_risk_summary,
        "broad_base_balance_preview": broad_base_balance_preview,
        "broad_base_balance_summary": broad_base_balance_summary,
        "real_trade_enabled": False,
        "broker_api_enabled": False,
    }


def signals_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    preview_rows = read_csv_rows(REPORT_DIR / "strategy_enhancement_preview.csv")
    tracking_rows = read_csv_rows(REPORT_DIR / "strategy_preview_tracking.csv")
    original = sorted(preview_rows, key=lambda r: r.get("original_rank") or 999999)[:10]
    adjusted = sorted(preview_rows, key=lambda r: r.get("adjusted_rank_preview") or 999999)[:10]
    original_top3 = {str(r.get("symbol")) for r in original[:3]}
    adjusted_top3 = {str(r.get("symbol")) for r in adjusted[:3]}
    deltas = sorted(
        [row for row in preview_rows if row.get("score_delta") is not None],
        key=lambda row: abs(float(row.get("score_delta") or 0)),
        reverse=True,
    )[:10]
    bonus_hits = [row for row in preview_rows if float(row.get("broad_index_balance_bonus") or 0) > 0 or float(row.get("defensive_balance_bonus") or 0) > 0]
    penalty_hits = [
        row
        for row in preview_rows
        if float(row.get("same_group_concentration_penalty") or 0) < 0
        or float(row.get("high_beta_penalty") or 0) < 0
        or float(row.get("data_health_penalty") or 0) < 0
        or float(row.get("liquidity_penalty") or 0) < 0
    ]
    return {
        "original_top10": original,
        "adjusted_preview_top10": adjusted,
        "original_top3": original[:3],
        "adjusted_preview_top3": adjusted[:3],
        "top3_entered": sorted(adjusted_top3 - original_top3 - {"None", "nan"}),
        "top3_exited": sorted(original_top3 - adjusted_top3 - {"None", "nan"}),
        "top3_difference": sorted((original_top3 ^ adjusted_top3) - {"None", "nan"}),
        "score_delta_extremes": deltas,
        "bonus_hits": bonus_hits[:10],
        "penalty_hits": penalty_hits[:10],
        "buy_ranking": data.get("buy_ranking", []) if isinstance(data, dict) else [],
        "preview_only": True,
        "adjusted_rank_score_execution_enabled": False,
        "tracking_rows": tracking_rows[-50:],
    }


def data_health_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    update = data_update_status()
    sources = data_source_status()
    policy_sources = formal_update_source_policy()
    health = data.get("health_summary", {}) if isinstance(data, dict) else {}
    coverage_md = tail_text(REPORT_DIR / "latest_data_coverage.md", 80)
    health_md = tail_text(REPORT_DIR / "latest_data_health.md", 80)
    expected_date = str(update.get("requested_end") or update.get("latest_local_date") or data.get("latest_data_date") or "")
    inventory_rows = etf_inventory_snapshot()
    dated_inventory = []
    for row in inventory_rows:
        item = dict(row)
        price_date = str(item.get("price_date") or "")
        item["update_status"] = "up_to_date" if expected_date and price_date >= expected_date else "lagging"
        dated_inventory.append(item)
    current_count = sum(1 for row in dated_inventory if row.get("update_status") == "up_to_date")
    return {
        "etf_file_count": update.get("universe_size") or health.get("etf_file_count"),
        "latest_data_date": update.get("latest_local_date") or data.get("latest_data_date"),
        "new_rows": update.get("added_rows", 0),
        "failed_count": update.get("failed_count", 0),
        "status": update.get("status") or update.get("severity") or health.get("status", "unknown"),
        "diagnosis": update.get("reason") or update.get("recommendation") or "",
        "data_sources": policy_sources,
        "primary_provider": "TUSHARE",
        "primary_source": "TUSHARE",
        "fallback_enabled": False,
        "fallback_source": "DISABLED",
        "actual_source_used": "TUSHARE",
        "fallback_triggered": False,
        "failed_symbols": update.get("failed_symbols", []),
        "unresolved_symbols": update.get("unresolved_symbols", []),
        "source_priority": ["TUSHARE"],
        "baostock_role": "RECONCILIATION_ONLY",
        "jqdata_fallback": "DISABLED",
        "legacy_reconciliation": legacy_reconciliation_status(sources),
        "coverage_tail": coverage_md,
        "health_tail": health_md,
        "baostock_api_calls": 0,
        "jqdata_api_calls": 0,
        "actual_api_calls": update.get("actual_api_calls", 0),
        "processed_symbols": update.get("processed_symbols", 0),
        "up_to_date_count": update.get("up_to_date_count", 0),
        "requested_end": update.get("requested_end"),
        "generated_at": update.get("generated_at") or data.get("generated_at"),
        "inventory_summary": {
            "expected_price_date": expected_date or None,
            "total_count": len(dated_inventory),
            "up_to_date_count": current_count,
            "lagging_count": max(0, len(dated_inventory) - current_count),
            "price_unit": "元",
        },
        "etf_inventory": dated_inventory,
        "universe_quality_review": data.get("universe_quality_review", {}) if isinstance(data, dict) else {},
        "phase4c_data": data.get("phase4c_data", {}) if isinstance(data, dict) else {},
        "phase4c_tushare_staging": data.get("phase4c_tushare_staging", {}) if isinstance(data, dict) else {},
        "phase4c_alpha": data.get("phase4c_alpha", {}) if isinstance(data, dict) else {},
        "persistence_breakout_shadow": data.get("persistence_breakout_shadow", {}) if isinstance(data, dict) else {},
        "missed_opportunity_tracking": data.get("missed_opportunity_tracking", {}) if isinstance(data, dict) else {},
        "shadow_observation_weekly": data.get("shadow_observation_weekly", {}) if isinstance(data, dict) else {},
    }


def research_snapshot() -> dict[str, Any]:
    data = dashboard_data()
    tracking = data.get("strategy_preview_tracking", {}) if isinstance(data, dict) else {}
    shadow = data.get("shadow_model", {}) if isinstance(data, dict) else {}
    quality = data.get("research_quality_review", {}) if isinstance(data, dict) else {}
    integration = data.get("execution_layer_integration", {}) if isinstance(data, dict) else {}
    rows = read_csv_rows(REPORT_DIR / "strategy_preview_tracking.csv")
    status_counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("forward_returns_status") or "unknown")
        status_counts[key] = status_counts.get(key, 0) + 1
    return {
        "app_control_center": data.get("app_control_center", {}) if isinstance(data, dict) else {},
        "app_task_status": app_task_status(),
        "data_sources": data.get("data_sources", {}) if isinstance(data, dict) else {},
        "system_safety": data.get("system_safety", {}) if isinstance(data, dict) else {},
        "execution_safety": data.get("execution_safety", {}) if isinstance(data, dict) else {},
        "strategy_preview_tracking": tracking,
        "broad_base_balance_preview": data.get("broad_base_balance_preview", {}) if isinstance(data, dict) else {},
        "broad_base_balance_summary": data.get("broad_base_balance_summary", {}) if isinstance(data, dict) else {},
        "top_balance_candidates": data.get("top_balance_candidates", []) if isinstance(data, dict) else [],
        "sample_count": len(rows),
        "forward_return_status_counts": status_counts,
        "original_vs_adjusted": data.get("forward_return_comparison", {}),
        "shadow_model": shadow,
        "research_quality_review": quality,
        "execution_layer_integration": integration,
        "market_state": data.get("market_state", {}) if isinstance(data, dict) else {},
        "market_regime_audit": data.get("market_regime_audit", {}) if isinstance(data, dict) else {},
        "market_regime_stabilization": data.get("market_regime_stabilization", {}) if isinstance(data, dict) else {},
        "style_regime_fit": data.get("style_regime_fit", {}) if isinstance(data, dict) else {},
        "portfolio_exposure": data.get("portfolio_exposure", {}) if isinstance(data, dict) else {},
        "classification_summary": data.get("classification_summary", {}) if isinstance(data, dict) else {},
        "universe_quality_review": data.get("universe_quality_review", {}) if isinstance(data, dict) else {},
        "phase4c_data": data.get("phase4c_data", {}) if isinstance(data, dict) else {},
        "phase4c_tushare_staging": data.get("phase4c_tushare_staging", {}) if isinstance(data, dict) else {},
        "phase4c_alpha": data.get("phase4c_alpha", {}) if isinstance(data, dict) else {},
        "persistence_breakout_shadow": data.get("persistence_breakout_shadow", {}) if isinstance(data, dict) else {},
        "missed_opportunity_tracking": data.get("missed_opportunity_tracking", {}) if isinstance(data, dict) else {},
        "shadow_observation_weekly": data.get("shadow_observation_weekly", {}) if isinstance(data, dict) else {},
        "chatgpt_weekly_packet": data.get("chatgpt_weekly_packet", {}) if isinstance(data, dict) else {},
        "chatgpt_weekly_packet_summary": data.get("chatgpt_weekly_packet_summary", {}) if isinstance(data, dict) else {},
        "exit_rule_research": data.get("exit_rule_research", {}) if isinstance(data, dict) else {},
        "backtest_phase4a": data.get("backtest_phase4a", {}) if isinstance(data, dict) else {},
        "backtest_diagnostics": data.get("backtest_diagnostics", {}) if isinstance(data, dict) else {},
        "ranking_signal_research": data.get("ranking_signal_research", {}) if isinstance(data, dict) else {},
        "ranking_model_v2_backtest": data.get("ranking_model_v2_backtest", {}) if isinstance(data, dict) else {},
        "etf_risk_profile": data.get("etf_risk_profile", {}) if isinstance(data, dict) else {},
        "etf_risk_profile_summary": data.get("etf_risk_profile_summary", {}) if isinstance(data, dict) else {},
        "portfolio_risk_profile": data.get("portfolio_risk_profile", {}) if isinstance(data, dict) else {},
        "buy_ranking_risk_profile": data.get("buy_ranking_risk_profile", {}) if isinstance(data, dict) else {},
        "risk_profile_distribution": data.get("risk_profile_distribution", {}) if isinstance(data, dict) else {},
        "style_profile_distribution": data.get("style_profile_distribution", {}) if isinstance(data, dict) else {},
        "trade_review": data.get("trade_review", {}) if isinstance(data, dict) else {},
        "report_summaries": research_report_summaries(),
        "research_only": True,
        "sample_warning": "样本不足时只展示，不进入执行层。",
    }


def research_report_summaries() -> dict[str, Any]:
    allowed = {
        "shadow_observation_weekly": (
            REPORT_DIR / "shadow_observation_weekly.md",
            "每周影子观察",
            "用于判断 shadow 模型证据是否成熟，不是交易指令。",
        ),
        "missed_opportunity_tracker": (
            REPORT_DIR / "missed_opportunity_tracker.md",
            "错失机会追踪",
            "观察被过滤的高分候选后续表现。",
        ),
        "missed_opportunity_by_filter_reason": (
            REPORT_DIR / "missed_opportunity_by_filter_reason.md",
            "过滤原因分析",
            "按过滤原因拆解错失机会。",
        ),
        "risk_on_empty_signal_analysis": (
            REPORT_DIR / "risk_on_empty_signal_analysis.md",
            "强市场空信号分析",
            "研究 risk_on 但模型空仓的情况。",
        ),
        "persistence_breakout_shadow_signal": (
            REPORT_DIR / "persistence_breakout_shadow_signal.md",
            "突破影子信号",
            "只展示 persistence_breakout_v2 的影子信号。",
        ),
        "persistence_breakout_shadow_portfolio": (
            REPORT_DIR / "persistence_breakout_shadow_portfolio.md",
            "突破影子组合",
            "独立 shadow 组合，不写正式模拟持仓。",
        ),
        "model_shadow_comparison": (
            REPORT_DIR / "model_shadow_comparison.md",
            "影子模型对比",
            "比较多个研究模型，不接执行层。",
        ),
        "data_provider_status": (
            REPORT_DIR / "data_provider_status.md",
            "数据源状态",
            "展示日更数据源状态，不显示密钥。",
        ),
        "tushare_staging_check": (
            REPORT_DIR / "tushare_staging_check.md",
            "Tushare 预备区检查",
            "Tushare 只作为候选数据源检查。",
        ),
        "tushare_baostock_compare": (
            REPORT_DIR / "tushare_baostock_compare.md",
            "Tushare 与 BaoStock 对比",
            "检查两个数据源口径差异。",
        ),
        "regime_layer_phase2_market_audit": (
            REPORT_DIR / "regime_layer_phase2_market_audit.md",
            "市场状态 Phase 2 审计",
            "历史回放现有 market_regime，只用于研究判断。",
        ),
        "market_regime_audit_decision": (
            REPORT_DIR / "market_regime_audit_decision.md",
            "市场状态审计决策",
            "判断是否可以进入下一阶段 Regime Fit 研究。",
        ),
        "market_regime_replay": (
            REPORT_DIR / "market_regime_replay.md",
            "市场状态历史回放",
            "逐交易日 point-in-time 回放，不改执行层。",
        ),
        "regime_style_forward_return": (
            REPORT_DIR / "regime_style_forward_return.md",
            "Style x Regime 表现",
            "按 ETF style 分层观察不同市场状态下的后续收益。",
        ),
        "regime_layer_phase2_5_stabilization": (
            REPORT_DIR / "regime_layer_phase2_5_stabilization.md",
            "市场状态稳定化研究",
            "比较 raw 与多个稳定化候选，只作 shadow 研究。",
        ),
        "regime_stabilization_candidate_decision": (
            REPORT_DIR / "regime_stabilization_candidate_decision.md",
            "稳定化候选决策",
            "选择 shadow-only 稳定候选，不接执行层。",
        ),
        "regime_stabilization_detection_lag": (
            REPORT_DIR / "regime_stabilization_detection_lag.md",
            "稳定化检测延迟",
            "检查稳定化是否以过大滞后为代价。",
        ),
        "regime_layer_phase3_style_fit": (
            REPORT_DIR / "regime_layer_phase3_style_fit.md",
            "风格与市场状态适配研究",
            "Style-Regime Fit 研究报告，只做 shadow 观察。",
        ),
        "style_regime_fit_summary": (
            REPORT_DIR / "style_regime_fit_summary.md",
            "风格适配矩阵",
            "按风格与稳定市场状态展示 fit evidence。",
        ),
        "current_buy_top10_style_regime_fit": (
            REPORT_DIR / "current_buy_top10_style_regime_fit.md",
            "当前 BUY Top10 风格适配",
            "不修改 BUY ranking，只展示 fit 标签。",
        ),
    }
    result: dict[str, Any] = {}
    for key, (path, display_name, hint) in allowed.items():
        result[key] = {
            "status": "present" if path.exists() else "missing",
            "display_name": display_name,
            "hint": hint,
            "path": str(path.relative_to(PROJECT_ROOT)),
            "tail": tail_text(path, max_lines=80) if path.exists() else "报告缺失或暂未生成。",
        }
    return result


LOG_WHITELIST = {
    "daily_close.log": LOG_DIR / "daily_close.log",
    "catchup_check.log": LOG_DIR / "catchup_check.log",
    "app_tasks.log": LOG_DIR / "app_tasks" / "latest.log",
    "latest_app_task.log": LOG_DIR / "app_tasks" / "latest.log",
    "app_server.log": LOG_DIR / "app_server.log",
    "data_update_log.md": REPORT_DIR / "data_update_log.md",
}


def log_tail(name: str, max_lines: int = 200) -> dict[str, Any]:
    path = LOG_WHITELIST.get(name)
    if path is None:
        return {"name": name, "allowed": False, "tail": "该日志名称不在白名单内"}
    return {"name": name, "allowed": True, "tail": tail_text(path, max_lines=max_lines)}
