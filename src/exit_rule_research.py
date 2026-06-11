"""Offline exit-rule research.

Candidate rules are evaluated as research proxies only. No trading rules,
paper positions, or paper trades are changed.
"""

from __future__ import annotations

import argparse

import pandas as pd

from config import ETF_DAILY_DIR, REPORT_DIR
from etf_classification import CLASSIFICATION_FILE, main as build_classification


REPORT_FILE = REPORT_DIR / "exit_rule_research_report.md"
RESULT_FILE = REPORT_DIR / "exit_rule_research_results.csv"

STOP_LOSS_RULES = {
    "broad_index": "7%-10%",
    "sector": "5%-8%",
    "theme": "4%-6%",
    "hot_theme": "3%-5%",
    "bond_cash": "low_vol_or_none",
    "qdii": "price+premium+fx",
    "commodity_resource": "5%-8%",
    "unknown": "manual_review",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="退出规则离线研究")
    return parser.parse_args()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    classification = pd.read_csv(CLASSIFICATION_FILE, dtype={"code": str}).fillna("")
    rows = build_results(classification)
    results = pd.DataFrame(rows)
    results.to_csv(RESULT_FILE, index=False)
    write_report(results, classification)
    print(f"已生成退出规则研究结果：{RESULT_FILE}")
    print(f"已生成退出规则研究报告：{REPORT_FILE}")


def build_results(classification: pd.DataFrame) -> list[dict]:
    rows = []
    for _, meta in classification.iterrows():
        code = str(meta["code"])
        if meta.get("status") in {"failed_validation", "failed_dry_run", "unresolved", "excluded"}:
            continue
        prices = _load_prices(code)
        if prices.empty or len(prices) < 80:
            continue
        feat = _features(prices)
        rule_masks = {
            "rank_score_decline_2d": feat["proxy_score_decline_2d"],
            "rank_score_decline_3d": feat["proxy_score_decline_3d"],
            "rank_score_below_70_proxy": feat["proxy_score_pct"] < 0.70,
            "rank_drop_top3_to_out_top10_proxy": feat["proxy_top3"].shift(1).fillna(False) & (~feat["proxy_top10"]),
            "short_swing_buy_to_watch_proxy": feat["short_buy_to_watch"],
            "short_swing_buy_to_sell_proxy": feat["short_buy_to_sell"],
            "volume_and_rank_decay_proxy": feat["volume_decay"] & feat["proxy_score_decline_3d"],
        }
        for rule, mask in rule_masks.items():
            rows.append(_rule_stats(meta, feat, rule, mask))
        rows.append(_stop_loss_row(meta, feat))
    return rows


