"""Market regime source audit and point-in-time historical replay.

Research-only. This module audits existing market regime logic and replays it
over history without modifying market_regime, BUY ranking, paper trades,
paper positions, adjusted preview, or execution code.
"""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import phase4c_alpha_common as common
import ranking_model_v2_backtest as base
from config import DATA_DIR, PROJECT_ROOT, REPORT_DIR


REPLAY_CSV = DATA_DIR / "market_regime_replay.csv"
REPLAY_MD = REPORT_DIR / "market_regime_replay.md"
REPLAY_JSON = REPORT_DIR / "market_regime_replay.json"
SOURCE_AUDIT_MD = REPORT_DIR / "market_regime_source_audit.md"
SOURCE_AUDIT_JSON = REPORT_DIR / "market_regime_source_audit.json"
DISTRIBUTION_MD = REPORT_DIR / "market_regime_distribution.md"
DISTRIBUTION_JSON = REPORT_DIR / "market_regime_distribution.json"
STABILITY_MD = REPORT_DIR / "market_regime_stability.md"
STABILITY_JSON = REPORT_DIR / "market_regime_stability.json"
STYLE_CSV = REPORT_DIR / "regime_style_forward_return.csv"
STYLE_MD = REPORT_DIR / "regime_style_forward_return.md"
STYLE_JSON = REPORT_DIR / "regime_style_forward_return.json"
STRUCTURAL_CSV = REPORT_DIR / "regime_structural_risk_forward_return.csv"
STRUCTURAL_MD = REPORT_DIR / "regime_structural_risk_forward_return.md"
STRUCTURAL_JSON = REPORT_DIR / "regime_structural_risk_forward_return.json"
REALIZED_CSV = REPORT_DIR / "regime_realized_risk_forward_return.csv"
REALIZED_MD = REPORT_DIR / "regime_realized_risk_forward_return.md"
REALIZED_JSON = REPORT_DIR / "regime_realized_risk_forward_return.json"
REPRESENTATIVE_MD = REPORT_DIR / "representative_etf_regime_behavior.md"
BREADTH_MD = REPORT_DIR / "market_breadth_regime_analysis.md"
BREADTH_JSON = REPORT_DIR / "market_breadth_regime_analysis.json"
DECISION_MD = REPORT_DIR / "market_regime_audit_decision.md"
DECISION_JSON = REPORT_DIR / "market_regime_audit_decision.json"
PHASE_MD = REPORT_DIR / "regime_layer_phase2_market_audit.md"
PHASE_JSON = REPORT_DIR / "regime_layer_phase2_market_audit.json"

PROFILE_CSV = REPORT_DIR / "etf_risk_profile.csv"
HORIZONS = [1, 3, 5, 10, 20]
FOCUS_SYMBOLS = ["512800", "515000", "512880", "512010", "588000", "159915", "510300", "510500", "510180"]
NORMALIZED_MAP = {"risk_on": "OFFENSIVE", "neutral": "NEUTRAL", "risk_off": "DEFENSIVE"}
REALIZED_WEIGHTS = {
    "volatility_60d": 0.25,
    "beta_60d": 0.20,
    "max_drawdown_120d_abs": 0.20,
    "downside_volatility_60d": 0.15,
    "down_capture_60d": 0.10,
    "concentration_style_penalty": 0.10,
}


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    context = common.load_context()
    profile = _load_profile()
    source_audit = build_source_audit()
    replay = build_replay(context, profile)
    replay_df = pd.DataFrame(replay["rows"])
    replay_df.to_csv(REPLAY_CSV, index=False)
    REPLAY_JSON.write_text(_json_dumps(replay), encoding="utf-8")
    REPLAY_MD.write_text(render_replay_report(replay), encoding="utf-8")

    distribution = build_distribution(replay_df)
    DISTRIBUTION_JSON.write_text(_json_dumps(distribution), encoding="utf-8")
    DISTRIBUTION_MD.write_text(render_distribution_report(distribution), encoding="utf-8")

    stability = build_stability(replay_df)
    STABILITY_JSON.write_text(_json_dumps(stability), encoding="utf-8")
    STABILITY_MD.write_text(render_stability_report(stability), encoding="utf-8")

    forward_rows = build_forward_rows(context, profile, replay_df)
    style = aggregate_forward(forward_rows, ["normalized_regime", "style_profile"])
    structural = aggregate_forward(forward_rows, ["normalized_regime", "structural_risk_profile"])
    realized = aggregate_forward(forward_rows, ["normalized_regime", "realized_risk_profile_pit"])
    style_df = pd.DataFrame(style["rows"])
    structural_df = pd.DataFrame(structural["rows"])
    realized_df = pd.DataFrame(realized["rows"])
    style_df.to_csv(STYLE_CSV, index=False)
    structural_df.to_csv(STRUCTURAL_CSV, index=False)
    realized_df.to_csv(REALIZED_CSV, index=False)
    STYLE_JSON.write_text(_json_dumps(style), encoding="utf-8")
    STRUCTURAL_JSON.write_text(_json_dumps(structural), encoding="utf-8")
    REALIZED_JSON.write_text(_json_dumps(realized), encoding="utf-8")
    STYLE_MD.write_text(render_forward_report("Style x Regime Forward Return", style, ["normalized_regime", "style_profile"]), encoding="utf-8")
    STRUCTURAL_MD.write_text(render_forward_report("Structural Risk x Regime Forward Return", structural, ["normalized_regime", "structural_risk_profile"]), encoding="utf-8")
    REALIZED_MD.write_text(render_forward_report("Point-in-time Realized Risk x Regime Forward Return", realized, ["normalized_regime", "realized_risk_profile_pit"]), encoding="utf-8")

    representative = build_representative_report_rows(forward_rows, profile)
    REPRESENTATIVE_MD.write_text(render_representative_report(representative), encoding="utf-8")

    breadth = build_breadth_analysis(replay_df)
    BREADTH_JSON.write_text(_json_dumps(breadth), encoding="utf-8")
    BREADTH_MD.write_text(render_breadth_report(breadth), encoding="utf-8")

    decision = build_decision(distribution, stability, style, structural, realized, breadth, source_audit)
    DECISION_JSON.write_text(_json_dumps(decision), encoding="utf-8")
    DECISION_MD.write_text(render_decision_report(decision), encoding="utf-8")

    phase = build_phase_report_payload(source_audit, replay, distribution, stability, style, structural, realized, breadth, representative, decision)
    PHASE_JSON.write_text(_json_dumps(phase), encoding="utf-8")
    PHASE_MD.write_text(render_phase_report(phase), encoding="utf-8")

    SOURCE_AUDIT_JSON.write_text(_json_dumps(source_audit), encoding="utf-8")
    SOURCE_AUDIT_MD.write_text(render_source_audit(source_audit), encoding="utf-8")

    print(f"market_regime_replay rows: {len(replay_df)}")
    print(f"replay range: {replay.get('replay_start_date')} to {replay.get('replay_end_date')}")
    print(f"written: {REPLAY_MD}")
    print(f"written: {STYLE_MD}")
    print(f"written: {STRUCTURAL_MD}")
    print(f"written: {DECISION_MD}")


