"""Style x stabilized-regime fit research.

Research-only / shadow-only. This module uses the selected stabilized regime
candidate from Phase 2.5 and studies ETF style forward-return labels by regime.
It does not modify BUY ranking, adjusted preview, market_regime, paper trades,
paper positions, or execution code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import phase4c_alpha_common as common
import ranking_model_v2_backtest as ranking
import market_regime_replay as phase2
from config import DATA_DIR, REPORT_DIR


STABILIZATION_REPLAY_CSV = DATA_DIR / "market_regime_stabilization_replay.csv"
DECISION_JSON = REPORT_DIR / "regime_stabilization_candidate_decision.json"
PROFILE_CSV = REPORT_DIR / "etf_risk_profile.csv"
TRACKING_CSV = DATA_DIR / "style_regime_fit_tracking.csv"

SOURCE_AUDIT_MD = REPORT_DIR / "style_regime_fit_source_audit.md"
SOURCE_AUDIT_JSON = REPORT_DIR / "style_regime_fit_source_audit.json"
MATRIX_MD = REPORT_DIR / "style_regime_fit_matrix.md"
MATRIX_CSV = REPORT_DIR / "style_regime_fit_matrix.csv"
MATRIX_JSON = REPORT_DIR / "style_regime_fit_matrix.json"
SUMMARY_MD = REPORT_DIR / "style_regime_fit_summary.md"
SUMMARY_JSON = REPORT_DIR / "style_regime_fit_summary.json"
DIFF_MD = REPORT_DIR / "style_regime_differentiation.md"
DIFF_CSV = REPORT_DIR / "style_regime_differentiation.csv"
DIFF_JSON = REPORT_DIR / "style_regime_differentiation.json"
BUY_MD = REPORT_DIR / "current_buy_top10_style_regime_fit.md"
BUY_CSV = REPORT_DIR / "current_buy_top10_style_regime_fit.csv"
BUY_JSON = REPORT_DIR / "current_buy_top10_style_regime_fit.json"
PORTFOLIO_MD = REPORT_DIR / "current_portfolio_style_regime_fit.md"
PORTFOLIO_JSON = REPORT_DIR / "current_portfolio_style_regime_fit.json"
INTERACTION_MD = REPORT_DIR / "style_fit_signal_interaction.md"
INTERACTION_CSV = REPORT_DIR / "style_fit_signal_interaction.csv"
INTERACTION_JSON = REPORT_DIR / "style_fit_signal_interaction.json"
PHASE_DECISION_MD = REPORT_DIR / "style_regime_fit_phase_decision.md"
PHASE_DECISION_JSON = REPORT_DIR / "style_regime_fit_phase_decision.json"
PHASE_MD = REPORT_DIR / "regime_layer_phase3_style_fit.md"
PHASE_JSON = REPORT_DIR / "regime_layer_phase3_style_fit.json"

REGIMES = ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]
STYLES = [
    "BOND",
    "DIVIDEND",
    "LOW_VOL",
    "CORE_LARGE_CAP",
    "CORE_MID_CAP",
    "GROWTH_BROAD",
    "GROWTH_THEME",
    "SECTOR_CYCLICAL",
    "SECTOR_DEFENSIVE",
    "HIGH_BETA_THEME",
    "COMMODITY_CYCLICAL",
    "QDII_OBSERVATION",
]
HORIZONS = [1, 3, 5, 10, 20]
CORE_HORIZONS = [5, 10, 20]
MIN_SAMPLE_COUNT = 30
SELECTED_CANDIDATE_COLUMN = {
    "RAW": "candidate_a_regime",
    "CONFIRM_2D": "candidate_b_regime",
    "CONFIRM_3D": "candidate_c_regime",
    "ASYMMETRIC_CONFIRM": "candidate_d_regime",
}
EVIDENCE_ORDER = {
    "SUPPORTED": 2,
    "WEAK_SUPPORT": 1,
    "NEUTRAL": 0,
    "WEAK_CONFLICT": -1,
    "CONFLICT": -2,
    "INSUFFICIENT": 0,
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    replay = _read_replay()
    decision = _read_json(DECISION_JSON)
    profile = _read_profile()
    selected = str(decision.get("selected_candidate") or "ASYMMETRIC_CONFIRM")
    selected_col = SELECTED_CANDIDATE_COLUMN.get(selected, "candidate_d_regime")
    context = common.load_context()

    source_audit = build_source_audit(replay, decision, profile, selected, selected_col)
    forward_rows = build_style_forward_rows(replay, profile, selected_col, context)
    matrix = aggregate_matrix(forward_rows)
    summary = build_fit_summary(matrix)
    differentiation = build_differentiation(summary)
    buy_fit = build_current_buy_top10_fit(summary, decision, profile, context)
    portfolio_fit = build_current_portfolio_fit(summary, decision, profile)
    interaction = build_signal_interaction(replay, profile, selected_col, summary, context)
    tracking = update_tracking(buy_fit, context)
    phase_decision = build_phase_decision(summary, differentiation, buy_fit, portfolio_fit, interaction, source_audit)
    phase = build_phase_payload(source_audit, matrix, summary, differentiation, buy_fit, portfolio_fit, interaction, tracking, phase_decision)

    _write_json(SOURCE_AUDIT_JSON, source_audit)
    SOURCE_AUDIT_MD.write_text(render_source_audit(source_audit), encoding="utf-8")
    pd.DataFrame(matrix["rows"]).to_csv(MATRIX_CSV, index=False)
    _write_json(MATRIX_JSON, matrix)
    MATRIX_MD.write_text(render_matrix_report(matrix), encoding="utf-8")
    _write_json(SUMMARY_JSON, summary)
    SUMMARY_MD.write_text(render_summary_report(summary), encoding="utf-8")
    pd.DataFrame(differentiation["rows"]).to_csv(DIFF_CSV, index=False)
    _write_json(DIFF_JSON, differentiation)
    DIFF_MD.write_text(render_differentiation_report(differentiation), encoding="utf-8")
    pd.DataFrame(buy_fit["rows"]).to_csv(BUY_CSV, index=False)
    _write_json(BUY_JSON, buy_fit)
    BUY_MD.write_text(render_buy_fit_report(buy_fit), encoding="utf-8")
    _write_json(PORTFOLIO_JSON, portfolio_fit)
    PORTFOLIO_MD.write_text(render_portfolio_fit_report(portfolio_fit), encoding="utf-8")
    pd.DataFrame(interaction["rows"]).to_csv(INTERACTION_CSV, index=False)
    _write_json(INTERACTION_JSON, interaction)
    INTERACTION_MD.write_text(render_interaction_report(interaction), encoding="utf-8")
    _write_json(PHASE_DECISION_JSON, phase_decision)
    PHASE_DECISION_MD.write_text(render_phase_decision_report(phase_decision), encoding="utf-8")
    _write_json(PHASE_JSON, phase)
    PHASE_MD.write_text(render_phase_report(phase), encoding="utf-8")

    print(f"style_regime_fit selected_candidate: {selected}")
    print(f"current stable regime: {decision.get('current_selected_shadow_regime')}")
    print(f"style matrix rows: {len(matrix['rows'])}")
    print(f"tracking rows: {tracking.get('tracking_rows')}")
    print(f"written: {PHASE_MD}")


def build_source_audit(replay: pd.DataFrame, decision: dict, profile: pd.DataFrame, selected: str, selected_col: str) -> dict[str, Any]:
    unknown_count = int((profile.get("style_profile", pd.Series(dtype=str)).astype(str) == "UNKNOWN").sum()) if not profile.empty else 0
    return {
        "generated_at": _now(),
        "selected_candidate": selected,
        "selected_candidate_column": selected_col,
        "selected_candidate_is_expected": selected == "ASYMMETRIC_CONFIRM",
        "stable_regime_current_date": decision.get("current_date"),
        "current_stable_regime": decision.get("current_selected_shadow_regime"),
        "replay_rows": int(len(replay)),
        "replay_start": str(replay["date"].iloc[0]) if not replay.empty else "",
        "replay_end": str(replay["date"].iloc[-1]) if not replay.empty else "",
        "stable_regime_column_present": selected_col in replay.columns,
        "stable_regime_values": sorted(replay.get(selected_col, pd.Series(dtype=str)).dropna().astype(str).unique().tolist()),
        "stable_regime_point_in_time": True,
        "stable_regime_point_in_time_note": "ASYMMETRIC_CONFIRM was generated sequentially from raw regime using only T and prior days; no backfill.",
        "profile_rows": int(len(profile)),
        "style_profile_unknown_count": unknown_count,
        "style_profile_unknown_zero": unknown_count == 0,
        "minimum_sample_count": MIN_SAMPLE_COUNT,
        "forward_returns_label_only": True,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_style_forward_rows(replay: pd.DataFrame, profile: pd.DataFrame, selected_col: str, context: dict) -> list[dict[str, Any]]:
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    raw_replay = _read_csv(DATA_DIR / "market_regime_replay.csv")
    benchmark_by_date = raw_replay.set_index(raw_replay["date"].astype(str)).to_dict(orient="index") if not raw_replay.empty else {}
    rows = []
    for _, regime_row in replay.iterrows():
        date = pd.Timestamp(regime_row["date"])
        regime = str(regime_row[selected_col])
        bench_returns = _benchmark_returns_from_replay(benchmark_by_date.get(date.strftime("%Y-%m-%d"), {}))
        for symbol in context["price_data"]:
            p = profile_map.get(str(symbol))
            if not p:
                continue
            style = str(p.get("style_profile", "UNKNOWN"))
            if style == "UNKNOWN":
                continue
            for horizon in HORIZONS:
                fwd = phase2._forward_return(str(symbol), date, horizon, context)
                if fwd is None:
                    continue
                bench = bench_returns.get(horizon)
                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "regime": regime,
                    "symbol": str(symbol),
                    "name": p.get("name", symbol),
                    "style_profile": style,
                    "structural_risk_profile": p.get("structural_risk_profile", ""),
                    "realized_risk_profile": p.get("realized_risk_profile", ""),
                    "forward_horizon": horizon,
                    "forward_return": fwd,
                    "benchmark_forward_return": bench,
                    "benchmark_excess_return": fwd - bench if bench is not None and not pd.isna(bench) else None,
                    "forward_return_is_label_only": True,
                    "research_only": True,
                    "execution_allowed": False,
                })
    return rows


def aggregate_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    df = pd.DataFrame(rows)
    out = []
    if not df.empty:
        for (regime, style, horizon), sub in df.groupby(["regime", "style_profile", "forward_horizon"], dropna=False):
            returns = pd.to_numeric(sub["forward_return"], errors="coerce").dropna()
            excess = pd.to_numeric(sub["benchmark_excess_return"], errors="coerce").dropna()
            metrics = {
                "regime": regime,
                "style_profile": style,
                "forward_horizon": int(horizon),
                "sample_count": int(len(returns)),
                "mean_forward_return": _mean(returns.tolist()),
                "median_forward_return": _median(returns.tolist()),
                "positive_rate": float((returns > 0).mean()) if len(returns) else None,
                "q25_forward_return": _percentile(returns.tolist(), 25),
                "q75_forward_return": _percentile(returns.tolist(), 75),
                "worst_10pct_mean": _worst_tail_mean(returns.tolist(), 0.10),
                "benchmark_excess_mean": _mean(excess.tolist()),
                "benchmark_excess_median": _median(excess.tolist()),
                "research_only": True,
                "execution_allowed": False,
            }
            evidence, reasons = fit_evidence(metrics)
            metrics["fit_evidence"] = evidence
            metrics["evidence_reasons"] = "; ".join(reasons)
            out.append(metrics)
    return {
        "generated_at": _now(),
        "minimum_sample_count": MIN_SAMPLE_COUNT,
        "fit_evidence_rules": _fit_rules(),
        "rows": sorted(out, key=lambda r: (str(r["style_profile"]), str(r["regime"]), int(r["forward_horizon"]))),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def fit_evidence(row: dict[str, Any]) -> tuple[str, list[str]]:
    n = int(_float(row.get("sample_count")))
    if n < MIN_SAMPLE_COUNT:
        return "INSUFFICIENT", [f"sample_count {n} < {MIN_SAMPLE_COUNT}"]
    ex_med = _float(row.get("benchmark_excess_median"), fallback=float("nan"))
    med = _float(row.get("median_forward_return"), fallback=float("nan"))
    pos = _float(row.get("positive_rate"), fallback=float("nan"))
    positive = int(pd.notna(ex_med) and ex_med > 0) + int(pd.notna(med) and med > 0) + int(pd.notna(pos) and pos >= 0.55)
    negative = int(pd.notna(ex_med) and ex_med < 0) + int(pd.notna(med) and med < 0) + int(pd.notna(pos) and pos <= 0.45)
    reasons = [f"excess_median={_fmt(ex_med)}", f"median={_fmt(med)}", f"positive_rate={_fmt(pos)}", f"sample={n}"]
    if positive == 3:
        return "SUPPORTED", reasons
    if positive >= 2:
        return "WEAK_SUPPORT", reasons
    if negative == 3:
        return "CONFLICT", reasons
    if negative >= 2:
        return "WEAK_CONFLICT", reasons
    return "NEUTRAL", reasons


def build_fit_summary(matrix: dict) -> dict[str, Any]:
    rows = matrix.get("rows", [])
    by_key = {(r["regime"], r["style_profile"], int(r["forward_horizon"])): r for r in rows}
    summary_rows = []
    matrix_table = []
    for style in STYLES:
        line = {"style_profile": style}
        for regime in REGIMES:
            core = [by_key.get((regime, style, h), {}) for h in CORE_HORIZONS]
            overall, consistency, conflict, reason = overall_evidence(core)
            row10 = by_key.get((regime, style, 10), {})
            item = {
                "style_profile": style,
                "regime": regime,
                "overall_fit_evidence": overall,
                "horizon_consistency": consistency,
                "horizon_conflict": conflict,
                "overall_reason": reason,
                "sample_count_10d": row10.get("sample_count"),
                "median_return_10d": row10.get("median_forward_return"),
                "benchmark_excess_median_10d": row10.get("benchmark_excess_median"),
                "fit_evidence_10d": row10.get("fit_evidence", "INSUFFICIENT"),
                "research_only": True,
                "execution_allowed": False,
            }
            summary_rows.append(item)
            line[regime] = {
                "overall_fit_evidence": overall,
                "median_return_10d": row10.get("median_forward_return"),
                "benchmark_excess_median_10d": row10.get("benchmark_excess_median"),
                "sample_count_10d": row10.get("sample_count"),
            }
        matrix_table.append(line)
    support_by_regime = {
        regime: [
            row["style_profile"] for row in summary_rows
            if row["regime"] == regime and row["overall_fit_evidence"] in {"SUPPORTED", "WEAK_SUPPORT"}
        ]
        for regime in REGIMES
    }
    conflict_by_regime = {
        regime: [
            row["style_profile"] for row in summary_rows
            if row["regime"] == regime and row["overall_fit_evidence"] in {"CONFLICT", "WEAK_CONFLICT"}
        ]
        for regime in REGIMES
    }
    return {
        "generated_at": _now(),
        "rows": summary_rows,
        "matrix_table": matrix_table,
        "support_by_regime": support_by_regime,
        "conflict_by_regime": conflict_by_regime,
        "minimum_sample_count": MIN_SAMPLE_COUNT,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def overall_evidence(core_rows: list[dict]) -> tuple[str, str, bool, str]:
    valid = [r for r in core_rows if r and r.get("fit_evidence") != "INSUFFICIENT"]
    if len(valid) < 2:
        return "INSUFFICIENT", "insufficient_core_horizon", False, "fewer than 2 core horizons have enough samples"
    values = [EVIDENCE_ORDER.get(str(r.get("fit_evidence")), 0) for r in valid]
    support = sum(1 for v in values if v > 0)
    conflict = sum(1 for v in values if v < 0)
    horizon_conflict = support > 0 and conflict > 0
    row10 = next((r for r in core_rows if r and int(_float(r.get("forward_horizon"))) == 10), {})
    ev10 = str(row10.get("fit_evidence", "INSUFFICIENT"))
    if horizon_conflict:
        if support > conflict:
            return "WEAK_SUPPORT", "mixed_core_horizon", True, "core horizons mixed; cannot mark SUPPORTED"
        if conflict > support:
            return "WEAK_CONFLICT", "mixed_core_horizon", True, "core horizons mixed; cannot mark CONFLICT"
        return "NEUTRAL", "mixed_core_horizon", True, "core horizons conflict"
    if support == len(valid):
        return ("SUPPORTED" if ev10 == "SUPPORTED" and len(valid) >= 3 else "WEAK_SUPPORT", "consistent_positive", False, "core horizons positive")
    if conflict == len(valid):
        return ("CONFLICT" if ev10 == "CONFLICT" and len(valid) >= 3 else "WEAK_CONFLICT", "consistent_negative", False, "core horizons negative")
    return "NEUTRAL", "mixed_or_flat", False, "no stable positive/negative direction"


def build_differentiation(summary: dict) -> dict[str, Any]:
    rows = []
    summary_rows = summary.get("rows", [])
    for style in STYLES:
        style_rows = [r for r in summary_rows if r["style_profile"] == style]
        values = {
            r["regime"]: _float(r.get("benchmark_excess_median_10d"), fallback=float("nan"))
            for r in style_rows
        }
        clean = {k: v for k, v in values.items() if pd.notna(v)}
        if clean:
            best_regime = max(clean, key=clean.get)
            worst_regime = min(clean, key=clean.get)
            gap = clean[best_regime] - clean[worst_regime]
        else:
            best_regime = worst_regime = ""
            gap = None
        rows.append({
            "style_profile": style,
            "OFFENSIVE_10d_median_excess": values.get("OFFENSIVE"),
            "NEUTRAL_10d_median_excess": values.get("NEUTRAL"),
            "DEFENSIVE_10d_median_excess": values.get("DEFENSIVE"),
            "best_regime": best_regime,
            "worst_regime": worst_regime,
            "best_vs_worst_gap": gap,
            "regime_sensitive": bool(gap is not None and gap >= 0.01),
            "regime_sensitivity_strength": "HIGH" if gap is not None and gap >= 0.02 else ("MEDIUM" if gap is not None and gap >= 0.01 else "LOW"),
            "research_only": True,
            "execution_allowed": False,
        })
    sensitive = [r["style_profile"] for r in rows if r["regime_sensitive"]]
    insensitive = [r["style_profile"] for r in rows if not r["regime_sensitive"]]
    return {
        "generated_at": _now(),
        "rows": rows,
        "regime_sensitive_styles": sensitive,
        "regime_insensitive_styles": insensitive,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_current_buy_top10_fit(summary: dict, decision: dict, profile: pd.DataFrame, context: dict) -> dict[str, Any]:
    ranking_rows = _read_buy_ranking().head(10).to_dict(orient="records")
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    current_regime = str(decision.get("current_selected_shadow_regime") or "NEUTRAL")
    lookup = _summary_lookup(summary)
    rows = []
    for row in ranking_rows:
        symbol = str(row.get("code", "")).zfill(6)
        p = profile_map.get(symbol, {})
        style = str(p.get("style_profile", "UNKNOWN"))
        fit = lookup.get((current_regime, style), {})
        latest_date = str(decision.get("current_date") or "")
        rows.append({
            "rank": int(_float(row.get("rank"))),
            "symbol": symbol,
            "name": row.get("name", p.get("name", symbol)),
            "raw_score": _float(row.get("rank_score"), fallback=float("nan")),
            "style_profile": style,
            "current_stable_regime": current_regime,
            "overall_fit_evidence": fit.get("overall_fit_evidence", "INSUFFICIENT"),
            "10d_median_forward_return": fit.get("median_return_10d"),
            "10d_benchmark_excess_median": fit.get("benchmark_excess_median_10d"),
            "sample_count": fit.get("sample_count_10d"),
            "fit_interpretation": _fit_interpretation(symbol, style, current_regime, fit),
            "snapshot_date": latest_date,
            "research_only": True,
            "execution_allowed": False,
        })
    counts = _evidence_counts(rows, "overall_fit_evidence")
    return {
        "generated_at": _now(),
        "snapshot_date": decision.get("current_date"),
        "current_stable_regime": current_regime,
        "rows": rows,
        "counts": counts,
        "has_regime_conflict": counts.get("CONFLICT", 0) + counts.get("WEAK_CONFLICT", 0) > 0,
        "conflict_count": counts.get("CONFLICT", 0) + counts.get("WEAK_CONFLICT", 0),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_current_portfolio_fit(summary: dict, decision: dict, profile: pd.DataFrame) -> dict[str, Any]:
    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    current_regime = str(decision.get("current_selected_shadow_regime") or "NEUTRAL")
    lookup = _summary_lookup(summary)
    total_value = pd.to_numeric(positions.get("market_value", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    rows = []
    for _, pos in positions.iterrows():
        symbol = str(pos.get("symbol", "")).zfill(6)
        p = profile_map.get(symbol, {})
        style = str(p.get("style_profile", pos.get("style_profile", "UNKNOWN")))
        fit = lookup.get((current_regime, style), {})
        mv = _float(pos.get("market_value"))
        rows.append({
            "symbol": symbol,
            "name": pos.get("name", p.get("name", symbol)),
            "current_weight": mv / total_value if total_value else 0.0,
            "style_profile": style,
            "structural_risk_profile": p.get("structural_risk_profile", pos.get("risk_profile", "")),
            "realized_risk_profile": p.get("realized_risk_profile", pos.get("risk_profile", "")),
            "current_stable_regime": current_regime,
            "overall_fit_evidence": fit.get("overall_fit_evidence", "INSUFFICIENT"),
            "fit_interpretation": _fit_interpretation(symbol, style, current_regime, fit),
            "research_only": True,
            "execution_allowed": False,
        })
    counts = _evidence_counts(rows, "overall_fit_evidence")
    return {
        "generated_at": _now(),
        "current_stable_regime": current_regime,
        "rows": rows,
        "counts": counts,
        "conflict_count": counts.get("CONFLICT", 0) + counts.get("WEAK_CONFLICT", 0),
        "portfolio_has_regime_conflict": counts.get("CONFLICT", 0) + counts.get("WEAK_CONFLICT", 0) > 0,
        "regime_style_concentration": _style_concentration(rows),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_signal_interaction(replay: pd.DataFrame, profile: pd.DataFrame, selected_col: str, summary: dict, context: dict) -> dict[str, Any]:
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    summary_lookup = _summary_lookup(summary)
    rows = []
    replay_map = replay.set_index("date").to_dict(orient="index")
    for date_text, regime_row in replay_map.items():
        date = pd.Timestamp(date_text)
        daily_rows = ranking.build_daily_rows(date, context)
        ranked = ranking.rank_rows(daily_rows, "top10_diversified_filter_v2")[:30]
        stable_regime = str(regime_row.get(selected_col))
        for row in ranked:
            symbol = str(row.get("symbol"))
            p = profile_map.get(symbol, {})
            style = str(p.get("style_profile", "UNKNOWN"))
            fit = summary_lookup.get((stable_regime, style), {})
            bucket = signal_bucket(_float(row.get("rank_score")))
            for horizon in HORIZONS:
                fwd = phase2._forward_return(symbol, date, horizon, context)
                if fwd is None:
                    continue
                rows.append({
                    "date": date_text,
                    "symbol": symbol,
                    "signal_strength_bucket": bucket,
                    "style_fit_evidence": fit.get("overall_fit_evidence", "INSUFFICIENT"),
                    "forward_horizon": horizon,
                    "forward_return": fwd,
                    "research_only": True,
                    "execution_allowed": False,
                })
    df = pd.DataFrame(rows)
    out = []
    if not df.empty:
        for (bucket, evidence, horizon), sub in df.groupby(["signal_strength_bucket", "style_fit_evidence", "forward_horizon"]):
            returns = pd.to_numeric(sub["forward_return"], errors="coerce").dropna()
            out.append({
                "signal_strength_bucket": bucket,
                "style_fit_evidence": evidence,
                "forward_horizon": int(horizon),
                "sample_count": int(len(returns)),
                "mean_forward_return": _mean(returns.tolist()),
                "median_forward_return": _median(returns.tolist()),
                "positive_rate": float((returns > 0).mean()) if len(returns) else None,
                "research_only": True,
                "execution_allowed": False,
            })
    incremental = _incremental_signal_value(out)
    return {
        "generated_at": _now(),
        "signal_strength_bucket_rules": {"STRONG": "rank_score >= 75", "MEDIUM": "55 <= rank_score < 75", "WEAK": "rank_score < 55"},
        "rows": sorted(out, key=lambda r: (str(r["signal_strength_bucket"]), str(r["style_fit_evidence"]), int(r["forward_horizon"]))),
        "fit_has_incremental_signal_value": incremental["has_value"],
        "incremental_signal_reason": incremental["reason"],
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def update_tracking(buy_fit: dict, context: dict) -> dict[str, Any]:
    existing = _read_csv(TRACKING_CSV)
    current = []
    for row in buy_fit.get("rows", []):
        date_text = str(row.get("snapshot_date"))
        symbol = str(row.get("symbol"))
        item = {
            "snapshot_date": date_text,
            "stable_regime": row.get("current_stable_regime"),
            "symbol": symbol,
            "name": row.get("name"),
            "rank": row.get("rank"),
            "raw_score": row.get("raw_score"),
            "style_profile": row.get("style_profile"),
            "fit_evidence": row.get("overall_fit_evidence"),
            "fit_reason": row.get("fit_interpretation"),
            "research_only": True,
            "execution_allowed": False,
        }
        for horizon in HORIZONS:
            fwd = phase2._forward_return(symbol, pd.Timestamp(date_text), horizon, context)
            item[f"forward_{horizon}d"] = fwd
            item[f"matured_{horizon}d"] = fwd is not None
        current.append(item)
    combined = pd.concat([existing, pd.DataFrame(current)], ignore_index=True) if not existing.empty else pd.DataFrame(current)
    if not combined.empty:
        combined["snapshot_date"] = combined["snapshot_date"].astype(str)
        combined["symbol"] = combined["symbol"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
        combined = combined.drop_duplicates(["snapshot_date", "symbol"], keep="last").sort_values(["snapshot_date", "rank", "symbol"])
        combined.to_csv(TRACKING_CSV, index=False)
    return {
        "generated_at": _now(),
        "tracking_rows": int(len(combined)) if not combined.empty else 0,
        "latest_snapshot_date": buy_fit.get("snapshot_date"),
        "latest_rows": current,
        "tracking_file": str(TRACKING_CSV),
        "research_only": True,
        "execution_allowed": False,
    }


def build_phase_decision(summary: dict, differentiation: dict, buy_fit: dict, portfolio_fit: dict, interaction: dict, source_audit: dict) -> dict[str, Any]:
    all_evidence = [row["overall_fit_evidence"] for row in summary.get("rows", [])]
    historical_support = any(v in {"SUPPORTED", "CONFLICT"} for v in all_evidence)
    enough_samples = source_audit.get("style_profile_unknown_zero") and bool(summary.get("rows"))
    differentiation_exists = len(differentiation.get("regime_sensitive_styles", [])) > 0
    incremental = bool(interaction.get("fit_has_incremental_signal_value"))
    ready_shadow = bool(historical_support and enough_samples and differentiation_exists)
    ready_adjusted = bool(ready_shadow and incremental)
    return {
        "generated_at": _now(),
        "style_fit_has_historical_support": historical_support,
        "style_fit_has_incremental_signal_value": incremental,
        "current_buy_top10_has_regime_conflict": bool(buy_fit.get("has_regime_conflict")),
        "current_portfolio_has_regime_conflict": bool(portfolio_fit.get("portfolio_has_regime_conflict")),
        "buy_top10_conflict_count": buy_fit.get("conflict_count", 0),
        "portfolio_conflict_count": portfolio_fit.get("conflict_count", 0),
        "ready_for_fit_shadow_observation": ready_shadow,
        "ready_for_adjusted_preview_research": ready_adjusted,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "decision_reason": _phase_decision_reason(historical_support, differentiation_exists, incremental),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_phase_payload(source_audit: dict, matrix: dict, summary: dict, differentiation: dict, buy_fit: dict, portfolio_fit: dict, interaction: dict, tracking: dict, decision: dict) -> dict[str, Any]:
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 3 - Style-Regime Fit Research",
        "selected_stable_regime_candidate": source_audit.get("selected_candidate"),
        "current_stable_regime": source_audit.get("current_stable_regime"),
        "replay_range": {"start": source_audit.get("replay_start"), "end": source_audit.get("replay_end"), "rows": source_audit.get("replay_rows")},
        "style_regime_matrix": summary.get("matrix_table", []),
        "support_by_regime": summary.get("support_by_regime", {}),
        "conflict_by_regime": summary.get("conflict_by_regime", {}),
        "regime_sensitive_styles": differentiation.get("regime_sensitive_styles", []),
        "regime_insensitive_styles": differentiation.get("regime_insensitive_styles", []),
        "current_buy_top10_fit": buy_fit,
        "current_portfolio_fit": portfolio_fit,
        "signal_interaction": interaction,
        "tracking": tracking,
        "phase_decision": decision,
        "research_only": True,
        "shadow_only": True,
        "ready_for_execution": False,
        "safety": _safety_payload(),
    }


def _phase_decision_reason(historical: bool, differentiated: bool, incremental: bool) -> str:
    if historical and differentiated and incremental:
        return "style fit has historical support, regime differentiation, and preliminary incremental signal value; still shadow-only."
    if historical and differentiated:
        return "style fit has historical support and regime differentiation, but incremental signal value is not yet strong enough for adjusted preview research."
    return "style fit evidence is not mature enough; keep tracking only."


def _incremental_signal_value(rows: list[dict]) -> dict[str, Any]:
    strong = [r for r in rows if r["signal_strength_bucket"] == "STRONG" and int(r["forward_horizon"]) == 10]
    supported = [r for r in strong if r["style_fit_evidence"] in {"SUPPORTED", "WEAK_SUPPORT"}]
    conflict = [r for r in strong if r["style_fit_evidence"] in {"CONFLICT", "WEAK_CONFLICT"}]
    sup_med = _weighted_mean(supported, "median_forward_return", "sample_count")
    con_med = _weighted_mean(conflict, "median_forward_return", "sample_count")
    if sup_med is None or con_med is None:
        return {"has_value": False, "reason": "insufficient STRONG signal supported/conflict samples for 10d comparison"}
    gap = sup_med - con_med
    return {
        "has_value": gap > 0.003,
        "reason": f"STRONG+supported 10d median minus STRONG+conflict = {_fmt(gap)}",
    }


def _weighted_mean(rows: list[dict], value_col: str, weight_col: str) -> float | None:
    nums = []
    weights = []
    for row in rows:
        v = _float(row.get(value_col), fallback=float("nan"))
        w = _float(row.get(weight_col), fallback=float("nan"))
        if pd.notna(v) and pd.notna(w) and w > 0:
            nums.append(v * w)
            weights.append(w)
    return sum(nums) / sum(weights) if weights else None


def _read_buy_ranking() -> pd.DataFrame:
    rows = _read_markdown_table(REPORT_DIR / "buy_signal_ranking.md", "Top BUY Ranking")
    parsed = []
    for row in rows:
        parsed.append({
            "rank": _float(row.get("rank")),
            "code": str(row.get("code", "")).zfill(6),
            "name": row.get("name", ""),
            "rank_score": _float(row.get("rank_score"), fallback=float("nan")),
            "group": row.get("group", ""),
        })
    return pd.DataFrame(parsed)


def _read_markdown_table(path: Path, section_title: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        if line.strip().startswith("## "):
            in_section = section_title in line
            continue
        if in_section and line.strip().startswith("|"):
            table.append(line)
        elif in_section and table:
            break
    if len(table) < 3:
        return []
    headers = [cell.strip() for cell in table[0].strip("|").split("|")]
    rows = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def render_source_audit(audit: dict) -> str:
    return "\n".join([
        "# Style-Regime Fit Source Audit",
        "",
        f"- selected_candidate: {audit.get('selected_candidate')}",
        f"- selected_candidate_column: {audit.get('selected_candidate_column')}",
        f"- current_stable_regime: {audit.get('current_stable_regime')}",
        f"- replay range: {audit.get('replay_start')} to {audit.get('replay_end')} ({audit.get('replay_rows')} rows)",
        f"- style_profile UNKNOWN count: {audit.get('style_profile_unknown_count')}",
        f"- minimum_sample_count: {audit.get('minimum_sample_count')}",
        f"- stable_regime_point_in_time: {audit.get('stable_regime_point_in_time')}",
        f"- forward_returns_label_only: {audit.get('forward_returns_label_only')}",
        "",
        "research_only=true; shadow_only=true; execution_allowed=false.",
    ])


def render_matrix_report(matrix: dict) -> str:
    return "\n".join([
        "# Style-Regime Fit Matrix Detail",
        "",
        "每行是 regime × style × horizon。Forward return 只作为未来 label。",
        "",
        _markdown_table(matrix.get("rows", []), ["regime", "style_profile", "forward_horizon", "sample_count", "median_forward_return", "positive_rate", "benchmark_excess_median", "fit_evidence"], 240),
    ])


def render_summary_report(summary: dict) -> str:
    rows = []
    for item in summary.get("matrix_table", []):
        row = {"Style": item["style_profile"]}
        for regime in REGIMES:
            cell = item.get(regime, {})
            row[regime] = f"{cell.get('overall_fit_evidence')} / 10d med={_fmt(cell.get('median_return_10d'))} / excess={_fmt(cell.get('benchmark_excess_median_10d'))} / n={cell.get('sample_count_10d')}"
        rows.append(row)
    return "\n".join([
        "# Style-Regime Fit Summary",
        "",
        _markdown_table(rows, ["Style", "OFFENSIVE", "NEUTRAL", "DEFENSIVE"]),
        "",
        "## Support by Regime",
        json.dumps(summary.get("support_by_regime", {}), ensure_ascii=False, indent=2),
        "",
        "## Conflict by Regime",
        json.dumps(summary.get("conflict_by_regime", {}), ensure_ascii=False, indent=2),
    ])


def render_differentiation_report(payload: dict) -> str:
    return "\n".join([
        "# Style Regime Differentiation",
        "",
        _markdown_table(payload.get("rows", []), ["style_profile", "best_regime", "worst_regime", "best_vs_worst_gap", "regime_sensitive", "regime_sensitivity_strength"]),
    ])


def render_buy_fit_report(payload: dict) -> str:
    return "\n".join([
        "# Current BUY Top10 Style-Regime Fit",
        "",
        f"- current_stable_regime: {payload.get('current_stable_regime')}",
        f"- conflict_count: {payload.get('conflict_count')}",
        "",
        _markdown_table(payload.get("rows", []), ["rank", "symbol", "name", "raw_score", "style_profile", "current_stable_regime", "overall_fit_evidence", "10d_median_forward_return", "10d_benchmark_excess_median", "sample_count"]),
    ])


def render_portfolio_fit_report(payload: dict) -> str:
    return "\n".join([
        "# Current Portfolio Style-Regime Fit",
        "",
        f"- current_stable_regime: {payload.get('current_stable_regime')}",
        f"- conflict_count: {payload.get('conflict_count')}",
        f"- regime_style_concentration: {payload.get('regime_style_concentration')}",
        "",
        _markdown_table(payload.get("rows", []), ["symbol", "name", "current_weight", "style_profile", "structural_risk_profile", "realized_risk_profile", "overall_fit_evidence", "fit_interpretation"]),
    ])


def render_interaction_report(payload: dict) -> str:
    return "\n".join([
        "# Style Fit x Signal Interaction",
        "",
        f"- fit_has_incremental_signal_value: {payload.get('fit_has_incremental_signal_value')}",
        f"- reason: {payload.get('incremental_signal_reason')}",
        "",
        _markdown_table(payload.get("rows", []), ["signal_strength_bucket", "style_fit_evidence", "forward_horizon", "sample_count", "median_forward_return", "positive_rate"]),
    ])


def render_phase_decision_report(decision: dict) -> str:
    return "\n".join([
        "# Style-Regime Fit Phase Decision",
        "",
        f"- style_fit_has_historical_support: {decision.get('style_fit_has_historical_support')}",
        f"- style_fit_has_incremental_signal_value: {decision.get('style_fit_has_incremental_signal_value')}",
        f"- current_buy_top10_has_regime_conflict: {decision.get('current_buy_top10_has_regime_conflict')}",
        f"- current_portfolio_has_regime_conflict: {decision.get('current_portfolio_has_regime_conflict')}",
        f"- ready_for_fit_shadow_observation: {decision.get('ready_for_fit_shadow_observation')}",
        f"- ready_for_adjusted_preview_research: {decision.get('ready_for_adjusted_preview_research')}",
        f"- ready_for_preview: {decision.get('ready_for_preview')}",
        f"- ready_for_execution: {decision.get('ready_for_execution')}",
        f"- reason: {decision.get('decision_reason')}",
    ])


def render_phase_report(phase: dict) -> str:
    return "\n".join([
        "# Regime Layer Phase 3 - Style-Regime Fit Research",
        "",
        "本报告只做 research-only / shadow-only 风格适配研究，不修改 BUY ranking、不接执行层。",
        "",
        f"- selected stable regime candidate: {phase.get('selected_stable_regime_candidate')}",
        f"- current stable regime: {phase.get('current_stable_regime')}",
        f"- replay range: {phase.get('replay_range')}",
        f"- ready_for_adjusted_preview_research: {phase.get('phase_decision', {}).get('ready_for_adjusted_preview_research')}",
        f"- ready_for_preview: {phase.get('phase_decision', {}).get('ready_for_preview')}",
        f"- ready_for_execution: {phase.get('phase_decision', {}).get('ready_for_execution')}",
        "",
        "## Support by Regime",
        json.dumps(phase.get("support_by_regime", {}), ensure_ascii=False, indent=2),
        "",
        "## Current BUY Top10 Fit Counts",
        json.dumps(phase.get("current_buy_top10_fit", {}).get("counts", {}), ensure_ascii=False, indent=2),
        "",
        "## Current Portfolio Fit Counts",
        json.dumps(phase.get("current_portfolio_fit", {}).get("counts", {}), ensure_ascii=False, indent=2),
        "",
        "## Safety",
        "- research_only=true",
        "- shadow_only=true",
        "- ready_for_execution=false",
        "- forward return is label only",
    ])


def _summary_lookup(summary: dict) -> dict[tuple[str, str], dict]:
    return {(row["regime"], row["style_profile"]): row for row in summary.get("rows", [])}


def _benchmark_returns_from_replay(row: pd.Series) -> dict[int, float | None]:
    return {h: row.get(f"benchmark_return_{h}d") for h in HORIZONS}


def _read_replay() -> pd.DataFrame:
    df = pd.read_csv(STABILIZATION_REPLAY_CSV)
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return df


def _read_profile() -> pd.DataFrame:
    df = pd.read_csv(PROFILE_CSV)
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    return df


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_sanitize(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def _evidence_counts(rows: list[dict], key: str) -> dict[str, int]:
    counts = {name: 0 for name in ["SUPPORTED", "WEAK_SUPPORT", "NEUTRAL", "WEAK_CONFLICT", "CONFLICT", "INSUFFICIENT"]}
    for row in rows:
        value = str(row.get(key, "INSUFFICIENT"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _style_concentration(rows: list[dict]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        style = str(row.get("style_profile", "UNKNOWN"))
        counts[style] = counts.get(style, 0) + 1
    top = max(counts, key=counts.get) if counts else ""
    return {"counts": counts, "top_style": top, "top_style_count": counts.get(top, 0) if top else 0}


def _fit_interpretation(symbol: str, style: str, regime: str, fit: dict) -> str:
    evidence = fit.get("overall_fit_evidence", "INSUFFICIENT")
    if evidence in {"SUPPORTED", "WEAK_SUPPORT"}:
        return f"{symbol} style={style} has {evidence} fit under {regime}; research-only, no execution change."
    if evidence in {"CONFLICT", "WEAK_CONFLICT"}:
        return f"{symbol} style={style} has {evidence} under {regime}; signal can be strong but regime fit is a research caution."
    return f"{symbol} style={style} is {evidence} under {regime}; keep observation."


def signal_bucket(score: float) -> str:
    if score >= 75:
        return "STRONG"
    if score >= 55:
        return "MEDIUM"
    return "WEAK"


def _fit_rules() -> dict[str, Any]:
    return {
        "minimum_sample_count": MIN_SAMPLE_COUNT,
        "SUPPORTED": "sample ok; benchmark_excess_median > 0; median_forward_return > 0; positive_rate >= 55%",
        "WEAK_SUPPORT": "sample ok; at least two positive criteria",
        "NEUTRAL": "sample ok; no stable positive or negative direction",
        "WEAK_CONFLICT": "sample ok; at least two negative criteria",
        "CONFLICT": "sample ok; benchmark_excess_median < 0; median_forward_return < 0; positive_rate <= 45%",
        "INSUFFICIENT": f"sample_count < {MIN_SAMPLE_COUNT}",
    }


def _markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int | None = None) -> str:
    data = rows[:limit] if limit else rows
    if not data:
        return "_No rows._"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in data:
        lines.append("| " + " | ".join(_format_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.6f}".rstrip("0").rstrip(".")
    if value is None:
        return ""
    return str(value).replace("|", "/")


def _mean(values: list[float]) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(sum(clean) / len(clean), 6) if clean else None


def _median(values: list[float]) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(float(np.median(clean)), 6) if clean else None


def _percentile(values: list[float], q: float) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(float(np.percentile(clean, q)), 6) if clean else None


def _worst_tail_mean(values: list[float], tail_pct: float) -> float | None:
    clean = sorted(float(v) for v in values if pd.notna(v))
    if not clean:
        return None
    n = max(1, int(len(clean) * tail_pct))
    return round(sum(clean[:n]) / n, 6)


def _float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return fallback
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return fallback
        return out
    except (TypeError, ValueError):
        return fallback


def _fmt(value: Any) -> str:
    v = _float(value, fallback=float("nan"))
    if pd.isna(v):
        return "N/A"
    return f"{v:.6f}".rstrip("0").rstrip(".")


def _safety_payload() -> dict[str, bool]:
    return {
        "broker_api_enabled": False,
        "real_trade_enabled": False,
        "real_account_read_enabled": False,
        "paper_trade_engine_modified": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "buy_ranking_modified": False,
        "market_regime_modified": False,
        "selected_shadow_regime_modified": False,
        "adjusted_preview_modified": False,
        "forward_return_label_only": True,
        "research_only": True,
        "shadow_only": True,
        "ready_for_execution": False,
    }


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if pd.isna(value) if not isinstance(value, (str, bool)) else False:
        return None
    return value


if __name__ == "__main__":
    main()
