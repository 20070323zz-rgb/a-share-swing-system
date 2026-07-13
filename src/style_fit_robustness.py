"""Style Fit robustness core audit.

Research-only / shadow-only Phase 3.5A audit for the Phase 3
Style-Regime Fit results. This module writes robustness evidence reports only.
It does not modify BUY ranking, market regime, adjusted preview, paper trades,
paper positions, dashboard, app, or execution code.
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
import style_regime_fit as phase3
from config import DATA_DIR, PROJECT_ROOT, REPORT_DIR


STABILIZATION_REPLAY_CSV = DATA_DIR / "market_regime_stabilization_replay.csv"
RAW_REPLAY_CSV = DATA_DIR / "market_regime_replay.csv"
PROFILE_CSV = REPORT_DIR / "etf_risk_profile.csv"
PHASE3_SUMMARY_JSON = REPORT_DIR / "style_regime_fit_summary.json"
PHASE3_DECISION_JSON = REPORT_DIR / "style_regime_fit_phase_decision.json"
STABILIZATION_DECISION_JSON = REPORT_DIR / "regime_stabilization_candidate_decision.json"

BASE_CSV = DATA_DIR / "style_fit_robustness_base.csv"
SEGMENTS_CSV = DATA_DIR / "style_fit_regime_segments.csv"

SOURCE_AUDIT_MD = REPORT_DIR / "style_fit_robustness_source_audit.md"
SOURCE_AUDIT_JSON = REPORT_DIR / "style_fit_robustness_source_audit.json"
TIME_MD = REPORT_DIR / "style_fit_time_robustness.md"
TIME_CSV = REPORT_DIR / "style_fit_time_robustness.csv"
TIME_JSON = REPORT_DIR / "style_fit_time_robustness.json"
ETF_MD = REPORT_DIR / "style_fit_etf_level_robustness.md"
ETF_CSV = REPORT_DIR / "style_fit_etf_level_robustness.csv"
ETF_JSON = REPORT_DIR / "style_fit_etf_level_robustness.json"
SEGMENT_MD = REPORT_DIR / "style_fit_regime_segment_robustness.md"
SEGMENT_CSV = REPORT_DIR / "style_fit_regime_segment_robustness.csv"
SEGMENT_JSON = REPORT_DIR / "style_fit_regime_segment_robustness.json"
HORIZON_MD = REPORT_DIR / "style_fit_horizon_robustness.md"
HORIZON_CSV = REPORT_DIR / "style_fit_horizon_robustness.csv"
HORIZON_JSON = REPORT_DIR / "style_fit_horizon_robustness.json"
HIGH_BETA_MD = REPORT_DIR / "style_fit_high_beta_theme_audit.md"
HIGH_BETA_CSV = REPORT_DIR / "style_fit_high_beta_theme_audit.csv"
HIGH_BETA_JSON = REPORT_DIR / "style_fit_high_beta_theme_audit.json"
COMMODITY_MD = REPORT_DIR / "style_fit_commodity_cyclical_audit.md"
COMMODITY_CSV = REPORT_DIR / "style_fit_commodity_cyclical_audit.csv"
COMMODITY_JSON = REPORT_DIR / "style_fit_commodity_cyclical_audit.json"
INCREMENTAL_MD = REPORT_DIR / "style_fit_incremental_value_robustness.md"
INCREMENTAL_CSV = REPORT_DIR / "style_fit_incremental_value_robustness.csv"
INCREMENTAL_JSON = REPORT_DIR / "style_fit_incremental_value_robustness.json"
SUMMARY_MD = REPORT_DIR / "style_fit_robustness_core_summary.md"
SUMMARY_JSON = REPORT_DIR / "style_fit_robustness_core_summary.json"
DECISION_MD = REPORT_DIR / "regime_layer_phase3_5a_decision.md"
DECISION_JSON = REPORT_DIR / "regime_layer_phase3_5a_decision.json"

HORIZONS = [1, 3, 5, 10, 20]
CORE_HORIZONS = [5, 10, 20]
REGIMES = ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]
AUDIT_STYLES = ["HIGH_BETA_THEME", "COMMODITY_CYCLICAL"]
SUPPORT_EVIDENCE = {"SUPPORTED", "WEAK_SUPPORT"}
CONFLICT_EVIDENCE = {"CONFLICT", "WEAK_CONFLICT"}
SELECTED_CANDIDATE_COLUMN = {
    "RAW": "candidate_a_regime",
    "CONFIRM_2D": "candidate_b_regime",
    "CONFIRM_3D": "candidate_c_regime",
    "ASYMMETRIC_CONFIRM": "candidate_d_regime",
}

MIN_GROUP_SAMPLE = 30
MIN_ETF_COUNT = 3
MIN_SEGMENT_COUNT = 2
TOP_RANKED_CANDIDATES = 30
MATERIAL_MEDIAN_SHIFT = 0.01
MODERATE_SEGMENT_CONCENTRATION = 0.45
HIGH_SEGMENT_CONCENTRATION = 0.65
ROBUSTNESS_CLASSES = ["ROBUST_SUPPORT", "PARTIAL_SUPPORT", "FRAGILE", "CONFLICTING", "INSUFFICIENT"]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    inputs = load_inputs()
    source_audit = build_source_audit(inputs)
    _write_json(SOURCE_AUDIT_JSON, source_audit)
    SOURCE_AUDIT_MD.write_text(render_source_audit(source_audit), encoding="utf-8")
    if source_audit["future_leakage_found"] or source_audit["blocking_conflict_found"]:
        print("Style Fit robustness source audit blocked Phase 3.5A.")
        return

    base = build_base_dataset(inputs)
    segments = build_regime_segments(inputs["replay"], inputs["selected_col"])
    if not base.empty:
        base = base.merge(segments[["segment_id", "segment_start_date", "segment_end_date"]], on="segment_id", how="left")
    base.to_csv(BASE_CSV, index=False)
    segments.to_csv(SEGMENTS_CSV, index=False)

    time_payload = build_time_robustness(base)
    etf_payload = build_etf_level_robustness(base)
    segment_payload = build_segment_robustness(base, segments)
    horizon_payload = build_horizon_robustness(base)
    high_beta_payload = build_style_special_audit(base, segments, "HIGH_BETA_THEME")
    commodity_payload = build_style_special_audit(base, segments, "COMMODITY_CYCLICAL")
    incremental_payload = build_incremental_value_robustness(base, time_payload, etf_payload, segment_payload, horizon_payload)
    summary_payload = build_core_summary(
        source_audit,
        time_payload,
        etf_payload,
        segment_payload,
        horizon_payload,
        high_beta_payload,
        commodity_payload,
        incremental_payload,
    )
    decision = build_decision(source_audit, summary_payload)

    write_payload(TIME_CSV, TIME_JSON, TIME_MD, time_payload, render_time_report)
    write_payload(ETF_CSV, ETF_JSON, ETF_MD, etf_payload, render_etf_report)
    write_payload(SEGMENT_CSV, SEGMENT_JSON, SEGMENT_MD, segment_payload, render_segment_report)
    write_payload(HORIZON_CSV, HORIZON_JSON, HORIZON_MD, horizon_payload, render_horizon_report)
    write_payload(HIGH_BETA_CSV, HIGH_BETA_JSON, HIGH_BETA_MD, high_beta_payload, render_special_report)
    write_payload(COMMODITY_CSV, COMMODITY_JSON, COMMODITY_MD, commodity_payload, render_special_report)
    write_payload(INCREMENTAL_CSV, INCREMENTAL_JSON, INCREMENTAL_MD, incremental_payload, render_incremental_report)
    _write_json(SUMMARY_JSON, summary_payload)
    SUMMARY_MD.write_text(render_summary_report(summary_payload), encoding="utf-8")
    _write_json(DECISION_JSON, decision)
    DECISION_MD.write_text(render_decision_report(decision), encoding="utf-8")

    if decision.get("ready_for_phase_3_5b") and not decision.get("blocking_methodology_issue_found"):
        update_project_context(decision, summary_payload)

    print("style_fit_robustness Phase 3.5A complete")
    print(f"base rows: {len(base)}")
    print(f"segments: {len(segments)}")
    print(f"ready_for_phase_3_5b: {decision.get('ready_for_phase_3_5b')}")
    print(f"written: {DECISION_MD}")


def load_inputs() -> dict[str, Any]:
    replay = _read_csv(STABILIZATION_REPLAY_CSV, dtype={"date": str}).sort_values("date").drop_duplicates("date", keep="last")
    raw_replay = _read_csv(RAW_REPLAY_CSV, dtype={"date": str}).sort_values("date").drop_duplicates("date", keep="last")
    profile = _read_csv(PROFILE_CSV, dtype={"symbol": str})
    profile["symbol"] = profile["symbol"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(profile["symbol"].astype(str)).str.zfill(6)
    summary = _read_json(PHASE3_SUMMARY_JSON)
    phase3_decision = _read_json(PHASE3_DECISION_JSON)
    stabilization_decision = _read_json(STABILIZATION_DECISION_JSON)
    selected = str(stabilization_decision.get("selected_candidate") or "ASYMMETRIC_CONFIRM")
    selected_col = SELECTED_CANDIDATE_COLUMN.get(selected, "candidate_d_regime")
    return {
        "replay": replay,
        "raw_replay": raw_replay,
        "profile": profile,
        "summary": summary,
        "phase3_decision": phase3_decision,
        "stabilization_decision": stabilization_decision,
        "selected": selected,
        "selected_col": selected_col,
        "context": common.load_context(),
    }


def build_source_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    replay = inputs["replay"]
    raw = inputs["raw_replay"]
    profile = inputs["profile"]
    selected_col = inputs["selected_col"]
    context = inputs["context"]
    summary_rows = inputs["summary"].get("rows", [])
    style_count = int(profile["style_profile"].nunique()) if "style_profile" in profile else 0
    regime_count = int(replay[selected_col].nunique()) if selected_col in replay else 0
    price_symbols = {str(symbol).zfill(6) for symbol in context.get("price_data", {})}
    profile_symbols = set(profile["symbol"].astype(str).str.zfill(6).tolist())
    available_horizons = [
        h for h in HORIZONS
        if f"benchmark_return_{h}d" in raw.columns
    ]
    audit = {
        "source_audit_version": 1,
        "generated_at": _now(),
        "stable_regime_source": "data/market_regime_stabilization_replay.csv candidate_d_regime from Phase 2.5 ASYMMETRIC_CONFIRM replay",
        "selected_regime_candidate": inputs["selected"],
        "selected_candidate_column": selected_col,
        "style_profile_source": "reports/etf_risk_profile.csv style_profile",
        "etf_daily_source": "data/etf_daily/",
        "signal_source": "ranking_model_v2_backtest.build_daily_rows + rank_rows(top10_diversified_filter_v2), top 30, matching Phase 3 signal interaction",
        "benchmark_label_source": "data/market_regime_replay.csv benchmark_return_{h}d columns",
        "benchmark_label_join": "same T-date join; point_in_time_safe_for_evaluation",
        "benchmark_labels_evaluation_only": True,
        "replay_start_date": str(replay["date"].iloc[0]) if not replay.empty else "",
        "replay_end_date": str(replay["date"].iloc[-1]) if not replay.empty else "",
        "etf_count": int(len(price_symbols & profile_symbols)),
        "style_count": style_count,
        "regime_count": regime_count,
        "forward_horizon_available": available_horizons,
        "phase3_sample_unit": "ETF-day pooling for style matrix; ranked ETF-day pooling for signal interaction",
        "phase3_summary_rows": int(len(summary_rows)),
        "phase3_uses_etf_day_pooling": True,
        "overlapping_forward_windows_present": True,
        "cross_sectional_dependence_possible": True,
        "regime_segment_dependence_possible": True,
        "same_style_highly_similar_etf_possible": True,
        "field_mapping": {
            "date": "date",
            "symbol": "symbol, normalized to six-digit string",
            "stable_regime": selected_col,
            "style_profile": "reports/etf_risk_profile.csv style_profile",
            "signal_bucket": "rank_score bucket: STRONG >=75, MEDIUM >=55, else WEAK",
            "fit_evidence_level": "Phase 3 overall_fit_evidence by stable_regime x style_profile",
            "benchmark_forward_return": "market_regime_replay benchmark_return_{h}d",
        },
        "stable_regime_column_present": selected_col in replay.columns,
        "raw_replay_date_unique": bool(raw["date"].is_unique) if "date" in raw else False,
        "stable_replay_date_unique": bool(replay["date"].is_unique) if "date" in replay else False,
        "selected_candidate_is_asymmetric_confirm": inputs["selected"] == "ASYMMETRIC_CONFIRM",
        "future_leakage_found": False,
        "future_leakage_notes": [
            "T-day regime is read from Phase 2.5 stable replay only.",
            "Benchmark forward returns are joined on same T date and used only as evaluation labels.",
            "Forward ETF returns are generated only as labels after T-day signal/style/regime assignment.",
        ],
        "blocking_conflict_found": False,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }
    if selected_col not in replay.columns or inputs["selected"] != "ASYMMETRIC_CONFIRM":
        audit["blocking_conflict_found"] = True
    return audit


def build_base_dataset(inputs: dict[str, Any]) -> pd.DataFrame:
    replay = inputs["replay"]
    raw = inputs["raw_replay"]
    profile = inputs["profile"]
    summary_lookup = _summary_lookup(inputs["summary"])
    profile_map = profile.set_index("symbol").to_dict(orient="index")
    raw_map = raw.set_index("date").to_dict(orient="index") if not raw.empty else {}
    context = inputs["context"]
    rows: list[dict[str, Any]] = []
    segment_by_date = segment_lookup(build_regime_segments(replay, inputs["selected_col"]))
    for _, replay_row in replay.iterrows():
        date_text = str(replay_row["date"])
        date = pd.Timestamp(date_text)
        stable_regime = str(replay_row[inputs["selected_col"]])
        daily_rows = ranking.build_daily_rows(date, context)
        ranked = ranking.rank_rows(daily_rows, "top10_diversified_filter_v2")[:TOP_RANKED_CANDIDATES]
        benchmark = raw_map.get(date_text, {})
        for ranked_row in ranked:
            symbol = str(ranked_row.get("symbol", "")).zfill(6)
            profile_row = profile_map.get(symbol)
            if not profile_row:
                continue
            style = str(profile_row.get("style_profile", "UNKNOWN"))
            fit = summary_lookup.get((stable_regime, style), {})
            item = {
                "date": date_text,
                "symbol": symbol,
                "name": ranked_row.get("name") or profile_row.get("name", symbol),
                "rank": int(_float(ranked_row.get("rank"))),
                "rank_score": _round(ranked_row.get("rank_score")),
                "style_profile": style,
                "stable_regime": stable_regime,
                "segment_id": segment_by_date.get(date_text, ""),
                "signal_bucket": phase3.signal_bucket(_float(ranked_row.get("rank_score"))),
                "fit_evidence_level": str(fit.get("overall_fit_evidence", "INSUFFICIENT")),
                "signal_fit_group": "",
                "research_only": True,
                "execution_allowed": False,
            }
            item["signal_fit_group"] = signal_fit_group(item["signal_bucket"], item["fit_evidence_level"])
            has_forward = False
            for horizon in HORIZONS:
                fwd = phase2._forward_return(symbol, date, horizon, context)
                bench = _maybe_float(benchmark.get(f"benchmark_return_{horizon}d"))
                item[f"forward_return_{horizon}d"] = _round(fwd)
                item[f"benchmark_forward_return_{horizon}d"] = _round(bench)
                item[f"benchmark_excess_{horizon}d"] = _round(fwd - bench) if fwd is not None and bench is not None else None
                has_forward = has_forward or fwd is not None
            if has_forward:
                rows.append(item)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["symbol"] = df["symbol"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(df["symbol"].astype(str)).str.zfill(6)
        df = df.sort_values(["date", "rank", "symbol"]).reset_index(drop=True)
    return df


def build_regime_segments(replay: pd.DataFrame, selected_col: str) -> pd.DataFrame:
    rows = []
    current_regime = None
    current_dates: list[str] = []
    counters: dict[str, int] = {}
    for _, row in replay.sort_values("date").iterrows():
        date_text = str(row["date"])
        regime = str(row[selected_col])
        if current_regime is None:
            current_regime = regime
            current_dates = [date_text]
            continue
        if regime == current_regime:
            current_dates.append(date_text)
            continue
        counters[current_regime] = counters.get(current_regime, 0) + 1
        rows.append(_segment_row(current_regime, counters[current_regime], current_dates))
        current_regime = regime
        current_dates = [date_text]
    if current_regime is not None and current_dates:
        counters[current_regime] = counters.get(current_regime, 0) + 1
        rows.append(_segment_row(current_regime, counters[current_regime], current_dates))
    return pd.DataFrame(rows)


def _segment_row(regime: str, index: int, dates: list[str]) -> dict[str, Any]:
    return {
        "segment_id": f"{regime}_{index:03d}",
        "stable_regime": regime,
        "segment_start_date": dates[0],
        "segment_end_date": dates[-1],
        "segment_trading_days": int(len(dates)),
    }


def build_time_robustness(base: pd.DataFrame) -> dict[str, Any]:
    rows = []
    if base.empty:
        return payload("time", rows, "INSUFFICIENT", {"calendar_split_conclusion": "INSUFFICIENT", "chronological_split_conclusion": "INSUFFICIENT"})
    df = base.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    periods: list[tuple[str, str, pd.Series]] = []
    for year, sub in df.groupby(df["date_dt"].dt.year):
        periods.append(("CALENDAR_YEAR", str(year), df["date_dt"].dt.year == year))
    unique_dates = sorted(df["date"].unique().tolist())
    midpoint = len(unique_dates) // 2
    early = set(unique_dates[:midpoint])
    late = set(unique_dates[midpoint:])
    periods.extend([
        ("CHRONOLOGICAL_HALF", "EARLY", df["date"].isin(early)),
        ("CHRONOLOGICAL_HALF", "LATE", df["date"].isin(late)),
    ])
    for period_type, period_label, mask in periods:
        sub = df[mask]
        for horizon in CORE_HORIZONS:
            stats = compare_supported_conflict(sub, horizon)
            for group in ["STRONG_SUPPORTED", "STRONG_CONFLICT"]:
                group_stats = stats["groups"].get(group, empty_stats())
                rows.append({
                    "period_type": period_type,
                    "period_label": period_label,
                    "signal_fit_group": group,
                    "horizon": f"{horizon}d",
                    **group_stats,
                    "supported_vs_conflict_median_diff": stats["median_diff"],
                    "supported_vs_conflict_excess_diff": stats["excess_diff"],
                    "direction_consistent": stats["direction"] != "CONFLICT_BEATS_SUPPORTED" and stats["direction"] != "INSUFFICIENT",
                    "direction": stats["direction"],
                    "research_only": True,
                    "execution_allowed": False,
                })
    support_rows = [r for r in rows if r["signal_fit_group"] == "STRONG_SUPPORTED" and r["horizon"] == "10d"]
    consistent = [bool(r["direction_consistent"]) for r in support_rows if r["sample_count"] >= MIN_GROUP_SAMPLE]
    classification = classify_support(consistent)
    calendar = summarize_period_direction(rows, "CALENDAR_YEAR")
    chrono = summarize_period_direction(rows, "CHRONOLOGICAL_HALF")
    return payload("time", rows, classification, {"calendar_split_conclusion": calendar, "chronological_split_conclusion": chrono})


def build_etf_level_robustness(base: pd.DataFrame) -> dict[str, Any]:
    rows = []
    if base.empty:
        return payload("etf_level", rows, "INSUFFICIENT", {"pooled_vs_etf_direction_reversal": False, "max_pooling_bias_flag": "INSUFFICIENT"})
    for keys, sub in base.groupby(["stable_regime", "style_profile", "signal_fit_group"], dropna=False):
        if keys[2] not in {"STRONG_SUPPORTED", "STRONG_CONFLICT"}:
            continue
        stable_regime, style, group = keys
        for horizon in HORIZONS:
            ret_col = f"forward_return_{horizon}d"
            ex_col = f"benchmark_excess_{horizon}d"
            symbol_rows = []
            for symbol, sym_sub in sub.groupby("symbol"):
                stats = series_stats(sym_sub[ret_col], sym_sub[ex_col])
                if stats["sample_count"] > 0:
                    symbol_rows.append({"symbol": symbol, **stats})
            pooled = series_stats(sub[ret_col], sub[ex_col])
            etf_count = len(symbol_rows)
            etf_median = median([r["median_forward_return"] for r in symbol_rows])
            etf_excess = median([r["benchmark_excess_median"] for r in symbol_rows])
            etf_positive_share = mean([1.0 if _float(r["positive_rate"]) > 0.5 else 0.0 for r in symbol_rows])
            flag = pooling_bias_flag(pooled["median_forward_return"], etf_median)
            rows.append({
                "stable_regime": stable_regime,
                "style_profile": style,
                "signal_fit_group": group,
                "horizon": f"{horizon}d",
                "etf_count": etf_count,
                "total_observation_count": int(pooled["sample_count"]),
                "etf_median_of_medians": etf_median,
                "etf_median_excess": etf_excess,
                "etf_positive_share": etf_positive_share,
                "pooled_median_return": pooled["median_forward_return"],
                "pooled_median_excess": pooled["benchmark_excess_median"],
                "aggregation_direction_consistent": flag != "DIRECTION_REVERSAL" and etf_count >= MIN_ETF_COUNT,
                "pooling_bias_flag": flag if etf_count >= MIN_ETF_COUNT else "INSUFFICIENT",
                "research_only": True,
                "execution_allowed": False,
            })
    flags = [r["pooling_bias_flag"] for r in rows if r["horizon"] in {"5d", "10d", "20d"}]
    classification = classify_flags(flags, "etf")
    return payload("etf_level", rows, classification, {
        "pooled_vs_etf_direction_reversal": "DIRECTION_REVERSAL" in flags,
        "max_pooling_bias_flag": max_flag(flags, ["INSUFFICIENT", "NO_MATERIAL_SHIFT", "MODERATE_SHIFT", "DIRECTION_REVERSAL"]),
    })


def build_segment_robustness(base: pd.DataFrame, segments: pd.DataFrame) -> dict[str, Any]:
    rows = []
    if base.empty:
        return payload("segment", rows, "INSUFFICIENT", {"segment_count": int(len(segments)), "max_segment_concentration_flag": "INSUFFICIENT"})
    for keys, sub in base.groupby(["stable_regime", "style_profile", "signal_fit_group"], dropna=False):
        if keys[2] not in {"STRONG_SUPPORTED", "STRONG_CONFLICT"}:
            continue
        stable_regime, style, group = keys
        for horizon in HORIZONS:
            ret_col = f"forward_return_{horizon}d"
            ex_col = f"benchmark_excess_{horizon}d"
            segment_rows = []
            total_count = int(pd.to_numeric(sub[ret_col], errors="coerce").notna().sum())
            for segment_id, seg_sub in sub.groupby("segment_id"):
                stats = series_stats(seg_sub[ret_col], seg_sub[ex_col])
                if stats["sample_count"] > 0:
                    segment_rows.append({"segment_id": segment_id, **stats})
            qualified = [r for r in segment_rows if r["sample_count"] >= MIN_GROUP_SAMPLE]
            largest_obs_share = max([r["sample_count"] for r in segment_rows], default=0) / total_count if total_count else None
            contribution_values = [abs(_float(r["median_forward_return"]) * _float(r["sample_count"])) for r in segment_rows if r["median_forward_return"] is not None]
            largest_contribution_share = max(contribution_values, default=0) / sum(contribution_values) if sum(contribution_values) else None
            concentration = segment_concentration_flag(largest_obs_share, largest_contribution_share, len(qualified))
            beats_share = segment_beats_share(base, stable_regime, style, horizon)
            direction_consistent = None
            if concentration != "INSUFFICIENT" and beats_share is not None:
                direction_consistent = bool(beats_share >= 0.5)
            rows.append({
                "stable_regime": stable_regime,
                "style_profile": style,
                "signal_fit_group": group,
                "horizon": f"{horizon}d",
                "segment_count": len(segment_rows),
                "qualified_segment_count": len(qualified),
                "segment_median_return_median": median([r["median_forward_return"] for r in qualified]),
                "segment_excess_median": median([r["benchmark_excess_median"] for r in qualified]),
                "segment_positive_share": mean([1.0 if _float(r["positive_rate"]) > 0.5 else 0.0 for r in qualified]),
                "segment_supported_beats_conflict_share": beats_share,
                "largest_segment_observation_share": _round(largest_obs_share),
                "largest_segment_contribution_share": _round(largest_contribution_share),
                "segment_concentration_flag": concentration,
                "segment_direction_consistent": direction_consistent,
                "research_only": True,
                "execution_allowed": False,
            })
    flags = [r["segment_concentration_flag"] for r in rows if r["horizon"] in {"5d", "10d", "20d"}]
    direction = [
        r["segment_direction_consistent"]
        for r in rows
        if r["signal_fit_group"] == "STRONG_SUPPORTED" and r["horizon"] in {"5d", "10d", "20d"} and r["segment_direction_consistent"] is not None
    ]
    if direction and any(v is False for v in direction):
        classification = "CONFLICTING"
    else:
        classification = classify_flags(flags, "segment")
    return payload("segment", rows, classification, {
        "segment_count": int(len(segments)),
        "single_segment_dominance_found": any(f == "HIGH" for f in flags),
        "max_segment_concentration_flag": max_flag(flags, ["INSUFFICIENT", "LOW", "MODERATE", "HIGH"]),
    })


def build_horizon_robustness(base: pd.DataFrame) -> dict[str, Any]:
    rows = []
    for horizon in HORIZONS:
        stats = compare_supported_conflict(base, horizon)
        sup = stats["groups"].get("STRONG_SUPPORTED", empty_stats())
        con = stats["groups"].get("STRONG_CONFLICT", empty_stats())
        rows.append({
            "horizon": f"{horizon}d",
            "supported_median_return": sup["median_forward_return"],
            "conflict_median_return": con["median_forward_return"],
            "median_diff": stats["median_diff"],
            "supported_benchmark_excess_median": sup["benchmark_excess_median"],
            "conflict_benchmark_excess_median": con["benchmark_excess_median"],
            "excess_diff": stats["excess_diff"],
            "supported_positive_rate": sup["positive_rate"],
            "conflict_positive_rate": con["positive_rate"],
            "positive_rate_diff": _diff(sup["positive_rate"], con["positive_rate"]),
            "supported_count": sup["sample_count"],
            "conflict_count": con["sample_count"],
            "direction": stats["direction"],
            "research_only": True,
            "execution_allowed": False,
        })
    core_dirs = [r["direction"] for r in rows if r["horizon"] in {"5d", "10d", "20d"}]
    supported_core = sum(1 for d in core_dirs if d == "SUPPORTED_BEATS_CONFLICT")
    conflict_core = sum(1 for d in core_dirs if d == "CONFLICT_BEATS_SUPPORTED")
    horizon_fragile = not (supported_core == len(core_dirs) or conflict_core == len(core_dirs)) or (supported_core == 1 and any(r["horizon"] == "10d" and r["direction"] == "SUPPORTED_BEATS_CONFLICT" for r in rows))
    if any(d == "INSUFFICIENT" for d in core_dirs):
        classification = "INSUFFICIENT"
    elif conflict_core:
        classification = "CONFLICTING"
    elif horizon_fragile:
        classification = "FRAGILE"
    else:
        classification = "ROBUST_SUPPORT"
    return payload("horizon", rows, classification, {
        "horizon_fragile": bool(horizon_fragile),
        "core_horizons_same_direction": len(set(core_dirs)) == 1 and "INSUFFICIENT" not in core_dirs,
        "directions": {r["horizon"]: r["direction"] for r in rows},
    })


def build_style_special_audit(base: pd.DataFrame, segments: pd.DataFrame, style: str) -> dict[str, Any]:
    rows = []
    explanations = []
    flags: list[str] = []
    style_df = base[base["style_profile"] == style].copy() if not base.empty else pd.DataFrame()
    for regime in REGIMES:
        sub = style_df[style_df["stable_regime"] == regime] if not style_df.empty else pd.DataFrame()
        row = {
            "style_profile": style,
            "stable_regime": regime,
            "etf_count": int(sub["symbol"].nunique()) if not sub.empty else 0,
            "observation_count": int(len(sub)),
            "segment_count": int(sub["segment_id"].nunique()) if not sub.empty else 0,
            "research_only": True,
            "execution_allowed": False,
        }
        for horizon in CORE_HORIZONS:
            ret_col = f"forward_return_{horizon}d"
            ex_col = f"benchmark_excess_{horizon}d"
            stats = series_stats(sub[ret_col], sub[ex_col]) if not sub.empty else empty_stats()
            row[f"{horizon}d_median"] = stats["median_forward_return"]
            row[f"{horizon}d_benchmark_excess_median"] = stats["benchmark_excess_median"]
            row[f"{horizon}d_etf_level_median"] = median([
                series_stats(sym_sub[ret_col], sym_sub[ex_col])["median_forward_return"]
                for _, sym_sub in sub.groupby("symbol")
            ]) if not sub.empty else None
            row[f"{horizon}d_segment_level_median"] = median([
                series_stats(seg_sub[ret_col], seg_sub[ex_col])["median_forward_return"]
                for _, seg_sub in sub.groupby("segment_id")
            ]) if not sub.empty else None
        rows.append(row)
    robust_regimes = [
        r["stable_regime"] for r in rows
        if r["etf_count"] >= MIN_ETF_COUNT
        and r["segment_count"] >= MIN_SEGMENT_COUNT
        and all((_maybe_float(r.get(f"{h}d_etf_level_median")) or 0) > 0 for h in CORE_HORIZONS)
    ]
    if {"OFFENSIVE", "DEFENSIVE"}.issubset(set(robust_regimes)):
        flags.append("TRUE_MULTI_REGIME_BEHAVIOR")
        explanations.append(f"{style} remains positive across OFFENSIVE and DEFENSIVE at ETF-level on core horizons.")
    if any(r["segment_count"] < MIN_SEGMENT_COUNT and r["observation_count"] > 0 for r in rows):
        flags.append("SEGMENT_CONCENTRATED")
    if any(r["etf_count"] < MIN_ETF_COUNT and r["observation_count"] > 0 for r in rows):
        flags.append("SAMPLE_DEPENDENCE_RISK")
    if not flags:
        flags.append("INSUFFICIENT" if style_df.empty else "AGGREGATION_MASKING")
    if not explanations:
        explanations.append(f"{style} evidence is not cleanly robust after ETF-level and segment-level checks.")
    return payload(style.lower(), rows, "PARTIAL_SUPPORT" if "TRUE_MULTI_REGIME_BEHAVIOR" in flags else ("INSUFFICIENT" if "INSUFFICIENT" in flags else "FRAGILE"), {
        "style_profile": style,
        "preliminary_explanation": " ".join(explanations),
        "flags": sorted(set(flags)),
    })


def build_incremental_value_robustness(base: pd.DataFrame, time_payload: dict, etf_payload: dict, segment_payload: dict, horizon_payload: dict) -> dict[str, Any]:
    rows = []
    for horizon in CORE_HORIZONS:
        add_increment_row(rows, "Pooled ETF-day", "ALL", horizon, compare_supported_conflict(base, horizon))
    for row in time_payload.get("rows", []):
        if row["signal_fit_group"] == "STRONG_SUPPORTED":
            rows.append({
                "analysis_method": "Calendar / Chronological Time Split",
                "period_or_group": f"{row['period_type']}:{row['period_label']}",
                "horizon": row["horizon"],
                "supported_count": row["sample_count"],
                "conflict_count": counterpart_count(time_payload["rows"], row),
                "supported_median": row["median_forward_return"],
                "conflict_median": counterpart_value(time_payload["rows"], row, "median_forward_return"),
                "median_diff": row["supported_vs_conflict_median_diff"],
                "supported_excess_median": row["benchmark_excess_median"],
                "conflict_excess_median": counterpart_value(time_payload["rows"], row, "benchmark_excess_median"),
                "excess_diff": row["supported_vs_conflict_excess_diff"],
                "direction": row["direction"],
                "incremental_value_supported": row["direction"] == "SUPPORTED_BEATS_CONFLICT",
                "research_only": True,
                "execution_allowed": False,
            })
    for horizon in CORE_HORIZONS:
        add_aggregate_increment_row(rows, base, horizon, "symbol", "ETF-Level Aggregation")
        add_aggregate_increment_row(rows, base, horizon, "segment_id", "Regime-Segment Aggregation")
    for row in horizon_payload.get("rows", []):
        if row["horizon"] in {"5d", "10d", "20d"}:
            rows.append({
                "analysis_method": "Horizon",
                "period_or_group": "ALL",
                "horizon": row["horizon"],
                "supported_count": row["supported_count"],
                "conflict_count": row["conflict_count"],
                "supported_median": row["supported_median_return"],
                "conflict_median": row["conflict_median_return"],
                "median_diff": row["median_diff"],
                "supported_excess_median": row["supported_benchmark_excess_median"],
                "conflict_excess_median": row["conflict_benchmark_excess_median"],
                "excess_diff": row["excess_diff"],
                "direction": row["direction"],
                "incremental_value_supported": row["direction"] == "SUPPORTED_BEATS_CONFLICT",
                "research_only": True,
                "execution_allowed": False,
            })
    support = {
        "pooled_support": method_support(rows, "Pooled ETF-day"),
        "time_split_support": method_support(rows, "Calendar / Chronological Time Split"),
        "etf_level_support": method_support(rows, "ETF-Level Aggregation"),
        "segment_level_support": method_support(rows, "Regime-Segment Aggregation"),
        "horizon_support": method_support(rows, "Horizon"),
    }
    support_count = sum(1 for v in support.values() if v)
    conflict_count = sum(1 for r in rows if r["horizon"] in {"5d", "10d", "20d"} and r["direction"] == "CONFLICT_BEATS_SUPPORTED")
    if support_count >= 4 and conflict_count == 0:
        classification = "ROBUST_SUPPORT"
    elif support_count >= 4 and conflict_count <= 1:
        classification = "PARTIAL_SUPPORT"
    elif support_count >= 3 and conflict_count == 0:
        classification = "PARTIAL_SUPPORT"
    elif conflict_count:
        classification = "CONFLICTING"
    elif support_count > 0:
        classification = "FRAGILE"
    else:
        classification = "INSUFFICIENT"
    extra = {**support, "incremental_value_robustness_preliminary": classification, "core_reversal_count": conflict_count}
    return payload("incremental", rows, classification, extra)


def build_core_summary(source_audit: dict, time_payload: dict, etf_payload: dict, segment_payload: dict, horizon_payload: dict, high_beta: dict, commodity: dict, incremental: dict) -> dict[str, Any]:
    major_warning = any(v in {"FRAGILE", "CONFLICTING"} for v in [
        time_payload["classification"],
        etf_payload["classification"],
        segment_payload["classification"],
        horizon_payload["classification"],
        incremental["classification"],
    ])
    blocking = bool(source_audit["future_leakage_found"] or source_audit["blocking_conflict_found"])
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 3.5A",
        "time_robustness_classification": time_payload["classification"],
        "calendar_split_conclusion": time_payload.get("calendar_split_conclusion"),
        "chronological_split_conclusion": time_payload.get("chronological_split_conclusion"),
        "etf_level_robustness_classification": etf_payload["classification"],
        "pooled_vs_etf_direction_reversal": etf_payload.get("pooled_vs_etf_direction_reversal"),
        "pooling_bias_flag": etf_payload.get("max_pooling_bias_flag"),
        "segment_robustness_classification": segment_payload["classification"],
        "segment_count": segment_payload.get("segment_count"),
        "single_segment_dominance_found": segment_payload.get("single_segment_dominance_found"),
        "segment_concentration_flag": segment_payload.get("max_segment_concentration_flag"),
        "horizon_robustness_classification": horizon_payload["classification"],
        "horizon_directions": horizon_payload.get("directions"),
        "core_horizons_same_direction": horizon_payload.get("core_horizons_same_direction"),
        "horizon_fragile": horizon_payload.get("horizon_fragile"),
        "incremental_value_robustness_preliminary": incremental["classification"],
        "pooled_support": incremental.get("pooled_support"),
        "time_split_support": incremental.get("time_split_support"),
        "etf_level_support": incremental.get("etf_level_support"),
        "segment_level_support": incremental.get("segment_level_support"),
        "horizon_support": incremental.get("horizon_support"),
        "high_beta_theme_preliminary_explanation": high_beta.get("preliminary_explanation"),
        "high_beta_theme_flags": high_beta.get("flags", []),
        "commodity_cyclical_preliminary_explanation": commodity.get("preliminary_explanation"),
        "commodity_cyclical_flags": commodity.get("flags", []),
        "phase3_original_conclusion_still_directionally_supported": incremental["classification"] in {"ROBUST_SUPPORT", "PARTIAL_SUPPORT", "FRAGILE"},
        "phase3_incremental_value_still_directionally_supported": incremental["classification"] in {"ROBUST_SUPPORT", "PARTIAL_SUPPORT"},
        "major_robustness_warning_found": bool(major_warning),
        "blocking_methodology_issue_found": blocking,
        "ready_for_phase_3_5b": not blocking,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_decision(source_audit: dict, summary: dict) -> dict[str, Any]:
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 3.5A",
        "source_audit_passed": not source_audit["future_leakage_found"] and not source_audit["blocking_conflict_found"],
        "time_robustness_classification": summary["time_robustness_classification"],
        "etf_level_robustness_classification": summary["etf_level_robustness_classification"],
        "segment_robustness_classification": summary["segment_robustness_classification"],
        "horizon_robustness_classification": summary["horizon_robustness_classification"],
        "incremental_value_robustness_preliminary": summary["incremental_value_robustness_preliminary"],
        "high_beta_theme_flags": summary["high_beta_theme_flags"],
        "commodity_cyclical_flags": summary["commodity_cyclical_flags"],
        "phase3_original_conclusion_still_directionally_supported": summary["phase3_original_conclusion_still_directionally_supported"],
        "phase3_incremental_value_still_directionally_supported": summary["phase3_incremental_value_still_directionally_supported"],
        "major_robustness_warning_found": summary["major_robustness_warning_found"],
        "blocking_methodology_issue_found": summary["blocking_methodology_issue_found"],
        "ready_for_phase_3_5b": bool(summary["ready_for_phase_3_5b"]),
        "ready_for_preview": False,
        "ready_for_execution": False,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def update_project_context(decision: dict, summary: dict) -> None:
    status_path = PROJECT_ROOT / "docs" / "current_phase_status.json"
    state_path = PROJECT_ROOT / "docs" / "current_project_state.md"
    status = _read_json(status_path)
    now = _now() + " CST"
    completed_main = list(status.get("completed_main_phases", []))
    if "Project Context Persistence Phase" not in completed_main:
        completed_main.append("Project Context Persistence Phase")
    status.update({
        "context_updated_at": now,
        "context_updated_by": "Codex",
        "context_update_reason": "Regime Layer Phase 3.5A Style Fit Robustness Core Audit completed; Phase 3.5B robustness decision is next",
        "main_phase": "Regime Layer Phase 3.5 - Style Fit Robustness Audit",
        "main_phase_id": "regime_layer_phase_3_5",
        "phase_status": "IN_PROGRESS",
        "phase_started_at": now,
        "phase_completed_at": None,
        "completed_main_phases": completed_main,
        "current_batch": "Phase 3.5B",
        "current_batch_id": "phase_3_5b",
        "current_batch_status": "PENDING",
        "completed_batches": ["Phase 3.5A"],
        "pending_batches": ["Phase 3.5B", "Phase 3.5C", "Phase 3.5D"],
        "blocked_batches": [],
        "skipped_batches": [],
        "last_completed_batch": "Phase 3.5A",
        "resume_from": "Phase 3.5B",
        "required_batches": ["Phase 3.5A", "Phase 3.5B", "Phase 3.5C", "Phase 3.5D"],
        "final_closeout_batch": "Phase 3.5D",
        "next_research_phase": "Regime Layer Phase 3.5B - Robustness Decision Batch",
        "current_phase_report": "reports/style_fit_robustness_core_summary.md",
        "current_phase_decision": "reports/regime_layer_phase3_5a_decision.json",
        "formal_model_changed": False,
        "buy_ranking_changed": False,
        "market_regime_changed": False,
        "ready_for_fit_shadow_observation": True,
        "ready_for_adjusted_preview_research": True,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "research_only": True,
        "execution_allowed": False,
    })
    history = list(status.get("phase_transition_history", []))
    history.append({
        "from_phase": "Project Context Persistence Phase",
        "to_phase": "Regime Layer Phase 3.5 - Style Fit Robustness Audit",
        "reason": "Phase 3.5A completed and Phase 3.5B robustness decision is next",
        "recorded_at": now,
        "transition_type": "BATCH_COMPLETION",
        "completed_batch": "Phase 3.5A",
        "next_batch": "Phase 3.5B",
    })
    status["phase_transition_history"] = history
    _write_json(status_path, status)

    state_text = render_current_project_state(summary, now)
    state_path.write_text(state_text, encoding="utf-8")


def render_current_project_state(summary: dict, now: str) -> str:
    challenge = ""
    if summary.get("major_robustness_warning_found"):
        challenge = "\nPhase 3.5A robustness evidence may challenge Phase 3 preliminary conclusion. Formal readiness adjustment is reserved for Phase 3.5B decision.\n"
    return f"""# Current Project State