def build_source_audit() -> dict[str, Any]:
    market_state_source = _source_function_summary(PROJECT_ROOT / "src" / "market_state.py", "build_market_rows")
    phase4c_source = _source_function_summary(PROJECT_ROOT / "src" / "phase4c_alpha_common.py", "market_regime")
    readers = _grep_project("market_regime")
    return {
        "generated_at": _now(),
        "primary_market_regime_source_file": "src/phase4c_alpha_common.py",
        "primary_market_regime_function": "market_regime(date, context)",
        "primary_market_regime_states": ["risk_on", "neutral", "risk_off"],
        "normalized_mapping": NORMALIZED_MAP,
        "market_state_source_file": "src/market_state.py",
        "market_state_function": "build_market_rows / _summary_row / _state_and_range",
        "market_state_states": ["market_strong", "market_neutral", "market_weak", "risk_off"],
        "phase4c_logic": phase4c_source,
        "market_state_logic": market_state_source,
        "input_features": [
            "510300 ret_20 ret_60 volatility_20 close_vs_ma60",
            "159915 ret_20 minus 510300 ret_20",
            "518880 ret_20 minus 510300 ret_20",
        ],
        "thresholds": [
            "risk_on if 510300 ret20 > 2.5%, ret60 > 0, close > ma60",
            "risk_on if 159915 ret20 - 510300 ret20 > 2.5% and 510300 ret20 > 0",
            "risk_off if 510300 ret20 < -2.5%",
            "risk_off if 510300 ret60 < -4%",
            "risk_off if 510300 vol20 > 1.8% and ret20 < 0",
            "risk_off if 518880 ret20 - 510300 ret20 > 4% and 510300 ret20 < 1%",
        ],
        "future_data_risk": "No direct future data in phase4c_alpha_common.market_regime; it uses row_on_date(df, date), which selects <= date.",
        "single_index_dependency": "High. 510300 is the main anchor; 159915 and 518880 are auxiliary.",
        "uses_etf_pool_breadth": False,
        "uses_buy_watch_sell_count": False,
        "uses_high_beta_growth_strength": "Growth only through 159915 relative strength; no ETF pool high_beta breadth.",
        "uses_risk_pressure": "Gold relative strength and 510300 vol/drawdown proxy only.",
        "logic_complexity": "simple rule-based proxy",
        "research_only": True,
        "modules_reading_market_regime": readers[:80],
        "paper_trade_engine_impact": "No direct paper_trade_engine dependency found in this audit; Phase 4C/shadow research reads market_regime.",
        "execution_allowed": False,
    }


def build_replay(context: dict, profile: pd.DataFrame) -> dict[str, Any]:
    dates = context["dates"]
    start_index = base.MIN_HISTORY_DAYS
    replay_dates = dates[start_index:]
    rows = []
    for date in replay_dates:
        daily_rows = base.build_daily_rows(date, context)
        regime = common.market_regime(date, context)
        normalized = NORMALIZED_MAP.get(regime, "UNKNOWN")
        rows.append(_replay_row(date, regime, normalized, daily_rows, context))
    return {
        "generated_at": _now(),
        "replay_start_date": replay_dates[0].strftime("%Y-%m-%d") if replay_dates else "",
        "replay_end_date": replay_dates[-1].strftime("%Y-%m-%d") if replay_dates else "",
        "replay_trading_days": len(replay_dates),
        "raw_market_regime_values": sorted({row["raw_market_regime"] for row in rows}),
        "normalized_mapping": NORMALIZED_MAP,
        "rows": rows,
        "point_in_time_realized_profile_available": True,
        "point_in_time_realized_profile_note": "realized risk profile is recalculated per T date from <=T data; forward returns are labels only.",
        "research_only": True,
        "execution_allowed": False,
    }


def _replay_row(date: pd.Timestamp, regime: str, normalized: str, daily_rows: list[dict], context: dict) -> dict[str, Any]:
    pool_size = len(daily_rows)
    buy_rows = [r for r in daily_rows if _is_buy_like(r)]
    sell_rows = [r for r in daily_rows if _is_sell_like(r)]
    watch_count = max(pool_size - len(buy_rows) - len(sell_rows), 0)
    strong_rows = [r for r in daily_rows if bool(r.get("strong_trend_confirm")) and _float(r.get("relative_strength_vs_510300")) > 0]
    risky_rows = [r for r in daily_rows if _float(r.get("drawdown_60")) < -0.08 or _float(r.get("volatility_20")) > 0.025]
    strength = _strength_buckets(daily_rows)
    bench_returns = _benchmark_forward_returns(date, context)
    market_score = None
    reason = _regime_reason(date, context)
    return {
        "date": date.strftime("%Y-%m-%d"),
        "raw_market_regime": regime,
        "market_regime": regime,
        "normalized_regime": normalized,
        "regime_score": market_score,
        "regime_reason": reason,
        "pool_size": pool_size,
        "buy_count": len(buy_rows),
        "watch_count": watch_count,
        "sell_count": len(sell_rows),
        "risk_count": len(risky_rows),
        "buy_breadth": len(buy_rows) / pool_size if pool_size else 0.0,
        "sell_breadth": len(sell_rows) / pool_size if pool_size else 0.0,
        "strong_resonance_count": len(strong_rows),
        "strong_resonance_breadth": len(strong_rows) / pool_size if pool_size else 0.0,
        "broad_base_strength": strength.get("broad_base_strength"),
        "growth_strength": strength.get("growth_strength"),
        "high_beta_strength": strength.get("high_beta_strength"),
        "defensive_strength": strength.get("defensive_strength"),
        "risk_pressure": (len(sell_rows) + len(risky_rows)) / (2 * pool_size) if pool_size else 0.0,
        **bench_returns,
        "research_only": True,
        "execution_allowed": False,
    }