def _rule_stats(meta: pd.Series, feat: pd.DataFrame, rule: str, mask: pd.Series) -> dict:
    events = feat[mask].copy()
    fwd5 = pd.to_numeric(events.get("future_5d_return", pd.Series(dtype=float)), errors="coerce").dropna()
    fwd10 = pd.to_numeric(events.get("future_10d_return", pd.Series(dtype=float)), errors="coerce").dropna()
    fwd20 = pd.to_numeric(events.get("future_20d_return", pd.Series(dtype=float)), errors="coerce").dropna()
    return {
        "code": meta["code"],
        "name": meta["name"],
        "group": meta.get("group", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "rule": rule,
        "event_count": int(len(events)),
        "avg_next_5d_return": _mean(fwd5),
        "avg_next_10d_return": _mean(fwd10),
        "avg_next_20d_return": _mean(fwd20),
        "negative_next_10d_rate": _negative_rate(fwd10),
        "evidence_level": _evidence_label(len(events)),
        "suggestion": _rule_suggestion(rule, meta.get("etf_type", "unknown"), len(events), _mean(fwd10)),
    }


def _stop_loss_row(meta: pd.Series, feat: pd.DataFrame) -> dict:
    etf_type = meta.get("etf_type", "unknown")
    dd20 = feat["close"] / feat["close"].rolling(20).max() - 1
    threshold = {
        "broad_index": -0.07,
        "sector": -0.05,
        "theme": -0.04,
        "hot_theme": -0.03,
        "bond_cash": -0.02,
        "qdii": -0.06,
        "commodity_resource": -0.05,
    }.get(etf_type, -0.06)
    events = dd20 <= threshold
    return {
        "code": meta["code"],
        "name": meta["name"],
        "group": meta.get("group", ""),
        "etf_type": etf_type,
        "rule": f"type_stop_loss_proxy_{STOP_LOSS_RULES.get(etf_type, 'manual')}",
        "event_count": int(events.sum()),
        "avg_next_5d_return": _mean(feat.loc[events, "future_5d_return"]),
        "avg_next_10d_return": _mean(feat.loc[events, "future_10d_return"]),
        "avg_next_20d_return": _mean(feat.loc[events, "future_20d_return"]),
        "negative_next_10d_rate": _negative_rate(feat.loc[events, "future_10d_return"]),
        "evidence_level": _evidence_label(int(events.sum())),
        "suggestion": "research_only_type_stop; do_not_online_without_backtest",
    }


def write_report(results: pd.DataFrame, classification: pd.DataFrame) -> None:
    lines = [
        "# 退出规则离线研究报告",
        "",
        "本报告只研究候选退出规则，不上线、不自动卖出、不修改仓位。",
        "",
        "## 候选规则说明",
        "| 规则 | 逻辑 | 适用 ETF 类型 | 优点 | 风险 |",
        "| --- | --- | --- | --- | --- |",
        "| A1 rank_score 连续 2 天下滑 | proxy_score 连续 2 天下滑 | 行业/主题/宽基 | 更早识别走弱 | 易被震荡噪声误伤 |",
        "| A2 rank_score 连续 3 天下滑 | proxy_score 连续 3 天下滑 | 行业/主题 | 减少短噪声 | 可能退出偏晚 |",
        "| A3 rank_score 跌破 70 | proxy_score 分位跌破 70% | 全部 ETF | 简单清晰 | proxy 与真实 rank_score 不完全一致 |",
        "| A4 Top3 跌出 Top10 | ETF 内 proxy top3 转非 top10 | 强势轮动 | 适合热点退潮 | 需要横截面真实历史排名 |",
        "| B1 short_swing BUY 转 WATCH | 5 日动量从强转弱 | 主题/行业 | 与短周期风险匹配 | 可能错过中期趋势 |",
        "| B2 short_swing BUY 转 SELL | 5 日动量转负且跌破 ma10 | 主题/行业 | 风险更明确 | 触发较晚 |",
        "| C 类型化止损 | 按 ETF 类型设不同止损 | 全部 ETF | 匹配波动差异 | 阈值需回测验证 |",
        "| D 热度衰减代理 | 成交量下降 + proxy_score 下降 | 主题 ETF | 无新闻数据时可代理热度 | 不能替代真实新闻情绪 |",
        "",
        "## 离线统计汇总",
        "| etf_type | rule | event_count | avg_next_10d | negative_next_10d_rate | evidence | suggestion |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    if results.empty:
        lines.append("|  | 无可用样本 | 0 |  |  | hypothesis_only | 需要更多数据 |")
    else:
        grouped = (
            results.groupby(["etf_type", "rule"], dropna=False)
            .agg(
                event_count=("event_count", "sum"),
                avg_next_10d_return=("avg_next_10d_return", "mean"),
                negative_next_10d_rate=("negative_next_10d_rate", "mean"),
            )
            .reset_index()
        )
        grouped["evidence_level"] = grouped["event_count"].apply(_evidence_label)
        for _, row in grouped.iterrows():
            suggestion = _group_suggestion(row["rule"], row["etf_type"], row["event_count"], row["avg_next_10d_return"])
            lines.append(
                f"| {row['etf_type']} | {row['rule']} | {int(row['event_count'])} | {_pct(row['avg_next_10d_return'])} | "
                f"{_pct(row['negative_next_10d_rate'])} | {row['evidence_level']} | {suggestion} |"
            )
    lines += [
        "",
        "## 是否建议进入模拟观察",
        "- rank_score 连续下降：建议进入模拟观察，但必须使用真实历史 rank_score 后再评估。",
        "- short_swing 转弱：建议先用于 REVIEW/禁止加仓，不直接自动卖出。",
        "- 类型化止损：建议进入离线回测，不建议直接上线。",
        "- 热度衰减：在新闻数据未接入前只能作为代理研究，不建议上线。",
        "",
        "## 不建议上线项",
        "- 任何未经过样本验证的主题 ETF 自动减仓规则。",
        "- 新闻/热度直接触发 BUY 或 SELL。",
        "- 对当前模拟持仓自动卖出或自动改仓。",
        "",
        "## 数据限制",
        "- 当前 rank_score 没有完整历史序列，本报告使用 proxy_score 代替。",
        "- short_swing 转弱用 5 日收益和 ma10 的代理定义。",
        "- 热度衰减使用成交量和 proxy_score 代理，不能替代真实新闻情绪。",
        "- 所有结论为 research/simulation 层，不进入 live paper trade execution。",
    ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values("date").reset_index(drop=True).copy()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ret5"] = df["close"] / df["close"].shift(5) - 1
    df["ret20"] = df["close"] / df["close"].shift(20) - 1
    df["vol20"] = df["close"].pct_change().rolling(20).std()
    df["proxy_score"] = df["ret20"].fillna(0) + 0.5 * df["ret5"].fillna(0) - df["vol20"].fillna(0)
    df["proxy_score_pct"] = df["proxy_score"].rolling(120, min_periods=30).rank(pct=True)
    df["proxy_top3"] = df["proxy_score_pct"] >= 0.97
    df["proxy_top10"] = df["proxy_score_pct"] >= 0.90
    df["proxy_score_decline_2d"] = (df["proxy_score"] < df["proxy_score"].shift(1)) & (df["proxy_score"].shift(1) < df["proxy_score"].shift(2))
    df["proxy_score_decline_3d"] = df["proxy_score_decline_2d"] & (df["proxy_score"].shift(2) < df["proxy_score"].shift(3))
    df["short_buy"] = (df["ret5"] > 0.03) & (df["close"] > df["ma10"])
    df["short_watch"] = (df["ret5"] > 0) & (df["ret5"] <= 0.03)
    df["short_sell"] = (df["ret5"] <= 0) & (df["close"] < df["ma10"])
    df["short_buy_to_watch"] = df["short_buy"].shift(1).fillna(False) & df["short_watch"]
    df["short_buy_to_sell"] = df["short_buy"].shift(1).fillna(False) & df["short_sell"]
    if "volume" in df.columns:
        df["volume_ma5"] = df["volume"].rolling(5).mean()
        df["volume_ma20"] = df["volume"].rolling(20).mean()
        df["volume_decay"] = (df["volume_ma5"] < df["volume_ma20"]) & (df["volume_ma5"] < df["volume_ma5"].shift(1))
    else:
        df["volume_decay"] = False
    for window in [5, 10, 20]:
        df[f"future_{window}d_return"] = df["close"].shift(-window) / df["close"] - 1
    return df


def _load_prices(code: str) -> pd.DataFrame:
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{code}.csv"
        if path.exists():
            df = pd.read_csv(path)
            if "date" in df.columns and "close" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                if "volume" in df.columns:
                    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
                return df.dropna(subset=["date", "close"]).sort_values("date")
    return pd.DataFrame()


def _mean(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def _negative_rate(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float((values < 0).mean()) if len(values) else None


def _evidence_label(count: int) -> str:
    if count >= 200:
        return "evidence_supported"
    if count >= 40:
        return "sample_limited"
    return "hypothesis_only"


def _rule_suggestion(rule: str, etf_type: str, count: int, avg_next_10d: float | None) -> str:
    if count < 40:
        return "need_more_data"
    if avg_next_10d is not None and avg_next_10d < 0:
        return "candidate_for_simulation_review"
    return "research_only_not_online"


def _group_suggestion(rule: str, etf_type: str, count: int, avg_next_10d: float | None) -> str:
    if count < 40:
        return "需要更多数据"
    if avg_next_10d is not None and avg_next_10d < 0:
        return "可进入模拟观察"
    return "暂不建议上线"


def _pct(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
