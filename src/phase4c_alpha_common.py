"""Shared research utilities for Phase 4C alpha/regime studies.

Research-only. No broker APIs, no real orders, no paper trading file writes.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import ranking_model_v2_backtest as base  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"
MAIN_CASH = float(base.MAIN_INITIAL_CASH)
BENCHMARK_STRATEGY = "buy_and_hold_510300"
V2_STRATEGY = "top10_diversified_filter_v2"


def load_context() -> dict:
    pool = base.load_trade_pool()
    price_data = base.load_price_data(pool)
    pool = pool[pool["symbol"].astype(str).isin(price_data)].reset_index(drop=True)
    dates = base.build_common_dates(price_data)
    feature_data = {symbol: base.compute_features(df) for symbol, df in price_data.items()}
    return {
        "pool": pool,
        "price_data": price_data,
        "feature_data": feature_data,
        "dates": dates,
        "meta": base.build_meta(pool),
    }


def market_regime(date: pd.Timestamp, context: dict) -> str:
    features = context["feature_data"]
    bench = base.row_on_date(features.get("510300", pd.DataFrame()), date)
    growth = base.row_on_date(features.get("159915", pd.DataFrame()), date)
    gold = base.row_on_date(features.get("518880", pd.DataFrame()), date)
    if bench is None:
        return "neutral"
    b_ret20 = base.to_float(bench.get("ret_20"))
    b_ret60 = base.to_float(bench.get("ret_60"))
    b_vol = base.to_float(bench.get("volatility_20"))
    b_trend = bool(bench.get("close", 0) > bench.get("ma60", 10**9))
    g_ret20 = base.to_float(growth.get("ret_20")) if growth is not None else 0.0
    gold_ret20 = base.to_float(gold.get("ret_20")) if gold is not None else 0.0
    if (b_ret20 > 0.025 and b_ret60 > 0 and b_trend) or (g_ret20 - b_ret20 > 0.025 and b_ret20 > 0):
        return "risk_on"
    if b_ret20 < -0.025 or b_ret60 < -0.04 or (b_vol > 0.018 and b_ret20 < 0) or (gold_ret20 - b_ret20 > 0.04 and b_ret20 < 0.01):
        return "risk_off"
    return "neutral"


def custom_score(row: dict, strategy: str, regime: str, rank_memory: dict[str, list[int]] | None = None) -> float | None:
    raw = base.score_row(row, "top10_diversified_filter_v2", {})
    if raw is None:
        return None
    etf_type = str(row.get("etf_type", ""))
    group = str(row.get("group", ""))
    high_beta = etf_type in {"theme", "high_beta"} or "科技" in group or "新能源" in group
    defensive = etf_type in {"bond_cash", "commodity"} or "债" in group or "黄金" in group or "红利" in group
    cyclical = "周期" in group or "资源" in group or "煤炭" in str(row.get("name", ""))

    if strategy == "static_v2_baseline" or strategy == "single_score_v2_baseline":
        return raw
    if strategy == "risk_on_relaxed_filter_v2":
        if regime == "risk_on":
            return raw + 12 * row["p_rs_510300"] + 8 * row["p_ret_20"] + (6 if high_beta else 0)
        return raw
    if strategy == "risk_off_defensive_v2":
        if regime == "risk_off":
            return raw + (10 if defensive else 0) - (10 if high_beta else 0) + 8 * row["p_volatility_low"]
        return raw - (4 if high_beta else 0)
    if strategy == "regime_switching_v2":
        if regime == "risk_on":
            return raw + 10 * row["p_rs_510300"] + 6 * row["p_ret_20"] + (5 if high_beta else 0)
        if regime == "risk_off":
            return raw + (10 if defensive else 0) + 8 * row["p_volatility_low"] - (10 if high_beta else 0)
        return raw
    if strategy == "type_weighted_score_v2":
        if etf_type == "broad_index":
            return 34 * row["p_trend_slope_20"] + 26 * row["p_ret_60"] + 22 * row["p_ret_20"] + 18 * row["p_volatility_low"]
        if high_beta:
            return raw + 14 * row["p_risk_adjusted"] + 8 * row["p_rs_510300"] - (0 if regime == "risk_on" else 6)
        if cyclical:
            return raw + 10 * row["p_ret_60"] + 8 * row["p_trend_slope_20"]
        if defensive:
            return raw + 8 * row["p_volatility_low"] + (6 if regime == "risk_off" else -2)
        return raw + 8 * row["p_rs_group"]
    if strategy == "type_regime_combined_v2":
        typed = custom_score(row, "type_weighted_score_v2", regime, rank_memory)
        if typed is None:
            return None
        if regime == "risk_on":
            return typed + 8 * row["p_rs_510300"] + (5 if high_beta else 0)
        if regime == "risk_off":
            return typed + (8 if defensive else 0) - (8 if high_beta else 0)
        return typed
    if strategy == "relative_strength_plus_trend_v2":
        if not row.get("trend_confirm"):
            return None
        return 38 * row["p_rs_510300"] + 22 * row["p_rs_group"] + 22 * row["p_trend_slope_20"] + 18 * row["p_ret_20"]
    if strategy == "risk_adjusted_momentum_v2":
        return 45 * row["p_risk_adjusted"] + 25 * row["p_ret_20"] + 15 * row["p_volatility_low"] + 15 * row["p_trend_slope_20"]
    if strategy == "persistence_breakout_v2":
        persistence = _ranking_persistence_bonus(str(row.get("symbol")), rank_memory)
        breakout = 8 if row.get("strong_trend_confirm") and row.get("ma_distance_20", 0) > 0 else 0
        return raw + persistence + breakout
    if strategy == "alpha_blend_simple_v2":
        return 36 * row["p_rs_510300"] + 28 * row["p_risk_adjusted"] + 24 * row["p_trend_slope_20"] + 12 * row["p_liquidity"]
    return raw


def _ranking_persistence_bonus(symbol: str, rank_memory: dict[str, list[int]] | None) -> float:
    if not rank_memory or symbol not in rank_memory:
        return 0.0
    recent = [rank for rank in rank_memory[symbol][-3:] if rank <= 10]
    return min(len(recent) * 3.0, 9.0)


def run_research_strategy(strategy: str, context: dict, initial_cash: float = MAIN_CASH) -> base.StrategyResult:
    dates: list[pd.Timestamp] = context["dates"]
    price_data: dict[str, pd.DataFrame] = context["price_data"]
    cash = initial_cash
    positions: dict[str, base.Position] = {}
    bad_days: dict[str, int] = {}
    cooldown: dict[str, int] = {}
    rank_memory: dict[str, list[int]] = {}
    result = base.StrategyResult(strategy=strategy, initial_cash=initial_cash)
    result.equity_curve.append(base.equity_row(dates[base.MIN_HISTORY_DAYS], strategy, initial_cash, cash, positions, price_data, initial_cash))

    for idx in range(base.MIN_HISTORY_DAYS, len(dates) - 1):
        signal_date = dates[idx]
        exec_date = dates[idx + 1]
        regime = market_regime(signal_date, context)
        daily_rows = base.build_daily_rows(signal_date, context)
        ranking = rank_custom_rows(daily_rows, strategy, regime, rank_memory)
        for row in ranking[:20]:
            rank_memory.setdefault(str(row["symbol"]), []).append(int(row["rank"]))
            rank_memory[str(row["symbol"])] = rank_memory[str(row["symbol"])][-5:]
        rank_map = {str(row["symbol"]): row for row in ranking}

        for symbol in list(cooldown):
            cooldown[symbol] -= 1
            if cooldown[symbol] <= 0:
                cooldown.pop(symbol, None)

        for symbol in list(positions):
            pos = positions[symbol]
            row = rank_map.get(symbol)
            exit_rank = 24 if regime == "risk_off" else base.EXIT_RANK_BELOW
            is_bad = row is None or int(row.get("rank", 999)) > exit_rank
            bad_days[symbol] = bad_days.get(symbol, 0) + 1 if is_bad else 0
            holding_days = idx - pos.entry_index
            reason = ""
            max_days = base.max_holding_days(pos.etf_type)
            if regime == "risk_on" and strategy in {"risk_on_relaxed_filter_v2", "regime_switching_v2", "type_regime_combined_v2"}:
                max_days += 10
            if holding_days >= max_days:
                reason = f"max_holding_days_{max_days}"
            elif holding_days >= base.MIN_HOLDING_DAYS and bad_days.get(symbol, 0) >= base.CONFIRM_DAYS:
                reason = f"rank_below_{exit_rank}_confirmed_{base.CONFIRM_DAYS}d"
            if reason:
                proceeds = base.sell_position(result, pos, exec_date, idx + 1, price_data, reason)
                if proceeds is not None:
                    cash += proceeds
                    positions.pop(symbol, None)
                    bad_days.pop(symbol, None)
                    cooldown[symbol] = base.COOLDOWN_DAYS

        target_rows = select_custom_targets(strategy, ranking, positions, cooldown, regime)
        slots = base.MAX_HOLDINGS - len(positions)
        target_total = target_position_pct(strategy, regime)
        for row in target_rows:
            if slots <= 0:
                break
            symbol = str(row["symbol"])
            if symbol in positions:
                continue
            target_value = min(initial_cash * base.MAX_SINGLE_POSITION_PCT, initial_cash * target_total / base.MAX_HOLDINGS)
            cash, bought = base.buy_position(result, row, exec_date, idx + 1, price_data, cash, target_value)
            if bought is not None:
                positions[symbol] = bought
                slots -= 1

        eq, exposure = base.mark_to_market(cash, positions, signal_date, price_data)
        row = base.equity_row(signal_date, strategy, initial_cash, cash, positions, price_data, eq, exposure)
        row["market_regime"] = regime
        result.equity_curve.append(row)
        base.append_position_rows(result, signal_date, strategy, positions, price_data, idx)

    final_date = dates[-1]
    final_idx = len(dates) - 1
    for symbol in list(positions):
        proceeds = base.sell_position(result, positions[symbol], final_date, final_idx, price_data, "backtest_end_liquidation")
        if proceeds is not None:
            cash += proceeds
            positions.pop(symbol, None)
    result.equity_curve.append(base.equity_row(final_date, strategy, initial_cash, cash, positions, price_data, cash, 0.0))
    result.metrics = base.compute_metrics(result, dates)
    result.metrics["avg_exposure"] = result.metrics.get("exposure_avg", 0)
    result.yearly = base.compute_yearly(result)
    add_regime_metrics(result)
    return result


def rank_custom_rows(rows: list[dict], strategy: str, regime: str, rank_memory: dict[str, list[int]] | None = None) -> list[dict]:
    ranked = []
    for row in rows:
        score = custom_score(row, strategy, regime, rank_memory)
        if score is None:
            continue
        item = dict(row)
        item["rank_score"] = round(float(score), 6)
        item["strategy"] = strategy
        item["market_regime"] = regime
        ranked.append(item)
    ranked.sort(key=lambda item: item["rank_score"], reverse=True)
    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
    return ranked


def select_custom_targets(strategy: str, ranking: list[dict], positions: dict[str, base.Position], cooldown: dict[str, int], regime: str) -> list[dict]:
    selected: list[dict] = []
    held = set(positions)
    group_counts: dict[str, int] = {}
    high_beta_count = 0
    group_limit = 2 if (regime == "risk_on" and strategy in {"risk_on_relaxed_filter_v2", "regime_switching_v2", "type_regime_combined_v2"}) else 1
    high_beta_limit = 2 if (regime == "risk_on" and strategy in {"risk_on_relaxed_filter_v2", "regime_switching_v2", "type_regime_combined_v2"}) else 1
    for row in ranking[:12]:
        symbol = str(row["symbol"])
        group = str(row.get("group", ""))
        etf_type = str(row.get("etf_type", ""))
        high_beta = etf_type in {"theme", "high_beta"}
        if symbol in held or symbol in cooldown:
            continue
        if not row.get("trend_confirm") and not (regime == "risk_on" and strategy in {"risk_on_relaxed_filter_v2", "regime_switching_v2"}):
            continue
        if row.get("amount_ma20", 0) < 30_000_000:
            continue
        if group_counts.get(group, 0) >= group_limit:
            continue
        if high_beta and high_beta_count >= high_beta_limit:
            continue
        selected.append(row)
        group_counts[group] = group_counts.get(group, 0) + 1
        if high_beta:
            high_beta_count += 1
        if len(selected) >= base.MAX_HOLDINGS:
            break
    return selected


def target_position_pct(strategy: str, regime: str) -> float:
    if strategy in {"risk_off_defensive_v2", "regime_switching_v2", "type_regime_combined_v2"} and regime == "risk_off":
        return 0.40
    if strategy in {"risk_on_relaxed_filter_v2", "regime_switching_v2", "type_regime_combined_v2"} and regime == "risk_on":
        return 0.60
    return base.TARGET_TOTAL_POSITION_PCT


def add_regime_metrics(result: base.StrategyResult) -> None:
    df = pd.DataFrame(result.equity_curve)
    if df.empty or "market_regime" not in df.columns:
        result.metrics.update({"risk_on_return": 0.0, "neutral_return": 0.0, "risk_off_return": 0.0})
        return
    df = df.sort_values("date").copy()
    df["daily_return"] = pd.to_numeric(df["equity"], errors="coerce").pct_change(fill_method=None).fillna(0.0)
    for regime in ["risk_on", "neutral", "risk_off"]:
        sub = df[df["market_regime"] == regime]
        result.metrics[f"{regime}_return"] = float((1 + sub["daily_return"]).prod() - 1) if not sub.empty else 0.0


def result_frames(results: list[base.StrategyResult]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = pd.DataFrame([r.metrics for r in results])
    equity = pd.DataFrame([row for r in results for row in r.equity_curve])
    trades = pd.DataFrame([row for r in results for row in r.trades])
    yearly = pd.DataFrame([row for r in results for row in r.yearly])
    return summary, equity, trades, yearly


def benchmark_rows() -> pd.DataFrame:
    path = REPORT_DIR / "ranking_model_v2_summary.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_510300_benchmark() -> dict:
    summary = benchmark_rows()
    if summary.empty:
        return {}
    row = summary[(summary["strategy"] == BENCHMARK_STRATEGY) & (summary["initial_cash"] == MAIN_CASH)]
    if row.empty:
        row = summary[summary["strategy"] == BENCHMARK_STRATEGY]
    return row.iloc[0].to_dict() if not row.empty else {}


def write_json(path: Path, payload: dict) -> None:
    import json

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/A"


def metric_payload(row: pd.Series | dict) -> dict:
    data = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    keys = [
        "strategy",
        "initial_cash",
        "total_return",
        "annualized_return",
        "max_drawdown",
        "sharpe",
        "calmar",
        "win_rate",
        "profit_factor",
        "trade_count",
        "turnover",
        "avg_holding_days",
        "exposure_avg",
        "avg_exposure",
        "cost_total",
        "risk_on_return",
        "neutral_return",
        "risk_off_return",
    ]
    return {key: data.get(key) for key in keys if key in data}
