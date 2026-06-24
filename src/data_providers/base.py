"""Base data-provider interface for staged market-data ingestion.

Design goals:
- local cache first;
- explicit source and available_date;
- retry/backoff/rate-limit hooks;
- never overwrite newer trusted local rows;
- no broker API and no real trading side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


DAILY_BAR_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "source",
    "fetch_time",
    "available_date",
]


@dataclass
class DailyBarSchema:
    columns: list[str] = field(default_factory=lambda: DAILY_BAR_COLUMNS.copy())
    notes: str = "date/open/high/low/close/volume/amount/source/fetch_time/available_date"


@dataclass
class ProviderStatus:
    name: str
    configured: bool
    usable: bool
    message: str = ""
    last_error: str = ""


@dataclass
class ProviderResult:
    provider: str
    symbol: str
    status: str
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    message: str = ""
    source_status: ProviderStatus | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DataProvider(Protocol):
    name: str

    def status(self) -> ProviderStatus:
        ...

    def fetch_daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        ...


def normalize_daily_bar_schema(df: pd.DataFrame, source: str, fetch_time: str, available_date: str | None = None) -> pd.DataFrame:
    """Return a schema-normalized copy without mutating the source data."""
    if df is None or df.empty:
        return pd.DataFrame(columns=DAILY_BAR_COLUMNS)
    out = df.copy()
    rename = {
        "money": "amount",
        "成交额": "amount",
        "成交量": "volume",
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
    }
    out = out.rename(columns={col: rename.get(str(col).strip(), col) for col in out.columns})
    for col in ["date", "open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            out[col] = pd.NA
    if "amount" not in out.columns:
        out["amount"] = pd.NA
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["source"] = source
    out["fetch_time"] = fetch_time
    out["available_date"] = available_date or out["date"]
    return out[DAILY_BAR_COLUMNS].dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date").reset_index(drop=True)


def existing_local_path(data_dir: Path, symbol: str) -> Path | None:
    code = "".join(ch for ch in str(symbol) if ch.isdigit())[-6:]
    if not code:
        return None
    for prefix in ["sh", "sz"]:
        path = data_dir / f"{prefix}_{code}.csv"
        if path.exists():
            return path
    matches = sorted(data_dir.glob(f"*{code}*.csv"))
    return matches[0] if matches else None