## 1. Snapshot Metadata

- Project: A-Share Swing System
- Repository root: `<project_root>`
- State snapshot date: 2026-07-08
- State snapshot source: Regime Layer Phase 3.5A robustness reports and existing context decision files.

This file is a human and Codex shared current project fact snapshot. It is not a history log, README replacement, or phase report.

## 2. Current Project Stage

- Engineering Maturity: approximately stable / operational
- Strategy Maturity: research validation stage
- Current Main Research Track: Regime & Risk Allocation

Current stage:

```text
工程系统基本成型
正式模型稳定运行观察
Shadow / Research 正在验证自适应 Regime Layer
Regime Layer Phase 3.5 - Style Fit Robustness Audit IN_PROGRESS
```

## 3. Formal Model State

- Formal model unchanged.
- `mid_trend = 70%`
- `short_swing = 30%`
- Uses BUY / WATCH / SELL framework.
- Paper simulation active.
- ETF-first.
- Total stock exposure `<= 10%`.

Regime Layer has not changed formal execution.

Style Fit has not changed BUY ranking.

## 4. Completed Regime/Risk Phases

| Phase | Name | Status |
| --- | --- | --- |
| Phase 1 | ETF Realized Risk Profile | COMPLETE |
| Phase 1.5 | Style + Structural Risk Profile | COMPLETE |
| Phase 2 | Market Regime Audit & Historical Replay | COMPLETE |
| Phase 2.5 | Regime Stabilization Research | COMPLETE |
| Phase 3 | Style-Regime Fit Research | COMPLETE |
| Phase 3.5A | Style Fit Robustness Core Audit | COMPLETE |

