"""Read-only paper portfolio valuation helpers.

Official paper valuation basis:
data/paper_positions.csv + data/etf_daily/{exchange}_{symbol}.csv latest close.

This module never writes positions/trades, never connects to broker APIs, and
never reads account credentials.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import ETF_DAILY_DIR, PAPER_POSITIONS_FILE


def load_latest_position_valuation(
    positions_file: Path = PAPER_POSITIONS_FILE,
    etf_daily_dir: Path = ETF_DAILY_DIR,
) -> dict[str, Any]:
    positions = _read_positions(positions_file)
    rows: list[dict[str, Any]] = []
    for item in positions.to_dict(orient="records"):
        symbol = _normalize_symbol(item.get("symbol") or item.get("code"))
        quantity = _float(item.get("quantity"))
        cost = _position_cost(item, quantity)
        latest = latest_close(symbol, etf_daily_dir)
        position_price = _float(item.get("current_price")) or _float(item.get("last_price")) or _float(item.get("entry_price"))
        price = latest["close"]
        price_source = latest["source"]
        price_status = latest["status"]
        as_of_date = latest["date"]
        warning = ""
        if price <= 0 and position_price > 0:
            price = position_price
            price_source = "paper_positions.current_price"
            price_status = "missing_daily_price_fallback_position_price"
            as_of_date = str(item.get("updated_at") or "")
            warning = "missing latest ETF close; fallback to position snapshot price"
        elif price <= 0:
            price_status = "missing_price"
            warning = "missing latest ETF close and position snapshot price"
        market_value = quantity * price if price > 0 else 0.0
        pnl = market_value - cost
        position_file_market_value = _float(item.get("market_value"))
        rows.append(
            {
                **item,
                "symbol": symbol,
                "name": item.get("name") or symbol,
                "quantity": quantity,
                "cost": round(cost, 2),
                "total_cost": round(cost, 2),
                "latest_close": round(price, 6) if price > 0 else 0.0,
                "current_price": round(price, 6) if price > 0 else 0.0,
                "last_price": round(price, 6) if price > 0 else 0.0,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(pnl, 2),
                "unrealized_pnl_pct": pnl / cost if cost else 0.0,
                "unrealized_return": pnl / cost if cost else 0.0,
                "as_of_date": as_of_date,
                "price_status": price_status,
                "price_source": price_source,
                "valuation_source": "paper_positions + etf_daily latest close",
                "warning": warning,
                "position_file_price": position_price,
                "position_file_market_value": round(position_file_market_value, 2),
                "market_value_diff_vs_position_file": round(market_value - position_file_market_value, 2),
            }
        )
    df = pd.DataFrame(rows)
    summary = _summary(df)
    return {"positions": df, "summary": summary}


def latest_close(symbol: str, etf_daily_dir: Path = ETF_DAILY_DIR) -> dict[str, Any]:
    code = _normalize_symbol(symbol)
    path = _price_file(code, etf_daily_dir)
    if path is None:
        return {"close": 0.0, "date": "", "status": "price_file_not_found", "source": ""}
    try:
        df = pd.read_csv(path, usecols=lambda col: col in {"date", "close"})
    except Exception as exc:
        return {"close": 0.0, "date": "", "status": f"price_file_read_error:{exc}", "source": str(path)}
    if "date" not in df.columns or "close" not in df.columns:
        return {"close": 0.0, "date": "", "status": "missing_date_or_close", "source": str(path)}
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date")
    if df.empty:
        return {"close": 0.0, "date": "", "status": "no_valid_price_rows", "source": str(path)}
    row = df.iloc[-1]
    return {
        "close": float(row["close"]),
        "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
        "status": "ok",
        "source": str(path),
    }


def _read_positions(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(path, dtype={"symbol": str}, keep_default_na=False).fillna("")
    if "symbol" not in df.columns and "code" in df.columns:
        df["symbol"] = df["code"]
    if "symbol" not in df.columns:
        df["symbol"] = ""
    return df[df["symbol"].astype(str).str.strip() != ""].copy()


def _summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "status": "no_positions",
            "position_count": 0,
            "total_market_value": 0.0,
            "total_cost": 0.0,
            "total_unrealized_pnl": 0.0,
            "as_of_date": "",
            "price_warning_count": 0,
            "valuation_source": "paper_positions + etf_daily latest close",
        }
    warning_count = int((df["price_status"].astype(str) != "ok").sum())
    dates = sorted({str(value) for value in df["as_of_date"].fillna("").astype(str) if str(value)})
    as_of_date = dates[-1] if len(dates) == 1 else ("mixed:" + ",".join(dates) if dates else "")
    return {
        "status": "ok" if warning_count == 0 else "price_warning",
        "position_count": int(len(df)),
        "total_market_value": round(float(pd.to_numeric(df["market_value"], errors="coerce").fillna(0).sum()), 2),
        "total_cost": round(float(pd.to_numeric(df["cost"], errors="coerce").fillna(0).sum()), 2),
        "total_unrealized_pnl": round(float(pd.to_numeric(df["unrealized_pnl"], errors="coerce").fillna(0).sum()), 2),
        "as_of_date": as_of_date,
        "price_warning_count": warning_count,
        "valuation_source": "paper_positions + etf_daily latest close",
    }


def _price_file(symbol: str, etf_daily_dir: Path) -> Path | None:
    if not symbol:
        return None
    prefix = "sh" if symbol.startswith(("5", "6")) else "sz"
    preferred = etf_daily_dir / f"{prefix}_{symbol}.csv"
    if preferred.exists():
        return preferred
    matches = sorted(etf_daily_dir.glob(f"*_{symbol}.csv"))
    return matches[0] if matches else None


def _normalize_symbol(value: object) -> str:
    text = str(value or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        return digits[:6]
    return text


def _position_cost(row: dict[str, Any], quantity: float) -> float:
    for key in ["total_cost", "cost", "raw_cost"]:
        value = _float(row.get(key))
        if value > 0:
            return value
    avg = _float(row.get("avg_cost")) or _float(row.get("entry_price"))
    return avg * quantity if avg > 0 and quantity > 0 else 0.0


def _float(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return numeric