def build_distribution(df: pd.DataFrame) -> dict[str, Any]:
    rows = df.to_dict(orient="records") if not df.empty else []
    total = len(rows)
    counts = df["normalized_regime"].value_counts().to_dict() if not df.empty else {}
    distribution = {key: {"day_count": int(counts.get(key, 0)), "percentage": (counts.get(key, 0) / total if total else 0.0)} for key in ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]}
    monthly = []
    if not df.empty:
        temp = df.copy()
        temp["month"] = pd.to_datetime(temp["date"]).dt.strftime("%Y-%m")
        for month, sub in temp.groupby("month"):
            item = {"month": month, "trading_days": len(sub)}
            for regime in ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]:
                c = int((sub["normalized_regime"] == regime).sum())
                item[f"{regime}_days"] = c
                item[f"{regime}_pct"] = c / len(sub) if len(sub) else 0.0
            monthly.append(item)
    max_pct = max((v["percentage"] for v in distribution.values()), default=0.0)
    return {
        "generated_at": _now(),
        "total_days": total,
        "distribution": distribution,
        "monthly_distribution": monthly,
        "dominant_regime": max(distribution, key=lambda k: distribution[k]["day_count"]) if distribution else "",
        "dominant_regime_percentage": max_pct,
        "extreme_imbalance": max_pct >= 0.80,
        "has_two_states_with_samples": sum(1 for v in distribution.values() if v["day_count"] >= 20) >= 2,
        "has_discrimination": max_pct < 0.80 and sum(1 for v in distribution.values() if v["day_count"] > 0) >= 2,
        "research_only": True,
        "execution_allowed": False,
    }


def build_stability(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"generated_at": _now(), "runs": [], "research_only": True, "execution_allowed": False}
    regimes = df[["date", "normalized_regime"]].to_dict(orient="records")
    runs = []
    current = regimes[0]["normalized_regime"]
    start = regimes[0]["date"]
    duration = 0
    for item in regimes:
        if item["normalized_regime"] == current:
            duration += 1
            end = item["date"]
            continue
        runs.append({"regime": current, "start_date": start, "end_date": end, "duration": duration})
        current = item["normalized_regime"]
        start = item["date"]
        end = item["date"]
        duration = 1
    runs.append({"regime": current, "start_date": start, "end_date": end, "duration": duration})
    durations = [r["duration"] for r in runs]
    switch_count = max(len(runs) - 1, 0)
    one_day = sum(1 for r in runs if r["duration"] == 1)
    three_day = sum(1 for r in runs if r["duration"] <= 3)
    five_day = sum(1 for r in runs if r["duration"] <= 5)
    whipsaw = _whipsaw_count(runs, 3)
    by_regime = {}
    for regime in ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]:
        ds = [r["duration"] for r in runs if r["regime"] == regime]
        by_regime[regime] = {
            "run_count": len(ds),
            "average_duration": _mean(ds),
            "median_duration": _median(ds),
            "max_duration": max(ds) if ds else 0,
        }
    return {
        "generated_at": _now(),
        "regime_switch_count": switch_count,
        "average_regime_duration": _mean(durations),
        "median_regime_duration": _median(durations),
        "max_regime_duration": max(durations) if durations else 0,
        "one_day_reversal_count": one_day,
        "three_day_reversal_count": three_day,
        "five_day_reversal_count": five_day,
        "short_regime_whipsaw_count": whipsaw,
        "by_regime": by_regime,
        "runs": runs,
        "frequent_switching": switch_count / max(len(df), 1) > 0.20 or whipsaw > 10,
        "needs_future_hysteresis_research": switch_count / max(len(df), 1) > 0.12 or whipsaw > 5,
        "research_only": True,
        "execution_allowed": False,
    }


def build_forward_rows(context: dict, profile: pd.DataFrame, replay_df: pd.DataFrame) -> list[dict[str, Any]]:
    if profile.empty or replay_df.empty:
        return []
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    replay_map = replay_df.set_index("date").to_dict(orient="index")
    pit_cache = {date: _point_in_time_realized_profiles(pd.Timestamp(date), context, profile_map) for date in replay_df["date"].astype(str).tolist()}
    rows = []
    for date_text, replay in replay_map.items():
        date = pd.Timestamp(date_text)
        bench_returns = _benchmark_forward_returns(date, context)
        bench_by_h = {h: bench_returns.get(f"benchmark_return_{h}d") for h in HORIZONS}
        for symbol, df in context["price_data"].items():
            profile_row = profile_map.get(symbol, {})
            if not profile_row:
                continue
            for h in HORIZONS:
                fwd = _forward_return(symbol, date, h, context)
                if fwd is None:
                    continue
                bench = bench_by_h.get(h)
                rows.append({
                    "date": date_text,
                    "symbol": symbol,
                    "name": profile_row.get("name", symbol),
                    "normalized_regime": replay.get("normalized_regime"),
                    "raw_market_regime": replay.get("raw_market_regime"),
                    "style_profile": profile_row.get("style_profile", "UNKNOWN"),
                    "structural_risk_profile": profile_row.get("structural_risk_profile", "UNKNOWN"),
                    "realized_risk_profile_pit": pit_cache.get(date_text, {}).get(symbol, "INSUFFICIENT_DATA"),
                    "forward_horizon": h,
                    "forward_return": fwd,
                    "benchmark_forward_return": bench,
                    "benchmark_excess_return": fwd - bench if bench is not None else None,
                    "profile_mode": "style/structural_static_latest; realized_point_in_time",
                    "research_only": True,
                    "execution_allowed": False,
                })
    return rows