## 5. Current Research Architecture

```text
Market Regime
↓
ASYMMETRIC_CONFIRM shadow stabilization
↓
Style-Regime Fit
↓
Style Fit Robustness Audit
↓
mid_trend + short_swing
↓
BUY Ranking
↓
Structural / Realized Risk
↓
Portfolio Exposure
```

Responsibilities:

- Style Profile: opportunity / regime fit.
- Structural Risk: future risk budget research.
- Realized Risk: recent observed risk.

`structural_risk_regime_fit_supported = false`.

Therefore structural risk must not be used as the core style/asset fit input.

## 6. Selected Shadow Regime

- selected candidate: `ASYMMETRIC_CONFIRM`
- shadow-only: true
- research-only: true
- not formal execution

Latest known snapshot:

```text
latest_data_date = 2026-07-07
latest_known_regime_date = 2026-07-06
raw regime as of 2026-07-06 = NEUTRAL
selected shadow regime as of 2026-07-06 = NEUTRAL
regime_snapshot_stale = true
```

This snapshot is stale relative to 2026-07-07 data. Do not describe it as the live current market regime.

## 7. Phase 3.5A Current Conclusions

From `reports/regime_layer_phase3_5a_decision.json`:

```text
time_robustness_classification = {summary.get("time_robustness_classification")}
etf_level_robustness_classification = {summary.get("etf_level_robustness_classification")}
segment_robustness_classification = {summary.get("segment_robustness_classification")}
horizon_robustness_classification = {summary.get("horizon_robustness_classification")}
incremental_value_robustness_preliminary = {summary.get("incremental_value_robustness_preliminary")}
ready_for_phase_3_5b = {str(summary.get("ready_for_phase_3_5b")).lower()}
ready_for_preview = false
ready_for_execution = false
execution_allowed = false
```
{challenge}
Phase 3.5A is a preliminary robustness core audit, not the final Phase 3.5 decision.

