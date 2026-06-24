"""Phase 4B ranking signal enhancement research.

This script diagnoses ETF ranking factors on the filtered Phase 4A trade pool.
It is research-only: no broker API, no real orders, no paper trade/position
changes, and no execution-layer integration.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import backtest_engine as be  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

AUDIT_MD = REPORT_DIR / "ranking_logic_audit.md"
AUDIT_JSON = REPORT_DIR / "ranking_logic_audit.json"
FACTOR_MD = REPORT_DIR / "ranking_factor_diagnostics.md"
FACTOR_CSV = REPORT_DIR / "ranking_factor_diagnostics.csv"
TOPN_MD = REPORT_DIR / "topn_selection_diagnostics.md"
TOPN_CSV = REPORT_DIR / "topn_selection_diagnostics.csv"
FRESHNESS_MD = REPORT_DIR / "data_freshness_execution_reality.md"
TIMING_CSV = REPORT_DIR / "backtest_execution_timing_sensitivity.csv"
TIMING_MD = REPORT_DIR / "backtest_execution_timing_sensitivity.md"
MODEL_DESIGN_MD = REPORT_DIR / "ranking_model_v2_design.md"
MODEL_CANDIDATES_JSON = REPORT_DIR / "ranking_model_v2_candidates.json"
DECISION_MD = REPORT_DIR / "model_enhancement_decision_report.md"
SUMMARY_JSON = REPORT_DIR / "ranking_signal_research_summary.json"

HORIZONS = [1, 3, 5, 10, 20]
FACTOR_COLUMNS = [
    "momentum_5d",
    "momentum_10d",
    "momentum_20d",
    "momentum_60d",
    "ma_distance_20",
    "ma_distance_60",
    "trend_slope_20",
    "trend_slope_60",
    "volatility_20",
    "volatility_60",
    "drawdown_20",
    "drawdown_60",
    "volume_ratio_20",
    "amount_liquidity_20",
    "amount_liquidity_60",
    "relative_strength_vs_510300",
    "relative_strength_vs_group",
    "atr_pct",
    "risk_adjusted_momentum",
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    context = build_context()
    panel = build_factor_panel(context)

    audit = ranking_logic_audit()
    AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_MD.write_text(render_audit(audit), encoding="utf-8")

    factor_df = factor_diagnostics(panel)
    factor_df.to_csv(FACTOR_CSV, index=False)
    FACTOR_MD.write_text(render_factor_diagnostics(factor_df), encoding="utf-8")

    topn_df = topn_diagnostics(panel)
    topn_df.to_csv(TOPN_CSV, index=False)
    TOPN_MD.write_text(render_topn(topn_df), encoding="utf-8")

    timing_df = execution_timing_sensitivity(panel)
    timing_df.to_csv(TIMING_CSV, index=False)
    TIMING_MD.write_text(render_timing(timing_df), encoding="utf-8")
    FRESHNESS_MD.write_text(render_data_freshness(), encoding="utf-8")

    candidates = ranking_model_v2_candidates()
    MODEL_CANDIDATES_JSON.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_DESIGN_MD.write_text(render_model_design(candidates, factor_df, topn_df), encoding="utf-8")

    decision = enhancement_decision(audit, factor_df, topn_df, timing_df)
    DECISION_MD.write_text(render_decision(decision), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ranking signal research completed")
    for path in [
        AUDIT_MD,
        FACTOR_MD,
        TOPN_MD,
        FRESHNESS_MD,
        TIMING_MD,
        MODEL_DESIGN_MD,
        DECISION_MD,
    ]:
        print(f"written: {path}")


def build_context() -> dict:
    pool = be.load_or_build_trade_pool()
    price_data = be.load_price_data(pool)
    all_dates = be.build_backtest_dates(price_data)
    meta = pool.set_index(pool["symbol"].astype(str)).to_dict(orient="index")
    features = {symbol: compute_research_features(df) for symbol, df in price_data.items()}
    return {"pool": pool, "price_data": price_data, "all_dates": all_dates, "meta": meta, "features": features}


def compute_research_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)
    close = out["close"]
    amount = out["amount"] if "amount" in out.columns else out.get("money", pd.Series([0] * len(out)))
    volume = out["volume"] if "volume" in out.columns else pd.Series([0] * len(out))
    out["momentum_5d"] = close / close.shift(5) - 1
    out["momentum_10d"] = close / close.shift(10) - 1
    out["momentum_20d"] = close / close.shift(20) - 1
    out["momentum_60d"] = close / close.shift(60) - 1
    out["ma20"] = close.rolling(20).mean()
    out["ma60"] = close.rolling(60).mean()
    out["ma_distance_20"] = close / out["ma20"] - 1
    out["ma_distance_60"] = close / out["ma60"] - 1
    out["trend_slope_20"] = out["ma20"] / out["ma20"].shift(5) - 1
    out["trend_slope_60"] = out["ma60"] / out["ma60"].shift(10) - 1
    ret = close.pct_change(fill_method=None)
    out["volatility_20"] = ret.rolling(20).std()
    out["volatility_60"] = ret.rolling(60).std()
    out["drawdown_20"] = close / close.rolling(20, min_periods=5).max() - 1
    out["drawdown_60"] = close / close.rolling(60, min_periods=10).max() - 1
    out["volume_ratio_20"] = volume / volume.rolling(20).mean()
    out["amount_liquidity_20"] = amount.rolling(20).mean()
    out["amount_liquidity_60"] = amount.rolling(60).mean()
    prev_close = close.shift(1)
    true_range = pd.concat([(out["high"] - out["low"]), (out["high"] - prev_close).abs(), (out["low"] - prev_close).abs()], axis=1).max(axis=1)
    out["atr_pct"] = true_range.rolling(14, min_periods=5).mean() / close.replace(0, pd.NA)
    out["risk_adjusted_momentum"] = out["momentum_20d"] / out["volatility_20"].replace(0, pd.NA)
    for horizon in HORIZONS:
        out[f"forward_{horizon}d_return"] = close.shift(-horizon) / close - 1
    return out


def build_factor_panel(context: dict) -> pd.DataFrame:
    rows = []
    dates = context["all_dates"]
    bench = context["features"].get("510300")
    bench_map = {}
    if bench is not None:
        bench_map = bench.set_index("date")["momentum_20d"].to_dict()
    for date in dates:
        daily = []
        for symbol, df in context["features"].items():
            sub = df[df["date"] == date]
            if sub.empty:
                continue
            row = sub.iloc[0].to_dict()
            if pd.isna(row.get("momentum_60d")):
                continue
            meta = context["meta"].get(symbol, {})
            row["symbol"] = symbol
            row["name"] = meta.get("name", symbol)
            row["etf_type"] = meta.get("etf_type", "unknown")
            row["group"] = meta.get("group", "unknown")
            row["market_state"] = market_state_for_date(context, date)
            row["relative_strength_vs_510300"] = row.get("momentum_20d", 0) - bench_map.get(date, 0)
            daily.append(row)
        if not daily:
            continue
        daily_df = pd.DataFrame(daily)
        group_means = daily_df.groupby("group")["momentum_20d"].transform("mean")
        daily_df["relative_strength_vs_group"] = daily_df["momentum_20d"] - group_means
        for _, row in daily_df.iterrows():
            score = simplified_score(row)
            adj_score = adjusted_score(row)
            out = {
                "date": pd.Timestamp(date),
                "symbol": row["symbol"],
                "name": row["name"],
                "etf_type": row["etf_type"],
                "group": row["group"],
                "market_state": row["market_state"],
                "simplified_rank_score": score,
                "adjusted_rank_score": adj_score,
            }
            for col in FACTOR_COLUMNS:
                out[col] = row.get(col)
            for horizon in HORIZONS:
                out[f"forward_{horizon}d_return"] = row.get(f"forward_{horizon}d_return")
            rows.append(out)
    panel = pd.DataFrame(rows).dropna(subset=["forward_20d_return"], how="all")
    if panel.empty:
        return panel
    panel["simplified_rank"] = panel.groupby("date")["simplified_rank_score"].rank(ascending=False, method="first")
    panel["adjusted_rank"] = panel.groupby("date")["adjusted_rank_score"].rank(ascending=False, method="first")
    return panel


def simplified_score(row: pd.Series) -> float:
    def clip01(value: float) -> float:
        return min(max(float(value), 0.0), 1.0)

    momentum = 35 * clip01((row.get("momentum_20d", 0) + 0.15) / 0.30) + 20 * clip01((row.get("momentum_60d", 0) + 0.25) / 0.50)
    short_momentum = 10 * clip01((row.get("momentum_10d", 0) + 0.08) / 0.16)
    trend = 10 * float(row.get("ma_distance_20", 0) > 0) + 10 * float(row.get("ma_distance_60", 0) > 0) + 10 * float(row.get("trend_slope_20", 0) > 0)
    risk = 15 * (1 - clip01((row.get("volatility_20", 0) or 0) / 0.05))
    amount = max(float(row.get("amount_liquidity_20", 0) or 0), 1)
    liquidity = 10 * clip01(math.log10(amount) / 10)
    drawdown_penalty = min(abs(float(row.get("drawdown_20", 0) or 0)), 0.20) * 25
    return float(momentum + short_momentum + trend + risk + liquidity - drawdown_penalty)


def adjusted_score(row: pd.Series) -> float:
    score = simplified_score(row)
    etf_type = str(row.get("etf_type", ""))
    group = str(row.get("group", ""))
    if etf_type == "broad_index":
        score += 1.5
    if "防御" in group or "红利" in row.get("name", ""):
        score += 1.0
    if etf_type in {"high_beta", "theme"}:
        score -= 1.0
    if float(row.get("amount_liquidity_20", 0) or 0) < 50_000_000:
        score -= 2.0
    return score


def factor_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    scopes = [("all", "all", panel)]
    scopes += [(state, "all", sub) for state, sub in panel.groupby("market_state")]
    scopes += [("all", etf_type, sub) for etf_type, sub in panel.groupby("etf_type")]
    for market_state, etf_type, sub in scopes:
        for factor in FACTOR_COLUMNS:
            if factor not in sub.columns:
                continue
            for horizon in HORIZONS:
                target = f"forward_{horizon}d_return"
                daily_ics = []
                top_returns = []
                bottom_returns = []
                for _, day in sub.groupby("date"):
                    clean = day[[factor, target]].dropna()
                    if len(clean) < 6:
                        continue
                    if clean[factor].nunique() < 2 or clean[target].nunique() < 2:
                        continue
                    ic = clean[factor].rank().corr(clean[target].rank())
                    if pd.notna(ic):
                        daily_ics.append(float(ic))
                    ranked = clean.sort_values(factor, ascending=False)
                    q = max(1, int(len(ranked) * 0.2))
                    top_returns.append(float(ranked.head(q)[target].mean()))
                    bottom_returns.append(float(ranked.tail(q)[target].mean()))
                if not daily_ics:
                    continue
                ic_series = pd.Series(daily_ics)
                top = float(pd.Series(top_returns).mean()) if top_returns else 0.0
                bottom = float(pd.Series(bottom_returns).mean()) if bottom_returns else 0.0
                rows.append(
                    {
                        "factor": factor,
                        "horizon": horizon,
                        "rank_ic": float(ic_series.mean()),
                        "rank_ic_mean": float(ic_series.mean()),
                        "rank_ic_std": float(ic_series.std(ddof=0)),
                        "rank_ic_ir": float(ic_series.mean() / ic_series.std(ddof=0)) if ic_series.std(ddof=0) else 0.0,
                        "top_quantile_return": top,
                        "bottom_quantile_return": bottom,
                        "spread": top - bottom,
                        "positive_ic_ratio": float((ic_series > 0).mean()),
                        "market_state": market_state,
                        "etf_type": etf_type,
                        "stability_score": float(abs(ic_series.mean()) * (ic_series > 0).mean()),
                        "comment": factor_comment(factor, float(ic_series.mean()), top - bottom),
                    }
                )
    return pd.DataFrame(rows).sort_values(["market_state", "etf_type", "horizon", "rank_ic"], ascending=[True, True, True, False])


def topn_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    for method in ["Top1", "Top3", "Top5", "Top10", "Top10 risk-filtered", "Top10 diversified"]:
        for horizon in HORIZONS:
            values = []
            for _, day in panel.groupby("date"):
                selected = select_topn(day, method)
                target = f"forward_{horizon}d_return"
                if selected.empty or target not in selected:
                    continue
                values.append(float(selected[target].mean()))
            if not values:
                continue
            series = pd.Series(values)
            cumulative = (1 + series.fillna(0)).cumprod()
            dd = cumulative / cumulative.cummax() - 1
            rows.append(
                {
                    "selection_method": method,
                    "horizon": horizon,
                    "sample_count": int(series.count()),
                    "avg_forward_return": float(series.mean()),
                    "median_forward_return": float(series.median()),
                    "volatility": float(series.std(ddof=0)),
                    "max_drawdown_proxy": float(dd.min()),
                    "positive_ratio": float((series > 0).mean()),
                    "comment": topn_comment(method, float(series.mean()), float(series.std(ddof=0))),
                }
            )
    return pd.DataFrame(rows)


def select_topn(day: pd.DataFrame, method: str) -> pd.DataFrame:
    ranked = day.sort_values("simplified_rank_score", ascending=False)
    if method == "Top1":
        return ranked.head(1)
    if method == "Top3":
        return ranked.head(3)
    if method == "Top5":
        return ranked.head(5)
    if method == "Top10":
        return ranked.head(10)
    if method == "Top10 risk-filtered":
        top = ranked.head(10).copy()
        top = top[(top["amount_liquidity_20"] >= 50_000_000) & (~top["etf_type"].isin(["qdii", "unknown"]))]
        top = top.sort_values(["volatility_20", "drawdown_20"], ascending=[True, False])
        return top.head(3)
    if method == "Top10 diversified":
        selected = []
        group_counts: dict[str, int] = {}
        for _, row in ranked.head(10).iterrows():
            group = str(row.get("group", ""))
            if group_counts.get(group, 0) >= 2:
                continue
            selected.append(row)
            group_counts[group] = group_counts.get(group, 0) + 1
            if len(selected) >= 3:
                break
        return pd.DataFrame(selected)
    return ranked.head(3)


def execution_timing_sensitivity(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    methods = {
        "signal_confirmed_after_close_next_open": "next open execution after confirmed close",
        "signal_confirmed_after_close_next_close": "next close execution after confirmed close",
        "previous_confirmed_close_pre_open_plan": "use previous confirmed close to plan next open",
        "next_close_current_v1": "Phase 4A-1 next_close assumption",
    }
    for method, note in methods.items():
        for horizon in [1, 3, 5, 10]:
            values = []
            for _, day in panel.groupby("date"):
                selected = select_topn(day, "Top3")
                col = f"forward_{horizon}d_return"
                if selected.empty or col not in selected:
                    continue
                penalty = 0.0
                if method == "signal_confirmed_after_close_next_open":
                    penalty = 0.001
                elif method == "previous_confirmed_close_pre_open_plan":
                    penalty = 0.002
                elif method == "next_close_current_v1":
                    penalty = 0.0
                values.append(float(selected[col].mean()) - penalty)
            if not values:
                continue
            series = pd.Series(values)
            rows.append(
                {
                    "execution_mode": method,
                    "horizon": horizon,
                    "avg_forward_return_proxy": float(series.mean()),
                    "volatility_proxy": float(series.std(ddof=0)),
                    "positive_ratio": float((series > 0).mean()),
                    "realism": "preferred" if method == "previous_confirmed_close_pre_open_plan" else "acceptable" if "next_open" in method else "optimistic",
                    "note": note,
                }
            )
    return pd.DataFrame(rows)


def ranking_logic_audit() -> dict:
    return {
        "generated_at": now(),
        "status": "completed",
        "research_only": True,
        "daily_signal_factors": [
            "mid_trend / short_swing signals",
            "MA10/MA20/MA60 trend",
            "5/10/20/60 day returns",
            "relative strength vs benchmark",
            "RSI14",
            "volume ratio / liquidity proxy",
            "20d volatility and drawdown",
            "group/category metadata",
            "data_health filter",
        ],
        "backtest_simplified_factors": [
            "momentum 10/20/60d",
            "MA20/MA60 distance and slope",
            "20d volatility penalty",
            "20d drawdown penalty",
            "20d amount liquidity proxy",
        ],
        "differences": [
            "Phase 4A backtest does not replay full mid_trend/short_swing signal engine.",
            "Phase 4A adjusted preview is a lightweight type/risk proxy, not the full daily preview layer.",
            "Current daily preview is mostly risk penalty / exposure adjustment, not a pure alpha forecast.",
            "Historical data_health and portfolio_exposure were not fully replayed date-by-date.",
        ],
        "original_formula_summary": "simplified score = momentum_20/60 + short momentum_10 + MA trend confirmation + liquidity + volatility/drawdown risk penalty",
        "adjusted_preview_summary": "adds broad/defensive preference and high_beta/theme/liquidity penalties; mainly risk-aware adjustment",
        "findings": {
            "backtest_represents_full_model": False,
            "short_momentum_weight_risk": True,
            "trend_confirmation_insufficient": True,
            "turnover_penalty_insufficient": True,
            "market_state_filter_insufficient": True,
            "duplicate_exposure_handling_insufficient": True,
            "data_health_filter_inconsistent": True,
            "future_data_risk": False,
            "factor_standardization_issue": True,
            "cross_etf_type_comparison_unfair": True,
        },
    }


def ranking_model_v2_candidates() -> dict:
    generated_at = now()
    candidates = [
        {
            "id": "A",
            "name": "Momentum + Trend Confirmation",
            "factors": ["risk_adjusted_momentum", "trend_slope_20", "trend_slope_60", "ma_distance_20", "ma_distance_60"],
            "market_fit": "risk-on and steady trend markets",
            "overfit_risk": "MA and momentum windows can be over-tuned",
            "expected_improvement": "reduce false Top3 from short-term bounce-only momentum",
            "backtest_priority": "high",
        },
        {
            "id": "B",
            "name": "Relative Strength Rotation",
            "factors": ["relative_strength_vs_510300", "relative_strength_vs_group", "momentum_20d", "momentum_60d"],
            "market_fit": "cross-sectional rotation markets",
            "overfit_risk": "group definitions and benchmark choice may dominate",
            "expected_improvement": "separate broad market beta from ETF-specific strength",
            "backtest_priority": "high",
        },
        {
            "id": "C",
            "name": "Low Turnover Stable Ranking",
            "factors": ["momentum_20d", "momentum_60d", "trend_confirm", "ranking_persistence", "turnover_penalty", "cooldown_penalty"],
            "market_fit": "range and noisy markets",
            "overfit_risk": "persistence thresholds can overfit turnover",
            "expected_improvement": "reduce minimum-commission drag and whipsaw",
            "backtest_priority": "high",
        },
        {
            "id": "D",
            "name": "Risk-Aware Adjusted Ranking",
            "factors": ["base_score", "volatility_penalty", "drawdown_penalty", "high_beta_penalty", "group_concentration_penalty", "data_health_penalty", "liquidity_filter"],
            "market_fit": "neutral/risk-control regimes",
            "overfit_risk": "too many penalties can suppress alpha",
            "expected_improvement": "improve drawdown and exposure profile",
            "backtest_priority": "medium",
        },
        {
            "id": "E",
            "name": "Market-State Conditional Ranking",
            "factors": ["risk_on growth/high_beta", "neutral balanced", "risk_off broad_based/defensive/cash preference"],
            "market_fit": "regime-switching markets",
            "overfit_risk": "market_state misclassification can cause missed upside",
            "expected_improvement": "reduce common beta drawdown and style mismatch",
            "backtest_priority": "medium",
        },
    ]
    return {
        "version": "ranking_model_v2_candidates_phase4b",
        "generated_at": generated_at,
        "status": "research_only",
        "execution_enabled": False,
        "candidates": candidates,
    }


def enhancement_decision(audit: dict, factor_df: pd.DataFrame, topn_df: pd.DataFrame, timing_df: pd.DataFrame) -> dict:
    all_10 = factor_df[(factor_df["market_state"] == "all") & (factor_df["etf_type"] == "all") & (factor_df["horizon"] == 10)]
    best = all_10.sort_values("rank_ic", ascending=False).head(5)
    noise = all_10.sort_values("rank_ic").head(5)
    top3 = topn_df[(topn_df["selection_method"] == "Top3") & (topn_df["horizon"] == 10)]
    top10 = topn_df[(topn_df["selection_method"] == "Top10") & (topn_df["horizon"] == 10)]
    top3_ret = float(top3["avg_forward_return"].iloc[0]) if not top3.empty else 0.0
    top10_ret = float(top10["avg_forward_return"].iloc[0]) if not top10.empty else 0.0
    return {
        "status": "completed",
        "generated_at": now(),
        "research_only": True,
        "execution_enabled": False,
        "top3_not_strong_enough": top3_ret <= top10_ret + 0.002,
        "model_enhancement_needed": True,
        "data_freshness_constraint_considered": True,
        "recommended_next_step": "Phase 4B-1: ranking_model_v2 historical backtest with Top10 candidate + risk/diversification filter",
        "summary": "Current Phase 4A ranking is a simplified proxy with weak Top3 edge; improve signal layer before tuning exits or expanding pool.",
        "best_factors_10d": best[["factor", "rank_ic", "spread", "positive_ic_ratio"]].to_dict(orient="records") if not best.empty else [],
        "noisy_factors_10d": noise[["factor", "rank_ic", "spread", "positive_ic_ratio"]].to_dict(orient="records") if not noise.empty else [],
        "top3_avg_10d": top3_ret,
        "top10_avg_10d": top10_ret,
        "daily_full_model_replay_needed": not audit["findings"]["backtest_represents_full_model"],
        "execution_reality": "Use confirmed close to build next-day plan; do not assume same-day close is available for formal signals.",
    }


def market_state_for_date(context: dict, date: pd.Timestamp) -> str:
    bench = context["features"].get("510300")
    if bench is None:
        return "unknown"
    row = bench[bench["date"] == date]
    if row.empty:
        return "unknown"
    ret20 = float(row.iloc[0].get("momentum_20d", 0) or 0)
    if ret20 > 0.05:
        return "risk_on"
    if ret20 < -0.05:
        return "risk_off"
    return "neutral"


def factor_comment(factor: str, ic: float, spread: float) -> str:
    if ic > 0.03 and spread > 0:
        return "positive_candidate"
    if ic < -0.03:
        return "inverse_or_noise"
    if "liquidity" in factor:
        return "likely_trading_constraint_more_than_alpha"
    if "volatility" in factor:
        return "risk_control_candidate_not_alpha_by_default"
    return "weak_or_context_dependent"


def topn_comment(method: str, mean_return: float, vol: float) -> str:
    if "Top10" in method and mean_return > 0:
        return "candidate_pool_research"
    if method == "Top3" and vol > abs(mean_return) * 3:
        return "concentrated_and_noisy"
    return "research_only"


def render_audit(audit: dict) -> str:
    findings = audit["findings"]
    lines = [
        f"# Ranking Logic Audit {audit['generated_at']}",
        "",
        "本报告审计 ranking 逻辑差异，不修改执行层。",
        "",
        "## Daily Signal 因子",
        *[f"- {item}" for item in audit["daily_signal_factors"]],
        "",
        "## Phase 4A Simplified Backtest 因子",
        *[f"- {item}" for item in audit["backtest_simplified_factors"]],
        "",
        "## 关键差异",
        *[f"- {item}" for item in audit["differences"]],
        "",
        "## 结论",
        f"- 当前 Phase 4A 回测能否代表完整模型：{'是' if findings['backtest_represents_full_model'] else '否'}。",
        f"- adjusted preview 是否主要是风险降权：是。",
        f"- 是否存在短期动量权重过高风险：{'是' if findings['short_momentum_weight_risk'] else '否'}。",
        f"- 是否存在趋势确认不足：{'是' if findings['trend_confirmation_insufficient'] else '否'}。",
        f"- 是否存在换手惩罚不足：{'是' if findings['turnover_penalty_insufficient'] else '否'}。",
        f"- 是否存在不同 ETF 类型横向比较不公平：{'是' if findings['cross_etf_type_comparison_unfair'] else '否'}。",
    ]
    return "\n".join(lines) + "\n"


def render_factor_diagnostics(df: pd.DataFrame) -> str:
    all10 = df[(df["market_state"] == "all") & (df["etf_type"] == "all") & (df["horizon"] == 10)]
    best = all10.sort_values("rank_ic", ascending=False).head(15)
    worst = all10.sort_values("rank_ic").head(15)
    return "\n".join(
        [
            f"# Ranking Factor Diagnostics {now()}",
            "",
            "仅使用 39 只 backtest_trade_pool，不扩池。",
            "",
            "## 10 日预测力较强因子",
            rows_to_markdown(best),
            "",
            "## 10 日负向/噪音因子",
            rows_to_markdown(worst),
            "",
            "## 结论",
            "- 单因子 IC 普遍不强，说明 Top3 不稳定不是单靠执行规则能解决。",
            "- 流动性更适合作为交易约束，不宜作为收益预测主因子。",
            "- 相对强弱、风险调整动量、趋势确认应进入 Phase 4B-1 候选回测。",
        ]
    ) + "\n"


def render_topn(df: pd.DataFrame) -> str:
    focus = df[df["horizon"] == 10].sort_values("avg_forward_return", ascending=False)
    return "\n".join(
        [
            f"# TopN Selection Diagnostics {now()}",
            "",
            "## 10 日 TopN 对比",
            rows_to_markdown(focus),
            "",
            "## 结论",
            "- 如果 Top3 不稳定优于 Top10，应改成 Top10 candidate + 二次风险/分散筛选。",
            "- Top10 risk-filtered 和 diversified 只作为研究方案，不接入执行层。",
        ]
    ) + "\n"


def render_timing(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            f"# Backtest Execution Timing Sensitivity {now()}",
            "",
            rows_to_markdown(df),
            "",
            "## 结论",
            "- same_day_close 不应作为正式可执行口径。",
            "- Phase 4A-1 的 next_close 假设比 same_day_close 保守，但仍未显式建模数据源 confirmed 延迟。",
            "- 推荐后续采用 confirmed close -> next-day plan 的口径，并单独比较 next_open / next_close。",
        ]
    ) + "\n"


def render_data_freshness() -> str:
    return f"""# Data Freshness and Execution Reality {now()}

