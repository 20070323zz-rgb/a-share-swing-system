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
    PAPER_COMMISSION_RATE,
    PAPER_COOLDOWN_DAYS_AFTER_SELL,
    PAPER_DEFAULT_MARKET_STATE,
    PAPER_EXECUTION_PRICE_TYPE,
    PAPER_INITIAL_CASH,
    PAPER_LOT_SIZE,
    PAPER_MAX_HOLDINGS,
    PAPER_MAX_SINGLE_POSITION_PCT,
    PAPER_MIN_COMMISSION,
    PAPER_MODE,
    PAPER_POSITIONS_FILE,
    PAPER_SLIPPAGE_RATE,
    PAPER_STAMP_TAX_RATE,
    PAPER_TARGET_POSITION_NEUTRAL,
    PAPER_TARGET_POSITION_STRONG,
    PAPER_TARGET_POSITION_WEAK,
    PAPER_TRANSFER_FEE_RATE,
    PAPER_TRADES_FILE,
    PAPER_USE_MARKET_STATE_POSITION,
    REAL_TRADE_ENABLED,
    REPORT_DIR,
    WATCHLIST_FILE,
)


PLAN_MD_FILE = REPORT_DIR / "paper_trade_plan.md"
PLAN_CSV_FILE = REPORT_DIR / "paper_trade_plan.csv"
ENGINE_REPORT_FILE = REPORT_DIR / "paper_trade_engine_report.md"
DESIGN_REPORT_FILE = REPORT_DIR / "paper_trade_engine_design_report.md"
PHASE1_REPORT_FILE = REPORT_DIR / "phase1_paper_trading_closure_report.md"
REALISM_REPORT_FILE = REPORT_DIR / "trade_execution_realism_report.md"
DASHBOARD_APP_FUTURE_PLAN_FILE = REPORT_DIR / "dashboard_app_future_plan.md"
ENGINE_STATE_FILE = DATA_DIR / "paper_trade_engine_state.json"
BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
SELL_REVIEW_FILE = REPORT_DIR / "sell_signal_review.csv"
DATA_HEALTH_FILE = REPORT_DIR / "latest_data_health.md"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
LEGACY_CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
EXPANSION_CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"
MARKET_STATE_FILE = REPORT_DIR / "market_state.csv"
PORTFOLIO_EXPOSURE_FILE = REPORT_DIR / "portfolio_exposure.csv"
QUALITY_REVIEW_FILE = REPORT_DIR / "model_research_quality_review.json"
PHASE2C_REPORT_FILE = REPORT_DIR / "phase2c_execution_layer_light_integration_report.md"

TRADE_COLUMNS = [
    "date",
    "symbol",
    "name",
    "action",
    "price",
    "raw_close",
    "execution_price",
    "execution_price_type",
    "quantity",
    "gross_amount",
    "commission",
    "stamp_tax",
    "transfer_fee",
    "net_cash_change",
    "slippage_rate",
    "reason",
    "source",
    "created_at",
    "holding_days",
    "realized_pnl",
    "realized_pnl_pct",
    "cash_after_trade",
    "position_value_after_trade",
    "total_equity_after_trade",
    "trade_date",
    "strategy_source",
    "position_type",
    "amount",
    "fee",
    "order_type",
    "simulated_cash",
    "position_value",
    "total_equity",
    "is_simulated",
]

POSITION_COLUMNS = [
    "symbol",
    "name",
    "quantity",
    "avg_cost",
    "raw_cost",
    "total_cost",
    "commission_paid",
    "entry_date",
    "last_price",
    "market_value",
    "unrealized_pnl",
    "unrealized_pnl_pct",
    "holding_days",
    "etf_type",
    "group",
    "max_holding_days",
    "stop_loss_price",
    "distance_to_stop_pct",
    "sell_review_status",
    "data_health_status",
    "protection_period",
    "updated_at",
    "strategy_source",
    "position_type",
    "entry_price",
    "cost",
    "stop_loss",
    "reason",
    "current_price",
    "unrealized_return",
    "risk_alert",
]

