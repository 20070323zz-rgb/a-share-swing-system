"""Lightweight offline parameter sweep for ETF rotation research.

The sweep is intentionally simple and research-only. It does not update BUY
ranking weights, paper positions, paper trades, or strategy rules.
"""

from __future__ import annotations

from itertools import product

import pandas as pd

from config import ETF_DAILY_DIR, REPORT_DIR
from data_loader import load_price_data
from etf_classifier import CLASSIFICATION_FILE, EXCLUDED_STATUS, main as build_classification


CSV_FILE = REPORT_DIR / "parameter_sweep.csv"
REPORT_FILE = REPORT_DIR / "parameter_sweep_report.md"

MOMENTUM_WINDOWS = [10, 20, 40, 60]
VOL_WINDOWS = [10, 20, 40]
MAX_HOLDINGS = [1, 3, 5, 8]
TOP_N_UNIVERSE = 80
LOOKBACK_DAYS = 260


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    classification = pd.read_csv(CLASSIFICATION_FILE, dtype=str, keep_default_na=False).fillna("")
    market = _build_market_panel(classification)
    rows = build_sweep(market)
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)
    REPORT_FILE.write_text(render_report(df), encoding="utf-8")
    print(f"parameter_sweep rows: {len(df)}")
    print(f"written: {CSV_FILE}")
    print(f"written: {REPORT_FILE}")


def build_sweep(market: pd.DataFrame) -> list[dict]:
    rows = []
    if market.empty:
        for momentum_window, vol_window, max_holdings in product(MOMENTUM_WINDOWS, VOL_WINDOWS, MAX_HOLDINGS):
            rows.append(_empty_row(momentum_window, vol_window, max_holdings, "no_market_panel"))
        return rows
    dates = sorted(market["date"].unique())
    if len(dates) < 90:
        for momentum_window, vol_window, max_holdings in product(MOMENTUM_WINDOWS, VOL_WINDOWS, MAX_HOLDINGS):
            rows.append(_empty_row(momentum_window, vol_window, max_holdings, "date_sample_below_90"))
        return rows
    for momentum_window, vol_window, max_holdings in product(MOMENTUM_WINDOWS, VOL_WINDOWS, MAX_HOLDINGS):
        rows.append(_simulate_config(market, dates, momentum_window, vol_window, max_holdings))
    return rows


