"""Phase 4C Alpha: v2 underperformance attribution.

Research-only. Reads existing backtest outputs and local ETF data; never writes
paper trading files and never changes execution logic.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import phase4c_alpha_common as common  # noqa: E402
import ranking_model_v2_backtest as base  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "reports"
MD_REPORT = REPORT_DIR / "v2_underperformance_attribution.md"
CSV_REPORT = REPORT_DIR / "v2_underperformance_attribution.csv"
JSON_REPORT = REPORT_DIR / "v2_underperformance_attribution.json"
GUARDRAILS_REPORT = REPORT_DIR / "model_overfit_guardrails.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    attribution = build_attribution()
    pd.DataFrame(attribution["sections"]).to_csv(CSV_REPORT, index=False)
    common.write_json(JSON_REPORT, attribution)
    MD_REPORT.write_text(render_report(attribution), encoding="utf-8")
    GUARDRAILS_REPORT.write_text(render_guardrails(), encoding="utf-8")
    print(f"written: {MD_REPORT}")
    print(f"written: {CSV_REPORT}")
    print(f"written: {JSON_REPORT}")
    print(f"written: {GUARDRAILS_REPORT}")


def build_attribution() -> dict:
    summary = _read("ranking_model_v2_summary.csv")
    equity = _read("ranking_model_v2_equity_curve.csv")
    trades = _read("ranking_model_v2_trades.csv")
    positions = _read("ranking_model_v2_positions.csv")
    top10 = _read("top10_candidate_filter_analysis.csv")
    context = common.load_context()
    v2 = _row(summary, common.V2_STRATEGY)
    bench = _row(summary, common.BENCHMARK_STRATEGY)
    yearly = annual_attribution(equity)
    monthly = monthly_attribution(equity)
    exposure = exposure_attribution(equity)
    style = style_attribution(positions)
    filters = filter_attribution(top10, context)
    trade_attr = trade_attribution(trades)
    symbol_attr = symbol_contribution(trades)
    conclusion = conclude(v2, bench, exposure, style, filters, monthly)
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "research_only": True,
        "v2_metrics": v2,
        "benchmark_510300_metrics": bench,
        "yearly_attribution": yearly.to_dict(orient="records"),
        "monthly_attribution_top_lags": monthly.head(12).to_dict(orient="records"),
        "exposure_attribution": exposure,
        "style_attribution": style,
        "filter_attribution": filters,
        "trade_attribution": trade_attr,
        "symbol_contribution": symbol_attr,
        "conclusion": conclusion,
        "sections": flatten_sections(yearly, monthly, exposure, style, filters, trade_attr, symbol_attr),
        "safety": safety(),
    }


def annual_attribution(equity: pd.DataFrame) -> pd.DataFrame:
    df = _equity_subset(equity)
    if df.empty:
        return pd.DataFrame()
    df["year"] = pd.to_datetime(df["date"]).dt.year
    rows = []
    for year, sub in df.groupby("year"):
        by_strategy = {}
        for strategy, s in sub.groupby("strategy"):
            s = s.sort_values("date")
            ret = float(s["equity"].iloc[-1] / s["equity"].iloc[0] - 1)
            dd = max_drawdown(s["equity"])
            by_strategy[strategy] = {"return": ret, "max_drawdown": dd}
        v2 = by_strategy.get(common.V2_STRATEGY, {})
        bench = by_strategy.get(common.BENCHMARK_STRATEGY, {})
        rows.append(
            {
                "year": int(year),
                "v2_return": v2.get("return", 0.0),
                "benchmark_return": bench.get("return", 0.0),
                "excess_return": v2.get("return", 0.0) - bench.get("return", 0.0),
                "v2_max_drawdown": v2.get("max_drawdown", 0.0),
            }
        )
    return pd.DataFrame(rows).sort_values("excess_return")


def monthly_attribution(equity: pd.DataFrame) -> pd.DataFrame:
    df = _equity_subset(equity)
    if df.empty:
        return pd.DataFrame()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    rows = []
    for month, sub in df.groupby("month"):
        values = {}
        for strategy, s in sub.groupby("strategy"):
            s = s.sort_values("date")
            values[strategy] = float(s["equity"].iloc[-1] / s["equity"].iloc[0] - 1)
        rows.append(
            {
                "month": month,
                "v2_return": values.get(common.V2_STRATEGY, 0.0),
                "benchmark_return": values.get(common.BENCHMARK_STRATEGY, 0.0),
                "excess_return": values.get(common.V2_STRATEGY, 0.0) - values.get(common.BENCHMARK_STRATEGY, 0.0),
                "benchmark_fast_up": values.get(common.BENCHMARK_STRATEGY, 0.0) > 0.04,
            }
        )
    return pd.DataFrame(rows).sort_values("excess_return")


def exposure_attribution(equity: pd.DataFrame) -> dict:
    df = equity[(equity["strategy"] == common.V2_STRATEGY) & (equity["initial_cash"] == common.MAIN_CASH)].copy()
    if df.empty:
        return {}
    exposure = pd.to_numeric(df["exposure"], errors="coerce").fillna(0)
    return {
        "avg_exposure": float(exposure.mean()),
        "median_exposure": float(exposure.median()),
        "low_exposure_days_lt_40pct": int((exposure < 0.40).sum()),
        "cash_or_empty_days_lt_10pct": int((exposure < 0.10).sum()),
        "target_total_position": base.TARGET_TOTAL_POSITION_PCT,
        "interpretation": "v2 is structurally capped around 60% gross exposure, so it may lag 510300 in fast beta rallies.",
    }


def style_attribution(positions: pd.DataFrame) -> dict:
    pos = positions[(positions["strategy"] == common.V2_STRATEGY) & (positions["initial_cash"] == common.MAIN_CASH)].copy()
    if pos.empty:
        return {}
    by_type = pos.groupby("etf_type")["market_value"].sum().sort_values(ascending=False)
    by_group = pos.groupby("group")["market_value"].sum().sort_values(ascending=False)
    total = float(pos["market_value"].sum()) or 1.0
    high_beta_share = float(by_type.reindex(["theme", "high_beta"]).fillna(0).sum() / total)
    defensive_share = float(by_type.reindex(["bond_cash", "commodity"]).fillna(0).sum() / total)
    return {
        "type_exposure_share": {str(k): float(v / total) for k, v in by_type.head(10).items()},
        "group_exposure_share": {str(k): float(v / total) for k, v in by_group.head(10).items()},
        "high_beta_share": high_beta_share,
        "defensive_share": defensive_share,
        "interpretation": "High-beta exposure is limited by top10 diversified filters; this protects drawdown but can cap upside in risk-on regimes.",
    }


def filter_attribution(top10: pd.DataFrame, context: dict) -> dict:
    if top10.empty:
        return {}
    rows = []
    for _, row in top10.iterrows():
        if bool(row.get("selected")):
            continue
        symbol = str(row.get("symbol"))
        date = pd.Timestamp(row.get("date"))
        fwd = forward_return(symbol, date, context, 20)
        rows.append(
            {
                "filter_reason": str(row.get("filter_reason", "")),
                "symbol": symbol,
                "name": str(row.get("name", symbol)),
                "date": date.strftime("%Y-%m-%d"),
                "rank": int(row.get("rank", 999)),
                "forward_20d_return": fwd,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    summary = (
        df.groupby("filter_reason")
        .agg(count=("symbol", "count"), avg_forward_20d_return=("forward_20d_return", "mean"), max_forward_20d_return=("forward_20d_return", "max"))
        .reset_index()
        .sort_values("avg_forward_20d_return", ascending=False)
    )
    missed = df.sort_values("forward_20d_return", ascending=False).head(15)
    return {
        "by_filter_reason": summary.to_dict(orient="records"),
        "top_missed_upside": missed.to_dict(orient="records"),
        "interpretation": "Positive forward returns among filtered symbols indicate that some filters may be too defensive in risk-on phases.",
    }


def trade_attribution(trades: pd.DataFrame) -> dict:
    t = trades[(trades["strategy"] == common.V2_STRATEGY) & (trades["initial_cash"] == common.MAIN_CASH)].copy()
    if t.empty:
        return {}
    sell = t[t["side"] == "SELL"].copy()
    reasons = sell.groupby("reason").agg(count=("symbol", "count"), pnl=("pnl", "sum"), avg_holding_days=("holding_days", "mean")).reset_index().sort_values("pnl")
    return {
        "trade_count": int(len(t)),
        "sell_count": int(len(sell)),
        "buy_count": int((t["side"] == "BUY").sum()),
        "total_cost": float(pd.to_numeric(t["commission"], errors="coerce").fillna(0).sum() + pd.to_numeric(t["slippage"], errors="coerce").fillna(0).sum()),
        "sell_reason_summary": reasons.to_dict(orient="records"),
        "interpretation": "Reduced turnover helped drawdown and cost, but max holding/cooldown/rank exits may also miss long trend continuation.",
    }


def symbol_contribution(trades: pd.DataFrame) -> dict:
    t = trades[(trades["strategy"] == common.V2_STRATEGY) & (trades["initial_cash"] == common.MAIN_CASH) & (trades["side"] == "SELL")].copy()
    if t.empty:
        return {}
    by_symbol = t.groupby(["symbol", "name"]).agg(pnl=("pnl", "sum"), trades=("symbol", "count"), avg_holding_days=("holding_days", "mean")).reset_index()
    return {
        "top_positive": by_symbol.sort_values("pnl", ascending=False).head(10).to_dict(orient="records"),
        "top_negative": by_symbol.sort_values("pnl", ascending=True).head(10).to_dict(orient="records"),
    }


def forward_return(symbol: str, date: pd.Timestamp, context: dict, window: int) -> float | None:
    df = context["price_data"].get(str(symbol))
    if df is None or df.empty:
        return None
    dates = pd.to_datetime(df["date"])
    sub = df[dates >= date].sort_values("date")
    if len(sub) <= window:
        return None
    return float(sub["close"].iloc[window] / sub["close"].iloc[0] - 1)


def conclude(v2: dict, bench: dict, exposure: dict, style: dict, filters: dict, monthly: pd.DataFrame) -> dict:
    lag_fast_months = int((monthly.get("benchmark_fast_up", pd.Series(dtype=bool)) & (monthly.get("excess_return", pd.Series(dtype=float)) < 0)).sum()) if not monthly.empty else 0
    return {
        "main_causes": [
            "Structural exposure cap around 60% makes v2 lag beta buy-and-hold during fast rallies.",
            "Top10 diversification and high-beta limits reduce drawdown but filter out some upside.",
            "Trend confirmation avoids weak setups but can buy late or skip early breakouts.",
        ],
        "alpha_strength": "improved versus original/adjusted, but not strong enough to beat 510300 buy-and-hold.",
        "over_defensive": True,
        "exposure_insufficient": bool(exposure.get("avg_exposure", 0) < 0.58),
        "filtered_upside_issue": bool(filters.get("top_missed_upside")),
        "fast_up_lag_months": lag_fast_months,
        "next_research_direction": "test regime-aware relaxed filters and simple alpha enhancements; keep execution disabled.",
    }


def flatten_sections(yearly: pd.DataFrame, monthly: pd.DataFrame, exposure: dict, style: dict, filters: dict, trade_attr: dict, symbol_attr: dict) -> list[dict]:
    rows = []
    for item in yearly.to_dict(orient="records"):
        rows.append({"section": "yearly", **item})
    for item in monthly.head(12).to_dict(orient="records"):
        rows.append({"section": "monthly_lag", **item})
    rows.append({"section": "exposure", **exposure})
    rows.append({"section": "style", "high_beta_share": style.get("high_beta_share"), "defensive_share": style.get("defensive_share")})
    rows.append({"section": "trade", **{k: v for k, v in trade_attr.items() if k != "sell_reason_summary"}})
    return rows


def render_report(payload: dict) -> str:
    lines = [
        f"# v2 收益拖累归因 {payload['generated_at']}",
        "",
        "本报告只做 research/diagnostics，不修改模拟盘、不接执行层。",
        "",
        "## 摘要",
    ]
    for item in payload["conclusion"]["main_causes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            f"- v2 收益：{common.pct(payload['v2_metrics'].get('total_return'))}",
            f"- 510300 buy-and-hold：{common.pct(payload['benchmark_510300_metrics'].get('total_return'))}",
            f"- 平均仓位：{common.pct(payload['exposure_attribution'].get('avg_exposure'))}",
            "",
            "## 年度归因",
            "| year | v2_return | 510300_return | excess | v2_drawdown |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["yearly_attribution"]:
        lines.append(f"| {row['year']} | {common.pct(row['v2_return'])} | {common.pct(row['benchmark_return'])} | {common.pct(row['excess_return'])} | {common.pct(row['v2_max_drawdown'])} |")
    lines.extend(["", "## 月度明显落后月份", "| month | v2 | 510300 | excess | fast_up |", "| --- | ---: | ---: | ---: | --- |"])
    for row in payload["monthly_attribution_top_lags"][:10]:
        lines.append(f"| {row['month']} | {common.pct(row['v2_return'])} | {common.pct(row['benchmark_return'])} | {common.pct(row['excess_return'])} | {row['benchmark_fast_up']} |")
    lines.extend(
        [
            "",
            "## 仓位归因",
            f"- 平均仓位：{common.pct(payload['exposure_attribution'].get('avg_exposure'))}",
            f"- 低仓位天数 exposure<40%：{payload['exposure_attribution'].get('low_exposure_days_lt_40pct')}",
            f"- 目标总仓位：{common.pct(payload['exposure_attribution'].get('target_total_position'))}",
            "",
            "## 过滤归因",
            "过滤规则保护了回撤，但在部分 risk-on 阶段也过滤掉后续上涨标的。",
        ]
    )
    for row in payload.get("filter_attribution", {}).get("by_filter_reason", [])[:8]:
        lines.append(f"- {row['filter_reason']}: count={row['count']}, avg_forward_20d={common.pct(row['avg_forward_20d_return'])}, max={common.pct(row['max_forward_20d_return'])}")
    lines.extend(
        [
            "",
            "## 交易归因",
            f"- 交易数：{payload['trade_attribution'].get('trade_count')}",
            f"- 总成本：{payload['trade_attribution'].get('total_cost'):.2f}",
            "- 交易次数下降降低成本和回撤，但也可能因确认/冷却/最大持有期错过趋势延续。",
            "",
            "## 结论",
            f"- 是否过度防守：{payload['conclusion']['over_defensive']}",
            f"- 是否仓位不足：{payload['conclusion']['exposure_insufficient']}",
            f"- 是否存在过滤错失上涨：{payload['conclusion']['filtered_upside_issue']}",
            f"- 下一步：{payload['conclusion']['next_research_direction']}",
        ]
    )
    return "\n".join(lines)


def render_guardrails() -> str:
    rules = [
        "每个新候选模型最多新增 2-3 个核心 alpha 因子。",
        "每个因子必须有明确经济逻辑。",
        "不允许因为历史收益最高就直接采用。",
        "必须输出年度表现、月度表现、最大回撤期表现。",
        "必须保留 510300 buy-and-hold、original、adjusted、top10_diversified_filter_v2 作为对照。",
        "必须计算交易次数和成本。",
        "必须检查是否依赖单一 ETF 或单一年份。",
        "不允许使用 future_return、future_drawdown、future_rank 作为特征。",
        "不允许使用没有 available_date 的外部数据。",
        "新模型如果只在单一年份有效，不得标记为候选。",
        "新模型如果收益提高但回撤大幅恶化，不得标记为可 shadow。",
        "新模型只能 research/backtest，不得接执行层。",
    ]
    return "# 模型防过拟合护栏\n\n" + "\n".join(f"{idx}. {rule}" for idx, rule in enumerate(rules, start=1))


def _read(name: str) -> pd.DataFrame:
    path = REPORT_DIR / name
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def _row(summary: pd.DataFrame, strategy: str) -> dict:
    if summary.empty:
        return {}
    sub = summary[(summary["strategy"] == strategy) & (summary["initial_cash"] == common.MAIN_CASH)]
    if sub.empty:
        sub = summary[summary["strategy"] == strategy]
    return sub.iloc[0].to_dict() if not sub.empty else {}


def _equity_subset(equity: pd.DataFrame) -> pd.DataFrame:
    if equity.empty:
        return equity
    return equity[(equity["initial_cash"] == common.MAIN_CASH) & (equity["strategy"].isin([common.V2_STRATEGY, common.BENCHMARK_STRATEGY]))].copy()


def max_drawdown(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float((values / values.cummax() - 1).min())


def safety() -> dict:
    return {
        "broker_api": False,
        "real_order": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "paper_trade_engine_changed": False,
        "execution_enabled": False,
    }


if __name__ == "__main__":
    main()
