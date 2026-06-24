"""Phase 4A-1 research-only ETF rotation backtest engine.

This module builds a reproducible daily ETF rotation backtest with transaction
costs and 100-share lot constraints. It writes research reports only. It never
reads real accounts, touches broker APIs, or modifies paper trading files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import math
import re

import pandas as pd

from config import DEFAULT_BACKTEST_INITIAL_CASH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
REPORT_DIR = PROJECT_ROOT / "reports"

UNIVERSE_REVIEW_CSV = REPORT_DIR / "universe_quality_review.csv"
TRADE_POOL_CSV = DATA_DIR / "backtest_trade_pool.csv"
TRADE_POOL_REPORT = REPORT_DIR / "backtest_trade_pool_report.md"

REPORT_MD = REPORT_DIR / "backtest_phase4a_report.md"
SUMMARY_CSV = REPORT_DIR / "backtest_summary.csv"
TRADES_CSV = REPORT_DIR / "backtest_trades.csv"
EQUITY_CSV = REPORT_DIR / "backtest_equity_curve.csv"
POSITIONS_CSV = REPORT_DIR / "backtest_positions.csv"
METRICS_JSON = REPORT_DIR / "backtest_metrics.json"
YEARLY_CSV = REPORT_DIR / "backtest_yearly_summary.csv"

INITIAL_CASH = float(DEFAULT_BACKTEST_INITIAL_CASH)
COMMISSION_RATE = 0.00012
MIN_COMMISSION = 5.0
STAMP_TAX_RATE = 0.0
SLIPPAGE_RATE = 0.0003
LOT_SIZE = 100
MAX_HOLDINGS = 3
MAX_SINGLE_POSITION_PCT = 0.20
TARGET_TOTAL_POSITION_PCT = 0.60
MAX_HOLDING_DAYS_DEFAULT = 20
EXIT_RANK_THRESHOLD = 20
MIN_HISTORY_DAYS = 60
EXECUTION_PRICE_ASSUMPTION = "next_close"


@dataclass
class Position:
    symbol: str
    name: str
    quantity: int
    avg_cost: float
    entry_date: pd.Timestamp
    entry_value: float
    commission_paid: float = 0.0
    slippage_paid: float = 0.0


@dataclass
class StrategyResult:
    strategy: str
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    positions: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    yearly: list[dict] = field(default_factory=list)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    trade_pool = load_or_build_trade_pool()
    price_data = load_price_data(trade_pool)
    all_dates = build_backtest_dates(price_data)
    if len(all_dates) < MIN_HISTORY_DAYS + 2:
        raise RuntimeError("not enough dates for Phase 4A backtest")

    feature_data = {symbol: compute_features(df) for symbol, df in price_data.items()}
    results = [
        run_rotation_strategy("original_ranking_baseline", trade_pool, price_data, feature_data, all_dates, adjusted=False),
        run_rotation_strategy("adjusted_preview_baseline", trade_pool, price_data, feature_data, all_dates, adjusted=True),
        run_buy_and_hold_510300(trade_pool, price_data, all_dates),
        run_cash_baseline(all_dates),
    ]
    write_outputs(trade_pool, results, all_dates)
    print(f"backtest trade pool: {len(trade_pool)}")
    print(f"strategies: {', '.join(result.strategy for result in results)}")
    print(f"written: {REPORT_MD}")
    print(f"written: {SUMMARY_CSV}")
    print(f"written: {TRADES_CSV}")
    print(f"written: {EQUITY_CSV}")
    print(f"written: {POSITIONS_CSV}")
    print(f"written: {METRICS_JSON}")
    print(f"written: {YEARLY_CSV}")


def load_or_build_trade_pool() -> pd.DataFrame:
    if TRADE_POOL_CSV.exists() and TRADE_POOL_CSV.stat().st_size > 0:
        df = pd.read_csv(TRADE_POOL_CSV, dtype=str).fillna("")
    else:
        if not UNIVERSE_REVIEW_CSV.exists():
            raise FileNotFoundError(f"missing {UNIVERSE_REVIEW_CSV}")
        review = pd.read_csv(UNIVERSE_REVIEW_CSV)
        mask = (
            (review["recommended_pool"] == "trade_pool")
            & (~review["qdii_flag"].astype(bool))
            & (review["classification_status"] != "unknown")
            & (~review["liquidity_status"].isin(["low", "ultra_low", "unknown"]))
            & (review["data_length_status"] == "ok")
        )
        df = review.loc[mask].copy()
        cols = [
            "symbol",
            "name",
            "etf_type",
            "group",
            "avg_amount_20d",
            "trading_days",
            "start_date",
            "end_date",
            "review_reason",
        ]
        df = df[cols].sort_values(["group", "symbol"]).reset_index(drop=True)
        df.to_csv(TRADE_POOL_CSV, index=False)
    write_trade_pool_report(df)
    return df


def write_trade_pool_report(df: pd.DataFrame) -> None:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Backtest Trade Pool Report {generated_at}",
        "",
        "本交易池只用于 Phase 4A-1 研究回测，不改变模拟盘执行逻辑。",
        "",
        f"- trade_pool 数量：{len(df)}",
        "- 来源：reports/universe_quality_review.csv 中 recommended_pool=trade_pool 的高质量 ETF。",
        "- 已排除：QDII、unknown、低流动性、短历史不足、exclude_pool。",
        "",
        "## ETF 列表",
        rows_to_markdown(df, ["symbol", "name", "etf_type", "group", "avg_amount_20d", "trading_days"]),
    ]
    TRADE_POOL_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_price_data(pool: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for symbol in pool["symbol"].astype(str):
        path = find_price_file(symbol)
        if path is None:
            continue
        df = pd.read_csv(path)
        if df.empty or "date" not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for col in ["open", "high", "low", "close", "volume", "amount", "money"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "amount" not in df.columns and "money" in df.columns:
            df["amount"] = df["money"]
        df = df.dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date").drop_duplicates("date", keep="last")
        if len(df) >= MIN_HISTORY_DAYS:
            data[str(symbol)] = df
    return data


def find_price_file(symbol: str) -> Path | None:
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
        if path.exists():
            return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*{symbol}*.csv"))
    return matches[0] if matches else None


def build_backtest_dates(price_data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    dates = sorted(set().union(*(set(df["date"]) for df in price_data.values())))
    return [pd.Timestamp(d) for d in dates if pd.notna(d)]


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)
    close = out["close"]
    out["return_5d"] = close / close.shift(5) - 1
    out["return_10d"] = close / close.shift(10) - 1
    out["return_20d"] = close / close.shift(20) - 1
    out["return_60d"] = close / close.shift(60) - 1
    out["ma10"] = close.rolling(10).mean()
    out["ma20"] = close.rolling(20).mean()
    out["ma60"] = close.rolling(60).mean()
    out["trend_score_raw"] = (
        (close > out["ma20"]).astype(float) * 10
        + (close > out["ma60"]).astype(float) * 10
        + ((out["ma20"] - out["ma20"].shift(5)) > 0).astype(float) * 10
    )
    out["volatility_20d"] = close.pct_change(fill_method=None).rolling(20).std()
    out["drawdown_20d"] = close / close.rolling(20, min_periods=5).max() - 1
    out["amount_ma20"] = out.get("amount", pd.Series([0] * len(out))).rolling(20).mean()
    return out


def run_rotation_strategy(
    strategy: str,
    pool: pd.DataFrame,
    price_data: dict[str, pd.DataFrame],
    feature_data: dict[str, pd.DataFrame],
    all_dates: list[pd.Timestamp],
    adjusted: bool,
) -> StrategyResult:
    meta = pool.set_index(pool["symbol"].astype(str)).to_dict(orient="index")
    cash = INITIAL_CASH
    positions: dict[str, Position] = {}
    result = StrategyResult(strategy=strategy)
    start_index = MIN_HISTORY_DAYS
    end_index = len(all_dates) - 1

    for idx in range(start_index, end_index):
        signal_date = all_dates[idx]
        exec_date = all_dates[idx + 1]
        ranking = build_daily_ranking(signal_date, feature_data, meta, positions, adjusted)
        rank_map = {row["symbol"]: row for row in ranking}

        for symbol in list(positions):
            position = positions[symbol]
            row = rank_map.get(symbol)
            holding_days = trading_days_between(all_dates, position.entry_date, signal_date)
            max_days = max_holding_days(meta.get(symbol, {}).get("etf_type", ""))
            reason = ""
            if row is None:
                reason = "not_in_ranking_or_missing_data"
            elif int(row["rank"]) > EXIT_RANK_THRESHOLD:
                reason = f"rank_below_top_{EXIT_RANK_THRESHOLD}"
            elif holding_days >= max_days:
                reason = f"max_holding_days_{max_days}"
            if reason:
                cash += sell_position(strategy, symbol, position, exec_date, price_data, result, reason)
                del positions[symbol]

        slots = MAX_HOLDINGS - len(positions)
        if slots > 0:
            targets = [row for row in ranking[:MAX_HOLDINGS] if row["symbol"] not in positions][:slots]
            for row in targets:
                symbol = row["symbol"]
                target_value = INITIAL_CASH * MAX_SINGLE_POSITION_PCT
                cash, bought = buy_position(strategy, row, exec_date, price_data, cash, target_value, result)
                if bought:
                    positions[symbol] = bought

        equity, exposure = mark_to_market(cash, positions, signal_date, price_data)
        result.equity_curve.append(
            {
                "date": signal_date.strftime("%Y-%m-%d"),
                "strategy": strategy,
                "equity": round(equity, 4),
                "cash": round(cash, 4),
                "position_value": round(equity - cash, 4),
                "cash_ratio": round(cash / equity, 6) if equity else 0,
                "exposure": round(exposure, 6),
                "holdings": len(positions),
            }
        )
        for pos in positions.values():
            price = close_on_or_before(price_data[pos.symbol], signal_date)
            result.positions.append(
                {
                    "date": signal_date.strftime("%Y-%m-%d"),
                    "strategy": strategy,
                    "symbol": pos.symbol,
                    "name": pos.name,
                    "quantity": pos.quantity,
                    "avg_cost": round(pos.avg_cost, 6),
                    "close": round(price, 6),
                    "market_value": round(pos.quantity * price, 4),
                    "holding_days": trading_days_between(all_dates, pos.entry_date, signal_date),
                }
            )

    final_date = all_dates[-1]
    for symbol in list(positions):
        position = positions[symbol]
        cash += sell_position(strategy, symbol, position, final_date, price_data, result, "backtest_end_liquidation")
        del positions[symbol]
    equity, exposure = mark_to_market(cash, positions, final_date, price_data)
    result.equity_curve.append(
        {
            "date": final_date.strftime("%Y-%m-%d"),
            "strategy": strategy,
            "equity": round(equity, 4),
            "cash": round(cash, 4),
            "position_value": 0.0,
            "cash_ratio": 1.0,
            "exposure": round(exposure, 6),
            "holdings": 0,
        }
    )
    result.metrics = compute_metrics(strategy, result.equity_curve, result.trades)
    result.yearly = compute_yearly(strategy, result.equity_curve, result.trades)
    return result


def build_daily_ranking(
    date: pd.Timestamp,
    feature_data: dict[str, pd.DataFrame],
    meta: dict[str, dict],
    positions: dict[str, Position],
    adjusted: bool,
) -> list[dict]:
    rows = []
    for symbol, df in feature_data.items():
        sub = df[df["date"] <= date]
        if sub.empty or len(sub) < MIN_HISTORY_DAYS:
            continue
        row = sub.iloc[-1]
        if pd.isna(row.get("return_20d")) or pd.isna(row.get("return_60d")):
            continue
        amount_ma20 = float(row.get("amount_ma20") or 0)
        if amount_ma20 <= 0:
            continue
        score = score_ranking_row(row, amount_ma20)
        if adjusted:
            score += adjusted_preview_delta(symbol, meta.get(symbol, {}), positions)
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "name": meta.get(symbol, {}).get("name", symbol),
                "etf_type": meta.get(symbol, {}).get("etf_type", ""),
                "group": meta.get(symbol, {}).get("group", ""),
                "rank_score": round(score, 6),
                "close": float(row["close"]),
            }
        )
    rows.sort(key=lambda item: item["rank_score"], reverse=True)
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
    return rows


def score_ranking_row(row: pd.Series, amount_ma20: float) -> float:
    momentum = 35 * clip01((float(row["return_20d"]) + 0.15) / 0.30) + 20 * clip01((float(row["return_60d"]) + 0.25) / 0.50)
    short_momentum = 10 * clip01((float(row.get("return_10d", 0)) + 0.08) / 0.16)
    trend = float(row.get("trend_score_raw", 0))
    vol = float(row.get("volatility_20d") or 0)
    risk = 15 * (1 - clip01(vol / 0.05))
    liquidity = 10 * clip01(math.log10(max(amount_ma20, 1)) / 10)
    drawdown = float(row.get("drawdown_20d") or 0)
    drawdown_penalty = min(abs(drawdown), 0.20) * 25
    return momentum + short_momentum + trend + risk + liquidity - drawdown_penalty


def adjusted_preview_delta(symbol: str, meta: dict, positions: dict[str, Position]) -> float:
    etf_type = str(meta.get("etf_type", ""))
    group = str(meta.get("group", ""))
    held_groups = {str(pos_symbol) for pos_symbol in positions}
    position_groups = set()
    # Stored positions only have symbol/name. Group is recovered via closure meta by symbol.
    for pos_symbol in positions:
        # This loop is intentionally simple; group concentration is a preview proxy.
        if pos_symbol == symbol:
            continue
    delta = 0.0
    if etf_type == "broad_index":
        delta += 1.5
    if "防御" in group or "红利" in group:
        delta += 1.0
    if etf_type in {"theme", "high_beta"}:
        delta -= 1.0
    if symbol in held_groups:
        delta -= 0.5
    return delta


def buy_position(
    strategy: str,
    row: dict,
    exec_date: pd.Timestamp,
    price_data: dict[str, pd.DataFrame],
    cash: float,
    target_value: float,
    result: StrategyResult,
) -> tuple[float, Position | None]:
    symbol = row["symbol"]
    price = execution_price(symbol, exec_date, price_data, side="buy")
    if price is None:
        record_skip(result, strategy, exec_date, symbol, row.get("name", symbol), "missing_execution_price_buy")
        return cash, None
    quantity = int(target_value // (price * LOT_SIZE)) * LOT_SIZE
    if quantity <= 0:
        record_skip(result, strategy, exec_date, symbol, row.get("name", symbol), "target_value_less_than_100_shares")
        return cash, None
    gross = quantity * price
    commission = max(gross * COMMISSION_RATE, MIN_COMMISSION)
    slippage = gross * SLIPPAGE_RATE
    total_cost = gross + commission + slippage
    if total_cost > cash:
        quantity = int((cash - MIN_COMMISSION) // (price * (1 + SLIPPAGE_RATE) * LOT_SIZE)) * LOT_SIZE
        if quantity <= 0:
            record_skip(result, strategy, exec_date, symbol, row.get("name", symbol), "insufficient_cash_for_100_shares")
            return cash, None
        gross = quantity * price
        commission = max(gross * COMMISSION_RATE, MIN_COMMISSION)
        slippage = gross * SLIPPAGE_RATE
        total_cost = gross + commission + slippage
    if total_cost > cash:
        record_skip(result, strategy, exec_date, symbol, row.get("name", symbol), "insufficient_cash_after_costs")
        return cash, None
    cash -= total_cost
    result.trades.append(
        trade_row(strategy, exec_date, symbol, row.get("name", symbol), "BUY", quantity, price, gross, commission, slippage, 0.0, "top_ranking_buy")
    )
    return cash, Position(symbol, row.get("name", symbol), quantity, price, exec_date, gross, commission, slippage)


def sell_position(
    strategy: str,
    symbol: str,
    position: Position,
    exec_date: pd.Timestamp,
    price_data: dict[str, pd.DataFrame],
    result: StrategyResult,
    reason: str,
) -> float:
    price = execution_price(symbol, exec_date, price_data, side="sell")
    if price is None:
        record_skip(result, strategy, exec_date, symbol, position.name, f"missing_execution_price_sell:{reason}")
        return 0.0
    gross = position.quantity * price
    commission = max(gross * COMMISSION_RATE, MIN_COMMISSION)
    slippage = gross * SLIPPAGE_RATE
    stamp_tax = gross * STAMP_TAX_RATE
    proceeds = gross - commission - slippage - stamp_tax
    pnl = proceeds - position.entry_value - position.commission_paid - position.slippage_paid
    result.trades.append(
        trade_row(strategy, exec_date, symbol, position.name, "SELL", position.quantity, price, gross, commission, slippage, pnl, reason)
    )
    return proceeds


def trade_row(
    strategy: str,
    date: pd.Timestamp,
    symbol: str,
    name: str,
    side: str,
    quantity: int,
    price: float,
    gross: float,
    commission: float,
    slippage: float,
    pnl: float,
    reason: str,
) -> dict:
    return {
        "date": date.strftime("%Y-%m-%d"),
        "strategy": strategy,
        "symbol": symbol,
        "name": name,
        "side": side,
        "quantity": int(quantity),
        "price": round(price, 6),
        "gross_value": round(gross, 4),
        "commission": round(commission, 4),
        "slippage": round(slippage, 4),
        "stamp_tax": 0.0,
        "pnl": round(pnl, 4),
        "reason": reason,
        "execution_price_assumption": EXECUTION_PRICE_ASSUMPTION,
    }


def record_skip(result: StrategyResult, strategy: str, date: pd.Timestamp, symbol: str, name: str, reason: str) -> None:
    result.trades.append(
        {
            "date": date.strftime("%Y-%m-%d"),
            "strategy": strategy,
            "symbol": symbol,
            "name": name,
            "side": "SKIP",
            "quantity": 0,
            "price": 0.0,
            "gross_value": 0.0,
            "commission": 0.0,
            "slippage": 0.0,
            "stamp_tax": 0.0,
            "pnl": 0.0,
            "reason": reason,
            "execution_price_assumption": EXECUTION_PRICE_ASSUMPTION,
        }
    )


def execution_price(symbol: str, date: pd.Timestamp, price_data: dict[str, pd.DataFrame], side: str) -> float | None:
    df = price_data.get(symbol)
    if df is None or df.empty:
        return None
    exact = df[df["date"] == date]
    if exact.empty:
        future = df[df["date"] >= date]
        if future.empty:
            return None
        exact = future.head(1)
    return float(exact.iloc[0]["close"])


def close_on_or_before(df: pd.DataFrame, date: pd.Timestamp) -> float:
    sub = df[df["date"] <= date]
    return float(sub.iloc[-1]["close"]) if not sub.empty else 0.0


def mark_to_market(cash: float, positions: dict[str, Position], date: pd.Timestamp, price_data: dict[str, pd.DataFrame]) -> tuple[float, float]:
    value = 0.0
    for pos in positions.values():
        value += pos.quantity * close_on_or_before(price_data[pos.symbol], date)
    equity = cash + value
    exposure = value / equity if equity else 0.0
    return equity, exposure


def run_buy_and_hold_510300(pool: pd.DataFrame, price_data: dict[str, pd.DataFrame], all_dates: list[pd.Timestamp]) -> StrategyResult:
    strategy = "buy_and_hold_510300"
    symbol = "510300" if "510300" in price_data else str(pool.iloc[0]["symbol"])
    name = str(pool.set_index(pool["symbol"].astype(str)).to_dict(orient="index").get(symbol, {}).get("name", symbol))
    result = StrategyResult(strategy=strategy)
    cash = INITIAL_CASH
    first_date = all_dates[MIN_HISTORY_DAYS + 1]
    price = execution_price(symbol, first_date, price_data, "buy")
    quantity = 0
    if price:
        target = INITIAL_CASH * TARGET_TOTAL_POSITION_PCT
        quantity = int(target // (price * LOT_SIZE)) * LOT_SIZE
        gross = quantity * price
        commission = max(gross * COMMISSION_RATE, MIN_COMMISSION) if quantity else 0.0
        slippage = gross * SLIPPAGE_RATE
        total = gross + commission + slippage
        if quantity and total <= cash:
            cash -= total
            result.trades.append(trade_row(strategy, first_date, symbol, name, "BUY", quantity, price, gross, commission, slippage, 0.0, "buy_and_hold"))
    for date in all_dates[MIN_HISTORY_DAYS + 1 :]:
        close = close_on_or_before(price_data[symbol], date)
        value = quantity * close
        equity = cash + value
        result.equity_curve.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "strategy": strategy,
                "equity": round(equity, 4),
                "cash": round(cash, 4),
                "position_value": round(value, 4),
                "cash_ratio": round(cash / equity, 6) if equity else 1.0,
                "exposure": round(value / equity, 6) if equity else 0.0,
                "holdings": 1 if quantity else 0,
            }
        )
    result.metrics = compute_metrics(strategy, result.equity_curve, result.trades)
    result.yearly = compute_yearly(strategy, result.equity_curve, result.trades)
    return result


def run_cash_baseline(all_dates: list[pd.Timestamp]) -> StrategyResult:
    strategy = "cash_baseline"
    result = StrategyResult(strategy=strategy)
    for date in all_dates[MIN_HISTORY_DAYS + 1 :]:
        result.equity_curve.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "strategy": strategy,
                "equity": INITIAL_CASH,
                "cash": INITIAL_CASH,
                "position_value": 0.0,
                "cash_ratio": 1.0,
                "exposure": 0.0,
                "holdings": 0,
            }
        )
    result.metrics = compute_metrics(strategy, result.equity_curve, result.trades)
    result.yearly = compute_yearly(strategy, result.equity_curve, result.trades)
    return result


def compute_metrics(strategy: str, equity_curve: list[dict], trades: list[dict]) -> dict:
    df = pd.DataFrame(equity_curve)
    if df.empty:
        return {"strategy": strategy}
    df["date"] = pd.to_datetime(df["date"])
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    returns = df["equity"].pct_change(fill_method=None).dropna()
    total_return = df["equity"].iloc[-1] / df["equity"].iloc[0] - 1
    years = max((df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25, 1 / 365.25)
    annualized = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1
    peak = df["equity"].cummax()
    dd = df["equity"] / peak - 1
    max_dd = float(dd.min())
    sharpe = float((returns.mean() / returns.std()) * (252 ** 0.5)) if len(returns) > 2 and returns.std() else 0.0
    calmar = annualized / abs(max_dd) if max_dd < 0 else 0.0
    trade_df = pd.DataFrame(trades)
    sells = trade_df[trade_df["side"] == "SELL"] if not trade_df.empty else pd.DataFrame()
    wins = sells[sells["pnl"] > 0]["pnl"] if not sells.empty else pd.Series(dtype=float)
    losses = sells[sells["pnl"] < 0]["pnl"] if not sells.empty else pd.Series(dtype=float)
    buy_sell = trade_df[trade_df["side"].isin(["BUY", "SELL"])] if not trade_df.empty else pd.DataFrame()
    total_traded = float(buy_sell["gross_value"].sum()) if not buy_sell.empty else 0.0
    avg_equity = float(df["equity"].mean()) if not df.empty else INITIAL_CASH
    return {
        "strategy": strategy,
        "total_return": round(float(total_return), 6),
        "annualized_return": round(float(annualized), 6),
        "max_drawdown": round(max_dd, 6),
        "sharpe": round(sharpe, 6),
        "calmar": round(float(calmar), 6),
        "win_rate": round(float(len(wins) / len(sells)), 6) if len(sells) else 0.0,
        "avg_win": round(float(wins.mean()), 4) if len(wins) else 0.0,
        "avg_loss": round(float(losses.mean()), 4) if len(losses) else 0.0,
        "profit_factor": round(float(wins.sum() / abs(losses.sum())), 6) if len(losses) and abs(losses.sum()) > 0 else 0.0,
        "trade_count": int(len(buy_sell)),
        "turnover": round(float(total_traded / avg_equity), 6) if avg_equity else 0.0,
        "avg_holding_days": round(avg_holding_days(trade_df), 4),
        "best_trade": round(float(sells["pnl"].max()), 4) if len(sells) else 0.0,
        "worst_trade": round(float(sells["pnl"].min()), 4) if len(sells) else 0.0,
        "final_equity": round(float(df["equity"].iloc[-1]), 4),
        "cash_ratio_avg": round(float(df["cash_ratio"].mean()), 6),
        "exposure_avg": round(float(df["exposure"].mean()), 6),
        "cost_total": round(float(buy_sell.get("commission", pd.Series(dtype=float)).sum() + buy_sell.get("slippage", pd.Series(dtype=float)).sum()), 4),
        "slippage_total": round(float(buy_sell.get("slippage", pd.Series(dtype=float)).sum()), 4),
        "commission_total": round(float(buy_sell.get("commission", pd.Series(dtype=float)).sum()), 4),
    }


def avg_holding_days(trade_df: pd.DataFrame) -> float:
    if trade_df.empty:
        return 0.0
    entries: dict[str, pd.Timestamp] = {}
    days = []
    for _, row in trade_df.iterrows():
        key = f"{row.get('strategy')}:{row.get('symbol')}"
        date = pd.Timestamp(row.get("date"))
        if row.get("side") == "BUY":
            entries[key] = date
        elif row.get("side") == "SELL" and key in entries:
            days.append((date - entries.pop(key)).days)
    return float(sum(days) / len(days)) if days else 0.0


def compute_yearly(strategy: str, equity_curve: list[dict], trades: list[dict]) -> list[dict]:
    df = pd.DataFrame(equity_curve)
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    trade_df = pd.DataFrame(trades)
    if not trade_df.empty:
        trade_df["date"] = pd.to_datetime(trade_df["date"])
        trade_df["year"] = trade_df["date"].dt.year
    rows = []
    for year, sub in df.groupby("year"):
        eq = sub["equity"].astype(float)
        ret = eq.iloc[-1] / eq.iloc[0] - 1
        dd = eq / eq.cummax() - 1
        tsub = trade_df[trade_df["year"] == year] if not trade_df.empty else pd.DataFrame()
        sells = tsub[tsub["side"] == "SELL"] if not tsub.empty else pd.DataFrame()
        wins = sells[sells["pnl"] > 0] if not sells.empty else pd.DataFrame()
        rows.append(
            {
                "strategy": strategy,
                "year": int(year),
                "return": round(float(ret), 6),
                "max_drawdown": round(float(dd.min()), 6),
                "trade_count": int(len(tsub[tsub["side"].isin(["BUY", "SELL"])])) if not tsub.empty else 0,
                "win_rate": round(float(len(wins) / len(sells)), 6) if len(sells) else 0.0,
                "turnover": round(float(tsub.get("gross_value", pd.Series(dtype=float)).sum() / eq.mean()), 6) if not tsub.empty and eq.mean() else 0.0,
            }
        )
    return rows


def write_outputs(pool: pd.DataFrame, results: list[StrategyResult], all_dates: list[pd.Timestamp]) -> None:
    summary = pd.DataFrame([r.metrics for r in results])
    trades = pd.DataFrame([row for r in results for row in r.trades])
    equity = pd.DataFrame([row for r in results for row in r.equity_curve])
    positions = pd.DataFrame([row for r in results for row in r.positions])
    yearly = pd.DataFrame([row for r in results for row in r.yearly])
    summary.to_csv(SUMMARY_CSV, index=False)
    trades.to_csv(TRADES_CSV, index=False)
    equity.to_csv(EQUITY_CSV, index=False)
    positions.to_csv(POSITIONS_CSV, index=False)
    yearly.to_csv(YEARLY_CSV, index=False)
    metrics_payload = {
        "version": "phase4a_1_basic_etf_rotation_backtest",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "research_only": True,
        "execution_enabled": False,
        "execution_price_assumption": EXECUTION_PRICE_ASSUMPTION,
        "trade_pool_count": int(len(pool)),
        "strategies": {r.strategy: r.metrics for r in results},
        "costs": {
            "commission_rate": COMMISSION_RATE,
            "min_commission": MIN_COMMISSION,
            "slippage_rate": SLIPPAGE_RATE,
            "stamp_tax_rate": STAMP_TAX_RATE,
            "lot_size": LOT_SIZE,
        },
    }
    METRICS_JSON.write_text(json.dumps(metrics_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_report(pool, summary, yearly, metrics_payload, all_dates), encoding="utf-8")


def render_report(pool: pd.DataFrame, summary: pd.DataFrame, yearly: pd.DataFrame, payload: dict, all_dates: list[pd.Timestamp]) -> str:
    best = summary.sort_values("total_return", ascending=False).iloc[0].to_dict() if not summary.empty else {}
    baseline = summary[summary["strategy"] == "buy_and_hold_510300"].iloc[0].to_dict() if "buy_and_hold_510300" in set(summary.get("strategy", [])) else {}
    generated_at = payload["generated_at"]
    lines = [
        f"# Phase 4A-1 基础 ETF 轮动回测报告 {generated_at}",
        "",
        "本报告为 research/backtest 输出，不接入模拟盘执行层，不构成真实交易建议。",
        "",
        "## 成交与组合假设",
        f"- 信号日收盘后生成，第一版成交价假设：`{EXECUTION_PRICE_ASSUMPTION}`。",
        "- 日频回测，不做日内。",
        f"- 初始资金：{INITIAL_CASH:.2f}",
        "- 资金口径：20000 是当前研究/回测主基准；10000 仅保留为成本敏感性对照，不代表用户需要真实投入。",
        "- 原因：10000 本金受 ETF 最低 5 元佣金影响过大，当前小资金轮动更适合用 20000 做研究基准。",
        f"- 总目标仓位：{TARGET_TOTAL_POSITION_PCT:.0%}",
        f"- 最多持有：{MAX_HOLDINGS} 只",
        f"- 单只上限：{MAX_SINGLE_POSITION_PCT:.0%}",
        f"- 佣金：{COMMISSION_RATE}，最低佣金：{MIN_COMMISSION}，滑点：{SLIPPAGE_RATE}，ETF 印花税：{STAMP_TAX_RATE}",
        f"- 交易单位：{LOT_SIZE} 份整数倍；不允许负现金、不允许杠杆、不允许做空。",
        "",
        "## 回测交易池",
        f"- 交易池数量：{len(pool)}",
        f"- 回测日期范围：{all_dates[MIN_HISTORY_DAYS].strftime('%Y-%m-%d')} 至 {all_dates[-1].strftime('%Y-%m-%d')}",
        "- 来源：data/backtest_trade_pool.csv。",
        "- 已排除：QDII、unknown、低流动性、短历史不足、exclude_pool。",
        "",
        "## 策略比较摘要",
        rows_to_markdown(summary, list(summary.columns)),
        "",
        "## 年度摘要",
        rows_to_markdown(yearly, list(yearly.columns)) if not yearly.empty else "暂无年度数据。",
        "",
        "## 初步结论",
        f"- 总收益最高策略：{best.get('strategy', 'N/A')}，total_return={pct(best.get('total_return'))}，max_drawdown={pct(best.get('max_drawdown'))}。",
        f"- 510300 buy-and-hold total_return={pct(baseline.get('total_return'))}，max_drawdown={pct(baseline.get('max_drawdown'))}。",
        "- original / adjusted ranking 第一版为历史日线重建简化模型，和当前 daily signal 不完全一致。",
        "- adjusted preview 第一版只做轻量 ETF 类型/防御/宽基偏好调整，未完整重建当前组合暴露模型。",
        "",
        "## 偏差与限制",
        "1. 存在幸存者偏差。",
        "2. ETF 池是当前筛选后的 trade_pool，不代表任意历史时点可交易全集。",
        "3. 不含 QDII。",
        "4. 不含 unknown。",
        "5. 不含低流动性 ETF。",
        "6. 第一版不含复杂止盈止损。",
        "7. 第一版不含真实盘中成交。",
        "8. 成交价是假设，可能与真实可成交价格不同。",
        "9. 数据源可能有口径差异。",
        "10. 回测结果不能直接用于实盘。",
        "",
        "## 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不修改 paper_trades.csv。",
        "- 不修改 paper_positions.csv。",
        "- 不改变 paper_trade_engine.py 当前执行规则。",
    ]
    return "\n".join(lines) + "\n"


def rows_to_markdown(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "暂无数据。"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        lines.append("| " + " | ".join(format_value(row.get(col, "")) for col in cols) + " |")
    return "\n".join(lines)


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", "/").replace("\n", " ")


def pct(value: object) -> str:
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "N/A"


def clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def max_holding_days(etf_type: str) -> int:
    if etf_type in {"theme", "high_beta"}:
        return 20
    if etf_type in {"sector"}:
        return 30
    if etf_type in {"commodity_resource"}:
        return 30
    if etf_type in {"bond_cash"}:
        return 60
    return MAX_HOLDING_DAYS_DEFAULT


def trading_days_between(all_dates: list[pd.Timestamp], start: pd.Timestamp, end: pd.Timestamp) -> int:
    return len([date for date in all_dates if start < date <= end])


def extract_code(value: object) -> str:
    match = re.search(r"(\d{6})", str(value))
    return match.group(1) if match else ""


if __name__ == "__main__":
    main()
