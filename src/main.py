"""A 股周线波段模拟盘入口。"""

from __future__ import annotations

import argparse
from datetime import date

import pandas as pd

from config import BENCHMARK_CODE, DATA_DIR, REPORT_DIR, TRADES_FILE, WATCHLIST_FILE
from data_coverage import write_data_coverage_report
from data_fetcher import fetch_watchlist_data
from data_health import write_data_health_report
from data_loader import load_price_data, read_trades_with_validation, read_watchlist
from factor_analysis import write_factor_analysis_report
from indicators import add_indicators, latest_on_or_before
from paper_portfolio import update_paper_portfolio
from portfolio import SimAccount
from reporting import (
    build_cycle_decisions,
    save_account_status,
    save_model_dataset,
    save_signals,
    write_daily_report,
    write_brief_report,
    write_ranking_report,
    write_risk_report,
    write_short_swing_report,
    write_weekly_review,
)
from signal_engine import make_signal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A 股周线波段模拟盘")
    parser.add_argument("--date", help="运行日期，例如 2026-05-29。不填则使用最新行情日期或今天。")
    parser.add_argument("--weekly", action="store_true", help="强制生成周复盘报告。")
    parser.add_argument("--fetch-data", action="store_true", help="先用公开行情源下载 enabled=1 标的的本地日线 CSV。")
    parser.add_argument("--start-date", help="下载行情起始日期，例如 2025-01-01。")
    parser.add_argument("--end-date", help="下载行情结束日期，例如 2026-06-02。")
    parser.add_argument("--batch-size", type=int, default=5, help="每批最多下载的标的数量，默认 5。")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="标的和重试之间的等待秒数，默认 2。")
    parser.add_argument("--retry", type=int, default=2, help="每个公开行情接口最多重试次数，默认 2。")
    parser.add_argument("--fetch-code", help="只下载指定代码，例如 510500。")
    parser.add_argument("--fetch-group", help="只下载 watchlist.csv 中指定 group 的 enabled=1 标的，例如 宽基。")
    parser.add_argument("--fetch-source", choices=["auto", "akshare", "baostock", "tushare"], default="auto", help="指定行情数据源，默认 auto。")
    parser.add_argument("--incremental", action="store_true", help="启用增量更新：已有 CSV 时只回看最近一段重新抓取并合并。")
    parser.add_argument("--lookback-days", type=int, default=10, help="增量更新从最后交易日前回看的天数，默认 10。")
    parser.add_argument("--strategy", choices=["mid_trend", "short_swing"], default="mid_trend", help="选择主报告策略，默认 mid_trend。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    requested_date = pd.to_datetime(args.date) if args.date else None

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    watchlist = read_watchlist(WATCHLIST_FILE)

    if args.fetch_data:
        start_date, end_date = _fetch_date_range(args.start_date, args.end_date)
        fetch_results = fetch_watchlist_data(
            watchlist,
            start_date,
            end_date,
            batch_size=args.batch_size,
            sleep_seconds=args.sleep_seconds,
            retry=args.retry,
            fetch_code=args.fetch_code,
            fetch_group=args.fetch_group,
            fetch_source=args.fetch_source,
            incremental=args.incremental,
            lookback_days=args.lookback_days,
        )
        fresh_count = sum(1 for item in fetch_results if item.status == "fresh_download_success")
        cached_count = sum(1 for item in fetch_results if item.status == "cached_success")
        failed_count = sum(1 for item in fetch_results if item.status == "failed")
        print(f"行情下载完成：新下载成功 {fresh_count} 个，缓存可用 {cached_count} 个，失败 {failed_count} 个。")
        print("已生成数据更新日志：reports/data_update_log.md")
        print("已生成数据质量报告：reports/data_quality_report.md")
        print("已生成观察池健康报告：reports/watchlist_health_report.md")

    trades, trade_warnings = read_trades_with_validation(TRADES_FILE)
    account = SimAccount(trades)

    raw_data, missing_data = _load_all_data(watchlist)
    _, coverage_summary = write_data_coverage_report(watchlist)
    _, health_summary = write_data_health_report(watchlist)
    benchmark_raw = raw_data.get(BENCHMARK_CODE)
    benchmark_with_indicators = add_indicators(benchmark_raw) if benchmark_raw is not None else None

    price_history: dict[str, pd.DataFrame] = {}
    latest_rows: dict[str, pd.Series] = {}
    latest_prices: dict[str, float] = {}

    for _, meta in watchlist.iterrows():
        code = str(meta["code"])
        raw = raw_data.get(code)
        if raw is None:
            continue
        with_indicators = add_indicators(raw, benchmark_with_indicators)
        latest = latest_on_or_before(with_indicators, requested_date)
        if latest is None:
            missing_data.append(f"{code} 没有早于指定日期的行情")
            continue
        price_history[code] = with_indicators
        latest_rows[code] = latest
        latest_prices[code] = float(latest["close"])

    run_date = _decide_run_date(latest_rows, requested_date)
    account.update_highest_close(price_history, pd.to_datetime(run_date))

    signal_watchlist = _signal_watchlist(watchlist, latest_rows)
    mid_signals = []
    short_signals = []
    for _, meta in signal_watchlist.iterrows():
        code = str(meta["code"])
        mid_signals.append(make_signal(latest_rows.get(code), meta, account, latest_prices, run_date, strategy="mid_trend"))
        short_signals.append(make_signal(latest_rows.get(code), meta, account, latest_prices, run_date, strategy="short_swing"))

    signals = short_signals if args.strategy == "short_swing" else mid_signals
    cycle_rows = build_cycle_decisions(mid_signals, short_signals, latest_rows)
    paper_path, paper_summary = update_paper_portfolio(run_date, latest_prices, watchlist)
    save_signals(signals)
    model_dataset_path = save_model_dataset(run_date, watchlist, latest_rows, mid_signals, price_history, short_signals, cycle_rows)
    factor_analysis_path = write_factor_analysis_report(model_dataset_path)
    ranking_path = write_ranking_report(run_date, watchlist, latest_rows, mid_signals, short_signals, cycle_rows)
    short_swing_path = write_short_swing_report(run_date, short_signals, cycle_rows)
    brief_path = write_brief_report(run_date, mid_signals, short_signals, cycle_rows, missing_data, model_dataset_path, coverage_summary, health_summary, paper_summary)
    account_history = save_account_status(run_date, account, latest_prices)
    daily_path = write_daily_report(run_date, account, latest_prices, signals, missing_data, trade_warnings, short_signals, cycle_rows)
    risk_path = write_risk_report(run_date, account, latest_prices)

    weekly_path = None
    if args.weekly or pd.to_datetime(run_date).weekday() == 4:
        weekly_path = write_weekly_review(run_date, account, latest_prices, account_history, signals)

    print(f"已生成每日信号报告：{daily_path}")
    print(f"已生成每日最简摘要：{brief_path}")
    print(f"已生成ETF横截面排名报告：{ranking_path}")
    print(f"已生成因子有效性报告：{factor_analysis_path}")
    print(f"已生成短期策略报告：{short_swing_path}")
    print("已生成数据覆盖报告：reports/latest_data_coverage.md")
    print("已生成数据健康报告：reports/latest_data_health.md")
    print(f"已生成模拟盘持仓报告：{paper_path}")
    print(f"已生成风险控制报告：{risk_path}")
    print(f"已更新模型研究数据集：{model_dataset_path}")
    if weekly_path:
        print(f"已生成周复盘报告：{weekly_path}")
    print("所有交易均为模拟盘记录，不含任何真实下单接口。")


def _load_all_data(watchlist: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """读取观察名单和基准所需的所有本地行情。"""
    codes = set(watchlist["code"].astype(str).tolist())
    codes.add(BENCHMARK_CODE)
    enabled_codes = set(watchlist.loc[watchlist["enabled"], "code"].astype(str).tolist())
    enabled_codes.add(BENCHMARK_CODE)
    raw_data: dict[str, pd.DataFrame] = {}
    missing_data: list[str] = []
    for code in sorted(codes):
        df, warning = load_price_data(DATA_DIR, code)
        if warning and code in enabled_codes:
            missing_data.append(f"{code}: {warning}")
        if df is not None:
            raw_data[code] = df
    return raw_data, missing_data


def _signal_watchlist(watchlist: pd.DataFrame, latest_rows: dict[str, pd.Series]) -> pd.DataFrame:
    """交易池只取 enabled=1；观察池仅在已有行情时展示。"""
    enabled_mask = watchlist["enabled"].astype(bool)
    observe_with_data = (watchlist["role"] == "observe_pool") & watchlist["code"].astype(str).isin(latest_rows.keys())
    return watchlist[enabled_mask | observe_with_data].copy()


def _decide_run_date(latest_rows: dict[str, pd.Series], requested_date: pd.Timestamp | None) -> str:
    """优先使用指定日期；否则使用所有行情里的最新日期；没有数据时用今天。"""
    if requested_date is not None:
        return requested_date.strftime("%Y-%m-%d")
    if latest_rows:
        latest_date = max(row["date"] for row in latest_rows.values())
        return latest_date.strftime("%Y-%m-%d")
    return date.today().strftime("%Y-%m-%d")


def _fetch_date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    """整理行情下载日期，默认结束日期为今天。"""
    end = pd.to_datetime(end_date).strftime("%Y-%m-%d") if end_date else date.today().strftime("%Y-%m-%d")
    start = pd.to_datetime(start_date).strftime("%Y-%m-%d") if start_date else (pd.to_datetime(end) - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    return start, end


if __name__ == "__main__":
    main()
