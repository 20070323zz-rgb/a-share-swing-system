"""未来收益标签生成。

future returns 只用于研究和模型训练，严禁参与当日信号、排名或评分。
"""

from __future__ import annotations

import pandas as pd


LABEL_HORIZONS = [5, 10, 20, 60]


def add_future_return_labels(model_df: pd.DataFrame, price_history: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """为 model_dataset 回填 future returns 和横截面 rank。"""
    out = model_df.copy()
    for horizon in LABEL_HORIZONS:
        out[f"future_{horizon}d_return"] = out.get(f"future_{horizon}d_return", "")
        out[f"future_{horizon}d_rank"] = out.get(f"future_{horizon}d_rank", "")
    out["future_20d_top30"] = out.get("future_20d_top30", "")

    for idx, row in out.iterrows():
        code = str(row.get("code", ""))
        history = price_history.get(code)
        if history is None or history.empty:
            continue
        date_value = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(date_value):
            continue
        history = history.sort_values("date").reset_index(drop=True)
        match = history.index[history["date"] == date_value]
        if len(match) == 0:
            continue
        pos = int(match[0])
        current_close = float(history.loc[pos, "close"])
        if current_close <= 0:
            continue
        for horizon in LABEL_HORIZONS:
            future_pos = pos + horizon
            if future_pos < len(history):
                out.at[idx, f"future_{horizon}d_return"] = round(float(history.loc[future_pos, "close"]) / current_close - 1, 6)

    for horizon in LABEL_HORIZONS:
        ret_col = f"future_{horizon}d_return"
        rank_col = f"future_{horizon}d_rank"
        numeric = pd.to_numeric(out[ret_col], errors="coerce")
        out[rank_col] = numeric.groupby(out["date"]).rank(pct=True, na_option="keep").round(6)

    future_20_rank = pd.to_numeric(out["future_20d_rank"], errors="coerce")
    out["future_20d_top30"] = future_20_rank.apply(lambda value: "" if pd.isna(value) else int(value >= 0.70))
    return out


def add_future_labels_to_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    """给单个价格序列生成未来收益标签，用于研究脚本。"""
    out = df.copy().sort_values("date").reset_index(drop=True)
    for horizon in LABEL_HORIZONS:
        out[f"future_{horizon}d_return"] = out["close"].shift(-horizon) / out["close"] - 1
    return out
