"""历史回测模块：只使用本地 CSV 做模拟，不包含真实交易接口。"""

from __future__ import annotations

import argparse

import pandas as pd

from config import BACKTEST_RESULT_FILE, BACKTEST_SUMMARY_FILE, BENCHMARK_CODE, DATA_DIR, INITIAL_CASH, REPORT_DIR, STRATEGY_COMPARE_REPORT_FILE, WATCHLIST_FILE
from data_loader import load_price_data, read_watchlist
from indicators import add_indicators
from portfolio import SimAccount, calculate_max_drawdown
from signal_engine import make_signal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A 股周线波段策略历史回测")
    parser.add_argument("--code", help="要回测的证券代码，例如 510300")
    parser.add_argument("--benchmark-code", default=BENCHMARK_CODE, help="基准代码，默认 510300")
    parser.add_argument("--strategy", choices=["mid_trend", "short_swing"], default="mid_trend", help="回测策略，默认 mid_trend。")
    parser.add_argument("--all", action="store_true", help="批量回测默认 ETF 列表。")
    parser.add_argument("--compare-strategies", action="store_true", help="批量比较 mid_trend 和 short_swing。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if args.all and args.compare_strategies:
        summaries = run_strategy_comparison(args.benchmark_code)
        write_strategy_compare_report(summaries)
        print(f"已生成策略对比报告：{STRATEGY_COMPARE_REPORT_FILE}")
        print("回测只使用本地行情 CSV，不包含任何真实交易或下单功能。")
        return
    if not args.code:
        raise SystemExit("请提供 --code，或使用 --all --compare-strategies。")
    summary, trades = run_backtest(args.code, args.benchmark_code, args.strategy)
    write_backtest_outputs(summary, trades)
    print(f"已生成回测交易明细：{BACKTEST_RESULT_FILE}")
    print(f"已生成回测摘要：{BACKTEST_SUMMARY_FILE}")
    print("回测只使用本地行情 CSV，不包含任何真实交易或下单功能。")


def run_backtest(code: str, benchmark_code: str = BENCHMARK_CODE, strategy: str = "mid_trend") -> tuple[dict, pd.DataFrame]:
    """读取本地行情并按 signal_engine 规则执行单标的历史回测。"""
    watchlist = read_watchlist(WATCHLIST_FILE)
    meta = _find_meta(watchlist, code).copy()
    meta["strategy"] = strategy
    raw, warning = load_price_data(DATA_DIR, code)
    if raw is None:
        return _empty_summary(code, warning or "缺少行情数据"), pd.DataFrame()

    benchmark_raw, benchmark_warning = load_price_data(DATA_DIR, benchmark_code)
    benchmark_with_indicators = add_indicators(benchmark_raw) if benchmark_raw is not None else None
    data = add_indicators(raw, benchmark_with_indicators)

    trades = []
    closed_trades = []
    equity_curve = []

    for _, row in data.iterrows():
        run_date = row["date"].strftime("%Y-%m-%d")
        account = SimAccount(_trades_dataframe(trades))
        account.update_highest_close({code: data[data["date"] <= row["date"]]}, row["date"])
        latest_prices = {code: float(row["close"])}
        signal = make_signal(row, meta, account, latest_prices, run_date, strategy=strategy)

        if signal.signal == "BUY" and signal.suggested_shares > 0:
            _append_trade(trades, run_date, meta, "BUY", signal.close, signal.suggested_shares, signal.reasons)
        elif signal.signal == "SELL" and code in account.positions:
            position = account.positions[code]
            _append_trade(trades, run_date, meta, "SELL", signal.close, position.shares, signal.reasons)
            closed_trades.append(_closed_trade_from_pair(trades, code))

        account_after_signal = SimAccount(_trades_dataframe(trades))
        equity_curve.append(
            {
                "date": run_date,
                "total_assets": account_after_signal.total_assets(latest_prices),
                "signal": signal.signal,
            }
        )

    if trades and trades[-1]["action"] == "BUY":
        last_row = data.iloc[-1]
        account = SimAccount(_trades_dataframe(trades))
        if code in account.positions:
            position = account.positions[code]
            _append_trade(
                trades,
                last_row["date"].strftime("%Y-%m-%d"),
                meta,
                "SELL",
                float(last_row["close"]),
                position.shares,
                "回测结束，按最后一个交易日收盘价模拟平仓",
            )
            closed_trades.append(_closed_trade_from_pair(trades, code))

    result_df = pd.DataFrame(closed_trades)
    summary = _build_summary(code, meta, result_df, pd.DataFrame(equity_curve), benchmark_warning)
    summary["strategy"] = strategy
    return summary, result_df


def run_strategy_comparison(benchmark_code: str = BENCHMARK_CODE) -> list[dict]:
    """批量比较中期与短期策略。"""
    codes = ["159915", "512100", "510300", "512480", "512760"]
    summaries = []
    for code in codes:
        for strategy in ["mid_trend", "short_swing"]:
            summary, _ = run_backtest(code, benchmark_code, strategy)
            summaries.append(summary)
    return summaries


def write_backtest_outputs(summary: dict, trades: pd.DataFrame) -> None:
    """保存回测交易明细 CSV 和 Markdown 摘要。"""
    if trades.empty:
        pd.DataFrame(
            columns=[
                "code",
                "name",
                "buy_date",
                "sell_date",
                "buy_price",
                "sell_price",
                "shares",
                "profit",
                "return",
                "holding_days",
                "buy_reason",
                "sell_reason",
            ]
        ).to_csv(BACKTEST_RESULT_FILE, index=False)
    else:
        trades.to_csv(BACKTEST_RESULT_FILE, index=False)

    lines = [
        f"# 回测摘要 {summary['code']} {summary['name']} {summary.get('strategy', 'mid_trend')}",
        "",
        "## 核心结果",
        f"- 总收益率：{summary['total_return']:.2%}",
        f"- 最大回撤：{summary['max_drawdown']:.2%}",
        f"- 胜率：{summary['win_rate']:.2%}",
        f"- 交易次数：{summary['trade_count']}",
        f"- 总持仓天数：{summary['total_holding_days']}",
        f"- 平均持仓天数：{summary['avg_holding_days']:.1f}",
        "",
        "## 数据提示",
        f"- {summary['data_note']}",
        "",
        "## 每笔交易明细",
    ]
    if trades.empty:
        lines.append("- 暂无完成交易。")
    else:
        for _, row in trades.iterrows():
            lines.append(
                f"- {row['buy_date']} 买入，{row['sell_date']} 卖出；"
                f"收益 {row['profit']:.2f} 元，收益率 {row['return']:.2%}，持仓 {row['holding_days']} 天；"
                f"买入原因：{row['buy_reason']}；卖出原因：{row['sell_reason']}"
            )
    lines += [
        "",
        "## 安全说明",
        "- 本回测只读取 data/ 下的本地 CSV。",
        "- 本回测不连接券商、不下单、不保存任何账号密码或 token。",
    ]
    BACKTEST_SUMMARY_FILE.write_text("\n".join(lines), encoding="utf-8")


def write_strategy_compare_report(summaries: list[dict]) -> None:
    """保存 mid_trend 与 short_swing 策略对比报告。"""
    lines = [
        "# 策略对比报告",
        "",
        "本报告只比较本地 CSV 回测结果，不包含任何真实交易接口或下单功能。",
        "",
        "| 代码 | 名称 | 策略 | 总收益率 | 最大回撤 | 胜率 | 交易次数 | 平均持仓天数 | 盈亏比 | 最长连续亏损 | 当前是否持仓 | 周期提示 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for item in summaries:
        avg_days = item["avg_holding_days"]
        strategy = item.get("strategy", "mid_trend")
        if strategy == "short_swing":
            cycle_note = "接近 10-20 天" if 10 <= avg_days <= 20 else "未落在 10-20 天目标附近"
        else:
            cycle_note = "接近 20-60 天" if 20 <= avg_days <= 60 else "未落在 20-60 天目标附近"
        lines.append(
            f"| {item['code']} | {item['name']} | {strategy} | {item['total_return']:.2%} | {item['max_drawdown']:.2%} | "
            f"{item['win_rate']:.2%} | {item['trade_count']} | {avg_days:.1f} | {item.get('profit_loss_ratio', 0.0):.2f} | "
            f"{item.get('max_consecutive_losses', 0)} | {'是' if item.get('has_open_position') else '否'} | {cycle_note} |"
        )
    lines += [
        "",
        "## 结论提示",
        "- short_swing 是实验策略，不替代 mid_trend 主策略。",
        "- 如果平均持仓不符合目标周期，应先记录问题，不要强行调参。",
    ]
    STRATEGY_COMPARE_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _find_meta(watchlist: pd.DataFrame, code: str) -> pd.Series:
    """从观察名单中寻找标的；找不到时使用 ETF 默认信息。"""
    matched = watchlist[watchlist["code"].astype(str) == str(code)]
    if not matched.empty:
        return matched.iloc[0]
    return pd.Series({"code": str(code), "name": str(code), "type": "ETF", "enabled": True, "note": "临时回测标的"})


def _append_trade(trades: list[dict], run_date: str, meta: pd.Series, action: str, price: float, shares: float, reason: str) -> None:
    """把一次模拟成交追加到回测交易流水。"""
    trades.append(
        {
            "date": run_date,
            "code": str(meta["code"]),
            "name": str(meta["name"]),
            "type": str(meta["type"]).upper(),
            "action": action,
            "price": round(float(price), 4),
            "shares": int(shares),
            "amount": round(float(price) * float(shares), 2),
            "fee": 0.0,
            "reason": reason,
            "cash_after": "",
            "position_after": "",
            "is_simulated": True,
            "strategy": str(meta.get("strategy", "mid_trend")),
        }
    )


def _trades_dataframe(trades: list[dict]) -> pd.DataFrame:
    """把回测交易流水转换成 SimAccount 可读取的 DataFrame。"""
    if not trades:
        return pd.DataFrame(
            columns=[
                "date",
                "code",
                "name",
                "type",
                "action",
                "price",
                "shares",
                "amount",
                "fee",
                "reason",
                "cash_after",
                "position_after",
                "is_simulated",
                "strategy",
            ]
        )
    df = pd.DataFrame(trades)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _closed_trade_from_pair(trades: list[dict], code: str) -> dict:
    """用最近一组 BUY/SELL 生成一笔完整交易明细。"""
    sell = trades[-1]
    buy = next(item for item in reversed(trades[:-1]) if item["code"] == code and item["action"] == "BUY")
    profit = (sell["price"] - buy["price"]) * sell["shares"]
    cost = buy["price"] * sell["shares"]
    holding_days = (pd.to_datetime(sell["date"]) - pd.to_datetime(buy["date"])).days
    return {
        "code": code,
        "name": buy["name"],
        "buy_date": buy["date"],
        "sell_date": sell["date"],
        "buy_price": buy["price"],
        "sell_price": sell["price"],
        "shares": sell["shares"],
        "profit": round(profit, 2),
        "return": profit / cost if cost else 0.0,
        "holding_days": holding_days,
        "buy_reason": buy["reason"],
        "sell_reason": sell["reason"],
    }


def _build_summary(code: str, meta: pd.Series, trades: pd.DataFrame, equity_curve: pd.DataFrame, benchmark_warning: str | None) -> dict:
    """汇总收益率、最大回撤、胜率、交易次数和持仓天数。"""
    total_profit = float(trades["profit"].sum()) if not trades.empty else 0.0
    trade_count = len(trades)
    wins = trades[trades["profit"] > 0] if not trades.empty else pd.DataFrame()
    losses = trades[trades["profit"] < 0] if not trades.empty else pd.DataFrame()
    total_holding_days = int(trades["holding_days"].sum()) if not trades.empty else 0
    profit_loss_ratio = abs(wins["profit"].mean() / losses["profit"].mean()) if len(wins) and len(losses) else 0.0
    max_consecutive_losses = _max_consecutive_losses(trades)
    data_note = "数据读取正常。"
    if benchmark_warning:
        data_note = f"基准数据提示：{benchmark_warning}；相对强弱可能无法正常计算。"
    if equity_curve.empty:
        max_drawdown = 0.0
    else:
        max_drawdown = calculate_max_drawdown(equity_curve["total_assets"])
    return {
        "code": code,
        "name": str(meta["name"]),
        "total_return": total_profit / INITIAL_CASH,
        "max_drawdown": max_drawdown,
        "win_rate": len(wins) / trade_count if trade_count else 0.0,
        "trade_count": trade_count,
        "total_holding_days": total_holding_days,
        "avg_holding_days": total_holding_days / trade_count if trade_count else 0.0,
        "profit_loss_ratio": profit_loss_ratio,
        "max_consecutive_losses": max_consecutive_losses,
        "has_open_position": False,
        "data_note": data_note,
    }


def _max_consecutive_losses(trades: pd.DataFrame) -> int:
    if trades.empty or "profit" not in trades.columns:
        return 0
    max_streak = 0
    streak = 0
    for profit in trades["profit"]:
        if profit < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def _empty_summary(code: str, note: str) -> dict:
    """缺少行情时生成空摘要，避免回测崩溃。"""
    return {
        "code": code,
        "name": code,
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0,
        "trade_count": 0,
        "total_holding_days": 0,
        "avg_holding_days": 0.0,
        "profit_loss_ratio": 0.0,
        "max_consecutive_losses": 0,
        "has_open_position": False,
        "data_note": note,
    }


if __name__ == "__main__":
    main()
