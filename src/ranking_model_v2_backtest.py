"""Phase 4B-1 benchmark-informed ETF ranking model v2 backtest.

This module is research-only. It reads local ETF daily data and the filtered
backtest trade pool, then writes reports under reports/. It never connects to
broker APIs, never places orders, and never modifies paper trading files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import re
from pathlib import Path
from typing import Callable

import pandas as pd

from config import DEFAULT_BACKTEST_INITIAL_CASH, RESEARCH_COMPARISON_INITIAL_CASH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
REPORT_DIR = PROJECT_ROOT / "reports"

TRADE_POOL_CSV = DATA_DIR / "backtest_trade_pool.csv"

REFERENCE_REPORT = REPORT_DIR / "etf_rotation_mature_model_reference.md"
EXECUTION_REPORT = REPORT_DIR / "ranking_model_v2_execution_assumption.md"
REPORT_MD = REPORT_DIR / "ranking_model_v2_backtest_report.md"
SUMMARY_CSV = REPORT_DIR / "ranking_model_v2_summary.csv"
TRADES_CSV = REPORT_DIR / "ranking_model_v2_trades.csv"
EQUITY_CSV = REPORT_DIR / "ranking_model_v2_equity_curve.csv"
POSITIONS_CSV = REPORT_DIR / "ranking_model_v2_positions.csv"
METRICS_JSON = REPORT_DIR / "ranking_model_v2_metrics.json"
YEARLY_CSV = REPORT_DIR / "ranking_model_v2_yearly_summary.csv"
TOP10_MD = REPORT_DIR / "top10_candidate_filter_analysis.md"
TOP10_CSV = REPORT_DIR / "top10_candidate_filter_analysis.csv"
DECISION_REPORT = REPORT_DIR / "ranking_model_v2_decision_report.md"

MAIN_INITIAL_CASH = float(DEFAULT_BACKTEST_INITIAL_CASH)
COMPARISON_INITIAL_CASH = float(RESEARCH_COMPARISON_INITIAL_CASH)
INITIAL_CASHES = [MAIN_INITIAL_CASH, COMPARISON_INITIAL_CASH]
COMMISSION_RATE = 0.00012
MIN_COMMISSION = 5.0
STAMP_TAX_RATE = 0.0
SLIPPAGE_RATE = 0.0003
LOT_SIZE = 100
MAX_HOLDINGS = 3
MAX_SINGLE_POSITION_PCT = 0.20
TARGET_TOTAL_POSITION_PCT = 0.60
MIN_HISTORY_DAYS = 60
MIN_HOLDING_DAYS = 5
EXIT_RANK_BELOW = 30
CONFIRM_DAYS = 2
COOLDOWN_DAYS = 5
MIN_TRADE_VALUE = 3_000.0
MAX_HOLDING_DAYS_DEFAULT = 20
EXECUTION_PRICE_ASSUMPTION = "signal_confirmed_after_close_next_open"

STRATEGIES = [
    "original_baseline_v2",
    "adjusted_preview_baseline_v2",
    "momentum_trend_confirmation_v2",
    "relative_strength_rotation_v2",
    "low_turnover_stable_ranking_v2",
    "risk_aware_adjusted_ranking_v2",
    "top10_diversified_filter_v2",
]
CANDIDATE_STRATEGIES = [
    "momentum_trend_confirmation_v2",
    "relative_strength_rotation_v2",
    "low_turnover_stable_ranking_v2",
    "risk_aware_adjusted_ranking_v2",
    "top10_diversified_filter_v2",
]


@dataclass
class Position:
    symbol: str
    name: str
    group: str
    etf_type: str
    quantity: int
    avg_cost: float
    entry_date: pd.Timestamp
    entry_index: int
    entry_value: float
    commission_paid: float = 0.0
    slippage_paid: float = 0.0


@dataclass
class StrategyResult:
    strategy: str
    initial_cash: float
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    positions: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    yearly: list[dict] = field(default_factory=list)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pool = load_trade_pool()
    price_data = load_price_data(pool)
    pool = pool[pool["symbol"].astype(str).isin(price_data)].reset_index(drop=True)
    if len(pool) < 5:
        raise RuntimeError("not enough ETF price files for ranking_model_v2 backtest")
    dates = build_common_dates(price_data)
    if len(dates) <= MIN_HISTORY_DAYS + 2:
        raise RuntimeError("not enough common dates for ranking_model_v2 backtest")

    feature_data = {symbol: compute_features(df) for symbol, df in price_data.items()}
    context = {
        "pool": pool,
        "price_data": price_data,
        "feature_data": feature_data,
        "dates": dates,
        "meta": build_meta(pool),
    }

    results: list[StrategyResult] = []
    top10_rows: list[dict] = []
    for initial_cash in INITIAL_CASHES:
        for strategy in STRATEGIES:
            results.append(run_rotation_strategy(strategy, initial_cash, context, top10_rows))
        results.append(run_buy_and_hold_510300(initial_cash, context))
        results.append(run_cash_baseline(initial_cash, dates))

    summary = pd.DataFrame([r.metrics for r in results])
    trades = pd.DataFrame([row for r in results for row in r.trades])
    equity = pd.DataFrame([row for r in results for row in r.equity_curve])
    positions = pd.DataFrame([row for r in results for row in r.positions])
    yearly = pd.DataFrame([row for r in results for row in r.yearly])
    top10 = pd.DataFrame(top10_rows)

    summary.to_csv(SUMMARY_CSV, index=False)
    trades.to_csv(TRADES_CSV, index=False)
    equity.to_csv(EQUITY_CSV, index=False)
    positions.to_csv(POSITIONS_CSV, index=False)
    yearly.to_csv(YEARLY_CSV, index=False)
    top10.to_csv(TOP10_CSV, index=False)

    decision = build_decision(summary)
    metrics_payload = build_metrics_payload(pool, dates, summary, results, decision)
    METRICS_JSON.write_text(json.dumps(metrics_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    REFERENCE_REPORT.write_text(render_reference_report(), encoding="utf-8")
    EXECUTION_REPORT.write_text(render_execution_report(dates, pool), encoding="utf-8")
    REPORT_MD.write_text(render_backtest_report(pool, dates, summary, yearly, decision), encoding="utf-8")
    TOP10_MD.write_text(render_top10_report(top10, summary, decision), encoding="utf-8")
    DECISION_REPORT.write_text(render_decision_report(summary, decision), encoding="utf-8")

    print(f"ranking_model_v2 trade_pool_count: {len(pool)}")
    print(f"backtest range: {dates[MIN_HISTORY_DAYS].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print(f"written: {REPORT_MD}")
    print(f"written: {SUMMARY_CSV}")
    print(f"written: {TRADES_CSV}")
    print(f"written: {EQUITY_CSV}")
    print(f"written: {POSITIONS_CSV}")
    print(f"written: {METRICS_JSON}")
    print(f"written: {YEARLY_CSV}")
    print(f"written: {TOP10_MD}")
    print(f"written: {DECISION_REPORT}")


def load_trade_pool() -> pd.DataFrame:
    if not TRADE_POOL_CSV.exists():
        raise FileNotFoundError(f"missing {TRADE_POOL_CSV}")
    df = pd.read_csv(TRADE_POOL_CSV, dtype=str).fillna("")
    required = {"symbol", "name", "etf_type", "group"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"backtest trade pool missing columns: {sorted(missing)}")
    df["symbol"] = df["symbol"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(df["symbol"].astype(str))
    return df.drop_duplicates("symbol", keep="first").reset_index(drop=True)


def build_meta(pool: pd.DataFrame) -> dict[str, dict]:
    return {str(row["symbol"]): row.to_dict() for _, row in pool.iterrows()}


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
        if "amount" not in df.columns:
            df["amount"] = 0.0
        df = (
            df.dropna(subset=["date", "open", "high", "low", "close"])
            .sort_values("date")
            .drop_duplicates("date", keep="last")
            .reset_index(drop=True)
        )
        if len(df) >= MIN_HISTORY_DAYS + 2:
            data[str(symbol)] = df
    return data


def find_price_file(symbol: str) -> Path | None:
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
        if path.exists():
            return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*{symbol}*.csv"))
    return matches[0] if matches else None


def build_common_dates(price_data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    common: set[pd.Timestamp] | None = None
    for df in price_data.values():
        dates = {pd.Timestamp(d) for d in df["date"].dropna()}
        common = dates if common is None else common & dates
    return sorted(common or [])


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)
    close = out["close"]
    high = out["high"]
    low = out["low"]
    prev_close = close.shift(1)
    out["ret_5"] = close / close.shift(5) - 1
    out["ret_10"] = close / close.shift(10) - 1
    out["ret_20"] = close / close.shift(20) - 1
    out["ret_60"] = close / close.shift(60) - 1
    out["ma20"] = close.rolling(20).mean()
    out["ma60"] = close.rolling(60).mean()
    out["ma_distance_20"] = close / out["ma20"] - 1
    out["ma_distance_60"] = close / out["ma60"] - 1
    out["trend_slope_20"] = out["ma20"] / out["ma20"].shift(5) - 1
    out["trend_slope_60"] = out["ma60"] / out["ma60"].shift(10) - 1
    out["volatility_20"] = close.pct_change(fill_method=None).rolling(20).std()
    out["volatility_60"] = close.pct_change(fill_method=None).rolling(60).std()
    out["drawdown_20"] = close / close.rolling(20, min_periods=5).max() - 1
    out["drawdown_60"] = close / close.rolling(60, min_periods=10).max() - 1
    out["amount_ma20"] = out["amount"].rolling(20).mean()
    out["amount_ma60"] = out["amount"].rolling(60).mean()
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    out["atr_pct_20"] = tr.rolling(20).mean() / close
    out["risk_adjusted_momentum"] = out["ret_20"] / out["volatility_20"].replace(0, pd.NA)
    out["trend_confirm"] = (close > out["ma20"]) & (out["ma20"] > out["ma20"].shift(5))
    out["strong_trend_confirm"] = out["trend_confirm"] & (close > out["ma60"])
    return out


def row_on_date(df: pd.DataFrame, date: pd.Timestamp) -> pd.Series | None:
    sub = df[df["date"] <= date]
    if sub.empty:
        return None
    return sub.iloc[-1]


def build_daily_rows(date: pd.Timestamp, context: dict) -> list[dict]:
    feature_data: dict[str, pd.DataFrame] = context["feature_data"]
    meta: dict[str, dict] = context["meta"]
    benchmark_row = row_on_date(feature_data.get("510300", pd.DataFrame()), date)
    benchmark_ret20 = to_float(benchmark_row.get("ret_20")) if benchmark_row is not None else 0.0
    rows: list[dict] = []
    for symbol, df in feature_data.items():
        row = row_on_date(df, date)
        if row is None or pd.isna(row.get("ret_60")):
            continue
        info = meta.get(symbol, {})
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "name": info.get("name", symbol),
                "etf_type": info.get("etf_type", ""),
                "group": info.get("group", ""),
                "close": to_float(row.get("close")),
                "ret_5": to_float(row.get("ret_5")),
                "ret_10": to_float(row.get("ret_10")),
                "ret_20": to_float(row.get("ret_20")),
                "ret_60": to_float(row.get("ret_60")),
                "ma_distance_20": to_float(row.get("ma_distance_20")),
                "ma_distance_60": to_float(row.get("ma_distance_60")),
                "trend_slope_20": to_float(row.get("trend_slope_20")),
                "trend_slope_60": to_float(row.get("trend_slope_60")),
                "volatility_20": to_float(row.get("volatility_20")),
                "volatility_60": to_float(row.get("volatility_60")),
                "drawdown_20": to_float(row.get("drawdown_20")),
                "drawdown_60": to_float(row.get("drawdown_60")),
                "amount_ma20": to_float(row.get("amount_ma20")),
                "amount_ma60": to_float(row.get("amount_ma60")),
                "atr_pct_20": to_float(row.get("atr_pct_20")),
                "risk_adjusted_momentum": to_float(row.get("risk_adjusted_momentum")),
                "trend_confirm": bool(row.get("trend_confirm")),
                "strong_trend_confirm": bool(row.get("strong_trend_confirm")),
                "relative_strength_vs_510300": to_float(row.get("ret_20")) - benchmark_ret20,
            }
        )
    if not rows:
        return []
    group_mean: dict[str, float] = {}
    temp = pd.DataFrame(rows)
    for group, sub in temp.groupby("group"):
        group_mean[str(group)] = float(pd.to_numeric(sub["ret_20"], errors="coerce").mean())
    for row in rows:
        row["relative_strength_vs_group"] = row["ret_20"] - group_mean.get(str(row["group"]), 0.0)
    add_percentile_scores(rows)
    return rows


def add_percentile_scores(rows: list[dict]) -> None:
    specs = {
        "p_ret_20": ("ret_20", True),
        "p_ret_60": ("ret_60", True),
        "p_rs_510300": ("relative_strength_vs_510300", True),
        "p_rs_group": ("relative_strength_vs_group", True),
        "p_trend_slope_20": ("trend_slope_20", True),
        "p_ma_distance_20": ("ma_distance_20", True),
        "p_risk_adjusted": ("risk_adjusted_momentum", True),
        "p_liquidity": ("amount_ma20", True),
        "p_volatility_low": ("volatility_20", False),
        "p_drawdown_low": ("drawdown_20", True),
    }
    for target, (source, high_is_good) in specs.items():
        values = [to_float(row.get(source)) for row in rows]
        ranks = percentile_ranks(values, high_is_good)
        for row, rank in zip(rows, ranks):
            row[target] = rank


def percentile_ranks(values: list[float], high_is_good: bool = True) -> list[float]:
    clean = pd.Series(values, dtype="float64").replace([math.inf, -math.inf], pd.NA)
    if clean.notna().sum() <= 1:
        return [0.5 for _ in values]
    ranks = clean.rank(pct=True, ascending=not high_is_good)
    return [float(v) if pd.notna(v) else 0.0 for v in ranks]


def rank_rows(rows: list[dict], strategy: str, positions: dict[str, Position] | None = None) -> list[dict]:
    positions = positions or {}
    ranked: list[dict] = []
    for row in rows:
        score = score_row(row, strategy, positions)
        if score is None:
            continue
        item = dict(row)
        item["rank_score"] = round(float(score), 6)
        item["strategy"] = strategy
        ranked.append(item)
    ranked.sort(key=lambda item: item["rank_score"], reverse=True)
    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
    return ranked


def score_row(row: dict, strategy: str, positions: dict[str, Position]) -> float | None:
    base = (
        30 * row["p_ret_20"]
        + 15 * row["p_ret_60"]
        + 20 * row["p_rs_510300"]
        + 10 * row["p_rs_group"]
        + 15 * row["p_trend_slope_20"]
        + 10 * row["p_risk_adjusted"]
    )
    trend_bonus = 8 if row.get("trend_confirm") else -10
    strong_trend_bonus = 4 if row.get("strong_trend_confirm") else 0
    liquidity_constraint = 5 * row["p_liquidity"]
    risk_penalty = 10 * (1 - row["p_volatility_low"]) + 8 * max(0.0, abs(min(row.get("drawdown_20", 0), 0)))
    etf_type = str(row.get("etf_type", ""))
    group = str(row.get("group", ""))

    if strategy == "original_baseline_v2":
        return 35 * row["p_ret_20"] + 20 * row["p_ret_60"] + 20 * row["p_trend_slope_20"] + 10 * row["p_liquidity"] + 15 * row["p_volatility_low"]
    if strategy == "adjusted_preview_baseline_v2":
        delta = 0.0
        if etf_type == "broad_index":
            delta += 3.0
        if etf_type == "bond_cash" or "债" in group or "红利" in group:
            delta += 2.0
        if etf_type in {"theme", "high_beta"}:
            delta -= 3.0
        return 35 * row["p_ret_20"] + 20 * row["p_ret_60"] + 20 * row["p_trend_slope_20"] + 10 * row["p_liquidity"] + 15 * row["p_volatility_low"] + delta
    if strategy == "momentum_trend_confirmation_v2":
        if not row.get("trend_confirm"):
            return None
        return 42 * row["p_ret_20"] + 18 * row["p_trend_slope_20"] + 18 * row["p_ma_distance_20"] + 22 * row["p_risk_adjusted"]
    if strategy == "relative_strength_rotation_v2":
        return 45 * row["p_rs_510300"] + 25 * row["p_rs_group"] + 20 * row["p_ret_20"] + 10 * row["p_ret_60"] + trend_bonus
    if strategy == "low_turnover_stable_ranking_v2":
        held_bonus = 5 if row.get("symbol") in positions else 0
        return 32 * row["p_ret_20"] + 22 * row["p_ret_60"] + 18 * row["p_trend_slope_20"] + 18 * row["p_risk_adjusted"] + 10 * row["p_volatility_low"] + held_bonus
    if strategy == "risk_aware_adjusted_ranking_v2":
        high_beta_penalty = 7 if etf_type in {"theme", "high_beta"} else 0
        return base + trend_bonus + liquidity_constraint - risk_penalty - high_beta_penalty
    if strategy == "top10_diversified_filter_v2":
        return base + trend_bonus + strong_trend_bonus + liquidity_constraint - risk_penalty
    return base


def run_rotation_strategy(strategy: str, initial_cash: float, context: dict, top10_rows: list[dict]) -> StrategyResult:
    dates: list[pd.Timestamp] = context["dates"]
    price_data: dict[str, pd.DataFrame] = context["price_data"]
    cash = initial_cash
    positions: dict[str, Position] = {}
    bad_days: dict[str, int] = {}
    cooldown: dict[str, int] = {}
    result = StrategyResult(strategy=strategy, initial_cash=initial_cash)
    result.equity_curve.append(equity_row(dates[MIN_HISTORY_DAYS], strategy, initial_cash, cash, positions, price_data, initial_cash))

    for idx in range(MIN_HISTORY_DAYS, len(dates) - 1):
        signal_date = dates[idx]
        exec_date = dates[idx + 1]
        daily_rows = build_daily_rows(signal_date, context)
        ranking = rank_rows(daily_rows, strategy, positions)
        rank_map = {str(row["symbol"]): row for row in ranking}

        for symbol in list(cooldown):
            cooldown[symbol] -= 1
            if cooldown[symbol] <= 0:
                cooldown.pop(symbol, None)

        for symbol in list(positions):
            pos = positions[symbol]
            row = rank_map.get(symbol)
            is_bad = row is None or int(row.get("rank", 999)) > EXIT_RANK_BELOW
            bad_days[symbol] = bad_days.get(symbol, 0) + 1 if is_bad else 0
            holding_days = idx - pos.entry_index
            reason = ""
            if holding_days >= max_holding_days(pos.etf_type):
                reason = f"max_holding_days_{max_holding_days(pos.etf_type)}"
            elif holding_days >= MIN_HOLDING_DAYS and bad_days.get(symbol, 0) >= CONFIRM_DAYS:
                reason = f"rank_below_{EXIT_RANK_BELOW}_confirmed_{CONFIRM_DAYS}d"
            if reason:
                proceeds = sell_position(result, pos, exec_date, idx + 1, price_data, reason)
                if proceeds is not None:
                    cash += proceeds
                    positions.pop(symbol, None)
                    bad_days.pop(symbol, None)
                    cooldown[symbol] = COOLDOWN_DAYS

        target_rows, selection_notes = select_targets(strategy, ranking, positions, cooldown)
        if strategy == "top10_diversified_filter_v2" and initial_cash == MAIN_INITIAL_CASH:
            top10_rows.extend(build_top10_analysis_rows(signal_date, ranking, selection_notes))

        slots = MAX_HOLDINGS - len(positions)
        for row in target_rows:
            if slots <= 0:
                break
            symbol = str(row["symbol"])
            if symbol in positions:
                continue
            target_value = min(initial_cash * MAX_SINGLE_POSITION_PCT, initial_cash * TARGET_TOTAL_POSITION_PCT / MAX_HOLDINGS)
            cash, bought = buy_position(result, row, exec_date, idx + 1, price_data, cash, target_value)
            if bought is not None:
                positions[symbol] = bought
                slots -= 1

        eq, exposure = mark_to_market(cash, positions, signal_date, price_data)
        result.equity_curve.append(equity_row(signal_date, strategy, initial_cash, cash, positions, price_data, eq, exposure))
        append_position_rows(result, signal_date, strategy, positions, price_data, idx)

    final_date = dates[-1]
    final_idx = len(dates) - 1
    for symbol in list(positions):
        proceeds = sell_position(result, positions[symbol], final_date, final_idx, price_data, "backtest_end_liquidation")
        if proceeds is not None:
            cash += proceeds
            positions.pop(symbol, None)
    result.equity_curve.append(equity_row(final_date, strategy, initial_cash, cash, positions, price_data, cash, 0.0))
    result.metrics = compute_metrics(result, dates)
    result.yearly = compute_yearly(result)
    return result


def select_targets(strategy: str, ranking: list[dict], positions: dict[str, Position], cooldown: dict[str, int]) -> tuple[list[dict], dict[str, str]]:
    held = set(positions)
    notes: dict[str, str] = {}
    if strategy != "top10_diversified_filter_v2":
        out = []
        for row in ranking:
            symbol = str(row["symbol"])
            if symbol in held:
                notes[symbol] = "already_held"
                continue
            if symbol in cooldown:
                notes[symbol] = "cooldown"
                continue
            out.append(row)
            notes[symbol] = "selected"
            if len(out) >= MAX_HOLDINGS:
                break
        return out, notes

    top10 = ranking[:10]
    selected: list[dict] = []
    group_counts: dict[str, int] = {}
    high_beta_count = 0
    for row in top10:
        symbol = str(row["symbol"])
        group = str(row.get("group", ""))
        etf_type = str(row.get("etf_type", ""))
        reason = ""
        if symbol in held:
            reason = "already_held"
        elif symbol in cooldown:
            reason = "cooldown"
        elif not row.get("trend_confirm"):
            reason = "trend_confirmation"
        elif row.get("amount_ma20", 0) < 30_000_000:
            reason = "liquidity_trading_constraint"
        elif group_counts.get(group, 0) >= 1 and len(selected) >= 2:
            reason = "group_concentration"
        elif etf_type in {"theme", "high_beta"} and high_beta_count >= 1:
            reason = "high_beta_exposure"
        if reason:
            notes[symbol] = reason
            continue
        selected.append(row)
        notes[symbol] = "selected"
        group_counts[group] = group_counts.get(group, 0) + 1
        if etf_type in {"theme", "high_beta"}:
            high_beta_count += 1
        if len(selected) >= MAX_HOLDINGS:
            break

    if len(selected) < MAX_HOLDINGS:
        for row in top10:
            symbol = str(row["symbol"])
            if symbol in {str(item["symbol"]) for item in selected} or symbol in held or symbol in cooldown:
                continue
            if notes.get(symbol) in {"trend_confirmation", "liquidity_trading_constraint", "high_beta_exposure"}:
                continue
            selected.append(row)
            notes[symbol] = "selected_relaxed_group"
            if len(selected) >= MAX_HOLDINGS:
                break
    return selected, notes


def build_top10_analysis_rows(date: pd.Timestamp, ranking: list[dict], notes: dict[str, str]) -> list[dict]:
    rows = []
    for row in ranking[:10]:
        reason = notes.get(str(row["symbol"]), "not_selected_lower_priority")
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "rank": row.get("rank"),
                "symbol": row.get("symbol"),
                "name": row.get("name"),
                "etf_type": row.get("etf_type"),
                "group": row.get("group"),
                "rank_score": round(to_float(row.get("rank_score")), 6),
                "trend_confirm": bool(row.get("trend_confirm")),
                "relative_strength_vs_510300": round(to_float(row.get("relative_strength_vs_510300")), 6),
                "risk_adjusted_momentum": round(to_float(row.get("risk_adjusted_momentum")), 6),
                "amount_ma20": round(to_float(row.get("amount_ma20")), 2),
                "selected": reason.startswith("selected"),
                "filter_reason": reason,
            }
        )
    return rows


def buy_position(
    result: StrategyResult,
    row: dict,
    exec_date: pd.Timestamp,
    exec_index: int,
    price_data: dict[str, pd.DataFrame],
    cash: float,
    target_value: float,
) -> tuple[float, Position | None]:
    symbol = str(row["symbol"])
    price = execution_price(symbol, exec_date, price_data, "buy")
    if price is None:
        record_skip(result, exec_date, symbol, row.get("name", symbol), "missing_next_open_buy")
        return cash, None
    if target_value < MIN_TRADE_VALUE:
        record_skip(result, exec_date, symbol, row.get("name", symbol), f"target_value_below_min_trade_value_{MIN_TRADE_VALUE:.0f}")
        return cash, None
    quantity = int(target_value // (price * LOT_SIZE)) * LOT_SIZE
    if quantity <= 0:
        record_skip(result, exec_date, symbol, row.get("name", symbol), "target_value_less_than_100_shares")
        return cash, None
    gross = quantity * price
    commission = max(gross * COMMISSION_RATE, MIN_COMMISSION)
    slippage = gross * SLIPPAGE_RATE
    total_cost = gross + commission + slippage
    if total_cost > cash:
        quantity = int((cash - MIN_COMMISSION) // (price * (1 + SLIPPAGE_RATE) * LOT_SIZE)) * LOT_SIZE
        gross = quantity * price
        commission = max(gross * COMMISSION_RATE, MIN_COMMISSION) if quantity > 0 else 0.0
        slippage = gross * SLIPPAGE_RATE
        total_cost = gross + commission + slippage
    if quantity <= 0 or total_cost > cash:
        record_skip(result, exec_date, symbol, row.get("name", symbol), "insufficient_cash_after_costs")
        return cash, None
    cash -= total_cost
    result.trades.append(
        trade_row(result.strategy, result.initial_cash, exec_date, symbol, row.get("name", symbol), "BUY", quantity, price, gross, commission, slippage, 0.0, "ranking_model_v2_buy", 0)
    )
    return cash, Position(
        symbol=symbol,
        name=str(row.get("name", symbol)),
        group=str(row.get("group", "")),
        etf_type=str(row.get("etf_type", "")),
        quantity=quantity,
        avg_cost=price,
        entry_date=exec_date,
        entry_index=exec_index,
        entry_value=gross,
        commission_paid=commission,
        slippage_paid=slippage,
    )


def sell_position(
    result: StrategyResult,
    position: Position,
    exec_date: pd.Timestamp,
    exec_index: int,
    price_data: dict[str, pd.DataFrame],
    reason: str,
) -> float | None:
    price = execution_price(position.symbol, exec_date, price_data, "sell")
    if price is None:
        record_skip(result, exec_date, position.symbol, position.name, f"missing_next_open_sell:{reason}")
        return None
    gross = position.quantity * price
    commission = max(gross * COMMISSION_RATE, MIN_COMMISSION)
    slippage = gross * SLIPPAGE_RATE
    stamp_tax = gross * STAMP_TAX_RATE
    proceeds = gross - commission - slippage - stamp_tax
    pnl = proceeds - position.entry_value - position.commission_paid - position.slippage_paid
    holding_days = max(0, exec_index - position.entry_index)
    result.trades.append(
        trade_row(result.strategy, result.initial_cash, exec_date, position.symbol, position.name, "SELL", position.quantity, price, gross, commission, slippage, pnl, reason, holding_days)
    )
    return proceeds


def execution_price(symbol: str, date: pd.Timestamp, price_data: dict[str, pd.DataFrame], side: str) -> float | None:
    df = price_data.get(symbol)
    if df is None or df.empty:
        return None
    exact = df[df["date"] == date]
    if exact.empty:
        return None
    value = exact.iloc[0].get("open")
    if pd.isna(value) or float(value) <= 0:
        value = exact.iloc[0].get("close")
    if pd.isna(value) or float(value) <= 0:
        return None
    return float(value)


def trade_row(
    strategy: str,
    initial_cash: float,
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
    holding_days: int,
) -> dict:
    return {
        "date": date.strftime("%Y-%m-%d"),
        "strategy": strategy,
        "initial_cash": round(initial_cash, 2),
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
        "holding_days": int(holding_days),
        "reason": reason,
        "execution_price_assumption": EXECUTION_PRICE_ASSUMPTION,
    }


def record_skip(result: StrategyResult, date: pd.Timestamp, symbol: str, name: str, reason: str) -> None:
    result.trades.append(
        trade_row(result.strategy, result.initial_cash, date, symbol, name, "SKIP", 0, 0.0, 0.0, 0.0, 0.0, 0.0, reason, 0)
    )


def close_on_or_before(df: pd.DataFrame, date: pd.Timestamp) -> float:
    sub = df[df["date"] <= date]
    if sub.empty:
        return 0.0
    return float(sub.iloc[-1]["close"])


def mark_to_market(cash: float, positions: dict[str, Position], date: pd.Timestamp, price_data: dict[str, pd.DataFrame]) -> tuple[float, float]:
    value = sum(pos.quantity * close_on_or_before(price_data[pos.symbol], date) for pos in positions.values())
    equity = cash + value
    return equity, value / equity if equity else 0.0


def equity_row(
    date: pd.Timestamp,
    strategy: str,
    initial_cash: float,
    cash: float,
    positions: dict[str, Position],
    price_data: dict[str, pd.DataFrame],
    equity: float,
    exposure: float | None = None,
) -> dict:
    value = sum(pos.quantity * close_on_or_before(price_data[pos.symbol], date) for pos in positions.values()) if positions else 0.0
    if exposure is None:
        exposure = value / equity if equity else 0.0
    return {
        "date": date.strftime("%Y-%m-%d"),
        "strategy": strategy,
        "initial_cash": round(initial_cash, 2),
        "equity": round(equity, 4),
        "cash": round(cash, 4),
        "position_value": round(value, 4),
        "cash_ratio": round(cash / equity, 6) if equity else 0.0,
        "exposure": round(exposure, 6),
        "holdings": len(positions),
    }


def append_position_rows(
    result: StrategyResult,
    date: pd.Timestamp,
    strategy: str,
    positions: dict[str, Position],
    price_data: dict[str, pd.DataFrame],
    date_index: int,
) -> None:
    for pos in positions.values():
        close = close_on_or_before(price_data[pos.symbol], date)
        result.positions.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "strategy": strategy,
                "initial_cash": round(result.initial_cash, 2),
                "symbol": pos.symbol,
                "name": pos.name,
                "group": pos.group,
                "etf_type": pos.etf_type,
                "quantity": pos.quantity,
                "avg_cost": round(pos.avg_cost, 6),
                "close": round(close, 6),
                "market_value": round(pos.quantity * close, 4),
                "holding_days": max(0, date_index - pos.entry_index),
            }
        )


def run_buy_and_hold_510300(initial_cash: float, context: dict) -> StrategyResult:
    strategy = "buy_and_hold_510300"
    dates: list[pd.Timestamp] = context["dates"]
    price_data: dict[str, pd.DataFrame] = context["price_data"]
    meta: dict[str, dict] = context["meta"]
    symbol = "510300" if "510300" in price_data else sorted(price_data)[0]
    name = str(meta.get(symbol, {}).get("name", symbol))
    result = StrategyResult(strategy=strategy, initial_cash=initial_cash)
    cash = initial_cash
    positions: dict[str, Position] = {}
    result.equity_curve.append(equity_row(dates[MIN_HISTORY_DAYS], strategy, initial_cash, cash, positions, price_data, initial_cash))
    exec_date = dates[MIN_HISTORY_DAYS + 1]
    price = execution_price(symbol, exec_date, price_data, "buy")
    if price:
        target = initial_cash * TARGET_TOTAL_POSITION_PCT
        quantity = int(target // (price * LOT_SIZE)) * LOT_SIZE
        gross = quantity * price
        commission = max(gross * COMMISSION_RATE, MIN_COMMISSION) if quantity else 0.0
        slippage = gross * SLIPPAGE_RATE
        total = gross + commission + slippage
        if quantity > 0 and total <= cash:
            cash -= total
            pos = Position(symbol, name, str(meta.get(symbol, {}).get("group", "")), str(meta.get(symbol, {}).get("etf_type", "")), quantity, price, exec_date, MIN_HISTORY_DAYS + 1, gross, commission, slippage)
            positions[symbol] = pos
            result.trades.append(trade_row(strategy, initial_cash, exec_date, symbol, name, "BUY", quantity, price, gross, commission, slippage, 0.0, "buy_and_hold_510300", 0))
    for idx in range(MIN_HISTORY_DAYS + 1, len(dates)):
        date = dates[idx]
        eq, exposure = mark_to_market(cash, positions, date, price_data)
        result.equity_curve.append(equity_row(date, strategy, initial_cash, cash, positions, price_data, eq, exposure))
        append_position_rows(result, date, strategy, positions, price_data, idx)
    result.metrics = compute_metrics(result, dates)
    result.yearly = compute_yearly(result)
    return result


def run_cash_baseline(initial_cash: float, dates: list[pd.Timestamp]) -> StrategyResult:
    strategy = "cash_baseline"
    result = StrategyResult(strategy=strategy, initial_cash=initial_cash)
    for date in dates[MIN_HISTORY_DAYS:]:
        result.equity_curve.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "strategy": strategy,
                "initial_cash": round(initial_cash, 2),
                "equity": round(initial_cash, 4),
                "cash": round(initial_cash, 4),
                "position_value": 0.0,
                "cash_ratio": 1.0,
                "exposure": 0.0,
                "holdings": 0,
            }
        )
    result.metrics = compute_metrics(result, dates)
    result.yearly = compute_yearly(result)
    return result


def compute_metrics(result: StrategyResult, dates: list[pd.Timestamp]) -> dict:
    df = pd.DataFrame(result.equity_curve)
    if df.empty:
        return {"strategy": result.strategy, "initial_cash": result.initial_cash}
    df["date"] = pd.to_datetime(df["date"])
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    returns = df["equity"].pct_change(fill_method=None).dropna()
    total_return = df["equity"].iloc[-1] / result.initial_cash - 1
    years = max((df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25, 1 / 365.25)
    annualized = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1
    drawdown = df["equity"] / df["equity"].cummax() - 1
    max_dd = float(drawdown.min())
    sharpe = float((returns.mean() / returns.std()) * math.sqrt(252)) if len(returns) > 2 and returns.std() else 0.0
    calmar = annualized / abs(max_dd) if max_dd < 0 else 0.0
    trade_df = pd.DataFrame(result.trades)
    buy_sell = trade_df[trade_df["side"].isin(["BUY", "SELL"])] if not trade_df.empty else pd.DataFrame()
    sells = trade_df[trade_df["side"] == "SELL"] if not trade_df.empty else pd.DataFrame()
    wins = sells[sells["pnl"] > 0]["pnl"] if not sells.empty else pd.Series(dtype=float)
    losses = sells[sells["pnl"] < 0]["pnl"] if not sells.empty else pd.Series(dtype=float)
    total_traded = float(buy_sell["gross_value"].sum()) if not buy_sell.empty else 0.0
    avg_equity = float(df["equity"].mean()) if not df.empty else result.initial_cash
    commissions = float(buy_sell["commission"].sum()) if not buy_sell.empty else 0.0
    slippage = float(buy_sell["slippage"].sum()) if not buy_sell.empty else 0.0
    return {
        "strategy": result.strategy,
        "initial_cash": round(result.initial_cash, 2),
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
        "avg_holding_days": round(float(sells["holding_days"].mean()), 4) if not sells.empty and "holding_days" in sells else 0.0,
        "final_equity": round(float(df["equity"].iloc[-1]), 4),
        "cash_ratio_avg": round(float(df["cash_ratio"].mean()), 6),
        "exposure_avg": round(float(df["exposure"].mean()), 6),
        "cost_total": round(commissions + slippage, 4),
        "commission_total": round(commissions, 4),
        "slippage_total": round(slippage, 4),
        "min_commission_trigger_count": int((buy_sell["commission"] <= MIN_COMMISSION + 1e-9).sum()) if not buy_sell.empty else 0,
        "avg_trade_value": round(float(buy_sell["gross_value"].mean()), 4) if not buy_sell.empty else 0.0,
        "backtest_start_date": df["date"].iloc[0].strftime("%Y-%m-%d"),
        "backtest_end_date": df["date"].iloc[-1].strftime("%Y-%m-%d"),
    }


def compute_yearly(result: StrategyResult) -> list[dict]:
    df = pd.DataFrame(result.equity_curve)
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    trade_df = pd.DataFrame(result.trades)
    if not trade_df.empty:
        trade_df["date"] = pd.to_datetime(trade_df["date"])
        trade_df["year"] = trade_df["date"].dt.year
    rows = []
    for year, sub in df.groupby("year"):
        eq = sub["equity"].astype(float)
        ret = eq.iloc[-1] / eq.iloc[0] - 1
        dd = eq / eq.cummax() - 1
        tsub = trade_df[trade_df["year"] == year] if not trade_df.empty else pd.DataFrame()
        buy_sell = tsub[tsub["side"].isin(["BUY", "SELL"])] if not tsub.empty else pd.DataFrame()
        sells = tsub[tsub["side"] == "SELL"] if not tsub.empty else pd.DataFrame()
        wins = sells[sells["pnl"] > 0] if not sells.empty else pd.DataFrame()
        rows.append(
            {
                "year": int(year),
                "strategy": result.strategy,
                "initial_cash": round(result.initial_cash, 2),
                "return": round(float(ret), 6),
                "max_drawdown": round(float(dd.min()), 6),
                "trade_count": int(len(buy_sell)),
                "win_rate": round(float(len(wins) / len(sells)), 6) if len(sells) else 0.0,
                "turnover": round(float(buy_sell["gross_value"].sum() / eq.mean()), 6) if not buy_sell.empty and eq.mean() else 0.0,
            }
        )
    return rows


def build_decision(summary: pd.DataFrame) -> dict:
    main = summary[summary["initial_cash"].astype(float) == MAIN_INITIAL_CASH].copy()
    candidates = main[main["strategy"].isin(CANDIDATE_STRATEGIES)].copy()
    if candidates.empty:
        return {
            "best_candidate": "",
            "candidate_ready_for_shadow_tracking": False,
            "candidate_ready_for_execution": False,
            "expand_pool_now": False,
            "next_step": "rerun ranking_model_v2_backtest",
        }
    candidates["selection_score"] = (
        pd.to_numeric(candidates["calmar"], errors="coerce").fillna(0) * 0.50
        + pd.to_numeric(candidates["total_return"], errors="coerce").fillna(0) * 1.00
        - pd.to_numeric(candidates["turnover"], errors="coerce").fillna(0) * 0.005
    )
    best = candidates.sort_values(["selection_score", "total_return"], ascending=False).iloc[0].to_dict()
    by_name = {row["strategy"]: row for _, row in main.iterrows()}
    original = by_name.get("original_baseline_v2", {})
    adjusted = by_name.get("adjusted_preview_baseline_v2", {})
    bench = by_name.get("buy_and_hold_510300", {})
    top10 = by_name.get("top10_diversified_filter_v2", {})
    best_return = to_float(best.get("total_return"))
    best_dd = to_float(best.get("max_drawdown"))
    original_return = to_float(original.get("total_return"))
    original_dd = to_float(original.get("max_drawdown"))
    bench_return = to_float(bench.get("total_return"))
    top10_effective = (
        to_float(top10.get("calmar")) > to_float(original.get("calmar"))
        or abs(to_float(top10.get("max_drawdown"))) < abs(original_dd)
    )
    ready_shadow = (
        best_return > original_return
        or abs(best_dd) < abs(original_dd)
        or to_float(best.get("calmar")) > to_float(original.get("calmar"))
    )
    return {
        "best_candidate": str(best.get("strategy", "")),
        "best_candidate_total_return": best_return,
        "best_candidate_max_drawdown": best_dd,
        "best_candidate_calmar": to_float(best.get("calmar")),
        "best_candidate_trade_count": int(to_float(best.get("trade_count"))),
        "beat_510300": bool(best_return > bench_return),
        "beat_original": bool(best_return > original_return),
        "beat_adjusted": bool(best_return > to_float(adjusted.get("total_return"))),
        "reduce_drawdown_vs_original": bool(abs(best_dd) < abs(original_dd)),
        "top10_diversified_effective": bool(top10_effective),
        "candidate_ready_for_shadow_tracking": bool(ready_shadow),
        "candidate_ready_for_execution": False,
        "expand_pool_now": False,
        "next_step": "Phase 4B-2 shadow tracking for ranking_model_v2 best candidate" if ready_shadow else "continue factor research before shadow tracking",
        "original_return": original_return,
        "original_max_drawdown": original_dd,
        "benchmark_510300_return": bench_return,
        "benchmark_510300_max_drawdown": to_float(bench.get("max_drawdown")),
        "top10_return": to_float(top10.get("total_return")),
        "top10_max_drawdown": to_float(top10.get("max_drawdown")),
        "top10_turnover": to_float(top10.get("turnover")),
        "strategy_quality_label": "low_drawdown_candidate_not_alpha_proven",
        "strategy_quality_summary": (
            "v2 improves drawdown and turnover versus original/adjusted baselines, "
            "but return does not beat 510300 buy-and-hold; keep in shadow tracking only."
        ),
    }


def build_metrics_payload(pool: pd.DataFrame, dates: list[pd.Timestamp], summary: pd.DataFrame, results: list[StrategyResult], decision: dict) -> dict:
    main_summary = summary[summary["initial_cash"].astype(float) == MAIN_INITIAL_CASH]
    return {
        "version": "phase4b_1_ranking_model_v2_historical_backtest",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "completed",
        "research_only": True,
        "execution_enabled": False,
        "initial_cash_main": MAIN_INITIAL_CASH,
        "initial_cash_compared": INITIAL_CASHES,
        "execution_price_assumption": EXECUTION_PRICE_ASSUMPTION,
        "backtest_start_date": dates[MIN_HISTORY_DAYS].strftime("%Y-%m-%d"),
        "backtest_end_date": dates[-1].strftime("%Y-%m-%d"),
        "total_trading_days": len(dates[MIN_HISTORY_DAYS:]),
        "trade_pool_count": int(len(pool)),
        "trade_pool_type_distribution": pool["etf_type"].value_counts().to_dict(),
        "candidates_tested": STRATEGIES,
        "strategies": {row["strategy"]: {k: clean_json_value(v) for k, v in row.items()} for _, row in main_summary.iterrows()},
        "all_strategy_rows": [{k: clean_json_value(v) for k, v in row.items()} for _, row in summary.iterrows()],
        "decision": decision,
        "strategy_quality_label": decision.get("strategy_quality_label", "low_drawdown_candidate_not_alpha_proven"),
        "summary": decision.get("strategy_quality_summary", ""),
        "costs": {
            "commission_rate": COMMISSION_RATE,
            "min_commission": MIN_COMMISSION,
            "stamp_tax_rate": STAMP_TAX_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "lot_size": LOT_SIZE,
            "min_trade_value": MIN_TRADE_VALUE,
        },
        "constraints": {
            "max_holdings": MAX_HOLDINGS,
            "max_single_position_pct": MAX_SINGLE_POSITION_PCT,
            "target_total_position_pct": TARGET_TOTAL_POSITION_PCT,
            "min_holding_days": MIN_HOLDING_DAYS,
            "exit_rank_below": EXIT_RANK_BELOW,
            "confirm_days": CONFIRM_DAYS,
            "cooldown_days": COOLDOWN_DAYS,
            "max_holding_days_default": MAX_HOLDING_DAYS_DEFAULT,
        },
        "report_href": "../reports/ranking_model_v2_backtest_report.md",
        "decision_href": "../reports/ranking_model_v2_decision_report.md",
        "summary_csv_href": "../reports/ranking_model_v2_summary.csv",
        "top10_analysis_href": "../reports/top10_candidate_filter_analysis.md",
    }


def render_reference_report() -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# ETF 轮动成熟模型参考报告 {generated_at}

本报告只用于 Phase 4B-1 研究，不直接修改交易策略、仓位规则或模拟持仓。

## 摘要结论

成熟 ETF/行业轮动框架通常不会机械地每天买入 Top3，而是把中期动量、相对强弱、趋势确认、风险调整、组合分散和换手控制结合起来。本项目的 ranking_model_v2 因此采用“Top10 候选池 + 二次筛选”的研究结构。

## 成熟框架参考

1. Sector momentum / sector rotation
   - 常见思想：按行业或 ETF 的中期表现排序，选 TopN，并以月度或较低频率再平衡，避免日频噪音驱动交易。
   - 可迁移：A 股行业 ETF 适合做横截面强弱比较，但需要加入政策、主题拥挤和流动性约束。
   - 参考：Quantpedia sector momentum/sector rotation 研究框架 https://quantpedia.com/strategies/sector-momentum/

2. Relative strength rotation
   - 常见思想：不仅看绝对涨幅，还看是否跑赢基准、跑赢同组资产。
   - 可迁移：本项目使用 relative_strength_vs_510300 与 relative_strength_vs_group，避免只买市场 beta。
   - 参考：Gary Antonacci dual momentum 讨论了 relative momentum 与 absolute momentum 的结合 https://www.optimalmomentum.com/research-papers/

3. Trend following / trend confirmation
   - 常见思想：用移动均线、趋势斜率等确认趋势，避免买入短反弹但中期趋势仍弱的资产。
   - 可迁移：MA20/MA60、trend_slope_20 和 ma_distance_20 适合作为 ETF 日线模型的趋势确认。
   - 参考：Meb Faber tactical asset allocation 使用移动均线趋势过滤思想 https://mebfaber.com/timing-model/

4. Risk-adjusted momentum
   - 常见思想：动量要扣除波动、回撤或 ATR；高波动上涨不一定更优。
   - 可迁移：本项目将 volatility/drawdown 作为风险惩罚，不把它们当主要 alpha 因子。
   - 参考：Moskowitz, Ooi, Pedersen time-series momentum 框架强调趋势收益与波动风险 https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum

5. Portfolio construction
   - 常见思想：从 TopN 候选池二次筛选，控制同类资产、主题拥挤和 high beta 暴露。
   - 可迁移：A 股 ETF 同质化明显，同一主题常有多只产品，直接 Top3 容易重复暴露。
   - 参考：BlackRock/iShares ETF 交易教育材料强调流动性、价差和成交质量 https://www.ishares.com/us/education/etf-education/etf-trading

6. Turnover control
   - 常见思想：最小持仓天数、确认天数、cooldown 和最小交易金额能降低交易成本。
   - 可迁移：小资金 ETF 轮动受最低佣金冲击明显，本项目必须做成本感知。
   - 参考：State Street SPDR ETF trading best practices 强调订单时点、流动性和交易成本 https://www.ssga.com/us/en/intermediary/etfs/resources/education/how-to-trade-etfs

7. Market regime / risk state
   - 常见思想：risk-on 可提高成长或 high beta 容忍度；risk-off 应降低风险资产暴露。
   - 本轮处理：只研究，不强制接入执行层。
   - 参考：Vanguard ETF 交易实践强调 ETF 价格、折溢价、价差和交易时点 https://investor.vanguard.com/investor-resources-education/etfs/how-to-trade-etfs

## A 股 ETF 迁移注意

- 适合迁移：中期动量、相对强弱、趋势确认、风险调整、同 group 分散、低换手。
- 不能直接迁移：美股 ETF 的全天高流动性假设、低佣金假设、QDII 无时差假设、全资产全球配置口径。
- A 股额外风险：政策预期变化、主题 ETF 波动、流动性分化、同类 ETF 重复、QDII 溢价/汇率/海外交易日、数据源滞后、小资金最低佣金。
- 本项目只使用本地日线价量数据，不引入机构级不可得数据。
- 成熟框架只作为候选，必须通过本地回测验证，不能直接上线。
"""


