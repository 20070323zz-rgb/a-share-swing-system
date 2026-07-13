"""Layered review state for current paper positions.

This is a review-only layer. It does not modify paper positions/trades, does
not connect to broker APIs, and does not trigger automatic reduce/sell actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR
from valuation import load_latest_position_valuation


SELL_REVIEW_CSV = REPORT_DIR / "sell_signal_review.csv"
POSITION_REVIEW_CSV = REPORT_DIR / "position_review_state.csv"
POSITION_REVIEW_JSON = REPORT_DIR / "position_review_state.json"
POSITION_REVIEW_MD = REPORT_DIR / "position_review_state.md"
AUDIT_MD = REPORT_DIR / "review_state_audit.md"
AUDIT_JSON = REPORT_DIR / "review_state_audit.json"

STATE_CN = {
    "HOLD": "继续持有",
    "REVIEW_1": "轻度观察",
    "REVIEW_2": "重点复核",
    "REDUCE_CANDIDATE": "减仓候选",
    "REDUCE": "减仓信号",
    "SELL": "卖出信号",
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    review = build_position_review_state()
    rows = review["rows"]
    df = pd.DataFrame(rows)
    df.to_csv(POSITION_REVIEW_CSV, index=False)
    POSITION_REVIEW_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    POSITION_REVIEW_MD.write_text(render_position_review_md(review), encoding="utf-8")
    audit = build_audit(review)
    AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_MD.write_text(render_audit_md(audit), encoding="utf-8")
    print(f"position_review_state rows: {len(rows)}")
    print(f"written: {POSITION_REVIEW_MD}")
    print(f"written: {AUDIT_MD}")


def build_position_review_state() -> dict[str, Any]:
    valuation = load_latest_position_valuation()
    positions = valuation["positions"]
    sell_review = _read_csv(SELL_REVIEW_CSV)
    sell_map = {str(row.get("symbol", "")).strip(): row for row in sell_review.to_dict(orient="records")}
    rows: list[dict[str, Any]] = []
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", "")).strip()
        review_row = sell_map.get(symbol, {})
        row = _review_position(item, review_row)
        rows.append(row)
    summary = _summary(rows, valuation.get("summary", {}))
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_only": True,
        "execution_allowed": False,
        "state_labels": STATE_CN,
        "summary": summary,
        "rows": rows,
        "safety": _safety(),
    }


def _review_position(item: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    symbol = str(item.get("symbol", "")).strip()
    name = str(item.get("name") or review.get("name") or symbol)
    mid = str(review.get("mid_trend_signal") or _parse_reason_signal(item.get("reason"), "mid_trend") or "N/A").upper()
    short = str(review.get("short_swing_signal") or _parse_reason_signal(item.get("reason"), "short_swing") or "N/A").upper()
    entry_mid = str(review.get("entry_mid_trend_signal") or _parse_reason_signal(item.get("reason"), "mid_trend") or "N/A").upper()
    entry_short = str(review.get("entry_short_swing_signal") or _parse_reason_signal(item.get("reason"), "short_swing") or "N/A").upper()
    etf_type = str(review.get("etf_type") or item.get("etf_type") or "unknown")
    group = str(review.get("group") or item.get("group") or "")
    current_action = str(review.get("sell_review_status") or item.get("sell_review_status") or "HOLD").upper()
    rank = _float(review.get("rank_score"), fallback=_parse_reason_score(item.get("reason")))
    rank_change = _float(review.get("rank_score_change"), fallback=float("nan"))
    rank_decay_days = int(_float(review.get("rank_decline_days"), 0))
    unrealized_pnl = _float(item.get("unrealized_pnl"))
    unrealized_pnl_pct = _float(item.get("unrealized_pnl_pct"), _float(item.get("unrealized_return")))
    high_beta = etf_type in {"high_beta", "theme", "hot_theme"} or any(key in name for key in ["证券", "券商", "AI", "半导体", "芯片"])
    flags = _flags(review, item, mid, short, entry_mid, entry_short, unrealized_pnl_pct, rank_change, rank_decay_days, high_beta)
    review_state, review_level, action = _decide_layer(flags, mid, short, current_action)
    reasons = _reason_text(flags, review, item)
    if review_state == "HOLD" and unrealized_pnl_pct > 0.08:
        reasons.append("浮盈较高，进入浮盈保护观察；不自动止盈。")
        action = "继续持有；跟踪浮盈回撤和 rank_score 是否连续下降。"
    if review_state == "HOLD" and high_beta:
        reasons.append("高 beta/情绪型 ETF，继续持有但保持风险观察。")
    return {
        "symbol": symbol,
        "name": name,
        "current_action": current_action,
        "review_state": review_state,
        "review_state_cn": STATE_CN.get(review_state, review_state),
        "review_level": review_level,
        "is_reduce_candidate": review_state == "REDUCE_CANDIDATE",
        "mid_trend": mid,
        "short_swing": short,
        "entry_mid_trend": entry_mid,
        "entry_short_swing": entry_short,
        "unrealized_pnl": round(unrealized_pnl, 2),
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "rank": None if pd.isna(rank) else round(rank, 4),
        "rank_change": None if pd.isna(rank_change) else round(rank_change, 4),
        "rank_decay_days": rank_decay_days,
        "group": group,
        "type": etf_type,
        "high_beta_flag": bool(high_beta),
        "holding_days": int(_float(item.get("holding_days"))),
        "latest_close": _float(item.get("latest_close"), _float(item.get("current_price"))),
        "market_value": _float(item.get("market_value")),
        "as_of_date": item.get("as_of_date", ""),
        "price_status": item.get("price_status", ""),
        "data_health_status": review.get("data_health_status") or item.get("data_health_status", "N/A"),
        "sell_review_status": current_action,
        "condition_flags": "; ".join(flags),
        "review_reasons": "；".join(reasons) if reasons else "未触发额外分层条件。",
        "recommended_review_action": action,
        "execution_allowed": False,
        "safety_note": "观察状态，不会自动交易。",
    }


def _flags(
    review: dict[str, Any],
    item: dict[str, Any],
    mid: str,
    short: str,
    entry_mid: str,
    entry_short: str,
    unrealized_pnl_pct: float,
    rank_change: float,
    rank_decay_days: int,
    high_beta: bool,
) -> list[str]:
    flags: list[str] = []
    raw_flags = str(review.get("condition_flags") or "")
    for flag in [part.strip() for part in raw_flags.split(";") if part.strip()]:
        flags.append(flag)
    if entry_short == "BUY" and short == "WATCH":
        flags.append("short_swing_buy_to_watch")
    if entry_short == "BUY" and short == "SELL":
        flags.append("short_swing_buy_to_sell")
    if mid in {"WATCH", "SELL"} and entry_mid == "BUY":
        flags.append("mid_trend_buy_to_weak")
    if pd.notna(rank_change) and rank_change < 0:
        flags.append("rank_single_day_decline")
    if rank_decay_days >= 2:
        flags.append("rank_decline_2d")
    if rank_decay_days >= 3:
        flags.append("rank_decline_3d")
    if unrealized_pnl_pct <= -0.035:
        flags.append("floating_loss_over_3_5pct")
    if unrealized_pnl_pct <= -0.05:
        flags.append("floating_loss_over_5pct")
    if high_beta and (short in {"WATCH", "SELL"} or pd.notna(rank_change) and rank_change < 0):
        flags.append("high_beta_watch")
    if str(review.get("type_review_severity", "")).lower() == "elevated":
        flags.append("type_review_elevated")
    if "stop_loss_break" in raw_flags or str(review.get("sell_review_status", "")).upper() == "SELL":
        flags.append("hard_sell_candidate")
    if str(item.get("price_status", "")) not in {"", "ok"}:
        flags.append("price_warning")
    return list(dict.fromkeys(flags))


def _decide_layer(flags: list[str], mid: str, short: str, current_action: str) -> tuple[str, int, str]:
    if "hard_sell_candidate" in flags or mid == "SELL":
        return "SELL", 5, "卖出信号候选；仍只生成复核，不自动卖出。"
    if mid == "WATCH" or "mid_trend_buy_to_weak" in flags:
        return "REDUCE_CANDIDATE", 3, "中期趋势转弱，进入减仓候选观察；不自动减仓。"

    reduce_conditions = {
        "short_swing_buy_to_watch",
        "rank_decline_2d",
        "rank_decline_3d",
        "floating_loss_over_3_5pct",
        "floating_loss_over_5pct",
        "type_review_elevated",
        "high_beta_watch",
    }
    review2_conditions = {
        "short_swing_buy_to_watch",
        "rank_decline_2d",
        "floating_loss_over_3_5pct",
        "type_review_elevated",
        "high_beta_watch",
    }
    reduce_hits = len([flag for flag in flags if flag in reduce_conditions])
    review2_hits = len([flag for flag in flags if flag in review2_conditions])
    if reduce_hits >= 3 or "rank_decline_3d" in flags:
        return "REDUCE_CANDIDATE", 3, "减仓候选观察：条件叠加，但不触发自动交易。"
    if review2_hits >= 2 or current_action == "REVIEW":
        return "REVIEW_2", 2, "重点复核：禁止加仓，次日继续观察。"
    if any(flag in flags for flag in ["short_swing_buy_to_watch", "rank_single_day_decline", "floating_loss_over_3_5pct", "high_beta_watch"]):
        return "REVIEW_1", 1, "轻度观察：继续持有，等待下一次复核。"
    return "HOLD", 0, "继续持有；未触发分层复核条件。"


def _reason_text(flags: list[str], review: dict[str, Any], item: dict[str, Any]) -> list[str]:
    mapping = {
        "short_swing_buy_to_watch": "short_swing 从 BUY 转 WATCH，短周期动能转弱。",
        "short_swing_buy_to_sell": "short_swing 从 BUY 转 SELL，需人工重点复核。",
        "mid_trend_buy_to_weak": "mid_trend 从 BUY 转弱，属于强复核条件。",
        "rank_single_day_decline": "rank_score 单日下降。",
        "rank_decline_2d": "rank_score 连续 2 日下降。",
        "rank_decline_3d": "rank_score 连续 3 日下降。",
        "floating_loss_over_3_5pct": "浮亏超过 3.5% 观察阈值。",
        "floating_loss_over_5pct": "浮亏超过 5% 重点复核阈值。",
        "type_review_elevated": "类型化复核 severity=elevated。",
        "high_beta_watch": "高 beta/主题属性，需要更敏感观察。",
        "price_warning": "估值价格存在警告，需确认数据质量。",
        "hard_sell_candidate": "触发硬卖出候选条件，但仍不自动交易。",
    }
    reasons = [mapping[flag] for flag in flags if flag in mapping]
    note = str(review.get("action_note") or "")
    if note and note not in reasons:
        reasons.append(note)
    if str(item.get("price_status", "")) == "ok":
        reasons.append("估值价格状态正常。")
    return list(dict.fromkeys(reasons))


def _summary(rows: list[dict[str, Any]], valuation_summary: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("review_state", "UNKNOWN"))
        counts[key] = counts.get(key, 0) + 1
    return {
        "position_count": len(rows),
        "state_counts": counts,
        "reduce_candidate_count": counts.get("REDUCE_CANDIDATE", 0),
        "review_2_count": counts.get("REVIEW_2", 0),
        "high_beta_watch_count": sum(1 for row in rows if row.get("high_beta_flag")),
        "profit_protection_watch_count": sum(1 for row in rows if _float(row.get("unrealized_pnl_pct")) > 0.08),
        "valuation_as_of_date": valuation_summary.get("as_of_date", ""),
        "price_warning_count": valuation_summary.get("price_warning_count", 0),
        "execution_allowed": False,
        "safety_note": "以下为模拟仓观察状态，不会自动交易。",
    }


def build_audit(review: dict[str, Any]) -> dict[str, Any]:
    rows = review.get("rows", [])
    by_symbol = {row["symbol"]: row for row in rows}
    source_files = {
        "sell_review_logic": "src/sell_signal_review.py",
        "position_review_layer": "src/position_review_state.py",
        "dashboard_builder": "dashboard/build_dashboard.py",
        "app_portfolio": "app/frontend/src/pages/Portfolio.jsx",
        "app_home": "app/frontend/src/pages/Home.jsx",
        "app_reader": "app/backend/readers.py",
    }
    return {
        "generated_at": review.get("generated_at"),
        "review_logic_source": "src/sell_signal_review.py produces HOLD/WATCH/REVIEW/REDUCE/SELL review-only status; src/position_review_state.py adds layered REVIEW_1/REVIEW_2/REDUCE_CANDIDATE observation state.",
        "current_review_shortcoming": "旧 REVIEW 只有单一标黄状态，无法区分轻度观察、重点复核和减仓候选观察。",
        "auto_sell_triggered_by_review": False,
        "paper_trade_engine_modified": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "source_files": source_files,
        "symbols": by_symbol,
        "state_counts": review.get("summary", {}).get("state_counts", {}),
        "recommended_layering": STATE_CN,
        "safety": _safety(),
    }


def render_position_review_md(review: dict[str, Any]) -> str:
    summary = review["summary"]
    lines = [
        f"# 持仓 REVIEW 分层报告 {review['generated_at']}",
        "",
        "本报告只做模拟仓观察分层，不自动交易，不写入 paper_trades.csv，不修改 paper_positions.csv。",
        "",
        "## 摘要",
        f"- 持仓数量：{summary['position_count']}",
        f"- 状态分布：{summary['state_counts']}",
        f"- REDUCE_CANDIDATE 数量：{summary['reduce_candidate_count']}",
        f"- REVIEW_2 数量：{summary['review_2_count']}",
        f"- high_beta 观察数量：{summary['high_beta_watch_count']}",
        f"- 浮盈保护观察数量：{summary['profit_protection_watch_count']}",
        f"- 估值日期：{summary.get('valuation_as_of_date') or 'N/A'}",
        "- execution_allowed：false",
        "- 安全说明：以下为模拟仓观察状态，不会自动交易。",
        "",
        "## 状态定义",
        "- HOLD = 继续持有",
        "- REVIEW_1 = 轻度观察",
        "- REVIEW_2 = 重点复核",
        "- REDUCE_CANDIDATE = 减仓候选（观察状态，不是交易指令）",
        "- REDUCE = 减仓信号（本轮不接执行层）",
        "- SELL = 卖出信号（本轮不接执行层）",
        "",
        "## 持仓复核明细",
        "| symbol | name | current_action | review_state | mid | short | PnL | rank | rank_change | rank_decay_days | group | type | high_beta | execution_allowed | reasons | action |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in review["rows"]:
        lines.append(
            f"| {row['symbol']} | {row['name']} | {row['current_action']} | {row['review_state']} / {row['review_state_cn']} | "
            f"{row['mid_trend']} | {row['short_swing']} | {_pct(row['unrealized_pnl_pct'])} | {_fmt(row['rank'])} | {_fmt(row['rank_change'])} | "
            f"{row['rank_decay_days']} | {row['group']} | {row['type']} | {row['high_beta_flag']} | {str(row['execution_allowed']).lower()} | "
            f"{str(row['review_reasons']).replace('|', '/')} | {str(row['recommended_review_action']).replace('|', '/')} |"
        )
    lines += [
        "",
        "## 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不修改 paper_trade_engine.py。",
        "- 不修改正式买入/卖出规则。",
        "- 不修改 paper_trades.csv / paper_positions.csv。",
        "- REDUCE_CANDIDATE 只是观察状态。",
    ]
    return "\n".join(lines)


def render_audit_md(audit: dict[str, Any]) -> str:
    rows = audit.get("symbols", {})
    lines = [
        f"# REVIEW 状态审计报告 {audit['generated_at']}",
        "",
        "## 当前 REVIEW 逻辑来源",
        f"- {audit['review_logic_source']}",
        "- 当前 HOLD / REVIEW / REDUCE / SELL 来自 sell_signal_review.csv。",
        "- 本轮新增 position_review_state 只做展示和复核分层，不接执行层。",
        "",
        "## 当前 512800 进入 REVIEW 的具体原因",
    ]
    bank = rows.get("512800", {})
    if bank:
        lines += [
            f"- review_state：{bank.get('review_state')} / {bank.get('review_state_cn')}",
            f"- short_swing：{bank.get('short_swing')}",
            f"- mid_trend：{bank.get('mid_trend')}",
            f"- rank_decay_days：{bank.get('rank_decay_days')}",
            f"- unrealized_pnl_pct：{_pct(bank.get('unrealized_pnl_pct'))}",
            f"- reasons：{bank.get('review_reasons')}",
        ]
    else:
        lines.append("- 512800 当前不在持仓中。")
    lines += [
        "",
        "## 是否会自动卖出",
        "- 否。",
        "- REVIEW_1 / REVIEW_2 / REDUCE_CANDIDATE 都是观察状态，不触发 paper_trade_engine。",
        "",
        "## 当前 REVIEW 的不足",
        f"- {audit['current_review_shortcoming']}",
        "",
        "## 推荐分层方案",
    ]
    for key, label in audit.get("recommended_layering", {}).items():
        lines.append(f"- {key} = {label}")
    lines += [
        "",
        "## 安全边界",
        "- 未修改 paper_trade_engine.py。",
        "- 未修改 paper_trades.csv。",
        "- 未修改 paper_positions.csv。",
        "- 未接券商 API，未真实下单。",
    ]
    return "\n".join(lines)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def _parse_reason_signal(reason: object, key: str) -> str:
    import re

    match = re.search(rf"{key}=([A-Z_]+)", str(reason or ""))
    return match.group(1) if match else ""


def _parse_reason_score(reason: object) -> float:
    import re

    match = re.search(r"rank_score=([0-9.]+)", str(reason or ""))
    return float(match.group(1)) if match else float("nan")


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


def _safety() -> dict[str, bool]:
    return {
        "broker_api": False,
        "real_order": False,
        "real_account": False,
        "paper_trade_engine_modified": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "execution_allowed": False,
    }


if __name__ == "__main__":
    main()
