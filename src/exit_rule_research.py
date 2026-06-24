"""Offline exit-rule research.

This is a research layer only. It does not change sell_signal_review,
paper_positions, paper_trades, or formal strategy rules.
"""

from __future__ import annotations

import pandas as pd

from config import ETF_DAILY_DIR, REPORT_DIR
from data_loader import load_price_data
from etf_classifier import CLASSIFICATION_FILE, EXCLUDED_STATUS, main as build_classification


CSV_FILE = REPORT_DIR / "exit_rule_research.csv"
LEGACY_RESULT_FILE = REPORT_DIR / "exit_rule_research_results.csv"
REPORT_FILE = REPORT_DIR / "exit_rule_research_report.md"

STOP_LOSS = {
    "broad_index": -0.08,
    "sector": -0.06,
    "theme": -0.05,
    "high_beta": -0.05,
    "commodity_resource": -0.06,
    "bond_cash": -0.02,
    "qdii": -0.07,
    "unknown": -0.06,
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    classification = pd.read_csv(CLASSIFICATION_FILE, dtype=str, keep_default_na=False).fillna("")
    rows = build_results(classification)
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)
    df.to_csv(LEGACY_RESULT_FILE, index=False)
    REPORT_FILE.write_text(render_report(df), encoding="utf-8")
    print(f"exit_rule rows: {len(df)}")
    print(f"written: {CSV_FILE}")
    print(f"written: {REPORT_FILE}")


def build_results(classification: pd.DataFrame) -> list[dict]:
    rows = []
    for _, meta in classification.iterrows():
        if meta.get("status") in EXCLUDED_STATUS:
            continue
        symbol = str(meta.get("symbol") or meta.get("code") or "").strip()
        if not symbol:
            continue
        prices, error = load_price_data(ETF_DAILY_DIR, symbol)
        if error or prices is None or len(prices) < 90:
            rows.append(_insufficient_row(meta, "all_rules", f"price_sample_insufficient: {error or len(prices) if prices is not None else 'missing'}"))
            continue
        feat = _features(prices)
        etf_type = str(meta.get("etf_type") or "unknown")
        masks = {
            "rank_score_decline_2d_proxy": feat["proxy_score_decline_2d"],
            "rank_score_decline_3d_proxy": feat["proxy_score_decline_3d"],
            "rank_score_below_70_proxy": feat["proxy_score_pct"] < 0.70,
            "top_decile_drop_proxy": feat["proxy_top_decile"].shift(1).fillna(False) & (~feat["proxy_top_decile"]),
            "short_swing_buy_to_watch_proxy": feat["short_buy_to_watch"],
            "short_swing_buy_to_sell_proxy": feat["short_buy_to_sell"],
            "volume_heat_decay_proxy": feat["volume_decay"] & feat["proxy_score_decline_2d"],
            "type_stop_loss_proxy": feat["drawdown20"] <= STOP_LOSS.get(etf_type, -0.06),
        }
        for rule_name, mask in masks.items():
            rows.append(_rule_stats(meta, feat, rule_name, mask))
    return rows


