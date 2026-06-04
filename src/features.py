"""ETF 模型研究因子计算。

本模块只处理本地行情和研究特征，不连接券商、不下单。
"""

from __future__ import annotations

import pandas as pd


def compute_features(df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None, meta: dict | None = None) -> pd.DataFrame:
    """计算统一研究因子。"""
    out = df.copy().sort_values("date").reset_index(drop=True)
    out["ma10"] = out["close"].rolling(10).mean()
    out["ma20"] = out["close"].rolling(20).mean()
    out["ma60"] = out["close"].rolling(60).mean()
    out["close_above_ma10"] = out["close"] > out["ma10"]
    out["close_above_ma20"] = out["close"] > out["ma20"]
    out["close_above_ma60"] = out["close"] > out["ma60"]
    out["ma10_slope"] = out["ma10"] - out["ma10"].shift(1)
    out["ma20_slope"] = out["ma20"] - out["ma20"].shift(1)
    out["return_5d"] = out["close"] / out["close"].shift(5) - 1
    out["return_10d"] = out["close"] / out["close"].shift(10) - 1
    out["return_20d"] = out["close"] / out["close"].shift(20) - 1
    out["return_60d"] = out["close"] / out["close"].shift(60) - 1
    out["volume_ma5"] = out["volume"].rolling(5).mean()
    out["volume_ma20"] = out["volume"].rolling(20).mean()
    out["volume_ratio_5d"] = out["volume"] / out["volume_ma5"]
    out["volume_ratio_20d"] = out["volume_ma5"] / out["volume_ma20"]
    out["volatility_20d"] = out["close"].pct_change().rolling(20).std()
    out["max_drawdown_20d"] = out["close"].rolling(20).apply(_window_max_drawdown, raw=False)
    out["distance_to_ma10"] = out["close"] / out["ma10"] - 1
    out["distance_to_ma20"] = out["close"] / out["ma20"] - 1

    if benchmark_df is not None and not benchmark_df.empty:
        bench = benchmark_df[["date", "close"]].copy().sort_values("date")
        for window in [10, 20, 60]:
            bench[f"benchmark_return_{window}d"] = bench["close"] / bench["close"].shift(window) - 1
        out = out.merge(bench[["date", "benchmark_return_10d", "benchmark_return_20d", "benchmark_return_60d"]], on="date", how="left")
        for window in [10, 20, 60]:
            out[f"relative_strength_{window}d"] = out[f"return_{window}d"] - out[f"benchmark_return_{window}d"]
    else:
        for window in [10, 20, 60]:
            out[f"relative_strength_{window}d"] = pd.NA

    meta = meta or {}
    out["group"] = meta.get("group", "")
    out["role"] = meta.get("role", "")
    out["preferred_strategy"] = meta.get("preferred_strategy", "")
    return out


def latest_feature_row(df: pd.DataFrame, benchmark_df: pd.DataFrame | None, meta: dict, run_date: pd.Timestamp | None = None) -> pd.Series | None:
    """返回指定日期前最近一行研究因子。"""
    features = compute_features(df, benchmark_df, meta)
    if features.empty:
        return None
    if run_date is None:
        return features.iloc[-1]
    subset = features[features["date"] <= run_date]
    return None if subset.empty else subset.iloc[-1]


def _window_max_drawdown(close: pd.Series) -> float:
    peak = close.cummax()
    drawdown = close / peak - 1
    return float(drawdown.min())