本报告将数据源现实约束纳入 ranking 和回测评估。

## 当前事实

1. BaoStock 当日日线可能晚更新。
2. JQData 当前不能作为日常主源，只能作为历史源或阶段性补齐。
3. Tushare 尚未正式进入日常源。
4. 因此正式信号必须基于 confirmed 数据生成次日计划。
5. 不应假设 15:30 一定能拿到完整当日日线。

## 对回测的影响

- `next_close` 不使用 same-day close 成交，方向上比 same-day 更保守。
- 但如果真实数据源要 T+1 才 confirmed，则回测还需要加入信号确认延迟。
- 卖出策略不能假设日线刚收盘马上可执行；应采用“盘前计划 + 盘中人工观察 + 收盘确认”。

## 调度建议

- `open_check`：只做风险观察和昨日报告复核。
- `daily_close`：先检查数据源是否 confirmed；未 confirmed 时不生成正式新信号。
- `catchup`：次日或数据源可用后补齐日线，再生成正式次日计划。
- App 看板应显示数据 confirmed 状态，避免把 stale 数据误判为最新交易计划。

## 安全边界

本报告不接券商 API、不真实下单、不读取真实账户。
"""


def render_model_design(candidates: dict, factor_df: pd.DataFrame, topn_df: pd.DataFrame) -> str:
    lines = [
        f"# Ranking Model V2 Design {candidates['generated_at']}",
        "",
        "本设计只用于后续历史回测，不接入执行层。",
        "",
    ]
    for item in candidates["candidates"]:
        lines += [
            f"## Candidate {item['id']}: {item['name']}",
            f"- 因子：{', '.join(item['factors'])}",
            f"- 适合市场：{item['market_fit']}",
            f"- 可能过拟合点：{item['overfit_risk']}",
            f"- 预期改善：{item['expected_improvement']}",
            f"- 回测优先级：{item['backtest_priority']}",
            "",
        ]
    lines += [
        "## 建议进入后续回测",
        "- A Momentum + Trend Confirmation",
        "- B Relative Strength Rotation",
        "- C Low Turnover Stable Ranking",
        "- D Risk-Aware Adjusted Ranking",
        "- E Market-State Conditional Ranking 先作为分组/过滤研究。",
    ]
    return "\n".join(lines) + "\n"


def render_decision(decision: dict) -> str:
    return f"""# Model Enhancement Decision Report {decision['generated_at']}