def render_report(results: pd.DataFrame) -> str:
    lines = [
        "# 退出规则离线研究报告",
        "",
        "本报告只研究候选退出规则，不上线、不自动卖出、不修改仓位。",
        "",
        "## 候选规则",
        "| rule | 说明 | 建议定位 |",
        "| --- | --- | --- |",
        "| rank_score_decline_2d_proxy | 代理评分连续 2 天下滑 | REVIEW 研究候选 |",
        "| rank_score_decline_3d_proxy | 代理评分连续 3 天下滑 | REDUCE 研究候选 |",
        "| rank_score_below_70_proxy | 评分分位跌破 70% | 禁止加仓/复核 |",
        "| top_decile_drop_proxy | 从强势分位掉出 | 热点退潮观察 |",
        "| short_swing_buy_to_watch_proxy | 短周期由强转弱 | REVIEW |",
        "| short_swing_buy_to_sell_proxy | 短周期转弱且跌破均线 | SELL 候选研究 |",
        "| volume_heat_decay_proxy | 成交热度和动量同步衰减 | 主题热度衰减代理 |",
        "| type_stop_loss_proxy | 按 ETF 类型默认止损阈值 | 硬风控研究候选 |",
        "",
        "## 汇总统计",
        "| etf_type | rule | event_count | win_rate_after_exit | avg_forward_return_10d | avg_forward_return_20d | max_drawdown_after_exit | profit_loss_ratio | false_exit_count | late_exit_count | evidence | suggestion |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if results.empty:
        lines.append("|  | 无可用样本 | 0 |  |  |  |  |  |  |  | hypothesis_only |  |")
    else:
        usable = results[pd.to_numeric(results["event_count"], errors="coerce").fillna(0) > 0].copy()
        if usable.empty:
            lines.append("|  | 无触发样本 | 0 |  |  |  |  |  |  |  | hypothesis_only |  |")
        else:
            numeric_cols = ["event_count", "win_rate_after_exit", "avg_forward_return_10d", "avg_forward_return_20d", "max_drawdown_after_exit", "profit_loss_ratio", "false_exit_count", "late_exit_count"]
            for col in numeric_cols:
                usable[col] = pd.to_numeric(usable[col], errors="coerce")
            grouped = (
                usable.groupby(["etf_type", "rule"], dropna=False)
                .agg(
                    event_count=("event_count", "sum"),
                    win_rate_after_exit=("win_rate_after_exit", "mean"),
                    avg_forward_return_10d=("avg_forward_return_10d", "mean"),
                    avg_forward_return_20d=("avg_forward_return_20d", "mean"),
                    max_drawdown_after_exit=("max_drawdown_after_exit", "min"),
                    profit_loss_ratio=("profit_loss_ratio", "mean"),
                    false_exit_count=("false_exit_count", "sum"),
                    late_exit_count=("late_exit_count", "sum"),
                )
                .reset_index()
            )
            grouped["evidence_level"] = grouped["event_count"].apply(_evidence_level)
            for _, row in grouped.iterrows():
                lines.append(
                    f"| {row['etf_type']} | {row['rule']} | {int(row['event_count'])} | {_pct(row['win_rate_after_exit'])} | "
                    f"{_pct(row['avg_forward_return_10d'])} | {_pct(row['avg_forward_return_20d'])} | {_pct(row['max_drawdown_after_exit'])} | "
                    f"{_num(row['profit_loss_ratio'])} | {int(row['false_exit_count'])} | {int(row['late_exit_count'])} | "
                    f"{row['evidence_level']} | {_suggestion(row['rule'], int(row['event_count']), row['avg_forward_return_10d'])} |"
                )
    lines += [
        "",
        "## 研究结论边界",
        "- 单日评分下降不能直接卖出，容易被震荡噪声误伤。",
        "- short_swing 转弱更适合作为 REVIEW/禁止加仓，而不是立即 SELL。",
        "- 类型化止损、连续下降和热度衰减需要后续回测验证后才能进入执行层。",
        "- 本报告不修改 sell_signal_review.py 的当前复核逻辑，也不写交易流水。",
    ]
    return "\n".join(lines)


def _features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values("date").reset_index(drop=True).copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["ma10"] = df["close"].rolling(10).mean()
    df["ret5"] = df["close"] / df["close"].shift(5) - 1
    df["ret20"] = df["close"] / df["close"].shift(20) - 1
    df["vol20"] = df["close"].pct_change().rolling(20).std()
    df["drawdown20"] = df["close"] / df["close"].rolling(20).max() - 1
    df["proxy_score"] = df["ret20"].fillna(0) + 0.5 * df["ret5"].fillna(0) - df["vol20"].fillna(0)
    df["proxy_score_pct"] = df["proxy_score"].rolling(120, min_periods=30).rank(pct=True)
    df["proxy_top_decile"] = df["proxy_score_pct"] >= 0.90
    df["proxy_score_decline_2d"] = (df["proxy_score"] < df["proxy_score"].shift(1)) & (df["proxy_score"].shift(1) < df["proxy_score"].shift(2))
    df["proxy_score_decline_3d"] = df["proxy_score_decline_2d"] & (df["proxy_score"].shift(2) < df["proxy_score"].shift(3))
    df["short_buy"] = (df["ret5"] > 0.03) & (df["close"] > df["ma10"])
    df["short_watch"] = (df["ret5"] > 0) & (df["ret5"] <= 0.03)
    df["short_sell"] = (df["ret5"] <= 0) & (df["close"] < df["ma10"])
    df["short_buy_to_watch"] = df["short_buy"].shift(1).fillna(False) & df["short_watch"]
    df["short_buy_to_sell"] = df["short_buy"].shift(1).fillna(False) & df["short_sell"]
    if "volume" in df.columns:
        volume = pd.to_numeric(df["volume"], errors="coerce")
        df["volume_decay"] = (volume.rolling(5).mean() < volume.rolling(20).mean()) & (volume.rolling(5).mean() < volume.rolling(5).mean().shift(1))
    else:
        df["volume_decay"] = False
    for window in [5, 10, 20]:
        df[f"future_{window}d_return"] = df["close"].shift(-window) / df["close"] - 1
        df[f"forward_{window}d_drawdown"] = _forward_drawdown_series(df["close"], window)
    return df


def _rule_stats(meta: pd.Series, feat: pd.DataFrame, rule: str, mask: pd.Series) -> dict:
    events = feat[mask].copy()
    fwd10 = pd.to_numeric(events.get("future_10d_return", pd.Series(dtype=float)), errors="coerce").dropna()
    fwd20 = pd.to_numeric(events.get("future_20d_return", pd.Series(dtype=float)), errors="coerce").dropna()
    dd20 = pd.to_numeric(events.get("forward_20d_drawdown", pd.Series(dtype=float)), errors="coerce").dropna()
    event_count = int(len(events))
    positive = fwd10[fwd10 > 0]
    negative = fwd10[fwd10 < 0]
    false_exit_count = int((fwd10 > 0.03).sum()) if len(fwd10) else 0
    late_exit_count = int((dd20 < -0.06).sum()) if len(dd20) else 0
    return {
        "symbol": meta.get("symbol", meta.get("code", "")),
        "code": meta.get("code", meta.get("symbol", "")),
        "name": meta.get("name", ""),
        "group": meta.get("group", ""),
        "pool": meta.get("pool", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "risk_profile": meta.get("risk_profile", ""),
        "rule": rule,
        "event_count": event_count,
        "win_rate_after_exit": float((fwd10 > 0).mean()) if len(fwd10) else "",
        "avg_forward_return_10d": _mean(fwd10),
        "avg_forward_return_20d": _mean(fwd20),
        "max_drawdown_after_exit": float(dd20.min()) if len(dd20) else "",
        "avg_holding_days": 10,
        "turnover_proxy": event_count / len(feat) if len(feat) else "",
        "profit_loss_ratio": _profit_loss_ratio(positive, negative),
        "false_exit_count": false_exit_count,
        "late_exit_count": late_exit_count,
        "evidence_level": _evidence_level(event_count),
        "suggestion": _suggestion(rule, event_count, _mean(fwd10)),
        "insufficient_reason": "" if event_count >= 30 else "event_count_below_30",
    }


def _insufficient_row(meta: pd.Series, rule: str, reason: str) -> dict:
    return {
        "symbol": meta.get("symbol", meta.get("code", "")),
        "code": meta.get("code", meta.get("symbol", "")),
        "name": meta.get("name", ""),
        "group": meta.get("group", ""),
        "pool": meta.get("pool", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "risk_profile": meta.get("risk_profile", ""),
        "rule": rule,
        "event_count": 0,
        "win_rate_after_exit": "",
        "avg_forward_return_10d": "",
        "avg_forward_return_20d": "",
        "max_drawdown_after_exit": "",
        "avg_holding_days": "",
        "turnover_proxy": "",
        "profit_loss_ratio": "",
        "false_exit_count": "",
        "late_exit_count": "",
        "evidence_level": "hypothesis_only",
        "suggestion": "need_more_data",
        "insufficient_reason": reason,
    }


def _forward_drawdown_series(close: pd.Series, window: int) -> pd.Series:
    close = pd.to_numeric(close, errors="coerce").reset_index(drop=True)
    values = []
    for idx in range(len(close)):
        if idx + window >= len(close) or close.iloc[idx] <= 0:
            values.append(float("nan"))
            continue
        segment = close.iloc[idx : idx + window + 1]
        values.append(float((segment / segment.iloc[0] - 1).min()))
    return pd.Series(values, dtype=float)


def _profit_loss_ratio(positive: pd.Series, negative: pd.Series) -> float | str:
    if positive.empty or negative.empty:
        return ""
    loss = abs(float(negative.mean()))
    return float(positive.mean()) / loss if loss else ""


def _mean(series: pd.Series) -> float | str:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if len(values) else ""


def _evidence_level(count: object) -> str:
    numeric = int(float(count)) if str(count) not in {"", "nan"} else 0
    if numeric >= 200:
        return "evidence_supported"
    if numeric >= 40:
        return "sample_limited"
    return "hypothesis_only"


def _suggestion(rule: str, event_count: int, avg_forward_10d: object) -> str:
    if event_count < 30:
        return "need_more_data"
    value = float(avg_forward_10d) if avg_forward_10d not in ("", None) else 0.0
    if value < 0:
        return "candidate_for_simulation_review"
    if "stop_loss" in rule:
        return "risk_control_candidate_requires_backtest"
    return "research_only_not_online"


def _pct(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2%}"


def _num(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2f}"


if __name__ == "__main__":
    main()