PLAN_COLUMNS = [
    "date",
    "run_date",
    "price_data_date",
    "symbol",
    "name",
    "action",
    "plan_status",
    "raw_close",
    "execution_price",
    "quantity",
    "gross_amount",
    "commission",
    "stamp_tax",
    "transfer_fee",
    "net_cash_change",
    "slippage_rate",
    "reason",
    "source",
    "market_state",
    "market_score",
    "suggested_position_pct",
    "current_position_pct",
    "position_alignment",
    "etf_type",
    "risk_profile",
    "holding_profile",
    "max_holding_days",
    "stop_loss_pct",
    "distance_to_stop_pct",
    "portfolio_exposure_status",
    "portfolio_balance_suggestion",
    "concentration_warning",
    "exposure_context",
    "buy_candidate_context",
    "research_confidence",
    "execution_layer_note",
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
    run_date = _engine_run_date()
    price_data_date = _latest_data_date()
    positions = _normalize_positions(_read_csv(PAPER_POSITIONS_FILE, POSITION_COLUMNS))
    trades = _normalize_trades(_read_csv(PAPER_TRADES_FILE, TRADE_COLUMNS))
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
        skipped_rows.append(_plan_row(run_date, "", "", "ENGINE", "skipped_duplicate", 0, 0, "engine already executed today", "paper_trade_engine", price_data_date=price_data_date))
        existing_plan = _read_csv(PLAN_CSV_FILE).to_dict(orient="records")
        skipped_rows.extend(existing_plan)
        status = "skipped_duplicate"
    else:
        sell_rows, positions_after, trades_after, cash = _process_sells(run_date, price_data_date, positions_after, trades_after, cash, dry_run, portfolio_before["position_ratio"])
        plan_rows.extend(sell_rows)
        executed_rows.extend([row for row in sell_rows if row["plan_status"] == "executed"])
        skipped_rows.extend([row for row in sell_rows if row["plan_status"].startswith("skipped")])

        buy_rows, positions_after, trades_after, cash = _process_buys(run_date, price_data_date, positions_after, trades_after, cash, dry_run, portfolio_before["position_ratio"])
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
    total_commission = sum(_float(row.get("commission")) for row in executed_rows)
    total_slippage_cost = sum(abs(_float(row.get("execution_price")) - _float(row.get("raw_close"))) * _float(row.get("quantity")) for row in executed_rows)
    total_trade_cost = total_commission + sum(_float(row.get("stamp_tax")) + _float(row.get("transfer_fee")) for row in executed_rows) + total_slippage_cost
    state_payload = {
        "date": run_date,
        "run_date": run_date,
        "price_data_date": price_data_date,
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
        "today_trade_cost": round(total_trade_cost, 2),
        "today_commission": round(total_commission, 2),
        "today_slippage_cost": round(total_slippage_cost, 2),
        "execution_price_type": PAPER_EXECUTION_PRICE_TYPE,
        "paper_use_market_state_position": PAPER_USE_MARKET_STATE_POSITION,
    }
    state[run_date] = state_payload
    _write_state(state)
    _write_outputs(plan_rows + skipped_rows if duplicate_execute else plan_rows, state_payload, portfolio_before, portfolio_after)
    return state_payload


def _process_sells(
    run_date: str,
    price_data_date: str,
    positions: pd.DataFrame,
    trades: pd.DataFrame,
    cash: float,
    dry_run: bool,
    current_position_pct: float,
) -> tuple[list[dict], pd.DataFrame, pd.DataFrame, float]:
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
        cost = _trade_cost("SELL", close, quantity)
        reason = _sell_reason(pos, review, close)
        if not reason:
            rows.append(_plan_row(run_date, symbol, name, "SELL", "skipped_no_sell_signal", close, quantity, "sell rules not triggered", "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=_phase2c_context(symbol, name, "SELL", positions, close, current_position_pct)))
            continue
        if _has_trade(trades, run_date, symbol, "SELL"):
            rows.append(_plan_row(run_date, symbol, name, "SELL", "skipped_duplicate_trade", close, quantity, "same-day SELL already exists", "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=_phase2c_context(symbol, name, "SELL", positions, close, current_position_pct)))
            continue
        allocated_cost = _float(pos.get("total_cost"), _float(pos.get("cost")))
        realized_pnl = round(cost["net_cash_change"] - allocated_cost, 2)
        realized_pct = realized_pnl / allocated_cost if allocated_cost else 0.0
        trade_row = _trade_row(run_date, symbol, name, "SELL", cost, reason, cash + cost["net_cash_change"], keep_positions, holding_days=int(_float(pos.get("holding_days"))), realized_pnl=realized_pnl, realized_pnl_pct=realized_pct)
        rows.append(_plan_row(run_date, symbol, name, "SELL", "planned" if dry_run else "executed", close, quantity, reason, "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=_phase2c_context(symbol, name, "SELL", positions, close, current_position_pct)))
        if not dry_run:
            trades = pd.concat([trades, pd.DataFrame([trade_row])], ignore_index=True)
            keep_positions = keep_positions[keep_positions["symbol"].astype(str) != symbol].copy()
            cash = round(cash + cost["net_cash_change"], 2)
    return rows, keep_positions, trades, cash


def _process_buys(
    run_date: str,
    price_data_date: str,
    positions: pd.DataFrame,
    trades: pd.DataFrame,
    cash: float,
    dry_run: bool,
    current_position_pct: float,
) -> tuple[list[dict], pd.DataFrame, pd.DataFrame, float]:
    ranking = _read_buy_ranking()
    health = _read_health()
    classification = _read_classification()
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
        quantity, cost = _affordable_lot_quantity(amount, close, cash)
        context = _phase2c_context(symbol, name, "BUY", positions, close, current_position_pct, candidate)
        if not can_buy:
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_rule_blocked", close, 0, reason, "paper_trade_engine", cost=_zero_trade_cost("BUY", close, 0), price_data_date=price_data_date, context=context))
            continue
        if cost["gross_amount"] <= 0 or quantity <= 0:
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_amount_too_small", close, quantity, "amount insufficient for 100 lots, target room, or minimum commission", "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=context))
            continue
        if cash + cost["net_cash_change"] < -0.0001:
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_cash_insufficient", close, quantity, "cash insufficient after commission", "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=context))
            continue
        if _has_trade(trades, run_date, symbol, "BUY"):
            rows.append(_plan_row(run_date, symbol, name, "BUY", "skipped_duplicate_trade", close, quantity, "same-day BUY already exists", "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=context))
            continue
        trade_row = _trade_row(run_date, symbol, name, "BUY", cost, _buy_reason(candidate, cost["gross_amount"]), cash + cost["net_cash_change"], positions)
        rows.append(_plan_row(run_date, symbol, name, "BUY", "planned" if dry_run else "executed", close, quantity, _buy_reason(candidate, cost["gross_amount"]), "paper_trade_engine", cost=cost, price_data_date=price_data_date, context=context))
        if not dry_run:
            trades = pd.concat([trades, pd.DataFrame([trade_row])], ignore_index=True)
            positions = _add_position(positions, candidate, run_date, cost)
            cash = round(cash + cost["net_cash_change"], 2)
            existing.add(symbol)
            slots = max(0, slots - 1)
            available_position_room = max(0.0, available_position_room - cost["gross_amount"])
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
    stop_loss = _float(pos.get("stop_loss_price"), _float(pos.get("stop_loss")))
    health_status = str(review.get("data_health_status", ""))
    protection = str(review.get("protection_period", "")) == "yes"
    holding_days = _float(pos.get("holding_days"))
    max_holding_days = _float(pos.get("max_holding_days"), _max_holding_days(str(pos.get("etf_type", ""))))
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
    if max_holding_days > 0 and holding_days >= max_holding_days and not (mid_signal == "BUY" and short_signal == "BUY"):
        return "max_holding_days reached without signal recovery"
    return ""


def _trade_row(
    run_date: str,
    symbol: str,
    name: str,
    action: str,
    cost: dict,
    reason: str,
    cash_after: float,
    positions: pd.DataFrame,
    holding_days: int = 0,
    realized_pnl: float = 0.0,
    realized_pnl_pct: float = 0.0,
) -> dict:
    position_value = _positions_value(positions)
    if action == "SELL":
        position_value = max(0.0, position_value - cost["raw_close"] * cost["quantity"])
    elif action == "BUY":
        position_value += cost["raw_close"] * cost["quantity"]
    total_equity = cash_after + position_value
    return {
        "date": run_date,
        "symbol": symbol,
        "name": name,
        "action": action,
        "price": round(cost["execution_price"], 6),
        "raw_close": round(cost["raw_close"], 6),
        "execution_price": round(cost["execution_price"], 6),
        "execution_price_type": PAPER_EXECUTION_PRICE_TYPE,
        "quantity": int(cost["quantity"]),
        "gross_amount": round(cost["gross_amount"], 2),
        "commission": round(cost["commission"], 2),
        "stamp_tax": round(cost["stamp_tax"], 2),
        "transfer_fee": round(cost["transfer_fee"], 2),
        "net_cash_change": round(cost["net_cash_change"], 2),
        "slippage_rate": PAPER_SLIPPAGE_RATE,
        "reason": reason,
        "source": "paper_trade_engine",
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "holding_days": int(holding_days),
        "realized_pnl": round(realized_pnl, 2),
        "realized_pnl_pct": round(realized_pnl_pct, 6),
        "cash_after_trade": round(cash_after, 2),
        "position_value_after_trade": round(position_value, 2),
        "total_equity_after_trade": round(total_equity, 2),
        "trade_date": run_date,
        "strategy_source": "paper_rule_validation",
        "position_type": "core",
        "amount": round(cost["gross_amount"], 2),
        "fee": round(cost["commission"] + cost["stamp_tax"] + cost["transfer_fee"], 2),
        "order_type": f"paper_{action.lower()}",
        "simulated_cash": round(cash_after, 2),
        "position_value": round(position_value, 2),
        "total_equity": round(total_equity, 2),
        "is_simulated": 1,
    }


def _add_position(positions: pd.DataFrame, candidate: dict, run_date: str, cost: dict) -> pd.DataFrame:
    class_row = _classification_row(str(candidate.get("symbol")))
    etf_type = str(class_row.get("etf_type") or _type_for(str(candidate.get("symbol")), str(candidate.get("name"))))
    group = str(class_row.get("group") or candidate.get("group", ""))
    quantity = int(cost["quantity"])
    raw_cost = float(cost["gross_amount"])
    total_cost = raw_cost + float(cost["commission"]) + float(cost["transfer_fee"])
    avg_cost = total_cost / quantity if quantity else cost["execution_price"]
    stop_loss_pct = _float(class_row.get("stop_loss_pct"), _stop_pct(etf_type))
    max_holding_days = int(_float(class_row.get("max_holding_days"), _max_holding_days(etf_type)))
    stop_loss = avg_cost * (1 - stop_loss_pct)
    row = {
        "symbol": candidate["symbol"],
        "name": candidate["name"],
        "quantity": int(quantity),
        "avg_cost": round(avg_cost, 6),
        "raw_cost": round(raw_cost, 2),
        "total_cost": round(total_cost, 2),
        "commission_paid": round(cost["commission"] + cost["transfer_fee"], 2),
        "entry_date": run_date,
        "last_price": round(cost["raw_close"], 6),
        "market_value": round(cost["raw_close"] * quantity, 2),
        "unrealized_pnl": round(cost["raw_close"] * quantity - total_cost, 2),
        "unrealized_pnl_pct": round((cost["raw_close"] * quantity - total_cost) / total_cost, 6) if total_cost else 0.0,
        "holding_days": 0,
        "etf_type": etf_type,
        "group": group,
        "max_holding_days": max_holding_days,
        "stop_loss_price": round(stop_loss, 6),
        "distance_to_stop_pct": round((cost["raw_close"] - stop_loss) / cost["raw_close"], 6) if cost["raw_close"] else 0.0,
        "sell_review_status": "N/A",
        "data_health_status": "N/A",
        "protection_period": "yes",
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "strategy_source": "resonance" if candidate.get("mid_trend_signal") == "BUY" and candidate.get("short_swing_signal") == "BUY" else "paper_rule_validation",
        "position_type": "core",
        "entry_price": round(avg_cost, 6),
        "cost": round(total_cost, 2),
        "stop_loss": round(stop_loss, 6),
        "reason": _buy_reason(candidate, cost["gross_amount"]),
        "current_price": round(cost["raw_close"], 6),
        "unrealized_return": 0.0,
        "risk_alert": "",
    }
    return pd.concat([positions, pd.DataFrame([row])], ignore_index=True)


def _write_outputs(plan_rows: list[dict], state_payload: dict, before: dict, after: dict) -> None:
    plan = pd.DataFrame(plan_rows)
    if plan.empty:
        plan = pd.DataFrame(columns=PLAN_COLUMNS)
    for col in PLAN_COLUMNS:
        if col not in plan.columns:
            plan[col] = ""
    plan = plan[PLAN_COLUMNS]
    plan.to_csv(PLAN_CSV_FILE, index=False)
    _write_plan_md(plan, state_payload, before, after)
    _write_engine_report(plan, state_payload, before, after)
    _write_design_report()
    _write_phase1_report(plan, state_payload, before, after)
    _write_realism_report()
    _write_dashboard_app_future_plan()
    _write_phase2c_report(plan, state_payload, before, after)


def _write_plan_md(plan: pd.DataFrame, state: dict, before: dict, after: dict) -> None:
    lines = [
        f"# 规则验证版模拟交易计划 {state['run_date']}",
        "",
        "本报告只针对本地模拟盘，不接券商 API，不真实下单。",
        f"模拟执行日期为 {state['run_date']}；价格使用本地最新行情数据日 {state['price_data_date']} 的 close proxy。",
        "",
        "## 引擎状态",
        f"- run_date：{state['run_date']}",
        f"- price_data_date：{state['price_data_date']}",
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
        f"- PAPER_USE_MARKET_STATE_POSITION：{PAPER_USE_MARKET_STATE_POSITION}",
        "",
        "## 账户摘要",
        f"- 执行前现金：{before['cash']:.2f}",
        f"- 执行前仓位：{before['position_ratio']:.2%}",
        f"- 执行后现金：{after['cash']:.2f}",
        f"- 执行后仓位：{after['position_ratio']:.2%}",
        "",
        "## Phase 2C 轻量接入说明",
        "- etf_type / max_holding_days / stop_loss_pct 已进入计划解释和风险展示。",
        "- market_state 只展示建议仓位区间，不改变买入金额或目标仓位。",
        "- portfolio_exposure 只生成组合平衡提示和集中度提示，不阻断交易。",
        "- 本轮不改变 max_holdings，不改变 paper_trade_engine 核心成交逻辑。",
        "",
        "## 交易计划与结果",
        "| run_date | price_data_date | symbol | name | action | status | raw_close | quantity | gross_amount | market_state | current/suggested position | etf_type | max_days | stop_loss_pct | exposure_status | balance_suggestion | concentration_warning | reason |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for _, row in plan.iterrows():
        lines.append(
            f"| {row.get('run_date', row.get('date',''))} | {row.get('price_data_date','')} | {row.get('symbol','')} | {row.get('name','')} | {row.get('action','')} | {row.get('plan_status','')} | "
            f"{_fmt(row.get('raw_close'))} | {_fmt(row.get('quantity'))} | {_fmt(row.get('gross_amount'))} | {row.get('market_state','')} / {_fmt(row.get('market_score'))} | "
            f"{_pct_text(row.get('current_position_pct'))} / {row.get('suggested_position_pct','')} ({row.get('position_alignment','')}) | {row.get('etf_type','')} | {_fmt(row.get('max_holding_days'))} | {_pct_text(row.get('stop_loss_pct'))} | "
            f"{row.get('portfolio_exposure_status','')} | {str(row.get('portfolio_balance_suggestion','')).replace('|','/')} | {str(row.get('concentration_warning','')).replace('|','/')} | {str(row.get('reason','')).replace('|','/')} |"
        )
    lines += [
        "",
        "## 交易成本口径",
        f"- 佣金率：{PAPER_COMMISSION_RATE}",
        f"- 单笔最低佣金：{PAPER_MIN_COMMISSION:.2f} 元",
        f"- 滑点率：{PAPER_SLIPPAGE_RATE}",
        f"- ETF 模拟暂不计印花税：{PAPER_STAMP_TAX_RATE}",
        f"- 过户费：{PAPER_TRANSFER_FEE_RATE}",
        f"- 执行价格口径：{PAPER_EXECUTION_PRICE_TYPE}",
        "",
        "## 安全边界",
        "- 只写本地模拟盘。",
        "- 不接真实交易。",
        "- 不添加真实交易按钮。",
    ]
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
        f"- 运行日期 run_date：{state['run_date']}",
        f"- 价格数据日期 price_data_date：{state['price_data_date']}",
        f"- 当前状态：{state['status']}",
        f"- dry_run：{state['dry_run']}",
        f"- 买入数量：{state['buy_count']}",
        f"- 卖出数量：{state['sell_count']}",
        f"- 今日佣金：{state.get('today_commission', 0):.2f}",
        f"- 今日滑点成本估算：{state.get('today_slippage_cost', 0):.2f}",
        f"- 今日交易成本合计：{state.get('today_trade_cost', 0):.2f}",
        f"- 执行价格口径：{state.get('execution_price_type', PAPER_EXECUTION_PRICE_TYPE)}",
        f"- paper_trades 同日同 symbol/action/source 重复数：{dup}",
        f"- 执行后现金：{after['cash']:.2f}",
        f"- 执行后持仓数：{after['position_count']}",
        f"- 执行后仓位：{after['position_ratio']:.2%}",
        f"- PAPER_USE_MARKET_STATE_POSITION：{PAPER_USE_MARKET_STATE_POSITION}",
        "",
        "## Phase 2C 轻量接入",
        "- 已接入 etf_type / max_holding_days / stop_loss_pct / classification_reason 到交易计划解释字段。",
        "- 已接入 market_state / market_score / suggested_position_pct / position_alignment 到交易计划解释字段。",
        "- 已接入 portfolio_exposure_status / portfolio_balance_suggestion / concentration_warning 到交易计划解释字段。",
        "- 以上字段只用于 REVIEW、风险展示、paper_trade_plan 解释和 dashboard 展示，不改变买卖结果。",
        "- market_state 仓位控制默认关闭，不直接改变目标仓位。",
        "",
        "## 交易成本真实化",
        f"- 佣金率：{PAPER_COMMISSION_RATE}",
        f"- 单笔最低佣金：{PAPER_MIN_COMMISSION:.2f} 元",
        f"- 滑点率：{PAPER_SLIPPAGE_RATE}",
        f"- ETF 模拟暂不计印花税：{PAPER_STAMP_TAX_RATE}",
        f"- 过户费率：{PAPER_TRANSFER_FEE_RATE}",
        "- 买入现金扣除包含成交金额、佣金和过户费。",
        "- 卖出现金增加扣除佣金、印花税和过户费。",
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
        f"- 佣金：万一点二，即 {PAPER_COMMISSION_RATE}；单笔最低 {PAPER_MIN_COMMISSION:.2f} 元。",
        f"- 滑点：{PAPER_SLIPPAGE_RATE}；买入上滑，卖出下滑。",
        f"- 交易单位：{PAPER_LOT_SIZE} 份整数倍。",
        "- ETF 模拟暂不计印花税。",
        "- dashboard 只读展示，不提供真实交易按钮。",
        "",
        "## 下一步",
        "- 继续回测自动买卖规则对回撤、胜率和过度交易的影响。",
    ]
    DESIGN_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_phase1_report(plan: pd.DataFrame, state: dict, before: dict, after: dict) -> None:
    lines = [
        "# 第一阶段模拟买卖闭环升级报告",
        "",
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 阶段目标：模拟盘自动买卖闭环 + 真实化交易成本/滑点/交易单位约束。",
        "- 本报告是本地模拟盘研究报告，不是真实交易方案。",
        "",
        "## 闭环状态",
        f"- paper_trade_engine 状态：{state.get('status')}",
        f"- dry_run：{state.get('dry_run')}",
        f"- 今日买入数量：{state.get('buy_count')}",
        f"- 今日卖出数量：{state.get('sell_count')}",
        f"- 今日跳过重复：{state.get('skipped_duplicate')}",
        f"- 跳过原因：{state.get('skip_reason')}",
        f"- 执行前现金：{before.get('cash', 0):.2f}",
        f"- 执行后现金：{after.get('cash', 0):.2f}",
        f"- 执行后持仓数：{after.get('position_count', 0)}",
        f"- 执行后仓位：{after.get('position_ratio', 0):.2%}",
        "",
        "## 规则落地",
        "- 卖出优先于买入。",
        "- 买入只考虑 trade_pool、BUY 共振、Top3、未持有、未冷静期、仓位和现金合规的 ETF。",
        "- 单只 ETF 不超过总权益 20%，最多持有 3 只。",
        f"- 交易数量按 {PAPER_LOT_SIZE} 份整数倍。",
        "- 同一交易日、同一 symbol、同一 action、同一 source 防重复写入。",
        "",
        "## 交易成本",
        f"- 佣金率：{PAPER_COMMISSION_RATE}",
        f"- 单笔最低佣金：{PAPER_MIN_COMMISSION:.2f} 元",
        f"- 滑点率：{PAPER_SLIPPAGE_RATE}",
        f"- 今日佣金：{state.get('today_commission', 0):.2f}",
        f"- 今日滑点成本估算：{state.get('today_slippage_cost', 0):.2f}",
        f"- ETF 模拟暂不计印花税：{PAPER_STAMP_TAX_RATE}",
        "",
        "## 安全边界",
        f"- REAL_TRADE_ENABLED：{REAL_TRADE_ENABLED}",
        f"- BROKER_API_ENABLED：{BROKER_API_ENABLED}",
        "- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。",
    ]
    if not plan.empty:
        lines += [
            "",
            "## 今日计划摘要",
            "| symbol | action | status | quantity | gross_amount | commission | reason |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
        for _, row in plan.iterrows():
            lines.append(
                f"| {row.get('symbol','')} | {row.get('action','')} | {row.get('plan_status','')} | {_fmt(row.get('quantity'))} | "
                f"{_fmt(row.get('gross_amount'))} | {_fmt(row.get('commission'))} | {str(row.get('reason','')).replace('|','/')} |"
            )
    PHASE1_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_realism_report() -> None:
    lines = [
        "# 模拟交易执行真实化报告",
        "",
        "本报告说明当前模拟盘的成交、成本和交易单位假设。它不连接真实交易系统。",
        "",
        "## 成本参数",
        f"- PAPER_COMMISSION_RATE：{PAPER_COMMISSION_RATE}",
        f"- PAPER_MIN_COMMISSION：{PAPER_MIN_COMMISSION:.2f}",
        f"- PAPER_STAMP_TAX_RATE：{PAPER_STAMP_TAX_RATE}",
        f"- PAPER_TRANSFER_FEE_RATE：{PAPER_TRANSFER_FEE_RATE}",
        f"- PAPER_SLIPPAGE_RATE：{PAPER_SLIPPAGE_RATE}",
        f"- PAPER_LOT_SIZE：{PAPER_LOT_SIZE}",
        f"- PAPER_EXECUTION_PRICE_TYPE：{PAPER_EXECUTION_PRICE_TYPE}",
        "",
        "## 买入计算",
        "- raw_close = close",
        "- execution_price = raw_close * (1 + slippage_rate)",
        "- gross_amount = execution_price * quantity",
        "- commission = max(gross_amount * commission_rate, minimum_commission)",
        "- net_cash_change = -(gross_amount + commission + transfer_fee)",
        "",
        "## 卖出计算",
        "- execution_price = raw_close * (1 - slippage_rate)",
        "- gross_amount = execution_price * quantity",
        "- commission = max(gross_amount * commission_rate, minimum_commission)",
        "- net_cash_change = gross_amount - commission - stamp_tax - transfer_fee",
        "",
        "## 限制",
        "- 当前无分时数据，成交价仍使用收盘价代理并叠加滑点。",
        "- ETF 模拟暂不计印花税。",
        "- 该口径用于模拟学习，不代表真实成交保证。",
    ]
    REALISM_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_dashboard_app_future_plan() -> None:
    lines = [
        "# Dashboard / App 未来路线计划",
        "",
        "本项目当前保持本地静态看板，不引入公网部署、登录系统或真实交易入口。",
        "",
        "## 当前阶段：静态 dashboard",
        "- 由 `dashboard/build_dashboard.py` 生成 `dashboard/index.html`。",
        "- 结构化快照为 `reports/dashboard_data.json`。",
        "- 适合 Safari / 手机浏览器打开本地文件。",
        "",
        "## 下一步：本地动态 Web App",
        "- 用本地服务读取 dashboard_data.json 和报告文件。",
        "- 支持更强筛选、图表、历史状态对比。",
        "- 仍然只读，不接真实交易。",
        "",
        "## 中期：PWA",
        "- 增加离线缓存、移动端图标、响应式交互。",
        "- 仍以本地/私有网络为主，不做公网交易终端。",
        "",
        "## 长期：小程序 / App",
        "- 需要稳定后端 API、权限体系、审计日志、数据版本管理。",
        "- 如未来涉及真实交易，必须重新定义权限和人工确认机制；当前阶段永久禁止。",
        "",
        "## 现在不直接做小程序的原因",
        "- 数据与策略仍在规则验证期。",
        "- 小程序需要后端、鉴权、部署和审计，当前收益小于复杂度。",
        "- 当前最重要的是保证模拟交易记录可复盘、看板数据结构稳定。",
    ]
    DASHBOARD_APP_FUTURE_PLAN_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_phase2c_report(plan: pd.DataFrame, state: dict, before: dict, after: dict) -> None:
    added_fields = [
        "market_state",
        "market_score",
        "suggested_position_pct",
        "current_position_pct",
        "position_alignment",
        "etf_type",
        "risk_profile",
        "holding_profile",
        "max_holding_days",
        "stop_loss_pct",
        "distance_to_stop_pct",
        "portfolio_exposure_status",
        "portfolio_balance_suggestion",
        "concentration_warning",
        "research_confidence",
        "execution_layer_note",
    ]
    lines = [
        "# Phase 2C 执行层轻量接入报告",
        "",
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 本报告说明 Phase 2B 高置信度研究结论如何轻量进入模拟交易计划和看板。",
        "",
        "## 本轮接入字段",
    ]
    lines.extend([f"- `{field}`" for field in added_fields])
    lines += [
        "",
        "## 只展示不执行的结论",
        "- market_state 只展示建议仓位，不改变买入金额、目标仓位或 max_holdings。",
        "- portfolio_exposure 只提示组合平衡和集中度，不阻断买入、不强制卖出。",
        "- etf_type 的 max_holding_days / stop_loss_pct 先用于计划解释和风险展示，不新增硬卖出规则。",
        "",
        "## 是否改变买卖结果",
        f"- buy_count：{state.get('buy_count')}",
        f"- sell_count：{state.get('sell_count')}",
        f"- dry_run：{state.get('dry_run')}",
        "- 本轮新增字段不参与 amount、slots、can_buy、sell_reason 的核心判断。",
        "",
        "## 是否改变核心逻辑",
        "- 未改变 PAPER_MAX_HOLDINGS。",
        "- 未改变 rank 权重分配。",
        "- 未启用 market_state 仓位控制。",
        "- 未启用 portfolio_exposure 硬阻断。",
        "",
        "## paper 文件",
        "- 本报告生成时不直接修改 paper_trades.csv。",
        "- dry-run 不修改 paper_positions.csv。",
        "- execute 模式仍保留原有防重复交易机制。",
        "",
        "## 计划字段覆盖",
        f"- paper_trade_plan 行数：{len(plan)}",
        f"- 新增字段存在数量：{sum(1 for field in added_fields if field in plan.columns)} / {len(added_fields)}",
        f"- 执行前仓位：{before.get('position_ratio', 0):.2%}",
        f"- 执行后仓位：{after.get('position_ratio', 0):.2%}",
        f"- PAPER_USE_MARKET_STATE_POSITION：{PAPER_USE_MARKET_STATE_POSITION}",
        "",
        "## L2 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存密码/token。",
        "- 不添加真实交易按钮。",
    ]
    PHASE2C_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def build_status() -> dict:
    state = _read_state()
    run_date = _engine_run_date()
    price_data_date = _latest_data_date()
    positions = _normalize_positions(_read_csv(PAPER_POSITIONS_FILE, POSITION_COLUMNS))
    trades = _normalize_trades(_read_csv(PAPER_TRADES_FILE, TRADE_COLUMNS))
    portfolio = _portfolio_summary(positions, trades)
    return {"date": run_date, "run_date": run_date, "price_data_date": price_data_date, "state": state.get(run_date, {}), "portfolio": portfolio}


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


def _plan_row(
    date: str,
    symbol: str,
    name: str,
    action: str,
    status: str,
    price: float,
    quantity: int,
    reason: str,
    source: str,
    cost: dict | None = None,
    price_data_date: str = "",
    context: dict | None = None,
) -> dict:
    cost = cost or _zero_trade_cost(action, price, quantity)
    row = {
        "date": date,
        "run_date": date,
        "price_data_date": price_data_date,
        "symbol": symbol,
        "name": name,
        "action": action,
        "plan_status": status,
        "raw_close": cost["raw_close"],
        "execution_price": cost["execution_price"],
        "quantity": quantity,
        "gross_amount": cost["gross_amount"],
        "commission": cost["commission"],
        "stamp_tax": cost["stamp_tax"],
        "transfer_fee": cost["transfer_fee"],
        "net_cash_change": cost["net_cash_change"],
        "slippage_rate": cost["slippage_rate"],
        "reason": reason,
        "source": source,
    }
    context = context or {}
    for key in PLAN_COLUMNS:
        if key not in row:
            row[key] = context.get(key, "")
    return row


def _phase2c_context(symbol: str, name: str, action: str, positions: pd.DataFrame, price: float, current_position_pct: float, candidate: dict | None = None) -> dict:
    classification = _classification_row(symbol)
    market = _market_state_context(current_position_pct)
    exposure = _portfolio_exposure_context(symbol, name, classification, candidate)
    etf_type = str(classification.get("etf_type") or _type_for(symbol, name))
    stop_loss_pct = _float(classification.get("stop_loss_pct"), _stop_pct(etf_type))
    max_holding_days = int(_float(classification.get("max_holding_days"), _max_holding_days(etf_type)))
    stop_loss_price = price * (1 - stop_loss_pct) if price else 0.0
    held = _position_row(positions, symbol)
    if held:
        stop_loss_price = _float(held.get("stop_loss_price"), _float(held.get("stop_loss"), stop_loss_price))
    distance_to_stop = (price - stop_loss_price) / price if price and stop_loss_price else ""
    auto_buy_allowed = str(classification.get("auto_buy_allowed", ""))
    confidence = _research_confidence()
    execution_note = (
        "phase2c_light_only; no amount/max_holdings/market_state execution change; "
        f"auto_buy_allowed={auto_buy_allowed}; classification={classification.get('classification_reason', '')}"
    )
    return {
        **market,
        "etf_type": etf_type,
        "risk_profile": classification.get("risk_profile", ""),
        "holding_profile": classification.get("holding_profile", ""),
        "max_holding_days": max_holding_days,
        "stop_loss_pct": stop_loss_pct,
        "distance_to_stop_pct": distance_to_stop,
        "portfolio_exposure_status": exposure.get("portfolio_exposure_status", ""),
        "portfolio_balance_suggestion": exposure.get("portfolio_balance_suggestion", ""),
        "concentration_warning": exposure.get("concentration_warning", ""),
        "exposure_context": exposure.get("exposure_context", ""),
        "buy_candidate_context": exposure.get("buy_candidate_context", "") if str(action).upper() == "BUY" else "",
        "research_confidence": confidence,
        "execution_layer_note": execution_note,
    }


def _classification_row(symbol: str) -> dict:
    df = _read_classification()
    if df.empty:
        return {}
    for col in ["symbol", "code"]:
        if col in df.columns:
            matched = df[df[col].astype(str) == str(symbol)]
            if not matched.empty:
                return matched.iloc[0].to_dict()
    return {}


def _read_classification() -> pd.DataFrame:
    df = _read_csv(CLASSIFICATION_FILE)
    if df.empty:
        df = _read_csv(LEGACY_CLASSIFICATION_FILE)
    if not df.empty and "symbol" not in df.columns and "code" in df.columns:
        df["symbol"] = df["code"]
    if not df.empty and "code" not in df.columns and "symbol" in df.columns:
        df["code"] = df["symbol"]
    return df


def _market_state_context(current_position_pct: float) -> dict:
    df = _read_csv(MARKET_STATE_FILE)
    summary = df[df["row_type"].astype(str) == "summary"].head(1) if not df.empty and "row_type" in df.columns else pd.DataFrame()
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    low = _float(row.get("suggested_total_position_min"), float("nan"))
    high = _float(row.get("suggested_total_position_max"), float("nan"))
    if pd.isna(low) or pd.isna(high):
        suggested = ""
        alignment = "unknown"
    else:
        suggested = f"{low:.2%}-{high:.2%}"
        if current_position_pct < low:
            alignment = "below_suggested_range"
        elif current_position_pct > high:
            alignment = "above_suggested_range"
        else:
            alignment = "aligned"
    return {
        "market_state": row.get("market_state", ""),
        "market_score": row.get("market_score", ""),
        "suggested_position_pct": suggested,
        "current_position_pct": current_position_pct,
        "position_alignment": alignment,
    }


def _portfolio_exposure_context(symbol: str, name: str, classification: dict, candidate: dict | None) -> dict:
    exposure = _read_csv(PORTFOLIO_EXPOSURE_FILE)
    summary = exposure[exposure["row_type"].astype(str) == "summary"].head(1) if not exposure.empty and "row_type" in exposure.columns else pd.DataFrame()
    summary_row = summary.iloc[0].to_dict() if not summary.empty else {}
    warnings = _json_list(summary_row.get("warnings_json", "[]"))
    etf_type = str(classification.get("etf_type") or _type_for(symbol, name))
    group = str(classification.get("group") or (candidate or {}).get("group", ""))
    missing_broad = any("暂无宽基" in item for item in warnings)
    high_beta_warning = any("high_beta" in item or "高 beta" in item for item in warnings)
    financial_or_cycle = group in {"金融地产", "周期资源"} or any(key in name for key in ["银行", "证券", "券商", "煤炭", "资源"])

    balance = ""
    concentration = ""
    if missing_broad and etf_type == "broad_index":
        balance = "当前组合缺少宽基，该候选具备组合平衡价值。"
    elif missing_broad:
        balance = "当前组合缺少宽基，本候选不能改善宽基缺口。"
    if (high_beta_warning or etf_type == "high_beta" or financial_or_cycle) and (etf_type == "high_beta" or financial_or_cycle):
        concentration = "当前组合已有金融/周期/高 beta 暴露，新增同类 ETF 可能加剧集中度。"
    context = "; ".join(warnings[:3]) if warnings else "no_major_exposure_warning"
    candidate_context = balance or concentration or "组合暴露仅提示，不阻断交易。"
    return {
        "portfolio_exposure_status": summary_row.get("overall_status", ""),
        "portfolio_balance_suggestion": balance,
        "concentration_warning": concentration,
        "exposure_context": context,
        "buy_candidate_context": candidate_context,
    }


def _research_confidence() -> str:
    data = _read_json(QUALITY_REVIEW_FILE)
    if not data:
        return "holding_period=MEDIUM; exit_rule=LOW_MEDIUM; parameter_sweep=LOW_MEDIUM; market_state=MEDIUM"
    return "; ".join(
        [
            f"holding_period={data.get('holding_period', {}).get('quality', 'N/A')}",
            f"exit_rule={data.get('exit_rule', {}).get('quality', 'N/A')}",
            f"parameter_sweep={data.get('parameter_sweep', {}).get('quality', 'N/A')}",
            f"market_state={data.get('market_state', {}).get('quality', 'N/A')}",
            "phase2c=light_integration_only",
        ]
    )


def _position_row(positions: pd.DataFrame, symbol: str) -> dict:
    if positions.empty or "symbol" not in positions.columns:
        return {}
    matched = positions[positions["symbol"].astype(str) == str(symbol)]
    return matched.iloc[0].to_dict() if not matched.empty else {}


def _json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except Exception:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _read_json(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _trade_cost(action: str, raw_close: float, quantity: int) -> dict:
    action = str(action).upper()
    raw_close = float(raw_close or 0.0)
    quantity = int(quantity or 0)
    if raw_close <= 0 or quantity <= 0:
        return _zero_trade_cost(action, raw_close, quantity)
    if action == "BUY":
        execution_price = raw_close * (1 + PAPER_SLIPPAGE_RATE)
        gross_amount = execution_price * quantity
        commission = max(gross_amount * PAPER_COMMISSION_RATE, PAPER_MIN_COMMISSION)
        stamp_tax = 0.0
        transfer_fee = gross_amount * PAPER_TRANSFER_FEE_RATE
        net_cash_change = -(gross_amount + commission + transfer_fee)
    else:
        execution_price = raw_close * (1 - PAPER_SLIPPAGE_RATE)
        gross_amount = execution_price * quantity
        commission = max(gross_amount * PAPER_COMMISSION_RATE, PAPER_MIN_COMMISSION)
        stamp_tax = gross_amount * PAPER_STAMP_TAX_RATE
        transfer_fee = gross_amount * PAPER_TRANSFER_FEE_RATE
        net_cash_change = gross_amount - commission - stamp_tax - transfer_fee
    return {
        "action": action,
        "raw_close": round(raw_close, 6),
        "execution_price": round(execution_price, 6),
        "quantity": quantity,
        "gross_amount": round(gross_amount, 2),
        "commission": round(commission, 2),
        "stamp_tax": round(stamp_tax, 2),
        "transfer_fee": round(transfer_fee, 2),
        "net_cash_change": round(net_cash_change, 2),
        "slippage_rate": PAPER_SLIPPAGE_RATE,
    }


def _zero_trade_cost(action: str, raw_close: float = 0.0, quantity: int = 0) -> dict:
    raw_close = float(raw_close or 0.0)
    return {
        "action": str(action).upper(),
        "raw_close": round(raw_close, 6),
        "execution_price": round(raw_close, 6),
        "quantity": int(quantity or 0),
        "gross_amount": 0.0,
        "commission": 0.0,
        "stamp_tax": 0.0,
        "transfer_fee": 0.0,
        "net_cash_change": 0.0,
        "slippage_rate": PAPER_SLIPPAGE_RATE,
    }


def _affordable_lot_quantity(target_amount: float, raw_close: float, cash: float) -> tuple[int, dict]:
    if target_amount <= 0 or raw_close <= 0 or cash <= PAPER_MIN_COMMISSION:
        return 0, _zero_trade_cost("BUY", raw_close, 0)
    max_gross_budget = min(float(target_amount), float(cash) - PAPER_MIN_COMMISSION)
    execution_price = raw_close * (1 + PAPER_SLIPPAGE_RATE)
    quantity = int((max_gross_budget / execution_price) // PAPER_LOT_SIZE * PAPER_LOT_SIZE)
    while quantity > 0:
        cost = _trade_cost("BUY", raw_close, quantity)
        if cash + cost["net_cash_change"] >= -0.0001:
            return quantity, cost
        quantity -= PAPER_LOT_SIZE
    return 0, _zero_trade_cost("BUY", raw_close, 0)


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
    df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns].copy()
    return df


def _normalize_trades(df: pd.DataFrame) -> pd.DataFrame:
    for col in TRADE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if df.empty:
        return df[TRADE_COLUMNS].copy()
    df["date"] = df["date"].where(df["date"].astype(str).str.strip() != "", df.get("trade_date", ""))
    df["trade_date"] = df["trade_date"].where(df["trade_date"].astype(str).str.strip() != "", df["date"])
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["action"] = df["action"].astype(str).str.upper().str.strip()
    numeric_defaults = {
        "price": 0.0,
        "raw_close": None,
        "execution_price": None,
        "quantity": 0.0,
        "gross_amount": None,
        "commission": None,
        "stamp_tax": 0.0,
        "transfer_fee": 0.0,
        "net_cash_change": None,
        "slippage_rate": 0.0,
        "holding_days": 0.0,
        "realized_pnl": 0.0,
        "realized_pnl_pct": 0.0,
        "cash_after_trade": None,
        "position_value_after_trade": None,
        "total_equity_after_trade": None,
        "amount": None,
        "fee": None,
        "simulated_cash": None,
        "position_value": None,
        "total_equity": None,
    }
    for col, fallback in numeric_defaults.items():
        values = pd.to_numeric(df[col], errors="coerce")
        if fallback is not None:
            values = values.fillna(fallback)
        df[col] = values
    df["raw_close"] = df["raw_close"].fillna(df["price"])
    df["execution_price"] = df["execution_price"].fillna(df["price"])
    df["gross_amount"] = df["gross_amount"].fillna(df["amount"]).fillna(df["execution_price"] * df["quantity"])
    df["commission"] = df["commission"].fillna(df["fee"]).fillna(0.0)
    df["fee"] = df["fee"].fillna(df["commission"]).fillna(0.0)
    df["amount"] = df["amount"].fillna(df["gross_amount"]).fillna(0.0)
    buy_mask = df["action"].eq("BUY")
    sell_mask = df["action"].eq("SELL")
    missing_buy_cash_mask = buy_mask & df["net_cash_change"].isna()
    missing_sell_cash_mask = sell_mask & df["net_cash_change"].isna()
    df.loc[missing_buy_cash_mask, "net_cash_change"] = -(
        df.loc[missing_buy_cash_mask, "gross_amount"]
        + df.loc[missing_buy_cash_mask, "commission"]
        + df.loc[missing_buy_cash_mask, "transfer_fee"]
    )
    df.loc[missing_sell_cash_mask, "net_cash_change"] = (
        df.loc[missing_sell_cash_mask, "gross_amount"]
        - df.loc[missing_sell_cash_mask, "commission"]
        - df.loc[missing_sell_cash_mask, "stamp_tax"]
        - df.loc[missing_sell_cash_mask, "transfer_fee"]
    )
    df["net_cash_change"] = df["net_cash_change"].fillna(0.0)
    df["execution_price_type"] = df["execution_price_type"].where(df["execution_price_type"].astype(str).str.strip() != "", PAPER_EXECUTION_PRICE_TYPE)
    df["source"] = df["source"].where(df["source"].astype(str).str.strip() != "", "paper_trade_engine")
    df["created_at"] = df["created_at"].where(df["created_at"].astype(str).str.strip() != "", "")
    df["order_type"] = df["order_type"].where(df["order_type"].astype(str).str.strip() != "", "paper_" + df["action"].astype(str).str.lower())
    df["is_simulated"] = df["is_simulated"].where(df["is_simulated"].astype(str).str.strip() != "", "1")
    df["cash_after_trade"] = df["cash_after_trade"].fillna(df["simulated_cash"])
    df["position_value_after_trade"] = df["position_value_after_trade"].fillna(df["position_value"])
    df["total_equity_after_trade"] = df["total_equity_after_trade"].fillna(df["total_equity"])
    df["simulated_cash"] = df["simulated_cash"].fillna(df["cash_after_trade"])
    df["position_value"] = df["position_value"].fillna(df["position_value_after_trade"])
    df["total_equity"] = df["total_equity"].fillna(df["total_equity_after_trade"])
    return df[TRADE_COLUMNS].copy()


def _normalize_positions(df: pd.DataFrame) -> pd.DataFrame:
    for col in POSITION_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if df.empty:
        return df[POSITION_COLUMNS].copy()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    for col in [
        "quantity",
        "avg_cost",
        "raw_cost",
        "total_cost",
        "commission_paid",
        "last_price",
        "market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "holding_days",
        "max_holding_days",
        "stop_loss_price",
        "distance_to_stop_pct",
        "entry_price",
        "cost",
        "stop_loss",
        "current_price",
        "unrealized_return",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["avg_cost"] = df["avg_cost"].fillna(df["entry_price"])
    df["raw_cost"] = df["raw_cost"].fillna(df["cost"]).fillna(df["avg_cost"] * df["quantity"])
    df["total_cost"] = df["total_cost"].fillna(df["cost"]).fillna(df["raw_cost"] + df["commission_paid"].fillna(0.0))
    df["commission_paid"] = df["commission_paid"].fillna(0.0)
    df["last_price"] = df["last_price"].fillna(df["current_price"]).fillna(df["entry_price"])
    df["stop_loss_price"] = df["stop_loss_price"].fillna(df["stop_loss"])
    df["entry_price"] = df["entry_price"].fillna(df["avg_cost"])
    df["cost"] = df["cost"].fillna(df["total_cost"])
    df["stop_loss"] = df["stop_loss"].fillna(df["stop_loss_price"])
    df["current_price"] = df["current_price"].fillna(df["last_price"])
    df["unrealized_return"] = df["unrealized_return"].fillna(df["unrealized_pnl_pct"])
    df["etf_type"] = df.apply(lambda row: _type_for(str(row["symbol"]), str(row["name"])) if _is_blank(row.get("etf_type")) else str(row.get("etf_type")), axis=1)
    df["group"] = df["group"].where(~df["group"].apply(_is_blank), "")
    df["max_holding_days"] = df["max_holding_days"].fillna(df["etf_type"].map(lambda x: _max_holding_days(str(x))))
    df["sell_review_status"] = df["sell_review_status"].where(~df["sell_review_status"].apply(_is_blank), "N/A")
    df["data_health_status"] = df["data_health_status"].where(~df["data_health_status"].apply(_is_blank), "N/A")
    df["protection_period"] = df["protection_period"].where(~df["protection_period"].apply(_is_blank), "no")
    df["updated_at"] = df["updated_at"].where(~df["updated_at"].apply(_is_blank), "")
    return df[POSITION_COLUMNS].copy()


def _is_blank(value: object) -> bool:
    text = str(value).strip().lower()
    return text in {"", "nan", "none", "nat"}


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
            action = str(row.get("action", "")).upper()
            net_change = _float(row.get("net_cash_change"), float("nan"))
            if pd.isna(net_change):
                amount = _float(row.get("amount"))
                fee = _float(row.get("fee"))
                net_change = -(amount + fee) if action == "BUY" else amount - fee if action == "SELL" else 0.0
            cash += net_change
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
        price = _latest_close(symbol) or _float(row.get("last_price"), _float(row.get("current_price"), _float(row.get("entry_price"))))
        qty = _float(row.get("quantity"))
        cost = _float(row.get("total_cost"), _float(row.get("cost"), _float(row.get("entry_price")) * qty))
        stop_loss = _float(row.get("stop_loss_price"), _float(row.get("stop_loss")))
        entry_date = pd.to_datetime(row.get("entry_date"), errors="coerce")
        holding_days = 0 if pd.isna(entry_date) else (pd.to_datetime(run_date) - entry_date).days
        market_value = price * qty
        pnl = market_value - cost
        etf_type = _type_for(symbol, str(row.get("name", symbol))) if _is_blank(row.get("etf_type")) else str(row.get("etf_type"))
        df.loc[idx, "last_price"] = price
        df.loc[idx, "market_value"] = round(market_value, 2)
        df.loc[idx, "unrealized_pnl"] = round(pnl, 2)
        df.loc[idx, "unrealized_pnl_pct"] = pnl / cost if cost else 0.0
        df.loc[idx, "holding_days"] = holding_days
        df.loc[idx, "etf_type"] = etf_type
        df.loc[idx, "max_holding_days"] = _float(row.get("max_holding_days"), _max_holding_days(etf_type))
        df.loc[idx, "stop_loss_price"] = stop_loss
        df.loc[idx, "distance_to_stop_pct"] = (price - stop_loss) / price if price and stop_loss else 0.0
        df.loc[idx, "protection_period"] = "yes" if holding_days <= 2 else "no"
        df.loc[idx, "updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[idx, "current_price"] = price
        df.loc[idx, "unrealized_return"] = df.loc[idx, "unrealized_pnl_pct"]
        df.loc[idx, "risk_alert"] = "触及或低于模拟止损价" if stop_loss and price <= stop_loss else ""
    return df[POSITION_COLUMNS].copy()


def _positions_value(positions: pd.DataFrame) -> float:
    if positions.empty:
        return 0.0
    if "market_value" in positions.columns:
        values = pd.to_numeric(positions["market_value"], errors="coerce")
        if values.notna().any():
            return float(values.fillna(0).sum())
    return sum((_latest_close(str(row.get("symbol", ""))) or _float(row.get("last_price"), _float(row.get("current_price")))) * _float(row.get("quantity")) for row in positions.to_dict(orient="records"))


def _positions_cost(positions: pd.DataFrame) -> float:
    if positions.empty:
        return 0.0
    series = pd.to_numeric(positions.get("total_cost", positions.get("cost", pd.Series(dtype=float))), errors="coerce")
    return float(series.fillna(0).sum())


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


def _engine_run_date() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d")


def _target_position_pct() -> float:
    if PAPER_DEFAULT_MARKET_STATE == "strong":
        return PAPER_TARGET_POSITION_STRONG
    if PAPER_DEFAULT_MARKET_STATE == "weak":
        return PAPER_TARGET_POSITION_WEAK
    return PAPER_TARGET_POSITION_NEUTRAL


def _pool_for(symbol: str, watchlist: pd.DataFrame, classification: pd.DataFrame) -> str:
    for df, code_col, pool_col in [(watchlist, "code", "role"), (classification, "symbol", "pool"), (classification, "code", "pool")]:
        if not df.empty and code_col in df.columns:
            matched = df[df[code_col].astype(str) == symbol]
            if not matched.empty:
                return str(matched.iloc[0].get(pool_col, ""))
    return ""


def _type_for(symbol: str, name: str) -> str:
    classification = _read_classification()
    if not classification.empty:
        for col in ["symbol", "code"]:
            if col in classification.columns:
                matched = classification[classification[col].astype(str) == symbol]
                if not matched.empty:
                    if symbol == "515880":
                        return "high_beta"
                    return str(matched.iloc[0].get("etf_type", "sector"))
    if symbol == "515880" or "证券" in name:
        return "high_beta"
    return "sector"


def _stop_pct(etf_type: str) -> float:
    return {"broad_index": 0.08, "sector": 0.06, "theme": 0.05, "hot_theme": 0.05, "high_beta": 0.05, "commodity_resource": 0.06, "bond_cash": 0.02, "qdii": 0.06}.get(etf_type, 0.06)


def _max_holding_days(etf_type: str) -> int:
    return {
        "broad_index": 60,
        "sector": 30,
        "commodity_resource": 30,
        "theme": 20,
        "hot_theme": 10,
        "high_beta": 20,
        "bond_cash": 90,
        "qdii": 45,
    }.get(str(etf_type), 30)


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


def _pct_text(value: object) -> str:
    numeric = _float(value, float("nan"))
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2%}"


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
