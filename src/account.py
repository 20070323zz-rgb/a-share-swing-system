"""模拟账户：只读取手工模拟成交，不连接真实交易。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import (
    ETF_STOP_LOSS,
    INITIAL_CASH,
    LOT_SIZE,
    MAX_ETF_POSITIONS,
    MAX_POSITION_VALUE,
    MAX_RISK_PER_TRADE,
    MAX_STOCK_POSITIONS,
    MIN_CASH,
    STOCK_STOP_LOSS,
)


@dataclass
class Position:
    code: str
    name: str
    type: str
    shares: float
    avg_price: float
    buy_date: pd.Timestamp
    highest_close: float


class SimAccount:
    """根据 trades.csv 重建模拟账户。"""

    def __init__(self, trades: pd.DataFrame) -> None:
        self.initial_cash = INITIAL_CASH
        self.cash = INITIAL_CASH
        self.positions: dict[str, Position] = {}
        self.realized_trades: list[dict] = []
        self._replay_trades(trades)

    def _replay_trades(self, trades: pd.DataFrame) -> None:
        """按时间顺序回放模拟成交。"""
        for _, trade in trades.sort_values("date").iterrows():
            action = str(trade["action"]).upper()
            code = str(trade["code"])
            price = float(trade["price"])
            shares = float(trade["shares"])
            amount = float(trade["amount"]) if trade["amount"] else price * shares
            fee = float(trade["fee"])

            if action == "BUY":
                self.cash -= amount + fee
                self._add_position(trade, amount, shares, price)
            elif action == "SELL":
                self.cash += amount - fee
                self._reduce_position(trade, amount, shares, price, fee)

    def _add_position(self, trade: pd.Series, amount: float, shares: float, price: float) -> None:
        code = str(trade["code"])
        if code not in self.positions:
            self.positions[code] = Position(
                code=code,
                name=str(trade.get("name", code)),
                type=str(trade.get("type", "ETF")).upper(),
                shares=shares,
                avg_price=price,
                buy_date=trade["date"],
                highest_close=price,
            )
            return

        pos = self.positions[code]
        old_cost = pos.avg_price * pos.shares
        new_shares = pos.shares + shares
        pos.avg_price = (old_cost + amount) / new_shares if new_shares else 0.0
        pos.shares = new_shares
        pos.buy_date = min(pos.buy_date, trade["date"])
        pos.highest_close = max(pos.highest_close, price)

    def _reduce_position(self, trade: pd.Series, amount: float, shares: float, price: float, fee: float) -> None:
        code = str(trade["code"])
        pos = self.positions.get(code)
        if pos is None:
            return

        sell_shares = min(shares, pos.shares)
        cost = pos.avg_price * sell_shares
        realized_pnl = price * sell_shares - cost - fee
        self.realized_trades.append(
            {
                "date": trade["date"],
                "code": code,
                "name": pos.name,
                "action": "SELL",
                "amount": amount,
                "realized_pnl": realized_pnl,
                "return": realized_pnl / cost if cost else 0.0,
            }
        )

        pos.shares -= sell_shares
        if pos.shares <= 0:
            del self.positions[code]

    def update_highest_close(self, price_history: dict[str, pd.DataFrame], run_date: pd.Timestamp) -> None:
        """用买入日至运行日之间的最高收盘价更新移动止盈参考价。"""
        for code, pos in self.positions.items():
            df = price_history.get(code)
            if df is None or df.empty:
                continue
            window = df[(df["date"] >= pos.buy_date) & (df["date"] <= run_date)]
            if not window.empty:
                pos.highest_close = max(pos.highest_close, float(window["close"].max()))

    def market_value(self, latest_prices: dict[str, float]) -> float:
        """按最新收盘价计算持仓市值。"""
        total = 0.0
        for code, pos in self.positions.items():
            total += pos.shares * latest_prices.get(code, pos.avg_price)
        return total

    def total_assets(self, latest_prices: dict[str, float]) -> float:
        return self.cash + self.market_value(latest_prices)

    def current_position_count(self, type_name: str) -> int:
        return sum(1 for pos in self.positions.values() if pos.type == type_name.upper())

    def suggested_position(self, code: str, type_name: str, price: float, stop_loss_price: float, latest_prices: dict[str, float]) -> dict:
        """根据风险、现金、仓位上限和持仓数量计算建议买入金额。"""
        type_name = type_name.upper()
        if code in self.positions:
            return _blocked_position("已有持仓，第一版不做自动加仓")

        if type_name == "ETF" and self.current_position_count("ETF") >= MAX_ETF_POSITIONS:
            return _blocked_position("ETF 持仓数量已满")
        if type_name == "STOCK" and self.current_position_count("STOCK") >= MAX_STOCK_POSITIONS:
            return _blocked_position("个股持仓数量已满")

        current_position_value = self.market_value(latest_prices)
        available_by_cash = max(0.0, self.cash - MIN_CASH)
        available_by_total_position = max(0.0, MAX_POSITION_VALUE - current_position_value)
        risk_per_share = max(0.0, price - stop_loss_price)

        if available_by_cash <= 0:
            return _blocked_position("现金不足，买入后会低于最低现金")
        if available_by_total_position <= 0:
            return _blocked_position("总仓位已达到上限")
        if risk_per_share <= 0:
            return _blocked_position("止损价不低于现价，无法计算风险")

        shares_by_risk = MAX_RISK_PER_TRADE / risk_per_share
        raw_amount = min(available_by_cash, available_by_total_position, shares_by_risk * price)
        shares = int(raw_amount / price / LOT_SIZE) * LOT_SIZE
        amount = shares * price
        if shares <= 0:
            return _blocked_position("按 100 股/份一手计算后，资金不足一手")

        return {
            "allowed": True,
            "reason": "",
            "suggested_amount": round(amount, 2),
            "suggested_shares": shares,
        }


def stop_loss_rate(type_name: str) -> float:
    return ETF_STOP_LOSS if type_name.upper() == "ETF" else STOCK_STOP_LOSS


def _blocked_position(reason: str) -> dict:
    return {
        "allowed": False,
        "reason": reason,
        "suggested_amount": 0.0,
        "suggested_shares": 0,
    }
