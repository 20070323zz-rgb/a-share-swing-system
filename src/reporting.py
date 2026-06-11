"""生成 Markdown 报告和 CSV 输出。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import (
    ACCOUNT_STATUS_FILE,
    FACTOR_ANALYSIS_REPORT_FILE,
    INITIAL_CASH,
    LATEST_BRIEF_FILE,
    LATEST_DAILY_FILE,
    LATEST_FACTOR_ANALYSIS_FILE,
    LATEST_RANKING_FILE,
    LATEST_SHORT_SWING_FILE,
    LATEST_WEEKLY_FILE,
    MAX_20D_RETURN_TO_CHASE,
    MAX_5D_RETURN_TO_CHASE,
    MAX_POSITION_VALUE,
    MAX_SINGLE_POSITION_RATIO,
    MID_TREND_CASH,
    MIN_CASH,
    MODEL_DATASET_FILE,
    REPORT_DIR,
    RANKING_REPORT_FILE,
    RISK_REPORT_FILE,
    SHORT_SWING_CASH,
    SIGNALS_FILE,
    STRATEGY_COMPARE_REPORT_FILE,
    VOLUME_RATIO_MAX,
    VOLUME_RATIO_MIN,
)
from portfolio import SimAccount, stop_loss_rate
from signal_engine import Signal
from labels import add_future_return_labels


def save_signals(signals: list[Signal]) -> None:
    """保存信号明细，方便复制给 ChatGPT 或继续分析。"""
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame([signal.to_dict() for signal in signals])
    if SIGNALS_FILE.exists() and SIGNALS_FILE.stat().st_size > 0:
        old_df = pd.read_csv(SIGNALS_FILE, dtype={"code": str})
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date", "code"], keep="last")
    else:
        combined = new_df
    combined.to_csv(SIGNALS_FILE, index=False)


def save_account_status(
    run_date: str,
    account: SimAccount,
    latest_prices: dict[str, float],
) -> pd.DataFrame:
    """保存账户状态，并计算当前最大回撤。"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    market_value = account.market_value(latest_prices)
    total_assets = account.cash + market_value
    row = {
        "date": run_date,
        "total_assets": round(total_assets, 2),
        "cash": round(account.cash, 2),
        "market_value": round(market_value, 2),
        "profit": round(total_assets - INITIAL_CASH, 2),
        "profit_pct": round(total_assets / INITIAL_CASH - 1, 6),
        "positions_count": len(account.positions),
    }

    if ACCOUNT_STATUS_FILE.exists() and ACCOUNT_STATUS_FILE.stat().st_size > 0:
        df = pd.read_csv(ACCOUNT_STATUS_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    else:
        df = pd.DataFrame([row])

    df["peak_assets"] = df["total_assets"].cummax()
    df["drawdown"] = df["total_assets"] / df["peak_assets"] - 1
    df.to_csv(ACCOUNT_STATUS_FILE, index=False)
    return df


def write_daily_report(
    run_date: str,
    account: SimAccount,
    latest_prices: dict[str, float],
    signals: list[Signal],
    missing_data: list[str],
    trade_warnings: list[str] | None = None,
    short_signals: list[Signal] | None = None,
    cycle_rows: list[dict] | None = None,
) -> Path:
    """生成每日信号 Markdown 报告。"""
    path = REPORT_DIR / f"daily_signal_{run_date}.md"
    total_assets = account.total_assets(latest_prices)
    trade_signals = [s for s in signals if s.enabled and s.role == "trade_pool"]
    observe_signals = [s for s in signals if s.role == "observe_pool"]
    buy_candidates = [s for s in trade_signals if s.signal == "BUY"]
    sell_candidates = [s for s in trade_signals if s.signal == "SELL"]

    lines = [
        f"# 每日信号报告 {run_date}",
        "",
        "## 账户概览",
        f"- 当前账户总资产：{total_assets:.2f} 元",
        f"- 当前现金：{account.cash:.2f} 元",
        f"- 当前持仓市值：{account.market_value(latest_prices):.2f} 元",
        f"- 最大总仓位限制：{MAX_POSITION_VALUE:.2f} 元",
        f"- 最低现金要求：{MIN_CASH:.2f} 元",
        "",
        "## 当前持仓",
    ]

    if account.positions:
        for pos in account.positions.values():
            price = latest_prices.get(pos.code, pos.avg_price)
            pnl = price / pos.avg_price - 1
            lines.append(
                f"- {pos.code} {pos.name}：{pos.shares:.0f} 份/股，成本 {pos.avg_price:.4f}，"
                f"现价 {price:.4f}，浮动收益 {pnl:.2%}，最高收盘参考 {pos.highest_close:.4f}"
            )
    else:
        lines.append("- 当前无持仓")

    lines += [
        "",
        "## 候选买入标的",
    ]
    _append_signal_list(lines, buy_candidates, empty_text="暂无候选买入")

    lines += [
        "",
        "## 候选卖出标的",
    ]
    _append_signal_list(lines, sell_candidates, empty_text="暂无候选卖出")

    lines += [
        "",
        "## 交易池分组概览",
    ]
    _append_group_overview(lines, trade_signals)

    lines += [
        "",
        "## 观察池信号",
    ]
    if observe_signals:
        _append_signal_table(lines, observe_signals)
    else:
        lines.append("- 暂无观察池信号")

    lines += [
        "",
        "## 全部信号明细",
    ]
    for signal in signals:
        lines.append(
            f"- {signal.code} {signal.name} [{signal.signal}] 收盘 {signal.close:.4f}；"
            f"原因：{signal.reasons or '无'}；禁止交易原因：{signal.block_reasons or '无'}；"
            f"止损价：{signal.stop_loss_price:.4f}；建议仓位：{signal.suggested_amount:.2f} 元，"
            f"{signal.suggested_shares} 份/股"
        )

    if short_signals is not None:
        lines += ["", "## short_swing 短期波段信号"]
        _append_signal_table(lines, [s for s in short_signals if s.enabled and s.role == "trade_pool"])

    if cycle_rows is not None:
        lines += ["", "## 双周期共振信号"]
        _append_cycle_decision_table(lines, cycle_rows)

    lines += [
        "",
        "## 数据问题",
    ]
    if missing_data:
        lines.extend([f"- {item}" for item in missing_data])
    else:
        lines.append("- 未发现数据缺失问题")

    lines += [
        "",
        "## 交易记录校验",
    ]
    if trade_warnings:
        lines.extend([f"- {item}" for item in trade_warnings])
    else:
        lines.append("- trades.csv 字段、日期、价格和数量检查通过")

    lines += [
        "",
        "## 明日计划",
        "- 只按模拟盘执行，不接真实交易接口。",
        "- 优先观察 BUY 和 SELL 信号，不追高，不突破风控上限。",
        "- 如果发生模拟成交，手动记录到 trades.csv 后再复盘。",
        "",
        "更多横截面排名请查看 reports/latest_ranking.md。",
        "WATCH 接近 BUY 评分请查看 latest_ranking.md。",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    LATEST_DAILY_FILE.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def write_brief_report(
    run_date: str,
    mid_signals: list[Signal],
    short_signals: list[Signal],
    cycle_rows: list[dict],
    missing_data: list[str],
    model_dataset_path: Path = MODEL_DATASET_FILE,
    coverage_summary: dict | None = None,
    health_summary: dict | None = None,
    paper_summary: dict | None = None,
) -> Path:
    """生成每天最简洁的查看入口，不输出真实交易指令。"""
    latest_model = _latest_model_slice(model_dataset_path)
    coverage_summary = coverage_summary or {}
    health_summary = health_summary or {}
    paper_summary = paper_summary or {}
    lines = [
        f"# 每日最简摘要 {run_date}",
        "",
        "本摘要只用于模拟盘观察，不包含任何真实交易指令。",
        "",
        "## 数据覆盖摘要",
        f"- 观察标的总数：{coverage_summary.get('total', 0)}",
        f"- ETF 总数：{coverage_summary.get('etf_total', 0)}",
        f"- ETF 数据缺失数量：{coverage_summary.get('etf_missing', 0)}",
        f"- 个股观察缺失数量：{coverage_summary.get('stock_observe_missing', 0)}",
        f"- observe_pool 总缺失数量：{coverage_summary.get('observe_pool_missing', 0)}",
        f"- 有效数据数量：{coverage_summary.get('valid', 0)}",
        f"- 数据过期数量：{coverage_summary.get('stale', 0)}",
        f"- trade_pool 覆盖率：{coverage_summary.get('trade_pool_rate', 0.0):.2%}",
        f"- observe_pool 覆盖率：{coverage_summary.get('observe_pool_rate', 0.0):.2%}",
        "- 600519、300750 等 STOCK 属于个股观察，不属于 ETF 下载脚本处理范围。",
        "",
        "## 数据健康摘要",
        f"- 正常：{health_summary.get('normal', 0)}",
        f"- 提醒：{health_summary.get('warning', 0)}",
        f"- 异常：{health_summary.get('error', 0)}",
        f"- 缺失：{health_summary.get('missing', 0)}",
        "",
        "## 双周期信号数量",
        f"- mid_trend：{_signal_counts_text(mid_signals)}",
        f"- short_swing：{_signal_counts_text(short_signals)}",
        "",
        "## 模拟盘摘要",
        f"- 当前总资产：{float(paper_summary.get('total_assets', INITIAL_CASH)):.2f} 元",
        f"- 当前现金：{float(paper_summary.get('cash', INITIAL_CASH)):.2f} 元",
        f"- 当前持仓数：{int(paper_summary.get('position_count', 0))}",
        f"- 今日是否有候选模拟买入：{_candidate_buy_text(mid_signals, short_signals, cycle_rows)}",
        f"- 是否触发风险提醒：{_risk_alert_text(paper_summary, cycle_rows)}",
        "",
        "## 双周期共振",
    ]
    _append_cycle_pair_brief(lines, cycle_rows, "BUY", "BUY", "mid BUY + short BUY")
    _append_cycle_pair_brief(lines, cycle_rows, "BUY", "WATCH", "mid BUY + short WATCH")
    _append_cycle_pair_brief(lines, cycle_rows, "WATCH", "BUY", "mid WATCH + short BUY")
    lines += [
        "",
        "## STRONG_RESONANCE 标的",
    ]
    _append_cycle_brief(lines, cycle_rows, "STRONG_RESONANCE")
    lines += ["", "## SHORT_TRIAL 标的"]
    _append_cycle_brief(lines, cycle_rows, "SHORT_TRIAL")
    lines += ["", "## RISK_ALERT 标的"]
    _append_cycle_brief(lines, cycle_rows, "RISK_ALERT")
    lines += ["", "## STRONG_RESONANCE 解释"]
    _append_strong_resonance_explanations(lines, cycle_rows, latest_model)

    lines += ["", "## 综合 Top 5"]
    _append_score_brief(lines, latest_model, "composite_score")
    lines += ["", "## watch_score Top 5"]
    _append_score_brief(lines, latest_model, "watch_score")
    lines += ["", "## group 强弱 Top 5"]
    _append_group_strength_brief(lines, latest_model, limit=5)

    lines += ["", "## 数据缺失和异常提醒"]
    lines.append(f"- ETF 数据缺失数量：{coverage_summary.get('etf_missing', 0)}")
    lines.append(f"- 个股观察缺失数量：{coverage_summary.get('stock_observe_missing', 0)}")
    lines.append(f"- observe_pool 总缺失数量：{coverage_summary.get('observe_pool_missing', 0)}")
    if missing_data:
        lines.append("- 主策略加载阶段仍有以下数据提示：")
        lines.extend([f"- {item}" for item in missing_data])
    else:
        lines.append("- 主策略加载阶段未发现额外数据缺失问题。")
    issue_symbols = health_summary.get("issue_symbols", [])
    if issue_symbols:
        lines.append(f"- 健康检查需关注：{', '.join(issue_symbols[:10])}")

    lines += ["", "## 今日建议"]
    lines.append(f"- {_brief_advice(cycle_rows)}")
    lines.append("- BUY ETF 排名请查看 reports/latest_buy_ranking.md；首次模拟买入计划请查看 reports/first_paper_buy_plan.md。")
    lines += [
        "",
        "## 安全边界",
        "- 不接券商 API，不下单，不读取账号密码，不自动交易。",
    ]
    LATEST_BRIEF_FILE.write_text("\n".join(lines), encoding="utf-8")
    return LATEST_BRIEF_FILE


def write_ranking_report(
    run_date: str,
    watchlist: pd.DataFrame,
    latest_rows: dict[str, pd.Series],
    signals: list[Signal],
    short_signals: list[Signal] | None = None,
    cycle_rows: list[dict] | None = None,
) -> Path:
    """生成 ETF 横截面强弱排名报告。"""
    signal_map = {signal.code: signal for signal in signals}
    ranking_rows: list[dict] = []
    missing_rows: list[dict] = []

    for _, meta in watchlist.iterrows():
        enabled = bool(meta.get("enabled", False))
        role = str(meta.get("role", "trade_pool"))
        type_name = str(meta.get("type", "ETF")).upper()
        if not enabled or role != "trade_pool" or type_name != "ETF":
            continue
        code = str(meta["code"])
        signal = signal_map.get(code)
        row = latest_rows.get(code)
        if row is None:
            missing_rows.append({"code": code, "name": meta.get("name", code), "group": meta.get("group", "未分类")})
            continue
        ranking_rows.append(
            {
                "code": code,
                "name": meta.get("name", code),
                "group": meta.get("group", "未分类"),
                "close": _numeric_row_value(row, "close"),
                "signal": signal.signal if signal else "NO_SIGNAL",
                "relative_strength": _numeric_row_value(row, "relative_strength"),
                "return_20d": _numeric_row_value(row, "ret20"),
                "return_5d": _numeric_row_value(row, "ret5"),
                "volume_ratio": _numeric_row_value(row, "volume_ratio"),
                "ma20": _numeric_row_value(row, "ma20"),
                "ma60": _numeric_row_value(row, "ma60"),
                "ma20_slope": _numeric_row_value(row, "ma20_slope"),
                "reasons": signal.reasons if signal else "",
                "block_reasons": signal.block_reasons if signal else "",
                "watch_score": _watch_score(signal, row) if signal else 0.0,
            }
        )

    df = pd.DataFrame(ranking_rows)
    df = _add_composite_score(df)
    lines = [
        f"# ETF 横截面强弱排名 {run_date}",
        "",
        "本报告只统计 enabled=1、role=trade_pool 且本地有合格行情 CSV 的 ETF，不包含任何真实交易接口或下单操作。",
        "",
    ]

    _append_top_section(lines, "composite_score Top 10", df, "composite_score")
    _append_top_section(lines, "相对强弱 Top 10", df, "relative_strength")
    _append_top_section(lines, "20 日涨幅 Top 10", df, "return_20d")
    _append_top_section(lines, "5 日涨幅 Top 10", df, "return_5d")
    _append_top_section(lines, "成交量改善 Top 10", df, "volume_ratio")

    lines += ["", "## 当前 BUY 标的汇总"]
    _append_ranking_rows(lines, df[df["signal"] == "BUY"] if not df.empty else df)

    lines += ["", "## 当前 SELL 标的汇总"]
    _append_ranking_rows(lines, df[df["signal"] == "SELL"] if not df.empty else df)

    lines += ["", "## WATCH 接近 BUY 评分 Top 10"]
    if df.empty:
        lines.append("- 暂无可排名标的。")
    else:
        watch_df = df[df["signal"] == "WATCH"].copy()
        if watch_df.empty:
            lines.append("- 暂无 WATCH 标的。")
        else:
            watch_df = watch_df.sort_values(["watch_score", "relative_strength", "return_20d", "volume_ratio"], ascending=False, na_position="last")
            _append_ranking_rows(lines, watch_df.head(10), include_watch_score=True)

    if short_signals is not None:
        lines += ["", "## short_swing watch_score Top 10"]
        short_df = _signals_to_score_frame(short_signals, latest_rows)
        short_df = short_df[short_df["signal"] == "WATCH"].copy() if not short_df.empty else short_df
        if short_df.empty:
            lines.append("- 暂无 short_swing WATCH 标的。")
        else:
            _append_ranking_rows(lines, short_df.sort_values("watch_score", ascending=False).head(10), include_watch_score=True)

    if cycle_rows is not None:
        lines += ["", "## 双周期综合评分 Top 10"]
        cycle_df = pd.DataFrame(cycle_rows)
        if cycle_df.empty:
            lines.append("- 暂无双周期评分。")
        else:
            _append_cycle_score_table(lines, cycle_df.sort_values("dual_score", ascending=False).head(10))
        lines += ["", "## 双周期共振 Top 10"]
        if cycle_df.empty:
            lines.append("- 暂无双周期共振。")
        else:
            resonance = cycle_df[cycle_df["resonance_type"].isin(["STRONG_RESONANCE", "SHORT_TRIAL", "MID_HOLD"])]
            _append_cycle_score_table(lines, resonance.sort_values("dual_score", ascending=False).head(10))

    lines += ["", "## group 强弱概览"]
    _append_ranking_group_overview(lines, df)

    lines += ["", "## 数据缺失标的"]
    if missing_rows:
        lines.append("| 代码 | 名称 | group |")
        lines.append("| --- | --- | --- |")
        for item in missing_rows:
            lines.append(f"| {item['code']} | {item['name']} | {item['group']} |")
    else:
        lines.append("- 本次排名范围内未发现数据缺失标的。")

    RANKING_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_RANKING_FILE.write_text(RANKING_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return RANKING_REPORT_FILE


def build_cycle_decisions(
    mid_signals: list[Signal],
    short_signals: list[Signal],
    latest_rows: dict[str, pd.Series],
) -> list[dict]:
    """合成中期与短期信号，生成双周期决策矩阵。"""
    short_map = {signal.code: signal for signal in short_signals}
    rows = []
    for mid in mid_signals:
        if not mid.enabled or mid.role != "trade_pool" or mid.type.upper() != "ETF":
            continue
        short = short_map.get(mid.code)
        if short is None:
            continue
        resonance_type, decision, mid_action, short_action = _cycle_decision(mid.signal, short.signal)
        short_position_limit = "短期账户单只 ETF 建议不超过 600-900 元（20%-30% 短期资金）"
        total_exposure_warning = "同一 ETF mid+short 合计风险暴露不超过总资产 35%"
        group_exposure_warning = "同一 group 总暴露不超过总资产 50%"
        row = latest_rows.get(mid.code)
        mid_score = _clamp_score(_watch_score(mid, row) if row is not None else 0.0)
        short_score = _clamp_score(_watch_score(short, row) if row is not None else 0.0)
        rows.append(
            {
                "code": mid.code,
                "name": mid.name,
                "group": mid.group,
                "mid_signal": mid.signal,
                "short_signal": short.signal,
                "mid_score": mid_score,
                "short_score": short_score,
                "dual_score": round((mid_score + short_score) / 2, 6),
                "resonance_type": resonance_type,
                "cycle_decision": decision,
                "mid_action": mid_action,
                "short_action": short_action,
                "short_position_limit": short_position_limit,
                "total_exposure_warning": total_exposure_warning,
                "group_exposure_warning": group_exposure_warning,
            }
        )
    return sorted(rows, key=lambda item: item["dual_score"], reverse=True)


def _cycle_decision(mid_signal: str, short_signal: str) -> tuple[str, str, str, str]:
    mid_signal = str(mid_signal).upper()
    short_signal = str(short_signal).upper()
    if mid_signal == "BUY" and short_signal == "BUY":
        return "STRONG_RESONANCE", "双周期强共振", "中期账户按规则买入", "短期账户小仓补充"
    if mid_signal == "WATCH" and short_signal == "BUY":
        return "SHORT_TRIAL", "短期试探，不动用中期资金", "中期账户继续观察", "短期账户小仓试探"
    if mid_signal == "BUY" and short_signal == "WATCH":
        return "MID_HOLD", "中期趋势确认，短期未加速", "中期账户按规则买入或持有", "短期账户不追"
    if mid_signal == "BUY" and short_signal == "SELL":
        return "RISK_ALERT", "中期仍在但短期转弱", "中期按原规则判断", "短期账户不参与"
    if mid_signal == "SELL" and short_signal == "BUY":
        return "AVOID", "中期趋势破坏后的短期反弹", "中期账户不买", "短期最多观察"
    if mid_signal == "SELL" and short_signal == "SELL":
        return "AVOID", "双周期走弱", "中期账户卖出或回避", "短期账户回避"
    return "OBSERVE", "继续观察", "中期账户观察", "短期账户观察"


def write_short_swing_report(run_date: str, signals: list[Signal], cycle_rows: list[dict]) -> Path:
    """保存 short_swing 实验策略报告。"""
    lines = [
        f"# short_swing 实验策略报告 {run_date}",
        "",
        "short_swing 是 30% 短期实验账户策略，只用于模拟盘学习，不替代 mid_trend 主策略。",
        "",
        "## 短期信号",
    ]
    _append_signal_table(lines, [s for s in signals if s.enabled and s.role == "trade_pool"])
    lines += ["", "## 双周期决策参考"]
    _append_cycle_decision_table(lines, cycle_rows)
    LATEST_SHORT_SWING_FILE.write_text("\n".join(lines), encoding="utf-8")
    return LATEST_SHORT_SWING_FILE


def write_risk_report(run_date: str, account: SimAccount, latest_prices: dict[str, float]) -> Path:
    """生成风险控制报告，展示现金比例、仓位比例和止损预计亏损。"""
    total_assets = account.total_assets(latest_prices)
    market_value = account.market_value(latest_prices)
    cash_ratio = account.cash / total_assets if total_assets else 0.0
    position_ratio = market_value / total_assets if total_assets else 0.0

    lines = [
        f"# 风险控制报告 {run_date}",
        "",
        "## 账户风险概览",
        f"- 总资产：{total_assets:.2f} 元",
        f"- 现金：{account.cash:.2f} 元",
        f"- 现金比例：{cash_ratio:.2%}",
        f"- 持仓市值：{market_value:.2f} 元",
        f"- 总仓位比例：{position_ratio:.2%}",
        f"- 最大总仓位限制：{MAX_POSITION_VALUE:.2f} 元",
        f"- 最低现金要求：{MIN_CASH:.2f} 元",
        "",
        "## 双周期资金分层",
        f"- mid_trend 中期账户模拟资金：{MID_TREND_CASH:.2f} 元，占 70%，主策略。",
        f"- short_swing 短期账户模拟资金：{SHORT_SWING_CASH:.2f} 元，占 30%，实验策略。",
        "- short_swing 不得动用 mid_trend 中期账户资金。",
        "- 双周期共振时，短期账户同一 ETF 补充仓建议不超过短期资金 20%-30%。",
        "- 同一 ETF 的 mid_trend + short_swing 合计风险暴露不超过总资产 35%。",
        "- 同一 group 总暴露不超过总资产 50%。",
        "",
        "## 持仓风险明细",
    ]

    if not account.positions:
        lines.append("- 当前无持仓，暂无单一标的仓位和止损风险。")
    else:
        for pos in account.positions.values():
            price = latest_prices.get(pos.code, pos.avg_price)
            value = pos.shares * price
            ratio = value / total_assets if total_assets else 0.0
            stop_price = pos.avg_price * (1 - stop_loss_rate(pos.type))
            expected_loss = max(0.0, (pos.avg_price - stop_price) * pos.shares)
            over_limit = ratio > MAX_SINGLE_POSITION_RATIO
            lines.append(
                f"- {pos.code} {pos.name}：市值 {value:.2f} 元，占总资产 {ratio:.2%}；"
                f"单一标的超限：{'是' if over_limit else '否'}；"
                f"止损价 {stop_price:.4f}；触发止损预计亏损 {expected_loss:.2f} 元"
            )

    lines += [
        "",
        "## 风控结论",
    ]
    if account.cash < MIN_CASH:
        lines.append(f"- 现金低于最低要求：当前 {account.cash:.2f} 元，要求不少于 {MIN_CASH:.2f} 元")
    if market_value > MAX_POSITION_VALUE:
        lines.append(f"- 总仓位超限：当前 {market_value:.2f} 元，上限 {MAX_POSITION_VALUE:.2f} 元")
    if account.cash >= MIN_CASH and market_value <= MAX_POSITION_VALUE:
        lines.append("- 未发现现金或总仓位超限。")
    lines.append("- 本报告只用于模拟盘复盘，不包含任何真实交易操作。")

    RISK_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    return RISK_REPORT_FILE


def write_weekly_review(
    run_date: str,
    account: SimAccount,
    latest_prices: dict[str, float],
    account_history: pd.DataFrame,
    signals: list[Signal],
) -> Path:
    """生成周复盘 Markdown 报告。"""
    path = REPORT_DIR / f"weekly_review_{run_date}.md"
    history = account_history.copy()
    history["date"] = pd.to_datetime(history["date"])
    end_date = pd.to_datetime(run_date)
    start_date = end_date - pd.Timedelta(days=7)
    week_history = history[(history["date"] >= start_date) & (history["date"] <= end_date)]

    if len(week_history) >= 2:
        week_return = week_history.iloc[-1]["total_assets"] / week_history.iloc[0]["total_assets"] - 1
        max_drawdown = week_history["drawdown"].min()
    else:
        week_return = 0.0
        max_drawdown = history["drawdown"].min() if "drawdown" in history else 0.0

    realized = pd.DataFrame(account.realized_trades)
    wins = realized[realized["realized_pnl"] > 0] if not realized.empty else pd.DataFrame()
    losses = realized[realized["realized_pnl"] < 0] if not realized.empty else pd.DataFrame()
    win_rate = len(wins) / len(realized) if len(realized) else 0.0
    profit_loss_ratio = abs(wins["realized_pnl"].mean() / losses["realized_pnl"].mean()) if len(wins) and len(losses) else 0.0
    risk_violations = _risk_violations(account, latest_prices)
    watch_next_week = [s for s in signals if s.signal in ["BUY", "WATCH"]][:10]

    lines = [
        f"# 周复盘报告 {run_date}",
        "",
        "## 本周表现",
        f"- 本周收益率：{week_return:.2%}",
        f"- 最大回撤：{max_drawdown:.2%}",
        f"- 胜率：{win_rate:.2%}",
        f"- 盈亏比：{profit_loss_ratio:.2f}",
        "",
        "## 持仓明细",
    ]

    if account.positions:
        for pos in account.positions.values():
            price = latest_prices.get(pos.code, pos.avg_price)
            lines.append(
                f"- {pos.code} {pos.name}：{pos.shares:.0f} 份/股，成本 {pos.avg_price:.4f}，"
                f"现价 {price:.4f}，市值 {pos.shares * price:.2f} 元"
            )
    else:
        lines.append("- 当前无持仓")

    lines += [
        "",
        "## 本周交易明细",
    ]
    if realized.empty:
        lines.append("- 本周暂无已实现卖出交易")
    else:
        for _, row in realized.iterrows():
            lines.append(f"- {row['date'].date()} {row['code']} {row['name']}：已实现盈亏 {row['realized_pnl']:.2f} 元")

    lines += [
        "",
        "## 是否违反风控",
    ]
    if risk_violations:
        lines.extend([f"- {item}" for item in risk_violations])
    else:
        lines.append("- 未发现明显风控违规")

    lines += [
        "",
        "## 策略执行情况",
        "- 检查是否只执行了模拟交易。",
        "- 检查是否在没有 BUY 信号时冲动买入。",
        "- 检查是否按 SELL 信号执行止损或移动止盈。",
        "",
        "## 下周观察名单",
    ]
    if watch_next_week:
        for signal in watch_next_week:
            lines.append(f"- {signal.code} {signal.name} [{signal.signal}]：{signal.reasons or signal.block_reasons}")
    else:
        lines.append("- 暂无观察标的")

    lines += [
        "",
        "## 需要交给 ChatGPT 分析的问题",
        "- 本周是否有违反交易计划的行为？",
        "- 当前持仓是否应该继续持有、减仓还是止盈？",
        "- 下周观察名单中，哪些标的更符合趋势和风控？",
        "- 我的模拟成交记录是否存在追高、过度交易或止损不坚决的问题？",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    LATEST_WEEKLY_FILE.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def save_model_dataset(
    run_date: str,
    watchlist: pd.DataFrame,
    latest_rows: dict[str, pd.Series],
    signals: list[Signal],
    price_history: dict[str, pd.DataFrame] | None = None,
    short_signals: list[Signal] | None = None,
    cycle_rows: list[dict] | None = None,
) -> Path:
    """追加保存每日横截面特征，供后续模型训练研究。"""
    signal_map = {signal.code: signal for signal in signals}
    short_signal_map = {signal.code: signal for signal in short_signals or []}
    cycle_map = {str(row["code"]): row for row in cycle_rows or []}
    rows = []
    for _, meta in watchlist.iterrows():
        if not bool(meta.get("enabled", False)):
            continue
        code = str(meta["code"])
        row = latest_rows.get(code)
        if row is None:
            continue
        signal = signal_map.get(code)
        short_signal = short_signal_map.get(code)
        cycle = cycle_map.get(code, {})
        rows.append(
            {
                "date": run_date,
                "code": code,
                "name": meta.get("name", code),
                "group": meta.get("group", "未分类"),
                "role": meta.get("role", "trade_pool"),
                "preferred_strategy": meta.get("preferred_strategy", "both"),
                "close": _row_value(row, "close"),
                "ma20": _row_value(row, "ma20"),
                "ma60": _row_value(row, "ma60"),
                "ma20_slope": _row_value(row, "ma20_slope"),
                "return_5d": _row_value(row, "ret5"),
                "return_20d": _row_value(row, "ret20"),
                "volume_ratio": _row_value(row, "volume_ratio"),
                "relative_strength": _row_value(row, "relative_strength"),
                "signal": signal.signal if signal else "NO_SIGNAL",
                "reasons": signal.reasons if signal else "",
                "block_reasons": signal.block_reasons if signal else "",
                "strategy": "mid_trend",
                "mid_trend_signal": signal.signal if signal else "NO_SIGNAL",
                "short_swing_signal": short_signal.signal if short_signal else "NO_SIGNAL",
                "mid_trend_score": "",
                "short_swing_score": "",
                "mid_trend_watch_score": _watch_score(signal, row) if signal else "",
                "short_swing_watch_score": _watch_score(short_signal, row) if short_signal else "",
                "resonance_type": cycle.get("resonance_type", ""),
                "cycle_decision": cycle.get("cycle_decision", ""),
                "composite_score": "",
                "watch_score": _watch_score(signal, row) if signal else "",
                "future_5d_return": "",
                "future_10d_return": "",
                "future_20d_return": "",
                "future_60d_return": "",
                "future_5d_rank": "",
                "future_10d_rank": "",
                "future_20d_rank": "",
                "future_60d_rank": "",
                "future_20d_top30": "",
            }
        )

    new_df = pd.DataFrame(rows)
    new_df = _score_model_rows(new_df)
    if MODEL_DATASET_FILE.exists() and MODEL_DATASET_FILE.stat().st_size > 0:
        old_df = pd.read_csv(MODEL_DATASET_FILE, dtype={"code": str})
        if "date" in old_df.columns:
            old_df = old_df[old_df["date"].astype(str) != str(run_date)]
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df
    if not combined.empty:
        combined = combined.drop_duplicates(subset=["date", "code"], keep="last").sort_values(["date", "code"])
        combined = _backfill_future_returns(combined, price_history or {})
    MODEL_DATASET_FILE.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(MODEL_DATASET_FILE, index=False)
    return MODEL_DATASET_FILE


def write_factor_analysis_report(model_dataset_path: Path = MODEL_DATASET_FILE) -> Path:
    """生成因子有效性研究报告，future returns 不参与任何交易信号。"""
    factors = ["relative_strength", "return_20d", "return_5d", "volume_ratio", "composite_score", "watch_score"]
    future_returns = ["future_5d_return", "future_20d_return", "future_60d_return"]
    future_ranks = ["future_5d_rank", "future_20d_rank", "future_60d_rank"]
    lines = [
        "# 因子有效性分析报告",
        "",
        "本报告只用于研究分析。future returns 严禁参与当日 signal、ranking、composite_score 或 watch_score 计算。",
        "",
    ]
    if not model_dataset_path.exists() or model_dataset_path.stat().st_size == 0:
        lines.append("- 暂无 model_dataset.csv，无法分析。")
        FACTOR_ANALYSIS_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
        LATEST_FACTOR_ANALYSIS_FILE.write_text(FACTOR_ANALYSIS_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        return FACTOR_ANALYSIS_REPORT_FILE

    df = pd.read_csv(model_dataset_path, dtype={"code": str})
    for col in factors + future_returns + future_ranks:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    sample_count = len(df)
    valid_future_count = int(df[future_returns].notna().any(axis=1).sum()) if all(col in df.columns for col in future_returns) else 0

    lines += [
        "## 样本数量提示",
        f"- 总样本行数：{sample_count}",
        f"- 已有任一 future return 的样本行数：{valid_future_count}",
    ]
    if valid_future_count < 30:
        lines.append("- 样本不足，不应过度解读。")

    lines += ["", "## 因子与 future return 相关性"]
    lines.append("| 因子 | future_5d_return | future_20d_return | future_60d_return |")
    lines.append("| --- | ---: | ---: | ---: |")
    for factor in factors:
        values = []
        for target in future_returns:
            values.append(_corr_text(df, factor, target, method="pearson"))
        lines.append(f"| {factor} | {' | '.join(values)} |")

    lines += ["", "## Spearman Rank IC"]
    lines.append("| 因子 | future_5d_rank | future_20d_rank | future_60d_rank |")
    lines.append("| --- | ---: | ---: | ---: |")
    for factor in factors:
        values = []
        for target in future_ranks:
            values.append(_corr_text(df, factor, target, method="spearman"))
        lines.append(f"| {factor} | {' | '.join(values)} |")

    lines += ["", "## composite_score Top 5 / Bottom 5 未来收益对比"]
    _append_score_future_compare(lines, df, "composite_score")

    lines += ["", "## watch_score Top 5 未来收益表现"]
    _append_score_future_compare(lines, df[df.get("signal", "") == "WATCH"].copy(), "watch_score", top_only=True)

    lines += ["", "## 按 group 汇总未来收益"]
    _append_future_group_summary(lines, df)

    FACTOR_ANALYSIS_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_FACTOR_ANALYSIS_FILE.write_text(FACTOR_ANALYSIS_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return FACTOR_ANALYSIS_REPORT_FILE


def _append_top_section(lines: list[str], title: str, df: pd.DataFrame, metric: str) -> None:
    lines += ["", f"## {title}"]
    if df.empty or metric not in df.columns:
        lines.append("- 暂无可排名标的。")
        return
    ranked = df.dropna(subset=[metric]).sort_values(metric, ascending=False).head(10)
    _append_ranking_rows(lines, ranked)


def _latest_model_slice(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(path, dtype={"code": str})
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()
    latest_date = df["date"].max()
    return df[df["date"] == latest_date].copy()


def _signal_counts_text(signals: list[Signal]) -> str:
    trade_signals = [s.signal for s in signals if s.enabled and s.role == "trade_pool"]
    counts = pd.Series(trade_signals).value_counts().to_dict() if trade_signals else {}
    return f"BUY {counts.get('BUY', 0)} / WATCH {counts.get('WATCH', 0)} / SELL {counts.get('SELL', 0)} / RISK {counts.get('RISK', 0)}"


def _append_cycle_brief(lines: list[str], cycle_rows: list[dict], resonance_type: str) -> None:
    matched = [row for row in cycle_rows if row.get("resonance_type") == resonance_type]
    if not matched:
        lines.append("- 无")
        return
    for row in matched:
        lines.append(f"- {row['code']} {row['name']}（{row['group']}）：{row['cycle_decision']}")


def _append_cycle_pair_brief(lines: list[str], cycle_rows: list[dict], mid_signal: str, short_signal: str, title: str) -> None:
    matched = [
        row
        for row in cycle_rows
        if str(row.get("mid_signal", "")).upper() == mid_signal and str(row.get("short_signal", "")).upper() == short_signal
    ]
    if not matched:
        lines.append(f"- {title}：0 个")
        return
    names = "；".join(f"{row['code']} {row['name']}（{row['group']}）" for row in matched[:10])
    lines.append(f"- {title}：{len(matched)} 个；{names}")


def _candidate_buy_text(mid_signals: list[Signal], short_signals: list[Signal], cycle_rows: list[dict]) -> str:
    mid_buy = [s for s in mid_signals if s.enabled and s.role == "trade_pool" and s.signal == "BUY"]
    short_buy = [s for s in short_signals if s.enabled and s.role == "trade_pool" and s.signal == "BUY"]
    resonance = [row for row in cycle_rows if row.get("resonance_type") in {"STRONG_RESONANCE", "SHORT_TRIAL", "MID_HOLD"}]
    count = len({s.code for s in mid_buy + short_buy} | {str(row.get("code")) for row in resonance})
    return f"是，{count} 个候选仅供模拟观察" if count else "否"


def _risk_alert_text(paper_summary: dict, cycle_rows: list[dict]) -> str:
    paper_risk = bool(paper_summary.get("has_risk_alert", False))
    cycle_risk = any(row.get("resonance_type") == "RISK_ALERT" for row in cycle_rows)
    if paper_risk and cycle_risk:
        return "是，模拟持仓和双周期均有提醒"
    if paper_risk:
        return "是，模拟持仓有提醒"
    if cycle_risk:
        return "是，双周期有 RISK_ALERT"
    return "否"


def _append_strong_resonance_explanations(lines: list[str], cycle_rows: list[dict], latest_model: pd.DataFrame) -> None:
    strong_rows = [row for row in cycle_rows if row.get("resonance_type") == "STRONG_RESONANCE"]
    if not strong_rows:
        lines.append("- 当前无 STRONG_RESONANCE 标的。")
        return
    model_map = {}
    if not latest_model.empty and "code" in latest_model.columns:
        model_map = latest_model.set_index(latest_model["code"].astype(str)).to_dict(orient="index")
    group_scores = {}
    if not latest_model.empty and "group" in latest_model.columns:
        for group, part in latest_model.groupby("group", dropna=False):
            group_scores[str(group)] = pd.to_numeric(part.get("composite_score", pd.Series(dtype=float)), errors="coerce").mean()
    for item in strong_rows:
        code = str(item.get("code", ""))
        model = model_map.get(code, {})
        group = str(item.get("group", model.get("group", "")))
        lines.append(f"### {code} {item.get('name', '')}")
        lines.append(f"- 趋势理由：{_trend_reason(model)}")
        lines.append(f"- 动量理由：20 日涨幅 {_fmt_number(model.get('return_20d', ''))}，5 日涨幅 {_fmt_number(model.get('return_5d', ''))}。")
        lines.append(f"- 相对强弱理由：relative_strength {_fmt_number(model.get('relative_strength', ''))}。")
        lines.append(f"- 成交量理由：volume_ratio {_fmt_number(model.get('volume_ratio', ''))}。")
        lines.append(f"- group 支撑：{group} 平均 composite_score {_fmt_number(group_scores.get(group, ''))}。")
        lines.append(f"- 风险提示：{_safe_text(model.get('block_reasons'), '未见主要阻断原因，但仍需按模拟盘仓位和止损规则观察。')}")


def _trend_reason(model: dict) -> str:
    close = _to_float(model.get("close"))
    ma20 = _to_float(model.get("ma20"))
    ma60 = _to_float(model.get("ma60"))
    ma20_slope = _to_float(model.get("ma20_slope"))
    reasons = []
    if close is not None and ma20 is not None:
        reasons.append("收盘价站上 MA20" if close > ma20 else "收盘价未站上 MA20")
    if close is not None and ma60 is not None:
        reasons.append("收盘价站上 MA60" if close > ma60 else "收盘价未站上 MA60")
    if ma20_slope is not None:
        reasons.append("MA20 向上" if ma20_slope > 0 else "MA20 未向上")
    return "；".join(reasons) if reasons else "趋势字段不足。"


def _to_float(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


def _safe_text(value: object, default: str) -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _append_score_brief(lines: list[str], df: pd.DataFrame, score_col: str) -> None:
    if df.empty or score_col not in df.columns:
        lines.append("- 暂无")
        return
    df = df.copy()
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
    ranked = df.dropna(subset=[score_col]).sort_values(score_col, ascending=False).head(5)
    if ranked.empty:
        lines.append("- 暂无")
        return
    for row in ranked.itertuples():
        lines.append(f"- {row.code} {row.name}（{row.group}）：{_fmt_number(getattr(row, score_col))}")


def _append_group_strength_brief(lines: list[str], df: pd.DataFrame, limit: int | None = None) -> None:
    if df.empty or "group" not in df.columns:
        lines.append("- 暂无")
        return
    group_rows = []
    for group, part in df.groupby("group", dropna=False):
        avg_score = pd.to_numeric(part.get("composite_score", pd.Series(dtype=float)), errors="coerce").mean()
        avg_rs = pd.to_numeric(part.get("relative_strength", pd.Series(dtype=float)), errors="coerce").mean()
        group_rows.append((group, avg_score, avg_rs, len(part)))
    group_rows.sort(key=lambda item: (1e9 if pd.isna(item[1]) else -item[1], str(item[0])))
    selected = group_rows[:limit] if limit else group_rows
    for group, avg_score, avg_rs, count in selected:
        lines.append(f"- {group}：{count} 个，平均 composite_score {_fmt_number(avg_score)}，平均 relative_strength {_fmt_number(avg_rs)}")


def _brief_advice(cycle_rows: list[dict]) -> str:
    resonance_types = {row.get("resonance_type") for row in cycle_rows}
    suggestions = []
    if "RISK_ALERT" in resonance_types:
        suggestions.append("风险提示")
    if "SHORT_TRIAL" in resonance_types:
        suggestions.append("短期试探")
        suggestions.append("等待中期确认")
    if "STRONG_RESONANCE" in resonance_types:
        suggestions.append("观察")
    if not suggestions:
        suggestions.append("观察")
    unique = []
    for item in suggestions:
        if item not in unique:
            unique.append(item)
    return " / ".join(unique)


def _corr_text(df: pd.DataFrame, factor: str, target: str, method: str) -> str:
    if factor not in df.columns or target not in df.columns:
        return ""
    subset = df[[factor, target]].dropna()
    if len(subset) < 3:
        return ""
    return _fmt_number(subset[factor].corr(subset[target], method=method))


def _append_score_future_compare(lines: list[str], df: pd.DataFrame, score_col: str, top_only: bool = False) -> None:
    future_cols = ["future_5d_return", "future_20d_return", "future_60d_return"]
    if df.empty or score_col not in df.columns:
        lines.append("- 暂无可分析样本。")
        return
    ranked = df.dropna(subset=[score_col]).sort_values(score_col, ascending=False)
    groups = [("Top 5", ranked.head(5))]
    if not top_only:
        groups.append(("Bottom 5", ranked.tail(5)))
    lines.append("| 分组 | 样本数 | 平均 future_5d | 平均 future_20d | 平均 future_60d |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for label, part in groups:
        values = []
        for col in future_cols:
            values.append(_fmt_number(pd.to_numeric(part.get(col, pd.Series(dtype=float)), errors="coerce").mean()))
        lines.append(f"| {label} | {len(part)} | {' | '.join(values)} |")


def _append_future_group_summary(lines: list[str], df: pd.DataFrame) -> None:
    if df.empty or "group" not in df.columns:
        lines.append("- 暂无 group 样本。")
        return
    lines.append("| group | 样本数 | 平均 future_5d | 平均 future_20d | 平均 future_60d |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for group, group_df in df.groupby("group", dropna=False):
        values = []
        for col in ["future_5d_return", "future_20d_return", "future_60d_return"]:
            values.append(_fmt_number(pd.to_numeric(group_df.get(col, pd.Series(dtype=float)), errors="coerce").mean()))
        lines.append(f"| {group} | {len(group_df)} | {' | '.join(values)} |")


def _score_model_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    score_input = df.rename(
        columns={
            "return_20d": "return_20d",
            "return_5d": "return_5d",
        }
    ).copy()
    for col in ["close", "ma20", "ma60", "ma20_slope", "return_5d", "return_20d", "volume_ratio", "relative_strength"]:
        score_input[col] = pd.to_numeric(score_input.get(col, pd.NA), errors="coerce")
    if "ma20_slope" not in score_input.columns:
        score_input["ma20_slope"] = pd.NA
    score_input["watch_score"] = pd.to_numeric(score_input.get("watch_score", pd.NA), errors="coerce").fillna(0.0)
    score_input = _add_composite_score(score_input)
    out = df.copy()
    out["composite_score"] = score_input["composite_score"].values
    out["watch_score"] = score_input["watch_score"].values
    out["mid_trend_score"] = out["composite_score"]
    out["mid_trend_watch_score"] = out["watch_score"]
    return out


def _backfill_future_returns(df: pd.DataFrame, price_history: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return add_future_return_labels(df, price_history)


def _add_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """计算 0-100 的横截面综合评分，只用于研究辅助。"""
    if df.empty:
        return df
    out = df.copy()
    score = pd.Series(0.0, index=out.index)
    metric_weights = {
        "relative_strength": 18.0,
        "return_20d": 14.0,
        "return_5d": 10.0,
        "volume_ratio": 10.0,
    }
    for metric, weight in metric_weights.items():
        if metric in out.columns:
            score += out[metric].rank(pct=True, na_option="bottom") * weight

    score += (out["close"] > out["ma20"]).fillna(False).astype(float) * 8.0
    score += (out["close"] > out["ma60"]).fillna(False).astype(float) * 8.0
    score += (out["ma20_slope"] > 0).fillna(False).astype(float) * 8.0
    block_counts = out["block_reasons"].fillna("").astype(str).apply(_split_count)
    score += (1.0 - (block_counts.clip(0, 5) / 5.0)) * 12.0
    score -= (out["return_20d"] > MAX_20D_RETURN_TO_CHASE).fillna(False).astype(float) * 8.0
    score -= (out["return_5d"] > MAX_5D_RETURN_TO_CHASE).fillna(False).astype(float) * 6.0
    score -= out[["relative_strength", "return_20d", "return_5d", "volume_ratio"]].isna().sum(axis=1) * 4.0

    group_bonus = pd.Series(0.0, index=out.index)
    for _, group_df in out.groupby("group", dropna=False):
        group_rank = group_df["relative_strength"].rank(pct=True, na_option="bottom")
        group_bonus.loc[group_df.index] = group_rank * 4.0
    score += group_bonus

    out["composite_score"] = score.clip(0, 100).round(6)
    out["watch_score"] = out["watch_score"].apply(_clamp_score)
    return out


def _signals_to_score_frame(signals: list[Signal], latest_rows: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for signal in signals:
        if not signal.enabled or signal.role != "trade_pool" or signal.type.upper() != "ETF":
            continue
        row = latest_rows.get(signal.code)
        if row is None:
            continue
        rows.append(
            {
                "code": signal.code,
                "name": signal.name,
                "group": signal.group,
                "close": signal.close,
                "signal": signal.signal,
                "relative_strength": _numeric_row_value(row, "relative_strength_10"),
                "return_20d": _numeric_row_value(row, "ret20"),
                "return_5d": _numeric_row_value(row, "ret5"),
                "volume_ratio": _numeric_row_value(row, "volume_ratio"),
                "ma20": _numeric_row_value(row, "ma20"),
                "ma60": _numeric_row_value(row, "ma60"),
                "ma20_slope": _numeric_row_value(row, "ma10_slope"),
                "reasons": signal.reasons,
                "block_reasons": signal.block_reasons,
                "watch_score": _watch_score(signal, row),
            }
        )
    return _add_composite_score(pd.DataFrame(rows))


def _append_cycle_decision_table(lines: list[str], cycle_rows: list[dict]) -> None:
    if not cycle_rows:
        lines.append("- 暂无双周期信号。")
        return
    _append_cycle_score_table(lines, pd.DataFrame(cycle_rows).head(20))


def _append_cycle_score_table(lines: list[str], df: pd.DataFrame) -> None:
    if df.empty:
        lines.append("- 暂无标的。")
        return
    lines.append("| 代码 | 名称 | group | mid | short | resonance_type | cycle_decision | dual_score | mid_action | short_action | short_position_limit | total_exposure_warning | group_exposure_warning |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |")
    for row in df.itertuples():
        lines.append(
            f"| {row.code} | {row.name} | {row.group} | {row.mid_signal} | {row.short_signal} | {row.resonance_type} | "
            f"{_escape_cell(row.cycle_decision)} | {_fmt_number(row.dual_score)} | {row.mid_action} | {row.short_action} | "
            f"{_escape_cell(row.short_position_limit)} | {_escape_cell(row.total_exposure_warning)} | {_escape_cell(row.group_exposure_warning)} |"
        )


def _append_ranking_rows(lines: list[str], df: pd.DataFrame, include_watch_score: bool = False) -> None:
    if df is None or df.empty:
        lines.append("- 暂无标的。")
        return
    if include_watch_score:
        lines.append("| 代码 | 名称 | group | signal | composite_score | watch_score | close | relative_strength | return_20d | return_5d | volume_ratio | reasons | block_reasons |")
        lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
        for row in df.itertuples():
            lines.append(
                f"| {row.code} | {row.name} | {row.group} | {row.signal} | {_fmt_number(getattr(row, 'composite_score', ''))} | {_fmt_number(row.watch_score)} | {_fmt_number(row.close)} | "
                f"{_fmt_number(row.relative_strength)} | {_fmt_number(row.return_20d)} | {_fmt_number(row.return_5d)} | {_fmt_number(row.volume_ratio)} | "
                f"{_escape_cell(_short_text(getattr(row, 'reasons', '') or '无', 120))} | {_escape_cell(_short_text(getattr(row, 'block_reasons', '') or '无', 120))} |"
            )
        return

    lines.append("| 代码 | 名称 | group | close | signal | relative_strength | return_20d | return_5d | volume_ratio | composite_score | watch_score | reasons | block_reasons |")
    lines.append("| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in df.itertuples():
        lines.append(
            f"| {row.code} | {row.name} | {row.group} | {_fmt_number(row.close)} | {row.signal} | "
            f"{_fmt_number(row.relative_strength)} | {_fmt_number(row.return_20d)} | {_fmt_number(row.return_5d)} | {_fmt_number(row.volume_ratio)} | "
            f"{_fmt_number(getattr(row, 'composite_score', ''))} | {_fmt_number(getattr(row, 'watch_score', ''))} | "
            f"{_escape_cell(_short_text(getattr(row, 'reasons', '') or '无', 120))} | {_escape_cell(_short_text(getattr(row, 'block_reasons', '') or '无', 120))} |"
        )


def _append_ranking_group_overview(lines: list[str], df: pd.DataFrame) -> None:
    if df.empty:
        lines.append("- 暂无可汇总标的。")
        return
    group_order = ["宽基", "行业", "主题", "防御"]
    grouped = df.groupby("group", dropna=False)
    rows = []
    for group, group_df in grouped:
        rows.append(
            {
                "group": group,
                "count": len(group_df),
                "buy": int((group_df["signal"] == "BUY").sum()),
                "watch": int((group_df["signal"] == "WATCH").sum()),
                "sell": int((group_df["signal"] == "SELL").sum()),
                "relative_strength": group_df["relative_strength"].mean(skipna=True),
                "return_20d": group_df["return_20d"].mean(skipna=True),
                "return_5d": group_df["return_5d"].mean(skipna=True),
                "volume_ratio": group_df["volume_ratio"].mean(skipna=True),
                "composite_score": group_df["composite_score"].mean(skipna=True) if "composite_score" in group_df.columns else float("nan"),
                "watch_score": group_df["watch_score"].mean(skipna=True) if "watch_score" in group_df.columns else float("nan"),
            }
        )
    rows.sort(key=lambda item: (group_order.index(item["group"]) if item["group"] in group_order else 99, str(item["group"])))

    lines.append("| group | 标的数量 | BUY | WATCH | SELL | 平均 relative_strength | 平均 return_20d | 平均 return_5d | 平均 volume_ratio | 平均 composite_score | 平均 watch_score |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item in rows:
        lines.append(
            f"| {item['group']} | {item['count']} | {item['buy']} | {item['watch']} | {item['sell']} | "
            f"{_fmt_number(item['relative_strength'])} | {_fmt_number(item['return_20d'])} | {_fmt_number(item['return_5d'])} | {_fmt_number(item['volume_ratio'])} | "
            f"{_fmt_number(item['composite_score'])} | {_fmt_number(item['watch_score'])} |"
        )


def _watch_score(signal: Signal | None, row: pd.Series) -> float:
    if signal is None:
        return 0.0
    block_count = _split_count(signal.block_reasons)
    reasons = str(signal.reasons or "")
    blocks = str(signal.block_reasons or "")
    relative_strength = _numeric_row_value(row, "relative_strength")
    volume_ratio = _numeric_row_value(row, "volume_ratio")
    return_20d = _numeric_row_value(row, "ret20")

    score = max(0.0, 40.0 - block_count * 8.0)
    score += 10.0 if "收盘价站上 MA20" in reasons else 0.0
    score += 10.0 if "收盘价站上 MA60" in reasons else 0.0
    score += 10.0 if "MA20 向上" in reasons else 0.0
    score += 12.0 if not pd.isna(relative_strength) and relative_strength > 0 else 0.0
    score += 10.0 if not pd.isna(volume_ratio) and VOLUME_RATIO_MIN <= volume_ratio <= VOLUME_RATIO_MAX else 0.0
    score += 8.0 if not pd.isna(return_20d) and return_20d <= MAX_20D_RETURN_TO_CHASE else 0.0
    score += 8.0 if "价格距离 MA20 不远" in reasons else 0.0
    if _has_serious_risk_block(blocks):
        score -= 20.0
    return _clamp_score(score)


def _clamp_score(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return round(min(100.0, max(0.0, numeric)), 6)


def _has_serious_risk_block(block_reasons: str) -> bool:
    serious_keywords = ["风控", "现金", "仓位", "超限", "不允许", "最大", "最低现金", "持仓数量"]
    return any(keyword in block_reasons for keyword in serious_keywords)


def _split_count(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return len([item for item in text.split("；") if item.strip()])


def _metric_score(value: float, scale: float) -> float:
    if pd.isna(value):
        return 0.0
    return float(value) * scale


def _numeric_row_value(row: pd.Series | None, column: str) -> float:
    if row is None or column not in row:
        return float("nan")
    value = pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0]
    return float(value) if not pd.isna(value) else float("nan")


def _fmt_number(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.6f}".rstrip("0").rstrip(".")


def _append_signal_list(lines: list[str], signals: list[Signal], empty_text: str) -> None:
    if not signals:
        lines.append(f"- {empty_text}")
        return
    for signal in signals:
        lines.append(
            f"- {signal.code} {signal.name}：止损价 {signal.stop_loss_price:.4f}，"
            f"建议 {signal.suggested_amount:.2f} 元 / {signal.suggested_shares} 份/股；"
            f"原因：{signal.reasons}"
        )


def _append_group_overview(lines: list[str], signals: list[Signal]) -> None:
    group_order = ["宽基", "行业", "主题", "防御"]
    for group in group_order:
        group_signals = [signal for signal in signals if signal.group == group]
        lines.append(f"### {group}")
        if group_signals:
            _append_signal_table(lines, group_signals)
        else:
            lines.append("- 暂无标的")

    other_groups = sorted({signal.group for signal in signals if signal.group not in group_order})
    for group in other_groups:
        lines.append(f"### {group}")
        _append_signal_table(lines, [signal for signal in signals if signal.group == group])


def _append_signal_table(lines: list[str], signals: list[Signal]) -> None:
    lines.append("| 代码 | 名称 | 信号 | 收盘价 | 主要原因 | 禁止交易原因 |")
    lines.append("| --- | --- | --- | ---: | --- | --- |")
    for signal in signals:
        lines.append(
            f"| {signal.code} | {signal.name} | {signal.signal} | {signal.close:.4f} | "
            f"{_escape_cell(_short_text(signal.reasons or '无'))} | {_escape_cell(_short_text(signal.block_reasons or '无'))} |"
        )


def _row_value(row: pd.Series | None, column: str) -> float | str:
    if row is None or column not in row:
        return ""
    value = row[column]
    if pd.isna(value):
        return ""
    return round(float(value), 6)


def _short_text(value: str, max_len: int = 80) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _escape_cell(value: str) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def _risk_violations(account: SimAccount, latest_prices: dict[str, float]) -> list[str]:
    violations = []
    market_value = account.market_value(latest_prices)
    if account.cash < MIN_CASH:
        violations.append(f"现金 {account.cash:.2f} 元，低于最低现金 {MIN_CASH:.2f} 元")
    if market_value > MAX_POSITION_VALUE:
        violations.append(f"持仓市值 {market_value:.2f} 元，超过最大总仓位 {MAX_POSITION_VALUE:.2f} 元")
    return violations
