"""Research-only market regime stabilization candidates.

This module treats the existing normalized market regime replay as the raw
baseline and evaluates point-in-time stabilization candidates. It does not
modify market_regime, BUY ranking, adjusted preview, paper trades, paper
positions, or execution code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import phase4c_alpha_common as common
import market_regime_replay as phase2
from config import DATA_DIR, REPORT_DIR


RAW_REPLAY_CSV = DATA_DIR / "market_regime_replay.csv"
PROFILE_CSV = REPORT_DIR / "etf_risk_profile.csv"
STABILIZATION_REPLAY_CSV = DATA_DIR / "market_regime_stabilization_replay.csv"
STABILIZATION_MD = REPORT_DIR / "market_regime_stabilization.md"
STABILIZATION_JSON = REPORT_DIR / "market_regime_stabilization.json"
STABILIZATION_CSV = REPORT_DIR / "market_regime_stabilization.csv"
SOURCE_AUDIT_MD = REPORT_DIR / "regime_stabilization_source_audit.md"
SOURCE_AUDIT_JSON = REPORT_DIR / "regime_stabilization_source_audit.json"
COMPARISON_MD = REPORT_DIR / "regime_stabilization_comparison.md"
COMPARISON_JSON = REPORT_DIR / "regime_stabilization_comparison.json"
COMPARISON_CSV = REPORT_DIR / "regime_stabilization_comparison.csv"
LAG_MD = REPORT_DIR / "regime_stabilization_detection_lag.md"
LAG_JSON = REPORT_DIR / "regime_stabilization_detection_lag.json"
LAG_CSV = REPORT_DIR / "regime_stabilization_detection_lag.csv"
STYLE_MD = REPORT_DIR / "stabilized_regime_style_forward_return.md"
STYLE_JSON = REPORT_DIR / "stabilized_regime_style_forward_return.json"
STYLE_CSV = REPORT_DIR / "stabilized_regime_style_forward_return.csv"
STRUCTURAL_MD = REPORT_DIR / "stabilized_regime_structural_risk_check.md"
STRUCTURAL_JSON = REPORT_DIR / "stabilized_regime_structural_risk_check.json"
DECISION_MD = REPORT_DIR / "regime_stabilization_candidate_decision.md"
DECISION_JSON = REPORT_DIR / "regime_stabilization_candidate_decision.json"
PHASE_MD = REPORT_DIR / "regime_layer_phase2_5_stabilization.md"
PHASE_JSON = REPORT_DIR / "regime_layer_phase2_5_stabilization.json"

CANDIDATES = ["RAW", "CONFIRM_2D", "CONFIRM_3D", "ASYMMETRIC_CONFIRM"]
REGIMES = ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]
HORIZONS = [1, 3, 5, 10, 20]
SCORE_WEIGHTS = {
    "whipsaw_reduction": 0.25,
    "median_duration_gain": 0.15,
    "switch_reduction": 0.10,
    "detection_lag_score": 0.20,
    "missed_segment_score": 0.10,
    "style_fit_preservation": 0.10,
    "style_fit_clarity": 0.10,
}
ASYMMETRIC_CONFIRM_DAYS = {
    ("DEFENSIVE", "OFFENSIVE"): 3,
    ("DEFENSIVE", "NEUTRAL"): 2,
    ("NEUTRAL", "OFFENSIVE"): 3,
    ("NEUTRAL", "DEFENSIVE"): 2,
    ("OFFENSIVE", "NEUTRAL"): 2,
    ("OFFENSIVE", "DEFENSIVE"): 2,
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = _read_raw_replay()
    profile = _read_profile()
    source_audit = build_source_audit(raw_df, profile)
    replay_df = build_stabilized_replay(raw_df)
    comparison = build_comparison(replay_df)
    lag = build_detection_lag(replay_df)
    context = common.load_context()
    forward_rows = build_forward_rows(replay_df, profile, context)
    style = aggregate_forward(forward_rows, ["candidate", "regime", "style_profile"])
    structural = aggregate_forward(forward_rows, ["candidate", "regime", "structural_risk_profile"])
    scores = build_candidate_scores(comparison, lag, style)
    decision = build_decision(replay_df, comparison, lag, style, structural, scores)
    phase = build_phase_payload(source_audit, comparison, lag, style, structural, scores, decision, replay_df)

    replay_df.to_csv(STABILIZATION_REPLAY_CSV, index=False)
    replay_df.to_csv(STABILIZATION_CSV, index=False)
    STABILIZATION_JSON.write_text(_json_dumps({"generated_at": _now(), "rows": replay_df.to_dict(orient="records"), "research_only": True, "execution_allowed": False}), encoding="utf-8")
    STABILIZATION_MD.write_text(render_stabilization_report(replay_df, decision), encoding="utf-8")
    SOURCE_AUDIT_JSON.write_text(_json_dumps(source_audit), encoding="utf-8")
    SOURCE_AUDIT_MD.write_text(render_source_audit(source_audit), encoding="utf-8")
    COMPARISON_JSON.write_text(_json_dumps(comparison), encoding="utf-8")
    pd.DataFrame(comparison["rows"]).to_csv(COMPARISON_CSV, index=False)
    COMPARISON_MD.write_text(render_comparison_report(comparison), encoding="utf-8")
    LAG_JSON.write_text(_json_dumps(lag), encoding="utf-8")
    pd.DataFrame(lag["rows"]).to_csv(LAG_CSV, index=False)
    LAG_MD.write_text(render_lag_report(lag), encoding="utf-8")
    STYLE_JSON.write_text(_json_dumps(style), encoding="utf-8")
    pd.DataFrame(style["rows"]).to_csv(STYLE_CSV, index=False)
    STYLE_MD.write_text(render_forward_report("Stabilized Regime Style Forward Return", style, ["candidate", "regime", "style_profile"]), encoding="utf-8")
    STRUCTURAL_JSON.write_text(_json_dumps(structural), encoding="utf-8")
    STRUCTURAL_MD.write_text(render_structural_report(structural), encoding="utf-8")
    DECISION_JSON.write_text(_json_dumps(decision), encoding="utf-8")
    DECISION_MD.write_text(render_decision_report(decision), encoding="utf-8")
    PHASE_JSON.write_text(_json_dumps(phase), encoding="utf-8")
    PHASE_MD.write_text(render_phase_report(phase), encoding="utf-8")

    print(f"market_regime_stabilization rows: {len(replay_df)}")
    print(f"selected_candidate: {decision.get('selected_candidate')}")
    print(f"current_raw_regime: {decision.get('current_raw_regime')}")
    print(f"current_shadow_regime: {decision.get('current_selected_shadow_regime')}")
    print(f"written: {PHASE_MD}")


def build_source_audit(raw_df: pd.DataFrame, profile: pd.DataFrame) -> dict[str, Any]:
    sorted_dates = pd.to_datetime(raw_df["date"], errors="coerce").dropna()
    duplicated_dates = int(raw_df["date"].duplicated().sum()) if "date" in raw_df else 0
    monotonic = bool(sorted_dates.is_monotonic_increasing)
    unique_regimes = sorted(raw_df.get("normalized_regime", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    label_cols = [col for col in raw_df.columns if col.startswith("benchmark_return_")]
    return {
        "generated_at": _now(),
        "input_files": {
            "raw_replay_csv": str(RAW_REPLAY_CSV),
            "raw_replay_json": str(REPORT_DIR / "market_regime_replay.json"),
            "phase2_stability_json": str(REPORT_DIR / "market_regime_stability.json"),
            "phase2_style_forward_csv": str(REPORT_DIR / "regime_style_forward_return.csv"),
            "phase2_decision_json": str(REPORT_DIR / "market_regime_audit_decision.json"),
            "etf_risk_profile_csv": str(PROFILE_CSV),
        },
        "raw_replay_rows": int(len(raw_df)),
        "raw_replay_start": str(raw_df["date"].iloc[0]) if not raw_df.empty else "",
        "raw_replay_end": str(raw_df["date"].iloc[-1]) if not raw_df.empty else "",
        "date_order_is_monotonic": monotonic,
        "duplicate_date_count": duplicated_dates,
        "normalized_regime_values": unique_regimes,
        "normalized_regime_mapping": {"risk_on": "OFFENSIVE", "neutral": "NEUTRAL", "risk_off": "DEFENSIVE"},
        "required_regimes_present": all(regime in unique_regimes for regime in REGIMES),
        "forward_return_label_columns": label_cols,
        "forward_returns_are_labels_only": True,
        "replay_is_point_in_time": True,
        "point_in_time_note": "Phase 2 raw replay was produced from row_on_date <= T. Phase 2.5 only transforms known raw regime states through confirmation rules.",
        "phase2_raw_regime_modified": False,
        "profile_rows": int(len(profile)),
        "research_only": True,
        "execution_allowed": False,
    }


def build_stabilized_replay(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["date"] = df["date"].astype(str)
    raw = df["normalized_regime"].astype(str).tolist()
    confirm2, pending2, days2 = _confirm_n(raw, 2)
    confirm3, pending3, days3 = _confirm_n(raw, 3)
    asym, pending_d, days_d = _confirm_asymmetric(raw)
    out = pd.DataFrame({
        "date": df["date"],
        "raw_regime": raw,
        "candidate_a_regime": raw,
        "candidate_b_regime": confirm2,
        "candidate_c_regime": confirm3,
        "candidate_d_regime": asym,
        "candidate_b_pending_state": pending2,
        "candidate_b_confirmation_days": days2,
        "candidate_c_pending_state": pending3,
        "candidate_c_confirmation_days": days3,
        "candidate_d_pending_state": pending_d,
        "candidate_d_confirmation_days": days_d,
        "raw_to_candidate_b_changed": [r != s for r, s in zip(raw, confirm2)],
        "raw_to_candidate_c_changed": [r != s for r, s in zip(raw, confirm3)],
        "raw_to_candidate_d_changed": [r != s for r, s in zip(raw, asym)],
        "research_only": True,
        "execution_allowed": False,
    })
    return out


def _confirm_n(raw: list[str], days_required: int) -> tuple[list[str], list[str], list[int]]:
    if not raw:
        return [], [], []
    stable = raw[0]
    pending = ""
    pending_days = 0
    stable_series: list[str] = []
    pending_series: list[str] = []
    day_series: list[int] = []
    for state in raw:
        if state == stable:
            pending = ""
            pending_days = 0
        else:
            if state == pending:
                pending_days += 1
            else:
                pending = state
                pending_days = 1
            if pending_days >= days_required:
                stable = state
                pending = ""
                pending_days = 0
        stable_series.append(stable)
        pending_series.append(pending)
        day_series.append(pending_days)
    return stable_series, pending_series, day_series


def _confirm_asymmetric(raw: list[str]) -> tuple[list[str], list[str], list[int]]:
    if not raw:
        return [], [], []
    stable = raw[0]
    pending = ""
    pending_days = 0
    stable_series: list[str] = []
    pending_series: list[str] = []
    day_series: list[int] = []
    for state in raw:
        if state == stable:
            pending = ""
            pending_days = 0
        else:
            required = ASYMMETRIC_CONFIRM_DAYS.get((stable, state), 2)
            if state == pending:
                pending_days += 1
            else:
                pending = state
                pending_days = 1
            if pending_days >= required:
                stable = state
                pending = ""
                pending_days = 0
        stable_series.append(stable)
        pending_series.append(pending)
        day_series.append(pending_days)
    return stable_series, pending_series, day_series


def build_comparison(replay_df: pd.DataFrame) -> dict[str, Any]:
    rows = []
    mapping = _candidate_columns()
    for candidate, col in mapping.items():
        stats = _state_stability_stats(replay_df[["date", col]].rename(columns={col: "regime"}))
        row = {"candidate": candidate, **stats, "research_only": True, "execution_allowed": False}
        rows.append(row)
    raw = next((row for row in rows if row["candidate"] == "RAW"), {})
    for row in rows:
        row["switch_reduction_vs_raw"] = _safe_ratio(_float(raw.get("regime_switch_count")) - _float(row.get("regime_switch_count")), _float(raw.get("regime_switch_count")))
        row["three_day_whipsaw_reduction_vs_raw"] = _safe_ratio(_float(raw.get("three_day_whipsaw_count")) - _float(row.get("three_day_whipsaw_count")), _float(raw.get("three_day_whipsaw_count")))
        row["median_duration_gain_vs_raw"] = _safe_ratio(_float(row.get("median_regime_duration")) - _float(raw.get("median_regime_duration")), max(_float(raw.get("median_regime_duration")), 1.0))
        row["distribution_distortion"] = _distribution_distortion(row, raw)
    return {
        "generated_at": _now(),
        "rows": rows,
        "baseline_candidate": "RAW",
        "research_only": True,
        "execution_allowed": False,
    }


def _state_stability_stats(df: pd.DataFrame) -> dict[str, Any]:
    runs = _runs(df["date"].astype(str).tolist(), df["regime"].astype(str).tolist())
    durations = [run["duration"] for run in runs]
    total = int(len(df))
    counts = df["regime"].value_counts().to_dict()
    out = {
        "regime_switch_count": max(len(runs) - 1, 0),
        "average_regime_duration": _mean(durations),
        "median_regime_duration": _median(durations),
        "max_regime_duration": max(durations) if durations else 0,
        "one_day_reversal_count": sum(1 for run in runs if run["duration"] == 1),
        "three_day_whipsaw_count": sum(1 for run in runs if run["duration"] <= 3),
        "five_day_whipsaw_count": sum(1 for run in runs if run["duration"] <= 5),
    }
    for regime in REGIMES:
        c = int(counts.get(regime, 0))
        out[f"{regime}_day_count"] = c
        out[f"{regime}_percentage"] = c / total if total else 0.0
    out["dominant_regime_percentage"] = max((out[f"{regime}_percentage"] for regime in REGIMES), default=0.0)
    out["distribution_extreme_distortion"] = out["dominant_regime_percentage"] >= 0.80
    return out


def _runs(dates: list[str], regimes: list[str]) -> list[dict[str, Any]]:
    if not regimes:
        return []
    runs = []
    current = regimes[0]
    start = dates[0]
    duration = 0
    end = dates[0]
    for date, regime in zip(dates, regimes):
        if regime == current:
            duration += 1
            end = date
            continue
        runs.append({"regime": current, "start_date": start, "end_date": end, "duration": duration})
        current = regime
        start = date
        end = date
        duration = 1
    runs.append({"regime": current, "start_date": start, "end_date": end, "duration": duration})
    return runs


def build_detection_lag(replay_df: pd.DataFrame) -> dict[str, Any]:
    raw_segments = _runs(replay_df["date"].astype(str).tolist(), replay_df["raw_regime"].astype(str).tolist())
    rows = []
    date_to_idx = {date: idx for idx, date in enumerate(replay_df["date"].astype(str).tolist())}
    for segment in raw_segments:
        start_idx = date_to_idx[segment["start_date"]]
        end_idx = date_to_idx[segment["end_date"]]
        target = segment["regime"]
        for candidate, col in _candidate_columns().items():
            values = replay_df[col].astype(str).iloc[start_idx:end_idx + 1].tolist()
            dates = replay_df["date"].astype(str).iloc[start_idx:end_idx + 1].tolist()
            detection_date = ""
            lag_days: int | None = None
            for offset, (date, value) in enumerate(zip(dates, values)):
                if value == target:
                    detection_date = date
                    lag_days = offset
                    break
            missed = lag_days is None
            rows.append({
                "raw_segment_start": segment["start_date"],
                "raw_segment_end": segment["end_date"],
                "raw_regime": target,
                "candidate": candidate,
                "candidate_detection_date": detection_date,
                "detection_lag_trading_days": lag_days if lag_days is not None else "",
                "segment_duration": segment["duration"],
                "candidate_missed_segment": bool(missed),
                "research_only": True,
                "execution_allowed": False,
            })
    summary = _lag_summary(rows)
    return {
        "generated_at": _now(),
        "rows": rows,
        "summary": summary,
        "research_only": True,
        "execution_allowed": False,
    }


def _lag_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for candidate in CANDIDATES:
        c_rows = [row for row in rows if row["candidate"] == candidate]
        summary[candidate] = _lag_stats(c_rows)
        by_regime = {}
        for regime in REGIMES:
            by_regime[regime] = _lag_stats([row for row in c_rows if row["raw_regime"] == regime])
        summary[candidate]["by_regime"] = by_regime
    return summary


def _lag_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [_float(row.get("detection_lag_trading_days"), fallback=float("nan")) for row in rows if row.get("detection_lag_trading_days") != ""]
    values = [value for value in values if pd.notna(value)]
    missed = sum(1 for row in rows if row.get("candidate_missed_segment"))
    return {
        "segment_count": len(rows),
        "average_detection_lag": _mean(values),
        "median_detection_lag": _median(values),
        "p90_detection_lag": _percentile(values, 90),
        "missed_segment_count": missed,
        "missed_segment_ratio": missed / len(rows) if rows else 0.0,
    }


def build_forward_rows(replay_df: pd.DataFrame, profile: pd.DataFrame, context: dict) -> list[dict[str, Any]]:
    if replay_df.empty or profile.empty:
        return []
    profile_map = profile.set_index(profile["symbol"].astype(str)).to_dict(orient="index")
    bench_returns_by_date = {
        str(row["date"]): {h: row.get(f"benchmark_return_{h}d") for h in HORIZONS}
        for _, row in _read_raw_replay().iterrows()
    }
    rows = []
    for _, replay in replay_df.iterrows():
        date_text = str(replay["date"])
        date = pd.Timestamp(date_text)
        for symbol in context["price_data"]:
            profile_row = profile_map.get(str(symbol), {})
            if not profile_row:
                continue
            for h in HORIZONS:
                fwd = phase2._forward_return(str(symbol), date, h, context)
                if fwd is None:
                    continue
                bench = bench_returns_by_date.get(date_text, {}).get(h)
                for candidate, col in _candidate_columns().items():
                    rows.append({
                        "date": date_text,
                        "candidate": candidate,
                        "regime": replay.get(col),
                        "symbol": str(symbol),
                        "name": profile_row.get("name", symbol),
                        "style_profile": profile_row.get("style_profile", "UNKNOWN"),
                        "structural_risk_profile": profile_row.get("structural_risk_profile", "UNKNOWN"),
                        "forward_horizon": h,
                        "forward_return": fwd,
                        "benchmark_forward_return": bench,
                        "benchmark_excess_return": fwd - bench if bench is not None and not pd.isna(bench) else None,
                        "forward_return_is_label_only": True,
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
        "rows": sorted(out, key=lambda row: tuple(str(row.get(col, "")) for col in group_cols) + (int(row.get("forward_horizon", 0)),)),
        "research_only": True,
        "execution_allowed": False,
    }


def build_candidate_scores(comparison: dict, lag: dict, style: dict) -> dict[str, Any]:
    comparison_map = {row["candidate"]: row for row in comparison.get("rows", [])}
    lag_summary = lag.get("summary", {})
    raw_clarity = _style_fit_clarity(style, "RAW")
    rows = []
    for candidate in CANDIDATES:
        comp = comparison_map.get(candidate, {})
        lag_stats = lag_summary.get(candidate, {})
        clarity = _style_fit_clarity(style, candidate)
        features = {
            "whipsaw_reduction": _clamp01(_float(comp.get("three_day_whipsaw_reduction_vs_raw"))),
            "median_duration_gain": _clamp01(_float(comp.get("median_duration_gain_vs_raw")) / 3.0),
            "switch_reduction": _clamp01(_float(comp.get("switch_reduction_vs_raw"))),
            "detection_lag_score": _clamp01(1.0 - _float(lag_stats.get("average_detection_lag")) / 5.0),
            "missed_segment_score": _clamp01(1.0 - _float(lag_stats.get("missed_segment_ratio"))),
            "style_fit_preservation": _clamp01(clarity / raw_clarity) if raw_clarity > 0 else 0.0,
            "style_fit_clarity": _clamp01(clarity / 0.02),
        }
        score = sum(features[key] * weight for key, weight in SCORE_WEIGHTS.items()) * 100
        rows.append({
            "candidate": candidate,
            **features,
            "style_fit_clarity_raw_value": clarity,
            "candidate_research_score": round(score, 6),
            "research_only": True,
            "execution_allowed": False,
        })
    return {
        "generated_at": _now(),
        "weights": SCORE_WEIGHTS,
        "rows": sorted(rows, key=lambda row: row["candidate_research_score"], reverse=True),
        "research_only": True,
        "execution_allowed": False,
    }


def _style_fit_clarity(style: dict, candidate: str) -> float:
    rows = [row for row in style.get("rows", []) if row.get("candidate") == candidate and int(_float(row.get("forward_horizon"))) == 10]
    spreads = []
    for regime in REGIMES:
        values = [_float(row.get("benchmark_excess_mean"), fallback=float("nan")) for row in rows if row.get("regime") == regime]
        values = [value for value in values if pd.notna(value)]
        if len(values) >= 2:
            spreads.append(max(values) - min(values))
    return _mean(spreads)


def build_decision(replay_df: pd.DataFrame, comparison: dict, lag: dict, style: dict, structural: dict, scores: dict) -> dict[str, Any]:
    rows = scores.get("rows", [])
    comp_map = {row["candidate"]: row for row in comparison.get("rows", [])}
    lag_map = lag.get("summary", {})
    raw = comp_map.get("RAW", {})
    candidate_checks = {}
    for row in rows:
        candidate = row["candidate"]
        if candidate == "RAW":
            continue
        comp = comp_map.get(candidate, {})
        lag_stats = lag_map.get(candidate, {})
        style_preserved = row.get("style_fit_preservation", 0) >= 0.75
        lag_ok = _float(lag_stats.get("average_detection_lag")) <= 3.0 and _float(lag_stats.get("missed_segment_ratio")) <= 0.30
        whipsaw_ok = _float(comp.get("three_day_whipsaw_count")) < _float(raw.get("three_day_whipsaw_count"))
        median_ok = _float(comp.get("median_regime_duration")) > _float(raw.get("median_regime_duration"))
        distribution_ok = not bool(comp.get("distribution_extreme_distortion"))
        candidate_checks[candidate] = {
            "style_preserved": bool(style_preserved),
            "lag_ok": bool(lag_ok),
            "whipsaw_ok": bool(whipsaw_ok),
            "median_duration_ok": bool(median_ok),
            "distribution_ok": bool(distribution_ok),
            "selection_eligible": bool(style_preserved and lag_ok and whipsaw_ok and median_ok and distribution_ok),
        }
    eligible = [row for row in rows if row["candidate"] != "RAW" and candidate_checks.get(row["candidate"], {}).get("selection_eligible")]
    non_raw = [row for row in rows if row["candidate"] != "RAW"]
    selected = eligible[0]["candidate"] if eligible else (non_raw[0]["candidate"] if non_raw else "CONFIRM_2D")
    selected_comp = comp_map.get(selected, {})
    selected_lag = lag_map.get(selected, {})
    current = replay_df.tail(1).to_dict(orient="records")[0] if not replay_df.empty else {}
    selected_col = _candidate_columns().get(selected, "candidate_b_regime")
    selected_checks = candidate_checks.get(selected, {})
    style_preserved = bool(selected_checks.get("style_preserved"))
    lag_ok = bool(selected_checks.get("lag_ok"))
    whipsaw_ok = bool(selected_checks.get("whipsaw_ok"))
    median_ok = bool(selected_checks.get("median_duration_ok"))
    distribution_ok = bool(selected_checks.get("distribution_ok"))
    ready_style_fit = bool(style_preserved and lag_ok and whipsaw_ok and median_ok and distribution_ok)
    return {
        "generated_at": _now(),
        "selected_candidate": selected,
        "selected_candidate_reason": _selected_reason(selected, selected_comp, selected_lag, raw, style_preserved),
        "raw_regime_still_formal": True,
        "candidate_is_research_only": True,
        "candidate_is_shadow_only": True,
        "ready_for_style_regime_fit_research": ready_style_fit,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "current_date": current.get("date", ""),
        "current_raw_regime": current.get("raw_regime", ""),
        "current_CONFIRM_2D_regime": current.get("candidate_b_regime", ""),
        "current_CONFIRM_3D_regime": current.get("candidate_c_regime", ""),
        "current_ASYMMETRIC_CONFIRM_regime": current.get("candidate_d_regime", ""),
        "current_selected_shadow_regime": current.get(selected_col, ""),
        "selection_checks": selected_checks,
        "all_candidate_selection_checks": candidate_checks,
        "structural_risk_role": "risk_budget_input_not_candidate_selection_target",
        "research_only": True,
        "execution_allowed": False,
    }


def build_phase_payload(source_audit: dict, comparison: dict, lag: dict, style: dict, structural: dict, scores: dict, decision: dict, replay_df: pd.DataFrame) -> dict[str, Any]:
    comp_map = {row["candidate"]: row for row in comparison.get("rows", [])}
    lag_map = lag.get("summary", {})
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 2.5",
        "source_audit": source_audit,
        "candidate_definitions": {
            "RAW": "Candidate A; direct normalized_regime baseline.",
            "CONFIRM_2D": "Candidate B; switch only after two consecutive raw days in the new state.",
            "CONFIRM_3D": "Candidate C; switch only after three consecutive raw days in the new state.",
            "ASYMMETRIC_CONFIRM": {
                "description": "Candidate D; two-day defensive/neutral confirmation and three-day offensive confirmation from defensive/neutral.",
                "rules": {f"{a}->{b}": days for (a, b), days in ASYMMETRIC_CONFIRM_DAYS.items()},
            },
        },
        "replay_range": {
            "start": str(replay_df["date"].iloc[0]) if not replay_df.empty else "",
            "end": str(replay_df["date"].iloc[-1]) if not replay_df.empty else "",
            "rows": int(len(replay_df)),
        },
        "comparison": comparison,
        "detection_lag": lag,
        "candidate_scores": scores,
        "style_fit_summary": _style_summary(style),
        "structural_risk_check": _structural_summary(structural),
        "decision": decision,
        "quick_metrics": {
            candidate: {
                "switch_count": comp_map.get(candidate, {}).get("regime_switch_count"),
                "median_duration": comp_map.get(candidate, {}).get("median_regime_duration"),
                "whipsaw": comp_map.get(candidate, {}).get("three_day_whipsaw_count"),
                "avg_detection_lag": lag_map.get(candidate, {}).get("average_detection_lag"),
                "missed_segment_ratio": lag_map.get(candidate, {}).get("missed_segment_ratio"),
            }
            for candidate in CANDIDATES
        },
        "research_only": True,
        "shadow_only": True,
        "ready_for_execution": False,
        "safety": _safety_payload(),
    }


def _style_summary(style: dict) -> dict[str, Any]:
    out = {}
    rows = style.get("rows", [])
    for candidate in CANDIDATES:
        out[candidate] = {
            "style_fit_clarity_10d": _style_fit_clarity(style, candidate),
            "best_by_regime_10d": _best_by_regime(rows, candidate, "style_profile"),
        }
    return out


def _structural_summary(structural: dict) -> dict[str, Any]:
    rows = structural.get("rows", [])
    return {
        candidate: {
            "best_by_regime_10d": _best_by_regime(rows, candidate, "structural_risk_profile"),
            "selection_role": "validation_only_not_primary_target",
        }
        for candidate in CANDIDATES
    }


def _best_by_regime(rows: list[dict], candidate: str, group_col: str) -> dict[str, Any]:
    out = {}
    for regime in REGIMES:
        subset = [
            row for row in rows
            if row.get("candidate") == candidate and row.get("regime") == regime and int(_float(row.get("forward_horizon"))) == 10
        ]
        if subset:
            best = max(subset, key=lambda row: _float(row.get("benchmark_excess_mean"), fallback=-999))
            out[regime] = {
                group_col: best.get(group_col),
                "benchmark_excess_mean_10d": best.get("benchmark_excess_mean"),
                "sample_count": best.get("sample_count"),
            }
    return out


def render_source_audit(audit: dict) -> str:
    return "\n".join([
        "# Regime Stabilization Source Audit",
        "",
        "本报告只审计 Phase 2 输出作为 Phase 2.5 输入，不修改 raw market_regime。",
        "",
        f"- raw replay rows: {audit.get('raw_replay_rows')}",
        f"- raw replay range: {audit.get('raw_replay_start')} to {audit.get('raw_replay_end')}",
        f"- date order monotonic: {audit.get('date_order_is_monotonic')}",
        f"- duplicate date count: {audit.get('duplicate_date_count')}",
        f"- normalized regimes: {', '.join(audit.get('normalized_regime_values', []))}",
        f"- forward returns are labels only: {audit.get('forward_returns_are_labels_only')}",
        f"- replay is point-in-time: {audit.get('replay_is_point_in_time')}",
        f"- Phase 2 raw regime modified: {audit.get('phase2_raw_regime_modified')}",
        "",
        "## Safety",
        "- research_only=true",
        "- execution_allowed=false",
        "- no paper trade / position write",
    ])


def render_stabilization_report(replay_df: pd.DataFrame, decision: dict) -> str:
    latest = replay_df.tail(1).to_dict(orient="records")[0] if not replay_df.empty else {}
    rows = [
        "# Market Regime Stabilization Replay",
        "",
        "Candidate A/B/C/D 均为 research-only / shadow-only，不影响正式 market_regime。",
        "",
        f"- selected_candidate: {decision.get('selected_candidate')}",
        f"- current_date: {latest.get('date', '')}",
        f"- raw_regime: {latest.get('raw_regime', '')}",
        f"- CONFIRM_2D: {latest.get('candidate_b_regime', '')}",
        f"- CONFIRM_3D: {latest.get('candidate_c_regime', '')}",
        f"- ASYMMETRIC_CONFIRM: {latest.get('candidate_d_regime', '')}",
        "",
        "## Latest Rows",
        _markdown_table(replay_df.tail(10).to_dict(orient="records"), ["date", "raw_regime", "candidate_b_regime", "candidate_c_regime", "candidate_d_regime"]),
    ]
    return "\n".join(rows)


def render_comparison_report(comparison: dict) -> str:
    rows = comparison.get("rows", [])
    return "\n".join([
        "# Regime Stabilization Comparison",
        "",
        "比较 RAW / CONFIRM_2D / CONFIRM_3D / ASYMMETRIC_CONFIRM 的切换、持续期和 whipsaw。",
        "",
        _markdown_table(rows, [
            "candidate", "regime_switch_count", "median_regime_duration", "average_regime_duration",
            "three_day_whipsaw_count", "five_day_whipsaw_count",
            "OFFENSIVE_percentage", "NEUTRAL_percentage", "DEFENSIVE_percentage",
        ]),
        "",
        "research_only=true; execution_allowed=false.",
    ])


def render_lag_report(lag: dict) -> str:
    summary_rows = []
    for candidate, item in lag.get("summary", {}).items():
        summary_rows.append({
            "candidate": candidate,
            "average_detection_lag": item.get("average_detection_lag"),
            "median_detection_lag": item.get("median_detection_lag"),
            "p90_detection_lag": item.get("p90_detection_lag"),
            "missed_segment_count": item.get("missed_segment_count"),
            "missed_segment_ratio": item.get("missed_segment_ratio"),
        })
    return "\n".join([
        "# Regime Stabilization Detection Lag",
        "",
        "Detection lag 按 raw regime segment 计算；未回填第一天，严格 point-in-time。",
        "",
        _markdown_table(summary_rows, ["candidate", "average_detection_lag", "median_detection_lag", "p90_detection_lag", "missed_segment_count", "missed_segment_ratio"]),
    ])


def render_forward_report(title: str, payload: dict, cols: list[str]) -> str:
    rows = payload.get("rows", [])
    display = [row for row in rows if int(_float(row.get("forward_horizon"))) in {5, 10, 20}]
    return "\n".join([
        f"# {title}",
        "",
        "Forward return 仅为事后 label，不参与当日状态生成。",
        "",
        _markdown_table(display, cols + ["forward_horizon", "sample_count", "mean_forward_return", "positive_rate", "benchmark_excess_mean", "sample_status"]),
    ])


def render_structural_report(structural: dict) -> str:
    return "\n".join([
        "# Stabilized Regime Structural Risk Check",
        "",
        "Structural risk 本轮只做验证，不作为稳定候选选择核心目标。Phase 2 已显示 structural risk x regime 支持不足，后续更适合作为 risk budget 输入。",
        "",
        render_forward_report("Structural Risk x Stabilized Regime", structural, ["candidate", "regime", "structural_risk_profile"]),
    ])


def render_decision_report(decision: dict) -> str:
    return "\n".join([
        "# Regime Stabilization Candidate Decision",
        "",
        f"- selected_candidate: {decision.get('selected_candidate')}",
        f"- reason: {decision.get('selected_candidate_reason')}",
        f"- raw_regime_still_formal: {decision.get('raw_regime_still_formal')}",
        f"- candidate_is_research_only: {decision.get('candidate_is_research_only')}",
        f"- candidate_is_shadow_only: {decision.get('candidate_is_shadow_only')}",
        f"- ready_for_style_regime_fit_research: {decision.get('ready_for_style_regime_fit_research')}",
        f"- ready_for_preview: {decision.get('ready_for_preview')}",
        f"- ready_for_execution: {decision.get('ready_for_execution')}",
        "",
        "## Current Date",
        f"- date: {decision.get('current_date')}",
        f"- raw: {decision.get('current_raw_regime')}",
        f"- CONFIRM_2D: {decision.get('current_CONFIRM_2D_regime')}",
        f"- CONFIRM_3D: {decision.get('current_CONFIRM_3D_regime')}",
        f"- ASYMMETRIC_CONFIRM: {decision.get('current_ASYMMETRIC_CONFIRM_regime')}",
        f"- selected shadow: {decision.get('current_selected_shadow_regime')}",
    ])


def render_phase_report(phase: dict) -> str:
    metrics = phase.get("quick_metrics", {})
    decision = phase.get("decision", {})
    score_rows = phase.get("candidate_scores", {}).get("rows", [])
    return "\n".join([
        "# Regime Layer Phase 2.5 - Stabilization Research",
        "",
        "本报告是 research-only / shadow-only。现有 market_regime 保持正式 baseline，不接 BUY ranking、不接执行层。",
        "",
        "## Candidate Metrics",
        _markdown_table([
            {
                "candidate": candidate,
                "switch_count": item.get("switch_count"),
                "median_duration": item.get("median_duration"),
                "whipsaw": item.get("whipsaw"),
                "avg_detection_lag": item.get("avg_detection_lag"),
                "missed_segment_ratio": item.get("missed_segment_ratio"),
            }
            for candidate, item in metrics.items()
        ], ["candidate", "switch_count", "median_duration", "whipsaw", "avg_detection_lag", "missed_segment_ratio"]),
        "",
        "## Research Score",
        _markdown_table(score_rows, ["candidate", "candidate_research_score", "whipsaw_reduction", "median_duration_gain", "switch_reduction", "detection_lag_score", "missed_segment_score", "style_fit_preservation", "style_fit_clarity"]),
        "",
        "## Decision",
        f"- selected_candidate: {decision.get('selected_candidate')}",
        f"- selected_reason: {decision.get('selected_candidate_reason')}",
        f"- current_raw_regime: {decision.get('current_raw_regime')}",
        f"- current_selected_shadow_regime: {decision.get('current_selected_shadow_regime')}",
        f"- ready_for_style_regime_fit_research: {decision.get('ready_for_style_regime_fit_research')}",
        f"- ready_for_preview: {decision.get('ready_for_preview')}",
        f"- ready_for_execution: {decision.get('ready_for_execution')}",
        "",
        "## Safety",
        "- research_only=true",
        "- shadow_only=true",
        "- ready_for_execution=false",
        "- forward return is label only",
        "- no broker API / no real order / no paper trade mutation",
    ])


def _selected_reason(candidate: str, comp: dict, lag: dict, raw: dict, style_preserved: bool) -> str:
    return (
        f"{candidate} selected by fixed research score: switch {raw.get('regime_switch_count')} -> {comp.get('regime_switch_count')}, "
        f"median duration {raw.get('median_regime_duration')} -> {comp.get('median_regime_duration')}, "
        f"3d whipsaw {raw.get('three_day_whipsaw_count')} -> {comp.get('three_day_whipsaw_count')}, "
        f"avg detection lag {lag.get('average_detection_lag')}, missed ratio {lag.get('missed_segment_ratio')}; "
        f"style_fit_preserved={style_preserved}."
    )


def _candidate_columns() -> dict[str, str]:
    return {
        "RAW": "candidate_a_regime",
        "CONFIRM_2D": "candidate_b_regime",
        "CONFIRM_3D": "candidate_c_regime",
        "ASYMMETRIC_CONFIRM": "candidate_d_regime",
    }


def _read_raw_replay() -> pd.DataFrame:
    df = pd.read_csv(RAW_REPLAY_CSV)
    required = {"date", "normalized_regime"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required replay columns: {sorted(missing)}")
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return df


def _read_profile() -> pd.DataFrame:
    if not PROFILE_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(PROFILE_CSV)
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    return df


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


def _distribution_distortion(row: dict, raw: dict) -> float:
    return sum(abs(_float(row.get(f"{regime}_percentage")) - _float(raw.get(f"{regime}_percentage"))) for regime in REGIMES) / 2


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def _mean(values: list[float]) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(sum(clean) / len(clean), 6) if clean else None


def _median(values: list[float]) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(float(np.median(clean)), 6) if clean else None


def _percentile(values: list[float], q: float) -> float | None:
    clean = [float(v) for v in values if pd.notna(v)]
    return round(float(np.percentile(clean, q)), 6) if clean else None


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


def _clamp01(value: float) -> float:
    if pd.isna(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


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
        "adjusted_preview_modified": False,
        "forward_return_label_only": True,
        "research_only": True,
        "shadow_only": True,
        "ready_for_execution": False,
    }


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


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
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    if pd.isna(value) if not isinstance(value, (str, bool)) else False:
        return None
    return value


if __name__ == "__main__":
    main()