def aggregate_forward(rows: list[dict[str, Any]], group_cols: list[str]) -> dict[str, Any]:
    if not rows:
        return {"generated_at": _now(), "rows": [], "research_only": True, "execution_allowed": False}
    df = pd.DataFrame(rows)
    out = []
    for keys, sub in df.groupby(group_cols + ["forward_horizon"], dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        item = dict(zip(group_cols + ["forward_horizon"], keys))
        returns = pd.to_numeric(sub["forward_return"], errors="coerce").dropna()
        excess = pd.to_numeric(sub["benchmark_excess_return"], errors="coerce").dropna()
        item.update({
            "sample_count": int(len(returns)),
            "mean_forward_return": _mean(returns.tolist()),
            "median_forward_return": _median(returns.tolist()),
            "positive_rate": float((returns > 0).mean()) if len(returns) else None,
            "benchmark_excess_mean": _mean(excess.tolist()),
            "benchmark_excess_median": _median(excess.tolist()),
            "sample_status": "insufficient_sample" if len(returns) < 30 else "ok",
            "research_only": True,
            "execution_allowed": False,
        })
        out.append(item)
    return {
        "generated_at": _now(),
        "group_columns": group_cols,
        "rows": sorted(out, key=lambda r: tuple(str(r.get(c, "")) for c in group_cols) + (int(r.get("forward_horizon", 0)),)),
        "research_only": True,
        "execution_allowed": False,
    }


def build_breadth_analysis(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"generated_at": _now(), "rows": [], "research_only": True, "execution_allowed": False}
    metrics = ["buy_breadth", "sell_breadth", "strong_resonance_breadth", "risk_pressure"]
    rows = []
    for regime, sub in df.groupby("normalized_regime"):
        row = {"normalized_regime": regime, "sample_count": len(sub)}
        for metric in metrics:
            row[f"{metric}_mean"] = _mean(pd.to_numeric(sub[metric], errors="coerce").dropna().tolist())
            row[f"{metric}_median"] = _median(pd.to_numeric(sub[metric], errors="coerce").dropna().tolist())
        rows.append(row)
    off = next((r for r in rows if r["normalized_regime"] == "OFFENSIVE"), {})
    defensive = next((r for r in rows if r["normalized_regime"] == "DEFENSIVE"), {})
    buy_gap = _float(off.get("buy_breadth_mean")) - _float(defensive.get("buy_breadth_mean"))
    sell_gap = _float(defensive.get("sell_breadth_mean")) - _float(off.get("sell_breadth_mean"))
    local_hotspot_risk = buy_gap < 0.03 and _float(off.get("strong_resonance_breadth_mean")) < 0.20
    return {
        "generated_at": _now(),
        "rows": rows,
        "offensive_buy_breadth_minus_defensive": buy_gap,
        "defensive_sell_breadth_minus_offensive": sell_gap,
        "offensive_buy_breadth_higher": buy_gap > 0.03,
        "defensive_sell_breadth_higher": sell_gap > 0.03,
        "local_hotspot_misread_risk": bool(local_hotspot_risk),
        "strong_resonance_predictive_value": "needs forward-return confirmation; breadth is descriptive in this phase",
        "research_only": True,
        "execution_allowed": False,
    }


def build_representative_report_rows(forward_rows: list[dict[str, Any]], profile: pd.DataFrame) -> list[dict[str, Any]]:
    if not forward_rows or profile.empty:
        return []
    df = pd.DataFrame(forward_rows)
    meta = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    rows = []
    for symbol in FOCUS_SYMBOLS:
        sub = df[df["symbol"].astype(str) == symbol]
        item = {
            "symbol": symbol,
            "name": meta.get(symbol, {}).get("name", symbol),
            "style_profile": meta.get(symbol, {}).get("style_profile", ""),
            "structural_risk_profile": meta.get(symbol, {}).get("structural_risk_profile", ""),
        }
        for regime in ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]:
            for h in [5, 10, 20]:
                part = sub[(sub["normalized_regime"] == regime) & (sub["forward_horizon"] == h)]
                item[f"{regime}_{h}d_sample"] = len(part)
                item[f"{regime}_{h}d_mean"] = _mean(pd.to_numeric(part["forward_return"], errors="coerce").dropna().tolist())
                item[f"{regime}_{h}d_excess"] = _mean(pd.to_numeric(part["benchmark_excess_return"], errors="coerce").dropna().tolist())
        rows.append(item)
    return rows


def build_decision(distribution: dict, stability: dict, style: dict, structural: dict, realized: dict, breadth: dict, source_audit: dict) -> dict[str, Any]:
    style_supported = _fit_supported(style, "style_profile")
    structural_supported = _fit_supported(structural, "structural_risk_profile")
    stable = not bool(stability.get("frequent_switching"))
    informative = bool(distribution.get("has_discrimination")) and bool(breadth.get("offensive_buy_breadth_higher") or breadth.get("defensive_sell_breadth_higher"))
    ready_phase = (
        bool(distribution.get("has_two_states_with_samples"))
        and bool(distribution.get("has_discrimination"))
        and (style_supported or structural_supported)
        and source_audit.get("future_data_risk", "").lower().startswith("no")
    )
    return {
        "generated_at": _now(),
        "existing_regime_is_informative": informative,
        "existing_regime_is_stable": stable,
        "existing_regime_has_whipsaw_problem": bool(stability.get("needs_future_hysteresis_research")),
        "style_regime_fit_supported": style_supported,
        "structural_risk_regime_fit_supported": structural_supported,
        "realized_risk_analysis_mode": "point_in_time_recomputed",
        "ready_for_regime_fit_phase": bool(ready_phase),
        "ready_for_preview": False,
        "ready_for_execution": False,
        "decision_reason": _decision_reason(informative, stable, style_supported, structural_supported, ready_phase),
        "research_only": True,
        "execution_allowed": False,
    }


def build_phase_report_payload(source_audit: dict, replay: dict, distribution: dict, stability: dict, style: dict, structural: dict, realized: dict, breadth: dict, representative: list[dict], decision: dict) -> dict[str, Any]:
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 2",
        "market_regime_source": {
            "file": source_audit.get("primary_market_regime_source_file"),
            "function": source_audit.get("primary_market_regime_function"),
            "states": source_audit.get("primary_market_regime_states"),
            "logic": source_audit.get("thresholds"),
        },
        "replay": {k: replay.get(k) for k in ["replay_start_date", "replay_end_date", "replay_trading_days", "raw_market_regime_values", "normalized_mapping"]},
        "distribution": distribution,
        "stability": {k: stability.get(k) for k in ["regime_switch_count", "average_regime_duration", "median_regime_duration", "max_regime_duration", "short_regime_whipsaw_count", "needs_future_hysteresis_research"]},
        "style_summary": _compact_fit_summary(style, "style_profile"),
        "structural_summary": _compact_fit_summary(structural, "structural_risk_profile"),
        "realized_summary": _compact_fit_summary(realized, "realized_risk_profile_pit"),
        "realized_risk_analysis_limit": "recomputed point-in-time profile from <=T data; still a research proxy and forward returns are labels only.",
        "breadth": breadth,
        "representative_etfs": representative,
        "decision": decision,
        "research_only": True,
        "ready_for_execution": False,
        "safety": _safety_payload(),
    }