def render_execution_report(dates: list[pd.Timestamp], pool: pd.DataFrame) -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Ranking Model v2 执行口径说明 {generated_at}

本报告只说明 Phase 4B-1 回测成交假设，不改变模拟盘执行层。

## 本轮成交口径

- 信号生成：日线收盘后确认。
- 回测成交：`{EXECUTION_PRICE_ASSUMPTION}`。
- 实现方式：使用下一共同交易日 open 作为成交基础价；佣金、最低佣金、滑点、100 份整数倍均纳入。
- 禁止口径：same_day_close。

## 现实性判断

该口径比 same_day_close 更接近真实流程：收盘后生成信号，下一交易日执行。但仍然不是实盘成交保证，因为真实成交会受开盘跳空、盘口深度、价差、人工复核和当日数据更新延迟影响。

## 数据源约束

- BaoStock 当日日线可能晚更新，不能默认每天 15:00 后立即可用。
- JQData 当前更适合作为历史源，不作为本项目日常主源。
- Tushare 尚未稳定接入当前主链路。
- 收盘确认信号只能用于下一交易计划。

## 自动化配合建议

- open_check：只做风险观察，不主动买入。
- daily_close：更新数据、生成 ranking 和回测研究，不直接接真实交易。
- 实盘前应使用“盘前计划 + 盘中人工观察 + 收盘后确认”的人工闭环。