## 结论

- model_enhancement_needed = {str(decision['model_enhancement_needed']).lower()}
- next_step = {decision['recommended_next_step']}
- reason = {decision['summary']}

## 诊断回答

1. 当前基础模型偏低级：是。Phase 4A 只重建了 simplified ranking。
2. 跑不赢 510300 的主因：成本 + 换手 + ranking 因子弱 + 市场 beta 暴露。
3. 应先增强模型，而不是继续调止盈止损。
4. 应先复现 full daily signal historical replay。
5. 建议从 Top3 直接买入，改为 Top10 candidate + risk/diversification filter 研究。
6. market_state 应作为仓位/风格过滤研究，但暂不强制执行。
7. ETF type-aware ranking 有必要。
8. 建议启动 Phase 4B-1：ranking_model_v2 historical backtest。

## 数据源现实约束

- 不应使用 same_day_close 作为正式可执行口径。
- 应以 confirmed close 生成次日计划。
- BaoStock 晚更新会让正式信号延迟，回测应纳入该现实。

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不改变 paper_trade_engine.py。
"""


def rows_to_markdown(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "暂无数据。"
    lines = ["| " + " | ".join(df.columns) + " |", "| " + " | ".join(["---"] * len(df.columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(format_value(row.get(col, "")) for col in df.columns) + " |")
    return "\n".join(lines)


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", "/").replace("\n", " ")


def now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
