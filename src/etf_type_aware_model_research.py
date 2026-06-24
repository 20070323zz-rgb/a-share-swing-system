"""Phase 4C Alpha: ETF type-aware ranking model research."""

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
MD_REPORT = REPORT_DIR / "etf_type_aware_model_research.md"
SUMMARY_CSV = REPORT_DIR / "etf_type_aware_model_summary.csv"
METRICS_JSON = REPORT_DIR / "etf_type_aware_model_metrics.json"

STRATEGIES = ["single_score_v2_baseline", "type_weighted_score_v2", "type_regime_combined_v2"]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    context = common.load_context()
    results = [common.run_research_strategy(strategy, context) for strategy in STRATEGIES]
    summary, equity, trades, yearly = common.result_frames(results)
    type_contrib = type_contribution(trades)
    summary = enrich_summary(summary)
    summary.to_csv(SUMMARY_CSV, index=False)
    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "research_only": True,
        "strategies": summary.to_dict(orient="records"),
        "best_candidate": best_candidate(summary),
        "type_contribution": type_contrib,
        "yearly": yearly.to_dict(orient="records"),
        "safety": {"execution_enabled": False, "broker_api": False, "real_order": False},
    }
    common.write_json(METRICS_JSON, payload)
    MD_REPORT.write_text(render_report(payload), encoding="utf-8")
    print(f"written: {MD_REPORT}")
    print(f"written: {SUMMARY_CSV}")
    print(f"written: {METRICS_JSON}")


def enrich_summary(summary: pd.DataFrame) -> pd.DataFrame:
    bench = common.load_510300_benchmark()
    bench_return = float(bench.get("total_return", 0) or 0)
    baseline_return = float(summary.loc[summary["strategy"] == "single_score_v2_baseline", "total_return"].iloc[0]) if "single_score_v2_baseline" in set(summary["strategy"]) else 0
    out = summary.copy()
    out["beat_510300"] = pd.to_numeric(out["total_return"], errors="coerce") > bench_return
    out["beat_v2_baseline"] = pd.to_numeric(out["total_return"], errors="coerce") > baseline_return
    out["ready_for_execution"] = False
    out["ready_for_shadow"] = out["beat_v2_baseline"] & (pd.to_numeric(out["max_drawdown"], errors="coerce") > -0.12)
    out["overfit_risk"] = "medium" 
    return out


def type_contribution(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {}
    # Map type from sell rows by symbol from trade name via current trade pool if possible.
    pool = pd.read_csv(PROJECT_ROOT / "data" / "backtest_trade_pool.csv", dtype=str).fillna("")
    meta = pool.set_index("symbol")["etf_type"].to_dict()
    rows = []
    sells = trades[trades["side"] == "SELL"].copy()
    if sells.empty:
        return {}
    sells["etf_type"] = sells["symbol"].astype(str).map(meta).fillna("unknown")
    grouped = sells.groupby(["strategy", "etf_type"]).agg(pnl=("pnl", "sum"), trades=("symbol", "count"), avg_holding_days=("holding_days", "mean")).reset_index()
    for _, row in grouped.iterrows():
        rows.append(row.to_dict())
    return {"by_strategy_type": rows}


def best_candidate(summary: pd.DataFrame) -> dict:
    if summary.empty:
        return {}
    row = summary.sort_values(["ready_for_shadow", "total_return", "calmar"], ascending=[False, False, False]).iloc[0]
    return common.metric_payload(row)


def render_report(payload: dict) -> str:
    best = payload.get("best_candidate", {})
    lines = [
        f"# ETF type-aware 模型研究 {payload['generated_at']}",
        "",
        "本研究只使用现有合格 trade_pool 和 ETF 分类，不扩池，不接执行层。",
        "",
        f"- 最佳候选：{best.get('strategy', 'N/A')}",
        f"- total_return：{common.pct(best.get('total_return'))}",
        f"- max_drawdown：{common.pct(best.get('max_drawdown'))}",
        "",
        "| strategy | return | max_drawdown | calmar | trades | avg_exposure | beat_v2 | shadow |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload.get("strategies", []):
        lines.append(
            f"| {row['strategy']} | {common.pct(row.get('total_return'))} | {common.pct(row.get('max_drawdown'))} | {row.get('calmar', 0):.2f} | {int(row.get('trade_count', 0))} | {common.pct(row.get('exposure_avg', row.get('avg_exposure')))} | {row.get('beat_v2_baseline')} | {row.get('ready_for_shadow')} |"
        )
    lines.extend(
        [
            "",
            "## 类型贡献",
            "不同 ETF 类型使用不同权重可以改善模型解释性，但样本仍短，不能直接接执行层。",
        ]
    )
    for row in payload.get("type_contribution", {}).get("by_strategy_type", [])[:20]:
        lines.append(f"- {row['strategy']} / {row['etf_type']}: pnl={row['pnl']:.2f}, trades={int(row['trades'])}, avg_holding_days={row['avg_holding_days']:.1f}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
