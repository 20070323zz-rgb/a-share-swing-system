"""Point-in-time metadata contracts for Tushare proof outputs."""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable

import pandas as pd

from .schemas import INTERFACE_SCHEMAS, PIT_METADATA_FIELDS


SOURCE_UPDATE_WINDOWS = {
    "index_basic": "daily metadata refresh; row-level historical publication timestamp unavailable",
    "index_daily": "trading day after market close, typically 15:00-17:00 Asia/Shanghai",
    "index_weight": "monthly snapshot; row-level publication timestamp unavailable",
    "index_classify": "taxonomy release/revision; historical publication timestamp unavailable",
    "index_member_all": "membership effective dates; historical publication timestamp unavailable",
    "daily_basic": "trading day after market close; row-level release timestamp unavailable",
    "fund_portfolio": "periodic disclosure; ann_date supplied at date granularity",
    "shibor": "official release 11:00 Asia/Shanghai; project conservative availability 12:00 with 60-minute lag",
}


def build_pit_records(
    interface: str,
    frame: pd.DataFrame,
    *,
    retrieved_at: str,
    query_hash: str,
    raw_payload_hash: str,
    local_trading_dates: Iterable[str],
    evidence_mode: str,
) -> pd.DataFrame:
    if interface not in INTERFACE_SCHEMAS:
        raise KeyError(f"unknown interface: {interface}")
    if evidence_mode not in {"real", "mock"}:
        raise ValueError("evidence_mode must be explicitly set to real or mock")
    trading_dates = sorted({_iso(value) for value in local_trading_dates if _iso(value)})
    records = []
    for row in frame.to_dict(orient="records"):
        observation_date, period_end, announcement_date = _event_dates(interface, row)
        available_date, available_at, pit_status, basis, confidence = _availability(
            interface,
            observation_date=observation_date,
            period_end=period_end,
            announcement_date=announcement_date,
            trading_dates=trading_dates,
        )
        records.append(
            {
                "source": "tushare",
                "evidence_mode": evidence_mode,
                "source_interface": interface,
                "entity_id": _entity_id(interface, row),
                "observation_date": observation_date,
                "period_end": period_end,
                "announcement_date": announcement_date,
                "source_update_window": SOURCE_UPDATE_WINDOWS[interface],
                "official_release_time": "11:00 Asia/Shanghai" if interface == "shibor" else "",
                "project_conservative_available_time": "12:00 Asia/Shanghai" if interface == "shibor" else "",
                "conservative_lag_minutes": 60 if interface == "shibor" else "",
                "retrieved_at": retrieved_at,
                "available_at": available_at,
                "available_date": available_date,
                "pit_basis": basis,
                "pit_confidence": confidence,
                "pit_status": pit_status,
                "query_hash": query_hash,
                "raw_payload_hash": raw_payload_hash,
                "schema_version": 1,
            }
        )
    return pd.DataFrame(records, columns=PIT_METADATA_FIELDS)


def interface_pit_summary(interface: str, pit_records: pd.DataFrame) -> dict[str, Any]:
    statuses = sorted(set(pit_records.get("pit_status", pd.Series(dtype=str)).dropna().astype(str)))
    return {
        "source": "tushare",
        "evidence_mode": "|".join(sorted(set(pit_records.get("evidence_mode", pd.Series(dtype=str)).dropna().astype(str)))),
        "source_interface": interface,
        "pit_statuses": statuses or [INTERFACE_SCHEMAS[interface].pit_default],
        "pit_resolved_rows": int((pit_records.get("pit_status", pd.Series(dtype=str)) == "PIT_RESOLVED").sum()),
        "pit_conservative_rows": int((pit_records.get("pit_status", pd.Series(dtype=str)) == "PIT_CONSERVATIVE").sum()),
        "pit_partial_rows": int((pit_records.get("pit_status", pd.Series(dtype=str)) == "PIT_PARTIAL").sum()),
        "pit_unresolved_rows": int((pit_records.get("pit_status", pd.Series(dtype=str)) == "PIT_UNRESOLVED").sum()),
        "reject_rows": int((pit_records.get("pit_status", pd.Series(dtype=str)) == "REJECT_FOR_HISTORICAL_BACKTEST").sum()),
    }


def _event_dates(interface: str, row: dict[str, Any]) -> tuple[str, str, str]:
    if interface in {"index_daily", "index_weight", "daily_basic"}:
        return _iso(row.get("trade_date")), "", ""
    if interface == "shibor":
        return _iso(row.get("date")), "", ""
    if interface == "fund_portfolio":
        return "", _iso(row.get("end_date")), _iso(row.get("ann_date"))
    if interface == "index_member_all":
        return _iso(row.get("in_date")), "", ""
    return "", "", ""


def _availability(
    interface: str,
    *,
    observation_date: str,
    period_end: str,
    announcement_date: str,
    trading_dates: list[str],
) -> tuple[str, str, str, str, str]:
    if interface == "fund_portfolio":
        if announcement_date and (not period_end or announcement_date >= period_end):
            return announcement_date, announcement_date, "PIT_RESOLVED", "ann_date version retained; available_date not earlier than ann_date", "HIGH"
        return "", "", "PIT_UNRESOLVED", "missing or invalid ann_date", "LOW"
    if interface in {"daily_basic", "index_daily"}:
        next_date = _next_trading_date(observation_date, trading_dates)
        if next_date:
            return next_date, next_date, "PIT_CONSERVATIVE", "next observed trading day after close", "HIGH"
        return "", "", "PIT_PARTIAL", "next trading day unavailable in local calendar snapshot", "MEDIUM"
    if interface == "shibor" and observation_date:
        return observation_date, f"{observation_date}T12:00:00+08:00", "PIT_CONSERVATIVE", "OFFICIAL_11AM_PLUS_PROJECT_LAG", "MEDIUM"
    if interface in {"index_weight", "index_member_all"}:
        return "", "", "PIT_PARTIAL", "effective/snapshot date exists but historical publication timestamp is absent", "MEDIUM"
    if interface in {"index_basic", "index_classify"}:
        return "", "", "PIT_UNRESOLVED", "current metadata/taxonomy does not prove historical availability", "LOW"
    return "", "", "REJECT_FOR_HISTORICAL_BACKTEST", "no approved PIT contract", "LOW"


def _entity_id(interface: str, row: dict[str, Any]) -> str:
    if interface == "index_weight":
        return f"{row.get('index_code', '')}|{row.get('con_code', '')}"
    if interface == "fund_portfolio":
        return f"{row.get('ts_code', '')}|{row.get('symbol', '')}"
    if interface == "index_classify":
        return str(row.get("index_code", ""))
    if interface == "index_member_all":
        return f"{row.get('l1_code', '')}|{row.get('ts_code', '')}"
    return str(row.get("ts_code") or row.get("date") or "")


def _next_trading_date(value: str, trading_dates: list[str]) -> str:
    return next((candidate for candidate in trading_dates if candidate > value), "") if value else ""


def _iso(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        parsed = pd.to_datetime(text, errors="coerce")
        return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")
