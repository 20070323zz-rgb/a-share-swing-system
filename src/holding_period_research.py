"""Offline holding-period research by ETF type.

Future returns are used only for offline research reports. They are never used
to generate same-day signals or paper execution.
"""

from __future__ import annotations

import pandas as pd

from config import ETF_DAILY_DIR, REPORT_DIR
from data_loader import load_price_data
from etf_classifier import CLASSIFICATION_FILE, EXCLUDED_STATUS, main as build_classification


WINDOWS = [3, 5, 10, 20, 30, 45, 60]
CSV_FILE = REPORT_DIR / "holding_period_research.csv"
LEGACY_RESULT_FILE = REPORT_DIR / "holding_period_research_results.csv"
REPORT_FILE = REPORT_DIR / "holding_period_research_report.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    classification = pd.read_csv(CLASSIFICATION_FILE, dtype=str, keep_default_na=False).fillna("")
    rows = build_results(classification)
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)
    df.to_csv(LEGACY_RESULT_FILE, index=False)
    REPORT_FILE.write_text(render_report(df, classification), encoding="utf-8")
    print(f"holding_period rows: {len(df)}")
    print(f"written: {CSV_FILE}")
    print(f"written: {REPORT_FILE}")


def build_results(classification: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for _, meta in classification.iterrows():
        if meta.get("status") in EXCLUDED_STATUS:
            continue
        symbol = str(meta.get("symbol") or meta.get("code") or "").strip()
        if not symbol:
            continue
        prices, error = load_price_data(ETF_DAILY_DIR, symbol)
        if error or prices is None or len(prices) < 90:
            for window in WINDOWS:
                rows.append(_insufficient_row(meta, window, f"price_sample_insufficient: {error or len(prices) if prices is not None else 'missing'}"))
            continue
        feat = _features(prices)
        signals = {
            "all_days": feat.dropna(subset=["close"]),
            "proxy_buy": feat[feat["proxy_buy_signal"]],
            "momentum_positive": feat[feat["ret20"] > 0],
            "short_swing_weakening": feat[feat["short_swing_weakening"]],
        }
        for window in WINDOWS:
            for signal_type, signal_rows in signals.items():
                rows.append(_stats_row(meta, feat, signal_rows, window, signal_type))
    return rows


def render_report(results: pd.DataFrame, classification: pd.DataFrame) -> str:
    lines = [
        "# ETF 类型化持有周期研究报告",
        "",
        "本报告是离线研究，不修改交易规则、不修改仓位、不写模拟买卖。",
        "",
        "## 样本说明",
        f"- 分类 ETF 数量：{len(classification)}",
        f"- 研究结果行数：{len(results)}",
        f"- 研究窗口：{WINDOWS}",
        "- proxy_buy：close > ma20 > ma60 且 ret20 > 0。",
        "- future_return 只用于离线评估，不参与当天信号。",
        "",
        "## 按类型和窗口汇总",
        "| etf_type | signal_type | window | sample_count | avg_return | median_return | win_rate | max_forward_drawdown | avg_volatility | evidence | preferred_match |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if results.empty:
        lines.append("|  | 无可用样本 |  |  |  |  |  |  |  | hypothesis_only |  |")
    else:
        usable = results[results["sample_count"].astype(str) != "0"].copy()
        if usable.empty:
            lines.append("|  | 样本不足 |  |  |  |  |  |  |  | hypothesis_only |  |")
        else:
            for col in ["avg_return", "median_return", "win_rate", "max_forward_drawdown", "avg_volatility"]:
                usable[col] = pd.to_numeric(usable[col], errors="coerce")
            grouped = (
                usable.groupby(["etf_type", "signal_type", "holding_window_days"], dropna=False)
                .agg(
                    sample_count=("sample_count", lambda values: pd.to_numeric(values, errors="coerce").fillna(0).sum()),
                    avg_return=("avg_return", "mean"),
                    median_return=("median_return", "mean"),
                    win_rate=("win_rate", "mean"),
                    max_forward_drawdown=("max_forward_drawdown", "min"),
                    avg_volatility=("avg_volatility", "mean"),
                )
                .reset_index()
            )
            grouped["evidence_level"] = grouped["sample_count"].apply(_evidence_level)
            grouped["preferred_match"] = grouped.apply(lambda row: _preferred_match(str(row["etf_type"]), int(row["holding_window_days"])), axis=1)
            for _, row in grouped.iterrows():
                lines.append(
                    f"| {row['etf_type']} | {row['signal_type']} | {int(row['holding_window_days'])} | {int(row['sample_count'])} | "
                    f"{_pct(row['avg_return'])} | {_pct(row['median_return'])} | {_pct(row['win_rate'])} | "
                    f"{_pct(row['max_forward_drawdown'])} | {_pct(row['avg_volatility'])} | {row['evidence_level']} | {row['preferred_match']} |"
                )
    lines += [
        "",
        "## 当前研究假设",
        "- broad_index：20-60 天仍是合理初始假设，需要继续看样本。",
        "- sector：10-30 天更贴合行业轮动，但不能单日降分就卖。",
        "- theme/high_beta：5-20 天更敏感，应优先做 REVIEW/REDUCE 候选研究。",
        "- commodity_resource：10-45 天，需结合商品价格和政策事件解释。",
        "- bond_cash：30-90 天，重点是稳定性和流动性。",
        "- qdii：10-45 天，需要额外溢价、汇率和海外交易日检查。",
        "",
        "## 安全边界",
        "- 不改变 mid_trend / short_swing / BUY ranking。",
        "- 不修改 paper_positions.csv 或 paper_trades.csv。",
    ]
    return "\n".join(lines)


def _features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values("date").reset_index(drop=True).copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ret5"] = df["close"] / df["close"].shift(5) - 1
    df["ret20"] = df["close"] / df["close"].shift(20) - 1
    df["daily_return"] = df["close"].pct_change()
    df["vol20"] = df["daily_return"].rolling(20).std()
    df["proxy_buy_signal"] = (df["close"] > df["ma20"]) & (df["ma20"] > df["ma60"]) & (df["ret20"] > 0)
    df["short_swing_weakening"] = (df["ret5"].shift(1) > 0) & (df["ret5"] <= 0)
    for window in WINDOWS:
        df[f"future_{window}d_return"] = df["close"].shift(-window) / df["close"] - 1
    return df


def _stats_row(meta: pd.Series, feat: pd.DataFrame, signal_rows: pd.DataFrame, window: int, signal_type: str) -> dict:
    col = f"future_{window}d_return"
    values = pd.to_numeric(signal_rows.get(col, pd.Series(dtype=float)), errors="coerce").dropna()
    dd = _window_forward_drawdowns(feat, signal_rows.index, window)
    vols = pd.to_numeric(signal_rows.get("vol20", pd.Series(dtype=float)), errors="coerce").dropna()
    sample_count = int(len(values))
    return {
        "symbol": meta.get("symbol", meta.get("code", "")),
        "code": meta.get("code", meta.get("symbol", "")),
        "name": meta.get("name", ""),
        "group": meta.get("group", ""),
        "pool": meta.get("pool", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "risk_profile": meta.get("risk_profile", ""),
        "signal_type": signal_type,
        "holding_window_days": window,
        "sample_count": sample_count,
        "avg_return": _mean(values),
        "median_return": float(values.median()) if sample_count else "",
        "win_rate": float((values > 0).mean()) if sample_count else "",
        "max_forward_drawdown": float(dd.min()) if len(dd) else "",
        "avg_volatility": _mean(vols),
        "return_drawdown_ratio": _return_drawdown_ratio(values, dd),
        "evidence_level": _evidence_level(sample_count),
        "preferred_match": _preferred_match(str(meta.get("etf_type", "unknown")), window),
        "insufficient_reason": "" if sample_count >= 30 else "sample_count_below_30",
    }


def _insufficient_row(meta: pd.Series, window: int, reason: str) -> dict:
    return {
        "symbol": meta.get("symbol", meta.get("code", "")),
        "code": meta.get("code", meta.get("symbol", "")),
        "name": meta.get("name", ""),
        "group": meta.get("group", ""),
        "pool": meta.get("pool", ""),
        "etf_type": meta.get("etf_type", "unknown"),
        "risk_profile": meta.get("risk_profile", ""),
        "signal_type": "all_days",
        "holding_window_days": window,
        "sample_count": 0,
        "avg_return": "",
        "median_return": "",
        "win_rate": "",
        "max_forward_drawdown": "",
        "avg_volatility": "",
        "return_drawdown_ratio": "",
        "evidence_level": "hypothesis_only",
        "preferred_match": _preferred_match(str(meta.get("etf_type", "unknown")), window),
        "insufficient_reason": reason,
    }


def _window_forward_drawdowns(feat: pd.DataFrame, indexes: pd.Index, window: int) -> pd.Series:
    close = pd.to_numeric(feat["close"], errors="coerce").reset_index(drop=True)
    values = []
    for idx in indexes:
        if idx + window >= len(close):
            continue
        segment = close.iloc[idx : idx + window + 1]
        base = segment.iloc[0]
        if base <= 0:
            continue
        values.append(float((segment / base - 1).min()))
    return pd.Series(values, dtype=float)


def _return_drawdown_ratio(values: pd.Series, dd: pd.Series) -> float | str:
    if values.empty or dd.empty:
        return ""
    avg = float(values.mean())
    worst = abs(float(dd.min()))
    if worst == 0:
        return ""
    return avg / worst


def _preferred_match(etf_type: str, window: int) -> str:
    ranges = {
        "broad_index": range(20, 61),
        "sector": range(10, 31),
        "theme": range(5, 21),
        "high_beta": range(5, 21),
        "commodity_resource": range(10, 46),
        "bond_cash": range(30, 91),
        "qdii": range(10, 46),
    }
    return "yes" if window in ranges.get(etf_type, []) else "no"


def _evidence_level(count: object) -> str:
    numeric = int(float(count)) if str(count) not in {"", "nan"} else 0
    if numeric >= 200:
        return "evidence_supported"
    if numeric >= 40:
        return "sample_limited"
    return "hypothesis_only"


def _mean(series: pd.Series) -> float | str:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if len(values) else ""


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
