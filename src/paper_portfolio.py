"""模拟盘持仓记录和估值报告。

本模块只读取/更新本地模拟盘 CSV，不连接券商 API，不下单，
不读取账号密码，也不会自动生成任何真实交易。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import INITIAL_CASH, LATEST_PAPER_PORTFOLIO_FILE, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE


POSITION_RECORD_COLUMNS = [
    "symbol",
    "name",
    "strategy_source",
    "position_type",
    "entry_date",
    "entry_price",
    "quantity",
    "cost",
    "stop_loss",
    "reason",
]
POSITION_CALC_COLUMNS = [
    "current_price",
    "market_value",
    "unrealized_pnl",
    "unrealized_return",
    "holding_days",
    "risk_alert",
]
POSITION_COLUMNS = POSITION_RECORD_COLUMNS + POSITION_CALC_COLUMNS
TRADE_COLUMNS = [
    "date",
    "symbol",
    "name",
    "action",
    "strategy_source",
    "position_type",
    "price",
    "quantity",
    "amount",
    "fee",
    "reason",
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
    enriched = _enrich_positions(positions, run_date, latest_prices, watchlist)
    enriched.to_csv(PAPER_POSITIONS_FILE, index=False)
    summary = _portfolio_summary(enriched)
    _write_report(run_date, enriched, summary)
    return LATEST_PAPER_PORTFOLIO_FILE, summary


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
    df = pd.read_csv(PAPER_POSITIONS_FILE, dtype={"symbol": str})
    for col in POSITION_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[POSITION_COLUMNS].copy()


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
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["name"] = df.apply(lambda row: row["name"] if str(row["name"]).strip() else meta_map.get(str(row["symbol"]), {}).get("name", row["symbol"]), axis=1)
    df["strategy_source"] = df["strategy_source"].fillna("").astype(str).str.strip()
    df.loc[~df["strategy_source"].isin(["mid_trend", "short_swing", "resonance"]), "strategy_source"] = "mid_trend"
    df["position_type"] = df["position_type"].fillna("").astype(str).str.strip()
    df.loc[~df["position_type"].isin(["core", "trial"]), "position_type"] = "core"
    df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["entry_price", "quantity", "cost", "stop_loss"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["cost"] = df["cost"].fillna(df["entry_price"] * df["quantity"]).fillna(0.0)
    df["current_price"] = df["symbol"].map(latest_prices).fillna(df["entry_price"]).fillna(0.0)
    df["market_value"] = df["current_price"] * df["quantity"].fillna(0.0)
    df["unrealized_pnl"] = df["market_value"] - df["cost"]
    df["unrealized_return"] = df["unrealized_pnl"] / df["cost"].where(df["cost"] != 0)
    run_ts = pd.to_datetime(run_date)
    entry_ts = pd.to_datetime(df["entry_date"], errors="coerce")
    df["holding_days"] = (run_ts - entry_ts).dt.days
    df["risk_alert"] = df.apply(_position_risk_alert, axis=1)
    for col in ["entry_price", "quantity", "cost", "stop_loss", "current_price", "market_value", "unrealized_pnl", "unrealized_return", "holding_days"]:
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


def _portfolio_summary(positions: pd.DataFrame) -> dict:
    market_value = _numeric_sum(positions, "market_value")
    cost = _numeric_sum(positions, "cost")
    cash = INITIAL_CASH - cost
    total_assets = cash + market_value
    risk_count = int((positions.get("risk_alert", pd.Series(dtype=str)).fillna("").astype(str).str.len() > 0).sum()) if not positions.empty else 0
    return {
        "initial_cash": INITIAL_CASH,
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "total_assets": round(total_assets, 2),
        "position_count": int(len(positions)),
        "unrealized_pnl": round(market_value - cost, 2),
        "risk_alert_count": risk_count,
        "has_risk_alert": risk_count > 0 or cash < 0,
    }


def _write_report(run_date: str, positions: pd.DataFrame, summary: dict) -> None:
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
        f"- 风险提醒数量：{summary['risk_alert_count']}",
        "",
        "## 当前持仓",
    ]
    if positions.empty:
        lines.append("- 当前无模拟持仓。")
    else:
        lines.append("| symbol | name | strategy_source | position_type | entry_date | entry_price | quantity | cost | current_price | market_value | unrealized_pnl | unrealized_return | holding_days | stop_loss | risk_alert |")
        lines.append("| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in positions.itertuples():
            lines.append(
                f"| {row.symbol} | {row.name} | {row.strategy_source} | {row.position_type} | {row.entry_date} | "
                f"{_fmt(row.entry_price)} | {_fmt(row.quantity)} | {_fmt(row.cost)} | {_fmt(row.current_price)} | "
                f"{_fmt(row.market_value)} | {_fmt(row.unrealized_pnl)} | {_fmt(row.unrealized_return)} | "
                f"{_fmt(row.holding_days)} | {_fmt(row.stop_loss)} | {str(row.risk_alert).replace('|', '/')} |"
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


def _fmt(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.6f}".rstrip("0").rstrip(".")