def _point_in_time_realized_profiles(date: pd.Timestamp, context: dict, profile_map: dict[str, dict]) -> dict[str, str]:
    bench_df = context["price_data"].get("510300", pd.DataFrame())
    bench_returns = _returns_until(bench_df, date)
    metric_rows = []
    for symbol, df in context["price_data"].items():
        prices = df[df["date"] <= date].copy()
        if len(prices) < 80:
            continue
        returns = _returns_until(df, date)
        meta = profile_map.get(symbol, {})
        row = {
            "symbol": symbol,
            "volatility_60d": _annualized_vol(returns, 60),
            "beta_60d": _beta(returns, bench_returns, 60),
            "max_drawdown_120d_abs": abs(_max_drawdown(prices, 120)),
            "downside_volatility_60d": _downside_vol(returns, 60),
            "down_capture_60d": _down_capture(returns, bench_returns, 60),
            "concentration_style_penalty": _concentration_penalty(meta),
            "is_bond": str(meta.get("style_profile")) == "BOND",
        }
        metric_rows.append(row)
    if not metric_rows:
        return {}
    df = pd.DataFrame(metric_rows)
    for metric in REALIZED_WEIGHTS:
        df[f"{metric}_pct_rank"] = pd.to_numeric(df[metric], errors="coerce").rank(pct=True, na_option="keep")
    profiles = {}
    for _, row in df.iterrows():
        score = 0.0
        weight = 0.0
        for metric, w in REALIZED_WEIGHTS.items():
            v = row.get(f"{metric}_pct_rank")
            if pd.isna(v):
                continue
            score += float(v) * w
            weight += w
        if weight <= 0:
            profiles[str(row["symbol"])] = "INSUFFICIENT_DATA"
            continue
        value = score / weight * 100
        pct = pd.to_numeric(df[[f"{m}_pct_rank" for m in REALIZED_WEIGHTS]].mean(axis=1), errors="coerce")
        # Use score percentile for the final five-bucket label.
        profiles[str(row["symbol"])] = "__PENDING__"
        row["_score"] = value
    score_series = []
    symbols = []
    for _, row in df.iterrows():
        score = 0.0
        weight = 0.0
        for metric, w in REALIZED_WEIGHTS.items():
            v = row.get(f"{metric}_pct_rank")
            if pd.isna(v):
                continue
            score += float(v) * w
            weight += w
        symbols.append(str(row["symbol"]))
        score_series.append(score / weight * 100 if weight else np.nan)
    ranks = pd.Series(score_series).rank(pct=True, na_option="keep").tolist()
    out = {}
    for symbol, score, pct in zip(symbols, score_series, ranks):
        meta = profile_map.get(symbol, {})
        if pd.isna(score) or pd.isna(pct):
            out[symbol] = "INSUFFICIENT_DATA"
        elif str(meta.get("style_profile")) == "BOND":
            out[symbol] = "DEFENSIVE" if pct <= 0.30 else "CORE"
        elif pct <= 0.20:
            out[symbol] = "DEFENSIVE"
        elif pct <= 0.40:
            out[symbol] = "CORE"
        elif pct <= 0.60:
            out[symbol] = "BALANCED"
        elif pct <= 0.80:
            out[symbol] = "OFFENSIVE"
        else:
            out[symbol] = "HIGH_BETA"
    return out


def _strength_buckets(rows: list[dict]) -> dict[str, float]:
    buckets = {
        "broad_base_strength": [],
        "growth_strength": [],
        "high_beta_strength": [],
        "defensive_strength": [],
    }
    for row in rows:
        group = str(row.get("group", ""))
        etf_type = str(row.get("etf_type", ""))
        value = _float(row.get("ret_20"))
        if etf_type == "broad_index" or "宽基" in group:
            buckets["broad_base_strength"].append(value)
        if etf_type == "theme" or "科技" in group or "新能源" in group:
            buckets["growth_strength"].append(value)
        if etf_type in {"theme", "high_beta"} or "证券" in str(row.get("name", "")):
            buckets["high_beta_strength"].append(value)
        if etf_type in {"bond_cash", "commodity"} or any(key in group for key in ["防御", "债券", "消费医药"]):
            buckets["defensive_strength"].append(value)
    return {key: _mean(vals) for key, vals in buckets.items()}


def _is_buy_like(row: dict) -> bool:
    return bool(row.get("trend_confirm")) and _float(row.get("ret_20")) > 0 and _float(row.get("relative_strength_vs_510300")) > -0.02


def _is_sell_like(row: dict) -> bool:
    return _float(row.get("ret_20")) < -0.02 or _float(row.get("drawdown_60")) < -0.08 or (not bool(row.get("trend_confirm")) and _float(row.get("ret_60")) < 0)


def _regime_reason(date: pd.Timestamp, context: dict) -> str:
    features = context["feature_data"]
    bench = base.row_on_date(features.get("510300", pd.DataFrame()), date)
    growth = base.row_on_date(features.get("159915", pd.DataFrame()), date)
    gold = base.row_on_date(features.get("518880", pd.DataFrame()), date)
    if bench is None:
        return "510300 unavailable; neutral fallback"
    b_ret20 = base.to_float(bench.get("ret_20"))
    b_ret60 = base.to_float(bench.get("ret_60"))
    b_vol = base.to_float(bench.get("volatility_20"))
    b_trend = bool(bench.get("close", 0) > bench.get("ma60", 10**9))
    g_ret20 = base.to_float(growth.get("ret_20")) if growth is not None else 0.0
    gold_ret20 = base.to_float(gold.get("ret_20")) if gold is not None else 0.0
    return f"510300 ret20={b_ret20:.4f}, ret60={b_ret60:.4f}, vol20={b_vol:.4f}, above_ma60={b_trend}; 159915_rel={g_ret20-b_ret20:.4f}; 518880_rel={gold_ret20-b_ret20:.4f}"


def _benchmark_forward_returns(date: pd.Timestamp, context: dict) -> dict[str, float | None]:
    return {f"benchmark_return_{h}d": _forward_return("510300", date, h, context) for h in HORIZONS}


