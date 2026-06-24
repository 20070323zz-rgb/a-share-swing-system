"""模拟交易复盘报告。

只读取本地模拟盘交易、持仓、绩效派生文件和 ETF 日线数据。
不接券商 API，不真实下单，不读取真实账户，不修改 paper_trades.csv /
paper_positions.csv，也不改变 paper_trade_engine.py 执行逻辑。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from config import ETF_DAILY_DIR, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR


AUDIT_FILE = REPORT_DIR / "trade_review_audit.md"
SUMMARY_MD_FILE = REPORT_DIR / "trade_review_summary.md"
SUMMARY_JSON_FILE = REPORT_DIR / "trade_review_summary.json"
DETAILS_CSV_FILE = REPORT_DIR / "trade_review_details.csv"
DETAILS_MD_FILE = REPORT_DIR / "trade_review_details.md"
OPEN_CSV_FILE = REPORT_DIR / "trade_review_open_positions.csv"
OPEN_MD_FILE = REPORT_DIR / "trade_review_open_positions.md"
LESSONS_MD_FILE = REPORT_DIR / "trade_review_lessons.md"
PERFORMANCE_PNL_FILE = REPORT_DIR / "paper_trade_pnl.csv"


DETAIL_COLUMNS = [
    "trade_id",
    "symbol",
    "name",
    "status",
    "side",
    "buy_date",
    "sell_date",
    "entry_price",
    "exit_price",
    "latest_price",
    "quantity",
    "gross_pnl",
    "cost",
    "net_pnl",
    "return_pct",
    "holding_days",
    "max_favorable_excursion",
    "max_favorable_excursion_pct",
    "max_adverse_excursion",
    "max_adverse_excursion_pct",
    "best_price_during_holding",
    "worst_price_during_holding",
    "entry_reason",
    "exit_reason",
    "signal_on_entry",
    "signal_on_exit",
    "rule_followed",
    "sell_timing_assessment",
    "cost_impact",
    "benchmark_510300_return_during_holding",
    "excess_return_vs_510300",
    "review_tag",
    "review_comment",
    "data_quality",
    "estimated_fields",
]


OPEN_COLUMNS = [
    "symbol",
    "name",
    "entry_date",
    "entry_price",
    "latest_price",
    "quantity",
    "market_value",
    "unrealized_pnl",
    "unrealized_return_pct",
    "holding_days",
    "max_favorable_excursion",
    "max_favorable_excursion_pct",
    "max_adverse_excursion",
    "max_adverse_excursion_pct",
    "current_drawdown_from_best",
    "risk_comment",
    "review_comment",
]


@dataclass
class Lot:
    symbol: str
    name: str
    buy_date: str
    entry_price: float
    quantity: int
    remaining: int
    cost_basis: float
    entry_reason: str
    signal_on_entry: str
    source: str

    @property
    def unit_cost(self) -> float:
        return self.cost_basis / self.quantity if self.quantity else 0.0


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    trades = _read_trades()
    positions = _read_positions()
    details = _build_review_details(trades, positions)
    open_positions = _build_open_positions(details, positions)
    summary = _build_summary(details, open_positions, trades, positions)

    details.to_csv(DETAILS_CSV_FILE, index=False)
    open_positions.to_csv(OPEN_CSV_FILE, index=False)
    SUMMARY_JSON_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    _write_audit(trades, positions, details)
    _write_summary_md(summary, details, open_positions)
    _write_details_md(details)
    _write_open_md(open_positions)
    _write_lessons_md(summary, details, open_positions)

    print(f"已生成交易复盘摘要：{SUMMARY_MD_FILE}")
    print(f"已生成交易复盘明细：{DETAILS_CSV_FILE}")


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
        "raw_close",
        "execution_price",
        "quantity",
        "gross_amount",
        "amount",
        "commission",
        "stamp_tax",
        "transfer_fee",
        "fee",
        "realized_pnl",
        "realized_pnl_pct",
        "slippage_rate",
        "is_simulated",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["execution_price"] = df["execution_price"].where(df["execution_price"] > 0, df["price"])
    df["gross_amount"] = df["gross_amount"].where(df["gross_amount"] > 0, df["amount"])
    df["fee"] = df["fee"].where(df["fee"] > 0, df["commission"] + df["stamp_tax"] + df["transfer_fee"])
    return df.sort_values(["date", "symbol", "action"]).copy()


def _read_positions() -> pd.DataFrame:
    if not PAPER_POSITIONS_FILE.exists() or PAPER_POSITIONS_FILE.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(PAPER_POSITIONS_FILE, dtype={"symbol": str}, keep_default_na=False).fillna("")
    for col in [
        "quantity",
        "avg_cost",
        "entry_price",
        "last_price",
        "current_price",
        "market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "holding_days",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["current_price"] = df["current_price"].where(df["current_price"] > 0, df["last_price"])
    df["entry_price"] = df["entry_price"].where(df["entry_price"] > 0, df["avg_cost"])
    return df


def _build_review_details(trades: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    rows: list[dict[str, Any]] = []
    lots: dict[str, list[Lot]] = {}
    latest_date = _latest_date(trades, positions)
    latest_prices = _latest_prices(positions)
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
        trade_date = row.get("trade_date") or str(pd.to_datetime(row.get("date")).date())
        name = row.get("name") or symbol

        if action == "BUY" and qty > 0:
            lots.setdefault(symbol, []).append(
                Lot(
                    symbol=symbol,
                    name=name,
                    buy_date=trade_date,
                    entry_price=price,
                    quantity=qty,
                    remaining=qty,
                    cost_basis=gross + cost,
                    entry_reason=str(row.get("reason", "")),
                    signal_on_entry=_signal_snapshot(row),
                    source=str(row.get("source", "")),
                )
            )
        elif action == "SELL" and qty > 0:
            remaining = qty
            allocated_cost = 0.0
            buy_dates: list[str] = []
            entry_prices: list[float] = []
            entry_reasons: list[str] = []
            signals_on_entry: list[str] = []
            matched_qty = 0
            for lot in lots.get(symbol, []):
                if remaining <= 0:
                    break
                take = min(remaining, lot.remaining)
                if take <= 0:
                    continue
                allocated_cost += lot.unit_cost * take
                buy_dates.append(lot.buy_date)
                entry_prices.append(lot.entry_price)
                entry_reasons.append(lot.entry_reason)
                signals_on_entry.append(lot.signal_on_entry)
                lot.remaining -= take
                remaining -= take
                matched_qty += take
            entry_price = sum(entry_prices) / len(entry_prices) if entry_prices else price
            buy_date = buy_dates[0] if buy_dates else ""
            proceeds = gross - cost
            net_pnl = proceeds - allocated_cost if allocated_cost else _to_float(row.get("realized_pnl"))
            ret = net_pnl / allocated_cost if allocated_cost else _nullable(row.get("realized_pnl_pct"))
            metrics = _excursion_metrics(symbol, buy_date, trade_date, entry_price, matched_qty)
            benchmark_return = _benchmark_return(buy_date, trade_date)
            sell_assessment = _sell_timing_assessment(price, metrics, symbol, trade_date)
            review_tag = _review_tags("closed", net_pnl, ret, metrics, benchmark_return, cost, allocated_cost, sell_assessment)
            rows.append(
                _detail_row(
                    trade_id=trade_id,
                    symbol=symbol,
                    name=name,
                    status="closed",
                    side="SELL",
                    buy_date=buy_date,
                    sell_date=trade_date,
                    entry_price=entry_price,
                    exit_price=price,
                    latest_price=_latest_price(symbol, latest_prices),
                    quantity=matched_qty,
                    gross_pnl=gross - allocated_cost if allocated_cost else None,
                    cost=cost,
                    net_pnl=net_pnl,
                    return_pct=ret,
                    holding_days=_days_between(buy_date, trade_date),
                    metrics=metrics,
                    entry_reason=" | ".join([x for x in entry_reasons if x]) or "N/A",
                    exit_reason=str(row.get("reason", "")) or "N/A",
                    signal_on_entry=" | ".join([x for x in signals_on_entry if x]) or "N/A",
                    signal_on_exit=_signal_snapshot(row),
                    rule_followed=_rule_followed(row),
                    sell_timing_assessment=sell_assessment,
                    cost_impact=cost / gross if gross else None,
                    benchmark_return=benchmark_return,
                    review_tag=review_tag,
                    review_comment=_review_comment("closed", net_pnl, ret, metrics, sell_assessment, benchmark_return),
                )
            )
            trade_id += 1

    for symbol, symbol_lots in lots.items():
        for lot in symbol_lots:
            if lot.remaining <= 0:
                continue
            latest_price = _latest_price(symbol, latest_prices)
            end_date = latest_date
            net_pnl = (latest_price - lot.unit_cost) * lot.remaining if latest_price else None
            ret = (latest_price / lot.unit_cost - 1) if latest_price and lot.unit_cost else None
            metrics = _excursion_metrics(symbol, lot.buy_date, end_date, lot.entry_price, lot.remaining)
            benchmark_return = _benchmark_return(lot.buy_date, end_date)
            review_tag = _review_tags("open", net_pnl, ret, metrics, benchmark_return, 0.0, lot.cost_basis, "持仓中")
            rows.append(
                _detail_row(
                    trade_id=trade_id,
                    symbol=symbol,
                    name=lot.name,
                    status="open",
                    side="HOLD",
                    buy_date=lot.buy_date,
                    sell_date="",
                    entry_price=lot.entry_price,
                    exit_price=None,
                    latest_price=latest_price,
                    quantity=lot.remaining,
                    gross_pnl=net_pnl,
                    cost=0.0,
                    net_pnl=net_pnl,
                    return_pct=ret,
                    holding_days=_days_between(lot.buy_date, end_date),
                    metrics=metrics,
                    entry_reason=lot.entry_reason or "N/A",
                    exit_reason="持仓中",
                    signal_on_entry=lot.signal_on_entry or "N/A",
                    signal_on_exit="N/A",
                    rule_followed="持仓中，尚未触发完整卖出闭环",
                    sell_timing_assessment="持仓中",
                    cost_impact=0.0,
                    benchmark_return=benchmark_return,
                    review_tag=review_tag,
                    review_comment=_review_comment("open", net_pnl, ret, metrics, "持仓中", benchmark_return),
                )
            )
            trade_id += 1
    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def _detail_row(
    *,
    trade_id: int,
    symbol: str,
    name: str,
    status: str,
    side: str,
    buy_date: str,
    sell_date: str,
    entry_price: float,
    exit_price: float | None,
    latest_price: float | None,
    quantity: int,
    gross_pnl: float | None,
    cost: float,
    net_pnl: float | None,
    return_pct: float | None,
    holding_days: int | None,
    metrics: dict[str, Any],
    entry_reason: str,
    exit_reason: str,
    signal_on_entry: str,
    signal_on_exit: str,
    rule_followed: str,
    sell_timing_assessment: str,
    cost_impact: float | None,
    benchmark_return: float | None,
    review_tag: str,
    review_comment: str,
) -> dict[str, Any]:
    excess = return_pct - benchmark_return if return_pct is not None and benchmark_return is not None else None
    estimated = ["MFE/MAE from daily high/low"]
    if status == "open":
        estimated.append("open trade PnL marked to latest local close")
    if benchmark_return is None:
        estimated.append("benchmark comparison unavailable")
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "name": name,
        "status": status,
        "side": side,
        "buy_date": buy_date,
        "sell_date": sell_date,
        "entry_price": _round(entry_price, 6),
        "exit_price": _round(exit_price, 6),
        "latest_price": _round(latest_price, 6),
        "quantity": quantity,
        "gross_pnl": _round(gross_pnl, 2),
        "cost": _round(cost, 2),
        "net_pnl": _round(net_pnl, 2),
        "return_pct": return_pct,
        "holding_days": holding_days,
        "max_favorable_excursion": metrics.get("mfe_amount"),
        "max_favorable_excursion_pct": metrics.get("mfe_pct"),
        "max_adverse_excursion": metrics.get("mae_amount"),
        "max_adverse_excursion_pct": metrics.get("mae_pct"),
        "best_price_during_holding": metrics.get("best_price"),
        "worst_price_during_holding": metrics.get("worst_price"),
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "signal_on_entry": signal_on_entry,
        "signal_on_exit": signal_on_exit,
        "rule_followed": rule_followed,
        "sell_timing_assessment": sell_timing_assessment,
        "cost_impact": cost_impact,
        "benchmark_510300_return_during_holding": benchmark_return,
        "excess_return_vs_510300": excess,
        "review_tag": review_tag,
        "review_comment": review_comment,
        "data_quality": metrics.get("data_quality", "ok"),
        "estimated_fields": "; ".join(estimated),
    }


def _build_open_positions(details: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
    if details.empty:
        return pd.DataFrame(columns=OPEN_COLUMNS)
    rows: list[dict[str, Any]] = []
    pos_map = positions.set_index(positions["symbol"].astype(str)).to_dict(orient="index") if not positions.empty and "symbol" in positions.columns else {}
    for row in details[details["status"].eq("open")].to_dict(orient="records"):
        symbol = str(row.get("symbol", ""))
        pos = pos_map.get(symbol, {})
        best = _to_float(row.get("best_price_during_holding"))
        latest = _to_float(row.get("latest_price"))
        current_drawdown = latest / best - 1 if best > 0 and latest > 0 else None
        risk_comment = _open_risk_comment(row, current_drawdown)
        rows.append(
            {
                "symbol": symbol,
                "name": row.get("name", symbol),
                "entry_date": row.get("buy_date", ""),
                "entry_price": row.get("entry_price", ""),
                "latest_price": row.get("latest_price", ""),
                "quantity": row.get("quantity", ""),
                "market_value": pos.get("market_value", ""),
                "unrealized_pnl": row.get("net_pnl", ""),
                "unrealized_return_pct": row.get("return_pct", ""),
                "holding_days": row.get("holding_days", ""),
                "max_favorable_excursion": row.get("max_favorable_excursion", ""),
                "max_favorable_excursion_pct": row.get("max_favorable_excursion_pct", ""),
                "max_adverse_excursion": row.get("max_adverse_excursion", ""),
                "max_adverse_excursion_pct": row.get("max_adverse_excursion_pct", ""),
                "current_drawdown_from_best": current_drawdown,
                "risk_comment": risk_comment,
                "review_comment": row.get("review_comment", ""),
            }
        )
    return pd.DataFrame(rows, columns=OPEN_COLUMNS)


def _build_summary(details: pd.DataFrame, open_positions: pd.DataFrame, trades: pd.DataFrame, positions: pd.DataFrame) -> dict[str, Any]:
    closed = details[details["status"].eq("closed")].copy() if not details.empty else pd.DataFrame()
    open_rows = details[details["status"].eq("open")].copy() if not details.empty else pd.DataFrame()
    pnl = pd.to_numeric(details.get("net_pnl", pd.Series(dtype=float)), errors="coerce") if not details.empty else pd.Series(dtype=float)
    closed_pnl = pd.to_numeric(closed.get("net_pnl", pd.Series(dtype=float)), errors="coerce") if not closed.empty else pd.Series(dtype=float)
    open_pnl = pd.to_numeric(open_rows.get("net_pnl", pd.Series(dtype=float)), errors="coerce") if not open_rows.empty else pd.Series(dtype=float)
    wins = closed_pnl[closed_pnl > 0]
    losses = closed_pnl[closed_pnl < 0]
    largest_profit = float(pnl.max()) if not pnl.dropna().empty else None
    largest_loss = float(pnl.min()) if not pnl.dropna().empty else None
    mfe_pct = pd.to_numeric(details.get("max_favorable_excursion_pct", pd.Series(dtype=float)), errors="coerce") if not details.empty else pd.Series(dtype=float)
    mae_pct = pd.to_numeric(details.get("max_adverse_excursion_pct", pd.Series(dtype=float)), errors="coerce") if not details.empty else pd.Series(dtype=float)
    cost_total = float(pd.to_numeric(details.get("cost", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()) if not details.empty else 0.0
    main_issue = "样本太少，且已实现盈亏为负；当前总盈利主要依赖未实现浮盈，不能判断策略稳定盈利。"
    if not open_pnl.empty and float(open_pnl.sum()) <= 0:
        main_issue = "未平仓持仓暂未贡献正收益，需继续观察买入质量和止损复核。"
    positive_signal = "当前未平仓持仓合计浮盈为正，说明部分买入信号已有正反馈，但仍需观察能否转为已实现收益。"
    if open_pnl.empty or float(open_pnl.sum()) <= 0:
        positive_signal = "当前正面信号不足，暂以风险复核和样本积累为主。"
    return {
        "status": "active",
        "trade_count": int(len(trades)),
        "review_trade_count": int(len(details)),
        "closed_trade_count": int(len(closed)),
        "open_position_count": int(len(open_rows)),
        "winning_trade_count": int(len(wins)),
        "losing_trade_count": int(len(losses)),
        "largest_net_profit": _round(largest_profit, 2),
        "largest_net_loss": _round(largest_loss, 2),
        "largest_unrealized_pnl": _round(float(open_pnl.max()), 2) if not open_pnl.dropna().empty else None,
        "largest_mfe_pct": float(mfe_pct.max()) if not mfe_pct.dropna().empty else None,
        "largest_mae_pct": float(mae_pct.min()) if not mae_pct.dropna().empty else None,
        "max_unrealized_trade": _record_for_extreme(open_rows, "net_pnl", largest=True),
        "max_adverse_trade": _record_for_extreme(details, "max_adverse_excursion_pct", largest=False),
        "cost_impact_total": _round(cost_total, 2),
        "main_issue": main_issue,
        "positive_signal": positive_signal,
        "should_not_conclude": "不应得出策略已稳定盈利、可以实盘、shadow 模型可接入执行层等结论。",
        "next_focus": [
            "观察未实现浮盈能否转为已实现收益",
            "观察卖出规则是否过早或过晚",
            "继续积累更多已平仓样本",
            "关注 515880 data_health caution 对持仓风险的影响",
        ],
        "sample_warning": "样本较少，不能判断策略稳定盈利。",
        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
            "paper_trade_engine_modified": False,
        },
    }


def _excursion_metrics(symbol: str, start_date: str, end_date: str, entry_price: float, quantity: int) -> dict[str, Any]:
    if not start_date or not end_date or entry_price <= 0 or quantity <= 0:
        return {"data_quality": "insufficient_input"}
    prices = _load_symbol_prices(symbol)
    if prices.empty:
        return {"data_quality": "insufficient_price_history"}
    start = pd.to_datetime(start_date, errors="coerce")
    end = pd.to_datetime(end_date, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return {"data_quality": "insufficient_date"}
    window = prices[(prices["date"] >= start.normalize()) & (prices["date"] <= end.normalize())].copy()
    if window.empty:
        return {"data_quality": "insufficient_price_window"}
    best_price = float(window["high"].max())
    worst_price = float(window["low"].min())
    mfe = (best_price - entry_price) * quantity
    mae = (worst_price - entry_price) * quantity
    return {
        "mfe_amount": _round(mfe, 2),
        "mfe_pct": best_price / entry_price - 1,
        "mae_amount": _round(mae, 2),
        "mae_pct": worst_price / entry_price - 1,
        "best_price": _round(best_price, 6),
        "worst_price": _round(worst_price, 6),
        "data_quality": "ok",
    }


def _load_symbol_prices(symbol: str) -> pd.DataFrame:
    code = str(symbol).strip()
    if not code:
        return pd.DataFrame()
    prefix = "sh" if code.startswith(("5", "6")) else "sz"
    path = ETF_DAILY_DIR / f"{prefix}_{code}.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, usecols=lambda col: col in {"date", "open", "high", "low", "close"})
    except Exception:
        return pd.DataFrame()
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            df[col] = df["close"]
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["date", "close"]).sort_values("date").copy()


def _benchmark_return(start_date: str, end_date: str) -> float | None:
    prices = _load_symbol_prices("510300")
    if prices.empty or not start_date or not end_date:
        return None
    start_price = _price_on_or_before(prices, start_date)
    end_price = _price_on_or_before(prices, end_date)
    if not start_price or not end_price:
        return None
    return end_price / start_price - 1


def _price_on_or_before(prices: pd.DataFrame, day: str) -> float | None:
    date = pd.to_datetime(day, errors="coerce")
    if pd.isna(date):
        return None
    subset = prices[prices["date"] <= date.normalize()]
    if subset.empty:
        return None
    return float(subset["close"].iloc[-1])


def _sell_timing_assessment(exit_price: float, metrics: dict[str, Any], symbol: str, sell_date: str) -> str:
    if metrics.get("data_quality") != "ok":
        return "样本不足"
    best = _to_float(metrics.get("best_price"))
    worst = _to_float(metrics.get("worst_price"))
    if best <= 0 or worst <= 0 or exit_price <= 0:
        return "无法判断"
    range_width = max(best - worst, 1e-9)
    location = (exit_price - worst) / range_width
    post = _post_sell_return(symbol, sell_date)
    if location >= 0.80:
        return "卖出较好"
    if post is not None and post > 0.05:
        return "可能卖早"
    if post is not None and post < -0.03:
        return "止损有效"
    if location <= 0.25:
        return "可能卖晚"
    return "无法判断"


def _post_sell_return(symbol: str, sell_date: str, lookahead_days: int = 5) -> float | None:
    prices = _load_symbol_prices(symbol)
    if prices.empty:
        return None
    date = pd.to_datetime(sell_date, errors="coerce")
    if pd.isna(date):
        return None
    after = prices[prices["date"] > date.normalize()].head(lookahead_days)
    sell_price = _price_on_or_before(prices, sell_date)
    if after.empty or not sell_price:
        return None
    return float(after["close"].max()) / sell_price - 1


def _review_tags(
    status: str,
    net_pnl: float | None,
    return_pct: float | None,
    metrics: dict[str, Any],
    benchmark_return: float | None,
    cost: float,
    cost_basis: float,
    sell_assessment: str,
) -> str:
    tags: list[str] = []
    pnl = _to_float(net_pnl)
    if status == "open":
        tags.append("持仓中")
    tags.append("盈利交易" if pnl > 0 else "亏损交易" if pnl < 0 else "盈亏接近零")
    if status == "open" and pnl > 0:
        tags.append("浮盈未兑现")
    if metrics.get("data_quality") != "ok":
        tags.append("数据不足")
    if _to_float(metrics.get("mae_pct")) <= -0.06:
        tags.append("回撤较大")
    elif metrics.get("data_quality") == "ok":
        tags.append("回撤较小")
    if cost_basis and cost / cost_basis > 0.003:
        tags.append("成本拖累")
    if benchmark_return is not None and return_pct is not None:
        tags.append("跑赢510300" if return_pct > benchmark_return else "跑输510300")
    if sell_assessment == "可能卖早":
        tags.append("卖早可能")
    if sell_assessment == "可能卖晚":
        tags.append("卖晚可能")
    if len(tags) <= 2:
        tags.append("样本不足")
    return ";".join(dict.fromkeys(tags))


def _review_comment(status: str, net_pnl: float | None, return_pct: float | None, metrics: dict[str, Any], sell_assessment: str, benchmark_return: float | None) -> str:
    pnl = _to_float(net_pnl)
    pct_text = _fmt_pct(return_pct)
    mfe = _fmt_pct(metrics.get("mfe_pct"))
    mae = _fmt_pct(metrics.get("mae_pct"))
    bench = _fmt_pct(benchmark_return)
    if status == "open":
        if pnl > 0:
            return f"该笔交易仍处于持仓中，当前未实现盈亏为正（{pct_text}），最大浮盈 {mfe}，最大浮亏 {mae}；尚未落袋，需要观察浮盈能否转化为已实现收益。"
        return f"该笔交易仍处于持仓中，当前未实现盈亏不理想（{pct_text}），最大浮亏 {mae}；需要复核买入信号和止损距离。"
    if pnl < 0:
        return f"该笔交易已平仓，净盈亏为负（{pct_text}），期间最大浮亏 {mae}；卖出评估为“{sell_assessment}”，后续需观察入场是否偏早或止损是否过紧。同期 510300 为 {bench}。"
    return f"该笔交易已平仓并盈利（{pct_text}），期间最大浮盈 {mfe}；卖出评估为“{sell_assessment}”。样本仍少，不宜据此判断规则稳定有效。同期 510300 为 {bench}。"


def _open_risk_comment(row: dict[str, Any], current_drawdown: float | None) -> str:
    pnl = _to_float(row.get("net_pnl"))
    if current_drawdown is not None and current_drawdown <= -0.05:
        return "从持仓期高点已有明显回撤，需观察浮盈回吐风险。"
    if pnl > 0:
        return "当前仍为浮盈，但属于未实现收益，需观察是否能继续保持。"
    return "当前浮盈贡献不足，需关注止损距离与信号是否继续有效。"


def _signal_snapshot(row: dict[str, Any]) -> str:
    parts = []
    reason = str(row.get("reason", ""))
    for key in ["rank_score", "mid_trend", "short_swing", "source"]:
        marker = f"{key}="
        if marker in reason:
            value = reason.split(marker, 1)[1].split(";", 1)[0].strip()
            parts.append(f"{key}={value}")
    strategy = str(row.get("strategy_source", "")).strip()
    if strategy:
        parts.append(f"strategy={strategy}")
    return "; ".join(parts) if parts else "N/A"


def _rule_followed(row: dict[str, Any]) -> str:
    source = str(row.get("source", "")).strip()
    order_type = str(row.get("order_type", "")).strip()
    is_simulated = _to_float(row.get("is_simulated"))
    if is_simulated == 1 and (source or order_type):
        return f"是，模拟流水来源 {source or order_type}"
    if source or order_type:
        return f"无法完全验证，记录来源 {source or order_type}"
    return "无法判断，交易流水缺少来源字段"


def _latest_date(trades: pd.DataFrame, positions: pd.DataFrame) -> str:
    dates: list[str] = []
    for symbol in positions.get("symbol", pd.Series(dtype=str)).astype(str):
        prices = _load_symbol_prices(symbol)
        if not prices.empty:
            dates.append(str(prices["date"].max().date()))
    if dates:
        return max(dates)
    if not trades.empty:
        return str(trades["date"].max().date())
    return pd.Timestamp.now().strftime("%Y-%m-%d")


def _latest_prices(positions: pd.DataFrame) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in positions.to_dict(orient="records"):
        symbol = str(row.get("symbol", "")).strip()
        price = _to_float(row.get("current_price")) or _to_float(row.get("last_price"))
        if symbol and price > 0:
            result[symbol] = price
    return result


def _latest_price(symbol: str, latest_prices: dict[str, float]) -> float | None:
    if symbol in latest_prices:
        return latest_prices[symbol]
    prices = _load_symbol_prices(symbol)
    if prices.empty:
        return None
    return float(prices["close"].iloc[-1])


def _record_for_extreme(df: pd.DataFrame, col: str, largest: bool) -> dict[str, Any] | None:
    if df.empty or col not in df.columns:
        return None
    work = df.copy()
    work["_metric"] = pd.to_numeric(work[col], errors="coerce")
    work = work.dropna(subset=["_metric"])
    if work.empty:
        return None
    row = work.sort_values("_metric", ascending=not largest).iloc[0].drop(labels=["_metric"]).to_dict()
    return {key: row.get(key) for key in ["symbol", "name", col, "net_pnl", "return_pct", "review_tag"] if key in row}


def _trade_cost(row: dict[str, Any]) -> float:
    fee = _to_float(row.get("fee"))
    commission = _to_float(row.get("commission"))
    stamp = _to_float(row.get("stamp_tax"))
    transfer = _to_float(row.get("transfer_fee"))
    return max(fee, commission + stamp + transfer)


def _days_between(start: str, end: str) -> int | None:
    try:
        return int((pd.to_datetime(end) - pd.to_datetime(start)).days)
    except Exception:
        return None


def _to_float(value: Any) -> float:
    try:
        if value in ("", None, "N/A"):
            return 0.0
        numeric = float(value)
    except Exception:
        return 0.0
    return 0.0 if pd.isna(numeric) else numeric


def _nullable(value: Any) -> float | None:
    try:
        numeric = float(value)
    except Exception:
        return None
    return None if pd.isna(numeric) else numeric


def _round(value: Any, digits: int) -> float | None:
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    if pd.isna(numeric):
        return None
    return round(numeric, digits)


def _fmt_money(value: Any) -> str:
    numeric = _to_float(value)
    sign = "+" if numeric > 0 else ""
    return f"{sign}{numeric:,.2f}"


def _fmt_pct(value: Any) -> str:
    if value in ("", None, "N/A"):
        return "暂无"
    try:
        numeric = float(value)
    except Exception:
        return "暂无"
    if pd.isna(numeric):
        return "暂无"
    return f"{numeric:.2%}"


def _write_audit(trades: pd.DataFrame, positions: pd.DataFrame, details: pd.DataFrame) -> None:
    trade_cols = ", ".join(trades.columns.tolist()) if not trades.empty else "无"
    position_cols = ", ".join(positions.columns.tolist()) if not positions.empty else "无"
    has_reason = "reason" in trades.columns
    has_signal = has_reason or "strategy_source" in trades.columns
    closed_count = int(details["status"].eq("closed").sum()) if not details.empty else 0
    open_count = int(details["status"].eq("open").sum()) if not details.empty else 0
    lines = [
        f"# 交易复盘数据审计 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本审计只读取本地模拟盘文件，不修改 `paper_trades.csv` / `paper_positions.csv`。",
        "",
        "## 当前交易记录字段",
        f"- `paper_trades.csv` 字段：{trade_cols}",
        f"- `paper_positions.csv` 字段：{position_cols}",
        "",
        "## 可用性判断",
        f"- 是否有买入/卖出理由字段：{'是，存在 reason/source/strategy_source' if has_reason else '否'}",
        f"- 是否有信号快照：{'部分有，可从 reason 中解析 rank_score/mid_trend/short_swing' if has_signal else '否'}",
        "- 是否能推导持仓周期：是，可由买入日期、卖出日期或最新数据日推导。",
        "- 是否能推导最大浮盈/最大浮亏：是，若本地 ETF 日线存在 high/low 字段。",
        f"- 是否能配对完整交易闭环：已平仓 {closed_count} 条；未平仓 {open_count} 条；采用 FIFO 配对。",
        "",
        "## 精确值",
        "- 交易日期、代码、方向、数量、成交价、成交金额、交易来源字段来自模拟交易流水。",
        "- 当前持仓数量、持仓市值、未实现盈亏来自模拟持仓文件。",
        "",
        "## 估算值",
        "- 最大浮盈/最大浮亏使用本地日线 high/low 估算。",
        "- 未平仓交易 PnL 使用最新本地 close/positions current_price 估算。",
        "- 510300 对比收益使用本地 510300 ETF close 估算。",
        "",
        "## 暂不能判断",
        "- 当前样本过少，不能判断策略稳定盈利。",
        "- 没有完整入场时刻分时数据，不能评估日内执行优劣。",
        "- 新闻/情绪/宏观触发原因未写入交易流水，不能做精确事件归因。",
    ]
    AUDIT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_md(summary: dict[str, Any], details: pd.DataFrame, open_positions: pd.DataFrame) -> None:
    lines = [
        f"# 交易复盘总览 {summary['last_updated']}",
        "",
        "本报告是模拟仓交易复盘，不是交易指令；不接券商 API，不真实下单。",
        "",
        "## 核心统计",
        f"- 当前交易流水总数：{summary['trade_count']}",
        f"- 复盘交易单元：{summary['review_trade_count']}",
        f"- 已平仓交易数：{summary['closed_trade_count']}",
        f"- 未平仓持仓数：{summary['open_position_count']}",
        f"- 盈利交易数：{summary['winning_trade_count']}",
        f"- 亏损交易数：{summary['losing_trade_count']}",
        f"- 当前最大单笔盈利：{_fmt_money(summary.get('largest_net_profit'))}",
        f"- 当前最大单笔亏损：{_fmt_money(summary.get('largest_net_loss'))}",
        f"- 最大 MFE：{_fmt_pct(summary.get('largest_mfe_pct'))}",
        f"- 最大 MAE：{_fmt_pct(summary.get('largest_mae_pct'))}",
        f"- 成本影响合计：{_fmt_money(summary.get('cost_impact_total'))}",
        "",
        "## 当前主要问题",
        f"- {summary['main_issue']}",
        "",
        "## 当前正面信号",
        f"- {summary['positive_signal']}",
        "",
        "## 当前不应下的结论",
        f"- {summary['should_not_conclude']}",
        "",
        "## 下一步观察重点",
    ]
    lines += [f"- {item}" for item in summary.get("next_focus", [])]
    lines += ["", "## 样本提醒", f"- {summary['sample_warning']}"]
    SUMMARY_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_details_md(details: pd.DataFrame) -> None:
    lines = [
        f"# 交易复盘明细 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 代码 | 名称 | 状态 | 买入日 | 卖出日 | 持仓天数 | 净盈亏 | 收益率 | 最大浮盈 | 最大浮亏 | 卖出评估 | 复盘标签 |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if details.empty:
        lines.append("| 暂无 | 暂无 | 暂无 | 暂无 | 暂无 | 0 | 0 | 暂无 | 暂无 | 暂无 | 暂无 | 暂无 |")
    else:
        for row in details.to_dict(orient="records"):
            lines.append(
                f"| {row.get('symbol','')} | {row.get('name','')} | {row.get('status','')} | {row.get('buy_date','')} | "
                f"{row.get('sell_date','')} | {row.get('holding_days','')} | {_fmt_money(row.get('net_pnl'))} | "
                f"{_fmt_pct(row.get('return_pct'))} | {_fmt_money(row.get('max_favorable_excursion'))} | "
                f"{_fmt_money(row.get('max_adverse_excursion'))} | {row.get('sell_timing_assessment','')} | {row.get('review_tag','')} |"
            )
    DETAILS_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_open_md(open_positions: pd.DataFrame) -> None:
    lines = [
        f"# 未平仓持仓复盘 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 代码 | 名称 | 买入日期 | 最新价 | 未实现盈亏 | 未实现收益率 | 最大浮盈 | 最大浮亏 | 从最高点回撤 | 复盘结论 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if open_positions.empty:
        lines.append("| 暂无 | 暂无 | 暂无 | 0 | 0 | 暂无 | 0 | 0 | 暂无 | 暂无 |")
    else:
        for row in open_positions.to_dict(orient="records"):
            lines.append(
                f"| {row.get('symbol','')} | {row.get('name','')} | {row.get('entry_date','')} | "
                f"{row.get('latest_price','')} | {_fmt_money(row.get('unrealized_pnl'))} | "
                f"{_fmt_pct(row.get('unrealized_return_pct'))} | {_fmt_money(row.get('max_favorable_excursion'))} | "
                f"{_fmt_money(row.get('max_adverse_excursion'))} | {_fmt_pct(row.get('current_drawdown_from_best'))} | "
                f"{row.get('review_comment','')} |"
            )
    OPEN_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_lessons_md(summary: dict[str, Any], details: pd.DataFrame, open_positions: pd.DataFrame) -> None:
    lines = [
        f"# 本周交易复盘结论 {summary['last_updated']}",
        "",
        "## 当前模拟仓的主要问题",
        f"- {summary['main_issue']}",
        "- 已实现盈亏仍为负，不能只看当前总权益为正。",
        "",
        "## 当前模拟仓的正面迹象",
        f"- {summary['positive_signal']}",
        "- 未平仓持仓中已有正反馈，但仍需要等待卖出闭环验证。",
        "",
        "## 需要继续观察的问题",
        "- 浮盈能否转化为已实现收益。",
        "- 卖出规则是否会过早止损或过晚退出。",
        "- 交易成本在小本金下是否持续拖累收益。",
        "- 515880 等 data_health caution 标的是否继续影响组合风险。",
        "",
        "## 不建议做的动作",
        "- 不建议把当前少量样本解释为策略成功。",
        "- 不建议接入真实交易。",
        "- 不建议把 shadow 模型接入执行层。",
        "- 不建议因为一两笔浮盈就放宽风控。",
        "",
        "## 下一步关注指标",
        "- 已实现盈亏是否转正。",
        "- 每笔交易 MFE/MAE 与最终盈亏的关系。",
        "- 跑赢/跑输 510300 的交易比例。",
        "- 卖出后 3-5 日价格表现，用于判断可能卖早或卖晚。",
    ]
    LESSONS_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
