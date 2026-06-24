"""Backfill paper portfolio equity curve from simulated trades and local closes.

This script creates derived files only. It never modifies paper_trades.csv,
paper_positions.csv, or the paper trade engine, and it never connects to a
broker or real account.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, PAPER_INITIAL_CASH, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR


BACKFILLED_CSV = DATA_DIR / "paper_equity_curve_backfilled.csv"
ORIGINAL_CURVE = DATA_DIR / "paper_equity_curve.csv"
SUMMARY_JSON = REPORT_DIR / "paper_performance_summary.json"
BACKFILLED_MD = REPORT_DIR / "paper_equity_curve_backfilled.md"
AUDIT_MD = REPORT_DIR / "paper_equity_curve_backfill_audit.md"
GAP_EXPLANATION_MD = REPORT_DIR / "paper_equity_curve_gap_explanation.md"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    trades = _read_trades()
    positions = _read_positions()
    original = _read_csv(ORIGINAL_CURVE)
    initial_cash, initial_cash_source = _infer_initial_cash(trades)
    daily = _backfill_equity_curve(trades, positions, initial_cash)

    daily.to_csv(BACKFILLED_CSV, index=False)
    _write_gap_explanation()
    _write_report(daily, original, initial_cash, initial_cash_source)
    _write_audit(daily, original, trades, positions, initial_cash, initial_cash_source)

    print(f"已生成回填权益曲线：{BACKFILLED_CSV}")
    print(f"已生成回填说明报告：{BACKFILLED_MD}")
    print(f"已生成回填审计报告：{AUDIT_MD}")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"symbol": str}, keep_default_na=False).fillna("")
    except Exception:
        return pd.DataFrame()


def _read_trades() -> pd.DataFrame:
    df = _read_csv(PAPER_TRADES_FILE)
    if df.empty:
        return df
    if "date" not in df.columns and "trade_date" in df.columns:
        df["date"] = df["trade_date"]
    if "trade_date" not in df.columns:
        df["trade_date"] = df.get("date", "")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
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
        "total_equity_after_trade",
        "total_equity",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["execution_price"] = df["execution_price"].where(df["execution_price"] > 0, df["price"])
    df["gross_amount"] = df["gross_amount"].where(df["gross_amount"] > 0, df["amount"])
    df["fee"] = df["fee"].where(df["fee"] > 0, df["commission"] + df["stamp_tax"] + df["transfer_fee"])
    missing_net = df["net_cash_change"].eq(0) & df["gross_amount"].gt(0)
    buy_mask = missing_net & df["action"].isin(["BUY", "PAPER_BUY"])
    sell_mask = missing_net & df["action"].isin(["SELL", "PAPER_SELL"])
    df.loc[buy_mask, "net_cash_change"] = -(df.loc[buy_mask, "gross_amount"] + df.loc[buy_mask, "fee"])
    df.loc[sell_mask, "net_cash_change"] = df.loc[sell_mask, "gross_amount"] - df.loc[sell_mask, "fee"]
    return df.sort_values(["date", "symbol", "action"]).copy()


def _read_positions() -> pd.DataFrame:
    return _read_csv(PAPER_POSITIONS_FILE)


def _infer_initial_cash(trades: pd.DataFrame) -> tuple[float, str]:
    summary = _read_json(SUMMARY_JSON)
    value = _to_float(summary.get("initial_cash"))
    if value > 0:
        return round(value, 2), "reports/paper_performance_summary.json.initial_cash"
    if not trades.empty:
        for col in ["total_equity_after_trade", "total_equity"]:
            values = pd.to_numeric(trades.get(col, pd.Series(dtype=float)), errors="coerce")
            positive = values[values > 0]
            if not positive.empty:
                return round(float(positive.iloc[0]), 2), f"paper_trades.csv.{col}"
    return float(PAPER_INITIAL_CASH), "config.PAPER_INITIAL_CASH"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _backfill_equity_curve(trades: pd.DataFrame, positions: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    columns = [
        "date",
        "cash",
        "position_value",
        "total_equity",
        "daily_pnl",
        "daily_return",
        "cumulative_pnl",
        "cumulative_return",
        "drawdown",
        "source",
        "quality_flag",
        "note",
    ]
    if trades.empty:
        return pd.DataFrame(columns=columns)

    symbols = sorted({str(item).strip() for item in trades["symbol"].dropna().astype(str) if str(item).strip()})
    price_map = {symbol: _load_symbol_prices(symbol) for symbol in symbols}
    all_price_dates = sorted(set().union(*[set(df["date"]) for df in price_map.values() if not df.empty]))
    first_trade_date = pd.Timestamp(trades["date"].min()).normalize()
    latest_position_symbols = _open_position_symbols(positions)
    latest_dates: list[pd.Timestamp] = [pd.Timestamp(trades["date"].max()).normalize()]
    for symbol in latest_position_symbols or symbols:
        price_df = price_map.get(symbol)
        if price_df is not None and not price_df.empty:
            latest_dates.append(pd.Timestamp(price_df["date"].max()).normalize())
    end_date = max(latest_dates)

    previous_prices = [day for day in all_price_dates if pd.Timestamp(day) < first_trade_date]
    start_date = pd.Timestamp(previous_prices[-1]).normalize() if previous_prices else first_trade_date
    calendar_dates = list(pd.date_range(start_date, end_date, freq="D"))

    trades_by_date = {key: frame for key, frame in trades.groupby(trades["date"].dt.normalize())}
    cash = float(initial_cash)
    holdings: dict[str, int] = {}
    prev_equity: float | None = None
    max_equity = float(initial_cash)
    rows: list[dict[str, Any]] = []

    for day in calendar_dates:
        trade_notes: list[str] = []
        for row in trades_by_date.get(pd.Timestamp(day), pd.DataFrame()).to_dict(orient="records"):
            symbol = str(row.get("symbol", "")).strip()
            action = str(row.get("action", "")).upper()
            qty = int(_to_float(row.get("quantity")))
            cash += _to_float(row.get("net_cash_change"))
            if action in {"BUY", "PAPER_BUY"}:
                holdings[symbol] = holdings.get(symbol, 0) + qty
            elif action in {"SELL", "PAPER_SELL"}:
                holdings[symbol] = max(0, holdings.get(symbol, 0) - qty)
            trade_notes.append(f"{action}:{symbol}:{qty}")

        position_value = 0.0
        missing_prices: list[str] = []
        carried_prices: list[str] = []
        for symbol, qty in holdings.items():
            if qty <= 0:
                continue
            price, price_date = _price_on_or_before(price_map.get(symbol, pd.DataFrame()), day)
            if price is None:
                missing_prices.append(symbol)
                continue
            if price_date is not None and pd.Timestamp(price_date).normalize() != pd.Timestamp(day).normalize():
                carried_prices.append(symbol)
            position_value += qty * price

        total_equity = cash + position_value
        max_equity = max(max_equity, total_equity)
        daily_pnl = 0.0 if prev_equity is None else total_equity - prev_equity
        daily_return = 0.0 if prev_equity in (None, 0) else daily_pnl / prev_equity
        cumulative_pnl = total_equity - initial_cash
        cumulative_return = cumulative_pnl / initial_cash if initial_cash else 0.0
        drawdown = total_equity / max_equity - 1 if max_equity else 0.0
        if missing_prices:
            quality_flag = "missing_price_estimated"
        elif carried_prices:
            quality_flag = "estimated_carry_forward"
        else:
            quality_flag = "estimated_good"
        note_parts = ["backfilled_from_paper_trades_and_local_close"]
        if trade_notes:
            note_parts.append("trades=" + ";".join(trade_notes))
        if carried_prices:
            note_parts.append("carry_forward_price=" + ",".join(sorted(set(carried_prices))))
        if missing_prices:
            note_parts.append("missing_price=" + ",".join(sorted(set(missing_prices))))
        rows.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "cash": round(cash, 2),
                "position_value": round(position_value, 2),
                "total_equity": round(total_equity, 2),
                "daily_pnl": round(daily_pnl, 2),
                "daily_return": daily_return,
                "cumulative_pnl": round(cumulative_pnl, 2),
                "cumulative_return": cumulative_return,
                "drawdown": drawdown,
                "source": "backfilled_from_trades_and_close",
                "quality_flag": quality_flag,
                "note": " | ".join(note_parts),
            }
        )
        prev_equity = total_equity
    return pd.DataFrame(rows, columns=columns)


def _open_position_symbols(positions: pd.DataFrame) -> list[str]:
    if positions.empty or "symbol" not in positions.columns:
        return []
    if "quantity" in positions.columns:
        qty = pd.to_numeric(positions["quantity"], errors="coerce").fillna(0.0)
        positions = positions[qty > 0]
    return sorted({str(item).strip() for item in positions["symbol"].astype(str) if str(item).strip()})


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


def _price_on_or_before(df: pd.DataFrame, day: pd.Timestamp) -> tuple[float | None, pd.Timestamp | None]:
    if df.empty:
        return None, None
    subset = df[df["date"] <= pd.Timestamp(day).normalize()]
    if subset.empty:
        return None, None
    row = subset.iloc[-1]
    return float(row["close"]), pd.Timestamp(row["date"]).normalize()


def _write_gap_explanation() -> None:
    lines = [
        "# 模拟仓历史盈亏曲线记录较少的原因",
        "",
        "本报告解释为什么模拟交易已经运行一段时间，但早期历史盈亏曲线记录仍然较少。",
        "",
        "## 原因",
        "",
        "1. 模拟交易早期主要记录的是交易流水和当前持仓。",
        "2. 当时没有在每个交易日收盘后持续保存完整账户快照。",
        "3. 历史盈亏曲线需要每日现金、持仓市值和总资产数据。",
        "4. `data/paper_equity_curve.csv` 是绩效模块上线后才开始稳定沉淀的派生文件。",
        "5. 因此它的记录数会少于用户直觉里的“模拟系统运行天数”。",
        "",
        "## 本轮处理",
        "",
        "本轮新增 `data/paper_equity_curve_backfilled.csv`，用模拟交易流水和本地 ETF 历史收盘价估算回填每日权益。",
        "",
        "## 口径说明",
        "",
        "- 回填结果是派生估算，不是真实当日保存的账户快照。",
        "- 非交易日或缺少当日价格时，会沿用最近可用收盘价，并在 `quality_flag` / `note` 中标记。",
        "- 后续 daily_close 应继续运行 `src/paper_performance.py`，让未来权益曲线持续沉淀。",
        "- 本项目仍然只做模拟盘学习，不接券商 API，不真实下单。",
    ]
    GAP_EXPLANATION_MD.write_text("\n".join(lines), encoding="utf-8")


def _write_report(daily: pd.DataFrame, original: pd.DataFrame, initial_cash: float, initial_cash_source: str) -> None:
    quality_counts = daily["quality_flag"].value_counts().to_dict() if not daily.empty and "quality_flag" in daily.columns else {}
    lines = [
        "# 模拟仓历史权益曲线回填报告",
        "",
        "本报告只使用本地模拟交易流水和 ETF 日线 close 生成派生曲线，不接券商 API，不真实下单。",
        "",
        "## 摘要",
        "",
        f"- 初始本金：{initial_cash:,.2f} 元",
        f"- 初始本金来源：`{initial_cash_source}`",
        f"- 原始权益曲线记录数：{len(original)}",
        f"- 回填权益曲线记录数：{len(daily)}",
        f"- 回填起始日期：{daily['date'].iloc[0] if not daily.empty else ''}",
        f"- 回填结束日期：{daily['date'].iloc[-1] if not daily.empty else ''}",
        f"- 质量标记分布：{quality_counts}",
        "",
        "## 重要说明",
        "",
        "- 当前正式模拟仓初始本金仍按 10,000 元口径处理。",
        "- 研究/回测默认 20,000 元不适用于本次正式模拟仓权益回填。",
        "- 回填曲线由交易流水和历史收盘价重建，属于估算数据。",
        "- 非交易日或缺价日使用最近可用 close 估值，并标记 `estimated_carry_forward`。",
        "- 本文件不会覆盖 `data/paper_equity_curve.csv`。",
        "",
        "## 最近记录",
        "",
    ]
    if daily.empty:
        lines.append("- 暂无可回填数据。")
    else:
        lines.append("| 日期 | 现金 | 持仓市值 | 总资产 | 日盈亏 | 累计收益 | 回撤 | 质量 |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in daily.tail(12).to_dict(orient="records"):
            lines.append(
                f"| {row['date']} | {_fmt_money(row['cash'])} | {_fmt_money(row['position_value'])} | "
                f"{_fmt_money(row['total_equity'])} | {_fmt_money(row['daily_pnl'])} | "
                f"{_fmt_pct(row['cumulative_return'])} | {_fmt_pct(row['drawdown'])} | {row['quality_flag']} |"
            )
    BACKFILLED_MD.write_text("\n".join(lines), encoding="utf-8")


def _write_audit(
    daily: pd.DataFrame,
    original: pd.DataFrame,
    trades: pd.DataFrame,
    positions: pd.DataFrame,
    initial_cash: float,
    initial_cash_source: str,
) -> None:
    lines = [
        "# 模拟仓权益曲线回填审计",
        "",
        "## 输入文件",
        "",
        f"- 交易流水：`{PAPER_TRADES_FILE.relative_to(PAPER_TRADES_FILE.parents[1])}`，读取 {len(trades)} 条",
        f"- 当前持仓：`{PAPER_POSITIONS_FILE.relative_to(PAPER_POSITIONS_FILE.parents[1])}`，读取 {len(positions)} 条",
        f"- 原始权益曲线：`{ORIGINAL_CURVE.relative_to(ORIGINAL_CURVE.parents[1])}`，读取 {len(original)} 条",
        f"- ETF 日线目录：`{ETF_DAILY_DIR}`",
        "",
        "## 字段映射",
        "",
        "- 日期：优先 `date`，缺失时使用 `trade_date`。",
        "- 交易方向：`BUY` / `SELL`，兼容 `PAPER_BUY` / `PAPER_SELL`。",
        "- 成交价：优先 `execution_price`，缺失时使用 `price`。",
        "- 现金变化：优先 `net_cash_change`，缺失时用成交额和费用估算。",
        "- 费用：优先 `fee`，否则使用 `commission + stamp_tax + transfer_fee`。",
        "",
        "## 回填规则",
        "",
        f"- 初始本金：{initial_cash:,.2f} 元，来源 `{initial_cash_source}`。",
        "- 从首笔交易前一个可用交易日开始回放；如果没有前一交易日，则从首笔交易日开始。",
        "- 逐日应用交易流水，更新现金和持仓数量。",
        "- 每日按 ETF 本地 close 估值。",
        "- 非交易日或缺当日 close 时使用最近可用 close，并标记为 `estimated_carry_forward`。",
        "- 如果完全找不到价格，标记为 `missing_price_estimated`。",
        "",
        "## 安全边界",
        "",
        "- 未修改 `data/paper_trades.csv`。",
        "- 未修改 `data/paper_positions.csv`。",
        "- 未修改 `src/paper_trade_engine.py`。",
        "- 未接券商 API。",
        "- 未真实下单。",
        "- 未读取真实账户。",
    ]
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def _to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        numeric = float(value)
    except Exception:
        return 0.0
    return 0.0 if pd.isna(numeric) else numeric


def _fmt_money(value: Any) -> str:
    return f"{_to_float(value):,.2f}"


def _fmt_pct(value: Any) -> str:
    try:
        numeric = float(value)
    except Exception:
        return "暂无"
    if pd.isna(numeric):
        return "暂无"
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
