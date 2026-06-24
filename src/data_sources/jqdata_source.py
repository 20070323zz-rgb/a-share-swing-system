"""JQData ETF daily downloader with staging-first import.

This module reads credentials only from environment variables or a local
project `.env` file. It never logs credentials and never touches broker APIs.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import date
import io
import json
import os
from pathlib import Path
import re
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
STAGING_DIR = DATA_DIR / "staging" / "jqdata"
REPORT_DIR = PROJECT_ROOT / "reports"

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


@dataclass
class JQDataConfig:
    username: str
    password: str
    source: str


def load_jqdata_config() -> tuple[JQDataConfig | None, str]:
    _load_dotenv_safely()
    username = (os.environ.get("JQDATA_USERNAME") or os.environ.get("JQDATA_USER") or "").strip()
    password = os.environ.get("JQDATA_PASSWORD", "").strip()
    if not username or not password:
        return None, "NOT_CONFIGURED"
    return JQDataConfig(username=username, password=password, source="env_or_dotenv"), "CONFIGURED"


def _load_dotenv_safely() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env", override=False)
    except Exception:
        return


def to_jq_symbol(symbol: str) -> str:
    code = _extract_code(symbol)
    if not code:
        return ""
    if code.startswith(("51", "52", "56", "58")):
        return f"{code}.XSHG"
    if code.startswith(("15", "16")):
        return f"{code}.XSHE"
    return ""


def from_jq_symbol(jq_symbol: str) -> str:
    match = re.search(r"(\d{6})", str(jq_symbol))
    return match.group(1) if match else ""


def to_file_symbol(symbol: str) -> str:
    code = _extract_code(symbol)
    if not code:
        return ""
    if code.startswith(("51", "52", "56", "58")):
        return f"sh_{code}"
    if code.startswith(("15", "16")):
        return f"sz_{code}"
    return ""


def _extract_code(symbol: str) -> str:
    match = re.search(r"(\d{6})", str(symbol))
    return match.group(1) if match else ""


def run_jqdata_update(
    items: pd.DataFrame,
    start: str,
    end: str,
    *,
    dry_run: bool = False,
    validate_only: bool = False,
    skip_backfill: bool = False,
) -> dict[str, Any]:
    config, config_status = load_jqdata_config()
    if config is None:
        return _empty_result("NOT_CONFIGURED", "JQData credentials are not configured; fallback is allowed.")

    try:
        from jqdatasdk import auth, get_price
    except Exception as exc:
        return _empty_result("ERROR", f"jqdatasdk import failed: {type(exc).__name__}")

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            auth(config.username, config.password)
    except Exception as exc:
        return _empty_result("AUTH_FAILED", f"JQData auth failed: {type(exc).__name__}")

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    ETF_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    updated_symbols: list[str] = []
    failed_symbols: list[str] = []
    pending_symbols: list[str] = []
    skipped_symbols: list[str] = []
    unresolved_symbols: list[str] = []
    total_new_rows = 0
    staging_files = 0

    for _, item in items.iterrows():
        code = str(item.get("code", "")).strip()
        name = str(item.get("name", code)).strip()
        jq_symbol = to_jq_symbol(code)
        file_symbol = to_file_symbol(code)
        if not jq_symbol or not file_symbol:
            unresolved_symbols.append(code)
            rows.append(_row(code, name, "unresolved", "code cannot be mapped to JQData exchange suffix"))
            continue

        local_path = ETF_DAILY_DIR / f"{file_symbol}.csv"
        ranges = _download_ranges(_read_existing(local_path), start, end, skip_backfill)
        if not ranges:
            skipped_symbols.append(code)
            rows.append(_row(code, name, "skipped_up_to_date", "local CSV already covers requested range", jq_symbol=jq_symbol, file_path=str(local_path.relative_to(PROJECT_ROOT))))
            continue

        if dry_run:
            skipped_symbols.append(code)
            rows.append(_row(code, name, "dry_run_planned", "; ".join(f"{m}:{s}~{e}" for s, e, m in ranges), jq_symbol=jq_symbol, file_path=str(local_path.relative_to(PROJECT_ROOT))))
            continue

        symbol_frames: list[pd.DataFrame] = []
        messages: list[str] = []
        for range_start, range_end, mode in ranges:
            try:
                fetched = get_price(
                    jq_symbol,
                    start_date=range_start,
                    end_date=range_end,
                    frequency="daily",
                    fields=["open", "high", "low", "close", "volume", "money"],
                    panel=False,
                )
            except Exception as exc:
                messages.append(f"{mode} {range_start}~{range_end}: ERROR {type(exc).__name__}")
                continue
            normalized = _normalize_jqdata(fetched, code, jq_symbol)
            if normalized.empty:
                messages.append(f"{mode} {range_start}~{range_end}: empty")
            else:
                messages.append(f"{mode} {range_start}~{range_end}: {len(normalized)} rows")
                symbol_frames.append(normalized)

        staged = _concat_frames(symbol_frames)
        staging_path = STAGING_DIR / f"{jq_symbol}.csv"
        if staged.empty:
            pending_symbols.append(code)
            rows.append(_row(code, name, "pending_source_update", "；".join(messages), jq_symbol=jq_symbol, file_path=str(staging_path.relative_to(PROJECT_ROOT))))
            continue

        staged.to_csv(staging_path, index=False)
        staging_files += 1
        valid, reason = validate_staged_csv(staging_path, expected_symbol=code)
        if not valid:
            failed_symbols.append(code)
            rows.append(_row(code, name, "failed_validation", reason, jq_symbol=jq_symbol, file_path=str(staging_path.relative_to(PROJECT_ROOT)), jq_rows=len(staged)))
            continue

        if validate_only:
            skipped_symbols.append(code)
            rows.append(_row(code, name, "validated_staging_only", reason, jq_symbol=jq_symbol, file_path=str(staging_path.relative_to(PROJECT_ROOT)), jq_rows=len(staged)))
            continue

        merged, new_rows = import_staged_csv(staging_path, local_path)
        total_new_rows += new_rows
        updated_symbols.append(code)
        rows.append(_row(
            code,
            name,
            "imported" if new_rows > 0 else "no_new_rows_after_merge",
            "validated and merged; local rows kept priority on duplicate dates",
            jq_symbol=jq_symbol,
            file_path=str(local_path.relative_to(PROJECT_ROOT)),
            jq_rows=len(staged),
            new_rows=new_rows,
            final_rows=len(merged),
            start_date=_date_min(merged),
            end_date=_date_max(merged),
        ))

    if failed_symbols:
        status = "ERROR" if not updated_symbols and not skipped_symbols else "PARTIAL"
    elif pending_symbols:
        status = "PENDING_SOURCE_UPDATE" if not updated_symbols else "PARTIAL"
    elif updated_symbols or skipped_symbols:
        status = "OK"
    else:
        status = "ERROR"

    return {
        "source": "jqdata",
        "status": status,
        "config_status": config_status,
        "staging_dir": str(STAGING_DIR.relative_to(PROJECT_ROOT)),
        "staging_files": staging_files,
        "rows": rows,
        "updated_symbols": updated_symbols,
        "failed_symbols": failed_symbols,
        "pending_symbols": pending_symbols,
        "skipped_symbols": skipped_symbols,
        "unresolved_symbols": unresolved_symbols,
        "new_rows": total_new_rows,
        "latest_data_date": _latest_local_data_date(),
        "message": _message_for_status(status, total_new_rows, failed_symbols, unresolved_symbols, pending_symbols),
    }


def validate_staged_csv(path: Path, expected_symbol: str = "") -> tuple[bool, str]:
    try:
        df = pd.read_csv(path, dtype={"symbol": str})
    except Exception as exc:
        return False, f"read failed: {type(exc).__name__}"
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return False, f"missing columns: {missing}"
    if df.empty:
        return False, "empty csv"
    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        return False, "date parse failed"
    if dates.duplicated().any():
        return False, "duplicate date"
    for col in ["open", "high", "low", "close", "volume"]:
        values = pd.to_numeric(df[col], errors="coerce")
        if values.isna().any():
            return False, f"{col} contains null/non-numeric"
        if (values < 0).any():
            return False, f"{col} contains negative"
    if (pd.to_numeric(df["high"], errors="coerce") < pd.to_numeric(df["low"], errors="coerce")).any():
        return False, "high < low"
    for col in ["money", "amount"]:
        if col in df.columns and (pd.to_numeric(df[col], errors="coerce").fillna(0) < 0).any():
            return False, f"{col} contains negative"
    if expected_symbol and "symbol" in df.columns:
        symbols = set(df["symbol"].dropna().astype(str))
        if symbols and symbols != {expected_symbol}:
            return False, f"symbol mismatch: {symbols}"
    return True, "passed validation"


def import_staged_csv(staging_path: Path, local_path: Path) -> tuple[pd.DataFrame, int]:
    staged = pd.read_csv(staging_path, dtype={"symbol": str})
    local_code = _local_code_from_path(local_path, staged)
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(staged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["code"] = local_code
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(staged[col], errors="coerce")
    out["amount"] = pd.to_numeric(staged.get("money", staged.get("amount", 0)), errors="coerce").fillna(0)
    for col in ["preclose", "adjustflag", "turn", "tradestatus", "pctChg", "isST"]:
        if col not in out.columns:
            out[col] = pd.NA
    out["adjustflag"] = out["adjustflag"].fillna("2")
    out["tradestatus"] = out["tradestatus"].fillna("1")
    out = out[["date", "code", "open", "high", "low", "close", "preclose", "volume", "amount", "adjustflag", "turn", "tradestatus", "pctChg", "isST"]]
    out = out.dropna(subset=["date", "open", "high", "low", "close", "volume"])

    old = _read_existing(local_path)
    old_dates = set()
    frames = []
    if old is not None and not old.empty:
        for col in out.columns:
            if col not in old.columns:
                old[col] = pd.NA
        old = old[out.columns]
        old_dates = set(pd.to_datetime(old["date"], errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
        frames.append(old)
    new_rows = len([d for d in out["date"].astype(str) if d not in old_dates])
    frames.append(out)
    merged = pd.concat(frames, ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    merged = merged.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="first").reset_index(drop=True)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(local_path, index=False)
    return merged, new_rows


def _local_code_from_path(local_path: Path, staged: pd.DataFrame) -> str:
    name = local_path.stem
    match = re.match(r"^(sh|sz)_(\d{6})$", name)
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    if "symbol" in staged.columns:
        code = _extract_code(str(staged["symbol"].dropna().astype(str).iloc[0])) if not staged["symbol"].dropna().empty else ""
        if code:
            file_symbol = to_file_symbol(code)
            prefix = file_symbol.split("_", 1)[0] if "_" in file_symbol else ""
            if prefix:
                return f"{prefix}.{code}"
    return ""


def _normalize_jqdata(df: Any, symbol: str, jq_symbol: str) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = pd.DataFrame(df).copy()
    if out.empty:
        return pd.DataFrame()
    if isinstance(out.index, pd.MultiIndex):
        out = out.reset_index()
    else:
        out = out.reset_index()
    if "time" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"time": "date"})
    if "index" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"index": "date"})
    if "money" not in out.columns and "amount" in out.columns:
        out["money"] = out["amount"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["symbol"] = symbol
    out["jq_symbol"] = jq_symbol
    out["source"] = "jqdata"
    keep = ["date", "open", "high", "low", "close", "volume", "money", "symbol", "jq_symbol", "source"]
    for col in keep:
        if col not in out.columns:
            out[col] = pd.NA
    for col in ["open", "high", "low", "close", "volume", "money"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[keep].dropna(subset=["date", "open", "high", "low", "close", "volume"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _download_ranges(old: pd.DataFrame | None, default_start: str, end: str, skip_backfill: bool) -> list[tuple[str, str, str]]:
    requested_start = pd.to_datetime(default_start)
    requested_end = pd.to_datetime(end)
    if old is None or old.empty or "date" not in old.columns:
        return [(requested_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward")]
    old_dates = pd.to_datetime(old["date"], errors="coerce").dropna()
    if old_dates.empty:
        return [(requested_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward")]
    first_date = old_dates.min()
    last_date = old_dates.max()
    ranges: list[tuple[str, str, str]] = []
    if not skip_backfill and first_date > requested_start:
        backward_end = first_date - pd.Timedelta(days=1)
        if requested_start <= backward_end:
            ranges.append((requested_start.strftime("%Y-%m-%d"), backward_end.strftime("%Y-%m-%d"), "backfill"))
    forward_start = last_date + pd.Timedelta(days=1)
    if last_date < requested_end and forward_start <= requested_end:
        ranges.append((forward_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward"))
    return ranges


def _read_existing(path: Path) -> pd.DataFrame | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path, dtype={"code": str})
    except Exception:
        return None


def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if out.empty:
        return out
    return out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _row(code: str, name: str, status: str, message: str, **kwargs: Any) -> dict[str, Any]:
    return {"code": code, "name": name, "status": status, "message": message, **kwargs}


def _empty_result(status: str, message: str) -> dict[str, Any]:
    return {
        "source": "jqdata",
        "status": status,
        "config_status": status,
        "rows": [],
        "updated_symbols": [],
        "failed_symbols": [],
        "pending_symbols": [],
        "skipped_symbols": [],
        "unresolved_symbols": [],
        "new_rows": 0,
        "latest_data_date": _latest_local_data_date(),
        "message": message,
    }


def _message_for_status(status: str, new_rows: int, failed_symbols: list[str], unresolved_symbols: list[str], pending_symbols: list[str]) -> str:
    if status == "OK":
        return f"JQData update finished; new_rows={new_rows}."
    if status == "PARTIAL":
        return f"JQData partial update; failed={len(failed_symbols)}, pending={len(pending_symbols)}, unresolved={len(unresolved_symbols)}, new_rows={new_rows}."
    if status == "PENDING_SOURCE_UPDATE":
        return f"JQData returned no new rows for requested range; pending={len(pending_symbols)}, fallback is recommended."
    return f"JQData update failed; failed={len(failed_symbols)}, unresolved={len(unresolved_symbols)}."


def _date_min(df: pd.DataFrame) -> str:
    values = pd.to_datetime(df.get("date"), errors="coerce").dropna()
    return values.min().strftime("%Y-%m-%d") if not values.empty else ""


def _date_max(df: pd.DataFrame) -> str:
    values = pd.to_datetime(df.get("date"), errors="coerce").dropna()
    return values.max().strftime("%Y-%m-%d") if not values.empty else ""


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
