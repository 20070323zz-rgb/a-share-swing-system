"""模拟仓绩效统计。

只读取本地 paper_trades / paper_positions / ETF 日线数据，生成派生报告。
不接券商 API，不真实下单，不读取真实账户，不修改原始模拟交易和持仓文件。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, PAPER_INITIAL_CASH, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR


EQUITY_CURVE_FILE = DATA_DIR / "paper_equity_curve.csv"
SUMMARY_JSON_FILE = REPORT_DIR / "paper_performance_summary.json"
SUMMARY_MD_FILE = REPORT_DIR / "paper_performance_summary.md"
DAILY_CSV_FILE = REPORT_DIR / "paper_performance_daily.csv"
TRADE_PNL_CSV_FILE = REPORT_DIR / "paper_trade_pnl.csv"
TRADE_PNL_MD_FILE = REPORT_DIR / "paper_trade_pnl.md"
EQUITY_MD_FILE = REPORT_DIR / "paper_equity_curve.md"
AUDIT_MD_FILE = REPORT_DIR / "paper_portfolio_metrics_audit.md"


@dataclass
class Lot:
    symbol: str
    name: str
    buy_date: str
    buy_price: float
    quantity: int
    remaining: int
    cost_total: float

    @property
    def unit_cost(self) -> float:
        return self.cost_total / self.quantity if self.quantity else 0.0


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    trades = _read_trades()
    positions = _read_positions()
    initial_cash = _infer_initial_cash(trades)
    latest_date = _latest_market_date(positions, trades)
    latest_prices = _latest_prices(positions)

    trade_pnl = _build_trade_pnl(trades, positions, latest_prices, latest_date)
    daily = _build_equity_curve(trades, initial_cash)
    if not daily.empty:
        daily.to_csv(DAILY_CSV_FILE, index=False)
        daily.to_csv(EQUITY_CURVE_FILE, index=False)
    else:
        pd.DataFrame(columns=_daily_columns()).to_csv(DAILY_CSV_FILE, index=False)
        pd.DataFrame(columns=_daily_columns()).to_csv(EQUITY_CURVE_FILE, index=False)

    trade_pnl.to_csv(TRADE_PNL_CSV_FILE, index=False)
    summary = _build_summary(trades, positions, daily, trade_pnl, initial_cash, latest_date)

    SUMMARY_JSON_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_summary_md(summary, daily, trade_pnl)
    _write_equity_md(summary, daily)
    _write_trade_pnl_md(trade_pnl)
    _write_audit_md(trades, positions, daily, trade_pnl, summary)
    print(f"已生成模拟仓绩效报告：{SUMMARY_MD_FILE}")
    print(f"已生成模拟仓权益曲线：{EQUITY_CURVE_FILE}")


def _read_trades() -> pd.DataFrame:
    if not PAPER_TRADES_FILE.exists() or PAPER_TRADES_FILE.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(PAPER_TRADES_FILE, dtype={"symbol": str}, keep_default_na=False).fillna("")
    if "date" not in df.columns and "trade_date" in df.columns:
        df["date"] = df["trade_date"]
    if "trade_date" not in df.columns:
        df["trade_date"] = df.get("date", "")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["trade_date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["symbol"] = df.get("symbol", "").astype(str).str.strip()
    df["action"] = df.get("action", "").astype(str).str.upper().str.strip()
    for col in [
        "price",
        "execution_price",
        "quantity",
        "gross_amount",
        "amount",
        "commission",
        "stamp_tax",
        "transfer_fee",
        "fee",
        "net_cash_change",
        "realized_pnl",
        "slippage_rate",
        "simulated_cash",
        "cash_after_trade",
        "position_value",
        "position_value_after_trade",
        "total_equity",
        "total_equity_after_trade",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["execution_price"] = df["execution_price"].where(df["execution_price"] > 0, df["price"])
    df["gross_amount"] = df["gross_amount"].where(df["gross_amount"] > 0, df["amount"])
    df["fee"] = df["fee"].where(df["fee"] > 0, df["commission"] + df["stamp_tax"] + df["transfer_fee"])
    missing_net = df["net_cash_change"].eq(0) & df["gross_amount"].gt(0)
    df.loc[missing_net & df["action"].eq("BUY"), "net_cash_change"] = -(df.loc[missing_net & df["action"].eq("BUY"), "gross_amount"] + df.loc[missing_net & df["action"].eq("BUY"), "fee"])
    df.loc[missing_net & df["action"].eq("SELL"), "net_cash_change"] = df.loc[missing_net & df["action"].eq("SELL"), "gross_amount"] - df.loc[missing_net & df["action"].eq("SELL"), "fee"]
    return df.sort_values(["date", "symbol", "action"]).copy()


def _read_positions() -> pd.DataFrame:
    if not PAPER_POSITIONS_FILE.exists() or PAPER_POSITIONS_FILE.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(PAPER_POSITIONS_FILE, dtype={"symbol": str}, keep_default_na=False).fillna("")
    for col in [
        "quantity",
        "avg_cost",
        "entry_price",
        "total_cost",
        "cost",
        "last_price",
        "current_price",
        "market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["current_price"] = df["current_price"].where(df["current_price"] > 0, df["last_price"])
    df["avg_cost"] = df["avg_cost"].where(df["avg_cost"] > 0, df["entry_price"])
    df["total_cost"] = df["total_cost"].where(df["total_cost"] > 0, df["cost"])
    df["market_value"] = df["market_value"].where(df["market_value"] > 0, df["quantity"] * df["current_price"])
    return df


def _infer_initial_cash(trades: pd.DataFrame) -> float:
    if not trades.empty:
        for col in ["total_equity_after_trade", "total_equity"]:
            values = pd.to_numeric(trades.get(col, pd.Series(dtype=float)), errors="coerce")
            positive = values[values > 0]
            if not positive.empty:
                return round(float(positive.iloc[0]), 2)
    return float(PAPER_INITIAL_CASH)


def _latest_market_date(positions: pd.DataFrame, trades: pd.DataFrame) -> str:
    dates: list[str] = []
    for symbol in positions.get("symbol", pd.Series(dtype=str)).astype(str):
        price_df = _load_symbol_prices(symbol)
        if not price_df.empty:
            dates.append(str(price_df["date"].max().date()))
    if dates:
        return max(dates)
    if not trades.empty:
        return str(trades["date"].max().date())
    return pd.Timestamp.now().strftime("%Y-%m-%d")


def _latest_prices(positions: pd.DataFrame) -> dict[str, float]:
    prices: dict[str, float] = {}
    for row in positions.to_dict(orient="records"):
        symbol = str(row.get("symbol", "")).strip()
        price = _to_float(row.get("current_price")) or _to_float(row.get("last_price"))
        if price <= 0:
            price_df = _load_symbol_prices(symbol)
            if not price_df.empty:
                price = float(price_df["close"].iloc[-1])
        if symbol and price > 0:
            prices[symbol] = price
    return prices


def _build_trade_pnl(trades: pd.DataFrame, positions: pd.DataFrame, latest_prices: dict[str, float], latest_date: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    lots: dict[str, list[Lot]] = {}
    trade_id = 1
    for row in trades.to_dict(orient="records"):
        symbol = str(row.get("symbol", "")).strip()
        if not symbol:
            continue
        action = str(row.get("action", "")).upper()
        qty = int(_to_float(row.get("quantity")))
        price = _to_float(row.get("execution_price")) or _to_float(row.get("price"))
        gross = _to_float(row.get("gross_amount")) or _to_float(row.get("amount")) or qty * price
        cost = _trade_cost(row)
        date = row.get("trade_date") or str(pd.to_datetime(row.get("date")).date())
        name = row.get("name") or symbol
        if action == "BUY" and qty > 0:
            lots.setdefault(symbol, []).append(Lot(symbol, name, date, price, qty, qty, gross + cost))
        elif action == "SELL" and qty > 0:
            remaining = qty
            allocated_cost = 0.0
            buy_dates: list[str] = []
            buy_prices: list[float] = []
            for lot in lots.get(symbol, []):
                if remaining <= 0:
                    break
                take = min(remaining, lot.remaining)
                if take <= 0:
                    continue
                allocated_cost += lot.unit_cost * take
                buy_dates.append(lot.buy_date)
                buy_prices.append(lot.buy_price)
                lot.remaining -= take
                remaining -= take
            proceeds = gross - cost
            net_pnl = proceeds - allocated_cost
            ret = net_pnl / allocated_cost if allocated_cost else None
            rows.append(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "name": name,
                    "buy_date": buy_dates[0] if buy_dates else "",
                    "sell_date": date,
                    "buy_price": round(sum(buy_prices) / len(buy_prices), 6) if buy_prices else None,
                    "sell_price": round(price, 6),
                    "quantity": qty - remaining,
                    "gross_pnl": round(gross - allocated_cost, 2) if allocated_cost else None,
                    "cost": round(cost, 2),
                    "net_pnl": round(net_pnl, 2) if allocated_cost else _nullable(row.get("realized_pnl")),
                    "return_pct": ret,
                    "holding_days": _days_between(buy_dates[0], date) if buy_dates else None,
                    "status": "closed",
                    "note": "FIFO 配对；仅模拟盘派生统计。",
                }
            )
            trade_id += 1
    for symbol, symbol_lots in lots.items():
        latest_price = latest_prices.get(symbol, 0.0)
        pos_meta = _position_meta(positions, symbol)
        for lot in symbol_lots:
            if lot.remaining <= 0:
                continue
            remaining_cost = lot.unit_cost * lot.remaining
            market_value = latest_price * lot.remaining
            net_pnl = market_value - remaining_cost if latest_price > 0 else None
            rows.append(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "name": lot.name or pos_meta.get("name", symbol),
                    "buy_date": lot.buy_date,
                    "sell_date": "",
                    "buy_price": round(lot.buy_price, 6),
                    "sell_price": None,
                    "quantity": lot.remaining,
                    "gross_pnl": round(net_pnl, 2) if net_pnl is not None else None,
                    "cost": 0.0,
                    "net_pnl": round(net_pnl, 2) if net_pnl is not None else None,
                    "return_pct": net_pnl / remaining_cost if remaining_cost else None,
                    "holding_days": _days_between(lot.buy_date, latest_date),
                    "status": "open",
                    "note": "未平仓持仓，按最新本地 close 估算未实现盈亏。",
                }
            )
            trade_id += 1
    return pd.DataFrame(rows, columns=[
        "trade_id",
        "symbol",
        "name",
        "buy_date",
        "sell_date",
        "buy_price",
        "sell_price",
        "quantity",
        "gross_pnl",
        "cost",
        "net_pnl",
        "return_pct",
        "holding_days",
        "status",
        "note",
    ])


def _build_equity_curve(trades: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=_daily_columns())
    symbols = sorted(set(trades["symbol"].astype(str)))
    price_map = {symbol: _load_symbol_prices(symbol) for symbol in symbols}
    available_dates = sorted(set().union(*[set(df["date"]) for df in price_map.values() if not df.empty]))
    if not available_dates:
        available_dates = sorted(pd.to_datetime(trades["date"]).dt.normalize().unique())
    start = pd.to_datetime(trades["date"].min()).normalize()
    end = max(pd.to_datetime(available_dates).max(), pd.to_datetime(trades["date"].max()).normalize())
    dates = [d for d in available_dates if start <= d <= end]
    if not dates:
        dates = list(pd.date_range(start, end, freq="D"))

    trades_by_date = {key: frame for key, frame in trades.groupby(trades["date"].dt.normalize())}
    cash = float(initial_cash)
    holdings: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    prev_equity: float | None = None
    max_equity = float(initial_cash)
    benchmark = _benchmark_returns(dates)

    for day in dates:
        for row in trades_by_date.get(pd.Timestamp(day), pd.DataFrame()).to_dict(orient="records"):
            symbol = str(row.get("symbol", "")).strip()
            action = str(row.get("action", "")).upper()
            qty = int(_to_float(row.get("quantity")))
            cash += _to_float(row.get("net_cash_change"))
            if action == "BUY":
                holdings[symbol] = holdings.get(symbol, 0) + qty
            elif action == "SELL":
                holdings[symbol] = max(0, holdings.get(symbol, 0) - qty)
        position_value = 0.0
        missing_prices: list[str] = []
        for symbol, qty in holdings.items():
            if qty <= 0:
                continue
            price = _price_on_or_before(price_map.get(symbol, pd.DataFrame()), day)
            if price is None:
                missing_prices.append(symbol)
                continue
            position_value += qty * price
        total_equity = cash + position_value
        max_equity = max(max_equity, total_equity)
        daily_pnl = 0.0 if prev_equity is None else total_equity - prev_equity
        daily_return = 0.0 if prev_equity in (None, 0) else daily_pnl / prev_equity
        cumulative_pnl = total_equity - initial_cash
        cumulative_return = cumulative_pnl / initial_cash if initial_cash else None
        drawdown = total_equity / max_equity - 1 if max_equity else None
        rows.append(
            {
                "date": pd.Timestamp(day).strftime("%Y-%m-%d"),
                "cash": round(cash, 2),
                "position_value": round(position_value, 2),
                "total_equity": round(total_equity, 2),
                "daily_pnl": round(daily_pnl, 2),
                "daily_return": daily_return,
                "cumulative_pnl": round(cumulative_pnl, 2),
                "cumulative_return": cumulative_return,
                "drawdown": drawdown,
                "benchmark_510300_return": benchmark.get(pd.Timestamp(day).strftime("%Y-%m-%d")),
                "note": "missing_price:" + ",".join(missing_prices) if missing_prices else "derived_from_local_trades_and_close",
            }
        )
        prev_equity = total_equity
    return pd.DataFrame(rows, columns=_daily_columns())


def _build_summary(
    trades: pd.DataFrame,
    positions: pd.DataFrame,
    daily: pd.DataFrame,
    trade_pnl: pd.DataFrame,
    initial_cash: float,
    latest_date: str,
) -> dict[str, Any]:
    current_cash = _latest_trade_value(trades, ["simulated_cash", "cash_after_trade"], initial_cash)
    current_position_value = _sum_numeric(positions, "market_value")
    current_total_equity = current_cash + current_position_value
    if not daily.empty:
        current_cash = float(daily["cash"].iloc[-1])
        current_position_value = float(daily["position_value"].iloc[-1])
        current_total_equity = float(daily["total_equity"].iloc[-1])
    realized = _sum_numeric(trades[trades["action"].eq("SELL")] if not trades.empty else trades, "realized_pnl")
    if realized == 0 and not trade_pnl.empty:
        realized = float(pd.to_numeric(trade_pnl.loc[trade_pnl["status"].eq("closed"), "net_pnl"], errors="coerce").fillna(0.0).sum())
    unrealized = _sum_numeric(positions, "unrealized_pnl")
    total_cost = sum(_trade_cost(row) for row in trades.to_dict(orient="records")) if not trades.empty else 0.0
    commission = _sum_numeric(trades, "commission") + _sum_numeric(trades, "fee")
    if not trades.empty and "fee" in trades.columns and "commission" in trades.columns:
        commission = float(pd.concat([trades["commission"], trades["fee"]], axis=1).max(axis=1).sum())
    slippage_total = _estimate_slippage(trades)
    closed = trade_pnl[trade_pnl["status"].eq("closed")].copy() if not trade_pnl.empty else pd.DataFrame()
    wins = closed[pd.to_numeric(closed.get("net_pnl", pd.Series(dtype=float)), errors="coerce").fillna(0.0) > 0] if not closed.empty else pd.DataFrame()
    losses = closed[pd.to_numeric(closed.get("net_pnl", pd.Series(dtype=float)), errors="coerce").fillna(0.0) < 0] if not closed.empty else pd.DataFrame()
    avg_win = float(pd.to_numeric(wins.get("net_pnl", pd.Series(dtype=float)), errors="coerce").mean()) if not wins.empty else None
    avg_loss = float(pd.to_numeric(losses.get("net_pnl", pd.Series(dtype=float)), errors="coerce").mean()) if not losses.empty else None
    gross_profit = float(pd.to_numeric(wins.get("net_pnl", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()) if not wins.empty else 0.0
    gross_loss = abs(float(pd.to_numeric(losses.get("net_pnl", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())) if not losses.empty else 0.0
    return {
        "status": "active",
        "initial_cash": round(initial_cash, 2),
        "initial_cash_source": "paper_trades.total_equity_after_trade" if not trades.empty else "config.PAPER_INITIAL_CASH",
        "research_initial_cash_main": 20000.0,
        "current_cash": round(current_cash, 2),
        "current_position_value": round(current_position_value, 2),
        "current_total_equity": round(current_total_equity, 2),
        "total_pnl_amount": round(current_total_equity - initial_cash, 2),
        "total_return_pct": (current_total_equity - initial_cash) / initial_cash if initial_cash else None,
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
        "max_equity": round(float(daily["total_equity"].max()), 2) if not daily.empty else round(current_total_equity, 2),
        "min_equity": round(float(daily["total_equity"].min()), 2) if not daily.empty else round(current_total_equity, 2),
        "max_drawdown": float(daily["drawdown"].min()) if not daily.empty else 0.0,
        "trade_count": int(len(trades)),
        "buy_count": int(trades["action"].eq("BUY").sum()) if not trades.empty else 0,
        "sell_count": int(trades["action"].eq("SELL").sum()) if not trades.empty else 0,
        "winning_trade_count": int(len(wins)),
        "losing_trade_count": int(len(losses)),
        "win_rate": int(len(wins)) / int(len(closed)) if len(closed) else None,
        "avg_win": round(avg_win, 2) if avg_win is not None and pd.notna(avg_win) else None,
        "avg_loss": round(avg_loss, 2) if avg_loss is not None and pd.notna(avg_loss) else None,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "total_cost": round(total_cost, 2),
        "commission_total": round(commission, 2),
        "slippage_total": round(slippage_total, 2),
        "daily_rows": int(len(daily)),
        "trade_pnl_rows": int(len(trade_pnl)),
        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_data_date": latest_date,
        "estimated_fields": [
            "paper_equity_curve uses local close prices and simulated trades",
            "open trade PnL is unrealized and mark-to-market",
            "slippage_total is estimated from raw close vs execution price when available",
        ],
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
        },
    }


def _daily_columns() -> list[str]:
    return [
        "date",
        "cash",
        "position_value",
        "total_equity",
        "daily_pnl",
        "daily_return",
        "cumulative_pnl",
        "cumulative_return",
        "drawdown",
        "benchmark_510300_return",
        "note",
    ]


def _load_symbol_prices(symbol: str) -> pd.DataFrame:
    code = str(symbol).strip()
    if not code:
        return pd.DataFrame()
    prefix = "sh" if code.startswith(("5", "6")) else "sz"
    path = ETF_DAILY_DIR / f"{prefix}_{code}.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, usecols=lambda col: col in {"date", "close"})
    except Exception:
        return pd.DataFrame()
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.dropna(subset=["date", "close"]).sort_values("date").copy()


def _benchmark_returns(dates: list[pd.Timestamp]) -> dict[str, float | None]:
    df = _load_symbol_prices("510300")
    if df.empty or not dates:
        return {pd.Timestamp(day).strftime("%Y-%m-%d"): None for day in dates}
    first_price = _price_on_or_before(df, min(dates))
    if not first_price:
        return {pd.Timestamp(day).strftime("%Y-%m-%d"): None for day in dates}
    result: dict[str, float | None] = {}
    for day in dates:
        price = _price_on_or_before(df, day)
        result[pd.Timestamp(day).strftime("%Y-%m-%d")] = price / first_price - 1 if price else None
    return result


def _price_on_or_before(df: pd.DataFrame, day: pd.Timestamp) -> float | None:
    if df.empty:
        return None
    subset = df[df["date"] <= pd.Timestamp(day).normalize()]
    if subset.empty:
        return None
    return float(subset["close"].iloc[-1])


def _latest_trade_value(trades: pd.DataFrame, cols: list[str], fallback: float) -> float:
    if trades.empty:
        return float(fallback)
    for col in cols:
        values = pd.to_numeric(trades.get(col, pd.Series(dtype=float)), errors="coerce")
        positive = values[values.notna()]
        if not positive.empty and float(positive.iloc[-1]) != 0:
            return float(positive.iloc[-1])
    cash = float(fallback)
    for row in trades.to_dict(orient="records"):
        cash += _to_float(row.get("net_cash_change"))
    return cash


def _trade_cost(row: dict[str, Any]) -> float:
    fee = _to_float(row.get("fee"))
    commission = _to_float(row.get("commission"))
    stamp = _to_float(row.get("stamp_tax"))
    transfer = _to_float(row.get("transfer_fee"))
    return max(fee, commission + stamp + transfer)


def _estimate_slippage(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    raw = pd.to_numeric(trades.get("raw_close", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    execution = pd.to_numeric(trades.get("execution_price", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    qty = pd.to_numeric(trades.get("quantity", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    return float((execution - raw).abs().mul(qty).sum())


def _position_meta(positions: pd.DataFrame, symbol: str) -> dict[str, Any]:
    if positions.empty or "symbol" not in positions.columns:
        return {}
    subset = positions[positions["symbol"].astype(str) == str(symbol)]
    return subset.iloc[0].to_dict() if not subset.empty else {}


def _sum_numeric(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).sum())


def _to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        numeric = float(value)
    except Exception:
        return 0.0
    return 0.0 if pd.isna(numeric) else numeric


def _nullable(value: Any) -> float | None:
    numeric = _to_float(value)
    return numeric if numeric != 0 else None


def _days_between(start: str, end: str) -> int | None:
    try:
        return int((pd.to_datetime(end) - pd.to_datetime(start)).days)
    except Exception:
        return None


def _fmt_money(value: Any) -> str:
    numeric = _to_float(value)
    return f"{numeric:,.2f}"


def _fmt_pct(value: Any) -> str:
    if value is None or value == "":
        return "暂无"
    try:
        numeric = float(value)
    except Exception:
        return "暂无"
    if pd.isna(numeric):
        return "暂无"
    return f"{numeric:.2%}"


def _tone_amount(value: Any) -> str:
    numeric = _to_float(value)
    sign = "+" if numeric > 0 else ""
    return f"{sign}{numeric:,.2f}"


def _write_summary_md(summary: dict[str, Any], daily: pd.DataFrame, trade_pnl: pd.DataFrame) -> None:
    lines = [
        f"# 模拟仓绩效摘要 {summary['last_updated']}",
        "",
        "本报告只读取本地模拟仓数据和 ETF 日线，不接券商 API，不真实下单，不读取真实账户。",
        "",
        "## 核心指标",
        f"- 初始本金：{_fmt_money(summary['initial_cash'])} 元（正式模拟仓实际口径）",
        f"- 当前现金：{_fmt_money(summary['current_cash'])} 元",
        f"- 当前持仓市值：{_fmt_money(summary['current_position_value'])} 元",
        f"- 当前总资产：{_fmt_money(summary['current_total_equity'])} 元",
        f"- 总盈亏：{_tone_amount(summary['total_pnl_amount'])} 元",
        f"- 总收益率：{_fmt_pct(summary['total_return_pct'])}",
        f"- 已实现盈亏：{_tone_amount(summary['realized_pnl'])} 元",
        f"- 未实现盈亏：{_tone_amount(summary['unrealized_pnl'])} 元",
        f"- 最大回撤：{_fmt_pct(summary['max_drawdown'])}",
        f"- 交易次数：{summary['trade_count']}，买入 {summary['buy_count']}，卖出 {summary['sell_count']}",
        f"- 胜率：{_fmt_pct(summary['win_rate'])}",
        f"- 总成本：{_fmt_money(summary['total_cost'])} 元，其中佣金约 {_fmt_money(summary['commission_total'])} 元，滑点估算 {_fmt_money(summary['slippage_total'])} 元",
        "",
        "## 数据口径",
        "- current_total_equity = 当前现金 + 当前持仓市值。",
        "- realized_pnl 来自模拟卖出流水或 FIFO 配对派生统计。",
        "- unrealized_pnl 来自当前本地持仓市值与持仓成本。",
        "- paper_equity_curve 使用本地 ETF close 和模拟交易流水逐日重估。",
        "- 若历史交易之前没有快照，不会伪造更早权益曲线。",
        "",
        "## 最近权益记录",
    ]
    if daily.empty:
        lines.append("- 暂无足够数据。")
    else:
        lines.append("| 日期 | 总资产 | 每日盈亏 | 累计盈亏 | 累计收益率 | 回撤 | 510300收益 |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in daily.tail(10).to_dict(orient="records"):
            lines.append(
                f"| {row['date']} | {_fmt_money(row['total_equity'])} | {_tone_amount(row['daily_pnl'])} | "
                f"{_tone_amount(row['cumulative_pnl'])} | {_fmt_pct(row['cumulative_return'])} | "
                f"{_fmt_pct(row['drawdown'])} | {_fmt_pct(row['benchmark_510300_return'])} |"
            )
    lines += [
        "",
        "## 交易盈亏概览",
        f"- 派生交易 PnL 记录：{len(trade_pnl)} 条",
        "- 未平仓记录按最新 close 估算未实现盈亏；已平仓记录按 FIFO 配对估算已实现盈亏。",
    ]
    SUMMARY_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_equity_md(summary: dict[str, Any], daily: pd.DataFrame) -> None:
    lines = [
        f"# 模拟仓权益曲线 {summary['last_updated']}",
        "",
        "本权益曲线是基于本地模拟交易流水和 ETF 日线 close 的派生结果。",
        "",
    ]
    if daily.empty:
        lines.append("暂无足够数据。")
    else:
        lines += [
            f"- 起始日期：{daily['date'].iloc[0]}",
            f"- 最新日期：{daily['date'].iloc[-1]}",
            f"- 当前总资产：{_fmt_money(summary['current_total_equity'])} 元",
            f"- 累计盈亏：{_tone_amount(summary['total_pnl_amount'])} 元",
            f"- 最大回撤：{_fmt_pct(summary['max_drawdown'])}",
            "",
            "| 日期 | 现金 | 持仓市值 | 总资产 | 每日盈亏 | 累计盈亏 | 累计收益率 | 回撤 | 510300收益 | 说明 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in daily.tail(30).to_dict(orient="records"):
            lines.append(
                f"| {row['date']} | {_fmt_money(row['cash'])} | {_fmt_money(row['position_value'])} | "
                f"{_fmt_money(row['total_equity'])} | {_tone_amount(row['daily_pnl'])} | "
                f"{_tone_amount(row['cumulative_pnl'])} | {_fmt_pct(row['cumulative_return'])} | "
                f"{_fmt_pct(row['drawdown'])} | {_fmt_pct(row['benchmark_510300_return'])} | {row.get('note','')} |"
            )
    EQUITY_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_trade_pnl_md(trade_pnl: pd.DataFrame) -> None:
    lines = [
        "# 模拟交易逐笔盈亏",
        "",
        "本报告为本地模拟交易派生统计，不代表真实账户，不触发任何买卖。",
        "",
    ]
    if trade_pnl.empty:
        lines.append("暂无足够交易数据。")
    else:
        lines += [
            "| trade_id | 代码 | 名称 | 买入日期 | 卖出日期 | 买入价 | 卖出价 | 数量 | 成本 | 净盈亏 | 收益率 | 持有天数 | 状态 |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in trade_pnl.to_dict(orient="records"):
            lines.append(
                f"| {row.get('trade_id')} | {row.get('symbol')} | {row.get('name')} | {row.get('buy_date','')} | "
                f"{row.get('sell_date','')} | {_fmt_money(row.get('buy_price'))} | {_fmt_money(row.get('sell_price')) if row.get('sell_price') not in [None, ''] else '暂无'} | "
                f"{row.get('quantity')} | {_fmt_money(row.get('cost'))} | {_tone_amount(row.get('net_pnl')) if row.get('net_pnl') not in [None, ''] else '暂无'} | "
                f"{_fmt_pct(row.get('return_pct'))} | {row.get('holding_days') if row.get('holding_days') is not None else '暂无'} | {row.get('status')} |"
            )
    TRADE_PNL_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_audit_md(trades: pd.DataFrame, positions: pd.DataFrame, daily: pd.DataFrame, trade_pnl: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        f"# 模拟仓绩效指标审计 {summary['last_updated']}",
        "",
        "本审计只读取本地模拟仓文件，不修改 paper_trades.csv / paper_positions.csv。",
        "",
        "## 当前数据来源",
        f"- 持仓来源：`{PAPER_POSITIONS_FILE}`，当前 {len(positions)} 条持仓记录。",
        f"- 交易来源：`{PAPER_TRADES_FILE}`，当前 {len(trades)} 条交易流水。",
        "- 最新估值价格：优先使用 positions 当前价；权益曲线使用 `data/etf_daily/` 本地 close。",
        "",
        "## 当前能计算的指标",
        "- 当前现金、持仓市值、当前总资产、总盈亏、总收益率。",
        "- 已实现盈亏：来自 SELL 流水或 FIFO 配对。",
        "- 未实现盈亏：来自当前持仓市值与成本。",
        "- 交易次数、买卖次数、胜率、平均盈利/亏损、profit factor。",
        "- 权益曲线、每日盈亏、累计盈亏、最大回撤。",
        "",
        "## 当前缺少或需要估算的字段",
        "- 早于第一笔模拟交易之前的权益历史不存在，不能伪造。",
        "- 若交易流水缺少完整 cost 字段，会使用 commission/stamp_tax/transfer_fee 或 fee 推导。",
        "- 未平仓逐笔 PnL 使用最新 close 估算，状态标记为 open。",
        "",
        "## 新增派生文件",
        f"- `{EQUITY_CURVE_FILE}`",
        f"- `{SUMMARY_JSON_FILE}`",
        f"- `{SUMMARY_MD_FILE}`",
        f"- `{DAILY_CSV_FILE}`",
        f"- `{TRADE_PNL_CSV_FILE}`",
        f"- `{TRADE_PNL_MD_FILE}`",
        f"- `{EQUITY_MD_FILE}`",
        "",
        "## 结论",
        f"- 是否需要新增 `data/paper_equity_curve.csv`：是，已新增。",
        f"- 当前权益曲线记录数：{len(daily)}。",
        f"- 当前逐笔 PnL 记录数：{len(trade_pnl)}。",
        "- 安全边界：未接券商 API，未真实下单，未读取真实账户。",
    ]
    AUDIT_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
