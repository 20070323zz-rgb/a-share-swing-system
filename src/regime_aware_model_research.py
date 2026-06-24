"""Phase 4C Alpha: market regime-aware ETF rotation research."""

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
MD_REPORT = REPORT_DIR / "regime_aware_model_research.md"
SUMMARY_CSV = REPORT_DIR / "regime_aware_model_summary.csv"
METRICS_JSON = REPORT_DIR / "regime_aware_model_metrics.json"

STRATEGIES = [
    "static_v2_baseline",
    "risk_on_relaxed_filter_v2",
    "risk_off_defensive_v2",
    "regime_switching_v2",
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
        "safety": safety(),
    }
    common.write_json(METRICS_JSON, payload)
    MD_REPORT.write_text(render_report(payload), encoding="utf-8")
    print(f"written: {MD_REPORT}")
    print(f"written: {SUMMARY_CSV}")
    print(f"written: {METRICS_JSON}")


def enrich_summary(summary: pd.DataFrame) -> pd.DataFrame:
    bench = common.load_510300_benchmark()
    bench_return = float(bench.get("total_return", 0) or 0)
    static_return = float(summary.loc[summary["strategy"] == "static_v2_baseline", "total_return"].iloc[0]) if "static_v2_baseline" in set(summary["strategy"]) else 0.0
    summary = summary.copy()
    summary["beat_510300"] = pd.to_numeric(summary["total_return"], errors="coerce") > bench_return
    summary["beat_v2_baseline"] = pd.to_numeric(summary["total_return"], errors="coerce") > static_return
    summary["ready_for_execution"] = False
    summary["ready_for_shadow"] = (summary["beat_v2_baseline"]) & (pd.to_numeric(summary["max_drawdown"], errors="coerce") > -0.12)
    summary["overfit_risk"] = "medium"
    return summary


def best_candidate(summary: pd.DataFrame) -> dict:
    if summary.empty:
        return {}
    candidates = summary.copy()
    candidates["score"] = pd.to_numeric(candidates["total_return"], errors="coerce").fillna(-9) + pd.to_numeric(candidates["calmar"], errors="coerce").fillna(0) * 0.03
    row = candidates.sort_values("score", ascending=False).iloc[0].to_dict()
    return common.metric_payload(row)


def render_report(payload: dict) -> str:
    best = payload.get("best_candidate", {})
    lines = [
        f"# Regime-aware 模型研究 {payload['generated_at']}",
        "",
        "本研究只使用市场内部日线数据，不使用未来数据，不接执行层。",
        "",
        f"- 最佳候选：{best.get('strategy', 'N/A')}",
        f"- total_return：{common.pct(best.get('total_return'))}",
        f"- max_drawdown：{common.pct(best.get('max_drawdown'))}",
        f"- ready_for_execution：false",
        "",
        "| strategy | return | max_drawdown | calmar | sharpe | trades | avg_exposure | risk_on | neutral | risk_off | shadow |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("strategies", []):
        lines.append(
            f"| {row['strategy']} | {common.pct(row.get('total_return'))} | {common.pct(row.get('max_drawdown'))} | {row.get('calmar', 0):.2f} | {row.get('sharpe', 0):.2f} | {int(row.get('trade_count', 0))} | {common.pct(row.get('exposure_avg', row.get('avg_exposure')))} | {common.pct(row.get('risk_on_return'))} | {common.pct(row.get('neutral_return'))} | {common.pct(row.get('risk_off_return'))} | {row.get('ready_for_shadow')} |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "- 如果 risk-on relaxed 版本收益改善，说明 v2 可能过度防守。",
            "- 如果 risk-off defensive 回撤改善但收益下降，说明防御层更适合作风控展示而非收益主模型。",
            "- 所有候选仍为 research-only，不能接入 paper_trade_engine。",
        ]
    )
    return "\n".join(lines)


def safety() -> dict:
    return {"broker_api": False, "real_order": False, "execution_enabled": False, "paper_files_modified": False}


if __name__ == "__main__":
    main()