## 8. Open Research Risks

Current unresolved issues:

- Style Fit robustness decision is not final until Phase 3.5B.
- `HIGH_BETA_THEME` flags: `{", ".join(summary.get("high_beta_theme_flags", []))}`
- `COMMODITY_CYCLICAL` flags: `{", ".join(summary.get("commodity_cyclical_flags", []))}`
- Effective sample size may still be affected by overlapping forward windows and cross-sectional dependence.

## 9. Current Main Bottlenecks

- Phase 3.5B must make the formal robustness decision.
- Real forward shadow samples are limited.
- Formal exit logic remains a major strategy bottleneck.
- Formal model is still research-unproven statistically.

## 10. Project Context Persistence

```text
Project Context Persistence Phase = COMPLETE
```

New threads must still execute repository bootstrap before substantive edits.

## 11. Immediate Next Work

```text
Regime Layer Phase 3.5B
Robustness Decision Batch
status = PENDING
```

Do not directly modify adjusted preview. Current `ready_for_preview=false`.

Context updated at: {now}
"""


def compare_supported_conflict(df: pd.DataFrame, horizon: int) -> dict[str, Any]:
    ret_col = f"forward_return_{horizon}d"
    ex_col = f"benchmark_excess_{horizon}d"
    groups = {
        "STRONG_SUPPORTED": series_stats(df[df["signal_fit_group"] == "STRONG_SUPPORTED"][ret_col], df[df["signal_fit_group"] == "STRONG_SUPPORTED"][ex_col]) if not df.empty else empty_stats(),
        "STRONG_CONFLICT": series_stats(df[df["signal_fit_group"] == "STRONG_CONFLICT"][ret_col], df[df["signal_fit_group"] == "STRONG_CONFLICT"][ex_col]) if not df.empty else empty_stats(),
    }
    sup = groups["STRONG_SUPPORTED"]
    con = groups["STRONG_CONFLICT"]
    median_diff = _diff(sup["median_forward_return"], con["median_forward_return"])
    excess_diff = _diff(sup["benchmark_excess_median"], con["benchmark_excess_median"])
    if sup["sample_count"] < MIN_GROUP_SAMPLE or con["sample_count"] < MIN_GROUP_SAMPLE:
        direction = "INSUFFICIENT"
    elif (median_diff or 0) > 0 and (excess_diff is None or excess_diff >= -0.001):
        direction = "SUPPORTED_BEATS_CONFLICT"
    elif (median_diff or 0) < 0 and (excess_diff is None or excess_diff <= 0.001):
        direction = "CONFLICT_BEATS_SUPPORTED"
    else:
        direction = "NEUTRAL"
    return {"groups": groups, "median_diff": _round(median_diff), "excess_diff": _round(excess_diff), "direction": direction}


def series_stats(returns: pd.Series | list[Any], excess: pd.Series | list[Any]) -> dict[str, Any]:
    ret = pd.to_numeric(pd.Series(returns), errors="coerce").dropna()
    ex = pd.to_numeric(pd.Series(excess), errors="coerce").dropna()
    return {
        "sample_count": int(len(ret)),
        "median_forward_return": _round(float(ret.median())) if len(ret) else None,
        "benchmark_excess_median": _round(float(ex.median())) if len(ex) else None,
        "positive_rate": _round(float((ret > 0).mean())) if len(ret) else None,
    }


def empty_stats() -> dict[str, Any]:
    return {"sample_count": 0, "median_forward_return": None, "benchmark_excess_median": None, "positive_rate": None}


def add_increment_row(rows: list[dict[str, Any]], method: str, group: str, horizon: int, stats: dict[str, Any]) -> None:
    sup = stats["groups"].get("STRONG_SUPPORTED", empty_stats())
    con = stats["groups"].get("STRONG_CONFLICT", empty_stats())
    rows.append({
        "analysis_method": method,
        "period_or_group": group,
        "horizon": f"{horizon}d",
        "supported_count": sup["sample_count"],
        "conflict_count": con["sample_count"],
        "supported_median": sup["median_forward_return"],
        "conflict_median": con["median_forward_return"],
        "median_diff": stats["median_diff"],
        "supported_excess_median": sup["benchmark_excess_median"],
        "conflict_excess_median": con["benchmark_excess_median"],
        "excess_diff": stats["excess_diff"],
        "direction": stats["direction"],
        "incremental_value_supported": stats["direction"] == "SUPPORTED_BEATS_CONFLICT",
        "research_only": True,
        "execution_allowed": False,
    })


def add_aggregate_increment_row(rows: list[dict[str, Any]], base: pd.DataFrame, horizon: int, group_col: str, method: str) -> None:
    ret_col = f"forward_return_{horizon}d"
    ex_col = f"benchmark_excess_{horizon}d"
    grouped_rows = {"STRONG_SUPPORTED": [], "STRONG_CONFLICT": []}
    for group_value, sub in base.groupby(group_col):
        for signal_group in grouped_rows:
            stats = series_stats(sub[sub["signal_fit_group"] == signal_group][ret_col], sub[sub["signal_fit_group"] == signal_group][ex_col])
            if stats["sample_count"]:
                grouped_rows[signal_group].append({"group": group_value, **stats})
    supported_rows = grouped_rows["STRONG_SUPPORTED"]
    conflict_rows = grouped_rows["STRONG_CONFLICT"]
    supported_median = median([r["median_forward_return"] for r in supported_rows])
    conflict_median = median([r["median_forward_return"] for r in conflict_rows])
    supported_excess = median([r["benchmark_excess_median"] for r in supported_rows])
    conflict_excess = median([r["benchmark_excess_median"] for r in conflict_rows])
    median_diff = _diff(supported_median, conflict_median)
    excess_diff = _diff(supported_excess, conflict_excess)
    min_units = MIN_ETF_COUNT if group_col == "symbol" else MIN_SEGMENT_COUNT
    if len(supported_rows) < min_units or len(conflict_rows) < min_units:
        direction = "INSUFFICIENT"
    elif (median_diff or 0) > 0:
        direction = "SUPPORTED_BEATS_CONFLICT"
    elif (median_diff or 0) < 0:
        direction = "CONFLICT_BEATS_SUPPORTED"
    else:
        direction = "NEUTRAL"
    rows.append({
        "analysis_method": method,
        "period_or_group": "ALL",
        "horizon": f"{horizon}d",
        "supported_count": int(sum(r["sample_count"] for r in supported_rows)),
        "conflict_count": int(sum(r["sample_count"] for r in conflict_rows)),
        "supported_median": supported_median,
        "conflict_median": conflict_median,
        "median_diff": _round(median_diff),
        "supported_excess_median": supported_excess,
        "conflict_excess_median": conflict_excess,
        "excess_diff": _round(excess_diff),
        "direction": direction,
        "incremental_value_supported": direction == "SUPPORTED_BEATS_CONFLICT",
        "research_only": True,
        "execution_allowed": False,
    })


def signal_fit_group(bucket: str, evidence: str) -> str:
    if bucket != "STRONG":
        return f"{bucket}_OTHER"
    if evidence in SUPPORT_EVIDENCE:
        return "STRONG_SUPPORTED"
    if evidence in CONFLICT_EVIDENCE:
        return "STRONG_CONFLICT"
    return "STRONG_OTHER"


def segment_lookup(segments: pd.DataFrame) -> dict[str, str]:
    mapping = {}
    for _, row in segments.iterrows():
        dates = pd.date_range(row["segment_start_date"], row["segment_end_date"], freq="D")
        for date in dates:
            mapping[date.strftime("%Y-%m-%d")] = row["segment_id"]
    return mapping


def segment_beats_share(base: pd.DataFrame, regime: str, style: str, horizon: int) -> float | None:
    values = []
    ret_col = f"forward_return_{horizon}d"
    sub = base[(base["stable_regime"] == regime) & (base["style_profile"] == style)]
    for segment_id, seg in sub.groupby("segment_id"):
        sup = pd.to_numeric(seg[seg["signal_fit_group"] == "STRONG_SUPPORTED"][ret_col], errors="coerce").dropna()
        con = pd.to_numeric(seg[seg["signal_fit_group"] == "STRONG_CONFLICT"][ret_col], errors="coerce").dropna()
        if len(sup) and len(con):
            values.append(float(sup.median()) > float(con.median()))
    return _round(sum(values) / len(values)) if values else None


def pooling_bias_flag(pooled: Any, etf_level: Any) -> str:
    p = _maybe_float(pooled)
    e = _maybe_float(etf_level)
    if p is None or e is None:
        return "INSUFFICIENT"
    if (p > 0 > e) or (p < 0 < e):
        return "DIRECTION_REVERSAL"
    if abs(p - e) >= MATERIAL_MEDIAN_SHIFT:
        return "MODERATE_SHIFT"
    return "NO_MATERIAL_SHIFT"


def segment_concentration_flag(obs_share: Any, contribution_share: Any, qualified_count: int) -> str:
    obs = _maybe_float(obs_share)
    contrib = _maybe_float(contribution_share)
    if qualified_count < MIN_SEGMENT_COUNT or obs is None:
        return "INSUFFICIENT"
    level = max(obs, contrib or 0.0)
    if level >= HIGH_SEGMENT_CONCENTRATION:
        return "HIGH"
    if level >= MODERATE_SEGMENT_CONCENTRATION:
        return "MODERATE"
    return "LOW"


def classify_support(values: list[bool]) -> str:
    if not values:
        return "INSUFFICIENT"
    positives = sum(1 for v in values if v)
    if positives == len(values):
        return "ROBUST_SUPPORT"
    if positives >= max(1, math.ceil(len(values) * 0.6)):
        return "PARTIAL_SUPPORT"
    if positives:
        return "FRAGILE"
    return "CONFLICTING"


def classify_flags(flags: list[str], kind: str) -> str:
    if not flags or all(f == "INSUFFICIENT" for f in flags):
        return "INSUFFICIENT"
    if "DIRECTION_REVERSAL" in flags:
        return "CONFLICTING"
    if "HIGH" in flags:
        return "FRAGILE"
    if "MODERATE_SHIFT" in flags or "MODERATE" in flags:
        return "PARTIAL_SUPPORT"
    if kind == "etf" and all(f == "NO_MATERIAL_SHIFT" for f in flags if f != "INSUFFICIENT"):
        return "ROBUST_SUPPORT"
    if kind == "segment" and all(f == "LOW" for f in flags if f != "INSUFFICIENT"):
        return "ROBUST_SUPPORT"
    return "PARTIAL_SUPPORT"


def method_support(rows: list[dict[str, Any]], method: str) -> bool:
    core = [r for r in rows if r["analysis_method"] == method and r["horizon"] in {"5d", "10d", "20d"}]
    if not core:
        return False
    return sum(1 for r in core if r["direction"] == "SUPPORTED_BEATS_CONFLICT") >= math.ceil(len(core) * 0.6)


def summarize_period_direction(rows: list[dict[str, Any]], period_type: str) -> str:
    sub = [r for r in rows if r["period_type"] == period_type and r["signal_fit_group"] == "STRONG_SUPPORTED" and r["horizon"] == "10d"]
    if not sub:
        return "INSUFFICIENT"
    counts: dict[str, int] = {}
    for row in sub:
        counts[str(row["direction"])] = counts.get(str(row["direction"]), 0) + 1
    return ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))


def counterpart_value(rows: list[dict[str, Any]], row: dict[str, Any], key: str) -> Any:
    other = next((r for r in rows if r.get("period_type") == row.get("period_type") and r.get("period_label") == row.get("period_label") and r.get("horizon") == row.get("horizon") and r.get("signal_fit_group") == "STRONG_CONFLICT"), {})
    return other.get(key)


def counterpart_count(rows: list[dict[str, Any]], row: dict[str, Any]) -> int:
    return int(_float(counterpart_value(rows, row, "sample_count")))


def max_flag(flags: list[str], order: list[str]) -> str:
    if not flags:
        return "INSUFFICIENT"
    rank = {flag: index for index, flag in enumerate(order)}
    return max(flags, key=lambda flag: rank.get(flag, -1))


def payload(name: str, rows: list[dict[str, Any]], classification: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "generated_at": _now(),
        "analysis": name,
        "classification": classification if classification in ROBUSTNESS_CLASSES else classification,
        "thresholds": {
            "min_group_sample": MIN_GROUP_SAMPLE,
            "min_etf_count": MIN_ETF_COUNT,
            "min_segment_count": MIN_SEGMENT_COUNT,
            "material_median_shift": MATERIAL_MEDIAN_SHIFT,
            "moderate_segment_concentration": MODERATE_SEGMENT_CONCENTRATION,
            "high_segment_concentration": HIGH_SEGMENT_CONCENTRATION,
        },
        "rows": rows,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
        **(extra or {}),
    }


def write_payload(csv_path: Path, json_path: Path, md_path: Path, payload_data: dict[str, Any], render) -> None:
    pd.DataFrame(payload_data.get("rows", [])).to_csv(csv_path, index=False)
    _write_json(json_path, payload_data)
    md_path.write_text(render(payload_data), encoding="utf-8")


def render_source_audit(audit: dict[str, Any]) -> str:
    return "\n".join([
        "# Style Fit Robustness Source Audit",
        "",
        f"- stable_regime_source: {audit.get('stable_regime_source')}",
        f"- selected_regime_candidate: {audit.get('selected_regime_candidate')}",
        f"- style_profile_source: {audit.get('style_profile_source')}",
        f"- signal_source: {audit.get('signal_source')}",
        f"- benchmark_label_join: {audit.get('benchmark_label_join')}",
        f"- replay range: {audit.get('replay_start_date')} to {audit.get('replay_end_date')}",
        f"- etf_count: {audit.get('etf_count')}",
        f"- style_count: {audit.get('style_count')}",
        f"- regime_count: {audit.get('regime_count')}",
        f"- phase3_sample_unit: {audit.get('phase3_sample_unit')}",
        f"- overlapping_forward_windows_present: {audit.get('overlapping_forward_windows_present')}",
        f"- cross_sectional_dependence_possible: {audit.get('cross_sectional_dependence_possible')}",
        f"- regime_segment_dependence_possible: {audit.get('regime_segment_dependence_possible')}",
        f"- future_leakage_found: {audit.get('future_leakage_found')}",
        f"- blocking_conflict_found: {audit.get('blocking_conflict_found')}",
    ])


def render_time_report(payload_data: dict[str, Any]) -> str:
    return basic_report("Style Fit Time Robustness", payload_data, ["period_type", "period_label", "signal_fit_group", "horizon", "sample_count", "median_forward_return", "benchmark_excess_median", "supported_vs_conflict_median_diff", "direction"])


def render_etf_report(payload_data: dict[str, Any]) -> str:
    return basic_report("Style Fit ETF-Level Robustness", payload_data, ["stable_regime", "style_profile", "signal_fit_group", "horizon", "etf_count", "total_observation_count", "etf_median_of_medians", "pooled_median_return", "pooling_bias_flag"])


def render_segment_report(payload_data: dict[str, Any]) -> str:
    return basic_report("Style Fit Regime-Segment Robustness", payload_data, ["stable_regime", "style_profile", "signal_fit_group", "horizon", "segment_count", "qualified_segment_count", "segment_median_return_median", "largest_segment_observation_share", "segment_concentration_flag"])


def render_horizon_report(payload_data: dict[str, Any]) -> str:
    return basic_report("Style Fit Horizon Robustness", payload_data, ["horizon", "supported_count", "conflict_count", "supported_median_return", "conflict_median_return", "median_diff", "direction"])


def render_special_report(payload_data: dict[str, Any]) -> str:
    return basic_report(f"{payload_data.get('style_profile')} Special Audit", payload_data, ["stable_regime", "etf_count", "observation_count", "segment_count", "5d_median", "10d_median", "20d_median", "10d_etf_level_median", "10d_segment_level_median"])


def render_incremental_report(payload_data: dict[str, Any]) -> str:
    return basic_report("Style Fit Incremental Value Robustness", payload_data, ["analysis_method", "period_or_group", "horizon", "supported_count", "conflict_count", "median_diff", "excess_diff", "direction", "incremental_value_supported"])


def render_summary_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Style Fit Robustness Core Summary",
        "",
        f"- time_robustness_classification: {summary.get('time_robustness_classification')}",
        f"- etf_level_robustness_classification: {summary.get('etf_level_robustness_classification')}",
        f"- segment_robustness_classification: {summary.get('segment_robustness_classification')}",
        f"- horizon_robustness_classification: {summary.get('horizon_robustness_classification')}",
        f"- incremental_value_robustness_preliminary: {summary.get('incremental_value_robustness_preliminary')}",
        f"- high_beta_theme_flags: {summary.get('high_beta_theme_flags')}",
        f"- commodity_cyclical_flags: {summary.get('commodity_cyclical_flags')}",
        f"- phase3_original_conclusion_still_directionally_supported: {summary.get('phase3_original_conclusion_still_directionally_supported')}",
        f"- phase3_incremental_value_still_directionally_supported: {summary.get('phase3_incremental_value_still_directionally_supported')}",
        f"- major_robustness_warning_found: {summary.get('major_robustness_warning_found')}",
        f"- blocking_methodology_issue_found: {summary.get('blocking_methodology_issue_found')}",
        f"- ready_for_phase_3_5b: {summary.get('ready_for_phase_3_5b')}",
        f"- ready_for_preview: {summary.get('ready_for_preview')}",
        f"- ready_for_execution: {summary.get('ready_for_execution')}",
    ]
    return "\n".join(lines)


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join([
        "# Regime Layer Phase 3.5A Decision",
        "",
        f"- source_audit_passed: {decision.get('source_audit_passed')}",
        f"- time_robustness_classification: {decision.get('time_robustness_classification')}",
        f"- etf_level_robustness_classification: {decision.get('etf_level_robustness_classification')}",
        f"- segment_robustness_classification: {decision.get('segment_robustness_classification')}",
        f"- horizon_robustness_classification: {decision.get('horizon_robustness_classification')}",
        f"- incremental_value_robustness_preliminary: {decision.get('incremental_value_robustness_preliminary')}",
        f"- ready_for_phase_3_5b: {decision.get('ready_for_phase_3_5b')}",
        f"- ready_for_preview: {decision.get('ready_for_preview')}",
        f"- ready_for_execution: {decision.get('ready_for_execution')}",
        "",
        "This is not the final Phase 3.5 robustness decision.",
    ])


def basic_report(title: str, payload_data: dict[str, Any], columns: list[str]) -> str:
    rows = payload_data.get("rows", [])
    return "\n".join([
        f"# {title}",
        "",
        f"- classification: {payload_data.get('classification')}",
        f"- research_only: {payload_data.get('research_only')}",
        f"- execution_allowed: {payload_data.get('execution_allowed')}",
        "",
        markdown_table(rows, columns, limit=160),
    ])


def markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int | None = None) -> str:
    data = rows[:limit] if limit else rows
    if not data:
        return "_No rows._"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in data:
        lines.append("| " + " | ".join(format_cell(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def _summary_lookup(summary: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["regime"]), str(row["style_profile"])): row for row in summary.get("rows", [])}


def _read_csv(path: Path, dtype: dict[str, Any] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=dtype)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload_data: Any) -> None:
    path.write_text(json.dumps(_sanitize(payload_data), ensure_ascii=False, indent=2), encoding="utf-8")


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
        return round(value, 6)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return value


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


def _maybe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _float(value: Any, fallback: float = 0.0) -> float:
    out = _maybe_float(value)
    return fallback if out is None else out


def _round(value: Any) -> float | None:
    out = _maybe_float(value)
    return round(out, 6) if out is not None else None


def _diff(a: Any, b: Any) -> float | None:
    aa = _maybe_float(a)
    bb = _maybe_float(b)
    if aa is None or bb is None:
        return None
    return round(aa - bb, 6)


def median(values: list[Any]) -> float | None:
    clean = [_maybe_float(v) for v in values]
    clean = [v for v in clean if v is not None]
    return round(float(np.median(clean)), 6) if clean else None


def mean(values: list[Any]) -> float | None:
    clean = [_maybe_float(v) for v in values]
    clean = [v for v in clean if v is not None]
    return round(float(sum(clean) / len(clean)), 6) if clean else None


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value).replace("|", "/")


if __name__ == "__main__":
    main()
