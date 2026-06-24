"""Phase 4C Alpha: limited alpha factor enhancement research."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import phase4c_alpha_common as common  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"
MD_REPORT = REPORT_DIR / "alpha_factor_enhancement_research.md"
SUMMARY_CSV = REPORT_DIR / "alpha_factor_enhancement_summary.csv"
METRICS_JSON = REPORT_DIR / "alpha_factor_enhancement_metrics.json"
COMPARISON_MD = REPORT_DIR / "phase4c_alpha_model_comparison.md"
COMPARISON_CSV = REPORT_DIR / "phase4c_alpha_model_comparison.csv"
DECISION_MD = REPORT_DIR / "phase4c_alpha_model_decision.md"
SUMMARY_JSON = REPORT_DIR / "phase4c_alpha_summary.json"

STRATEGIES = [
    "relative_strength_plus_trend_v2",
    "risk_adjusted_momentum_v2",
    "persistence_breakout_v2",
    "alpha_blend_simple_v2",
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    context = common.load_context()
    results = [common.run_research_strategy(strategy, context) for strategy in STRATEGIES]
    summary, equity, trades, yearly = common.result_frames(results)
    summary = enrich_summary(summary)
    summary.to_csv(SUMMARY_CSV, index=False)
    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "research_only": True,
        "strategies": summary.to_dict(orient="records"),
        "best_candidate": best_candidate(summary),
        "yearly": yearly.to_dict(orient="records"),
        "safety": {"execution_enabled": False, "broker_api": False, "real_order": False},
    }
    common.write_json(METRICS_JSON, payload)
    MD_REPORT.write_text(render_alpha_report(payload), encoding="utf-8")
    comparison = build_comparison(summary)
    comparison.to_csv(COMPARISON_CSV, index=False)
    decision = build_decision(comparison)
    COMPARISON_MD.write_text(render_comparison_report(comparison, decision), encoding="utf-8")
    DECISION_MD.write_text(render_decision_report(decision), encoding="utf-8")
    common.write_json(SUMMARY_JSON, decision)
    print(f"written: {MD_REPORT}")
    print(f"written: {SUMMARY_CSV}")
    print(f"written: {METRICS_JSON}")
    print(f"written: {COMPARISON_MD}")
    print(f"written: {COMPARISON_CSV}")
    print(f"written: {DECISION_MD}")


def enrich_summary(summary: pd.DataFrame) -> pd.DataFrame:
    bench = common.load_510300_benchmark()
    bench_return = float(bench.get("total_return", 0) or 0)
    v2_summary = _main_rows(common.benchmark_rows())
    v2_row = v2_summary[v2_summary["strategy"] == common.V2_STRATEGY]
    v2_return = float(v2_row["total_return"].iloc[0]) if not v2_row.empty else 0
    out = summary.copy()
    out["beat_510300"] = pd.to_numeric(out["total_return"], errors="coerce") > bench_return
    out["beat_v2_baseline"] = pd.to_numeric(out["total_return"], errors="coerce") > v2_return
    out["ready_for_execution"] = False
    out["ready_for_shadow"] = out["beat_v2_baseline"] & (pd.to_numeric(out["max_drawdown"], errors="coerce") > -0.12)
    out["overfit_risk"] = "medium"
    return out


def best_candidate(summary: pd.DataFrame) -> dict:
    if summary.empty:
        return {}
    candidates = summary.copy()
    candidates["score"] = pd.to_numeric(candidates["total_return"], errors="coerce").fillna(-9) + pd.to_numeric(candidates["calmar"], errors="coerce").fillna(0) * 0.02
    row = candidates.sort_values("score", ascending=False).iloc[0]
    return common.metric_payload(row)


def build_comparison(alpha_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    baseline = _main_rows(common.benchmark_rows())
    keep = [common.BENCHMARK_STRATEGY, "original_baseline_v2", "adjusted_preview_baseline_v2", common.V2_STRATEGY]
    rows.extend(baseline[baseline["strategy"].isin(keep)].to_dict(orient="records"))
    rows.extend(_best_from("regime_aware_model_summary.csv", "best_regime_aware_candidate"))
    rows.extend(_best_from("etf_type_aware_model_summary.csv", "best_type_aware_candidate"))
    if not alpha_summary.empty:
        best_alpha = alpha_summary.sort_values(["ready_for_shadow", "total_return", "calmar"], ascending=[False, False, False]).head(1).copy()
        if not best_alpha.empty:
            best_alpha["strategy"] = best_alpha["strategy"].astype(str)
            rows.extend(best_alpha.to_dict(orient="records"))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = _main_rows(df)
    bench_return = float(df.loc[df["strategy"] == common.BENCHMARK_STRATEGY, "total_return"].iloc[0]) if common.BENCHMARK_STRATEGY in set(df["strategy"]) else 0
    v2_return = float(df.loc[df["strategy"] == common.V2_STRATEGY, "total_return"].iloc[0]) if common.V2_STRATEGY in set(df["strategy"]) else 0
    df["beat_510300"] = pd.to_numeric(df["total_return"], errors="coerce") > bench_return
    df["beat_v2_baseline"] = pd.to_numeric(df["total_return"], errors="coerce") > v2_return
    df["ready_for_execution"] = False
    df["ready_for_shadow"] = (df["beat_v2_baseline"]) & (pd.to_numeric(df["max_drawdown"], errors="coerce") > -0.12)
    df.loc[df["strategy"] == common.BENCHMARK_STRATEGY, "ready_for_shadow"] = False
    df["overfit_risk"] = df.apply(overfit_risk, axis=1)
    df["main_weakness"] = df.apply(main_weakness, axis=1)
    for col in ["avg_exposure", "avg_holding_days"]:
        if col not in df.columns:
            df[col] = df.get("exposure_avg", 0) if col == "avg_exposure" else df.get("avg_holding_days", 0)
    cols = [
        "strategy",
        "total_return",
        "annualized_return",
        "max_drawdown",
        "calmar",
        "sharpe",
        "trade_count",
        "cost_total",
        "turnover",
        "avg_holding_days",
        "avg_exposure",
        "win_rate",
        "profit_factor",
        "beat_510300",
        "beat_v2_baseline",
        "ready_for_shadow",
        "ready_for_execution",
        "overfit_risk",
        "main_weakness",
    ]
    for col in cols:
        if col not in df.columns:
            df[col] = None
    return df[cols].drop_duplicates("strategy", keep="last")


def build_decision(comparison: pd.DataFrame) -> dict:
    if comparison.empty:
        return {"status": "missing", "ready_for_execution": False}
    candidates = comparison[comparison["strategy"] != common.BENCHMARK_STRATEGY].copy()
    candidates["score"] = pd.to_numeric(candidates["total_return"], errors="coerce").fillna(-9) + pd.to_numeric(candidates["calmar"], errors="coerce").fillna(0) * 0.02
    row = candidates.sort_values(["ready_for_shadow", "score"], ascending=[False, False]).iloc[0].to_dict()
    beat_510300 = bool(row.get("beat_510300", False))
    candidate_type = "strong_shadow" if beat_510300 and row.get("ready_for_shadow") else "defensive" if row.get("ready_for_shadow") else "rejected"
    return {
        "status": "completed",
        "research_only": True,
        "execution_enabled": False,
        "best_candidate": row.get("strategy", ""),
        "candidate_type": candidate_type,
        "best_total_return": row.get("total_return", 0),
        "best_max_drawdown": row.get("max_drawdown", 0),
        "beat_510300": beat_510300,
        "beat_v2_baseline": bool(row.get("beat_v2_baseline", False)),
        "ready_for_shadow": bool(row.get("ready_for_shadow", False)),
        "ready_for_execution": False,
        "overfit_guardrails_passed": bool(row.get("overfit_risk") in {"low", "medium"}),
        "summary": "Phase 4C alpha research completed. Candidate remains research/shadow only; execution integration is disabled.",
        "next_step": "Run shadow tracking for the best candidate only if user approves; do not alter paper_trade_engine.",
    }


def render_alpha_report(payload: dict) -> str:
    best = payload.get("best_candidate", {})
    lines = [
        f"# Alpha 因子增强研究 {payload['generated_at']}",
        "",
        "本研究限制在少量有经济逻辑的 alpha 因子，不做大规模网格，不用未来收益。",
        "",
        f"- 最佳 alpha 候选：{best.get('strategy', 'N/A')}",
        f"- total_return：{common.pct(best.get('total_return'))}",
        f"- max_drawdown：{common.pct(best.get('max_drawdown'))}",
        "",
        "| strategy | return | max_drawdown | calmar | trades | cost | beat_v2 | shadow |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload.get("strategies", []):
        lines.append(f"| {row['strategy']} | {common.pct(row.get('total_return'))} | {common.pct(row.get('max_drawdown'))} | {row.get('calmar', 0):.2f} | {int(row.get('trade_count', 0))} | {row.get('cost_total', 0):.2f} | {row.get('beat_v2_baseline')} | {row.get('ready_for_shadow')} |")
    lines.extend(["", "所有 alpha 候选 ready_for_execution=false。"])
    return "\n".join(lines)


def render_comparison_report(comparison: pd.DataFrame, decision: dict) -> str:
    lines = [
        f"# Phase 4C Alpha 模型综合对比 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- best_candidate: {decision.get('best_candidate')}",
        f"- candidate_type: {decision.get('candidate_type')}",
        f"- ready_for_shadow: {decision.get('ready_for_shadow')}",
        f"- ready_for_execution: {decision.get('ready_for_execution')}",
        "",
        "| strategy | return | max_drawdown | calmar | trades | cost | beat_510300 | beat_v2 | shadow | weakness |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in comparison.to_dict(orient="records"):
        lines.append(f"| {row['strategy']} | {common.pct(row.get('total_return'))} | {common.pct(row.get('max_drawdown'))} | {row.get('calmar', 0):.2f} | {int(row.get('trade_count') or 0)} | {float(row.get('cost_total') or 0):.2f} | {row.get('beat_510300')} | {row.get('beat_v2_baseline')} | {row.get('ready_for_shadow')} | {row.get('main_weakness')} |")
    return "\n".join(lines)


def render_decision_report(decision: dict) -> str:
    return "\n".join(
        [
            f"# Phase 4C Alpha 决策报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"- best_candidate: {decision.get('best_candidate')}",
            f"- candidate_type: {decision.get('candidate_type')}",
            f"- best_total_return: {common.pct(decision.get('best_total_return'))}",
            f"- best_max_drawdown: {common.pct(decision.get('best_max_drawdown'))}",
            f"- beat_510300: {decision.get('beat_510300')}",
            f"- beat_v2_baseline: {decision.get('beat_v2_baseline')}",
            f"- ready_for_shadow: {decision.get('ready_for_shadow')}",
            "- ready_for_execution: false",
            f"- overfit_guardrails_passed: {decision.get('overfit_guardrails_passed')}",
            "",
            "结论：本轮仅形成研究候选，不接入 paper_trade_engine。下一步如要推进，应先做 shadow tracking。",
        ]
    )


def _main_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "initial_cash" in df.columns:
        sub = df[pd.to_numeric(df["initial_cash"], errors="coerce") == common.MAIN_CASH].copy()
        return sub if not sub.empty else df.copy()
    return df.copy()


def _best_from(name: str, alias: str) -> list[dict]:
    path = REPORT_DIR / name
    if not path.exists():
        return []
    df = _main_rows(pd.read_csv(path))
    if df.empty:
        return []
    df["sort_score"] = pd.to_numeric(df["total_return"], errors="coerce").fillna(-9) + pd.to_numeric(df.get("calmar", 0), errors="coerce").fillna(0) * 0.02
    row = df.sort_values("sort_score", ascending=False).head(1).drop(columns=["sort_score"], errors="ignore")
    return row.to_dict(orient="records")


def overfit_risk(row: pd.Series) -> str:
    trades = float(row.get("trade_count") or 0)
    drawdown = float(row.get("max_drawdown") or 0)
    if trades > 140 or drawdown < -0.15:
        return "high"
    if trades < 10:
        return "medium"
    return "medium"


def main_weakness(row: pd.Series) -> str:
    if not bool(row.get("beat_510300", False)):
        return "does_not_beat_510300"
    if float(row.get("max_drawdown") or 0) < -0.12:
        return "drawdown_too_high"
    if float(row.get("trade_count") or 0) > 140:
        return "turnover_too_high"
    return "research_only_not_executed"


if __name__ == "__main__":
    main()