def _forward_return(symbol: str, date: pd.Timestamp, horizon: int, context: dict) -> float | None:
    df = context["price_data"].get(symbol)
    if df is None or df.empty:
        return None
    dates = df["date"].tolist()
    matches = [idx for idx, d in enumerate(dates) if pd.Timestamp(d) == pd.Timestamp(date)]
    if not matches:
        return None
    idx = matches[0]
    target = idx + horizon
    if target >= len(df):
        return None
    start = _float(df.iloc[idx].get("close"))
    end = _float(df.iloc[target].get("close"))
    if start == 0:
        return None
    return end / start - 1.0


def _load_profile() -> pd.DataFrame:
    if not PROFILE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PROFILE_CSV, dtype={"symbol": str}, keep_default_na=False)


def _source_function_summary(path: Path, function_name: str) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"path": str(path.relative_to(PROJECT_ROOT)), "function": function_name, "error": str(exc)}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "function": function_name,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "returns": "rule-based output; see source for exact implementation",
            }
    return {"path": str(path.relative_to(PROJECT_ROOT)), "function": function_name, "error": "not found"}


def _grep_project(pattern: str) -> list[str]:
    hits = []
    for root in ["src", "dashboard", "app/backend", "app/frontend/src"]:
        for path in (PROJECT_ROOT / root).glob("**/*"):
            if not path.is_file() or path.suffix not in {".py", ".jsx", ".js"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if pattern in text:
                hits.append(str(path.relative_to(PROJECT_ROOT)))
    return sorted(set(hits))


def render_source_audit(audit: dict[str, Any]) -> str:
    return "\n".join([
        "# Market Regime 来源审计",
        "",
        "本报告只审计现有逻辑，不修改 market_regime。",
        "",
        f"- primary source：{audit['primary_market_regime_source_file']}",
        f"- function：{audit['primary_market_regime_function']}",
        f"- raw states：{audit['primary_market_regime_states']}",
        f"- normalized mapping：{audit['normalized_mapping']}",
        f"- market_state source：{audit['market_state_source_file']} / {audit['market_state_function']}",
        "",
        "## 输入与阈值",
        "- 输入特征：" + "；".join(audit["input_features"]),
        "- 阈值：" + "；".join(audit["thresholds"]),
        f"- 是否读取未来数据：{audit['future_data_risk']}",
        f"- 是否只看单一指数：{audit['single_index_dependency']}",
        f"- 是否使用 ETF pool breadth：{audit['uses_etf_pool_breadth']}",
        f"- 是否使用 BUY/WATCH/SELL 数量：{audit['uses_buy_watch_sell_count']}",
        f"- 是否使用 high_beta/growth strength：{audit['uses_high_beta_growth_strength']}",
        f"- 是否使用风险压力：{audit['uses_risk_pressure']}",
        f"- 逻辑复杂度：{audit['logic_complexity']}",
        "",
        "## 读取 market_regime 的模块",
        _list_lines(audit.get("modules_reading_market_regime", [])),
        "",
        "## 执行层影响",
        f"- {audit['paper_trade_engine_impact']}",
        "- research_only=true",
        "- execution_allowed=false",
    ])


def render_replay_report(payload: dict[str, Any]) -> str:
    df = pd.DataFrame(payload.get("rows", []))
    sample = df.tail(10).to_dict(orient="records") if not df.empty else []
    return "\n".join([
        "# Market Regime 历史回放",
        "",
        "Point-in-time replay：每个 T 日只使用 T 日及以前数据；forward return 只作为标签。",
        "",
        f"- replay_start_date：{payload.get('replay_start_date')}",
        f"- replay_end_date：{payload.get('replay_end_date')}",
        f"- replay_trading_days：{payload.get('replay_trading_days')}",
        f"- raw values：{payload.get('raw_market_regime_values')}",
        f"- normalized mapping：{payload.get('normalized_mapping')}",
        f"- realized profile：{payload.get('point_in_time_realized_profile_note')}",
        "",
        _rows_table(sample, ["date", "raw_market_regime", "normalized_regime", "pool_size", "buy_count", "sell_count", "buy_breadth", "sell_breadth", "strong_resonance_breadth", "risk_pressure", "benchmark_return_10d"]),
        "",
        "## 安全边界",
        "- 本报告不修改 market_regime / ranking / adjusted preview / paper_trade_engine / paper_trades / paper_positions。",
    ])


def render_distribution_report(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Market Regime 分布分析",
        "",
        f"- total_days：{payload.get('total_days')}",
        f"- distribution：{payload.get('distribution')}",
        f"- dominant_regime：{payload.get('dominant_regime')}",
        f"- dominant_regime_percentage：{_pct(payload.get('dominant_regime_percentage'))}",
        f"- extreme_imbalance：{payload.get('extreme_imbalance')}",
        f"- has_discrimination：{payload.get('has_discrimination')}",
        "",
        "## 按月分布",
        _rows_table(payload.get("monthly_distribution", []), ["month", "trading_days", "OFFENSIVE_days", "OFFENSIVE_pct", "NEUTRAL_days", "NEUTRAL_pct", "DEFENSIVE_days", "DEFENSIVE_pct"]),
    ])


def render_stability_report(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Market Regime 稳定性分析",
        "",
        f"- regime_switch_count：{payload.get('regime_switch_count')}",
        f"- average_regime_duration：{_fmt(payload.get('average_regime_duration'))}",
        f"- median_regime_duration：{_fmt(payload.get('median_regime_duration'))}",
        f"- max_regime_duration：{payload.get('max_regime_duration')}",
        f"- one_day_reversal_count：{payload.get('one_day_reversal_count')}",
        f"- three_day_reversal_count：{payload.get('three_day_reversal_count')}",
        f"- five_day_reversal_count：{payload.get('five_day_reversal_count')}",
        f"- short_regime_whipsaw_count：{payload.get('short_regime_whipsaw_count')}",
        f"- needs_future_hysteresis_research：{payload.get('needs_future_hysteresis_research')}",
        "",
        "## by regime",
        _rows_table([{"regime": k, **v} for k, v in payload.get("by_regime", {}).items()], ["regime", "run_count", "average_duration", "median_duration", "max_duration"]),
        "",
        "本轮不实现 hysteresis / minimum duration，只记录未来研究需要。",
    ])


