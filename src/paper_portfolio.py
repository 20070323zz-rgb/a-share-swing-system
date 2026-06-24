"""模拟盘持仓记录和估值报告。

本模块只读取/更新本地模拟盘 CSV，不连接券商 API，不下单，
不读取账号密码，也不会自动生成任何真实交易。
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from config import DATA_DIR, ETF_STOP_LOSS, INITIAL_CASH, LATEST_PAPER_PORTFOLIO_FILE, PAPER_EXECUTION_PRICE_TYPE, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR, WATCHLIST_FILE
from data_loader import load_price_data, read_watchlist


CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
LEGACY_CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"


POSITION_RECORD_COLUMNS = [
    "symbol",
    "name",
    "quantity",
    "avg_cost",
    "raw_cost",
    "total_cost",
    "commission_paid",
    "entry_date",
    "last_price",
    "etf_type",
    "risk_profile",
    "holding_profile",
    "group",
    "max_holding_days",
    "stop_loss_pct",
    "classification_reason",
    "stop_loss_price",
    "sell_review_status",
    "data_health_status",
    "protection_period",
    "updated_at",
    "strategy_source",
    "position_type",
    "entry_price",
    "cost",
    "stop_loss",
    "reason",
]
POSITION_CALC_COLUMNS = [
    "market_value",
    "unrealized_pnl",
    "unrealized_pnl_pct",
    "holding_days",
    "distance_to_stop_pct",
    "current_price",
    "unrealized_return",
    "risk_alert",
]
POSITION_COLUMNS = POSITION_RECORD_COLUMNS + POSITION_CALC_COLUMNS
TRADE_COLUMNS = [
    "date",
    "trade_date",
    "symbol",
    "name",
    "action",
    "price",
    "raw_close",
    "execution_price",
    "execution_price_type",
    "quantity",
    "gross_amount",
    "commission",
    "stamp_tax",
    "transfer_fee",
    "net_cash_change",
    "slippage_rate",
    "reason",
    "source",
    "created_at",
    "holding_days",
    "realized_pnl",
    "realized_pnl_pct",
    "cash_after_trade",
    "position_value_after_trade",
    "total_equity_after_trade",
    "strategy_source",
    "position_type",
    "amount",
    "fee",
    "order_type",
    "simulated_cash",
    "position_value",
    "total_equity",
    "is_simulated",
]


def update_paper_portfolio(
    run_date: str,
    latest_prices: dict[str, float],
    watchlist: pd.DataFrame,
) -> tuple[Path, dict]:
    """更新模拟盘估值 CSV 和 Markdown 报告。"""
    _ensure_templates()
    positions = _read_positions()
    trades = _read_trades()
    enriched = _enrich_positions(positions, run_date, latest_prices, watchlist)
    if os.environ.get("PAPER_PORTFOLIO_READONLY", "0") != "1":
        enriched.to_csv(PAPER_POSITIONS_FILE, index=False)
    summary = _portfolio_summary(enriched, trades)
    _write_report(run_date, enriched, trades, summary)
    return LATEST_PAPER_PORTFOLIO_FILE, summary


def apply_paper_buy_plan(
    run_date: str,
    allocations: list[dict],
    latest_prices: dict[str, float],
    watchlist: pd.DataFrame,
) -> dict:
    """Apply simulated BUY allocations to local paper CSV files only."""
    _ensure_templates()
    positions = _read_positions()
    trades = _read_trades()
    positions = _normalize_position_frame(positions)
    trades = _normalize_trade_frame(trades)

    existing_symbols = set(positions["symbol"].astype(str)) if not positions.empty else set()
    available_slots = max(0, 3 - len(existing_symbols))
    cash = _cash_from_trades(trades, fallback=INITIAL_CASH - _numeric_sum(positions, "cost"))
    executed: list[dict] = []
    skipped: list[dict] = []

    for item in allocations:
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        if code not in existing_symbols and available_slots <= 0:
            skipped.append({**item, "skip_reason": "max_positions_reached"})
            continue
        if _has_same_day_signal_trade(trades, run_date, code):
            executed.extend(_same_day_signal_trade_rows(trades, run_date, code))
            continue

        price = float(latest_prices.get(code) or item.get("close") or 0.0)
        planned_amount = float(item.get("suggested_amount", 0.0) or 0.0)
        existing_value = _position_market_value(positions, code, latest_prices)
        room = max(0.0, INITIAL_CASH * 0.20 - existing_value)
        amount = min(planned_amount, room, cash)
        quantity = _paper_quantity(amount, price)
        amount = round(quantity * price, 2)
        if price <= 0 or quantity <= 0 or amount <= 0:
            skipped.append({**item, "skip_reason": "amount_or_quantity_too_small"})
            continue

        reason = _paper_trade_reason(item)
        positions = _upsert_position(positions, item, run_date, price, quantity, amount, reason)
        cash = round(cash - amount, 2)
        position_value = round(_positions_value_at_close(positions, latest_prices, {code: price}), 2)
        total_equity = round(cash + position_value, 2)
        trade_row = {
            "date": run_date,
            "trade_date": run_date,
            "symbol": code,
            "name": item.get("name", code),
            "action": "BUY",
            "strategy_source": _strategy_source(item),
            "position_type": "core" if item.get("mid_signal") == "BUY" else "trial",
            "price": round(price, 6),
            "quantity": int(quantity),
            "amount": amount,
            "realized_pnl": 0.0,
            "fee": 0.0,
            "execution_price_type": "close_price",
            "order_type": "paper_buy",
            "source": "buy_signal_ranking",
            "reason": reason,
            "simulated_cash": cash,
            "position_value": position_value,
            "total_equity": total_equity,
            "is_simulated": 1,
        }
        trades = pd.concat([trades, pd.DataFrame([trade_row])], ignore_index=True)
        executed.append(trade_row)
        if code not in existing_symbols:
            existing_symbols.add(code)
            available_slots -= 1

    positions = _normalize_position_frame(positions)
    trades = _normalize_trade_frame(trades)
    positions.to_csv(PAPER_POSITIONS_FILE, index=False)
    trades.to_csv(PAPER_TRADES_FILE, index=False)
    return {
        "executed": executed,
        "skipped": skipped,
        "executed_count": len(executed),
        "skipped_count": len(skipped),
    }


def _ensure_templates() -> None:
    PAPER_POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PAPER_PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PAPER_POSITIONS_FILE.exists():
        pd.DataFrame(columns=POSITION_COLUMNS).to_csv(PAPER_POSITIONS_FILE, index=False)
    if not PAPER_TRADES_FILE.exists():
        pd.DataFrame(columns=TRADE_COLUMNS).to_csv(PAPER_TRADES_FILE, index=False)


def _read_positions() -> pd.DataFrame:
    if not PAPER_POSITIONS_FILE.exists() or PAPER_POSITIONS_FILE.stat().st_size == 0:
        return pd.DataFrame(columns=POSITION_COLUMNS)
    df = pd.read_csv(PAPER_POSITIONS_FILE, dtype={"symbol": str}, keep_default_na=False).fillna("")
    for col in POSITION_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[POSITION_COLUMNS].copy()


def _read_trades() -> pd.DataFrame:
    if not PAPER_TRADES_FILE.exists() or PAPER_TRADES_FILE.stat().st_size == 0:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    df = pd.read_csv(PAPER_TRADES_FILE, dtype={"symbol": str}, keep_default_na=False).fillna("")
    for col in TRADE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[TRADE_COLUMNS].copy()
    if "trade_date" in df.columns:
        df["date"] = df["date"].where(df["date"].astype(str).str.strip() != "", df["trade_date"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["trade_date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["symbol"] = df["symbol"].fillna("").astype(str).str.strip()
    df["action"] = df["action"].fillna("").astype(str).str.upper().str.strip()
    for col in [
        "price",
        "raw_close",
        "execution_price",
        "quantity",
        "gross_amount",
        "commission",
        "stamp_tax",
        "transfer_fee",
        "net_cash_change",
        "slippage_rate",
        "amount",
        "realized_pnl",
        "realized_pnl_pct",
        "fee",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["raw_close"] = df["raw_close"].where(df["raw_close"] > 0, df["price"])
    df["execution_price"] = df["execution_price"].where(df["execution_price"] > 0, df["price"])
    df["gross_amount"] = df["gross_amount"].where(df["gross_amount"] > 0, df["amount"])
    df["commission"] = df["commission"].where(df["commission"] > 0, df["fee"])
    df["amount"] = df["amount"].where(df["amount"] > 0, df["gross_amount"])
    df["fee"] = df["fee"].where(df["fee"] > 0, df["commission"] + df["stamp_tax"] + df["transfer_fee"])
    buy_mask = df["action"].eq("BUY")
    sell_mask = df["action"].eq("SELL")
    missing_net = df["net_cash_change"].eq(0) & df["gross_amount"].gt(0)
    df.loc[buy_mask & missing_net, "net_cash_change"] = -(df.loc[buy_mask & missing_net, "gross_amount"] + df.loc[buy_mask & missing_net, "fee"])
    df.loc[sell_mask & missing_net, "net_cash_change"] = df.loc[sell_mask & missing_net, "gross_amount"] - df.loc[sell_mask & missing_net, "fee"]
    df["execution_price_type"] = df["execution_price_type"].where(df["execution_price_type"].astype(str).str.strip() != "", PAPER_EXECUTION_PRICE_TYPE)
    for col in ["simulated_cash", "position_value", "total_equity", "cash_after_trade", "position_value_after_trade", "total_equity_after_trade"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["date"]).copy()


def _normalize_position_frame(df: pd.DataFrame) -> pd.DataFrame:
    for col in POSITION_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[POSITION_COLUMNS].copy()


def _normalize_trade_frame(df: pd.DataFrame) -> pd.DataFrame:
    for col in TRADE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df["trade_date"] = df["trade_date"].where(df["trade_date"].astype(str).str.strip() != "", df["date"])
    return df[TRADE_COLUMNS].copy()


def _enrich_positions(
    positions: pd.DataFrame,
    run_date: str,
    latest_prices: dict[str, float],
    watchlist: pd.DataFrame,
) -> pd.DataFrame:
    if positions.empty:
        return pd.DataFrame(columns=POSITION_COLUMNS)
    df = positions.copy()
    meta_map = watchlist.set_index(watchlist["code"].astype(str)).to_dict(orient="index") if not watchlist.empty else {}
    classification_map = _read_classification_map()
    sell_review = _read_sell_review_map()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["name"] = df.apply(lambda row: row["name"] if str(row["name"]).strip() else meta_map.get(str(row["symbol"]), {}).get("name", row["symbol"]), axis=1)
    df["strategy_source"] = df["strategy_source"].fillna("").astype(str).str.strip()
    df.loc[~df["strategy_source"].isin(["mid_trend", "short_swing", "resonance"]), "strategy_source"] = "mid_trend"
    df["position_type"] = df["position_type"].fillna("").astype(str).str.strip()
    df.loc[~df["position_type"].isin(["core", "trial"]), "position_type"] = "core"
    df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["entry_price", "quantity", "cost", "stop_loss", "avg_cost", "raw_cost", "total_cost", "commission_paid", "last_price", "stop_loss_price", "max_holding_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["avg_cost"] = df["avg_cost"].fillna(df["entry_price"])
    df["raw_cost"] = df["raw_cost"].fillna(df["cost"]).fillna(df["avg_cost"] * df["quantity"]).fillna(0.0)
    df["total_cost"] = df["total_cost"].fillna(df["cost"]).fillna(df["raw_cost"] + df["commission_paid"].fillna(0.0)).fillna(0.0)
    df["commission_paid"] = df["commission_paid"].fillna(0.0)
    df["cost"] = df["cost"].fillna(df["total_cost"]).fillna(0.0)
    df["entry_price"] = df["entry_price"].fillna(df["avg_cost"]).fillna(0.0)
    df["stop_loss_price"] = df["stop_loss_price"].fillna(df["stop_loss"]).fillna(df["entry_price"] * (1 - ETF_STOP_LOSS))
    df["stop_loss"] = df["stop_loss"].fillna(df["stop_loss_price"])
    df["last_price"] = df["symbol"].map(latest_prices).fillna(df["last_price"]).fillna(df["entry_price"]).fillna(0.0)
    df["current_price"] = df["last_price"]
    df["market_value"] = df["current_price"] * df["quantity"].fillna(0.0)
    df["unrealized_pnl"] = df["market_value"] - df["total_cost"]
    df["unrealized_return"] = df["unrealized_pnl"] / df["total_cost"].where(df["total_cost"] != 0)
    df["unrealized_pnl_pct"] = df["unrealized_return"]
    run_ts = pd.to_datetime(run_date)
    entry_ts = pd.to_datetime(df["entry_date"], errors="coerce")
    df["holding_days"] = (run_ts - entry_ts).dt.days
    df["distance_to_stop_pct"] = (df["current_price"] - df["stop_loss_price"]) / df["current_price"].where(df["current_price"] != 0)
    df["protection_period"] = df["holding_days"].apply(lambda x: "yes" if pd.notna(x) and x <= 2 else "no")
    df["updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    df["data_health_status"] = df["data_health_status"].where(~df["data_health_status"].apply(_is_blank), "N/A")
    df["sell_review_status"] = df["sell_review_status"].where(~df["sell_review_status"].apply(_is_blank), "N/A")
    if sell_review:
        df["sell_review_status"] = df.apply(lambda row: sell_review.get(str(row["symbol"]), {}).get("sell_review_status", row["sell_review_status"]), axis=1)
        df["data_health_status"] = df.apply(lambda row: sell_review.get(str(row["symbol"]), {}).get("data_health_status", row["data_health_status"]), axis=1)
        df["protection_period"] = df.apply(lambda row: sell_review.get(str(row["symbol"]), {}).get("protection_period", row["protection_period"]), axis=1)
    df["etf_type"] = df.apply(lambda row: classification_map.get(str(row["symbol"]), {}).get("etf_type", row.get("etf_type")) if _is_blank(row.get("etf_type")) or str(row.get("etf_type")) == "N/A" else row.get("etf_type"), axis=1)
    df["risk_profile"] = df.apply(lambda row: classification_map.get(str(row["symbol"]), {}).get("risk_profile", row.get("risk_profile", "")), axis=1)
    df["holding_profile"] = df.apply(lambda row: classification_map.get(str(row["symbol"]), {}).get("holding_profile", row.get("holding_profile", "")), axis=1)
    df["classification_reason"] = df.apply(lambda row: classification_map.get(str(row["symbol"]), {}).get("classification_reason", row.get("classification_reason", "")), axis=1)
    df["group"] = df.apply(lambda row: classification_map.get(str(row["symbol"]), {}).get("group", row.get("group", "N/A")) if _is_blank(row.get("group")) or str(row.get("group")) == "N/A" else row.get("group"), axis=1)
    df["stop_loss_pct"] = df.apply(lambda row: _safe_float(classification_map.get(str(row["symbol"]), {}).get("stop_loss_pct", row.get("stop_loss_pct", "")), float("nan")), axis=1)
    df["max_holding_days"] = df.apply(lambda row: _safe_float(classification_map.get(str(row["symbol"]), {}).get("max_holding_days", row.get("max_holding_days", "")), 30), axis=1)
    df["etf_type"] = df["etf_type"].where(~df["etf_type"].apply(_is_blank), "N/A")
    df["group"] = df["group"].where(~df["group"].apply(_is_blank), "N/A")
    df["risk_alert"] = df.apply(_position_risk_alert, axis=1)
    for col in ["entry_price", "quantity", "cost", "stop_loss", "avg_cost", "raw_cost", "total_cost", "commission_paid", "last_price", "stop_loss_price", "current_price", "market_value", "unrealized_pnl", "unrealized_return", "unrealized_pnl_pct", "holding_days", "distance_to_stop_pct", "max_holding_days", "stop_loss_pct"]:
        df[col] = df[col].fillna("")
    return df[POSITION_COLUMNS].copy()


def _position_risk_alert(row: pd.Series) -> str:
    try:
        current_price = float(row.get("current_price", 0))
        stop_loss = float(row.get("stop_loss", 0))
    except (TypeError, ValueError):
        return ""
    if stop_loss > 0 and current_price > 0 and current_price <= stop_loss:
        return "触及或低于模拟止损价"
    return ""


def _portfolio_summary(positions: pd.DataFrame, trades: pd.DataFrame) -> dict:
    market_value = _numeric_sum(positions, "market_value")
    cost = _numeric_sum(positions, "total_cost") or _numeric_sum(positions, "cost")
    realized_pnl = _realized_pnl_from_trades(trades)
    cash = _cash_from_trades(trades, fallback=INITIAL_CASH - cost)
    total_assets = cash + market_value
    risk_count = int((positions.get("risk_alert", pd.Series(dtype=str)).fillna("").astype(str).str.len() > 0).sum()) if not positions.empty else 0
    return {
        "initial_cash": INITIAL_CASH,
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "total_assets": round(total_assets, 2),
        "total_equity": round(total_assets, 2),
        "position_count": int(len(positions)),
        "unrealized_pnl": round(market_value - cost, 2),
        "unrealized_pnl_pct": round((market_value - cost) / cost, 6) if cost else 0.0,
        "realized_pnl": round(realized_pnl, 2),
        "total_pnl": round(realized_pnl + market_value - cost, 2),
        "trade_count": int(len(trades)),
        "risk_alert_count": risk_count,
        "has_risk_alert": risk_count > 0 or cash < 0,
    }


def _write_report(run_date: str, positions: pd.DataFrame, trades: pd.DataFrame, summary: dict) -> None:
    sell_review = _read_sell_review_map()
    lines = [
        f"# 模拟盘持仓报告 {run_date}",
        "",
        "本报告只读取本地模拟盘记录，不接券商 API，不下单，不读取账号密码。",
        "",
        "## 账户摘要",
        f"- 初始模拟本金：{summary['initial_cash']:.2f} 元",
        f"- 当前现金：{summary['cash']:.2f} 元",
        f"- 当前持仓市值：{summary['market_value']:.2f} 元",
        f"- 当前总资产：{summary['total_assets']:.2f} 元",
        f"- 当前持仓数：{summary['position_count']}",
        f"- 浮动盈亏：{summary['unrealized_pnl']:.2f} 元",
        f"- 浮动盈亏率：{summary['unrealized_pnl_pct']:.2%}",
        f"- 已实现盈亏：{summary['realized_pnl']:.2f} 元",
        f"- 总盈亏：{summary['total_pnl']:.2f} 元",
        f"- 模拟交易流水数：{summary['trade_count']}",
        f"- 风险提醒数量：{summary['risk_alert_count']}",
        "",
        "## 当前持仓",
    ]
    if positions.empty:
        lines.append("- 当前无模拟持仓。")
    else:
        lines.append("| symbol | name | etf_type | type_risk | type_max_days | type_severity | type_review_note | strategy_source | entry_date | entry_price | quantity | cost | current_price | market_value | unrealized_pnl | unrealized_return | holding_days | stop_loss | distance_to_stop | risk_alert |")
        lines.append("| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in positions.itertuples():
            review = sell_review.get(str(row.symbol), {})
            lines.append(
                f"| {row.symbol} | {row.name} | {getattr(row, 'etf_type', '')} | {review.get('type_risk_level', getattr(row, 'risk_profile', ''))} | "
                f"{_fmt(review.get('type_max_holding_days', getattr(row, 'max_holding_days', '')))} | {review.get('type_review_severity', '')} | "
                f"{str(review.get('etf_type_review_note', '')).replace('|', '/')[:180]} | {row.strategy_source} | {row.entry_date} | "
                f"{_fmt(row.entry_price)} | {_fmt(row.quantity)} | {_fmt(row.cost)} | {_fmt(row.current_price)} | "
                f"{_fmt(row.market_value)} | {_fmt(row.unrealized_pnl)} | {_fmt(row.unrealized_return)} | "
                f"{_fmt(row.holding_days)} | {_fmt(row.stop_loss)} | {_pct_fmt(getattr(row, 'distance_to_stop_pct', ''))} | {str(row.risk_alert).replace('|', '/')} |"
            )
    lines += [
        "",
        "## 已实现盈亏",
        f"- realized_pnl：{summary['realized_pnl']:.2f} 元",
        "- realized_pnl 仅来自 data/paper_trades.csv 的本地模拟 BUY/SELL 流水，不代表真实账户。",
    ]
    if trades.empty:
        lines.append("- 当前无模拟交易流水。")
    else:
        lines.append("| trade_date | symbol | name | action | price | quantity | amount | realized_pnl | execution_price_type | order_type | source | simulated_cash | position_value | total_equity | reason |")
        lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |")
        for row in trades.sort_values("date").tail(10).itertuples():
            lines.append(
                f"| {row.date.strftime('%Y-%m-%d')} | {row.symbol} | {row.name} | {row.action} | "
                f"{_fmt(row.price)} | {_fmt(row.quantity)} | {_fmt(row.amount)} | {_fmt(row.realized_pnl)} | {row.execution_price_type} | "
                f"{row.order_type} | {row.source} | {_fmt(row.simulated_cash)} | {_fmt(row.position_value)} | "
                f"{_fmt(row.total_equity)} | {str(row.reason).replace('|', '/')} |"
            )

    lines += [
        "",
        "## 记录说明",
        "- 如需新增模拟持仓，手动填写 data/paper_positions.csv。",
        "- data/paper_trades.csv 只用于模拟流水备查，不代表任何真实交易。",
        "- 系统只做本地估值和报告，不会自动写入真实交易或下单。",
    ]
    LATEST_PAPER_PORTFOLIO_FILE.write_text("\n".join(lines), encoding="utf-8")


def _numeric_sum(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).sum())


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _read_sell_review_map() -> dict[str, dict]:
    path = REPORT_DIR / "sell_signal_review.csv"
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return {}
    if "symbol" not in df.columns:
        return {}
    return df.set_index(df["symbol"].astype(str)).to_dict(orient="index")


def _read_classification_map() -> dict[str, dict]:
    path = CLASSIFICATION_FILE if CLASSIFICATION_FILE.exists() else LEGACY_CLASSIFICATION_FILE
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return {}
    if "symbol" not in df.columns and "code" in df.columns:
        df["symbol"] = df["code"]
    if "symbol" not in df.columns:
        return {}
    return df.set_index(df["symbol"].astype(str)).to_dict(orient="index")


def _is_blank(value: object) -> bool:
    text = str(value).strip().lower()
    return text in {"", "nan", "none", "nat"}


def _cash_from_trades(trades: pd.DataFrame, fallback: float) -> float:
    if trades.empty:
        return round(float(fallback), 2)
    cash = INITIAL_CASH
    for row in trades.sort_values("date").itertuples():
        action = str(row.action).upper()
        net = _safe_float(getattr(row, "net_cash_change", 0.0))
        if net == 0.0:
            amount = float(row.amount)
            fee = float(row.fee)
            if action == "BUY":
                net = -(amount + fee)
            elif action == "SELL":
                net = amount - fee
        cash += net
    return round(cash, 2)


def _has_same_day_signal_trade(trades: pd.DataFrame, run_date: str, code: str) -> bool:
    if trades.empty:
        return False
    dates = pd.to_datetime(trades["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return bool(
        (
            (dates == run_date)
            & (trades["symbol"].astype(str) == code)
            & (trades["action"].astype(str).str.upper() == "BUY")
            & (trades["source"].astype(str) == "buy_signal_ranking")
        ).any()
    )


def _same_day_signal_trade_rows(trades: pd.DataFrame, run_date: str, code: str) -> list[dict]:
    if trades.empty:
        return []
    dates = pd.to_datetime(trades["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    mask = (
        (dates == run_date)
        & (trades["symbol"].astype(str) == code)
        & (trades["action"].astype(str).str.upper() == "BUY")
        & (trades["source"].astype(str) == "buy_signal_ranking")
    )
    rows = []
    for row in trades[mask].to_dict(orient="records"):
        row["already_recorded"] = True
        rows.append(row)
    return rows


def _position_market_value(positions: pd.DataFrame, code: str, latest_prices: dict[str, float]) -> float:
    if positions.empty:
        return 0.0
    match = positions[positions["symbol"].astype(str) == code]
    if match.empty:
        return 0.0
    quantity = pd.to_numeric(match["quantity"], errors="coerce").fillna(0.0).sum()
    price = float(latest_prices.get(code, 0.0) or 0.0)
    return float(quantity * price)


def _positions_value_at_close(positions: pd.DataFrame, latest_prices: dict[str, float], override_prices: dict[str, float] | None = None) -> float:
    override_prices = override_prices or {}
    total = 0.0
    if positions.empty:
        return total
    for row in positions.itertuples():
        code = str(row.symbol)
        price = float(override_prices.get(code, latest_prices.get(code, row.entry_price) or 0.0))
        total += float(row.quantity or 0.0) * price
    return total


def _paper_quantity(amount: float, price: float) -> int:
    if amount <= 0 or price <= 0:
        return 0
    return int((amount / price) // 100 * 100)


def _upsert_position(
    positions: pd.DataFrame,
    item: dict,
    run_date: str,
    price: float,
    quantity: int,
    amount: float,
    reason: str,
) -> pd.DataFrame:
    code = str(item.get("code", "")).strip()
    if positions.empty or code not in set(positions["symbol"].astype(str)):
        row = {
            "symbol": code,
            "name": item.get("name", code),
            "strategy_source": _strategy_source(item),
            "position_type": "core" if item.get("mid_signal") == "BUY" else "trial",
            "entry_date": run_date,
            "entry_price": round(price, 6),
            "quantity": int(quantity),
            "cost": round(amount, 2),
            "stop_loss": round(price * (1 - ETF_STOP_LOSS), 6),
            "reason": reason,
            "current_price": "",
            "market_value": "",
            "unrealized_pnl": "",
            "unrealized_return": "",
            "unrealized_pnl_pct": "",
            "holding_days": "",
            "risk_alert": "",
        }
        return pd.concat([positions, pd.DataFrame([row])], ignore_index=True)

    df = positions.copy()
    mask = df["symbol"].astype(str) == code
    old_quantity = pd.to_numeric(df.loc[mask, "quantity"], errors="coerce").fillna(0.0).iloc[0]
    old_cost = pd.to_numeric(df.loc[mask, "cost"], errors="coerce").fillna(0.0).iloc[0]
    new_quantity = old_quantity + quantity
    new_cost = old_cost + amount
    avg_price = new_cost / new_quantity if new_quantity else price
    df.loc[mask, "quantity"] = int(new_quantity)
    df.loc[mask, "cost"] = round(new_cost, 2)
    df.loc[mask, "entry_price"] = round(avg_price, 6)
    df.loc[mask, "stop_loss"] = round(avg_price * (1 - ETF_STOP_LOSS), 6)
    old_reason = str(df.loc[mask, "reason"].iloc[0]).strip()
    df.loc[mask, "reason"] = f"{old_reason}；{reason}" if old_reason else reason
    return df


def _strategy_source(item: dict) -> str:
    if item.get("mid_signal") == "BUY" and item.get("short_signal") == "BUY":
        return "resonance"
    if item.get("mid_signal") == "BUY":
        return "mid_trend"
    return "short_swing"


def _paper_trade_reason(item: dict) -> str:
    return (
        f"rank_score={float(item.get('rank_score', 0.0)):.6f}; "
        f"mid_trend={item.get('mid_signal')}; short_swing={item.get('short_signal')}; "
        f"source=buy_signal_ranking"
    )


def _realized_pnl_from_trades(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    realized = 0.0
    inventory: dict[str, dict[str, float]] = {}
    for row in trades.sort_values("date").itertuples():
        symbol = str(row.symbol)
        action = str(row.action).upper()
        price = _safe_float(getattr(row, "execution_price", 0.0)) or float(row.price)
        quantity = float(row.quantity)
        fee = _safe_float(getattr(row, "commission", 0.0)) + _safe_float(getattr(row, "stamp_tax", 0.0)) + _safe_float(getattr(row, "transfer_fee", 0.0))
        if fee <= 0:
            fee = float(row.fee)
        if not symbol or price <= 0 or quantity <= 0:
            continue
        state = inventory.setdefault(symbol, {"quantity": 0.0, "cost": 0.0})
        if action == "BUY":
            state["quantity"] += quantity
            state["cost"] += price * quantity + fee
        elif action == "SELL":
            if state["quantity"] <= 0:
                realized -= fee
                continue
            sell_quantity = min(quantity, state["quantity"])
            avg_cost = state["cost"] / state["quantity"] if state["quantity"] else 0.0
            realized += (price - avg_cost) * sell_quantity - fee
            state["quantity"] -= sell_quantity
            state["cost"] = max(0.0, state["cost"] - avg_cost * sell_quantity)
    return realized


def _fmt(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.6f}".rstrip("0").rstrip(".")


def _pct_fmt(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2%}"


def _latest_prices_from_local(watchlist: pd.DataFrame) -> tuple[str, dict[str, float]]:
    latest_prices: dict[str, float] = {}
    latest_dates: list[pd.Timestamp] = []
    for code in watchlist["code"].astype(str):
        df, _ = load_price_data(DATA_DIR, code)
        if df is None or df.empty:
            continue
        latest = df.sort_values("date").iloc[-1]
        latest_prices[str(code)] = float(latest["close"])
        latest_dates.append(pd.to_datetime(latest["date"]))
    run_date = max(latest_dates).strftime("%Y-%m-%d") if latest_dates else pd.Timestamp.today().strftime("%Y-%m-%d")
    return run_date, latest_prices


def main() -> None:
    watchlist = read_watchlist(WATCHLIST_FILE)
    run_date, latest_prices = _latest_prices_from_local(watchlist)
    path, _ = update_paper_portfolio(run_date, latest_prices, watchlist)
    print(f"已生成模拟盘持仓报告：{path}")
    print("本报告只读取本地模拟盘 CSV，不接券商 API，不下单。")


if __name__ == "__main__":
    main()
