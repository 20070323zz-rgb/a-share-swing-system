"""Phase 4C-2 persistence_breakout_v2 shadow tracking.

Research-only shadow layer. This module reads local ETF data and research
reports, writes shadow signals/portfolio/comparison files, and never writes
paper_trades.csv or paper_positions.csv.
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

import phase4c_alpha_common as common  # noqa: E402
import ranking_model_v2_backtest as base  # noqa: E402


DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"

MODEL_NAME = "persistence_breakout_v2"
INITIAL_CASH = 20_000.0
MAX_HOLDINGS = 3
TARGET_WEIGHT_PER_ETF = 0.20
TARGET_TOTAL_WEIGHT = 0.60
MIN_TRADE_VALUE = 3_000.0

SIGNAL_CSV = REPORT_DIR / "persistence_breakout_shadow_signal.csv"
SIGNAL_MD = REPORT_DIR / "persistence_breakout_shadow_signal.md"
PORTFOLIO_CSV = REPORT_DIR / "persistence_breakout_shadow_portfolio.csv"
PORTFOLIO_MD = REPORT_DIR / "persistence_breakout_shadow_portfolio.md"
TRACKING_CSV = DATA_DIR / "persistence_breakout_shadow_tracking.csv"
COMPARISON_CSV = REPORT_DIR / "model_shadow_comparison.csv"
COMPARISON_MD = REPORT_DIR / "model_shadow_comparison.md"
RULES_MD = REPORT_DIR / "persistence_breakout_shadow_observation_rules.md"
SUMMARY_JSON = REPORT_DIR / "persistence_breakout_shadow_summary.json"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    context = common.load_context()
    dates: list[pd.Timestamp] = context["dates"]
    if not dates:
        raise RuntimeError("no common trading dates available for persistence_breakout shadow")
    latest_date = dates[-1]
    rank_memory = build_rank_memory(context, latest_date)
    regime = common.market_regime(latest_date, context)
    latest_rows = base.build_daily_rows(latest_date, context)
    ranking = common.rank_custom_rows(latest_rows, MODEL_NAME, regime, rank_memory)
    targets = common.select_custom_targets(MODEL_NAME, ranking, {}, {}, regime)

    health = load_data_health_status()
    signal_df = build_signal_frame(latest_date, ranking, targets, rank_memory, health)
    portfolio_df = build_portfolio_frame(latest_date, signal_df, context)
    tracking_df = update_tracking(signal_df, context)
    comparison_df, comparison_summary = build_comparison(signal_df, tracking_df, health)

    signal_df.to_csv(SIGNAL_CSV, index=False)
    portfolio_df.to_csv(PORTFOLIO_CSV, index=False)
    tracking_df.to_csv(TRACKING_CSV, index=False)
    comparison_df.to_csv(COMPARISON_CSV, index=False)

    SIGNAL_MD.write_text(render_signal_report(latest_date, regime, signal_df), encoding="utf-8")
    PORTFOLIO_MD.write_text(render_portfolio_report(latest_date, portfolio_df), encoding="utf-8")
    COMPARISON_MD.write_text(render_comparison_report(latest_date, comparison_df, comparison_summary), encoding="utf-8")
    RULES_MD.write_text(render_observation_rules(), encoding="utf-8")

    selected = signal_df[signal_df["selected"] == True]  # noqa: E712
    summary = {
        "status": "active",
        "model_name": MODEL_NAME,
        "research_only": True,
        "execution_enabled": False,
        "paper_trade_engine_enabled": False,
        "real_trade_enabled": False,
        "initial_cash_assumption": INITIAL_CASH,
        "latest_signal_date": latest_date.strftime("%Y-%m-%d"),
        "market_regime": regime,
        "selected_count": int(len(selected)),
        "selected_symbols": selected["symbol"].astype(str).tolist(),
        "overlap_with_original": int(comparison_summary.get("overlap_with_original", 0)),
        "overlap_with_adjusted": int(comparison_summary.get("overlap_with_adjusted", 0)),
        "overlap_with_top10_diversified": int(comparison_summary.get("overlap_with_top10_diversified", 0)),
        "high_beta_count": int(selected["etf_type"].isin(["theme", "high_beta"]).sum()) if not selected.empty else 0,
        "data_health_caution_count": int((selected["data_health_status"] != "normal").sum()) if not selected.empty else 0,
        "tracking_days": int(tracking_df["date"].nunique()) if not tracking_df.empty else 0,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "summary": "persistence_breakout_v2 is active in shadow tracking only; it is not connected to paper_trade_engine.",
        "signal_report_href": "../reports/persistence_breakout_shadow_signal.md",
        "portfolio_report_href": "../reports/persistence_breakout_shadow_portfolio.md",
        "comparison_report_href": "../reports/model_shadow_comparison.md",
        "observation_rules_href": "../reports/persistence_breakout_shadow_observation_rules.md",
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"persistence_breakout_v2 latest_date: {latest_date.strftime('%Y-%m-%d')}")
    print(f"selected_count: {len(selected)}")
    print(f"written: {SIGNAL_MD}")
    print(f"written: {PORTFOLIO_MD}")
    print(f"written: {COMPARISON_MD}")
    print(f"written: {TRACKING_CSV}")


def build_rank_memory(context: dict, latest_date: pd.Timestamp) -> dict[str, list[int]]:
    dates: list[pd.Timestamp] = context["dates"]
    history = [d for d in dates if d <= latest_date][-6:-1]
    memory: dict[str, list[int]] = {}
    transient_memory: dict[str, list[int]] = {}
    for date in history:
        rows = base.build_daily_rows(date, context)
        regime = common.market_regime(date, context)
        ranked = common.rank_custom_rows(rows, MODEL_NAME, regime, transient_memory)
        for row in ranked[:20]:
            symbol = str(row["symbol"])
            rank = int(row["rank"])
            memory.setdefault(symbol, []).append(rank)
            transient_memory.setdefault(symbol, []).append(rank)
            transient_memory[symbol] = transient_memory[symbol][-5:]
    return {symbol: ranks[-5:] for symbol, ranks in memory.items()}


def build_signal_frame(
    date: pd.Timestamp,
    ranking: list[dict],
    targets: list[dict],
    rank_memory: dict[str, list[int]],
    health: dict[str, str],
) -> pd.DataFrame:
    selected_symbols = {str(row["symbol"]) for row in targets[:MAX_HOLDINGS]}
    rows: list[dict] = []
    created_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in ranking[:20]:
        symbol = str(row["symbol"])
        ranks = rank_memory.get(symbol, [])
        persistence_score = min(sum(1 for rank in ranks[-3:] if rank <= 10) / 3 * 100, 100) if ranks else 0.0
        breakout_confirmed = bool(row.get("strong_trend_confirm")) and float(row.get("ma_distance_20") or 0) > 0
        breakout_score = 100.0 if breakout_confirmed else 30.0 if row.get("trend_confirm") else 0.0
        trend_score = float(row.get("p_trend_slope_20") or 0) * 100
        alpha_score = float(row.get("rank_score") or 0)
        data_health_status = health.get(symbol, "normal")
        selected = symbol in selected_symbols
        filter_reasons = []
        if not row.get("trend_confirm"):
            filter_reasons.append("trend_not_confirmed")
        if float(row.get("amount_ma20") or 0) < 30_000_000:
            filter_reasons.append("liquidity_below_30m")
        if data_health_status != "normal":
            filter_reasons.append(f"data_health_{data_health_status}")
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "model_name": MODEL_NAME,
                "symbol": symbol,
                "name": row.get("name", ""),
                "rank": int(row.get("rank", 999)),
                "alpha_score": round(alpha_score, 4),
                "persistence_score": round(persistence_score, 4),
                "breakout_score": round(breakout_score, 4),
                "trend_score": round(trend_score, 4),
                "final_score": round(alpha_score, 4),
                "selected": bool(selected),
                "selection_reason": selection_reason(row, persistence_score, breakout_confirmed, selected),
                "filter_reasons": "; ".join(filter_reasons),
                "etf_type": row.get("etf_type", ""),
                "group": row.get("group", ""),
                "data_health_status": data_health_status,
                "trend_confirmed": bool(row.get("trend_confirm")),
                "breakout_confirmed": bool(breakout_confirmed),
                "ranking_persistence_confirmed": persistence_score >= 66.0,
                "relative_strength_score": round(float(row.get("p_rs_510300") or 0) * 100, 4),
                "risk_adjusted_momentum": round(float(row.get("risk_adjusted_momentum") or 0), 6),
                "shadow_action": "SHADOW_BUY_CANDIDATE" if selected else "WATCH",
                "execution_enabled": False,
                "created_at": created_at,
            }
        )
    return pd.DataFrame(rows)


def selection_reason(row: dict, persistence_score: float, breakout_confirmed: bool, selected: bool) -> str:
    if not selected:
        return "watch_only_not_selected"
    parts = [
        f"rank_{int(row.get('rank', 999))}",
        f"final_score_{float(row.get('rank_score') or 0):.2f}",
        f"persistence_{persistence_score:.1f}",
    ]
    if breakout_confirmed:
        parts.append("breakout_confirmed")
    if row.get("trend_confirm"):
        parts.append("trend_confirmed")
    return "; ".join(parts)


def build_portfolio_frame(date: pd.Timestamp, signal_df: pd.DataFrame, context: dict) -> pd.DataFrame:
    selected = signal_df[signal_df["selected"] == True].copy()  # noqa: E712
    rows: list[dict] = []
    for _, signal in selected.iterrows():
        symbol = str(signal["symbol"])
        price = latest_close(symbol, date, context)
        target_value = INITIAL_CASH * TARGET_WEIGHT_PER_ETF
        quantity = int(math.floor(target_value / max(price, 0.0001) / base.LOT_SIZE) * base.LOT_SIZE)
        estimated_value = quantity * price
        open_allowed = estimated_value >= MIN_TRADE_VALUE
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "model_name": MODEL_NAME,
                "symbol": symbol,
                "name": signal.get("name", ""),
                "rank": signal.get("rank"),
                "final_score": signal.get("final_score"),
                "target_weight": TARGET_WEIGHT_PER_ETF,
                "target_value": target_value,
                "shadow_price": round(price, 4),
                "lot_size": base.LOT_SIZE,
                "shadow_quantity": quantity if open_allowed else 0,
                "estimated_position_value": round(estimated_value if open_allowed else 0.0, 2),
                "min_trade_value": MIN_TRADE_VALUE,
                "execution_enabled": False,
                "paper_trade_engine_enabled": False,
                "real_trade_enabled": False,
                "shadow_action": "OPEN_SHADOW_POSITION" if open_allowed else "SKIP_MIN_TRADE_VALUE",
                "selection_reason": signal.get("selection_reason", ""),
            }
        )
    return pd.DataFrame(rows, columns=portfolio_columns())


def portfolio_columns() -> list[str]:
    return [
        "date",
        "model_name",
        "symbol",
        "name",
        "rank",
        "final_score",
        "target_weight",
        "target_value",
        "shadow_price",
        "lot_size",
        "shadow_quantity",
        "estimated_position_value",
        "min_trade_value",
        "execution_enabled",
        "paper_trade_engine_enabled",
        "real_trade_enabled",
        "shadow_action",
        "selection_reason",
    ]


def update_tracking(signal_df: pd.DataFrame, context: dict) -> pd.DataFrame:
    selected = signal_df[signal_df["selected"] == True].copy()  # noqa: E712
    tracking_rows: list[dict] = []
    if TRACKING_CSV.exists():
        tracking_rows.extend(pd.read_csv(TRACKING_CSV, dtype={"symbol": str}).to_dict(orient="records"))
    for _, signal in selected.iterrows():
        row = signal.to_dict()
        row.update(
            {
                "selected_rank": row.get("rank"),
                "selected_final_score": row.get("final_score"),
                "initial_cash_assumption": INITIAL_CASH,
                "target_weight": TARGET_WEIGHT_PER_ETF,
                "target_total_weight": TARGET_TOTAL_WEIGHT,
                "max_holdings": MAX_HOLDINGS,
            }
        )
        tracking_rows.append(row)
    if not tracking_rows:
        return pd.DataFrame(columns=tracking_columns())
    df = pd.DataFrame(tracking_rows)
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date", "symbol"])
    df = df.drop_duplicates(["date", "model_name", "symbol"], keep="last").reset_index(drop=True)
    for window in [1, 3, 5, 10, 20]:
        df[f"forward_return_{window}d"] = df.apply(lambda r: forward_return(str(r["symbol"]), r["date"], window, context), axis=1)
        df[f"benchmark_510300_return_{window}d"] = df.apply(lambda r: forward_return("510300", r["date"], window, context), axis=1)
    df["excess_return_vs_510300_10d"] = pd.to_numeric(df["forward_return_10d"], errors="coerce") - pd.to_numeric(
        df["benchmark_510300_return_10d"], errors="coerce"
    )
    for col in tracking_columns():
        if col not in df.columns:
            df[col] = ""
    return df[tracking_columns()]


def tracking_columns() -> list[str]:
    return [
        "date",
        "model_name",
        "symbol",
        "name",
        "selected_rank",
        "selected_final_score",
        "etf_type",
        "group",
        "data_health_status",
        "initial_cash_assumption",
        "target_weight",
        "target_total_weight",
        "max_holdings",
        "selection_reason",
        "forward_return_1d",
        "forward_return_3d",
        "forward_return_5d",
        "forward_return_10d",
        "forward_return_20d",
        "benchmark_510300_return_1d",
        "benchmark_510300_return_3d",
        "benchmark_510300_return_5d",
        "benchmark_510300_return_10d",
        "benchmark_510300_return_20d",
        "excess_return_vs_510300_10d",
        "execution_enabled",
        "created_at",
    ]


def build_comparison(signal_df: pd.DataFrame, tracking_df: pd.DataFrame, health: dict[str, str]) -> tuple[pd.DataFrame, dict]:
    persistence = selected_symbols_from_signal(signal_df)
    original = top_symbols_from_strategy_preview("original_rank")
    adjusted = top_symbols_from_strategy_preview("adjusted_rank_preview")
    top10 = selected_top10_diversified_symbols()
    benchmark = ["510300"]
    latest_tracking = latest_tracking_rows(tracking_df)
    rows = []
    for model, symbols in [
        (MODEL_NAME, persistence),
        ("original_ranking", original),
        ("adjusted_preview_ranking", adjusted),
        ("top10_diversified_filter_v2", top10),
        ("buy_and_hold_510300", benchmark),
    ]:
        rows.append(
            {
                "date": signal_df["date"].iloc[0] if not signal_df.empty else "",
                "model_name": model,
                "selected_symbols": " ".join(symbols),
                "selected_count": len(symbols),
                "overlap_with_persistence": len(set(symbols) & set(persistence)),
                "overlap_symbols": " ".join(sorted(set(symbols) & set(persistence))),
                "high_beta_count": count_high_beta(symbols, signal_df),
                "data_health_caution_count": sum(1 for symbol in symbols if health.get(symbol, "normal") != "normal"),
                "forward_return_1d_mean": mean_forward(latest_tracking, symbols, "forward_return_1d"),
                "forward_return_3d_mean": mean_forward(latest_tracking, symbols, "forward_return_3d"),
                "forward_return_5d_mean": mean_forward(latest_tracking, symbols, "forward_return_5d"),
                "forward_return_10d_mean": mean_forward(latest_tracking, symbols, "forward_return_10d"),
                "excess_return_vs_510300_10d_mean": mean_forward(latest_tracking, symbols, "excess_return_vs_510300_10d"),
                "execution_enabled": False,
                "research_only": True,
            }
        )
    summary = {
        "overlap_with_original": len(set(persistence) & set(original)),
        "overlap_with_adjusted": len(set(persistence) & set(adjusted)),
        "overlap_with_top10_diversified": len(set(persistence) & set(top10)),
    }
    return pd.DataFrame(rows), summary


def selected_symbols_from_signal(signal_df: pd.DataFrame) -> list[str]:
    if signal_df.empty:
        return []
    return signal_df[signal_df["selected"] == True]["symbol"].astype(str).str.zfill(6).tolist()  # noqa: E712


def top_symbols_from_strategy_preview(rank_col: str) -> list[str]:
    path = REPORT_DIR / "strategy_enhancement_preview.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path, dtype={"symbol": str})
    if rank_col not in df.columns or df.empty:
        return []
    if "date" in df.columns:
        latest = str(df["date"].max())
        df = df[df["date"].astype(str) == latest]
    df[rank_col] = pd.to_numeric(df[rank_col], errors="coerce")
    return df.dropna(subset=[rank_col]).sort_values(rank_col).head(MAX_HOLDINGS)["symbol"].astype(str).str.zfill(6).tolist()


def selected_top10_diversified_symbols() -> list[str]:
    path = REPORT_DIR / "top10_candidate_filter_analysis.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path, dtype={"symbol": str})
    if df.empty:
        return []
    if "date" in df.columns:
        latest = str(df["date"].max())
        df = df[df["date"].astype(str) == latest]
    if "selected" in df.columns:
        df = df[df["selected"].astype(str).str.lower().isin(["true", "1", "yes"])]
    return df.sort_values("rank").head(MAX_HOLDINGS)["symbol"].astype(str).str.zfill(6).tolist()


def latest_tracking_rows(tracking_df: pd.DataFrame) -> pd.DataFrame:
    if tracking_df.empty:
        return tracking_df
    latest = tracking_df["date"].max()
    return tracking_df[tracking_df["date"] == latest].copy()


def count_high_beta(symbols: list[str], signal_df: pd.DataFrame) -> int:
    meta: dict[str, str] = {}
    if not signal_df.empty and "etf_type" in signal_df.columns:
        meta.update(signal_df.set_index("symbol")["etf_type"].astype(str).to_dict())
    pool_path = DATA_DIR / "backtest_trade_pool.csv"
    if pool_path.exists():
        pool = pd.read_csv(pool_path, dtype=str).fillna("")
        if {"symbol", "etf_type"}.issubset(pool.columns):
            meta.update(pool.set_index("symbol")["etf_type"].astype(str).to_dict())
    return sum(1 for symbol in symbols if str(meta.get(symbol, "")) in {"theme", "high_beta"})


def mean_forward(df: pd.DataFrame, symbols: list[str], column: str) -> float | str:
    if df.empty or column not in df.columns or not symbols:
        return ""
    sub = df[df["symbol"].astype(str).isin(symbols)]
    values = pd.to_numeric(sub[column], errors="coerce").dropna()
    return round(float(values.mean()), 6) if not values.empty else ""


def load_data_health_status() -> dict[str, str]:
    path = REPORT_DIR / "latest_data_health.md"
    status: dict[str, str] = {}
    if not path.exists():
        return status
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 9 or parts[0] == "代码":
            continue
        symbol = parts[0].strip()
        raw = parts[8].strip()
        if raw == "正常":
            status[symbol] = "normal"
        elif raw == "提醒":
            status[symbol] = "caution"
        elif raw:
            status[symbol] = "error"
    return status


def latest_close(symbol: str, date: pd.Timestamp, context: dict) -> float:
    df = context["price_data"].get(symbol)
    if df is None or df.empty:
        return 0.0
    rows = df[pd.to_datetime(df["date"]) <= pd.Timestamp(date)]
    if rows.empty:
        return 0.0
    return float(rows.iloc[-1]["close"])


def forward_return(symbol: str, date: str, window: int, context: dict) -> float | str:
    df = context["price_data"].get(symbol)
    if df is None or df.empty:
        return ""
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    match = frame.index[frame["date"] == pd.Timestamp(date)]
    if len(match) == 0:
        return ""
    idx = int(match[0])
    target_idx = idx + window
    if target_idx >= len(frame):
        return ""
    start = float(frame.loc[idx, "close"])
    end = float(frame.loc[target_idx, "close"])
    if start <= 0:
        return ""
    return round(end / start - 1, 6)


def render_signal_report(date: pd.Timestamp, regime: str, signal_df: pd.DataFrame) -> str:
    selected = signal_df[signal_df["selected"] == True] if not signal_df.empty else pd.DataFrame()  # noqa: E712
    lines = [
        f"# persistence_breakout_v2 Shadow Signal {date.strftime('%Y-%m-%d')}",
        "",
        "本报告只做研究影子跟踪，不接券商 API，不真实下单，不写 paper_trades.csv / paper_positions.csv。",
        "",
        f"- model_name: {MODEL_NAME}",
        f"- market_regime: {regime}",
        f"- initial_cash_assumption: {INITIAL_CASH:.0f}",
        f"- selected_count: {len(selected)}",
        "- execution_enabled: false",
        "- ready_for_preview: false",
        "- ready_for_execution: false",
        "",
        "## Selected Shadow Candidates",
    ]
    lines.append(markdown_table(selected[["rank", "symbol", "name", "group", "etf_type", "final_score", "persistence_score", "breakout_confirmed", "data_health_status", "selection_reason"]]))
    lines.extend(["", "## Top 20 Signal Rows", markdown_table(signal_df.head(20))])
    return "\n".join(lines) + "\n"


def render_portfolio_report(date: pd.Timestamp, portfolio_df: pd.DataFrame) -> str:
    return "\n".join(
        [
            f"# persistence_breakout_v2 Shadow Portfolio {date.strftime('%Y-%m-%d')}",
            "",
            "本影子组合只用于观察，不执行交易，不写模拟盘正式持仓。",
            "",
            f"- initial_cash: {INITIAL_CASH:.0f}",
            f"- max_holdings: {MAX_HOLDINGS}",
            f"- target_weight_per_etf: {TARGET_WEIGHT_PER_ETF:.0%}",
            f"- target_total_weight: {TARGET_TOTAL_WEIGHT:.0%}",
            f"- min_trade_value: {MIN_TRADE_VALUE:.0f}",
            "- execution_enabled: false",
            "",
            markdown_table(portfolio_df),
        ]
    ) + "\n"


def render_comparison_report(date: pd.Timestamp, comparison_df: pd.DataFrame, summary: dict) -> str:
    return "\n".join(
        [
            f"# Model Shadow Comparison {date.strftime('%Y-%m-%d')}",
            "",
            "对比 persistence_breakout_v2 与 original / adjusted preview / top10_diversified_filter_v2 / 510300。仅研究，不接执行层。",
            "",
            f"- overlap_with_original: {summary.get('overlap_with_original', 0)}",
            f"- overlap_with_adjusted: {summary.get('overlap_with_adjusted', 0)}",
            f"- overlap_with_top10_diversified: {summary.get('overlap_with_top10_diversified', 0)}",
            "- execution_enabled: false",
            "",
            markdown_table(comparison_df),
        ]
    ) + "\n"


def render_observation_rules() -> str:
    return """# persistence_breakout_v2 Shadow Observation Rules

本规则只用于研究观察，不修改 BUY ranking、paper_trade_engine、paper_trades.csv 或 paper_positions.csv。

## 观察期
- 最少连续观察 20 个交易日。
- 同时记录 1/3/5/10/20 日未来收益，并与 510300 对比。
- 至少完成一个包含 risk_on / neutral / risk_off 的市场状态样本后，再讨论是否进入 preview。

## 可进入 preview 的最低条件
- 10 日平均超额收益稳定为正。
- selected ETF 的 data_health caution 数量低。
- high_beta 暴露没有明显放大回撤。
- 与 original / adjusted / top10_diversified 的差异能解释，而不是随机换仓。

## 当前结论
- ready_for_preview=false。
- ready_for_execution=false。
- execution_enabled=false。
- paper_trade_engine_enabled=false。
- real_trade_enabled=false。
"""


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
