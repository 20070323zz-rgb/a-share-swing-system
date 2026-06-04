"""信号生成模块：根据策略规则输出买入、卖出、持有或观望。"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from config import (
    EXTREME_VOLUME_RATIO,
    MAX_20D_RETURN_TO_CHASE,
    MAX_5D_RETURN_TO_CHASE,
    MAX_5D_RETURN_SHORT_SWING,
    MAX_DISTANCE_ABOVE_MA20,
    MAX_DISTANCE_ABOVE_MA10,
    PROFIT_ACTIVATE_TRAILING,
    SHORT_SWING_MAX_HOLDING_DAYS,
    SHORT_SWING_PROFIT_ACTIVATE_TRAILING,
    SHORT_SWING_STOP_LOSS,
    SHORT_SWING_TRAILING_DRAWDOWN,
    TRAILING_DRAWDOWN,
    VOLUME_RATIO_MAX,
    VOLUME_RATIO_MIN,
)
from portfolio import Position, SimAccount, stop_loss_rate


@dataclass
class Signal:
    date: str
    code: str
    name: str
    type: str
    group: str
    role: str
    enabled: bool
    signal: str
    close: float
    reasons: str
    block_reasons: str
    stop_loss_price: float
    suggested_amount: float
    suggested_shares: int

    def to_dict(self) -> dict:
        """转成字典，方便保存到 CSV。"""
        return asdict(self)


def make_signal(
    row: pd.Series | None,
    meta: pd.Series,
    account: SimAccount,
    latest_prices: dict[str, float],
    run_date: str,
    strategy: str = "mid_trend",
) -> Signal:
    """为单个标的生成 BUY、SELL、HOLD、WATCH 或 NO_DATA 信号。"""
    code = str(meta["code"])
    name = str(meta["name"])
    type_name = str(meta["type"]).upper()
    group = str(meta.get("group", "未分类"))
    role = str(meta.get("role", "trade_pool"))
    enabled = bool(meta.get("enabled", True))

    if row is None:
        return Signal(run_date, code, name, type_name, group, role, enabled, "NO_DATA", 0.0, "", "缺少本地行情数据", 0.0, 0.0, 0)

    close = float(row["close"])
    signal_date = row["date"].strftime("%Y-%m-%d")
    position = account.positions.get(code)
    if strategy == "short_swing":
        if position:
            return _short_swing_sell_or_hold_signal(row, position, meta, latest_prices)
        return _short_swing_buy_or_watch_signal(row, meta, account, latest_prices, signal_date, close)

    if position:
        return _sell_or_hold_signal(row, position, meta, latest_prices)

    return _buy_or_watch_signal(row, meta, account, latest_prices, signal_date, close)


def _buy_or_watch_signal(
    row: pd.Series,
    meta: pd.Series,
    account: SimAccount,
    latest_prices: dict[str, float],
    run_date: str,
    close: float,
) -> Signal:
    """检查趋势、相对强弱、成交量和追高过滤，决定是否进入候选买入。"""
    code = str(meta["code"])
    name = str(meta["name"])
    type_name = str(meta["type"]).upper()
    group = str(meta.get("group", "未分类"))
    role = str(meta.get("role", "trade_pool"))
    enabled = bool(meta.get("enabled", True))
    reasons: list[str] = []
    blocks: list[str] = []

    _check(row["close"] > row["ma20"], "收盘价站上 MA20", "收盘价未站上 MA20", reasons, blocks)
    _check(row["close"] > row["ma60"], "收盘价站上 MA60", "收盘价未站上 MA60", reasons, blocks)
    _check(row["ma20_slope"] > 0, "MA20 向上", "MA20 没有向上", reasons, blocks)
    _check(row["relative_strength"] > 0, "20 日涨幅强于基准", "20 日相对强弱不足", reasons, blocks)
    _check(
        VOLUME_RATIO_MIN <= row["volume_ratio"] <= VOLUME_RATIO_MAX,
        "成交量温和放大",
        "成交量没有温和放大",
        reasons,
        blocks,
    )
    _check(
        row["max_volume_ratio_20"] <= EXTREME_VOLUME_RATIO,
        "最近 20 日无极端爆量",
        "最近 20 日出现极端爆量",
        reasons,
        blocks,
    )
    _check(row["ret20"] <= MAX_20D_RETURN_TO_CHASE, "20 日涨幅未过热", "20 日涨幅过大，避免追高", reasons, blocks)
    _check(row["ret5"] <= MAX_5D_RETURN_TO_CHASE, "5 日涨幅未过热", "5 日连续涨幅过大，避免追高", reasons, blocks)
    _check(
        row["distance_above_ma20"] <= MAX_DISTANCE_ABOVE_MA20,
        "价格距离 MA20 不远",
        "价格距离 MA20 过远，避免追高",
        reasons,
        blocks,
    )

    stop_loss_price = close * (1 - stop_loss_rate(type_name))
    position_plan = account.suggested_position(code, type_name, close, stop_loss_price, latest_prices)
    if not position_plan["allowed"]:
        blocks.append(position_plan["reason"])

    signal = "BUY" if not blocks else "WATCH"
    return Signal(
        date=run_date,
        code=code,
        name=name,
        type=type_name,
        group=group,
        role=role,
        enabled=enabled,
        signal=signal,
        close=round(close, 4),
        reasons="；".join(reasons),
        block_reasons="；".join(blocks),
        stop_loss_price=round(stop_loss_price, 4),
        suggested_amount=position_plan["suggested_amount"],
        suggested_shares=position_plan["suggested_shares"],
    )


def _sell_or_hold_signal(row: pd.Series, position: Position, meta: pd.Series, latest_prices: dict[str, float]) -> Signal:
    """对已有持仓检查止损、跌破 MA60 和移动止盈。"""
    close = float(row["close"])
    run_date = row["date"].strftime("%Y-%m-%d")
    name = str(meta["name"])
    group = str(meta.get("group", "未分类"))
    role = str(meta.get("role", "trade_pool"))
    enabled = bool(meta.get("enabled", True))
    stop_loss_price = position.avg_price * (1 - stop_loss_rate(position.type))
    profit = close / position.avg_price - 1
    drawdown_from_high = close / position.highest_close - 1 if position.highest_close else 0.0

    reasons: list[str] = []
    blocks: list[str] = []
    sell_reasons: list[str] = []

    if close <= stop_loss_price:
        sell_reasons.append("触发买入价止损")
    if close < row["ma60"]:
        sell_reasons.append("跌破 MA60，按规则清仓")
    if profit >= PROFIT_ACTIVATE_TRAILING and drawdown_from_high <= -TRAILING_DRAWDOWN:
        sell_reasons.append("盈利超过 15% 后从高点回撤触发移动止盈")

    if sell_reasons:
        signal = "SELL"
        reasons = sell_reasons
    else:
        signal = "HOLD"
        reasons.append("已有持仓，未触发卖出规则")
        if profit >= PROFIT_ACTIVATE_TRAILING:
            reasons.append("盈利超过 15%，继续跟踪移动止盈")

    market_value = position.shares * latest_prices.get(position.code, close)
    return Signal(
        date=run_date,
        code=position.code,
        name=name,
        type=position.type,
        group=group,
        role=role,
        enabled=enabled,
        signal=signal,
        close=round(close, 4),
        reasons="；".join(reasons),
        block_reasons="；".join(blocks),
        stop_loss_price=round(stop_loss_price, 4),
        suggested_amount=round(market_value, 2) if signal == "SELL" else 0.0,
        suggested_shares=int(position.shares) if signal == "SELL" else 0,
    )


def _short_swing_buy_or_watch_signal(
    row: pd.Series,
    meta: pd.Series,
    account: SimAccount,
    latest_prices: dict[str, float],
    run_date: str,
    close: float,
) -> Signal:
    """短期波段实验策略：使用 MA10/MA20 和 10 日相对强弱。"""
    code = str(meta["code"])
    name = str(meta["name"])
    type_name = str(meta["type"]).upper()
    group = str(meta.get("group", "未分类"))
    role = str(meta.get("role", "trade_pool"))
    enabled = bool(meta.get("enabled", True))
    reasons: list[str] = []
    blocks: list[str] = []

    _check(row["close"] > row["ma10"], "收盘价站上 MA10", "收盘价未站上 MA10", reasons, blocks)
    _check(row["close"] > row["ma20"], "收盘价站上 MA20", "收盘价未站上 MA20", reasons, blocks)
    _check(row["ma10_slope"] > 0, "MA10 向上", "MA10 没有向上", reasons, blocks)
    _check(row["relative_strength_10"] > 0, "10 日涨幅强于基准", "10 日相对强弱不足", reasons, blocks)
    _check(VOLUME_RATIO_MIN <= row["volume_ratio"] <= VOLUME_RATIO_MAX, "成交量温和放大", "成交量没有温和放大", reasons, blocks)
    _check(row["ret5"] <= MAX_5D_RETURN_SHORT_SWING, "5 日涨幅未过热", "5 日涨幅过大，避免短线追高", reasons, blocks)
    _check(row["distance_above_ma10"] <= MAX_DISTANCE_ABOVE_MA10, "价格距离 MA10 不远", "价格距离 MA10 过远，避免追高", reasons, blocks)

    stop_loss_price = close * (1 - SHORT_SWING_STOP_LOSS)
    position_plan = account.suggested_position(code, type_name, close, stop_loss_price, latest_prices)
    if not position_plan["allowed"]:
        blocks.append(position_plan["reason"])

    signal = "BUY" if not blocks else "WATCH"
    return Signal(
        date=run_date,
        code=code,
        name=name,
        type=type_name,
        group=group,
        role=role,
        enabled=enabled,
        signal=signal,
        close=round(close, 4),
        reasons="；".join(reasons),
        block_reasons="；".join(blocks),
        stop_loss_price=round(stop_loss_price, 4),
        suggested_amount=position_plan["suggested_amount"],
        suggested_shares=position_plan["suggested_shares"],
    )


def _short_swing_sell_or_hold_signal(row: pd.Series, position: Position, meta: pd.Series, latest_prices: dict[str, float]) -> Signal:
    """短期波段卖出规则，目标更快退出。"""
    close = float(row["close"])
    run_date = row["date"].strftime("%Y-%m-%d")
    group = str(meta.get("group", "未分类"))
    role = str(meta.get("role", "trade_pool"))
    enabled = bool(meta.get("enabled", True))
    stop_loss_price = position.avg_price * (1 - SHORT_SWING_STOP_LOSS)
    profit = close / position.avg_price - 1
    drawdown_from_high = close / position.highest_close - 1 if position.highest_close else 0.0
    holding_days = (row["date"] - position.buy_date).days if hasattr(row["date"], "to_pydatetime") else 0

    sell_reasons: list[str] = []
    if close < row["ma20"]:
        sell_reasons.append("跌破 MA20，短期策略退出")
    if close < row["ma10"] and row["relative_strength_10"] <= 0:
        sell_reasons.append("跌破 MA10 且 10 日相对强弱转弱")
    if close <= stop_loss_price:
        sell_reasons.append("短期策略触发 5% 附近止损")
    if profit >= SHORT_SWING_PROFIT_ACTIVATE_TRAILING and drawdown_from_high <= -SHORT_SWING_TRAILING_DRAWDOWN:
        sell_reasons.append("盈利超过 8% 后从高点回撤触发短期移动止盈")
    if holding_days > SHORT_SWING_MAX_HOLDING_DAYS and row["relative_strength_10"] <= 0:
        sell_reasons.append("持仓超过 20 个交易日且短期信号转弱")

    signal = "SELL" if sell_reasons else "HOLD"
    reasons = sell_reasons if sell_reasons else ["短期持仓未触发卖出规则"]
    market_value = position.shares * latest_prices.get(position.code, close)
    return Signal(
        date=run_date,
        code=position.code,
        name=str(meta["name"]),
        type=position.type,
        group=group,
        role=role,
        enabled=enabled,
        signal=signal,
        close=round(close, 4),
        reasons="；".join(reasons),
        block_reasons="",
        stop_loss_price=round(stop_loss_price, 4),
        suggested_amount=round(market_value, 2) if signal == "SELL" else 0.0,
        suggested_shares=int(position.shares) if signal == "SELL" else 0,
    )


def _check(condition: bool, ok_reason: str, block_reason: str, reasons: list[str], blocks: list[str]) -> None:
    """把每条策略规则转成报告中能直接复盘的文字原因。"""
    if pd.isna(condition) or not bool(condition):
        blocks.append(block_reason)
    else:
        reasons.append(ok_reason)
