"""Weekly observation report for shadow models.

Research-only. This script aggregates shadow tracking outputs for
top10_diversified_filter_v2, persistence_breakout_v2, and missed opportunity
tracking. It never changes model rules, execution rules, paper trades, or paper
positions.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"

REPORT_MD = REPORT_DIR / "shadow_observation_weekly.md"
REPORT_CSV = REPORT_DIR / "shadow_observation_weekly.csv"
REPORT_JSON = REPORT_DIR / "shadow_observation_weekly.json"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    persistence_tracking = read_csv(DATA_DIR / "persistence_breakout_shadow_tracking.csv")
    missed_tracking = read_csv(DATA_DIR / "missed_opportunity_tracking.csv")
    persistence_signal = read_csv(REPORT_DIR / "persistence_breakout_shadow_signal.csv")
    model_comparison = read_csv(REPORT_DIR / "model_shadow_comparison.csv")
    persistence_portfolio = read_csv(REPORT_DIR / "persistence_breakout_shadow_portfolio.csv")
    v2_signal = read_csv(REPORT_DIR / "ranking_model_v2_shadow_signal.csv")
    v2_portfolio = read_csv(REPORT_DIR / "ranking_model_v2_shadow_portfolio.csv")

    file_status = build_file_status(
        {
            "persistence_tracking": DATA_DIR / "persistence_breakout_shadow_tracking.csv",
            "missed_tracking": DATA_DIR / "missed_opportunity_tracking.csv",
            "persistence_signal": REPORT_DIR / "persistence_breakout_shadow_signal.csv",
            "model_comparison": REPORT_DIR / "model_shadow_comparison.csv",
            "persistence_portfolio": REPORT_DIR / "persistence_breakout_shadow_portfolio.csv",
            "ranking_model_v2_shadow_signal": REPORT_DIR / "ranking_model_v2_shadow_signal.csv",
            "ranking_model_v2_shadow_portfolio": REPORT_DIR / "ranking_model_v2_shadow_portfolio.csv",
            "strategy_preview_tracking_report": REPORT_DIR / "strategy_preview_tracking_report.md",
        }
    )

    model_status = build_model_status(persistence_signal, persistence_tracking, v2_signal, v2_portfolio, model_comparison)
    persistence_stats = build_persistence_stats(persistence_signal, missed_tracking)
    missed_stats = build_missed_stats(missed_tracking)
    selected_vs_filtered = build_selected_vs_filtered()
    comparison_summary = build_model_comparison_summary(model_comparison)
    conclusion = build_conclusion(persistence_stats, missed_stats, selected_vs_filtered)

    row = {
        "review_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "status": "active",
        "research_only": True,
        "execution_enabled": False,
        "top10_diversified_active": model_status["top10_diversified_active"],
        "persistence_breakout_active": model_status["persistence_breakout_active"],
        "all_models_research_only": True,
        "any_model_execution_enabled": False,
        "signal_days": persistence_stats["signal_days_20d"],
        "selected_days": persistence_stats["selected_days_20d"],
        "persistence_empty_signal_days": persistence_stats["empty_signal_days_20d"],
        "risk_on_empty_days": persistence_stats["risk_on_empty_days_20d"],
        "avg_selected_count": persistence_stats["avg_selected_count_20d"],
        "top_filter_reasons": persistence_stats["top_filter_reasons"],
        "high_beta_selected_count": persistence_stats["high_beta_selected_count_20d"],
        "data_health_caution_selected_count": persistence_stats["data_health_caution_selected_count_20d"],
        "missed_opportunity_candidate_count": missed_stats["candidate_count"],
        "pending_count": missed_stats["pending_count"],
        "matured_1d_count": missed_stats["matured_1d_count"],
        "matured_3d_count": missed_stats["matured_3d_count"],
        "matured_5d_count": missed_stats["matured_5d_count"],
        "matured_10d_count": missed_stats["matured_10d_count"],
        "matured_20d_count": missed_stats["matured_20d_count"],
        "missed_opportunity_count": missed_stats["missed_opportunity_count"],
        "missed_opportunity_rate": missed_stats["missed_opportunity_rate"],
        "filter_effective_count": missed_stats["filter_effective_count"],
        "filter_effective_rate": missed_stats["filter_effective_rate"],
        "top_missed_filter_reason": missed_stats["top_missed_filter_reason"],
        "selected_forward_5d_mean": selected_vs_filtered.get("selected_forward_5d_mean", ""),
        "filtered_forward_5d_mean": selected_vs_filtered.get("filtered_forward_5d_mean", ""),
        "benchmark_510300_forward_5d_mean": selected_vs_filtered.get("benchmark_510300_forward_5d_mean", ""),
        "selected_forward_10d_mean": selected_vs_filtered.get("selected_forward_10d_mean", ""),
        "filtered_forward_10d_mean": selected_vs_filtered.get("filtered_forward_10d_mean", ""),
        "benchmark_510300_forward_10d_mean": selected_vs_filtered.get("benchmark_510300_forward_10d_mean", ""),
        "evidence_level": conclusion["evidence_level"],
        "ready_to_relax_filters": False,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "recommended_action": conclusion["recommended_action"],
        "summary": conclusion["summary"],
    }
    report_df = pd.DataFrame([row])
    report_df.to_csv(REPORT_CSV, index=False)

    payload = {
        "status": "active",
        "research_only": True,
        "execution_enabled": False,
        "evidence_level": conclusion["evidence_level"],
        "persistence_empty_signal_days": persistence_stats["empty_signal_days_20d"],
        "risk_on_empty_days": persistence_stats["risk_on_empty_days_20d"],
        "missed_opportunity_candidate_count": missed_stats["candidate_count"],
        "matured_forward_return_count": missed_stats["matured_10d_count"],
        "missed_opportunity_rate": missed_stats["missed_opportunity_rate"],
        "filter_effective_rate": missed_stats["filter_effective_rate"],
        "ready_to_relax_filters": False,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "recommended_action": conclusion["recommended_action"],
        "summary": conclusion["summary"],
        "report_href": "../reports/shadow_observation_weekly.md",
        "csv_href": "../reports/shadow_observation_weekly.csv",
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        render_report(
            row,
            file_status,
            model_status,
            persistence_stats,
            missed_stats,
            selected_vs_filtered,
            comparison_summary,
            model_comparison,
            conclusion,
        ),
        encoding="utf-8",
    )

    print(f"shadow observation evidence_level: {conclusion['evidence_level']}")
    print(f"missed candidates: {missed_stats['candidate_count']}")
    print(f"matured_10d_count: {missed_stats['matured_10d_count']}")
    print(f"written: {REPORT_MD}")
    print(f"written: {REPORT_CSV}")
    print(f"written: {REPORT_JSON}")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"symbol": str}).fillna("")
    except Exception:
        return pd.DataFrame()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_file_status(paths: dict[str, Path]) -> dict[str, str]:
    return {name: "present" if path.exists() else "missing" for name, path in paths.items()}


def build_model_status(
    persistence_signal: pd.DataFrame,
    persistence_tracking: pd.DataFrame,
    v2_signal: pd.DataFrame,
    v2_portfolio: pd.DataFrame,
    model_comparison: pd.DataFrame,
) -> dict:
    v2_active = (
        not v2_signal.empty
        or not v2_portfolio.empty
        or (REPORT_DIR / "ranking_model_v2_backtest_report.md").exists()
        or (REPORT_DIR / "ranking_model_v2_metrics.json").exists()
    )
    persistence_active = not persistence_signal.empty or not persistence_tracking.empty or (REPORT_DIR / "persistence_breakout_shadow_summary.json").exists()
    return {
        "top10_diversified_active": bool(v2_active),
        "persistence_breakout_active": bool(persistence_active),
        "model_comparison_available": not model_comparison.empty,
        "research_only": True,
        "execution_enabled": False,
        "ready_for_execution": False,
    }


def build_persistence_stats(signal: pd.DataFrame, missed: pd.DataFrame) -> dict:
    if signal.empty:
        return empty_persistence_stats()
    df = signal.copy()
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df["selected"] = df.get("selected", False).map(to_bool)
    df["rank"] = pd.to_numeric(df.get("rank"), errors="coerce")
    df = df.dropna(subset=["date"])
    daily = (
        df.groupby("date")
        .agg(
            selected_count=("selected", "sum"),
            high_beta_selected_count=("etf_type", lambda s: int(sum(is_high_beta_type(v) for v in s[df.loc[s.index, "selected"]]))),
            data_health_caution_selected_count=("data_health_status", lambda s: int(sum(str(v) != "normal" for v in s[df.loc[s.index, "selected"]]))),
        )
        .reset_index()
        .sort_values("date")
    )
    risk_on_empty_dates = set()
    if not missed.empty and {"date", "market_regime"}.issubset(missed.columns):
        m = missed.copy()
        m["date"] = pd.to_datetime(m["date"], errors="coerce")
        risk_on_empty_dates = set(m[m["market_regime"].astype(str) == "risk_on"]["date"].dropna())

    stats = {}
    for window in [5, 10, 20]:
        sub = daily.tail(window)
        signal_days = int(len(sub))
        selected_days = int((pd.to_numeric(sub["selected_count"], errors="coerce") > 0).sum()) if signal_days else 0
        empty_days = int((pd.to_numeric(sub["selected_count"], errors="coerce") == 0).sum()) if signal_days else 0
        stats[f"signal_days_{window}d"] = signal_days
        stats[f"selected_days_{window}d"] = selected_days
        stats[f"empty_signal_days_{window}d"] = empty_days
        stats[f"risk_on_empty_days_{window}d"] = int(sum(date in risk_on_empty_dates for date in sub["date"]))
        stats[f"avg_selected_count_{window}d"] = round(float(pd.to_numeric(sub["selected_count"], errors="coerce").mean()), 4) if signal_days else 0.0
        stats[f"high_beta_selected_count_{window}d"] = int(pd.to_numeric(sub["high_beta_selected_count"], errors="coerce").sum()) if signal_days else 0
        stats[f"data_health_caution_selected_count_{window}d"] = int(pd.to_numeric(sub["data_health_caution_selected_count"], errors="coerce").sum()) if signal_days else 0

    reasons = []
    if "filter_reasons" in df.columns:
        for value in df[df["selected"] == False]["filter_reasons"]:  # noqa: E712
            reasons.extend(split_reasons(value))
    if not missed.empty and "primary_filter_reason" in missed.columns:
        reasons.extend(missed["primary_filter_reason"].astype(str).tolist())
    reason_counts = pd.Series(reasons).value_counts() if reasons else pd.Series(dtype=int)
    stats["top_filter_reasons"] = ", ".join(reason_counts.head(3).index.astype(str).tolist())
    return stats


def empty_persistence_stats() -> dict:
    stats = {"top_filter_reasons": ""}
    for window in [5, 10, 20]:
        stats[f"signal_days_{window}d"] = 0
        stats[f"selected_days_{window}d"] = 0
        stats[f"empty_signal_days_{window}d"] = 0
        stats[f"risk_on_empty_days_{window}d"] = 0
        stats[f"avg_selected_count_{window}d"] = 0.0
        stats[f"high_beta_selected_count_{window}d"] = 0
        stats[f"data_health_caution_selected_count_{window}d"] = 0
    return stats


def build_missed_stats(missed: pd.DataFrame) -> dict:
    if missed.empty:
        return {
            "candidate_count": 0,
            "pending_count": 0,
            "matured_1d_count": 0,
            "matured_3d_count": 0,
            "matured_5d_count": 0,
            "matured_10d_count": 0,
            "matured_20d_count": 0,
            "missed_opportunity_count": 0,
            "missed_opportunity_rate": 0.0,
            "filter_effective_count": 0,
            "filter_effective_rate": 0.0,
            "top_missed_filter_reason": "",
        }
    df = missed.copy()
    candidate_count = int(len(df))
    stats = {"candidate_count": candidate_count}
    for window in [1, 3, 5, 10, 20]:
        stats[f"matured_{window}d_count"] = int(numeric(df.get(f"forward_return_{window}d", pd.Series(dtype=float))).notna().sum())
    stats["pending_count"] = candidate_count - stats["matured_10d_count"]
    missed_flag = df.get("missed_opportunity_flag", pd.Series(dtype=bool)).map(to_bool)
    effective_flag = df.get("filter_effective_flag", pd.Series(dtype=bool)).map(to_bool)
    stats["missed_opportunity_count"] = int(missed_flag.sum())
    stats["missed_opportunity_rate"] = round(float(missed_flag.mean()), 6) if candidate_count else 0.0
    stats["filter_effective_count"] = int(effective_flag.sum())
    stats["filter_effective_rate"] = round(float(effective_flag.mean()), 6) if candidate_count else 0.0
    if "primary_filter_reason" in df.columns and not df["primary_filter_reason"].empty:
        counts = df["primary_filter_reason"].astype(str).value_counts()
        stats["top_missed_filter_reason"] = str(counts.index[0]) if not counts.empty else ""
    else:
        stats["top_missed_filter_reason"] = ""
    return stats


def build_selected_vs_filtered() -> dict:
    path = REPORT_DIR / "selected_vs_filtered_forward_return.csv"
    df = read_csv(path)
    out = {}
    if df.empty:
        return out
    for bucket, prefix in [
        ("selected_candidates", "selected"),
        ("filtered_candidates", "filtered"),
        ("510300_benchmark", "benchmark_510300"),
    ]:
        row = df[df.get("bucket", "").astype(str) == bucket]
        if row.empty:
            continue
        out[f"{prefix}_forward_5d_mean"] = safe_value(row.iloc[0].get("forward_return_5d_mean", ""))
        out[f"{prefix}_forward_10d_mean"] = safe_value(row.iloc[0].get("forward_return_10d_mean", ""))
    return out


def build_model_comparison_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "available": False,
            "original_symbols": "",
            "adjusted_symbols": "",
            "top10_symbols": "",
            "persistence_symbols": "",
            "more_aggressive_model": "unknown",
            "more_diversified_model": "unknown",
            "health_best_model": "unknown",
        }
    rows = {str(row.get("model_name")): row for _, row in df.iterrows()}
    high_beta = {name: int(float(row.get("high_beta_count") or 0)) for name, row in rows.items()}
    health = {name: int(float(row.get("data_health_caution_count") or 0)) for name, row in rows.items()}
    selected_counts = {name: int(float(row.get("selected_count") or 0)) for name, row in rows.items()}
    more_aggressive = max(high_beta, key=high_beta.get) if high_beta else "unknown"
    more_diversified = min(selected_counts, key=selected_counts.get) if selected_counts else "unknown"
    health_best = min(health, key=health.get) if health else "unknown"
    return {
        "available": True,
        "original_symbols": str(rows.get("original_ranking", {}).get("selected_symbols", "")),
        "adjusted_symbols": str(rows.get("adjusted_preview_ranking", {}).get("selected_symbols", "")),
        "top10_symbols": str(rows.get("top10_diversified_filter_v2", {}).get("selected_symbols", "")),
        "persistence_symbols": str(rows.get("persistence_breakout_v2", {}).get("selected_symbols", "")),
        "more_aggressive_model": more_aggressive,
        "more_diversified_model": more_diversified,
        "health_best_model": health_best,
    }


def build_conclusion(persistence_stats: dict, missed_stats: dict, selected_vs_filtered: dict) -> dict:
    candidate_count = missed_stats["candidate_count"]
    matured_10d = missed_stats["matured_10d_count"]
    pending_ratio = (missed_stats["pending_count"] / candidate_count) if candidate_count else 1.0
    evidence_level = "insufficient" if pending_ratio > 0.5 else "low" if matured_10d < 20 else "medium"
    recommended_action = "continue_observation"
    summary = "Forward returns are mostly pending; evidence is insufficient. Keep all filters unchanged and continue weekly observation."
    if evidence_level == "low":
        summary = "Some forward returns are available, but matured samples are below 20. Do not relax filters."
    elif evidence_level == "medium":
        missed_rate = missed_stats["missed_opportunity_rate"]
        effective_rate = missed_stats["filter_effective_rate"]
        filtered_10d = to_float(selected_vs_filtered.get("filtered_forward_10d_mean"))
        bench_10d = to_float(selected_vs_filtered.get("benchmark_510300_forward_10d_mean"))
        if missed_rate > 0.5 and pd.notna(filtered_10d) and pd.notna(bench_10d) and filtered_10d > bench_10d:
            recommended_action = "study_relaxed_filter_variant"
            summary = "Filtered candidates show repeated positive excess returns. Study a relaxed variant, but do not change execution rules."
        elif effective_rate > 0.5:
            recommended_action = "keep_current_filters"
            summary = "Filter effective rate is high. Keep current strict filters."
    if persistence_stats.get("risk_on_empty_days_20d", 0) >= 5:
        recommended_action = "study_risk_on_relaxed_variant"
        summary += " Risk-on empty signals are frequent enough to justify a research-only relaxed variant study."
    return {
        "evidence_level": evidence_level,
        "recommended_action": recommended_action,
        "summary": summary,
    }


def render_report(
    row: dict,
    file_status: dict,
    model_status: dict,
    persistence_stats: dict,
    missed_stats: dict,
    selected_vs_filtered: dict,
    comparison_summary: dict,
    comparison_df: pd.DataFrame,
    conclusion: dict,
) -> str:
    lines = [
        "# Shadow Observation Weekly Review",
        "",
        "本报告只做 shadow observation / reporting，不修改任何模型规则，不接执行层，不真实交易。",
        "",
        "## 结论字段",
        f"- evidence_level: {conclusion['evidence_level']}",
        "- ready_to_relax_filters: false",
        "- ready_for_preview: false",
        "- ready_for_execution: false",
        f"- recommended_action: {conclusion['recommended_action']}",
        f"- summary: {conclusion['summary']}",
        "",
        "## A. Shadow 模型状态",
        f"- top10_diversified_filter_v2 active: {model_status['top10_diversified_active']}",
        f"- persistence_breakout_v2 active: {model_status['persistence_breakout_active']}",
        "- all_models_research_only: true",
        "- any_model_execution_enabled: false",
        "- ready_for_execution: false",
        "",
        "## 文件状态",
        markdown_table(pd.DataFrame([{"file": k, "status": v} for k, v in file_status.items()])),
        "",
        "## B. persistence_breakout_v2 最近观察",
        markdown_table(pd.DataFrame([persistence_stats])),
        "",
        "重点判断：当前可用样本显示 selected_count 为 0；risk_on 空仓次数为 "
        f"{persistence_stats.get('risk_on_empty_days_20d', 0)}。主要过滤原因：{persistence_stats.get('top_filter_reasons') or 'N/A'}。",
        "",
        "## C. missed opportunity 观察",
        markdown_table(pd.DataFrame([missed_stats])),
        "",
        "如果大部分 forward return 仍 pending，则证据不足，不允许据此放宽规则。",
        "",
        "## D. selected vs filtered vs benchmark",
        markdown_table(pd.DataFrame([selected_vs_filtered]) if selected_vs_filtered else pd.DataFrame()),
        "",
        "## E. original / adjusted / v2 对比",
        markdown_table(pd.DataFrame([comparison_summary])),
        "",
        markdown_table(comparison_df),
        "",
        "## 安全边界",
        "- 不接券商 API",
        "- 不真实下单",
        "- 不修改 paper_trades.csv",
        "- 不修改 paper_positions.csv",
        "- 不改变 paper_trade_engine.py",
        "- 不修改 persistence_breakout_v2 或 top10_diversified_filter_v2 规则",
        "- forward return 只作为事后 label，不作为当日特征",
    ]
    return "\n".join(lines) + "\n"


def split_reasons(value: object) -> list[str]:
    text = str(value or "").replace(",", ";")
    return [part.strip() for part in text.split(";") if part.strip()]


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}


def to_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def safe_value(value: object) -> object:
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return value


def is_high_beta_type(value: object) -> bool:
    return str(value) in {"theme", "high_beta"}


def markdown_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "暂无数据。"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.6f}".rstrip("0").rstrip("."))
    return view.to_markdown(index=False)


if __name__ == "__main__":
    main()