def render_forward_report(title: str, payload: dict[str, Any], cols: list[str]) -> str:
    rows = payload.get("rows", [])
    focus = [row for row in rows if int(row.get("forward_horizon", 0)) in {5, 10, 20}]
    return "\n".join([
        f"# {title}",
        "",
        "forward return 只作为 label，不参与 T 日 regime 判定。",
        "",
        _rows_table(focus, [*cols, "forward_horizon", "sample_count", "mean_forward_return", "median_forward_return", "positive_rate", "benchmark_excess_mean", "sample_status"]),
        "",
        "## 限制",
        "- 样本不足项标记 insufficient_sample。",
        "- style / structural 来自最新静态画像；realized risk 使用 T 日 point-in-time 重新计算。",
    ])


def render_representative_report(rows: list[dict[str, Any]]) -> str:
    return "\n".join([
        "# 代表 ETF Regime 行为",
        "",
        "本报告展示代表 ETF 在不同 regime 下的 5/10/20 日 forward return，不生成买卖指令。",
        "",
        _rows_table(rows, [
            "symbol", "name", "style_profile", "structural_risk_profile",
            "OFFENSIVE_5d_mean", "OFFENSIVE_10d_mean", "OFFENSIVE_20d_mean",
            "NEUTRAL_5d_mean", "NEUTRAL_10d_mean", "NEUTRAL_20d_mean",
            "DEFENSIVE_5d_mean", "DEFENSIVE_10d_mean", "DEFENSIVE_20d_mean",
            "OFFENSIVE_10d_excess", "NEUTRAL_10d_excess", "DEFENSIVE_10d_excess",
        ]),
    ])


def render_breadth_report(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Market Breadth 与 Regime 分析",
        "",
        "本报告检查当前 regime 是否真正区分市场宽度，避免局部热点被误读为全市场 risk_on。",
        "",
        _rows_table(payload.get("rows", []), ["normalized_regime", "sample_count", "buy_breadth_mean", "sell_breadth_mean", "strong_resonance_breadth_mean", "risk_pressure_mean"]),
        "",
        f"- OFFENSIVE buy breadth - DEFENSIVE buy breadth：{_fmt(payload.get('offensive_buy_breadth_minus_defensive'))}",
        f"- DEFENSIVE sell breadth - OFFENSIVE sell breadth：{_fmt(payload.get('defensive_sell_breadth_minus_offensive'))}",
        f"- OFFENSIVE buy breadth 是否明显更高：{payload.get('offensive_buy_breadth_higher')}",
        f"- DEFENSIVE sell breadth 是否明显更高：{payload.get('defensive_sell_breadth_higher')}",
        f"- 局部热点误判 risk_on 风险：{payload.get('local_hotspot_misread_risk')}",
        f"- strong resonance breadth：{payload.get('strong_resonance_predictive_value')}",
    ])


def render_decision_report(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Market Regime Audit Decision",
        "",
        f"- existing_regime_is_informative：{payload.get('existing_regime_is_informative')}",
        f"- existing_regime_is_stable：{payload.get('existing_regime_is_stable')}",
        f"- existing_regime_has_whipsaw_problem：{payload.get('existing_regime_has_whipsaw_problem')}",
        f"- style_regime_fit_supported：{payload.get('style_regime_fit_supported')}",
        f"- structural_risk_regime_fit_supported：{payload.get('structural_risk_regime_fit_supported')}",
        f"- ready_for_regime_fit_phase：{payload.get('ready_for_regime_fit_phase')}",
        f"- ready_for_preview：{payload.get('ready_for_preview')}",
        f"- ready_for_execution：{payload.get('ready_for_execution')}",
        f"- decision_reason：{payload.get('decision_reason')}",
        "",
        "本结论只决定是否继续研究，不进入执行层。",
    ])


def render_phase_report(payload: dict[str, Any]) -> str:
    d = payload.get("decision", {})
    replay = payload.get("replay", {})
    return "\n".join([
        "# Regime Layer Phase 2 - Market Audit / Historical Replay",
        "",
        "本报告为研究审计，不是执行方案。",
        "",
        "## 来源与逻辑",
        f"- 来源文件：{payload.get('market_regime_source', {}).get('file')}",
        f"- 来源函数：{payload.get('market_regime_source', {}).get('function')}",
        f"- 状态：{payload.get('market_regime_source', {}).get('states')}",
        f"- 阈值：{payload.get('market_regime_source', {}).get('logic')}",
        "",
        "## 回放范围",
        f"- replay_start_date：{replay.get('replay_start_date')}",
        f"- replay_end_date：{replay.get('replay_end_date')}",
        f"- replay_trading_days：{replay.get('replay_trading_days')}",
        "",
        "## 分布与稳定性",
        f"- distribution：{payload.get('distribution', {}).get('distribution')}",
        f"- regime_switch_count：{payload.get('stability', {}).get('regime_switch_count')}",
        f"- average_regime_duration：{_fmt(payload.get('stability', {}).get('average_regime_duration'))}",
        f"- short_regime_whipsaw_count：{payload.get('stability', {}).get('short_regime_whipsaw_count')}",
        f"- needs_future_hysteresis_research：{payload.get('stability', {}).get('needs_future_hysteresis_research')}",
        "",
        "## Forward Return 结果",
        f"- style summary：{payload.get('style_summary')}",
        f"- structural summary：{payload.get('structural_summary')}",
        f"- realized summary：{payload.get('realized_summary')}",
        f"- realized risk 分析限制：{payload.get('realized_risk_analysis_limit')}",
        "",
        "## 市场宽度",
        f"- breadth：{payload.get('breadth')}",
        "",
        "## Decision",
        f"- existing_regime_is_informative：{d.get('existing_regime_is_informative')}",
        f"- existing_regime_is_stable：{d.get('existing_regime_is_stable')}",
        f"- existing_regime_has_whipsaw_problem：{d.get('existing_regime_has_whipsaw_problem')}",
        f"- style_regime_fit_supported：{d.get('style_regime_fit_supported')}",
        f"- structural_risk_regime_fit_supported：{d.get('structural_risk_regime_fit_supported')}",
        f"- ready_for_regime_fit_phase：{d.get('ready_for_regime_fit_phase')}",
        f"- ready_for_preview：{d.get('ready_for_preview')}",
        f"- ready_for_execution：{d.get('ready_for_execution')}",
        "",
        "## 安全边界",
        "- research_only=true。",
        "- ready_for_execution=false。",
        "- 未修改 market_regime / BUY ranking / adjusted preview / paper_trade_engine / paper_trades / paper_positions。",
        "- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。",
    ])


