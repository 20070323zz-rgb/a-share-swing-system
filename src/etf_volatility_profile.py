"""Build ETF volatility profiles for exit-rule research.

This script is research-only. It reads local ETF daily CSV files and metadata,
then writes volatility reports. It never touches broker APIs, paper trades, or
paper positions.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
REPORT_DIR = PROJECT_ROOT / "reports"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.csv"

OUTPUT_CSV = REPORT_DIR / "etf_volatility_profile.csv"
OUTPUT_MD = REPORT_DIR / "etf_volatility_profile.md"

LOW_AMOUNT_THRESHOLD = 20_000_000.0
WATCH_AMOUNT_THRESHOLD = 50_000_000.0
MIN_BACKTEST_DAYS = 120


TYPE_ORDER = [
    "broad_index",
    "sector",
    "theme",
    "high_beta",
    "commodity_resource",
    "defensive",
    "bond_cash",
    "qdii",
    "unknown",
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_metadata()
    rows = []
    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        symbol = extract_code(path.stem)
        if not symbol:
            continue
        rows.append(profile_one(path, symbol, meta.get(symbol, {})))
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["etf_type", "group", "symbol"]).reset_index(drop=True)
    df.to_csv(OUTPUT_CSV, index=False)
    OUTPUT_MD.write_text(render_report(df), encoding="utf-8")
    print(f"volatility profile rows: {len(df)}")
    print(f"written: {OUTPUT_CSV}")
    print(f"written: {OUTPUT_MD}")


def load_metadata() -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for path, code_col, pool_col in [
        (CLASSIFICATION_FILE, "symbol", "pool"),
        (WATCHLIST_FILE, "code", "role"),
    ]:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
        except Exception:
            continue
        for _, row in df.iterrows():
            code = extract_code(row.get(code_col, ""))
            if not code:
                continue
            item = meta.setdefault(code, {})
            for field in ["name", "group", "etf_type", "risk_profile", "holding_profile"]:
                value = str(row.get(field, "") or "").strip()
                if value and not item.get(field):
                    item[field] = value
            pool = str(row.get(pool_col, "") or "").strip()
            if pool and not item.get("pool_current"):
                item["pool_current"] = pool
    return meta


def profile_one(path: Path, symbol: str, meta: dict) -> dict:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return base_row(symbol, meta, f"read_error: {exc}")
    required = {"date", "open", "high", "low", "close"}
    if df.empty or not required.issubset(df.columns):
        return base_row(symbol, meta, "missing_required_price_columns")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume", "amount", "money"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    if df.empty:
        return base_row(symbol, meta, "empty_after_clean")

    close = df["close"]
    returns = close.pct_change(fill_method=None)
    intraday_range = (df["high"] - df["low"]) / close.replace(0, pd.NA)
    drawdown = close / close.cummax() - 1.0
    rolling_20d_drawdown = close / close.rolling(20, min_periods=5).max() - 1.0
    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_pct = true_range / close.replace(0, pd.NA)
    amount_col = "amount" if "amount" in df.columns else "money" if "money" in df.columns else ""
    amount = df[amount_col] if amount_col else pd.Series(dtype=float)

    trading_days = int(len(df))
    avg_amount_20 = float(amount.tail(20).mean()) if not amount.empty else 0.0
    etf_type = normalize_type(str(meta.get("etf_type") or "unknown"), str(meta.get("group") or ""), str(meta.get("name") or symbol))
    return {
        "symbol": symbol,
        "name": meta.get("name") or symbol,
        "etf_type": etf_type,
        "group": meta.get("group") or "unknown",
        "start_date": df["date"].min().strftime("%Y-%m-%d"),
        "end_date": df["date"].max().strftime("%Y-%m-%d"),
        "trading_days": trading_days,
        "avg_daily_return": round(float(returns.mean(skipna=True)), 8),
        "daily_volatility": round(float(returns.std(skipna=True)), 8),
        "annualized_volatility": round(float(returns.std(skipna=True) * (252 ** 0.5)), 6),
        "avg_intraday_range_pct": round(float(intraday_range.mean(skipna=True)), 6),
        "max_drawdown": round(float(drawdown.min(skipna=True)), 6),
        "avg_rolling_20d_drawdown": round(float(rolling_20d_drawdown.mean(skipna=True)), 6),
        "atr_14_pct": round(float(atr_pct.rolling(14, min_periods=5).mean().iloc[-1]), 6),
        "atr_20_pct": round(float(atr_pct.rolling(20, min_periods=5).mean().iloc[-1]), 6),
        "recent_20d_volatility": round(float(returns.tail(20).std(skipna=True) * (252 ** 0.5)), 6),
        "recent_60d_volatility": round(float(returns.tail(60).std(skipna=True) * (252 ** 0.5)), 6),
        "liquidity_status": liquidity_status(avg_amount_20),
        "data_length_status": "short_history" if trading_days < MIN_BACKTEST_DAYS else "ok",
        "avg_amount_20d": round(avg_amount_20, 2),
        "read_status": "ok",
    }


def base_row(symbol: str, meta: dict, reason: str) -> dict:
    return {
        "symbol": symbol,
        "name": meta.get("name") or symbol,
        "etf_type": normalize_type(str(meta.get("etf_type") or "unknown"), str(meta.get("group") or ""), str(meta.get("name") or symbol)),
        "group": meta.get("group") or "unknown",
        "start_date": "",
        "end_date": "",
        "trading_days": 0,
        "avg_daily_return": 0.0,
        "daily_volatility": 0.0,
        "annualized_volatility": 0.0,
        "avg_intraday_range_pct": 0.0,
        "max_drawdown": 0.0,
        "avg_rolling_20d_drawdown": 0.0,
        "atr_14_pct": 0.0,
        "atr_20_pct": 0.0,
        "recent_20d_volatility": 0.0,
        "recent_60d_volatility": 0.0,
        "liquidity_status": "unknown",
        "data_length_status": "invalid",
        "avg_amount_20d": 0.0,
        "read_status": reason,
    }


def type_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for etf_type, sub in df.groupby("etf_type"):
        sub = sub[sub["read_status"] == "ok"]
        if sub.empty:
            continue
        rows.append(
            {
                "etf_type": etf_type,
                "count": int(len(sub)),
                "avg_annualized_volatility": sub["annualized_volatility"].mean(),
                "median_annualized_volatility": sub["annualized_volatility"].median(),
                "avg_max_drawdown": sub["max_drawdown"].mean(),
                "median_atr_14_pct": sub["atr_14_pct"].median(),
                "p75_atr_14_pct": sub["atr_14_pct"].quantile(0.75),
                "p90_atr_14_pct": sub["atr_14_pct"].quantile(0.90),
                "recommended_stop_search_range": stop_search_range(etf_type, sub["atr_14_pct"].median(), sub["annualized_volatility"].median()),
                "recommended_trailing_search_range": trailing_search_range(etf_type, sub["atr_14_pct"].median(), sub["annualized_volatility"].median()),
            }
        )
    return pd.DataFrame(rows).sort_values("etf_type")


def stop_search_range(etf_type: str, median_atr: float, median_vol: float) -> str:
    atr_pct = max(float(median_atr or 0), 0.005)
    if etf_type == "bond_cash":
        return "0.5%-2.5%; use bond/cash-specific validation"
    if etf_type == "qdii":
        return "observe only; add premium/fx/calendar checks before auto exit"
    if etf_type in {"theme", "high_beta"}:
        return f"4%-10% or {1.5 * atr_pct:.1%}-{3.5 * atr_pct:.1%} ATR-equivalent"
    if etf_type == "broad_index":
        return f"5%-12% or {2.0 * atr_pct:.1%}-{4.0 * atr_pct:.1%} ATR-equivalent"
    if etf_type in {"sector", "commodity_resource"}:
        return f"4%-10% or {1.8 * atr_pct:.1%}-{3.5 * atr_pct:.1%} ATR-equivalent"
    return "observe only until classification is fixed"


def trailing_search_range(etf_type: str, median_atr: float, median_vol: float) -> str:
    atr_pct = max(float(median_atr or 0), 0.005)
    if etf_type == "bond_cash":
        return "not primary; prefer duration/credit risk review"
    if etf_type == "qdii":
        return "observe only; premium/fx required"
    if etf_type in {"theme", "high_beta"}:
        return f"profit start 4%-10%, trail {2.0 * atr_pct:.1%}-{4.0 * atr_pct:.1%}"
    if etf_type == "broad_index":
        return f"profit start 5%-12%, trail {2.5 * atr_pct:.1%}-{5.0 * atr_pct:.1%}"
    if etf_type in {"sector", "commodity_resource"}:
        return f"profit start 4%-12%, trail {2.0 * atr_pct:.1%}-{4.5 * atr_pct:.1%}"
    return "observe only until classification is fixed"


def render_report(df: pd.DataFrame) -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = type_summary(df)
    lines = [
        f"# ETF Volatility Profile {generated_at}",
        "",
        "本报告只用于退出规则参数研究，不接入交易执行层。",
        "",
        "## 摘要",
        f"- ETF 数量：{len(df)}",
        f"- 数据有效数量：{int((df.get('read_status', pd.Series(dtype=str)) == 'ok').sum()) if not df.empty else 0}",
        f"- 短历史数量：{int((df.get('data_length_status', pd.Series(dtype=str)) == 'short_history').sum()) if not df.empty else 0}",
        f"- 低/未知流动性数量：{int(df.get('liquidity_status', pd.Series(dtype=str)).isin(['low', 'unknown']).sum()) if not df.empty else 0}",
        "",
        "## ETF 类型波动摘要",
        summary_to_markdown(summary),
        "",
        "## 最高波动 ETF 样例",
        rows_to_markdown(
            df[df["read_status"] == "ok"].sort_values("annualized_volatility", ascending=False).head(20),
            ["symbol", "name", "etf_type", "group", "annualized_volatility", "max_drawdown", "atr_14_pct", "liquidity_status"],
        ),
        "",
        "## 最大回撤 ETF 样例",
        rows_to_markdown(
            df[df["read_status"] == "ok"].sort_values("max_drawdown", ascending=True).head(20),
            ["symbol", "name", "etf_type", "group", "annualized_volatility", "max_drawdown", "atr_14_pct", "liquidity_status"],
        ),
        "",
        "## 使用说明",
        "- 本报告给出的是参数搜索范围，不是正式止盈止损规则。",
        "- 固定百分比规则容易忽略 ETF 类型差异，后续回测应与 ATR/波动率规则对比。",
        "- 债券/货币 ETF 不应套用普通权益 ETF 止盈止损。",
        "- QDII 暂不建议自动交易，需要溢价、汇率、海外交易日、申赎状态检查。",
    ]
    return "\n".join(lines) + "\n"


def summary_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "暂无数据。"
    cols = [
        "etf_type",
        "count",
        "avg_annualized_volatility",
        "median_annualized_volatility",
        "avg_max_drawdown",
        "median_atr_14_pct",
        "p75_atr_14_pct",
        "recommended_stop_search_range",
        "recommended_trailing_search_range",
    ]
    return rows_to_markdown(df, cols)


def rows_to_markdown(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "暂无数据。"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        lines.append("| " + " | ".join(format_value(row.get(col, "")) for col in cols) + " |")
    return "\n".join(lines)


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value).replace("|", "/").replace("\n", " ")


def liquidity_status(avg_amount_20: float) -> str:
    if avg_amount_20 <= 0:
        return "unknown"
    if avg_amount_20 < LOW_AMOUNT_THRESHOLD:
        return "low"
    if avg_amount_20 < WATCH_AMOUNT_THRESHOLD:
        return "watch"
    return "ok"


def normalize_type(etf_type: str, group: str, name: str) -> str:
    text = f"{etf_type} {group} {name}".lower()
    if "qdii" in text or any(keyword in text for keyword in ["港股", "恒生", "纳指", "标普", "日经", "印度", "德国", "中概"]):
        return "qdii"
    if "防御" in text or any(keyword in text for keyword in ["红利", "低波", "黄金"]):
        return "defensive"
    if etf_type in {"broad_based", "broad_index"}:
        return "broad_index"
    return etf_type or "unknown"


def extract_code(value: object) -> str:
    match = re.search(r"(\d{6})", str(value))
    return match.group(1) if match else ""


if __name__ == "__main__":
    main()