def render_report(df: pd.DataFrame) -> str:
    lines = [
        "# 参数扫描研究报告",
        "",
        "本报告为 phase2_model_research_v1 研究层，不修改 BUY ranking、不改仓位规则、不写模拟交易。",
        "",
        "## 扫描空间",
        f"- momentum_windows：{MOMENTUM_WINDOWS}",
        f"- volatility_windows：{VOL_WINDOWS}",
        f"- max_holdings：{MAX_HOLDINGS}",
        f"- 最近样本天数上限：{LOOKBACK_DAYS}",
        "",
        "## Top 参数组合",
        "| rank | momentum_window | volatility_window | max_holdings | sample_days | annual_return | annual_volatility | max_drawdown | sharpe_proxy | turnover_proxy | evidence | suggestion |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    if df.empty:
        lines.append("|  |  |  |  |  |  |  |  |  |  | hypothesis_only | 无结果 |")
    else:
        usable = df[pd.to_numeric(df["sample_days"], errors="coerce").fillna(0) > 30].copy()
        if usable.empty:
            lines.append("|  |  |  |  |  |  |  |  |  |  | hypothesis_only | 样本不足 |")
        else:
            usable["sharpe_proxy_num"] = pd.to_numeric(usable["sharpe_proxy"], errors="coerce").fillna(-999)
            top = usable.sort_values(["sharpe_proxy_num", "max_drawdown"], ascending=[False, False]).head(12)
            for idx, row in enumerate(top.to_dict(orient="records"), start=1):
                lines.append(
                    f"| {idx} | {row['momentum_window']} | {row['volatility_window']} | {row['max_holdings']} | {row['sample_days']} | "
                    f"{_pct(row['annual_return'])} | {_pct(row['annual_volatility'])} | {_pct(row['max_drawdown'])} | "
                    f"{_num(row['sharpe_proxy'])} | {_pct(row['turnover_proxy'])} | {row['evidence_level']} | {row['suggestion']} |"
                )
    lines += [
        "",
        "## 解释边界",
        "- 使用价格动量和波动惩罚代理，不等于当前正式 BUY ranking。",
        "- 未纳入交易成本、流动性冲击、新闻情绪和 QDII 溢价。",
        "- 结果只能作为 Main/GPT 评估参数方向的输入，不能直接上线。",
    ]
    return "\n".join(lines)


def _build_market_panel(classification: pd.DataFrame) -> pd.DataFrame:
    if classification.empty:
        return pd.DataFrame()
    candidates = classification[
        (~classification["status"].isin(EXCLUDED_STATUS))
        & (classification["etf_type"].isin(["broad_index", "sector", "theme", "high_beta", "commodity_resource"]))
    ].copy()
    rows = []
    for _, meta in candidates.head(TOP_N_UNIVERSE).iterrows():
        symbol = str(meta.get("symbol") or meta.get("code") or "").strip()
        prices, error = load_price_data(ETF_DAILY_DIR, symbol)
        if error or prices is None or len(prices) < 120:
            continue
        df = prices.sort_values("date").tail(LOOKBACK_DAYS + max(MOMENTUM_WINDOWS) + 5).copy()
        df["symbol"] = symbol
        df["name"] = meta.get("name", symbol)
        df["etf_type"] = meta.get("etf_type", "")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["next_return"] = df["close"].shift(-1) / df["close"] - 1
        df["daily_return"] = df["close"].pct_change()
        for window in MOMENTUM_WINDOWS:
            df[f"mom_{window}"] = df["close"] / df["close"].shift(window) - 1
        for window in VOL_WINDOWS:
            df[f"vol_{window}"] = df["daily_return"].rolling(window).std()
        rows.append(df[["date", "symbol", "name", "etf_type", "next_return"] + [f"mom_{w}" for w in MOMENTUM_WINDOWS] + [f"vol_{w}" for w in VOL_WINDOWS]])
    if not rows:
        return pd.DataFrame()
    panel = pd.concat(rows, ignore_index=True)
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")
    return panel.dropna(subset=["date", "symbol", "next_return"]).sort_values(["date", "symbol"]).reset_index(drop=True)


def _simulate_config(market: pd.DataFrame, dates: list[pd.Timestamp], momentum_window: int, vol_window: int, max_holdings: int) -> dict:
    mom_col = f"mom_{momentum_window}"
    vol_col = f"vol_{vol_window}"
    returns = []
    selections: list[set[str]] = []
    for date in dates[-LOOKBACK_DAYS:]:
        day = market[market["date"] == date].copy()
        day[mom_col] = pd.to_numeric(day[mom_col], errors="coerce")
        day[vol_col] = pd.to_numeric(day[vol_col], errors="coerce")
        day["next_return"] = pd.to_numeric(day["next_return"], errors="coerce")
        day = day.dropna(subset=[mom_col, vol_col, "next_return"])
        if len(day) < max_holdings:
            continue
        day["score"] = day[mom_col] - 0.7 * day[vol_col]
        selected = day.sort_values("score", ascending=False).head(max_holdings)
        returns.append(float(selected["next_return"].mean()))
        selections.append(set(selected["symbol"].astype(str)))
    if not returns:
        return _empty_row(momentum_window, vol_window, max_holdings, "no_valid_daily_selection")
    series = pd.Series(returns, dtype=float)
    equity = (1 + series).cumprod()
    annual_return = float(equity.iloc[-1] ** (252 / len(series)) - 1) if len(series) else 0.0
    annual_vol = float(series.std() * (252 ** 0.5)) if len(series) > 2 else 0.0
    max_drawdown = float((equity / equity.cummax() - 1).min()) if len(equity) else 0.0
    sharpe = annual_return / annual_vol if annual_vol else 0.0
    turnover = _turnover_proxy(selections)
    return {
        "momentum_window": momentum_window,
        "volatility_window": vol_window,
        "max_holdings": max_holdings,
        "sample_days": len(series),
        "annual_return": annual_return,
        "annual_volatility": annual_vol,
        "max_drawdown": max_drawdown,
        "sharpe_proxy": sharpe,
        "turnover_proxy": turnover,
        "evidence_level": "sample_limited" if len(series) >= 120 else "hypothesis_only",
        "suggestion": "candidate_for_deeper_backtest" if len(series) >= 120 and sharpe > 0 else "research_only",
        "insufficient_reason": "",
    }


def _empty_row(momentum_window: int, vol_window: int, max_holdings: int, reason: str) -> dict:
    return {
        "momentum_window": momentum_window,
        "volatility_window": vol_window,
        "max_holdings": max_holdings,
        "sample_days": 0,
        "annual_return": "",
        "annual_volatility": "",
        "max_drawdown": "",
        "sharpe_proxy": "",
        "turnover_proxy": "",
        "evidence_level": "hypothesis_only",
        "suggestion": "need_more_data",
        "insufficient_reason": reason,
    }


def _turnover_proxy(selections: list[set[str]]) -> float:
    if len(selections) < 2:
        return 0.0
    changes = []
    for prior, current in zip(selections, selections[1:]):
        if not prior and not current:
            changes.append(0.0)
            continue
        union = prior | current
        same = prior & current
        changes.append(1 - len(same) / len(union) if union else 0.0)
    return float(pd.Series(changes).mean()) if changes else 0.0


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