def _compact_fit_summary(payload: dict, group_col: str) -> dict[str, Any]:
    rows = payload.get("rows", [])
    selected = [r for r in rows if int(r.get("forward_horizon", 0)) == 10]
    best_by_regime = {}
    for regime in ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]:
        sub = [r for r in selected if r.get("normalized_regime") == regime and r.get("sample_status") == "ok"]
        if sub:
            best = max(sub, key=lambda r: _float(r.get("benchmark_excess_mean")))
            best_by_regime[regime] = {group_col: best.get(group_col), "benchmark_excess_mean_10d": best.get("benchmark_excess_mean"), "sample_count": best.get("sample_count")}
    return {"best_by_regime_10d": best_by_regime}


def _fit_supported(payload: dict, group_col: str) -> bool:
    summary = _compact_fit_summary(payload, group_col).get("best_by_regime_10d", {})
    if len(summary) < 2:
        return False
    labels = {str(v.get(group_col)) for v in summary.values()}
    values = [_float(v.get("benchmark_excess_mean_10d")) for v in summary.values()]
    return len(labels) >= 2 and (max(values) - min(values) > 0.01)


def _decision_reason(informative: bool, stable: bool, style_supported: bool, structural_supported: bool, ready: bool) -> str:
    parts = []
    parts.append("informative breadth/regime separation" if informative else "breadth separation is weak or mixed")
    parts.append("stable enough" if stable else "whipsaw/hysteresis issue needs study")
    parts.append("style fit supported" if style_supported else "style fit weak")
    parts.append("structural fit supported" if structural_supported else "structural fit weak")
    parts.append("ready for next audit phase" if ready else "not enough for preview/execution")
    return "; ".join(parts)


def _returns_until(df: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    sub = df[df["date"] <= date].copy()
    return pd.to_numeric(sub["close"], errors="coerce").pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)


def _annualized_vol(returns: pd.Series, window: int) -> float | None:
    sub = returns.dropna().tail(window)
    if len(sub) < max(20, window // 2):
        return None
    return float(sub.std(ddof=1) * math.sqrt(252))


def _downside_vol(returns: pd.Series, window: int) -> float | None:
    sub = returns.dropna().tail(window)
    sub = sub[sub < 0]
    if len(sub) < 5:
        return None
    return float(sub.std(ddof=1) * math.sqrt(252))


def _beta(returns: pd.Series, benchmark: pd.Series, window: int) -> float | None:
    aligned = pd.concat([returns.rename("asset"), benchmark.rename("bench")], axis=1).dropna().tail(window)
    if len(aligned) < max(20, window // 2):
        return None
    variance = aligned["bench"].var(ddof=1)
    if not variance or pd.isna(variance):
        return None
    return float(aligned["asset"].cov(aligned["bench"]) / variance)


def _max_drawdown(prices: pd.DataFrame, window: int) -> float:
    close = pd.to_numeric(prices["close"], errors="coerce").dropna().tail(window)
    if len(close) < max(20, window // 2):
        return 0.0
    return float((close / close.cummax() - 1.0).min())


def _down_capture(returns: pd.Series, benchmark: pd.Series, window: int) -> float | None:
    aligned = pd.concat([returns.rename("asset"), benchmark.rename("bench")], axis=1).dropna().tail(window)
    if len(aligned) < max(20, window // 2):
        return None
    sub = aligned[aligned["bench"] < 0]
    if len(sub) < 5:
        return None
    bench_sum = sub["bench"].sum()
    if not bench_sum or pd.isna(bench_sum):
        return None
    return float(sub["asset"].sum() / bench_sum)


def _concentration_penalty(meta: dict[str, Any]) -> float:
    style = str(meta.get("style_profile") or "")
    if style == "BOND":
        return 0.05
    if style in {"CORE_LARGE_CAP", "CORE_MID_CAP"}:
        return 0.25
    if style == "GROWTH_BROAD":
        return 0.40
    if style in {"SECTOR_DEFENSIVE", "SECTOR_CYCLICAL", "COMMODITY_CYCLICAL"}:
        return 0.62
    if style in {"GROWTH_THEME", "HIGH_BETA_THEME"}:
        return 0.82
    return 0.55


def _whipsaw_count(runs: list[dict], max_middle_duration: int) -> int:
    count = 0
    for i in range(1, len(runs) - 1):
        if runs[i - 1]["regime"] == runs[i + 1]["regime"] and runs[i]["regime"] != runs[i - 1]["regime"] and runs[i]["duration"] <= max_middle_duration:
            count += 1
    return count


def _safety_payload() -> dict[str, bool]:
    return {
        "broker_api": False,
        "real_order": False,
        "real_account": False,
        "credentials_read": False,
        "paper_trade_engine_modified": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "buy_ranking_modified": False,
        "market_regime_modified": False,
        "adjusted_preview_modified": False,
        "execution_allowed": False,
    }


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    if not rows:
        return "\n".join([header, sep, "| " + " | ".join("" for _ in columns) + " |"])
    body = ["| " + " | ".join(_fmt_cell(row.get(col)) for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def _list_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 无"


def _json_dumps(payload: Any) -> str:
    return json.dumps(_sanitize(payload), ensure_ascii=False, indent=2)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if value is pd.NaT:
        return None
    return value


def _fmt_cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return ""
        return f"{float(value):.4f}"
    text = str(value).replace("|", "/").replace("\n", " ")
    return text[:260]


def _fmt(value: Any) -> str:
    number = _float(value, fallback=np.nan)
    if pd.isna(number):
        return "N/A"
    return f"{number:.4f}"


def _pct(value: Any) -> str:
    number = _float(value, fallback=np.nan)
    if pd.isna(number):
        return "N/A"
    return f"{number:.2%}"


def _float(value: Any, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(number) or math.isinf(number):
        return fallback
    return number


def _mean(values: list[Any]) -> float | None:
    clean = [float(v) for v in values if v is not None and not pd.isna(v)]
    return round(float(np.mean(clean)), 6) if clean else None


def _median(values: list[Any]) -> float | None:
    clean = [float(v) for v in values if v is not None and not pd.isna(v)]
    return round(float(np.median(clean)), 6) if clean else None


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
