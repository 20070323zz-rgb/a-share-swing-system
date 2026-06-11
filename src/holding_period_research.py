"""Offline holding-period research by ETF type.

This script writes research reports only. It does not change live strategy
rules, paper positions, or paper trades.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import ETF_DAILY_DIR, REPORT_DIR
from etf_classification import CLASSIFICATION_FILE, main as build_classification


WINDOWS = [3, 5, 10, 20, 30, 60]
RESULT_FILE = REPORT_DIR / "holding_period_research_results.csv"
REPORT_FILE = REPORT_DIR / "holding_period_research_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF 类型化持有周期离线研究")
    return parser.parse_args()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    classification = pd.read_csv(CLASSIFICATION_FILE, dtype={"code": str}).fillna("")
    results = build_results(classification)
    pd.DataFrame(results).to_csv(RESULT_FILE, index=False)
    write_report(pd.DataFrame(results), classification)
    print(f"已生成持有周期研究结果：{RESULT_FILE}")
    print(f"已生成持有周期研究报告：{REPORT_FILE}")


def build_results(classification: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for _, meta in classification.iterrows():
        code = str(meta["code"])
        if meta.get("status") in {"failed_validation", "failed_dry_run", "unresolved", "excluded"}:
            continue
        prices = _load_prices(code)
        if prices.empty or len(prices) < 80:
            continue
        feat = _features(prices)
        buy_rows = feat[feat["proxy_buy_signal"]].copy()
        weakening_rows = feat[feat["short_swing_weakening"]].copy()
        rank_decline_rows = feat[feat["proxy_rank_decline_3d"]].copy()
        for window in WINDOWS:
            rows.append(_stats_row(meta, feat, buy_rows, window, "proxy_buy"))
            rows.append(_stats_row(meta, feat, weakening_rows, window, "short_swing_weakening"))
            rows.append(_stats_row(meta, feat, rank_decline_rows, window, "proxy_rank_decline_3d"))
    return rows


def _stats_row(meta: pd.Series, feat: pd.DataFrame, signal_rows: pd.DataFrame, window: int, signal_type: str) -> dict:
    col = f"future_{window}d_return"
    values = pd.to_numeric(signal_rows.get(col, pd.Series(dtype=float)), errors="coerce").dropna()
    max_dd = _window_forward_drawdowns(feat, signal_rows.index, window)
    avg_return = float(values.mean()) if len(values) else None
    win_rate = float((values > 0).mean()) if len(values) else None
    max_drawdown = float(max_dd.min()) if len(max_dd) else None
    return_dd = abs(avg_return / max_drawdown) if avg_return is not None and max_drawdown not in (None, 0) else None
    signal_count = int(len(values))
    evidence = _evidence_label(signal_count)
    return {
        "code": meta["code"],
        "name": meta["name"],
        "group": meta.get("group", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "holding_profile": meta.get("holding_profile", ""),
        "signal_type": signal_type,
        "holding_window_days": window,
        "avg_return": avg_return,
        "win_rate": win_rate,
        "max_forward_drawdown": max_drawdown,
        "return_drawdown_ratio": return_dd,
        "signal_count": signal_count,
        "avg_holding_days": window,
        "evidence_level": evidence,
        "conclusion_tag": _conclusion_tag(meta.get("etf_type", "unknown"), window, signal_count),
    }


def write_report(results: pd.DataFrame, classification: pd.DataFrame) -> None:
    lines = [
        "# ETF 类型化持有周期研究报告",
        "",
        "本报告是离线研究，不修改交易规则、不修改仓位、不写模拟买卖。",
        "",
        "## 样本说明",
        f"- 分类 ETF 数量：{len(classification)}",
        f"- 研究结果行数：{len(results)}",
        "- proxy_buy_signal：close > ma20 > ma60 且 20 日收益为正。",
        "- short_swing_weakening：前一日 5 日收益为正，当日 5 日收益转弱。",
        "- proxy_rank_decline_3d：价格动量代理分连续 3 日下降。",
        "- 所有 future return 只用于离线研究，严禁参与当天信号。",
        "",
        "## 按类型和窗口汇总",
        "| etf_type | signal_type | window | avg_return | win_rate | max_forward_drawdown | return/drawdown | signal_count | evidence |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if results.empty:
        lines.append("|  | 无可用样本 |  |  |  |  |  |  | sample_limited |")
    else:
        grouped = (
            results.groupby(["etf_type", "signal_type", "holding_window_days"], dropna=False)
            .agg(
                avg_return=("avg_return", "mean"),
                win_rate=("win_rate", "mean"),
                max_forward_drawdown=("max_forward_drawdown", "min"),
                return_drawdown_ratio=("return_drawdown_ratio", "mean"),
                signal_count=("signal_count", "sum"),
            )
            .reset_index()
        )
        grouped["evidence_level"] = grouped["signal_count"].apply(_evidence_label)
        for _, row in grouped.iterrows():
            lines.append(
                f"| {row['etf_type']} | {row['signal_type']} | {int(row['holding_window_days'])} | "
                f"{_pct(row['avg_return'])} | {_pct(row['win_rate'])} | {_pct(row['max_forward_drawdown'])} | "
                f"{_num(row['return_drawdown_ratio'])} | {int(row['signal_count'])} | {row['evidence_level']} |"
            )
    lines += [
        "",
        "## 重点判断",
        _type_judgement(results, "broad_index", "宽基是否适合 20-60 天"),
        _type_judgement(results, "sector", "行业是否更适合 10-30 天"),
        _type_judgement(results, "theme", "主题是否更适合 5-20 天"),
        _type_judgement(results, "hot_theme", "强事件主题是否应 3-10 天"),
        "",
        "## 当前持仓研究周期",
        "| code | name | etf_type | holding_profile | conclusion |",
        "| --- | --- | --- | --- | --- |",
    ]
    held_codes = {"515220", "512800", "515880"}
    held = classification[classification["code"].isin(held_codes)]
    for _, row in held.iterrows():
        lines.append(f"| {row['code']} | {row['name']} | {row['etf_type']} | {row['holding_profile']} | {row['classification_reason']} |")
    lines += [
        "",
        "## 结论边界",
        "- evidence_supported：样本数量相对较多，可进入下一阶段模拟观察。",
        "- sample_limited：样本有限，只能作为提示。",
        "- hypothesis_only：样本不足或缺失，需要继续积累。",
        "- 本报告不直接改变 mid_trend / short_swing / BUY ranking。",
    ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values("date").reset_index(drop=True).copy()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ret5"] = df["close"] / df["close"].shift(5) - 1
    df["ret20"] = df["close"] / df["close"].shift(20) - 1
    df["vol20"] = df["close"].pct_change().rolling(20).std()
    df["proxy_score"] = df["ret20"].fillna(0) + 0.5 * df["ret5"].fillna(0) - df["vol20"].fillna(0)
    df["proxy_buy_signal"] = (df["close"] > df["ma20"]) & (df["ma20"] > df["ma60"]) & (df["ret20"] > 0)
    df["short_swing_weakening"] = (df["ret5"].shift(1) > 0) & (df["ret5"] <= 0)
    df["proxy_rank_decline_3d"] = (df["proxy_score"] < df["proxy_score"].shift(1)) & (df["proxy_score"].shift(1) < df["proxy_score"].shift(2)) & (df["proxy_score"].shift(2) < df["proxy_score"].shift(3))
    for window in WINDOWS:
        df[f"future_{window}d_return"] = df["close"].shift(-window) / df["close"] - 1
    return df


def _window_forward_drawdowns(feat: pd.DataFrame, indexes: pd.Index, window: int) -> pd.Series:
    values = []
    close = feat["close"].reset_index(drop=True)
    for idx in indexes:
        if idx + window >= len(close):
            continue
        segment = close.iloc[idx : idx + window + 1]
        base = segment.iloc[0]
        if base <= 0:
            continue
        values.append(float((segment / base - 1).min()))
    return pd.Series(values, dtype=float)


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


def _evidence_label(count: int) -> str:
    if count >= 200:
        return "evidence_supported"
    if count >= 40:
        return "sample_limited"
    return "hypothesis_only"


def _conclusion_tag(etf_type: str, window: int, signal_count: int) -> str:
    if signal_count < 40:
        return "sample_limited"
    preferred = {
        "broad_index": range(20, 61),
        "sector": range(10, 31),
        "theme": range(5, 21),
        "hot_theme": range(3, 11),
        "bond_cash": range(30, 91),
        "qdii": range(10, 46),
        "commodity_resource": range(10, 46),
    }
    return "profile_match" if window in preferred.get(etf_type, []) else "profile_mismatch"


def _type_judgement(results: pd.DataFrame, etf_type: str, question: str) -> str:
    if results.empty or etf_type not in set(results.get("etf_type", [])):
        return f"- {question}：hypothesis_only，暂无足够样本。"
    subset = results[(results["etf_type"] == etf_type) & (results["signal_type"] == "proxy_buy")].copy()
    if subset.empty:
        return f"- {question}：hypothesis_only，暂无 proxy_buy 样本。"
    best = subset.sort_values(["return_drawdown_ratio", "avg_return"], ascending=False).head(1).iloc[0]
    return (
        f"- {question}：当前最佳窗口约 {int(best['holding_window_days'])} 日，"
        f"avg_return={_pct(best['avg_return'])}，signal_count={int(best['signal_count'])}，"
        f"证据等级={best['evidence_level']}。"
    )


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
