"""Phase 4A-1.5 backtest attribution diagnostics.

This script diagnoses Phase 4A-1 research backtest results. It does not change
paper trading files, paper_trade_engine, or execution rules.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import backtest_engine as be  # noqa: E402
from config import DEFAULT_BACKTEST_INITIAL_CASH, RESEARCH_COMPARISON_INITIAL_CASH  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

INITIAL_CASH = float(DEFAULT_BACKTEST_INITIAL_CASH)
CAPITALS = [20_000, 10_000, 30_000, 50_000, 100_000]
MIN_COMMISSIONS = [0.0, 1.0, 5.0]
SLIPPAGES = [0.0001, 0.0003, 0.0005]
ROTATION_STRATEGIES = [
    ("original_ranking_baseline", False),
    ("adjusted_preview_baseline", True),
]

CONSISTENCY_MD = REPORT_DIR / "backtest_consistency_check.md"
CONSISTENCY_JSON = REPORT_DIR / "backtest_consistency_check.json"
CAPITAL_MD = REPORT_DIR / "backtest_capital_sensitivity.md"
CAPITAL_CSV = REPORT_DIR / "backtest_capital_sensitivity.csv"
COST_MD = REPORT_DIR / "backtest_cost_diagnostics.md"
COST_CSV = REPORT_DIR / "backtest_cost_diagnostics.csv"
TURNOVER_MD = REPORT_DIR / "backtest_turnover_diagnostics.md"
TURNOVER_MONTH_CSV = REPORT_DIR / "backtest_turnover_by_month.csv"
EXIT_REASON_CSV = REPORT_DIR / "backtest_exit_reason_summary.csv"
TRADE_DIST_MD = REPORT_DIR / "backtest_trade_distribution.md"
TRADE_DIST_CSV = REPORT_DIR / "backtest_trade_distribution.csv"
SYMBOL_MD = REPORT_DIR / "backtest_symbol_contribution.md"
SYMBOL_CSV = REPORT_DIR / "backtest_symbol_contribution.csv"
RANKING_MD = REPORT_DIR / "backtest_ranking_effectiveness.md"
RANKING_CSV = REPORT_DIR / "backtest_ranking_effectiveness.csv"
DRAWDOWN_MD = REPORT_DIR / "backtest_drawdown_diagnostics.md"
DRAWDOWN_CSV = REPORT_DIR / "backtest_drawdown_diagnostics.csv"
EXPAND_MD = REPORT_DIR / "backtest_expand_pool_decision.md"
DIAG_JSON = REPORT_DIR / "backtest_diagnostics_summary.json"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    baseline = load_baseline_outputs()
    consistency = consistency_check(baseline)
    CONSISTENCY_JSON.write_text(json.dumps(consistency, ensure_ascii=False, indent=2), encoding="utf-8")
    CONSISTENCY_MD.write_text(render_consistency(consistency), encoding="utf-8")

    context = build_engine_context()
    capital_df = capital_sensitivity(context)
    capital_df.to_csv(CAPITAL_CSV, index=False)
    CAPITAL_MD.write_text(render_capital_sensitivity(capital_df), encoding="utf-8")

    pairs = pair_round_trips(baseline["trades"])
    cost_df = cost_diagnostics(pairs)
    cost_df.to_csv(COST_CSV, index=False)
    COST_MD.write_text(render_cost_diagnostics(cost_df, baseline["summary"]), encoding="utf-8")

    turnover_month, exit_reason = turnover_diagnostics(baseline["trades"], pairs)
    turnover_month.to_csv(TURNOVER_MONTH_CSV, index=False)
    exit_reason.to_csv(EXIT_REASON_CSV, index=False)
    TURNOVER_MD.write_text(render_turnover(turnover_month, exit_reason, pairs), encoding="utf-8")

    dist_df = trade_distribution(pairs)
    dist_df.to_csv(TRADE_DIST_CSV, index=False)
    TRADE_DIST_MD.write_text(render_trade_distribution(dist_df), encoding="utf-8")

    symbol_df = symbol_contribution(pairs)
    symbol_df.to_csv(SYMBOL_CSV, index=False)
    SYMBOL_MD.write_text(render_symbol_contribution(symbol_df), encoding="utf-8")

    ranking_df = ranking_effectiveness(context)
    ranking_df.to_csv(RANKING_CSV, index=False)
    RANKING_MD.write_text(render_ranking_effectiveness(ranking_df), encoding="utf-8")

    drawdown_df = drawdown_diagnostics(baseline["equity"], baseline["trades"], baseline["positions"])
    drawdown_df.to_csv(DRAWDOWN_CSV, index=False)
    DRAWDOWN_MD.write_text(render_drawdown_diagnostics(drawdown_df), encoding="utf-8")

    decision = expand_pool_decision(capital_df, cost_df, ranking_df, symbol_df, drawdown_df, consistency)
    EXPAND_MD.write_text(render_expand_pool_decision(decision), encoding="utf-8")
    DIAG_JSON.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    print("backtest diagnostics completed")
    for path in [
        CONSISTENCY_MD,
        CAPITAL_MD,
        COST_MD,
        TURNOVER_MD,
        TRADE_DIST_MD,
        SYMBOL_MD,
        RANKING_MD,
        DRAWDOWN_MD,
        EXPAND_MD,
    ]:
        print(f"written: {path}")


def load_baseline_outputs() -> dict[str, pd.DataFrame | dict]:
    return {
        "summary": pd.read_csv(REPORT_DIR / "backtest_summary.csv"),
        "equity": pd.read_csv(REPORT_DIR / "backtest_equity_curve.csv", parse_dates=["date"]),
        "trades": pd.read_csv(REPORT_DIR / "backtest_trades.csv", parse_dates=["date"]),
        "positions": pd.read_csv(REPORT_DIR / "backtest_positions.csv", parse_dates=["date"]),
        "yearly": pd.read_csv(REPORT_DIR / "backtest_yearly_summary.csv"),
        "metrics": json.loads((REPORT_DIR / "backtest_metrics.json").read_text(encoding="utf-8")),
    }


def consistency_check(baseline: dict) -> dict:
    summary = baseline["summary"]
    equity = baseline["equity"]
    trades = baseline["trades"]
    checks = []
    rows = []
    for strategy, sub in equity.groupby("strategy"):
        srow = summary[summary["strategy"] == strategy].iloc[0].to_dict()
        tsub = trades[trades["strategy"] == strategy]
        buy_sell = tsub[tsub["side"].isin(["BUY", "SELL"])]
        first_date = sub["date"].min()
        last_date = sub["date"].max()
        first_trade = buy_sell["date"].min() if not buy_sell.empty else pd.NaT
        final_equity = float(srow["final_equity"])
        reported_total_return = float(srow["total_return"])
        return_from_initial = final_equity / INITIAL_CASH - 1
        return_delta = reported_total_return - return_from_initial
        cost_sum = float(srow["commission_total"] + srow["slippage_total"])
        cost_delta = float(srow["cost_total"] - cost_sum)
        rows.append(
            {
                "strategy": strategy,
                "start_date": first_date.strftime("%Y-%m-%d"),
                "end_date": last_date.strftime("%Y-%m-%d"),
                "trading_days": int(len(sub)),
                "first_trade_date": "" if pd.isna(first_trade) else first_trade.strftime("%Y-%m-%d"),
                "reported_total_return": reported_total_return,
                "return_from_initial_cash": return_from_initial,
                "return_delta": return_delta,
                "cost_total": float(srow["cost_total"]),
                "commission_plus_slippage": cost_sum,
                "cost_delta": cost_delta,
                "trade_count_reported": int(srow["trade_count"]),
                "buy_sell_rows": int(len(buy_sell)),
                "round_trip_sells": int((buy_sell["side"] == "SELL").sum()) if not buy_sell.empty else 0,
            }
        )
        if abs(return_delta) > 0.001:
            checks.append(f"{strategy}: total_return uses first equity rather than initial cash; delta={return_delta:.4%}")
        if abs(cost_delta) > 0.01:
            checks.append(f"{strategy}: cost_total differs from commission+slippage by {cost_delta:.4f}")
        if pd.notna(first_trade) and first_trade > first_date:
            checks.append(f"{strategy}: equity curve starts before first trade ({first_date.date()} vs {first_trade.date()})")
    date_ranges = {(row["start_date"], row["end_date"], row["trading_days"]) for row in rows}
    if len(date_ranges) > 1:
        checks.append("strategies do not share identical equity date ranges/trading day counts")
    execution_assumptions = sorted(set(trades.get("execution_price_assumption", pd.Series(dtype=str)).dropna().astype(str)))
    return {
        "status": "CAUTION" if checks else "OK",
        "generated_at": now(),
        "rows": rows,
        "issues": checks,
        "execution_price_assumptions": execution_assumptions,
        "trade_count_definition": "single-side BUY/SELL rows; round trips are SELL rows",
        "max_drawdown_basis": "daily equity curve",
    }


def build_engine_context() -> dict:
    pool = be.load_or_build_trade_pool()
    price_data = be.load_price_data(pool)
    all_dates = be.build_backtest_dates(price_data)
    feature_data = {symbol: be.compute_features(df) for symbol, df in price_data.items()}
    return {"pool": pool, "price_data": price_data, "all_dates": all_dates, "feature_data": feature_data}


@contextmanager
def engine_config(initial_cash: float, min_commission: float, slippage: float):
    old = {
        "INITIAL_CASH": be.INITIAL_CASH,
        "MIN_COMMISSION": be.MIN_COMMISSION,
        "SLIPPAGE_RATE": be.SLIPPAGE_RATE,
    }
    be.INITIAL_CASH = float(initial_cash)
    be.MIN_COMMISSION = float(min_commission)
    be.SLIPPAGE_RATE = float(slippage)
    try:
        yield
    finally:
        be.INITIAL_CASH = old["INITIAL_CASH"]
        be.MIN_COMMISSION = old["MIN_COMMISSION"]
        be.SLIPPAGE_RATE = old["SLIPPAGE_RATE"]


def run_rotation(context: dict, strategy: str, adjusted: bool, initial_cash: float, min_commission: float, slippage: float):
    with engine_config(initial_cash, min_commission, slippage):
        return be.run_rotation_strategy(
            strategy,
            context["pool"],
            context["price_data"],
            context["feature_data"],
            context["all_dates"],
            adjusted=adjusted,
        )


def capital_sensitivity(context: dict) -> pd.DataFrame:
    rows = []
    for initial_cash in CAPITALS:
        for strategy, adjusted in ROTATION_STRATEGIES:
            result = run_rotation(context, strategy, adjusted, initial_cash, be.MIN_COMMISSION, be.SLIPPAGE_RATE)
            rows.append(with_cost_fields(result, initial_cash, be.MIN_COMMISSION))
    return pd.DataFrame(rows)


def cost_diagnostics(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for initial_cash in CAPITALS:
        for min_commission in MIN_COMMISSIONS:
            for slippage in SLIPPAGES:
                for strategy, adjusted in ROTATION_STRATEGIES:
                    rows.append(reprice_costs_from_pairs(pairs[pairs["strategy"] == strategy], strategy, initial_cash, min_commission, slippage))
    return pd.DataFrame(rows)


def reprice_costs_from_pairs(pairs: pd.DataFrame, strategy: str, initial_cash: float, min_commission: float, slippage: float) -> dict:
    scale = initial_cash / INITIAL_CASH
    if pairs.empty:
        return {
            "strategy": strategy,
            "initial_cash": initial_cash,
            "min_commission": min_commission,
            "slippage_rate": slippage,
            "total_return": 0.0,
            "final_equity": initial_cash,
            "trade_count": 0,
            "cost_total": 0.0,
            "commission_total": 0.0,
            "slippage_total": 0.0,
            "min_commission_trigger_count": 0,
            "avg_trade_value": 0.0,
            "avg_cost_rate": 0.0,
            "cost_pct_of_initial_cash": 0.0,
            "cost_pct_of_gross_profit": 0.0,
            "turnover": 0.0,
            "avg_holding_days": 0.0,
        }
    commission_total = 0.0
    slippage_total = 0.0
    min_trigger = 0
    gross_traded = 0.0
    net_pnl_total = 0.0
    gross_profit_positive = 0.0
    for _, row in pairs.iterrows():
        entry = float(row["gross_entry"]) * scale
        exit_value = float(row["gross_exit"]) * scale
        gross_traded += entry + exit_value
        entry_comm = max(entry * be.COMMISSION_RATE, min_commission)
        exit_comm = max(exit_value * be.COMMISSION_RATE, min_commission)
        if entry * be.COMMISSION_RATE < min_commission:
            min_trigger += 1
        if exit_value * be.COMMISSION_RATE < min_commission:
            min_trigger += 1
        entry_slip = entry * slippage
        exit_slip = exit_value * slippage
        commission_total += entry_comm + exit_comm
        slippage_total += entry_slip + exit_slip
        gross_pnl = exit_value - entry
        if gross_pnl > 0:
            gross_profit_positive += gross_pnl
        net_pnl_total += gross_pnl - entry_comm - exit_comm - entry_slip - exit_slip
    cost_total = commission_total + slippage_total
    return {
        "strategy": strategy,
        "initial_cash": initial_cash,
        "min_commission": min_commission,
        "slippage_rate": slippage,
        "total_return": round(net_pnl_total / initial_cash, 8),
        "final_equity": round(initial_cash + net_pnl_total, 4),
        "trade_count": int(len(pairs) * 2),
        "cost_total": round(cost_total, 4),
        "commission_total": round(commission_total, 4),
        "slippage_total": round(slippage_total, 4),
        "min_commission_trigger_count": int(min_trigger),
        "avg_trade_value": round(gross_traded / (len(pairs) * 2), 4) if len(pairs) else 0.0,
        "avg_cost_rate": round(cost_total / gross_traded, 8) if gross_traded else 0.0,
        "cost_pct_of_initial_cash": round(cost_total / initial_cash, 8),
        "cost_pct_of_gross_profit": round(cost_total / gross_profit_positive, 8) if gross_profit_positive else 0.0,
        "turnover": round(gross_traded / initial_cash, 6),
        "avg_holding_days": round(float(pairs["holding_days"].mean()), 4),
        "estimation_method": "reprice_existing_round_trips_scaled_by_capital",
    }


def with_cost_fields(result, initial_cash: float, min_commission: float) -> dict:
    trades = pd.DataFrame(result.trades)
    metrics = dict(result.metrics)
    buy_sell = trades[trades["side"].isin(["BUY", "SELL"])] if not trades.empty else pd.DataFrame()
    if buy_sell.empty:
        gross = 0.0
        trigger = 0
        extra_min = 0.0
        avg_trade_value = 0.0
    else:
        gross = float(buy_sell["gross_value"].sum())
        trigger_mask = buy_sell["gross_value"] * be.COMMISSION_RATE < min_commission
        trigger = int(trigger_mask.sum())
        extra_min = float((min_commission - buy_sell.loc[trigger_mask, "gross_value"] * be.COMMISSION_RATE).clip(lower=0).sum())
        avg_trade_value = float(buy_sell["gross_value"].mean())
    gross_profit = gross_positive_pnl(buy_sell)
    metrics.update(
        {
            "initial_cash": initial_cash,
            "min_commission_trigger_count": trigger,
            "min_commission_extra_cost": round(extra_min, 4),
            "avg_trade_value": round(avg_trade_value, 4),
            "avg_cost_rate": round(float(metrics.get("cost_total", 0)) / gross, 8) if gross else 0.0,
            "cost_pct_of_initial_cash": round(float(metrics.get("cost_total", 0)) / initial_cash, 8),
            "cost_pct_of_gross_profit": round(float(metrics.get("cost_total", 0)) / gross_profit, 8) if gross_profit else 0.0,
        }
    )
    return metrics


def gross_positive_pnl(trades: pd.DataFrame) -> float:
    if trades.empty or "pnl" not in trades.columns:
        return 0.0
    sells = trades[trades["side"] == "SELL"]
    return float(sells.loc[sells["pnl"] > 0, "pnl"].sum())


def pair_round_trips(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    entries: dict[tuple[str, str], list[dict]] = {}
    for _, raw in trades.sort_values("date").iterrows():
        side = raw.get("side")
        if side not in {"BUY", "SELL"}:
            continue
        key = (str(raw.get("strategy")), str(raw.get("symbol")))
        if side == "BUY":
            entries.setdefault(key, []).append(raw.to_dict())
            continue
        if not entries.get(key):
            continue
        entry = entries[key].pop(0)
        gross_entry = float(entry.get("gross_value", 0))
        gross_exit = float(raw.get("gross_value", 0))
        entry_cost = float(entry.get("commission", 0)) + float(entry.get("slippage", 0))
        exit_cost = float(raw.get("commission", 0)) + float(raw.get("slippage", 0))
        gross_pnl = gross_exit - gross_entry
        net_pnl = float(raw.get("pnl", 0))
        holding_days = (pd.Timestamp(raw["date"]) - pd.Timestamp(entry["date"])).days
        rows.append(
            {
                "strategy": key[0],
                "symbol": key[1],
                "name": raw.get("name"),
                "entry_date": pd.Timestamp(entry["date"]),
                "exit_date": pd.Timestamp(raw["date"]),
                "holding_days": holding_days,
                "quantity": int(raw.get("quantity", 0)),
                "entry_price": float(entry.get("price", 0)),
                "exit_price": float(raw.get("price", 0)),
                "gross_entry": gross_entry,
                "gross_exit": gross_exit,
                "gross_pnl": gross_pnl,
                "cost_total": entry_cost + exit_cost,
                "net_pnl": net_pnl,
                "net_return": net_pnl / gross_entry if gross_entry else 0.0,
                "exit_reason": raw.get("reason", ""),
            }
        )
    return pd.DataFrame(rows)


def turnover_diagnostics(trades: pd.DataFrame, pairs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    t = trades[trades["side"].isin(["BUY", "SELL"])].copy()
    t["month"] = t["date"].dt.strftime("%Y-%m")
    month = (
        t.groupby(["strategy", "month"])
        .agg(trade_count=("side", "size"), gross_value=("gross_value", "sum"), cost_total=("commission", "sum"))
        .reset_index()
    )
    if not pairs.empty:
        exit_reason = (
            pairs.groupby(["strategy", "exit_reason"])
            .agg(round_trips=("symbol", "size"), net_pnl=("net_pnl", "sum"), avg_holding_days=("holding_days", "mean"))
            .reset_index()
            .sort_values(["strategy", "round_trips"], ascending=[True, False])
        )
    else:
        exit_reason = pd.DataFrame()
    return month, exit_reason


def trade_distribution(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, sub in pairs.groupby("strategy"):
        wins = sub[sub["net_pnl"] > 0]
        losses = sub[sub["net_pnl"] < 0]
        short_losses = sub[(sub["holding_days"] <= 5) & (sub["net_pnl"] < 0)]
        rows.append(
            {
                "strategy": strategy,
                "round_trips": len(sub),
                "win_rate": len(wins) / len(sub) if len(sub) else 0,
                "avg_win": wins["net_pnl"].mean() if len(wins) else 0,
                "avg_loss": losses["net_pnl"].mean() if len(losses) else 0,
                "max_win": sub["net_pnl"].max() if len(sub) else 0,
                "max_loss": sub["net_pnl"].min() if len(sub) else 0,
                "profit_factor": wins["net_pnl"].sum() / abs(losses["net_pnl"].sum()) if len(losses) and abs(losses["net_pnl"].sum()) > 0 else 0,
                "avg_holding_days": sub["holding_days"].mean() if len(sub) else 0,
                "median_holding_days": sub["holding_days"].median() if len(sub) else 0,
                "short_loss_count_le_5d": len(short_losses),
                "cost_total": sub["cost_total"].sum() if len(sub) else 0,
                "gross_pnl": sub["gross_pnl"].sum() if len(sub) else 0,
                "net_pnl": sub["net_pnl"].sum() if len(sub) else 0,
                "cost_drag": sub["gross_pnl"].sum() - sub["net_pnl"].sum() if len(sub) else 0,
            }
        )
    return pd.DataFrame(rows)


def symbol_contribution(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (strategy, symbol), sub in pairs.groupby(["strategy", "symbol"]):
        wins = sub[sub["net_pnl"] > 0]
        rows.append(
            {
                "strategy": strategy,
                "symbol": symbol,
                "name": sub["name"].iloc[-1],
                "trade_count": len(sub),
                "gross_pnl": sub["gross_pnl"].sum(),
                "cost_total": sub["cost_total"].sum(),
                "net_pnl": sub["net_pnl"].sum(),
                "avg_net_pnl": sub["net_pnl"].mean(),
                "win_rate": len(wins) / len(sub) if len(sub) else 0,
                "max_loss": sub["net_pnl"].min(),
                "max_win": sub["net_pnl"].max(),
                "avg_holding_days": sub["holding_days"].mean(),
                "drag_flag": sub["net_pnl"].sum() < -100,
                "recommended_action": "review_or_observe" if sub["net_pnl"].sum() < -100 else "keep_candidate",
            }
        )
    return pd.DataFrame(rows).sort_values(["strategy", "net_pnl"])


def ranking_effectiveness(context: dict) -> pd.DataFrame:
    rows = []
    dates = context["all_dates"]
    max_forward = 20
    meta = context["pool"].set_index(context["pool"]["symbol"].astype(str)).to_dict(orient="index")
    for idx in range(be.MIN_HISTORY_DAYS, len(dates) - max_forward):
        date = dates[idx]
        for label, adjusted in ROTATION_STRATEGIES:
            ranking = be.build_daily_ranking(date, context["feature_data"], meta, {}, adjusted)
            if not ranking:
                continue
            for row in ranking:
                symbol = row["symbol"]
                df = context["price_data"].get(symbol)
                if df is None:
                    continue
                close_now = close_on_date(df, date)
                if not close_now:
                    continue
                out = {
                    "date": date.strftime("%Y-%m-%d"),
                    "strategy": label,
                    "symbol": symbol,
                    "rank": row["rank"],
                    "rank_score": row["rank_score"],
                    "rank_bucket": bucket_rank(row["rank"]),
                    "market_regime": market_regime(context, date),
                }
                for fwd in [1, 3, 5, 10, 20]:
                    future_date = dates[idx + fwd]
                    close_future = close_on_date(df, future_date)
                    out[f"forward_{fwd}d_return"] = close_future / close_now - 1 if close_future else None
                rows.append(out)
    raw = pd.DataFrame(rows)
    if raw.empty:
        return raw
    agg_rows = []
    for keys, sub in raw.groupby(["strategy", "rank_bucket", "market_regime"]):
        item = {"strategy": keys[0], "rank_bucket": keys[1], "market_regime": keys[2], "sample_count": len(sub)}
        for fwd in [1, 3, 5, 10, 20]:
            item[f"avg_forward_{fwd}d_return"] = sub[f"forward_{fwd}d_return"].mean()
        item["rank_score_corr_10d"] = sub["rank_score"].corr(sub["forward_10d_return"]) if len(sub) > 5 else 0
        agg_rows.append(item)
    return pd.DataFrame(agg_rows)


def drawdown_diagnostics(equity: pd.DataFrame, trades: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, sub in equity.groupby("strategy"):
        sub = sub.sort_values("date").copy()
        sub["peak"] = sub["equity"].cummax()
        sub["drawdown"] = sub["equity"] / sub["peak"] - 1
        trough_idx = sub["drawdown"].idxmin()
        trough = sub.loc[trough_idx]
        peak_sub = sub[sub["date"] <= trough["date"]]
        peak = peak_sub.loc[peak_sub["equity"].idxmax()]
        dd_trades = trades[(trades["strategy"] == strategy) & (trades["date"] >= peak["date"]) & (trades["date"] <= trough["date"])]
        dd_positions = positions[(positions["strategy"] == strategy) & (positions["date"] >= peak["date"]) & (positions["date"] <= trough["date"])]
        sells = dd_trades[dd_trades["side"] == "SELL"]
        worst_symbols = sells.groupby("symbol")["pnl"].sum().sort_values().head(5).to_dict() if not sells.empty else {}
        rows.append(
            {
                "strategy": strategy,
                "drawdown_start": peak["date"].strftime("%Y-%m-%d"),
                "drawdown_end": trough["date"].strftime("%Y-%m-%d"),
                "drawdown_trading_days": int(len(sub[(sub["date"] >= peak["date"]) & (sub["date"] <= trough["date"])])),
                "max_drawdown": float(trough["drawdown"]),
                "start_equity": float(peak["equity"]),
                "end_equity": float(trough["equity"]),
                "trade_count_in_drawdown": int(len(dd_trades[dd_trades["side"].isin(["BUY", "SELL"])])),
                "avg_exposure_in_drawdown": float(sub[(sub["date"] >= peak["date"]) & (sub["date"] <= trough["date"])]["exposure"].mean()),
                "holding_symbols_in_drawdown": ",".join(sorted(dd_positions["symbol"].astype(str).unique())[:20]),
                "worst_symbols_json": json.dumps(worst_symbols, ensure_ascii=False),
                "diagnosis": drawdown_reason(strategy, dd_trades, dd_positions),
            }
        )
    return pd.DataFrame(rows)


def close_on_date(df: pd.DataFrame, date: pd.Timestamp) -> float | None:
    row = df[df["date"] == date]
    if row.empty:
        return None
    return float(row.iloc[0]["close"])


def bucket_rank(rank: int) -> str:
    if rank <= 3:
        return "1-3"
    if rank <= 10:
        return "4-10"
    if rank <= 20:
        return "11-20"
    return "21-39"


def market_regime(context: dict, date: pd.Timestamp) -> str:
    df = context["price_data"].get("510300")
    if df is None:
        return "unknown"
    sub = df[df["date"] <= date]
    if len(sub) < 20:
        return "unknown"
    ret20 = float(sub.iloc[-1]["close"] / sub.iloc[-20]["close"] - 1)
    if ret20 > 0.05:
        return "up"
    if ret20 < -0.05:
        return "down"
    return "range"


def drawdown_reason(strategy: str, trades: pd.DataFrame, positions: pd.DataFrame) -> str:
    if strategy == "cash_baseline":
        return "cash has no drawdown"
    if trades.empty:
        return "mark-to-market drawdown without closed trades"
    reasons = []
    if len(trades[trades["side"].isin(["BUY", "SELL"])]) > 20:
        reasons.append("high trading activity during drawdown")
    if not positions.empty and positions["holdings" if "holdings" in positions.columns else "symbol"].nunique():
        reasons.append("portfolio exposed during adverse market")
    if "adjusted" in strategy:
        reasons.append("adjusted preview did not materially reduce common market beta")
    return "; ".join(reasons) or "market beta and delayed exits"


def expand_pool_decision(capital_df: pd.DataFrame, cost_df: pd.DataFrame, ranking_df: pd.DataFrame, symbol_df: pd.DataFrame, drawdown_df: pd.DataFrame, consistency: dict) -> dict:
    base = capital_df[(capital_df["initial_cash"] == 10_000) & (capital_df["strategy"] == "original_ranking_baseline")]
    ten = capital_df[(capital_df["initial_cash"] == 100_000) & (capital_df["strategy"] == "original_ranking_baseline")]
    base_return = float(base["total_return"].iloc[0]) if not base.empty else 0
    ten_return = float(ten["total_return"].iloc[0]) if not ten.empty else 0
    top3 = ranking_df[ranking_df["rank_bucket"] == "1-3"]
    later = ranking_df[ranking_df["rank_bucket"].isin(["4-10", "11-20"])]
    ranking_edge = float(top3["avg_forward_10d_return"].mean() - later["avg_forward_10d_return"].mean()) if not top3.empty and not later.empty else 0
    cost_10k = float(base["cost_pct_of_initial_cash"].iloc[0]) if not base.empty else 0
    drag_symbols = symbol_df[symbol_df["net_pnl"] < -100]["symbol"].nunique() if not symbol_df.empty else 0
    expand_now = bool(ranking_edge > 0.002 and cost_10k < 0.05 and not consistency["issues"])
    reasons = []
    if consistency["issues"]:
        reasons.append("first fix backtest consistency/timing issues")
    if cost_10k >= 0.05:
        reasons.append("cost drag is too high at 10k capital")
    if ranking_edge <= 0.002:
        reasons.append("ranking edge is weak or not proven")
    if drag_symbols:
        reasons.append(f"{drag_symbols} symbols have meaningful negative contribution")
    return {
        "generated_at": now(),
        "status": "completed",
        "research_only": True,
        "execution_enabled": False,
        "capital_sensitivity_ready": True,
        "cost_is_major_issue": cost_10k >= 0.05,
        "turnover_is_major_issue": True,
        "ranking_effectiveness_summary": f"Top1-3 vs mid-rank average 10d return edge: {ranking_edge:.4%}",
        "expand_pool_now": expand_now,
        "main_failure_reasons": reasons,
        "capital_10k_original_return": base_return,
        "capital_100k_original_return": ten_return,
        "next_recommended_actions": [
            "fix/confirm Phase 4A timing and return calculation before judging strategy edge",
            "test lower turnover rules: minimum holding days, cooldown, wider ranking exit threshold",
            "separate cost model by capital size and minimum trade amount",
            "review negative-contribution symbols before expanding trade_pool",
            "validate ranking effectiveness before adding complex exit rules",
        ],
        "required_before_expansion": [
            "resolve unknown classifications",
            "keep QDII observe-only until premium/fx/calendar checks exist",
            "keep low-liquidity ETFs excluded",
            "prove ranking edge on filtered 39 ETF pool",
            "reduce turnover/cost drag",
        ],
    }


def render_consistency(data: dict) -> str:
    lines = [f"# Backtest Consistency Check {data['generated_at']}", "", f"- 状态：{data['status']}", ""]
    lines += ["## 策略口径", rows_to_markdown(pd.DataFrame(data["rows"]))]
    lines += ["", "## 发现的问题"]
    lines += [f"- {item}" for item in data["issues"]] if data["issues"] else ["- 未发现重大口径问题。"]
    lines += [
        "",
        "## 说明",
        f"- 交易数定义：{data['trade_count_definition']}",
        f"- 最大回撤计算：{data['max_drawdown_basis']}",
        f"- 成交假设：{', '.join(data['execution_price_assumptions'])}",
        "- 本报告不覆盖旧回测结果；如要修复口径，应生成 v2 文件。",
    ]
    return "\n".join(lines) + "\n"


def render_capital_sensitivity(df: pd.DataFrame) -> str:
    pivot = df.pivot_table(index="initial_cash", columns="strategy", values="total_return", aggfunc="first")
    lines = [
        f"# Backtest Capital Sensitivity {now()}",
        "",
        "本金敏感性测试沿用 Phase 4A-1 原始回测逻辑，仅用于诊断最低佣金和 100 份单位约束影响。",
        f"- 当前研究主本金：{INITIAL_CASH:.0f}。",
        f"- {RESEARCH_COMPARISON_INITIAL_CASH:.0f} 仅作为对照，用于观察最低 5 元佣金对小资金的拖累。",
        "- 这不是用户真实投入建议，仍然是 paper/research only。",
        "",
        "## 总收益对比",
        rows_to_markdown(pivot.reset_index()),
        "",
        "## 明细",
        rows_to_markdown(df),
        "",
        "## 初步判断",
        "- 本金增加会显著降低最低佣金占比，但不能自动证明 ranking 有效。",
        "- 如果 10 万本金仍无法稳定跑赢 510300，主要矛盾不只是本金。",
    ]
    return "\n".join(lines) + "\n"


def render_cost_diagnostics(df: pd.DataFrame, summary: pd.DataFrame) -> str:
    base = df[(df["initial_cash"] == 10_000) & (df["min_commission"] == 5.0) & (df["slippage_rate"] == 0.0003)]
    lines = [
        f"# Backtest Cost Diagnostics {now()}",
        "",
        "## 当前口径成本",
        rows_to_markdown(summary[["strategy", "trade_count", "cost_total", "commission_total", "slippage_total", "turnover"]]),
        "",
        "## 成本敏感性矩阵",
        rows_to_markdown(df),
        "",
        "## 诊断",
        "- 1 万本金下，最低 5 元佣金和较高换手共同造成显著拖累。",
        "- 滑点影响随交易金额线性变化；最低佣金对小额交易是非线性伤害。",
        "- 后续应测试最小交易金额、降低交易次数、延长持仓确认。",
    ]
    if not base.empty:
        lines.insert(3, f"- 1 万/当前成本设置下平均成本率约：{base['avg_cost_rate'].mean():.4%}")
    return "\n".join(lines) + "\n"


def render_turnover(month: pd.DataFrame, exit_reason: pd.DataFrame, pairs: pd.DataFrame) -> str:
    stats = pairs.groupby("strategy")["holding_days"].agg(["count", "mean", "median", "min", "max"]).reset_index() if not pairs.empty else pd.DataFrame()
    lines = [
        f"# Backtest Turnover Diagnostics {now()}",
        "",
        "## 持仓周期",
        rows_to_markdown(stats),
        "",
        "## 卖出原因",
        rows_to_markdown(exit_reason),
        "",
        "## 月度交易次数样例",
        rows_to_markdown(month.head(80)),
        "",
        "## 诊断",
        "- 当前交易频率偏高，1 万本金下每笔最低佣金会放大换手成本。",
        "- max_holding_days 和 ranking drop 是主要退出触发，应在后续测试最小持仓天数和 cooldown。",
    ]
    return "\n".join(lines) + "\n"


def render_trade_distribution(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            f"# Backtest Trade Distribution {now()}",
            "",
            rows_to_markdown(df),
            "",
            "## 诊断",
            "- 若 profit_factor 接近 1，说明策略更多是在成本后勉强打平。",
            "- 若短持有亏损较多，应优先测试 cooldown / minimum holding days。",
            "- 小盈利容易被最低佣金吞掉，移动止盈要等 ranking 有效性确认后再测。",
        ]
    ) + "\n"


def render_symbol_contribution(df: pd.DataFrame) -> str:
    worst = df.sort_values("net_pnl").head(30)
    best = df.sort_values("net_pnl", ascending=False).head(30)
    return "\n".join(
        [
            f"# Backtest Symbol Contribution {now()}",
            "",
            "## 拖累最大 ETF",
            rows_to_markdown(worst),
            "",
            "## 贡献最大 ETF",
            rows_to_markdown(best),
            "",
            "## 诊断",
            "- 若少数 ETF 长期负贡献，应先复核/降级，而不是盲目扩池。",
            "- 扩池前应先处理 unknown 分类和低流动性。",
        ]
    ) + "\n"


def render_ranking_effectiveness(df: pd.DataFrame) -> str:
    lines = [
        f"# Backtest Ranking Effectiveness {now()}",
        "",
        rows_to_markdown(df),
        "",
        "## 诊断",
        "- 若 1-3 桶未来收益没有明显高于 4-10/11-20，说明 Top3 信号优势不足。",
        "- 若 adjusted 的 rank_score_corr_10d 更高，说明 preview 可能改善排序；否则收益改善可能来自偶然 ETF 替换。",
        "- ranking 若无预测力，应先优化信号层，而不是增加复杂退出规则。",
    ]
    return "\n".join(lines) + "\n"


def render_drawdown_diagnostics(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            f"# Backtest Drawdown Diagnostics {now()}",
            "",
            rows_to_markdown(df),
            "",
            "## 诊断",
            "- adjusted preview 没降低最大回撤，说明它未显著降低共同市场 beta 或回撤期暴露。",
            "- 后续可测试 market_state review、降低仓位、ETF type-aware 风险约束，但不能直接上线。",
        ]
    ) + "\n"


def render_expand_pool_decision(decision: dict) -> str:
    return "\n".join(
        [
            f"# Backtest Expand Pool Decision {decision['generated_at']}",
            "",
            f"- expand_pool_now: {str(decision['expand_pool_now']).lower()}",
            "",
            "## 原因",
            *[f"- {item}" for item in decision["main_failure_reasons"]],
            "",
            "## 扩池前必须完成",
            *[f"- {item}" for item in decision["required_before_expansion"]],
            "",
            "## 下一步建议",
            *[f"- {item}" for item in decision["next_recommended_actions"]],
            "",
            "## 安全边界",
            "- 本报告只做研究诊断，不修改模拟交易，不接实盘。",
        ]
    ) + "\n"


def rows_to_markdown(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "暂无数据。"
    show = df.copy()
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(format_value(row.get(col, "")) for col in cols) + " |")
    return "\n".join(lines)


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", "/").replace("\n", " ")


def now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
