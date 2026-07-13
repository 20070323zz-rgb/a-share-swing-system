"""Profit protection preview for current paper positions.

Read-only preview layer. It does not take profit, reduce positions, append
trades, modify paper positions, connect to broker APIs, or read real accounts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, REPORT_DIR
from valuation import load_latest_position_valuation


CSV_FILE = REPORT_DIR / "profit_protection_preview.csv"
JSON_FILE = REPORT_DIR / "profit_protection_preview.json"
MD_FILE = REPORT_DIR / "profit_protection_preview.md"
POSITION_REVIEW_FILE = REPORT_DIR / "position_review_state.json"

PROFIT_WATCH_MIN_PCT = 0.03
PROFIT_REVIEW_MIN_PCT = 0.05
PROFIT_DRAWDOWN_REVIEW_PCT = 0.30
PROFIT_DRAWDOWN_LOCK_PCT = 0.50

STATE_CN = {
    "NO_PROFIT": "暂无浮盈保护需求",
    "PROFIT_WATCH": "浮盈观察",
    "PROFIT_PROTECTION_REVIEW": "浮盈保护复核",
    "PROFIT_LOCK_CANDIDATE": "浮盈锁定候选",
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_profit_protection_preview()
    df = pd.DataFrame(payload["rows"])
    df.to_csv(CSV_FILE, index=False)
    JSON_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_FILE.write_text(render_report(payload), encoding="utf-8")
    print(f"profit_protection rows: {len(df)}")
    print(f"written: {MD_FILE}")


def build_profit_protection_preview() -> dict[str, Any]:
    valuation = load_latest_position_valuation()
    positions = valuation["positions"]
    review_map = _position_review_map()
    rows = []
    for item in positions.to_dict(orient="records"):
        rows.append(_position_profit_preview(item, review_map.get(str(item.get("symbol", "")).strip(), {})))
    summary = _summary(rows, valuation.get("summary", {}))
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "preview_only": True,
        "execution_allowed": False,
        "state_labels": STATE_CN,
        "thresholds": {
            "profit_watch_min_pct": PROFIT_WATCH_MIN_PCT,
            "profit_review_min_pct": PROFIT_REVIEW_MIN_PCT,
            "profit_drawdown_review_pct": PROFIT_DRAWDOWN_REVIEW_PCT,
            "profit_drawdown_lock_pct": PROFIT_DRAWDOWN_LOCK_PCT,
        },
        "summary": summary,
        "rows": rows,
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


def _position_profit_preview(item: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    symbol = str(item.get("symbol", "")).strip()
    name = str(item.get("name") or symbol)
    quantity = _float(item.get("quantity"))
    entry_date = str(item.get("entry_date") or "")
    entry_cost = _float(item.get("cost")) or _float(item.get("total_cost"))
    latest_close = _float(item.get("latest_close")) or _float(item.get("current_price"))
    latest_date = str(item.get("as_of_date") or "")
    current_market_value = _float(item.get("market_value"))
    current_pnl = current_market_value - entry_cost
    current_pnl_pct = current_pnl / entry_cost if entry_cost else 0.0
    curve = _profit_curve(symbol, quantity, entry_cost, entry_date)
    data_quality = "ok"
    estimated_fields: list[str] = []
    if curve.empty:
        data_quality = "estimated_from_latest_valuation_only"
        estimated_fields.append("peak_unrealized_pnl")
        peak_pnl = current_pnl
        peak_pnl_pct = current_pnl_pct
        peak_date = latest_date
        daily_rows = 0
    else:
        peak_idx = curve["unrealized_pnl"].idxmax()
        peak = curve.loc[peak_idx]
        peak_pnl = float(peak["unrealized_pnl"])
        peak_pnl_pct = float(peak["unrealized_pnl_pct"])
        peak_date = str(peak["date"])
        daily_rows = int(len(curve))
        if not entry_date:
            estimated_fields.append("entry_date")
            data_quality = "estimated_entry_date"
    drawdown_amount = max(0.0, peak_pnl - current_pnl) if peak_pnl > 0 else 0.0
    drawdown_pct = drawdown_amount / peak_pnl if peak_pnl > 0 else 0.0
    flags = _flags(current_pnl_pct, drawdown_pct, review)
    state, level, action = _decide_state(current_pnl, flags)
    reasons = _reasons(flags, current_pnl, current_pnl_pct, peak_pnl, drawdown_pct, review)
    return {
        "symbol": symbol,
        "name": name,
        "quantity": quantity,
        "entry_date": entry_date,
        "entry_cost": round(entry_cost, 2),
        "latest_close": round(latest_close, 6),
        "latest_date": latest_date,
        "current_market_value": round(current_market_value, 2),
        "current_unrealized_pnl": round(current_pnl, 2),
        "current_unrealized_pnl_pct": current_pnl_pct,
        "peak_unrealized_pnl": round(peak_pnl, 2),
        "peak_unrealized_pnl_pct": peak_pnl_pct,
        "peak_date": peak_date,
        "drawdown_from_profit_peak": round(drawdown_amount, 2),
        "drawdown_from_profit_peak_pct": drawdown_pct,
        "profit_protection_state": state,
        "profit_protection_state_cn": STATE_CN.get(state, state),
        "profit_protection_level": level,
        "profit_protection_reasons": "；".join(reasons),
        "recommended_review_action": action,
        "execution_allowed": False,
        "data_quality": data_quality,
        "estimated_fields": "; ".join(estimated_fields),
        "daily_curve_rows": daily_rows,
        "mid_trend": review.get("mid_trend", "N/A"),
        "short_swing": review.get("short_swing", "N/A"),
        "rank_decay_days": review.get("rank_decay_days", 0),
        "review_state": review.get("review_state", ""),
        "high_beta_flag": review.get("high_beta_flag", False),
        "safety_note": "浮盈保护为研究观察指标，不会自动交易。",
    }


def _profit_curve(symbol: str, quantity: float, entry_cost: float, entry_date: str) -> pd.DataFrame:
    path = _price_path(symbol)
    if path is None or quantity <= 0 or entry_cost <= 0:
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, usecols=lambda col: col in {"date", "close"})
    except Exception:
        return pd.DataFrame()
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date")
    if entry_date:
        start = pd.to_datetime(entry_date, errors="coerce")
        if pd.notna(start):
            df = df[df["date"] >= start]
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    out["market_value"] = out["close"] * quantity
    out["unrealized_pnl"] = out["market_value"] - entry_cost
    out["unrealized_pnl_pct"] = out["unrealized_pnl"] / entry_cost if entry_cost else 0.0
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def _flags(current_pnl_pct: float, drawdown_pct: float, review: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    short = str(review.get("short_swing", "")).upper()
    mid = str(review.get("mid_trend", "")).upper()
    rank_decay = int(_float(review.get("rank_decay_days")))
    high_beta = _boolish(review.get("high_beta_flag"))
    if current_pnl_pct > 0:
        flags.append("has_unrealized_profit")
    if current_pnl_pct >= PROFIT_WATCH_MIN_PCT:
        flags.append("profit_over_watch_threshold")
    if current_pnl_pct >= PROFIT_REVIEW_MIN_PCT:
        flags.append("profit_over_review_threshold")
    if drawdown_pct >= PROFIT_DRAWDOWN_REVIEW_PCT:
        flags.append("profit_drawdown_over_30pct")
    if drawdown_pct >= PROFIT_DRAWDOWN_LOCK_PCT:
        flags.append("profit_drawdown_over_50pct")
    if short == "WATCH":
        flags.append("short_swing_watch")
    if short == "SELL":
        flags.append("short_swing_sell")
    if rank_decay >= 2:
        flags.append("rank_decline_2d")
    if high_beta:
        flags.append("high_beta_watch")
    if mid in {"WATCH", "SELL"}:
        flags.append("mid_trend_weak")
    return flags


def _decide_state(current_pnl: float, flags: list[str]) -> tuple[str, int, str]:
    if current_pnl <= 0:
        return "NO_PROFIT", 0, "当前无浮盈，不需要浮盈保护；继续按 REVIEW/止损规则观察。"
    lock_hits = len(
        [
            flag
            for flag in flags
            if flag
            in {
                "profit_over_review_threshold",
                "profit_drawdown_over_50pct",
                "short_swing_watch",
                "short_swing_sell",
                "rank_decline_2d",
                "high_beta_watch",
                "mid_trend_weak",
            }
        ]
    )
    if "mid_trend_weak" in flags and "profit_drawdown_over_30pct" in flags:
        return "PROFIT_LOCK_CANDIDATE", 3, "浮盈锁定候选观察；需要人工复核，不自动止盈。"
    if lock_hits >= 3:
        return "PROFIT_LOCK_CANDIDATE", 3, "浮盈锁定候选观察；条件叠加但不自动交易。"
    review_hits = len(
        [
            flag
            for flag in flags
            if flag
            in {
                "profit_over_review_threshold",
                "profit_drawdown_over_30pct",
                "short_swing_watch",
                "rank_decline_2d",
                "high_beta_watch",
            }
        ]
    )
    if review_hits >= 2:
        return "PROFIT_PROTECTION_REVIEW", 2, "浮盈保护复核；观察是否继续回吐，不自动止盈。"
    return "PROFIT_WATCH", 1, "浮盈观察；跟踪峰值回撤，不自动止盈。"


def _reasons(
    flags: list[str],
    current_pnl: float,
    current_pnl_pct: float,
    peak_pnl: float,
    drawdown_pct: float,
    review: dict[str, Any],
) -> list[str]:
    if current_pnl <= 0:
        return ["当前浮盈小于等于 0，浮盈保护不启用。"]
    reasons = [
        f"当前浮盈 {current_pnl:.2f}，浮盈率 {current_pnl_pct:.2%}。",
        f"持仓以来最高浮盈 {peak_pnl:.2f}，从峰值回撤 {drawdown_pct:.2%}。",
    ]
    if "profit_over_review_threshold" in flags:
        reasons.append("当前浮盈率超过 5% 复核阈值。")
    elif "profit_over_watch_threshold" in flags:
        reasons.append("当前浮盈率超过 3% 观察阈值。")
    if "profit_drawdown_over_30pct" in flags:
        reasons.append("浮盈从峰值回撤超过 30%。")
    if "profit_drawdown_over_50pct" in flags:
        reasons.append("浮盈从峰值回撤超过 50%。")
    if "short_swing_watch" in flags:
        reasons.append("short_swing 已转 WATCH。")
    if "rank_decline_2d" in flags:
        reasons.append("rank_score 连续下降。")
    if "high_beta_watch" in flags:
        reasons.append("高 beta/主题属性，需要更敏感观察。")
    if review.get("review_state"):
        reasons.append(f"当前 REVIEW 分层：{review.get('review_state')}。")
    return reasons


def _summary(rows: list[dict[str, Any]], valuation_summary: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["profit_protection_state"]
        counts[key] = counts.get(key, 0) + 1
    profitable = [row for row in rows if _float(row.get("current_unrealized_pnl")) > 0]
    return {
        "position_count": len(rows),
        "state_counts": counts,
        "profitable_position_count": len(profitable),
        "profit_watch_count": counts.get("PROFIT_WATCH", 0),
        "profit_protection_review_count": counts.get("PROFIT_PROTECTION_REVIEW", 0),
        "profit_lock_candidate_count": counts.get("PROFIT_LOCK_CANDIDATE", 0),
        "total_current_unrealized_pnl": round(sum(_float(row.get("current_unrealized_pnl")) for row in rows), 2),
        "total_peak_unrealized_pnl": round(sum(max(0.0, _float(row.get("peak_unrealized_pnl"))) for row in rows), 2),
        "total_drawdown_from_profit_peak": round(sum(_float(row.get("drawdown_from_profit_peak")) for row in rows), 2),
        "valuation_as_of_date": valuation_summary.get("as_of_date", ""),
        "execution_allowed": False,
        "safety_note": "浮盈保护为研究观察指标，不会自动交易。",
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    row_map = {row["symbol"]: row for row in payload["rows"]}
    lines = [
        f"# 持仓浮盈保护 Preview {payload['generated_at']}",
        "",
        "本报告只做模拟仓浮盈保护观察，不自动止盈、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。",
        "",
        "## 摘要",
        f"- 当前持仓数：{summary['position_count']}",
        f"- 有浮盈持仓数：{summary['profitable_position_count']}",
        f"- PROFIT_WATCH：{summary['profit_watch_count']}",
        f"- PROFIT_PROTECTION_REVIEW：{summary['profit_protection_review_count']}",
        f"- PROFIT_LOCK_CANDIDATE：{summary['profit_lock_candidate_count']}",
        f"- 当前总未实现盈亏：{summary['total_current_unrealized_pnl']:.2f}",
        f"- 持仓以来总峰值浮盈：{summary['total_peak_unrealized_pnl']:.2f}",
        f"- 从浮盈峰值回撤合计：{summary['total_drawdown_from_profit_peak']:.2f}",
        f"- 估值日期：{summary.get('valuation_as_of_date') or 'N/A'}",
        "- execution_allowed：false",
        "",
        "## 状态定义",
        "- NO_PROFIT = 暂无浮盈保护需求",
        "- PROFIT_WATCH = 浮盈观察",
        "- PROFIT_PROTECTION_REVIEW = 浮盈保护复核",
        "- PROFIT_LOCK_CANDIDATE = 浮盈锁定候选（不是卖出信号）",
        "",
        "## 持仓明细",
        "| symbol | name | state | entry_date | latest_date | current_pnl | current_pnl_pct | peak_pnl | peak_pnl_pct | peak_date | drawdown_from_peak | drawdown_pct | action |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['symbol']} | {row['name']} | {row['profit_protection_state']} / {row['profit_protection_state_cn']} | "
            f"{row['entry_date']} | {row['latest_date']} | {row['current_unrealized_pnl']:.2f} | {_pct(row['current_unrealized_pnl_pct'])} | "
            f"{row['peak_unrealized_pnl']:.2f} | {_pct(row['peak_unrealized_pnl_pct'])} | {row['peak_date']} | "
            f"{row['drawdown_from_profit_peak']:.2f} | {_pct(row['drawdown_from_profit_peak_pct'])} | {row['recommended_review_action']} |"
        )
    tech = row_map.get("515000", {})
    lines += [
        "",
        "## 515000 科技ETF 重点观察",
    ]
    if tech:
        lines += [
            f"- profit_protection_state：{tech['profit_protection_state']} / {tech['profit_protection_state_cn']}",
            f"- 当前浮盈率：{_pct(tech['current_unrealized_pnl_pct'])}",
            f"- 最高浮盈日期：{tech['peak_date']}",
            f"- 从最高浮盈回撤：{tech['drawdown_from_profit_peak']:.2f}，回撤比例 {_pct(tech['drawdown_from_profit_peak_pct'])}",
            f"- 复核说明：{tech['profit_protection_reasons']}",
        ]
    else:
        lines.append("- 515000 当前不在持仓中。")
    lines += [
        "",
        "## 解释",
        "- 当前有浮盈的持仓会进入 PROFIT_WATCH 或更高层级。",
        "- PROFIT_PROTECTION_REVIEW 表示需要关注浮盈是否继续回吐。",
        "- PROFIT_LOCK_CANDIDATE 不是卖出信号，只是提示需要人工复核是否保护浮盈。",
        "- 本模块与 REVIEW / REDUCE_CANDIDATE 的区别：它只观察盈利回吐，不改变原有持仓复核状态。",
        "- 后续至少需要多轮模拟交易样本和不同市场状态验证，才可考虑规则化。",
        "",
        "## 安全边界",
        "- 当前是否建议自动止盈：否。",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不修改 paper_trade_engine.py。",
        "- 不修改 paper_trades.csv / paper_positions.csv。",
    ]
    return "\n".join(lines)


def _position_review_map() -> dict[str, dict[str, Any]]:
    if not POSITION_REVIEW_FILE.exists():
        return {}
    try:
        payload = json.loads(POSITION_REVIEW_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(row.get("symbol", "")).strip(): row for row in payload.get("rows", [])}


def _price_path(symbol: str) -> Path | None:
    prefix = "sh" if str(symbol).startswith(("5", "6")) else "sz"
    path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
    if path.exists():
        return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*_{symbol}.csv"))
    return matches[0] if matches else None


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _pct(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