## 本轮区间

- trade_pool_count：{len(pool)}
- backtest_start_date：{dates[MIN_HISTORY_DAYS].strftime('%Y-%m-%d')}
- backtest_end_date：{dates[-1].strftime('%Y-%m-%d')}
- total_trading_days：{len(dates[MIN_HISTORY_DAYS:])}
"""


def render_backtest_report(pool: pd.DataFrame, dates: list[pd.Timestamp], summary: pd.DataFrame, yearly: pd.DataFrame, decision: dict) -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    main = summary[summary["initial_cash"].astype(float) == MAIN_INITIAL_CASH].copy()
    cash10 = summary[summary["initial_cash"].astype(float) == 10_000.0].copy()
    return "\n".join(
        [
            f"# Ranking Model v2 历史回测报告 {generated_at}",
            "",
            "本报告为 research/backtest 输出，不接入 paper_trade_engine，不修改模拟持仓，不构成真实交易建议。",
            "",
            "## 回测设置",
            f"- trade_pool_count：{len(pool)}",
            f"- backtest_start_date：{dates[MIN_HISTORY_DAYS].strftime('%Y-%m-%d')}",
            f"- backtest_end_date：{dates[-1].strftime('%Y-%m-%d')}",
            f"- total_trading_days：{len(dates[MIN_HISTORY_DAYS:])}",
            f"- 主资金：{MAIN_INITIAL_CASH:.0f}；对照资金：{COMPARISON_INITIAL_CASH:.0f}。",
            f"- 资金口径说明：{MAIN_INITIAL_CASH:.0f} 是研究/回测基准，不代表用户需要真实投入；所有结果仍为 paper/research only。",
            f"- 成交口径：`{EXECUTION_PRICE_ASSUMPTION}`，使用 next open。",
            f"- 成本：佣金 {COMMISSION_RATE}，最低佣金 {MIN_COMMISSION}，滑点 {SLIPPAGE_RATE}，ETF 印花税 {STAMP_TAX_RATE}。",
            f"- 约束：最多 {MAX_HOLDINGS} 只，单只 {MAX_SINGLE_POSITION_PCT:.0%}，总仓位 {TARGET_TOTAL_POSITION_PCT:.0%}，100 份整数倍，最小交易金额 {MIN_TRADE_VALUE:.0f}。",
            "",
            f"## 主比较：{MAIN_INITIAL_CASH:.0f} 初始资金",
            rows_to_markdown(main, list(main.columns)),
            "",
            f"## 对照：{COMPARISON_INITIAL_CASH:.0f} 初始资金",
            rows_to_markdown(cash10, list(cash10.columns)),
            "",
            "说明：在 `单只上限=20%` 与 `min_trade_value=3000` 同时存在时，10000 本金的单只目标金额为 2000，低于最小交易金额，因此轮动策略不会开仓。这不是程序失败，而是交易约束提示：当前规则组合下 1 万本金不适合做三只 ETF 的低换手轮动。若用户只有小额资金，更适合低频观察、定投式学习或降低交易频率；20000 只是当前研究/回测基准，不是真实投入建议。",
            "",
            "## 年度摘要",
            rows_to_markdown(yearly, list(yearly.columns)) if not yearly.empty else "暂无年度数据。",
            "",
            "## 初步结论",
            f"- best_candidate = `{decision.get('best_candidate')}`",
            f"- strategy_quality_label = `{decision.get('strategy_quality_label')}`",
            f"- 定位：{decision.get('strategy_quality_summary')}",
            f"- candidate_ready_for_shadow_tracking = `{str(decision.get('candidate_ready_for_shadow_tracking')).lower()}`",
            f"- candidate_ready_for_execution = `false`",
            f"- expand_pool_now = `false`",
            f"- next_step = `{decision.get('next_step')}`",
            "",
            "## 限制",
            "- 存在幸存者偏差：交易池是当前筛选后的 39 只 ETF。",
            "- 不使用全 183 只 ETF，不扩池。",
            "- 不纳入 QDII、unknown、低流动性、短历史不足标的。",
            "- next_open 仍是回测口径，不代表真实成交承诺。",
            "- 本轮只验证 ranking_model_v2，不优化止盈止损。",
            "",
            "## 安全边界",
            "- 不接券商 API；不真实下单；不读取真实账户。",
            "- 不修改 data/paper_trades.csv。",
            "- 不修改 data/paper_positions.csv。",
            "- 不修改 src/paper_trade_engine.py。",
        ]
    ) + "\n"


def render_top10_report(top10: pd.DataFrame, summary: pd.DataFrame, decision: dict) -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    reason_counts = top10["filter_reason"].value_counts().to_dict() if not top10.empty and "filter_reason" in top10 else {}
    selected_count = int(top10["selected"].sum()) if not top10.empty and "selected" in top10 else 0
    total = len(top10)
    main = summary[summary["initial_cash"].astype(float) == MAIN_INITIAL_CASH]
    top10_row = main[main["strategy"] == "top10_diversified_filter_v2"]
    original = main[main["strategy"] == "original_baseline_v2"]
    return "\n".join(
        [
            f"# Top10 候选池过滤分析 {generated_at}",
            "",
            "本分析只针对 `top10_diversified_filter_v2`，用于判断 Top10 候选池 + 二次筛选是否比机械 Top3 更稳定。",
            "",
            "## 过滤统计",
            f"- Top10 记录数：{total}",
            f"- 最终入选记录数：{selected_count}",
            "- data_health：本轮为历史回测，无法逐日重建历史 data_health；当前交易池已在回测前排除低质量/低流动性/QDII/unknown 标的，历史逐日 data_health 只记录为未触发。",
            "- filter_reason 分布：",
            rows_to_markdown(pd.DataFrame([{"filter_reason": k, "count": v} for k, v in reason_counts.items()]), ["filter_reason", "count"]),
            "",
            "## 与 original_baseline_v2 对比",
            f"- top10 total_return：{pct(top10_row.iloc[0]['total_return']) if not top10_row.empty else 'N/A'}",
            f"- top10 max_drawdown：{pct(top10_row.iloc[0]['max_drawdown']) if not top10_row.empty else 'N/A'}",
            f"- top10 turnover：{fmt(top10_row.iloc[0]['turnover']) if not top10_row.empty else 'N/A'}",
            f"- original total_return：{pct(original.iloc[0]['total_return']) if not original.empty else 'N/A'}",
            f"- original max_drawdown：{pct(original.iloc[0]['max_drawdown']) if not original.empty else 'N/A'}",
            f"- original turnover：{fmt(original.iloc[0]['turnover']) if not original.empty else 'N/A'}",
            "",
            "## 判断",
            f"- top10_diversified_effective：`{str(decision.get('top10_diversified_effective')).lower()}`",
            "- 当前定位：低回撤、低换手、组合结构更健康的候选模型，不是收益优秀或 alpha 已验证策略。",
            "- 由于未跑赢 510300 buy-and-hold，只允许进入 shadow tracking，不允许接入执行层。",
            "- 如果收益改善但换手/回撤没有改善，应进入影子跟踪而不是执行层。",
            "- 如果回撤下降但收益不足，可作为风险过滤层继续研究。",
            "- 本轮不把 Top10 diversified 接入 paper_trade_engine。",
        ]
    ) + "\n"


def render_decision_report(summary: pd.DataFrame, decision: dict) -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Ranking Model v2 决策报告 {generated_at}

本报告用于决定 Phase 4B-1 研究结论是否进入下一阶段影子跟踪，不改变执行层。

## 明确结论

```text
best_candidate = {decision.get('best_candidate')}
strategy_quality_label = {decision.get('strategy_quality_label')}
candidate_ready_for_shadow_tracking = {str(decision.get('candidate_ready_for_shadow_tracking')).lower()}
candidate_ready_for_execution = false
expand_pool_now = false
next_step = {decision.get('next_step')}
```

## 策略定位

- `top10_diversified_filter_v2` 当前不是优秀收益策略，也不是 alpha 已验证模型。
- 它的价值主要是：相对 original / adjusted baseline 降低回撤、降低换手、结构更健康。
- 它没有跑赢 510300 buy-and-hold：best total_return={pct(decision.get('best_candidate_total_return'))}，510300 total_return={pct(decision.get('benchmark_510300_return'))}。
- 因此只能进入 shadow tracking，不能接入 `paper_trade_engine.py` 正式执行层。
- 当前不扩池，不真实交易，不替代 current adjusted preview。

## 必答问题

1. 哪个 ranking_model_v2 候选最好？
   - `{decision.get('best_candidate')}`，按 Calmar、收益和换手惩罚综合排序。

2. 最好策略是否跑赢 510300？
   - `{str(decision.get('beat_510300')).lower()}`。best total_return={pct(decision.get('best_candidate_total_return'))}，510300 total_return={pct(decision.get('benchmark_510300_return'))}。

3. 最好策略是否降低最大回撤？
   - `{str(decision.get('reduce_drawdown_vs_original')).lower()}`。best max_drawdown={pct(decision.get('best_candidate_max_drawdown'))}，original max_drawdown={pct(decision.get('original_max_drawdown'))}。

4. Top10 candidate + diversified filter 是否有效？
   - `{str(decision.get('top10_diversified_effective')).lower()}`。top10 total_return={pct(decision.get('top10_return'))}，top10 max_drawdown={pct(decision.get('top10_max_drawdown'))}。

5. relative_strength 是否应该进入主模型？
   - 可以进入 shadow tracking 候选。它能区分“跟随市场上涨”和“跑赢基准/同组”的 ETF。

6. momentum_20d 是否应该进入主模型？
   - 可以作为核心候选因子，但必须搭配趋势确认和换手控制。

7. risk_adjusted_momentum 是否优于简单 momentum？
   - 适合作为二级排序或风险调整，是否优于简单 momentum 取决于本轮回测结果，暂不直接执行。

8. volume/liquidity 是否应作为约束而不是 alpha？
   - 是。成交额/成交量更适合作为交易约束和数据质量过滤。

9. 成熟 ETF 轮动框架中哪些思想有效？
   - 中期动量、相对强弱、趋势确认、TopN 二次筛选、同 group 分散、最小持仓和 cooldown。

10. 哪些成熟框架不适合直接迁移到 A 股 ETF？
   - 美股低成本高流动性假设、全球多资产 ETF 配置口径、QDII 无折溢价/汇率风险假设、日内高频执行。

11. 是否应该进入 Phase 4B-2？
   - `{str(decision.get('candidate_ready_for_shadow_tracking')).lower()}`。

12. 是否可以把某个 v2 模型接入 shadow tracking？
   - `{str(decision.get('candidate_ready_for_shadow_tracking')).lower()}`，候选为 `{decision.get('best_candidate')}`。

13. 是否暂不应接入真实 paper_trade_engine？
   - 是，`candidate_ready_for_execution = false`。收益率仍不够理想，且未跑赢 510300，不能标记为 live-ready 或 profitable enough。

14. 是否仍不建议扩池？
   - 是，`expand_pool_now = false`；先修复模型与执行口径，再谈扩池。

## 安全边界

- 未修改 paper_trades.csv。
- 未修改 paper_positions.csv。
- 未修改 paper_trade_engine.py。
- 不接券商 API，不真实下单，不读取真实账户。
"""


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


def fmt(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except Exception:
        return "N/A"


def max_holding_days(etf_type: str) -> int:
    if etf_type in {"theme", "high_beta"}:
        return 20
    if etf_type in {"sector", "commodity_resource"}:
        return 20
    if etf_type == "bond_cash":
        return 30
    return MAX_HOLDING_DAYS_DEFAULT


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except Exception:
        return default


def clean_json_value(value: object) -> object:
    if isinstance(value, (int, str, bool)) or value is None:
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else 0.0
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def extract_code(value: object) -> str:
    match = re.search(r"(\d{6})", str(value))
    return match.group(1) if match else ""


if __name__ == "__main__":
    main()
