"""Track filtered high-score candidates for persistence_breakout_v2.

Research-only diagnostics. Forward returns are labels for later evaluation,
never same-day model features. This module never writes paper trading files,
never connects to broker APIs, and never changes persistence_breakout_v2 rules.
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


DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"

MODEL_NAME = "persistence_breakout_v2"
SIGNAL_CSV = REPORT_DIR / "persistence_breakout_shadow_signal.csv"
SHADOW_SUMMARY_JSON = REPORT_DIR / "persistence_breakout_shadow_summary.json"
TRACKING_CSV = DATA_DIR / "missed_opportunity_tracking.csv"

REPORT_MD = REPORT_DIR / "missed_opportunity_tracker.md"
REPORT_CSV = REPORT_DIR / "missed_opportunity_tracker.csv"
REPORT_JSON = REPORT_DIR / "missed_opportunity_tracker.json"
BY_REASON_MD = REPORT_DIR / "missed_opportunity_by_filter_reason.md"
BY_REASON_CSV = REPORT_DIR / "missed_opportunity_by_filter_reason.csv"
RISK_ON_MD = REPORT_DIR / "risk_on_empty_signal_analysis.md"
RISK_ON_CSV = REPORT_DIR / "risk_on_empty_signal_analysis.csv"
SELECTED_VS_FILTERED_MD = REPORT_DIR / "selected_vs_filtered_forward_return.md"
SELECTED_VS_FILTERED_CSV = REPORT_DIR / "selected_vs_filtered_forward_return.csv"
RULES_MD = REPORT_DIR / "missed_opportunity_observation_rules.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    context = common.load_context()
    signal = load_signal()
    summary = load_json(SHADOW_SUMMARY_JSON)
    market_regime = str(summary.get("market_regime") or "unknown")

    current_candidates = identify_candidates(signal, market_regime, context)
    tracking = update_tracking(current_candidates, context)
    by_reason = aggregate_by_reason(tracking)
    risk_on = analyze_risk_on_empty_days(tracking, signal, summary)
    selected_vs_filtered = compare_selected_vs_filtered(signal, tracking, context, market_regime)
    report_summary = build_summary(tracking, by_reason, risk_on)

    current_candidates.to_csv(REPORT_CSV, index=False)
    tracking.to_csv(TRACKING_CSV, index=False)
    by_reason.to_csv(BY_REASON_CSV, index=False)
    risk_on.to_csv(RISK_ON_CSV, index=False)
    selected_vs_filtered.to_csv(SELECTED_VS_FILTERED_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    REPORT_MD.write_text(render_tracker_report(current_candidates, tracking, report_summary), encoding="utf-8")
    BY_REASON_MD.write_text(render_by_reason_report(by_reason), encoding="utf-8")
    RISK_ON_MD.write_text(render_risk_on_report(risk_on), encoding="utf-8")
    SELECTED_VS_FILTERED_MD.write_text(render_selected_vs_filtered_report(selected_vs_filtered), encoding="utf-8")
    RULES_MD.write_text(render_observation_rules(), encoding="utf-8")

    print(f"missed opportunity candidates: {len(current_candidates)}")
    print(f"tracking rows: {len(tracking)}")
    print(f"written: {REPORT_MD}")
    print(f"written: {TRACKING_CSV}")
    print(f"written: {BY_REASON_MD}")
    print(f"written: {RISK_ON_MD}")
    print(f"written: {SELECTED_VS_FILTERED_MD}")


def load_signal() -> pd.DataFrame:
    if not SIGNAL_CSV.exists():
        return pd.DataFrame(columns=signal_columns())
    df = pd.read_csv(SIGNAL_CSV, dtype={"symbol": str}).fillna("")
    for col in signal_columns():
        if col not in df.columns:
            df[col] = ""
    df["symbol"] = df["symbol"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(df["symbol"].astype(str)).str.zfill(6)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    for col in ["alpha_score", "persistence_score", "breakout_score", "trend_score", "final_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["selected", "trend_confirmed", "breakout_confirmed", "ranking_persistence_confirmed"]:
        df[col] = df[col].map(to_bool)
    return df


def signal_columns() -> list[str]:
    return [
        "date",
        "model_name",
        "symbol",
        "name",
        "rank",
        "alpha_score",
        "persistence_score",
        "breakout_score",
        "trend_score",
        "final_score",
        "selected",
        "filter_reasons",
        "etf_type",
        "group",
        "data_health_status",
        "trend_confirmed",
        "breakout_confirmed",
        "ranking_persistence_confirmed",
    ]


def identify_candidates(signal: pd.DataFrame, market_regime: str, context: dict) -> pd.DataFrame:
    if signal.empty:
        return pd.DataFrame(columns=tracking_columns())
    df = signal.copy()
    df["model_name"] = df["model_name"].replace("", MODEL_NAME)
    df["market_regime"] = market_regime
    df["filter_reasons"] = df.apply(enrich_filter_reasons, axis=1)
    top10_cutoff = df["final_score"].nlargest(min(10, len(df))).min() if "final_score" in df else math.nan
    is_high_score = (df["rank"] <= 10) | (df["final_score"] >= top10_cutoff)
    candidates = df[(df["selected"] == False) & is_high_score & (df["filter_reasons"].astype(str).str.strip() != "")].copy()  # noqa: E712
    created_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for _, row in candidates.iterrows():
        symbol = str(row["symbol"]).zfill(6)
        signal_date = str(row["date"])
        close = close_on_date(symbol, signal_date, context)
        primary = primary_filter_reason(str(row.get("filter_reasons", "")))
        rows.append(
            {
                "date": signal_date,
                "model_name": str(row.get("model_name") or MODEL_NAME),
                "market_regime": market_regime,
                "symbol": symbol,
                "name": row.get("name", ""),
                "rank": nullable_int(row.get("rank")),
                "alpha_score": nullable_float(row.get("alpha_score")),
                "persistence_score": nullable_float(row.get("persistence_score")),
                "breakout_score": nullable_float(row.get("breakout_score")),
                "trend_score": nullable_float(row.get("trend_score")),
                "final_score": nullable_float(row.get("final_score")),
                "selected": False,
                "filter_reasons": row.get("filter_reasons", ""),
                "primary_filter_reason": primary,
                "etf_type": row.get("etf_type", ""),
                "group": row.get("group", ""),
                "high_beta_flag": is_high_beta(row),
                "data_health_status": row.get("data_health_status", "normal"),
                "trend_confirmed": bool(row.get("trend_confirmed", False)),
                "breakout_confirmed": bool(row.get("breakout_confirmed", False)),
                "ranking_persistence_confirmed": bool(row.get("ranking_persistence_confirmed", False)),
                "close_on_signal_date": close,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
    out = pd.DataFrame(rows)
    return fill_forward_return_columns(out, context)


def enrich_filter_reasons(row: pd.Series) -> str:
    reasons = split_reasons(row.get("filter_reasons", ""))
    if not to_bool(row.get("trend_confirmed")) and "trend_not_confirmed" not in reasons:
        reasons.append("trend_not_confirmed")
    if not to_bool(row.get("breakout_confirmed")) and "breakout_not_confirmed" not in reasons:
        reasons.append("breakout_not_confirmed")
    if not to_bool(row.get("ranking_persistence_confirmed")) and "ranking_persistence_not_confirmed" not in reasons:
        reasons.append("ranking_persistence_not_confirmed")
    health = str(row.get("data_health_status", "normal"))
    if health and health != "normal":
        reasons.append("data_health_filtered")
    return "; ".join(dict.fromkeys(reasons))


def split_reasons(value: object) -> list[str]:
    text = str(value or "").replace(",", ";")
    return [part.strip() for part in text.split(";") if part.strip()]


def primary_filter_reason(value: str) -> str:
    reasons = split_reasons(value)
    priority = [
        "data_health_filtered",
        "liquidity_below_30m",
        "liquidity_filtered",
        "trend_not_confirmed",
        "breakout_not_confirmed",
        "ranking_persistence_not_confirmed",
        "high_beta_filtered",
        "group_concentration_filtered",
        "min_trade_value_filtered",
    ]
    for item in priority:
        if item in reasons:
            return "liquidity_filtered" if item == "liquidity_below_30m" else item
    return reasons[0] if reasons else "other_filter_reason"


def update_tracking(current: pd.DataFrame, context: dict) -> pd.DataFrame:
    frames = []
    if TRACKING_CSV.exists():
        frames.append(pd.read_csv(TRACKING_CSV, dtype={"symbol": str}))
    if current is not None and not current.empty:
        frames.append(current)
    if not frames:
        return pd.DataFrame(columns=tracking_columns())
    df = pd.concat(frames, ignore_index=True)
    for col in tracking_columns():
        if col not in df.columns:
            df[col] = ""
    df["symbol"] = df["symbol"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(df["symbol"].astype(str)).str.zfill(6)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date", "symbol"]).drop_duplicates(["date", "model_name", "symbol"], keep="last")
    df = fill_forward_return_columns(df, context)
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    df["updated_at"] = now
    df["missed_opportunity_flag"] = df.apply(is_missed_opportunity, axis=1)
    df["filter_effective_flag"] = df.apply(is_filter_effective, axis=1)
    return df[tracking_columns()].sort_values(["date", "rank", "symbol"]).reset_index(drop=True)


def fill_forward_return_columns(df: pd.DataFrame, context: dict) -> pd.DataFrame:
    if df.empty:
        for col in tracking_columns():
            if col not in df.columns:
                df[col] = ""
        return df
    out = df.copy()
    for window in [1, 3, 5, 10, 20]:
        out[f"forward_return_{window}d"] = out.apply(lambda r: forward_return(str(r["symbol"]), str(r["date"]), window, context), axis=1)
        out[f"benchmark_510300_return_{window}d"] = out.apply(lambda r: forward_return("510300", str(r["date"]), window, context), axis=1)
    out["excess_return_vs_510300_5d"] = numeric(out["forward_return_5d"]) - numeric(out["benchmark_510300_return_5d"])
    out["excess_return_vs_510300_10d"] = numeric(out["forward_return_10d"]) - numeric(out["benchmark_510300_return_10d"])
    out["excess_return_vs_510300_20d"] = numeric(out["forward_return_20d"]) - numeric(out["benchmark_510300_return_20d"])
    return out


def aggregate_by_reason(tracking: pd.DataFrame) -> pd.DataFrame:
    if tracking.empty:
        return pd.DataFrame(columns=by_reason_columns())
    rows = []
    for reason, sub in tracking.groupby("primary_filter_reason", dropna=False):
        f10 = numeric(sub["forward_return_10d"])
        e10 = numeric(sub["excess_return_vs_510300_10d"])
        missed = sub["missed_opportunity_flag"].map(to_bool)
        effective = sub["filter_effective_flag"].map(to_bool)
        rows.append(
            {
                "primary_filter_reason": reason or "other_filter_reason",
                "candidate_count": int(len(sub)),
                "forward_5d_mean": mean_or_blank(sub["forward_return_5d"]),
                "forward_10d_mean": mean_or_blank(f10),
                "forward_20d_mean": mean_or_blank(sub["forward_return_20d"]),
                "excess_10d_mean": mean_or_blank(e10),
                "missed_opportunity_count": int(missed.sum()),
                "missed_opportunity_rate": round(float(missed.mean()), 6) if len(sub) else 0.0,
                "filter_effective_count": int(effective.sum()),
                "filter_effective_rate": round(float(effective.mean()), 6) if len(sub) else 0.0,
                "comment": filter_reason_comment(reason, f10, e10),
            }
        )
    return pd.DataFrame(rows, columns=by_reason_columns()).sort_values(["candidate_count", "primary_filter_reason"], ascending=[False, True])


def by_reason_columns() -> list[str]:
    return [
        "primary_filter_reason",
        "candidate_count",
        "forward_5d_mean",
        "forward_10d_mean",
        "forward_20d_mean",
        "excess_10d_mean",
        "missed_opportunity_count",
        "missed_opportunity_rate",
        "filter_effective_count",
        "filter_effective_rate",
        "comment",
    ]


def analyze_risk_on_empty_days(tracking: pd.DataFrame, signal: pd.DataFrame, summary: dict) -> pd.DataFrame:
    if signal.empty:
        return pd.DataFrame(columns=risk_on_columns())
    market_regime = str(summary.get("market_regime") or "unknown")
    selected_count = int(summary.get("selected_count", int(signal["selected"].map(to_bool).sum()) if "selected" in signal else 0) or 0)
    date = str(signal["date"].iloc[0])
    if not (market_regime == "risk_on" and selected_count == 0):
        return pd.DataFrame(columns=risk_on_columns())
    sub = tracking[(tracking["date"].astype(str) == date) & (tracking["market_regime"].astype(str) == "risk_on")]
    reasons = ", ".join(sub["primary_filter_reason"].value_counts().head(3).index.astype(str).tolist()) if not sub.empty else ""
    missed_rate = float(sub["missed_opportunity_flag"].map(to_bool).mean()) if not sub.empty else 0.0
    conclusion = "pending_forward_returns"
    if numeric(sub["forward_return_10d"]).notna().any():
        excess10 = numeric(sub["excess_return_vs_510300_10d"]).mean()
        conclusion = "possible_over_conservative" if excess10 > 0 else "filter_defense_currently_effective"
    return pd.DataFrame(
        [
            {
                "date": date,
                "market_regime": market_regime,
                "top10_candidate_count": int(len(sub)),
                "selected_count": selected_count,
                "top_filter_reasons": reasons,
                "avg_forward_return_5d": mean_or_blank(sub["forward_return_5d"]) if not sub.empty else "",
                "avg_forward_return_10d": mean_or_blank(sub["forward_return_10d"]) if not sub.empty else "",
                "avg_excess_return_10d": mean_or_blank(sub["excess_return_vs_510300_10d"]) if not sub.empty else "",
                "missed_opportunity_rate": round(missed_rate, 6),
                "conclusion": conclusion,
            }
        ],
        columns=risk_on_columns(),
    )


def risk_on_columns() -> list[str]:
    return [
        "date",
        "market_regime",
        "top10_candidate_count",
        "selected_count",
        "top_filter_reasons",
        "avg_forward_return_5d",
        "avg_forward_return_10d",
        "avg_excess_return_10d",
        "missed_opportunity_rate",
        "conclusion",
    ]


def compare_selected_vs_filtered(signal: pd.DataFrame, tracking: pd.DataFrame, context: dict, market_regime: str) -> pd.DataFrame:
    rows = []
    date = str(signal["date"].iloc[0]) if not signal.empty else ""
    selected = signal[signal["selected"].map(to_bool)].copy() if not signal.empty else pd.DataFrame()
    filtered = tracking[tracking["date"].astype(str) == date].copy() if not tracking.empty and date else pd.DataFrame()
    for label, symbols in [
        ("selected_candidates", selected["symbol"].astype(str).tolist() if not selected.empty else []),
        ("filtered_candidates", filtered["symbol"].astype(str).tolist() if not filtered.empty else []),
        ("510300_benchmark", ["510300"]),
    ]:
        rows.append(
            {
                "date": date,
                "market_regime": market_regime,
                "bucket": label,
                "symbol_count": len(symbols),
                "symbols": " ".join(symbols),
                "forward_return_1d_mean": mean_forward_for_symbols(symbols, date, 1, context),
                "forward_return_3d_mean": mean_forward_for_symbols(symbols, date, 3, context),
                "forward_return_5d_mean": mean_forward_for_symbols(symbols, date, 5, context),
                "forward_return_10d_mean": mean_forward_for_symbols(symbols, date, 10, context),
                "forward_return_20d_mean": mean_forward_for_symbols(symbols, date, 20, context),
                "conclusion": "pending" if date and math.isnan(mean_forward_for_symbols(symbols, date, 10, context, nan=True)) else "available",
            }
        )
    return pd.DataFrame(rows)


def build_summary(tracking: pd.DataFrame, by_reason: pd.DataFrame, risk_on: pd.DataFrame) -> dict:
    missed = tracking["missed_opportunity_flag"].map(to_bool) if not tracking.empty else pd.Series(dtype=bool)
    effective = tracking["filter_effective_flag"].map(to_bool) if not tracking.empty else pd.Series(dtype=bool)
    top_reason = ""
    if not by_reason.empty:
        candidates = by_reason.sort_values(["missed_opportunity_count", "candidate_count"], ascending=[False, False])
        top_reason = str(candidates.iloc[0]["primary_filter_reason"])
    pending = int(numeric(tracking["forward_return_10d"]).isna().sum()) if not tracking.empty else 0
    return {
        "status": "active",
        "research_only": True,
        "execution_enabled": False,
        "model_name": MODEL_NAME,
        "tracking_days": int(tracking["date"].nunique()) if not tracking.empty else 0,
        "candidate_count": int(len(tracking)),
        "missed_opportunity_count": int(missed.sum()) if len(missed) else 0,
        "missed_opportunity_rate": round(float(missed.mean()), 6) if len(missed) else 0.0,
        "filter_effective_rate": round(float(effective.mean()), 6) if len(effective) else 0.0,
        "risk_on_empty_signal_count": int(len(risk_on)),
        "top_missed_filter_reason": top_reason,
        "forward_return_10d_pending_count": pending,
        "ready_to_relax_filters": False,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "summary": "Missed opportunity tracking is active, but results are labels only and do not change persistence_breakout_v2 rules.",
        "tracker_report_href": "../reports/missed_opportunity_tracker.md",
        "by_reason_report_href": "../reports/missed_opportunity_by_filter_reason.md",
        "risk_on_report_href": "../reports/risk_on_empty_signal_analysis.md",
        "selected_vs_filtered_href": "../reports/selected_vs_filtered_forward_return.md",
        "observation_rules_href": "../reports/missed_opportunity_observation_rules.md",
    }


def is_missed_opportunity(row: pd.Series) -> bool:
    f10 = nullable_float(row.get("forward_return_10d"))
    e10 = nullable_float(row.get("excess_return_vs_510300_10d"))
    return bool(pd.notna(f10) and pd.notna(e10) and f10 > 0 and e10 > 0)


def is_filter_effective(row: pd.Series) -> bool:
    f10 = nullable_float(row.get("forward_return_10d"))
    e10 = nullable_float(row.get("excess_return_vs_510300_10d"))
    return bool(pd.notna(f10) and pd.notna(e10) and (f10 <= 0 or e10 <= 0))


def tracking_columns() -> list[str]:
    return [
        "date",
        "model_name",
        "market_regime",
        "symbol",
        "name",
        "rank",
        "alpha_score",
        "persistence_score",
        "breakout_score",
        "trend_score",
        "final_score",
        "selected",
        "filter_reasons",
        "primary_filter_reason",
        "etf_type",
        "group",
        "high_beta_flag",
        "data_health_status",
        "trend_confirmed",
        "breakout_confirmed",
        "ranking_persistence_confirmed",
        "close_on_signal_date",
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
        "excess_return_vs_510300_5d",
        "excess_return_vs_510300_10d",
        "excess_return_vs_510300_20d",
        "missed_opportunity_flag",
        "filter_effective_flag",
        "created_at",
        "updated_at",
    ]


def close_on_date(symbol: str, date: str, context: dict) -> float | str:
    df = context["price_data"].get(symbol)
    if df is None or df.empty:
        return ""
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    rows = frame[frame["date"] == pd.Timestamp(date)]
    if rows.empty:
        return ""
    return round(float(rows.iloc[0]["close"]), 6)


def forward_return(symbol: str, date: str, window: int, context: dict) -> float:
    df = context["price_data"].get(symbol)
    if df is None or df.empty:
        return math.nan
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    matches = frame.index[frame["date"] == pd.Timestamp(date)]
    if len(matches) == 0:
        return math.nan
    idx = int(matches[0])
    target_idx = idx + window
    if target_idx >= len(frame):
        return math.nan
    start = float(frame.loc[idx, "close"])
    end = float(frame.loc[target_idx, "close"])
    if start <= 0:
        return math.nan
    return round(end / start - 1, 6)


def mean_forward_for_symbols(symbols: list[str], date: str, window: int, context: dict, nan: bool = False) -> float:
    if not symbols or not date:
        return math.nan if nan else ""
    values = [forward_return(symbol, date, window, context) for symbol in symbols]
    clean = [value for value in values if pd.notna(value)]
    if not clean:
        return math.nan if nan else ""
    return round(float(pd.Series(clean).mean()), 6)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def mean_or_blank(values: pd.Series) -> float | str:
    nums = pd.to_numeric(values, errors="coerce").dropna()
    return round(float(nums.mean()), 6) if not nums.empty else ""


def nullable_float(value: object) -> float:
    try:
        num = float(value)
    except Exception:
        return math.nan
    return num if pd.notna(num) else math.nan


def nullable_int(value: object) -> int | str:
    try:
        if pd.isna(value):
            return ""
        return int(float(value))
    except Exception:
        return ""


def to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "是"}


def is_high_beta(row: pd.Series) -> bool:
    etf_type = str(row.get("etf_type", ""))
    group = str(row.get("group", ""))
    return etf_type in {"theme", "high_beta"} or "科技" in group or "新能源" in group


def filter_reason_comment(reason: str, f10: pd.Series, e10: pd.Series) -> str:
    if f10.dropna().empty or e10.dropna().empty:
        return "pending; forward return not mature enough"
    if float(e10.mean()) > 0:
        return "possible over-filtering; keep observing before changing rules"
    return "filter currently looks defensive/effective, sample still limited"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def render_tracker_report(current: pd.DataFrame, tracking: pd.DataFrame, summary: dict) -> str:
    return "\n".join(
        [
            "# Missed Opportunity Tracker",
            "",
            "本报告只做事后 diagnostics / tracking，不修改 persistence_breakout_v2 规则，不接执行层，不写模拟盘交易文件。",
            "",
            "## 字段映射",
            "- alpha_score/final_score: 来自 persistence_breakout_shadow_signal.csv。",
            "- selected: false 且 rank<=10 或 final_score 位于当日前 10，并且 filter_reasons 非空，进入 missed opportunity candidate。",
            "- breakout_not_confirmed / ranking_persistence_not_confirmed: 若源文件未写入 filter_reasons，则从对应 boolean 字段派生。",
            "- forward_return_*: 仅作为事后 label，不作为当日特征。",
            "",
            "## 摘要",
            f"- status: {summary.get('status')}",
            f"- candidate_count: {summary.get('candidate_count')}",
            f"- tracking_days: {summary.get('tracking_days')}",
            f"- missed_opportunity_count: {summary.get('missed_opportunity_count')}",
            f"- missed_opportunity_rate: {summary.get('missed_opportunity_rate')}",
            f"- filter_effective_rate: {summary.get('filter_effective_rate')}",
            f"- forward_return_10d_pending_count: {summary.get('forward_return_10d_pending_count')}",
            "- ready_to_relax_filters: false",
            "- ready_for_execution: false",
            "",
            "## Current Candidates",
            markdown_table(current),
            "",
            "## Tracking Tail",
            markdown_table(tracking.tail(30)),
        ]
    ) + "\n"


def render_by_reason_report(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Missed Opportunity By Filter Reason",
            "",
            "按 primary_filter_reason 归因。样本未到期时结论为 pending，不得据此调整规则。",
            "",
            markdown_table(df),
        ]
    ) + "\n"


def render_risk_on_report(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Risk-on Empty Signal Analysis",
            "",
            "专门观察 risk_on 但 selected_count=0 的日期，判断严格过滤是防守还是过度保守。",
            "",
            markdown_table(df),
        ]
    ) + "\n"


def render_selected_vs_filtered_report(df: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Selected vs Filtered Forward Return",
            "",
            "若未来 persistence_breakout_v2 出现 selected ETF，本表比较 selected / filtered / 510300 的后续表现。",
            "",
            markdown_table(df),
        ]
    ) + "\n"


def render_observation_rules() -> str:
    return """# Missed Opportunity Observation Rules

当前阶段不允许马上放宽过滤规则。

只有满足以下条件，未来才可以进入“规则放宽研究”：

1. 至少积累 20 个交易日。
2. risk_on 空仓样本足够多。
3. 被 trend_not_confirmed 过滤的候选，forward 10d 明显跑赢 510300。
4. 被 breakout_not_confirmed 过滤的候选，forward 10d 明显跑赢 510300。
5. missed_opportunity_rate 持续偏高。
6. 放宽过滤的模拟回测不显著增加回撤。
7. 仍保持 ready_for_execution = false。

当前结论：

- ready_to_relax_filters = false
- ready_for_preview = false
- ready_for_execution = false
- execution_enabled = false
- paper_trade_engine_enabled = false
- real_trade_enabled = false
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
