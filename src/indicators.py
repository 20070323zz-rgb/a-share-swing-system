"""技术指标计算。"""

from __future__ import annotations

import pandas as pd

from config import MA_LONG, MA_SHORT, RET_WINDOW


def add_indicators(df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """计算均线、涨跌幅、成交量变化和相对强弱。"""
    out = df.copy().sort_values("date")
    out["ma10"] = out["close"].rolling(10).mean()
    out["ma20"] = out["close"].rolling(MA_SHORT).mean()
    out["ma60"] = out["close"].rolling(MA_LONG).mean()
    out["ma10_slope"] = out["ma10"] - out["ma10"].shift(1)
    out["ma20_slope"] = out["ma20"] - out["ma20"].shift(1)
    out["ret10"] = out["close"] / out["close"].shift(10) - 1
    out["ret20"] = out["close"] / out["close"].shift(RET_WINDOW) - 1
    out["ret5"] = out["close"] / out["close"].shift(5) - 1
    out["rsi14"] = _rsi(out["close"], 14)
    out["volume_ma5"] = out["volume"].rolling(5).mean()
    out["volume_ma20"] = out["volume"].rolling(20).mean()
    out["volume_ratio"] = out["volume_ma5"] / out["volume_ma20"]
    out["max_volume_ratio_20"] = out["volume"] / out["volume_ma20"]
    out["max_volume_ratio_20"] = out["max_volume_ratio_20"].rolling(20).max()
    out["distance_above_ma10"] = out["close"] / out["ma10"] - 1
    out["distance_above_ma20"] = out["close"] / out["ma20"] - 1

    if benchmark_df is not None and not benchmark_df.empty:
        bench = benchmark_df[["date", "close"]].copy().sort_values("date")
        bench["benchmark_ret10"] = bench["close"] / bench["close"].shift(10) - 1
        bench["benchmark_ret20"] = bench["close"] / bench["close"].shift(RET_WINDOW) - 1
        out = out.merge(bench[["date", "benchmark_ret10", "benchmark_ret20"]], on="date", how="left")
        out["relative_strength_10"] = out["ret10"] - out["benchmark_ret10"]
        out["relative_strength"] = out["ret20"] - out["benchmark_ret20"]
    else:
        out["benchmark_ret10"] = pd.NA
        out["benchmark_ret20"] = pd.NA
        out["relative_strength_10"] = pd.NA
        out["relative_strength"] = pd.NA

    return out


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - 100 / (1 + rs)


def latest_on_or_before(df: pd.DataFrame, run_date: pd.Timestamp | None) -> pd.Series | None:
    """取指定日期之前最近一个交易日的数据。"""
    if df.empty:
        return None
    if run_date is None:
        return df.iloc[-1]
    subset = df[df["date"] <= run_date]
    if subset.empty:
        return None
    return subset.iloc[-1]
