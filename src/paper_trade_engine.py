"""Rule-validation paper trade engine.

This module writes only local paper trading CSV files when --execute is used.
It never connects to broker APIs, never places real orders, and never reads
real accounts, cash, holdings, passwords, or tokens.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import pandas as pd

from config import (
    BROKER_API_ENABLED,
    DATA_DIR,
    PAPER_AUTO_EXECUTE,
    PAPER_COOLDOWN_DAYS_AFTER_SELL,
    PAPER_DEFAULT_MARKET_STATE,
    PAPER_EXECUTION_PRICE_TYPE,
    PAPER_INITIAL_CASH,
    PAPER_LOT_SIZE,
    PAPER_MAX_HOLDINGS,
    PAPER_MAX_SINGLE_POSITION_PCT,
    PAPER_MODE,
    PAPER_POSITIONS_FILE,
    PAPER_TARGET_POSITION_NEUTRAL,
    PAPER_TARGET_POSITION_STRONG,
    PAPER_TARGET_POSITION_WEAK,
    PAPER_TRADES_FILE,
    REAL_TRADE_ENABLED,
    REPORT_DIR,
    WATCHLIST_FILE,
)


PLAN_MD_FILE = REPORT_DIR / "paper_trade_plan.md"
PLAN_CSV_FILE = REPORT_DIR / "paper_trade_plan.csv"
ENGINE_REPORT_FILE = REPORT_DIR / "paper_trade_engine_report.md"
DESIGN_REPORT_FILE = REPORT_DIR / "paper_trade_engine_design_report.md"
ENGINE_STATE_FILE = DATA_DIR / "paper_trade_engine_state.json"
BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
SELL_REVIEW_FILE = REPORT_DIR / "sell_signal_review.csv"
DATA_HEALTH_FILE = REPORT_DIR / "latest_data_health.md"
CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
EXPANSION_CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"

TRADE_COLUMNS = [
    "date",
    "trade_date",
    "symbol",
    "name",
    "action",
    "strategy_source",
    "position_type",
    "price",
    "quantity",
    "amount",
    "realized_pnl",
    "fee",
    "execution_price_type",
    "order_type",
    "source",
    "reason",
    "simulated_cash",
    "position_value",
    "total_equity",
    "is_simulated",
]

POSITION_COLUMNS = [
    "symbol",
    "name",
    "strategy_source",
    "position_type",
    "entry_date",
    "entry_price",
    "quantity",
    "cost",
    "stop_loss",
    "reason",
    "current_price",
    "market_value",
    "unrealized_pnl",
    "unrealized_return",
    "unrealized_pnl_pct",
    "holding_days",
    "risk_alert",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="规则验证版模拟盘自动买卖引擎")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="只生成计划，不写模拟交易和持仓。")
    mode.add_argument("--execute", action="store_true", help="按规则写入本地模拟盘。")
    mode.add_argument("--status", action="store_true", help="显示今日执行状态。")
    parser.add_argument("--force", action="store_true", help="允许重算计划；仍会防止重复写同日同 symbol/action/source 交易。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.status:
        print(json.dumps(build_status(), ensure_ascii=False, indent=2))
        return
    dry_run = not args.execute
    result = run_engine(dry_run=dry_run, force=args.force)
    print(f"paper_trade_engine status: {result['status']}")
    print(f"dry_run: {result['dry_run']}, buy_count: {result['buy_count']}, sell_count: {result['sell_count']}")
    print(f"plan: {PLAN_MD_FILE}")


def run_engine(dry_run: bool, force: bool = False) -> dict:
    _ensure_files()
    run_date = _latest_data_date()
    positions = _read_csv(PAPER_POSITIONS_FILE, POSITION_COLUMNS)
    trades = _read_csv(PAPER_TRADES_FILE, TRADE_COLUMNS)
    state = _read_state()
    day_state = state.get(run_date, {})
    duplicate_execute = bool(day_state.get("executed")) and not dry_run and not force

    portfolio_before = _portfolio_summary(positions, trades)
    plan_rows: list[dict] = []
    executed_rows: list[dict] = []
    skipped_rows: list[dict] = []
    positions_after = positions.copy()
    trades_after = trades.copy()
    cash = portfolio_before["cash"]

    if duplicate_execute:
        skipped_rows.append(_plan_row(run_date, "", "", "ENGINE", "skipped_duplicate", 0, 0, "engine already executed today", "paper_trade_engine"))
        existing_plan = _read_csv(PLAN_CSV_FILE).to_dict(orient="records")
        skipped_rows.extend(existing_plan)
        status = "skipped_duplicate"
    else:
        sell_rows, positions_after, trades_after, cash = _process_sells(run_date, positions_after, trades_after, cash, dry_run)
        plan_rows.extend(sell_rows)
        executed_rows.extend([row for row in sell_rows if row["plan_status"] == "executed"])
        skipped_rows.extend([row for row in sell_rows if row["plan_status"].startswith("skipped")])

        buy_rows, positions_after, trades_after, cash = _process_buys(run_date, positions_after, trades_after, cash, dry_run)
        plan_rows.extend(buy_rows)
        executed_rows.extend([row for row in buy_rows if row["plan_status"] == "executed"])
        skipped_rows.extend([row for row in buy_rows if row["plan_status"].startswith("skipped")])
        status = "dry_run" if dry_run else "executed"

    if not dry_run and not duplicate_execute:
        positions_after = _revalue_positions(positions_after, run_date)
        positions_after.to_csv(PAPER_POSITIONS_FILE, index=False)
        trades_after.to_csv(PAPER_TRADES_FILE, index=False)

    portfolio_after = _portfolio_summary(positions_after, trades_after)
    buy_count = sum(1 for row in executed_rows if row["action"] == "BUY")
    sell_count = sum(1 for row in executed_rows if row["action"] == "SELL")
    state_payload = {
        "date": run_date,
        "mode": PAPER_MODE,
        "auto_execute": PAPER_AUTO_EXECUTE,
        "real_trade_enabled": REAL_TRADE_ENABLED,
        "broker_api_enabled": BROKER_API_ENABLED,
        "status": status,
        "executed": bool(day_state.get("executed")) or (not dry_run and not duplicate_execute),
        "dry_run": dry_run,
        "force": force,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "skipped_duplicate": duplicate_execute,
        "skip_reason": "engine already executed today" if duplicate_execute else "",
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cash": portfolio_after["cash"],
        "position_count": portfolio_after["position_count"],
        "position_ratio": portfolio_after["position_ratio"],
    }
    state[run_date] = state_payload
    _write_state(state)
    _write_outputs(plan_rows + skipped_rows if duplicate_execute else plan_rows, state_payload, portfolio_before, portfolio_after)
    return state_payload


def _process_sells(run_date: str, positions: pd.DataFrame, trades: pd.DataFrame, cash: float, dry_run: bool) -> tuple[list[dict], pd.DataFrame, pd.DataFrame, float]:
    sell_review = _read_csv(SELL_REVIEW_FILE)
    review_map = sell_review.set_index("symbol").to_dict(orient="index") if not sell_review.empty and "symbol" in sell_review.columns else {}
    rows: list[dict] = []
    if positions.empty:
        return rows, positions, trades, cash
    keep_positions = positions.copy()
    for pos in positions.to_dict(orient="records"):
        symbol = str(pos.get("symbol", "")).strip()
        name = str(pos.get("name", symbol))
        review = review_map.get(symbol, {})
        close = _latest_close(symbol) or _float(pos.get("current_price"), _float(pos.get("entry_price")))
        quantity = int(_float(pos.get("quantity")))
        amount = round(close * quantity, 2)
        reason = _sell_reason(pos, review, close)
        if not reason:
            rows.append(_plan_row(run_date, symbol, name, "SELL", "skipped_no_sell_signal", close, quantity, "sell rules not triggered", "paper_trade_engine"))
            continue
        if _has_trade(trades, run_date, symbol, "SELL"):
            rows.append(_plan_row(run_date, symbol, name, "SELL", "skipped_duplicate_trade", close, quantity, "same-day SELL already exists", "paper_trade_engine"))
            continue
        trade_row = _trade_row(run_date, symbol, name, "SELL", close, quantity, amount, reason, cash + amount, trades, keep_positions)
        avg_cost = _float(pos.get("cost")) / quantity if quantity else close
        trade_row["realized_pnl"] = round((close - avg_cost) * quantity, 2)
        rows.append(_plan_row(run_date, symbol, name, "SELL", "planned" if dry_run else "executed", close, quantity, reason, "paper_trade_engine", amount))
        if not dry_run:
            trades = pd.concat([trades, pd.DataFrame([trade_row])], ignore_index=True)
            keep_positions = keep_positions[keep_positions["symbol"].astype(str) != symbol].copy()
            cash = round(cash + amount, 2)
    return rows, keep_positions, trades, cash


def _process_buys(run_date: str, positions: pd.DataFrame, trades: pd.DataFrame, cash: float, dry_run: bool) -> tuple[list[dict], pd.DataFrame, pd.DataFrame, float]:
    ranking = _read_buy_ranking()
    health = _read_health()
    classification = _read_csv(CLASSIFICATION_FILE)
    watchlist = _read_csv(WATCHLIST_FILE)
    existing = set(positions["symbol"].astype(str)) if not positions.empty else set()
    target_pct = _target_position_pct()
    current_value = _positions_value(positions)
    total_equity = cash + current_value
    target_value = total_equity * target_pct
    available_position_room = max(0.0, target_value - current_value)
    slots = max(0, PAPER_MAX_HOLDINGS - len(existing))
    rank_weights = {1: 0.50, 2: 0.30, 3: 0.20}
    rows: list[dict] = []
    for candidate in ranking[:3]:
        symbol = str(candidate.get("symbol", "")).strip()
        name = str(candidate.get("name", symbol))
        close = _latest_close(symbol)
        health_status = health.get(symbol, {}).get("status", "正常")
        can_buy, reason = _can_buy(candidate, positions, trades, watchlist, classification, health, run_date, slots)
        base_amount = total_equity * target_pct * rank_weights.get(int(candidate.get("rank") or 0), 0.0)
        amount = min(base_amount, total_equity * PAPER_MAX_SINGLE_POSITION_PCT, available_position_room, cash)
        if health_status == "提醒":
            amount *= 0.5
            reason = (reason + "; " if reason else "") + "data_health caution amount * 0.5"
        quantity = _lot_quantity(amount, close)
        amount = round(quantity * close, 2)
        if not can_buy:
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_rule_blocked", close, 0, reason, "paper_trade_engine", 0.0))
            continue
        if amount <= 0 or quantity <= 0:
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_amount_too_small", close, quantity, "amount insufficient for 100 lots or no target room", "paper_trade_engine", amount))
            continue
        if _has_trade(trades, run_date, symbol, "BUY"):
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_duplicate_trade", close, quantity, "same-day BUY already exists", "paper_trade_engine", amount))
            continue
        trade_row = _trade_row(run_date, symbol, name, "BUY", close, quantity, amount, _buy_reason(candidate, amount), cash - amount, trades, positions)
        rows.append(_plan_row(run_date, symbol, name, "BUY", "planned" if dry_run else "executed", close, quantity, _buy_reason(candidate, amount), "paper_trade_engine", amount))
        if not dry_run:
            trades = pd.concat([trades, pd.DataFrame([trade_row])], ignore_index=True)
            positions = _add_position(positions, candidate, run_date, close, quantity, amount)
            cash = round(cash - amount, 2)
            existing.add(symbol)
            slots = max(0, slots - 1)
            available_position_room = max(0.0, available_position_room - amount)
    return rows, positions, trades, cash


def _can_buy(candidate: dict, positions: pd.DataFrame, trades: pd.DataFrame, watchlist: pd.DataFrame, classification: pd.DataFrame, health: dict, run_date: str, slots: int) -> tuple[bool, str]:
    symbol = str(candidate.get("symbol", "")).strip()
    held_symbols = set(positions["symbol"].astype(str)) if not positions.empty else set()
    if symbol in held_symbols:
        return False, "already held"
    if slots <= 0:
        return False, "max holdings reached"
    if str(candidate.get("mid_trend_signal")) != "BUY" or str(candidate.get("short_swing_signal")) != "BUY":
        return False, "requires mid_trend BUY and short_swing BUY"
    pool = _pool_for(symbol, watchlist, classification)
    if pool != "trade_pool":
        return False, f"not trade_pool: {pool}"
    health_status = health.get(symbol, {}).get("status", "正常")
    if health_status == "异常":
        return False, "data_health error"
    if _in_cooldown(symbol, trades, run_date):
        return False, f"cooldown after sell {PAPER_COOLDOWN_DAYS_AFTER_SELL} days"
    return True, ""


def _sell_reason(pos: dict, review: dict, close: float) -> str:
    status = str(review.get("sell_review_status", "")).upper()
    short_signal = str(review.get("short_swing_signal", "")).upper()
    mid_signal = str(review.get("mid_trend_signal", "")).upper()
    rank = _float(review.get("rank_score"))
    stop_loss = _float(pos.get("stop_loss"))
    health_status = str(review.get("data_health_status", ""))
    protection = str(review.get("protection_period", "")) == "yes"
    if stop_loss > 0 and close <= stop_loss:
        return "stop_loss_break"
    if mid_signal == "SELL":
        return "mid_trend_sell"
    if health_status == "异常":
        return "data_health_error"
    if status == "SELL":
        return "sell_signal_review SELL"
    if short_signal == "SELL" and rank < 60:
        return "short_swing SELL and rank_score below 60"
    if protection and status in {"WATCH", "REVIEW", "REDUCE"}:
        return ""
    if _reduce_two_days(str(pos.get("symbol", ""))):
        return "REDUCE two consecutive days"
    return ""


def _trade_row(run_date: str, symbol: str, name: str, action: str, price: float, quantity: int, amount: float, reason: str, cash_after: float, trades: pd.DataFrame, positions: pd.DataFrame) -> dict:
    position_value = _positions_value(positions)
    if action == "SELL":
        position_value = max(0.0, position_value - amount)
    elif action == "BUY":
        position_value += amount
    total_equity = cash_after + position_value
    return {
        "date": run_date,
        "trade_date": run_date,
        "symbol": symbol,
        "name": name,
        "action": action,
        "strategy_source": "paper_rule_validation",
        "position_type": "core",
        "price": round(price, 6),
        "quantity": int(quantity),
        "amount": round(amount, 2),
        "realized_pnl": 0.0,
        "fee": 0.0,
        "execution_price_type": PAPER_EXECUTION_PRICE_TYPE,
        "order_type": f"paper_{action.lower()}",
        "source": "paper_trade_engine",
        "reason": reason,
        "simulated_cash": round(cash_after, 2),
        "position_value": round(position_value, 2),
        "total_equity": round(total_equity, 2),
        "is_simulated": 1,
    }


def _add_position(positions: pd.DataFrame, candidate: dict, run_date: str, price: float, quantity: int, amount: float) -> pd.DataFrame:
    etf_type = _type_for(str(candidate.get("symbol")), str(candidate.get("name")))
    stop_loss = price * (1 - _stop_pct(etf_type))
    row = {
        "symbol": candidate["symbol"],
        "name": candidate["name"],
        "strategy_source": "resonance" if candidate.get("mid_trend_signal") == "BUY" and candidate.get("short_swing_signal") == "BUY" else "paper_rule_validation",
        "position_type": "core",
        "entry_date": run_date,
        "entry_price": round(price, 6),
        "quantity": int(quantity),
        "cost": round(amount, 2),
        "stop_loss": round(stop_loss, 6),
        "reason": _buy_reason(candidate, amount),
        "current_price": price,
        "market_value": round(amount, 2),
        "unrealized_pnl": 0.0,
        "unrealized_return": 0.0,
        "unrealized_pnl_pct": 0.0,
        "holding_days": 0,
        "risk_alert": "",
    }
    return pd.concat([positions, pd.DataFrame([row])], ignore_index=True)


def _write_outputs(plan_rows: list[dict], state_payload: dict, before: dict, after: dict) -> None:
    plan = pd.DataFrame(plan_rows)
    if plan.empty:
        plan = pd.DataFrame(columns=["date", "symbol", "name", "action", "plan_status", "price", "quantity", "amount", "reason", "source"])
    plan.to_csv(PLAN_CSV_FILE, index=False)
    _write_plan_md(plan, state_payload, before, after)
    _write_engine_report(plan, state_payload, before, after)
    _write_design_report()


def _write_plan_md(plan: pd.DataFrame, state: dict, before: dict, after: dict) -> None:
    lines = [
        f"# 规则验证版模拟交易计划 {state['date']}",
        "",
        "本报告只针对本地模拟盘，不接券商 API，不真实下单。",
        "",
        "## 引擎状态",
        f"- PAPER_MODE：{PAPER_MODE}",
        f"- PAPER_AUTO_EXECUTE：{PAPER_AUTO_EXECUTE}",
        f"- REAL_TRADE_ENABLED：{REAL_TRADE_ENABLED}",
        f"- BROKER_API_ENABLED：{BROKER_API_ENABLED}",
        f"- status：{state['status']}",
        f"- dry_run：{state['dry_run']}",
        f"- buy_count：{state['buy_count']}",
        f"- sell_count：{state['sell_count']}",
        f"- skipped_duplicate：{state['skipped_duplicate']}",
        f"- skip_reason：{state['skip_reason']}",
        "",
        "## 账户摘要",
        f"- 执行前现金：{before['cash']:.2f}",
        f"- 执行前仓位：{before['position_ratio']:.2%}",
        f"- 执行后现金：{after['cash']:.2f}",
        f"- 执行后仓位：{after['position_ratio']:.2%}",
        "",
        "## 交易计划与结果",
        "| date | symbol | name | action | status | price | quantity | amount | reason |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for _, row in plan.iterrows():
        lines.append(
            f"| {row.get('date','')} | {row.get('symbol','')} | {row.get('name','')} | {row.get('action','')} | {row.get('plan_status','')} | "
            f"{_fmt(row.get('price'))} | {_fmt(row.get('quantity'))} | {_fmt(row.get('amount'))} | {str(row.get('reason','')).replace('|','/')} |"
        )
    lines += ["", "## 安全边界", "- 只写本地模拟盘。", "- 不接真实交易。", "- 不添加真实交易按钮。"]
    PLAN_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_engine_report(plan: pd.DataFrame, state: dict, before: dict, after: dict) -> None:
    dup = _duplicate_count(_read_csv(PAPER_TRADES_FILE, TRADE_COLUMNS))
    lines = [
        "# paper_trade_engine 执行报告",
        "",
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 本轮是模拟盘自动交易，不是真实交易。",
        "- launchd/catchup 只负责触发；paper_trade_engine 负责模拟盘规则判断和本地 CSV 写入。",
        "- Codex 只负责开发、修复和优化，不作为每日交易执行器。",
        f"- 当前状态：{state['status']}",
        f"- dry_run：{state['dry_run']}",
        f"- 买入数量：{state['buy_count']}",
        f"- 卖出数量：{state['sell_count']}",
        f"- paper_trades 同日同 symbol/action/source 重复数：{dup}",
        f"- 执行后现金：{after['cash']:.2f}",
        f"- 执行后持仓数：{after['position_count']}",
        f"- 执行后仓位：{after['position_ratio']:.2%}",
        "",
        "## dashboard 展示",
        "- 顶部状态栏展示 paper mode / auto execute / real trade disabled。",
        "- 今日模拟交易状态展示执行状态、买入/卖出数量、跳过原因。",
        "- 今日模拟交易计划展示执行/跳过记录。",
        "- 当前持仓展示保护期、止损、距离止损、sell review。",
        "",
        "## L2 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户/资金/持仓。",
        "- 不保存密码/token。",
    ]
    ENGINE_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_design_report() -> None:
    lines = [
        "# paper_trade_engine 设计报告",
        "",
        "- 模式：rule_validation。",
        "- 只服务本地模拟盘自动执行验证。",
        "- 卖出优先于买入。",
        "- 买入要求 trade_pool、mid_trend=BUY、short_swing=BUY、Top3、未持有、未冷静期、仓位合规。",
        "- 卖出只在 SELL、止损、mid_trend SELL、short_swing SELL+低分、data_health error 等硬条件触发。",
        "- 买入后 1-2 日保护期内，除硬风控外不自动卖出。",
        "- 单只 ETF 上限 20%，最多持有 3 只，默认 neutral 目标仓位 30%。",
        "- dashboard 只读展示，不提供真实交易按钮。",
        "",
        "## 下一步",
        "- 继续回测自动买卖规则对回撤、胜率和过度交易的影响。",
    ]
    DESIGN_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def build_status() -> dict:
    state = _read_state()
    run_date = _latest_data_date()
    positions = _read_csv(PAPER_POSITIONS_FILE, POSITION_COLUMNS)
    trades = _read_csv(PAPER_TRADES_FILE, TRADE_COLUMNS)
    portfolio = _portfolio_summary(positions, trades)
    return {"date": run_date, "state": state.get(run_date, {}), "portfolio": portfolio}


def _read_buy_ranking() -> list[dict]:
    rows = _read_markdown_table(BUY_RANKING_FILE, "Top BUY Ranking")
    result = []
    for row in rows:
        result.append(
            {
                "rank": int(_float(row.get("rank"), 0)),
                "symbol": row.get("code", ""),
                "name": row.get("name", ""),
                "group": row.get("group", ""),
                "mid_trend_signal": row.get("mid", "N/A"),
                "short_swing_signal": row.get("short", "N/A"),
                "rank_score": _float(row.get("rank_score")),
                "risk_note": row.get("风险提示", ""),
            }
        )
    return result


def _read_health() -> dict[str, dict]:
    rows = _read_markdown_table(DATA_HEALTH_FILE, "明细")
    return {str(row.get("代码", "")): {"status": row.get("状态", ""), "note": row.get("提醒", "")} for row in rows if row.get("代码")}


def _read_markdown_table(path: Path, section_title: str) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table = []
    for line in lines:
        if line.strip().startswith("## "):
            if table and in_section:
                break
            in_section = section_title in line
            continue
        if in_section and line.strip().startswith("|"):
            table.append(line)
        elif in_section and table:
            break
    if len(table) < 3:
        return []
    headers = [cell.strip() for cell in table[0].strip("|").split("|")]
    rows = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _plan_row(date: str, symbol: str, name: str, action: str, status: str, price: float, quantity: int, reason: str, source: str, amount: float = 0.0) -> dict:
    return {"date": date, "symbol": symbol, "name": name, "action": action, "plan_status": status, "price": price, "quantity": quantity, "amount": amount, "reason": reason, "source": source}


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not PAPER_POSITIONS_FILE.exists():
        pd.DataFrame(columns=POSITION_COLUMNS).to_csv(PAPER_POSITIONS_FILE, index=False)
    if not PAPER_TRADES_FILE.exists():
        pd.DataFrame(columns=TRADE_COLUMNS).to_csv(PAPER_TRADES_FILE, index=False)


def _read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns or [])
    df = pd.read_csv(path, dtype=str).fillna("")
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns].copy()
    return df


def _read_state() -> dict:
    if not ENGINE_STATE_FILE.exists() or ENGINE_STATE_FILE.stat().st_size == 0:
        return {}
    try:
        return json.loads(ENGINE_STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_state(state: dict) -> None:
    ENGINE_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _portfolio_summary(positions: pd.DataFrame, trades: pd.DataFrame) -> dict:
    positions = _revalue_positions(positions, _latest_data_date()) if not positions.empty else positions
    cash = PAPER_INITIAL_CASH
    if not trades.empty:
        for row in trades.to_dict(orient="records"):
            amount = _float(row.get("amount"))
            action = str(row.get("action", "")).upper()
            if action == "BUY":
                cash -= amount
            elif action == "SELL":
                cash += amount
    else:
        cash -= _positions_cost(positions)
    value = _positions_value(positions)
    total = cash + value
    return {"cash": round(cash, 2), "market_value": round(value, 2), "total_equity": round(total, 2), "position_count": int(len(positions)), "position_ratio": value / total if total else 0.0}


def _revalue_positions(positions: pd.DataFrame, run_date: str) -> pd.DataFrame:
    if positions.empty:
        return pd.DataFrame(columns=POSITION_COLUMNS)
    df = positions.copy().astype(object)
    for col in POSITION_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    for idx, row in df.iterrows():
        symbol = str(row.get("symbol", ""))
        price = _latest_close(symbol) or _float(row.get("current_price"), _float(row.get("entry_price")))
        qty = _float(row.get("quantity"))
        cost = _float(row.get("cost"), _float(row.get("entry_price")) * qty)
        df.loc[idx, "current_price"] = price
        df.loc[idx, "market_value"] = round(price * qty, 2)
        df.loc[idx, "unrealized_pnl"] = round(price * qty - cost, 2)
        df.loc[idx, "unrealized_return"] = (price * qty - cost) / cost if cost else 0.0
        df.loc[idx, "unrealized_pnl_pct"] = df.loc[idx, "unrealized_return"]
        df.loc[idx, "holding_days"] = (pd.to_datetime(run_date) - pd.to_datetime(row.get("entry_date"), errors="coerce")).days
        df.loc[idx, "risk_alert"] = "触及或低于模拟止损价" if _float(row.get("stop_loss")) and price <= _float(row.get("stop_loss")) else ""
    return df[POSITION_COLUMNS].copy()


def _positions_value(positions: pd.DataFrame) -> float:
    if positions.empty:
        return 0.0
    if "market_value" in positions.columns:
        values = pd.to_numeric(positions["market_value"], errors="coerce")
        if values.notna().any():
            return float(values.fillna(0).sum())
    return sum(_latest_close(str(row.get("symbol", ""))) * _float(row.get("quantity")) for row in positions.to_dict(orient="records"))


def _positions_cost(positions: pd.DataFrame) -> float:
    return float(pd.to_numeric(positions.get("cost", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not positions.empty else 0.0


def _latest_close(symbol: str) -> float:
    if not symbol:
        return 0.0
    prefix = "sh" if symbol.startswith(("5", "6")) else "sz"
    path = DATA_DIR / "etf_daily" / f"{prefix}_{symbol}.csv"
    if not path.exists():
        return 0.0
    try:
        df = pd.read_csv(path)
    except Exception:
        return 0.0
    if df.empty or "close" not in df.columns:
        return 0.0
    return _float(df.sort_values("date").iloc[-1]["close"])


def _latest_data_date() -> str:
    latest = ""
    for path in (DATA_DIR / "etf_daily").glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or pd.Timestamp.now().strftime("%Y-%m-%d")


def _target_position_pct() -> float:
    if PAPER_DEFAULT_MARKET_STATE == "strong":
        return PAPER_TARGET_POSITION_STRONG
    if PAPER_DEFAULT_MARKET_STATE == "weak":
        return PAPER_TARGET_POSITION_WEAK
    return PAPER_TARGET_POSITION_NEUTRAL


def _pool_for(symbol: str, watchlist: pd.DataFrame, classification: pd.DataFrame) -> str:
    for df, code_col, pool_col in [(watchlist, "code", "role"), (classification, "code", "pool")]:
        if not df.empty and code_col in df.columns:
            matched = df[df[code_col].astype(str) == symbol]
            if not matched.empty:
                return str(matched.iloc[0].get(pool_col, ""))
    return ""


def _type_for(symbol: str, name: str) -> str:
    classification = _read_csv(CLASSIFICATION_FILE)
    if not classification.empty:
        matched = classification[classification["code"].astype(str) == symbol]
        if not matched.empty:
            if symbol == "515880":
                return "high_beta"
            return str(matched.iloc[0].get("etf_type", "sector"))
    if symbol == "515880" or "证券" in name:
        return "high_beta"
    return "sector"


def _stop_pct(etf_type: str) -> float:
    return {"broad_index": 0.08, "sector": 0.06, "theme": 0.05, "hot_theme": 0.05, "high_beta": 0.05, "commodity_resource": 0.06, "bond_cash": 0.02, "qdii": 0.06}.get(etf_type, 0.06)


def _lot_quantity(amount: float, price: float) -> int:
    if amount <= 0 or price <= 0:
        return 0
    return int((amount / price) // PAPER_LOT_SIZE * PAPER_LOT_SIZE)


def _has_trade(trades: pd.DataFrame, run_date: str, symbol: str, action: str) -> bool:
    if trades.empty:
        return False
    dates = pd.to_datetime(trades["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    mask = (dates == run_date) & (trades["symbol"].astype(str) == symbol) & (trades["action"].astype(str).str.upper() == action) & (trades["source"].astype(str) == "paper_trade_engine")
    return bool(mask.any())


def _in_cooldown(symbol: str, trades: pd.DataFrame, run_date: str) -> bool:
    if trades.empty:
        return False
    df = trades[(trades["symbol"].astype(str) == symbol) & (trades["action"].astype(str).str.upper() == "SELL")].copy()
    if df.empty:
        return False
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    last_sell = df["date"].max()
    return (pd.to_datetime(run_date) - last_sell).days < PAPER_COOLDOWN_DAYS_AFTER_SELL


def _reduce_two_days(symbol: str) -> bool:
    hist = _read_csv(REPORT_DIR / "sell_signal_review_history.csv")
    if hist.empty:
        return False
    matched = hist[hist["symbol"].astype(str) == symbol].tail(2)
    return len(matched) == 2 and (matched["sell_review_status"].astype(str).str.upper() == "REDUCE").all()


def _buy_reason(candidate: dict, amount: float) -> str:
    return f"paper_rule_validation; rank={candidate.get('rank')}; rank_score={candidate.get('rank_score')}; mid_trend={candidate.get('mid_trend_signal')}; short_swing={candidate.get('short_swing_signal')}; amount={amount:.2f}"


def _duplicate_count(trades: pd.DataFrame) -> int:
    if trades.empty:
        return 0
    subset = trades[["date", "symbol", "action", "source"]].astype(str)
    return int(subset.duplicated().sum())


def _fmt(value: object) -> str:
    numeric = _float(value, float("nan"))
    if pd.isna(numeric):
        return ""
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


if __name__ == "__main__":
    main()
