"""High-beta paper position risk watch.

Observation-only module. It does not reduce/sell, does not write paper trades
or positions, and never connects to broker APIs or real accounts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import ETF_DAILY_DIR, PAPER_INITIAL_CASH, REPORT_DIR
from valuation import load_latest_position_valuation


CSV_FILE = REPORT_DIR / "high_beta_risk_watch.csv"
JSON_FILE = REPORT_DIR / "high_beta_risk_watch.json"
MD_FILE = REPORT_DIR / "high_beta_risk_watch.md"
POSITION_REVIEW_FILE = REPORT_DIR / "position_review_state.json"
PROFIT_PREVIEW_FILE = REPORT_DIR / "profit_protection_preview.json"
PORTFOLIO_EXPOSURE_FILE = REPORT_DIR / "portfolio_exposure.json"

HIGH_BETA_EQUITY_WATCH_PCT = 0.15
HIGH_BETA_EQUITY_CAUTION_PCT = 0.25
SINGLE_HIGH_BETA_WATCH_PCT = 0.10
FINANCE_HOLDINGS_WATCH_PCT = 0.40
FINANCE_EQUITY_WATCH_PCT = 0.15
RECENT_DRAWDOWN_10D_CAUTION_PCT = -0.05
RECENT_DRAWDOWN_10D_ELEVATED_PCT = -0.08
VOLATILITY_10D_WATCH_PCT = 0.035

STATE_CN = {
    "HB_NORMAL": "高波动正常",
    "HB_WATCH": "高波动观察",
    "HB_CAUTION": "高波动谨慎",
    "HB_ELEVATED": "高波动风险升高",
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_high_beta_risk_watch()
    df = pd.DataFrame(payload["rows"])
    df.to_csv(CSV_FILE, index=False)
    JSON_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_FILE.write_text(render_report(payload), encoding="utf-8")
    print(f"high_beta rows: {len(df)}")
    print(f"written: {MD_FILE}")


def build_high_beta_risk_watch() -> dict[str, Any]:
    valuation = load_latest_position_valuation()
    positions = valuation["positions"]
    exposure = _read_json(PORTFOLIO_EXPOSURE_FILE)
    position_review = _map_rows(_read_json(POSITION_REVIEW_FILE).get("rows", []))
    profit_preview = _map_rows(_read_json(PROFIT_PREVIEW_FILE).get("rows", []))
    total_equity = _total_equity()
    total_holdings = float(valuation.get("summary", {}).get("total_market_value", 0.0) or 0.0)
    enriched = []
    for item in positions.to_dict(orient="records"):
        review = position_review.get(str(item.get("symbol", "")).strip(), {})
        profit = profit_preview.get(str(item.get("symbol", "")).strip(), {})
        enriched.append(_merge_position(item, review, profit))
    high_beta_positions = [row for row in enriched if _is_high_beta(row)]
    finance_positions = [row for row in enriched if str(row.get("group", "")) == "金融地产"]
    exposure_summary = _exposure_summary(high_beta_positions, finance_positions, total_equity, total_holdings)
    rows = [_watch_row(row, exposure_summary, total_equity, total_holdings) for row in high_beta_positions]
    exposure_summary["high_beta_exposure_state"], exposure_summary["high_beta_exposure_reasons"] = _exposure_state(exposure_summary)
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observation_only": True,
        "execution_allowed": False,
        "state_labels": STATE_CN,
        "thresholds": {
            "high_beta_equity_watch_pct": HIGH_BETA_EQUITY_WATCH_PCT,
            "high_beta_equity_caution_pct": HIGH_BETA_EQUITY_CAUTION_PCT,
            "single_high_beta_watch_pct": SINGLE_HIGH_BETA_WATCH_PCT,
            "finance_holdings_watch_pct": FINANCE_HOLDINGS_WATCH_PCT,
            "finance_equity_watch_pct": FINANCE_EQUITY_WATCH_PCT,
            "recent_drawdown_10d_caution_pct": RECENT_DRAWDOWN_10D_CAUTION_PCT,
            "recent_drawdown_10d_elevated_pct": RECENT_DRAWDOWN_10D_ELEVATED_PCT,
            "volatility_10d_watch_pct": VOLATILITY_10D_WATCH_PCT,
        },
        "summary": exposure_summary,
        "rows": rows,
        "portfolio_exposure_source": "reports/portfolio_exposure.json" if exposure else "valuation positions",
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trade_engine_modified": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
            "execution_allowed": False,
        },
    }


def _merge_position(item: dict[str, Any], review: dict[str, Any], profit: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    for key in [
        "review_state",
        "mid_trend",
        "short_swing",
        "rank",
        "rank_change",
        "rank_decay_days",
        "high_beta_flag",
        "recommended_review_action",
    ]:
        if key in review:
            row[key] = review[key]
    for key in ["profit_protection_state", "drawdown_from_profit_peak_pct"]:
        if key in profit:
            row[key] = profit[key]
    return row


def _watch_row(row: dict[str, Any], exposure: dict[str, Any], total_equity: float, total_holdings: float) -> dict[str, Any]:
    symbol = str(row.get("symbol", "")).strip()
    prices = _price_window(symbol)
    metrics = _price_metrics(prices)
    market_value = _float(row.get("market_value"))
    weight_equity = market_value / total_equity if total_equity else 0.0
    weight_holdings = market_value / total_holdings if total_holdings else 0.0
    flags = _position_flags(row, metrics, weight_equity, exposure)
    state, level, action = _position_state(flags)
    reasons = _position_reasons(flags, exposure, metrics, row)
    return {
        "symbol": symbol,
        "name": row.get("name", symbol),
        "group": row.get("group", ""),
        "type": row.get("etf_type", row.get("type", "high_beta")),
        "quantity": _float(row.get("quantity")),
        "latest_close": _float(row.get("latest_close", row.get("current_price"))),
        "market_value": round(market_value, 2),
        "position_weight_of_equity": weight_equity,
        "position_weight_of_holdings": weight_holdings,
        "unrealized_pnl": _float(row.get("unrealized_pnl")),
        "unrealized_pnl_pct": _float(row.get("unrealized_pnl_pct")),
        "mid_trend": row.get("mid_trend", "N/A"),
        "short_swing": row.get("short_swing", "N/A"),
        "rank": row.get("rank", ""),
        "rank_change": row.get("rank_change", ""),
        "rank_decay_days": int(_float(row.get("rank_decay_days"))),
        "recent_return_5d": metrics["return_5d"],
        "recent_return_10d": metrics["return_10d"],
        "recent_volatility_10d": metrics["volatility_10d"],
        "recent_drawdown_10d": metrics["drawdown_10d"],
        "high_beta_risk_state": state,
        "high_beta_risk_state_cn": STATE_CN.get(state, state),
        "high_beta_risk_level": level,
        "high_beta_risk_reasons": "；".join(reasons),
        "recommended_review_action": action,
        "execution_allowed": False,
        "data_quality": metrics["data_quality"],
        "price_rows": metrics["rows"],
        "review_state": row.get("review_state", ""),
        "profit_protection_state": row.get("profit_protection_state", ""),
        "safety_note": "高波动风险为观察指标，不会自动交易。",
    }


def _position_flags(row: dict[str, Any], metrics: dict[str, Any], weight_equity: float, exposure: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    mid = str(row.get("mid_trend", "")).upper()
    short = str(row.get("short_swing", "")).upper()
    if weight_equity >= SINGLE_HIGH_BETA_WATCH_PCT:
        flags.append("single_high_beta_weight_watch")
    if exposure["high_beta_weight_of_equity"] >= HIGH_BETA_EQUITY_WATCH_PCT:
        flags.append("high_beta_equity_weight_watch")
    if exposure["finance_real_estate_weight_of_holdings"] >= FINANCE_HOLDINGS_WATCH_PCT:
        flags.append("finance_group_holdings_watch")
    if exposure["finance_real_estate_weight_of_equity"] >= FINANCE_EQUITY_WATCH_PCT:
        flags.append("finance_group_equity_watch")
    if short == "WATCH":
        flags.append("short_swing_watch")
    if short == "SELL":
        flags.append("short_swing_sell")
    if mid in {"WATCH", "SELL"}:
        flags.append("mid_trend_weak")
    if int(_float(row.get("rank_decay_days"))) >= 2:
        flags.append("rank_decline_2d")
    rank_change = _float(row.get("rank_change"), fallback=float("nan"))
    if pd.notna(rank_change) and rank_change < 0:
        flags.append("rank_single_day_decline")
    if metrics["drawdown_10d"] <= RECENT_DRAWDOWN_10D_CAUTION_PCT:
        flags.append("recent_drawdown_10d_caution")
    if metrics["drawdown_10d"] <= RECENT_DRAWDOWN_10D_ELEVATED_PCT:
        flags.append("recent_drawdown_10d_elevated")
    if metrics["volatility_10d"] >= VOLATILITY_10D_WATCH_PCT:
        flags.append("volatility_10d_watch")
    if _float(row.get("unrealized_pnl_pct")) <= -0.035:
        flags.append("floating_loss_watch")
    if str(row.get("profit_protection_state", "")).upper() in {"PROFIT_PROTECTION_REVIEW", "PROFIT_LOCK_CANDIDATE"}:
        flags.append("profit_protection_watch")
    return list(dict.fromkeys(flags))


def _position_state(flags: list[str]) -> tuple[str, int, str]:
    if "mid_trend_weak" in flags or "short_swing_sell" in flags or "recent_drawdown_10d_elevated" in flags:
        return "HB_ELEVATED", 3, "高波动风险升高，进入人工复核；不自动交易。"
    caution_set = {
        "high_beta_equity_weight_watch",
        "finance_group_holdings_watch",
        "finance_group_equity_watch",
        "rank_decline_2d",
        "recent_drawdown_10d_caution",
        "short_swing_watch",
        "floating_loss_watch",
        "profit_protection_watch",
    }
    caution_hits = len([flag for flag in flags if flag in caution_set])
    if caution_hits >= 2:
        return "HB_CAUTION", 2, "高波动谨慎观察；不自动减仓或卖出。"
    if any(flag in flags for flag in ["finance_group_holdings_watch", "single_high_beta_weight_watch", "volatility_10d_watch", "rank_single_day_decline", "short_swing_watch"]):
        return "HB_WATCH", 1, "高波动观察：证券类 ETF 对市场情绪敏感，不自动交易。"
    return "HB_NORMAL", 0, "高波动持仓仍在可观察范围内，继续跟踪。"


def _position_reasons(flags: list[str], exposure: dict[str, Any], metrics: dict[str, Any], row: dict[str, Any]) -> list[str]:
    reasons = ["证券/券商类 ETF 属 high_beta，对成交额、风险偏好和市场情绪更敏感。"]
    mapping = {
        "single_high_beta_weight_watch": "单只 high_beta 持仓占总资产比例达到观察阈值。",
        "high_beta_equity_weight_watch": "组合 high_beta 占总资产比例偏高。",
        "finance_group_holdings_watch": "金融地产组占持仓市值比例偏高，需观察组合集中度。",
        "finance_group_equity_watch": "金融地产组占总资产比例达到观察阈值。",
        "short_swing_watch": "short_swing 转 WATCH。",
        "short_swing_sell": "short_swing 转 SELL。",
        "mid_trend_weak": "mid_trend 转弱。",
        "rank_decline_2d": "rank_score 连续下降。",
        "rank_single_day_decline": "rank_score 单日下降。",
        "recent_drawdown_10d_caution": "近 10 日回撤达到谨慎观察阈值。",
        "recent_drawdown_10d_elevated": "近 10 日回撤达到风险升高阈值。",
        "volatility_10d_watch": "近 10 日波动率较高。",
        "floating_loss_watch": "当前浮亏扩大，需要观察。",
        "profit_protection_watch": "浮盈保护层进入复核/锁定候选。",
    }
    reasons.extend(mapping[flag] for flag in flags if flag in mapping)
    reasons.append(
        f"当前 high_beta 占总资产 {exposure['high_beta_weight_of_equity']:.2%}，占持仓 {exposure['high_beta_weight_of_holdings']:.2%}；"
        f"金融地产组占持仓 {exposure['finance_real_estate_weight_of_holdings']:.2%}。"
    )
    reasons.append(f"近 10 日波动率 {metrics['volatility_10d']:.2%}，近 10 日回撤 {metrics['drawdown_10d']:.2%}。")
    return list(dict.fromkeys(reasons))


def _exposure_summary(high_beta_positions: list[dict[str, Any]], finance_positions: list[dict[str, Any]], total_equity: float, total_holdings: float) -> dict[str, Any]:
    high_beta_market_value = sum(_float(row.get("market_value")) for row in high_beta_positions)
    finance_market_value = sum(_float(row.get("market_value")) for row in finance_positions)
    max_single = max([_float(row.get("market_value")) / total_equity for row in high_beta_positions], default=0.0) if total_equity else 0.0
    return {
        "total_equity": round(total_equity, 2),
        "total_holdings_market_value": round(total_holdings, 2),
        "high_beta_position_count": len(high_beta_positions),
        "high_beta_market_value": round(high_beta_market_value, 2),
        "high_beta_weight_of_equity": high_beta_market_value / total_equity if total_equity else 0.0,
        "high_beta_weight_of_holdings": high_beta_market_value / total_holdings if total_holdings else 0.0,
        "finance_real_estate_market_value": round(finance_market_value, 2),
        "finance_real_estate_weight_of_equity": finance_market_value / total_equity if total_equity else 0.0,
        "finance_real_estate_weight_of_holdings": finance_market_value / total_holdings if total_holdings else 0.0,
        "max_single_high_beta_weight": max_single,
        "execution_allowed": False,
        "safety_note": "高波动风险为观察指标，不会自动交易。",
    }


def _exposure_state(summary: dict[str, Any]) -> tuple[str, str]:
    reasons = []
    if summary["high_beta_weight_of_equity"] >= HIGH_BETA_EQUITY_CAUTION_PCT:
        reasons.append("high_beta 占总资产超过 25%。")
    elif summary["high_beta_weight_of_equity"] >= HIGH_BETA_EQUITY_WATCH_PCT:
        reasons.append("high_beta 占总资产超过 15%。")
    if summary["finance_real_estate_weight_of_holdings"] >= FINANCE_HOLDINGS_WATCH_PCT:
        reasons.append("金融地产组占持仓市值超过 40%，组合集中度需观察。")
    if summary["finance_real_estate_weight_of_equity"] >= FINANCE_EQUITY_WATCH_PCT:
        reasons.append("金融地产组占总资产超过 15%。")
    if summary["max_single_high_beta_weight"] >= SINGLE_HIGH_BETA_WATCH_PCT:
        reasons.append("单只 high_beta 占总资产超过 10%。")
    if len(reasons) >= 3 or summary["high_beta_weight_of_equity"] >= HIGH_BETA_EQUITY_CAUTION_PCT:
        return "HB_CAUTION", "；".join(reasons)
    if reasons:
        return "HB_WATCH", "；".join(reasons)
    return "HB_NORMAL", "high_beta 暴露处于观察范围内。"


def _price_window(symbol: str) -> pd.DataFrame:
    path = _price_path(symbol)
    if path is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, usecols=lambda col: col in {"date", "close"})
    except Exception:
        return pd.DataFrame()
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.dropna(subset=["date", "close"]).sort_values("date").tail(12)


def _price_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or len(df) < 2:
        return {"return_5d": 0.0, "return_10d": 0.0, "volatility_10d": 0.0, "drawdown_10d": 0.0, "rows": int(len(df)), "data_quality": "missing_or_insufficient"}
    close = df["close"].astype(float)
    ret = close.pct_change().dropna()
    latest = float(close.iloc[-1])
    ret5 = latest / float(close.iloc[-6]) - 1 if len(close) >= 6 else latest / float(close.iloc[0]) - 1
    ret10 = latest / float(close.iloc[-11]) - 1 if len(close) >= 11 else latest / float(close.iloc[0]) - 1
    vol10 = float(ret.tail(10).std()) if len(ret) >= 2 else 0.0
    peak10 = float(close.tail(10).max())
    drawdown10 = latest / peak10 - 1 if peak10 else 0.0
    quality = "ok" if len(close) >= 10 else "estimated_short_window"
    return {"return_5d": ret5, "return_10d": ret10, "volatility_10d": vol10, "drawdown_10d": drawdown10, "rows": int(len(close)), "data_quality": quality}


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"# high_beta 持仓风险观察 {payload['generated_at']}",
        "",
        "本报告只做 high_beta 风险观察，不自动减仓、不自动卖出、不写入 paper_trades.csv、不修改 paper_positions.csv。",
        "",
        "## 组合级 high_beta 暴露",
        f"- high_beta 持仓数量：{summary['high_beta_position_count']}",
        f"- high_beta 持仓市值：{summary['high_beta_market_value']:.2f}",
        f"- high_beta 占总资产比例：{summary['high_beta_weight_of_equity']:.2%}",
        f"- high_beta 占持仓市值比例：{summary['high_beta_weight_of_holdings']:.2%}",
        f"- 金融地产组市值：{summary['finance_real_estate_market_value']:.2f}",
        f"- 金融地产组占总资产比例：{summary['finance_real_estate_weight_of_equity']:.2%}",
        f"- 金融地产组占持仓市值比例：{summary['finance_real_estate_weight_of_holdings']:.2%}",
        f"- high_beta_exposure_state：{summary['high_beta_exposure_state']}",
        f"- high_beta_exposure_reasons：{summary['high_beta_exposure_reasons']}",
        "- execution_allowed：false",
        "",
        "## 持仓级 high_beta 观察",
        "| symbol | name | state | group | mv | equity_weight | holdings_weight | pnl | rank | rank_change | rank_decay | ret5 | ret10 | vol10 | dd10 | action |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not payload["rows"]:
        lines.append("|  | 当前无 high_beta 持仓 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |")
    for row in payload["rows"]:
        lines.append(
            f"| {row['symbol']} | {row['name']} | {row['high_beta_risk_state']} / {row['high_beta_risk_state_cn']} | {row['group']} | "
            f"{row['market_value']:.2f} | {row['position_weight_of_equity']:.2%} | {row['position_weight_of_holdings']:.2%} | {_pct(row['unrealized_pnl_pct'])} | "
            f"{_fmt(row['rank'])} | {_fmt(row['rank_change'])} | {row['rank_decay_days']} | {_pct(row['recent_return_5d'])} | {_pct(row['recent_return_10d'])} | "
            f"{_pct(row['recent_volatility_10d'])} | {_pct(row['recent_drawdown_10d'])} | {row['recommended_review_action']} |"
        )
    target = next((row for row in payload["rows"] if row["symbol"] == "512880"), None)
    lines += ["", "## 512880 证券ETF 重点观察"]
    if target:
        lines += [
            f"- high_beta_risk_state：{target['high_beta_risk_state']} / {target['high_beta_risk_state_cn']}",
            f"- 当前市值：{target['market_value']:.2f}",
            f"- 占总资产：{target['position_weight_of_equity']:.2%}",
            f"- 占持仓市值：{target['position_weight_of_holdings']:.2%}",
            f"- 近 10 日波动率：{_pct(target['recent_volatility_10d'])}",
            f"- 近 10 日回撤：{_pct(target['recent_drawdown_10d'])}",
            f"- 原因：{target['high_beta_risk_reasons']}",
        ]
    else:
        lines.append("- 512880 当前不在 high_beta 持仓中。")
    lines += [
        "",
        "## 解释",
        "- high_beta 观察层用于监控证券/券商等高波动 ETF 对市场情绪的敏感性。",
        "- 它与 REVIEW / PROFIT_WATCH 的区别：本报告关注波动、回撤和组合集中度，不改变持仓复核或浮盈保护状态。",
        "- 是否需要自动减仓：否。当前只是 observation。",
        "- 后续重点观察：short_swing 是否转弱、rank 是否连续下降、金融地产组是否继续集中、10 日回撤是否扩大。",
        "",
        "## 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不修改 paper_trade_engine.py。",
        "- 不修改 paper_trades.csv / paper_positions.csv。",
    ]
    return "\n".join(lines)


def _is_high_beta(row: dict[str, Any]) -> bool:
    text = " ".join(str(row.get(key, "")) for key in ["symbol", "name", "etf_type", "type", "risk_profile", "group"])
    return "high_beta" in text or "证券" in text or "券商" in text


def _total_equity() -> float:
    path = REPORT_DIR / "paper_performance_summary.json"
    payload = _read_json(path)
    value = _float(payload.get("current_total_equity"))
    return value if value > 0 else float(PAPER_INITIAL_CASH)


def _map_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("symbol", "")).strip(): row for row in rows}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _price_path(symbol: str) -> Path | None:
    prefix = "sh" if str(symbol).startswith(("5", "6")) else "sz"
    path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
    if path.exists():
        return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*_{symbol}.csv"))
    return matches[0] if matches else None


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _fmt(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
