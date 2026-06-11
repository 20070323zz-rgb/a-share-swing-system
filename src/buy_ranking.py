"""BUY ETF ranking and first paper buy plan.

This module ranks existing ETF BUY candidates for paper-trading research only.
It does not connect to broker APIs, place orders, or write paper trades.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import INITIAL_CASH, REPORT_DIR
from signal_engine import Signal


BUY_RANKING_REPORT_FILE = REPORT_DIR / "buy_signal_ranking.md"
LEGACY_BUY_RANKING_REPORT_FILE = REPORT_DIR / "buy_ranking_report.md"
LATEST_BUY_RANKING_FILE = REPORT_DIR / "latest_buy_ranking.md"
FIRST_PAPER_BUY_PLAN_FILE = REPORT_DIR / "first_paper_buy_plan.md"

MAX_SINGLE_ETF_AMOUNT = INITIAL_CASH * 0.20
MAX_HOLDINGS = 3
MIN_AVG_AMOUNT = 10_000_000.0
MIN_AVG_VOLUME = 500_000.0


def build_buy_ranking(
    run_date: str,
    watchlist: pd.DataFrame,
    latest_rows: dict[str, pd.Series],
    price_history: dict[str, pd.DataFrame],
    mid_signals: list[Signal],
    short_signals: list[Signal],
    cycle_rows: list[dict],
    health_summary: dict | None = None,
) -> list[dict]:
    """Build ranked ETF BUY candidates from existing mid/short signals."""
    mid_map = {item.code: item for item in mid_signals}
    short_map = {item.code: item for item in short_signals}
    cycle_map = {str(item.get("code")): item for item in cycle_rows}
    excluded_codes = _excluded_expansion_codes()
    health_summary = health_summary or {}
    health_blocked = set(health_summary.get("error_symbols", [])) | set(health_summary.get("missing_symbols", []))
    health_warning = set(health_summary.get("warning_symbols", []))
    rows: list[dict] = []

    for _, meta in watchlist.iterrows():
        code = str(meta.get("code", "")).strip()
        type_name = str(meta.get("type", "ETF")).upper()
        role = str(meta.get("role", "trade_pool"))
        enabled = bool(meta.get("enabled", False))
        if not code or type_name != "ETF" or role != "trade_pool" or not enabled:
            continue
        if code in excluded_codes:
            continue
        if code in health_blocked:
            continue

        mid = mid_map.get(code)
        short = short_map.get(code)
        if not mid or not short:
            continue
        if mid.signal != "BUY" and short.signal != "BUY":
            continue

        latest = latest_rows.get(code)
        history = price_history.get(code)
        if latest is None or history is None or history.empty:
            continue

        liquidity = _liquidity_metrics(history, latest)
        if liquidity["liquidity_failed"]:
            continue

        group = str(meta.get("group", ""))
        caution_flags = _caution_flags(group, latest, run_date)
        if code in health_warning:
            caution_flags.append("data_health 提醒，需人工复核")
        mid_score = _mid_trend_score(mid, latest)
        short_score = _short_momentum_score(short, latest)
        liquidity_score = _liquidity_score(liquidity)
        risk_score = _risk_score(history, latest)
        resonance_score = _resonance_score(mid, short, cycle_map.get(code))
        data_quality_score = _data_quality_score(history, latest, run_date, caution_flags)
        rank_score = round(
            mid_score + short_score + liquidity_score + risk_score + resonance_score + data_quality_score,
            6,
        )

        rows.append(
            {
                "date": run_date,
                "code": code,
                "name": str(meta.get("name", code)),
                "group": group,
                "mid_signal": mid.signal,
                "short_signal": short.signal,
                "rank_score": rank_score,
                "mid_trend_score": round(mid_score, 6),
                "short_momentum_score": round(short_score, 6),
                "liquidity_score": round(liquidity_score, 6),
                "risk_score": round(risk_score, 6),
                "resonance_score": round(resonance_score, 6),
                "data_quality_score": round(data_quality_score, 6),
                "close": _num(latest.get("close")),
                "return_5d": _num(latest.get("ret5")),
                "return_20d": _num(latest.get("ret20")),
                "relative_strength": _num(latest.get("relative_strength")),
                "volume_ratio": _num(latest.get("volume_ratio")),
                "avg_amount_20d": round(liquidity["avg_amount_20d"], 2),
                "avg_volume_20d": round(liquidity["avg_volume_20d"], 2),
                "caution": "；".join(caution_flags),
                "reasons": mid.reasons if mid.signal == "BUY" else short.reasons,
                "execution_price_type": "close_price",
                "is_paper_buy_candidate": True,
            }
        )

    return sorted(rows, key=lambda item: item["rank_score"], reverse=True)


def write_buy_ranking_report(
    run_date: str,
    watchlist: pd.DataFrame,
    latest_rows: dict[str, pd.Series],
    price_history: dict[str, pd.DataFrame],
    mid_signals: list[Signal],
    short_signals: list[Signal],
    cycle_rows: list[dict],
    health_summary: dict | None = None,
) -> tuple[Path, list[dict]]:
    """Write BUY ETF ranking report and return ranking rows."""
    rows = build_buy_ranking(run_date, watchlist, latest_rows, price_history, mid_signals, short_signals, cycle_rows, health_summary)
    lines = [
        f"# BUY ETF 排名报告 {run_date}",
        "",
        "本报告只对 ETF 模拟盘 BUY 候选排序，不接券商 API，不下单，不读取账号密码。",
        "",
        "## 评分说明",
        "- rank_score 为 100 分制 proxy score：mid_trend 30%，short_momentum 25%，liquidity 15%，risk 15%，resonance 10%，data_quality 5%。",
        "- 当前字段不足以判断实时盘口、ETF 溢价率和日内分时成交，相关风险以 caution 标注。",
        "- QDII、跨境、港股类 ETF 若无法判断溢价/滞后风险，会降低 data_quality 得分或标注 caution。",
        "- failed_validation / quarantine / unresolved / excluded ETF 不参与排名。",
        "",
        "## Top BUY Ranking",
    ]
    _append_ranking_table(lines, rows[:10])
    lines += [
        "",
        "## 全部 BUY 候选得分拆解",
    ]
    _append_ranking_table(lines, rows)
    lines += [
        "",
        "## 安全边界",
        "- 本报告只生成模拟盘排序，不生成真实交易指令。",
        "- 不接券商 API，不真实下单，不保存账号密码或 token。",
    ]
    BUY_RANKING_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LEGACY_BUY_RANKING_REPORT_FILE.write_text(BUY_RANKING_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    LATEST_BUY_RANKING_FILE.write_text(BUY_RANKING_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return BUY_RANKING_REPORT_FILE, rows


def build_paper_buy_allocations(
    ranking_rows: list[dict],
    paper_summary: dict,
    benchmark_row: pd.Series | None,
) -> tuple[str, float, list[dict]]:
    market_state, total_position_ratio = _market_state(benchmark_row, ranking_rows)
    max_total_amount = round(INITIAL_CASH * total_position_ratio, 2)
    available_cash = float(paper_summary.get("cash", INITIAL_CASH) or INITIAL_CASH)
    existing_positions = int(paper_summary.get("position_count", 0) or 0)
    slots = max(0, MAX_HOLDINGS - existing_positions)
    selected = ranking_rows[:slots]
    return market_state, total_position_ratio, _allocate_amounts(selected, max_total_amount, available_cash)


def write_first_paper_buy_plan(
    run_date: str,
    ranking_rows: list[dict],
    paper_summary: dict,
    benchmark_row: pd.Series | None,
    execution_result: dict | None = None,
    planned_allocations: list[dict] | None = None,
) -> Path:
    """Write the first paper buy plan and execution summary."""
    market_state, total_position_ratio, allocations = build_paper_buy_allocations(ranking_rows, paper_summary, benchmark_row)
    if planned_allocations is not None:
        allocations = planned_allocations
    max_total_amount = round(INITIAL_CASH * total_position_ratio, 2)
    execution_result = execution_result or {"executed": [], "skipped": []}
    executed = execution_result.get("executed", [])
    if not executed:
        executed = _existing_execution_rows(run_date)

    lines = [
        f"# 第一次模拟买入计划 {run_date}",
        "",
        "本计划只用于模拟盘和学习复盘，不接券商 API，不真实下单。",
        "",
        "## 当前已使用的因子",
        "- trend / momentum：MA10、MA20、MA60、MA10/MA20 slope、5/10/20/60 日收益。",
        "- RSI：rsi14 用于识别短期过热/过冷的风险辅助，不改变核心 BUY/SELL 规则。",
        "- relative strength：相对沪深300ETF 基准的 10/20/60 日相对强弱。",
        "- volume / liquidity：volume、volume_ma5、volume_ma20、volume_ratio、近 20 日成交额 proxy。",
        "- risk：20 日波动、20 日最大回撤、距离 MA10/MA20、追高过滤。",
        "- group / ETF category：宽基、金融地产、科技成长、周期资源、防御风格、QDII/跨境等分组标注。",
        "- mid_trend / short_swing：中期主策略与短期实验策略双周期信号。",
        "",
        "## 当前 BUY ETF 排名",
    ]
    _append_ranking_table(lines, ranking_rows[:10])
    lines += [
        "",
        "## 市场状态与总仓位",
        f"- 市场状态：{market_state}",
        f"- 建议总仓位比例：{total_position_ratio:.0%}",
        f"- 模拟本金：{INITIAL_CASH:.2f} 元",
        f"- 建议总买入上限：{max_total_amount:.2f} 元",
        f"- 单只 ETF 上限：{MAX_SINGLE_ETF_AMOUNT:.2f} 元",
        f"- 同时最多持有：{MAX_HOLDINGS} 只 ETF",
        "",
        "## 建议模拟买入列表",
    ]
    if not allocations:
        if executed:
            lines.append("- 同日模拟买入已写入，当前不重复加仓。")
        else:
            lines.append("- 当前无可执行的模拟买入候选。")
    else:
        lines.append("| rank | code | name | signal | rank_score | suggested_amount | execution_window | execution_price_type | caution |")
        lines.append("| ---: | --- | --- | --- | ---: | ---: | --- | --- | --- |")
        for item in allocations:
            lines.append(
                f"| {item['rank']} | {item['code']} | {item['name']} | "
                f"{item['mid_signal']} / {item['short_signal']} | {item['rank_score']:.6f} | "
                f"{item['suggested_amount']:.2f} | 今日收盘价 | close_price | {item.get('caution', '')} |"
            )
    lines += [
        "",
        "## 模拟执行时间规则",
        "- 信号基于收盘后日线数据生成。",
        "- 人工复核在当晚或次日中午完成。",
        "- 普通买入执行窗口：次日 14:30-14:50。",
        "- 普通卖出执行窗口：次日 14:30-14:50。",
        "- 不主动在 9:30-10:00 开盘阶段买入。",
        "- 不在 14:55-15:00 追单。",
        "- 风控止损允许 10:30 后执行。",
        "- 本次已获用户确认，第一次模拟买入使用今天收盘价写入本地模拟盘。",
        "- execution_price_type：close_price。",
        "",
        "## 本次模拟买入执行结果",
    ]
    if executed:
        lines.append("| trade_date | code | name | amount | price | quantity | execution_price_type | order_type | source | reason |")
        lines.append("| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |")
        for item in executed:
            lines.append(
                f"| {item['trade_date']} | {item['symbol']} | {item['name']} | {float(item['amount']):.2f} | "
                f"{float(item['price']):.6f} | {int(item['quantity'])} | {item['execution_price_type']} | "
                f"{item['order_type']} | {item['source']} | {str(item['reason']).replace('|', '/')} |"
            )
    else:
        lines.append("- 本次未写入模拟买入。")
    skipped = execution_result.get("skipped", [])
    if skipped:
        lines += ["", "## 跳过记录"]
        for item in skipped:
            lines.append(f"- {item.get('code')} {item.get('name', '')}: {item.get('skip_reason', '')}")

    lines += [
        "",
        "",
        "## 风险点",
        "- 当前排名使用日线 proxy score，不含实时盘口、折溢价、申赎清单和分时冲击成本。",
        "- QDII、跨境、港股类 ETF 可能存在净值滞后、汇率、假期错位和溢价风险。",
        "- 单日涨幅过大、成交额过低、数据健康异常或信号转弱时，应放弃模拟执行。",
        "",
        "## 失效条件",
        "- 次日收盘前 ETF 跌破 MA20 或出现明显放量长阴。",
        "- 最新 data_health 出现异常或行情缺失。",
        "- rank_score 明显下降，或 mid_trend / short_swing 信号不再满足计划对应条件。",
        "- 人工复核发现溢价、停牌、成交异常或不可解释的数据问题。",
        "",
        "## 是否建议执行第一次模拟盘买入",
        f"- 结论：{'已按用户确认写入第一次模拟买入' if executed else '暂不买入'}。",
        "- 本系统只写本地模拟盘文件，不连接真实交易账户。",
        "",
        "## 需要用户最终确认的模拟交易列表",
    ]
    if not allocations:
        lines.append("- 无。")
    else:
        for item in allocations:
            lines.append(
                f"- BUY {item['code']} {item['name']}，计划模拟金额 {item['suggested_amount']:.2f} 元，"
                "execution_price_type=close_price。"
            )
    lines += [
        "",
        "## 安全边界",
        "- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。",
        "- 本轮如有合格 BUY，已经只写入 data/paper_positions.csv / data/paper_trades.csv。",
    ]
    FIRST_PAPER_BUY_PLAN_FILE.write_text("\n".join(lines), encoding="utf-8")
    return FIRST_PAPER_BUY_PLAN_FILE


def _append_ranking_table(lines: list[str], rows: list[dict]) -> None:
    if not rows:
        lines.append("- 暂无 BUY ETF 候选。")
        return
    lines.append(
        "| rank | code | name | group | mid | short | rank_score | mid_trend | short_momentum | liquidity | risk | resonance | data_quality | 双周期共振 | 风险提示 | 进入模拟买入候选 |"
    )
    lines.append("| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |")
    for idx, row in enumerate(rows, start=1):
        resonance = "是" if row.get("mid_signal") == "BUY" and row.get("short_signal") == "BUY" else "否"
        candidate = "是" if row.get("is_paper_buy_candidate") else "否"
        lines.append(
            f"| {idx} | {row['code']} | {row['name']} | {row['group']} | {row['mid_signal']} | {row['short_signal']} | "
            f"{row['rank_score']:.6f} | {row['mid_trend_score']:.6f} | {row['short_momentum_score']:.6f} | "
            f"{row['liquidity_score']:.6f} | {row['risk_score']:.6f} | {row['resonance_score']:.6f} | "
            f"{row['data_quality_score']:.6f} | {resonance} | {row.get('caution', '')} | {candidate} |"
        )


def _existing_execution_rows(run_date: str) -> list[dict]:
    trades_path = Path(__file__).resolve().parents[1] / "data" / "paper_trades.csv"
    if not trades_path.exists() or trades_path.stat().st_size == 0:
        return []
    trades = pd.read_csv(trades_path, dtype=str).fillna("")
    required = {"date", "symbol", "action", "source"}
    if not required.issubset(set(trades.columns)):
        return []
    dates = pd.to_datetime(trades["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    rows = trades[
        (dates == run_date)
        & (trades["action"].astype(str).str.upper() == "BUY")
        & (trades["source"].astype(str) == "buy_signal_ranking")
    ].copy()
    if rows.empty:
        return []
    normalized: list[dict] = []
    for row in rows.to_dict(orient="records"):
        normalized.append(
            {
                "trade_date": row.get("trade_date") or row.get("date") or run_date,
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "amount": float(row.get("amount") or 0.0),
                "price": float(row.get("price") or 0.0),
                "quantity": int(float(row.get("quantity") or 0.0)),
                "execution_price_type": row.get("execution_price_type", "close_price"),
                "order_type": row.get("order_type", "paper_buy"),
                "source": row.get("source", "buy_signal_ranking"),
                "reason": row.get("reason", ""),
                "already_recorded": True,
            }
        )
    return normalized


def _allocate_amounts(rows: list[dict], max_total_amount: float, available_cash: float) -> list[dict]:
    if not rows or max_total_amount <= 0 or available_cash <= 0:
        return []
    weights_map = {
        1: [1.0],
        2: [0.6, 0.4],
        3: [0.5, 0.3, 0.2],
    }
    weights = weights_map.get(len(rows), weights_map[3])
    usable_amount = min(max_total_amount, available_cash)
    allocations: list[dict] = []
    for idx, (row, weight) in enumerate(zip(rows, weights), start=1):
        amount = usable_amount * weight
        if len(rows) == 1:
            amount = min(amount, MAX_SINGLE_ETF_AMOUNT)
        else:
            amount = min(amount, MAX_SINGLE_ETF_AMOUNT)
        multiplier = _cycle_amount_multiplier(row)
        amount = round(amount * multiplier, 2)
        if amount <= 0:
            continue
        allocations.append({**row, "rank": idx, "suggested_amount": amount})
    return allocations


def _cycle_amount_multiplier(row: dict) -> float:
    mid = str(row.get("mid_signal", ""))
    short = str(row.get("short_signal", ""))
    if mid == "BUY" and short == "BUY":
        return 1.0
    if mid == "BUY" and short != "BUY":
        return 0.5
    if short == "BUY" and mid != "BUY":
        return 0.5
    return 0.0


def _market_state(benchmark_row: pd.Series | None, ranking_rows: list[dict]) -> tuple[str, float]:
    if benchmark_row is None:
        return "market_neutral", 0.30
    close = _num(benchmark_row.get("close"))
    ma20 = _num(benchmark_row.get("ma20"))
    ma60 = _num(benchmark_row.get("ma60"))
    ret20 = _num(benchmark_row.get("ret20"))
    strong_count = sum(1 for row in ranking_rows if row.get("mid_signal") == "BUY" and row.get("short_signal") == "BUY")
    if close > ma20 > ma60 and ret20 > 0 and strong_count >= 3:
        return "market_strong", 0.50
    if close > ma60 or ret20 > -0.03 or strong_count >= 1:
        return "market_neutral", 0.30
    return "market_weak", 0.10


def _mid_trend_score(signal: Signal, row: pd.Series) -> float:
    score = 0.0
    score += 8.0 if signal.signal == "BUY" else 3.0 if signal.signal == "WATCH" else 0.0
    score += 5.0 if _bool(row.get("close") > row.get("ma20")) else 0.0
    score += 5.0 if _bool(row.get("close") > row.get("ma60")) else 0.0
    score += 4.0 if _num(row.get("ma20_slope")) > 0 else 0.0
    score += _scale(_num(row.get("relative_strength")), -0.05, 0.10) * 5.0
    score += _scale(_num(row.get("ret20")), -0.05, 0.15) * 3.0
    return min(score, 30.0)


def _short_momentum_score(signal: Signal, row: pd.Series) -> float:
    score = 0.0
    score += 7.0 if signal.signal == "BUY" else 3.0 if signal.signal == "WATCH" else 0.0
    score += 4.0 if _bool(row.get("close") > row.get("ma10")) else 0.0
    score += 4.0 if _num(row.get("ma10_slope")) > 0 else 0.0
    score += _scale(_num(row.get("relative_strength_10")), -0.04, 0.08) * 4.0
    score += _scale(_num(row.get("ret5")), -0.03, 0.08) * 4.0
    score += _scale(_num(row.get("volume_ratio")), 0.8, 2.0) * 2.0
    return min(score, 25.0)


def _liquidity_score(metrics: dict) -> float:
    amount_score = _scale(metrics["avg_amount_20d"], MIN_AVG_AMOUNT, 200_000_000.0) * 10.0
    volume_score = _scale(metrics["avg_volume_20d"], MIN_AVG_VOLUME, 50_000_000.0) * 5.0
    return min(amount_score + volume_score, 15.0)


def _risk_score(history: pd.DataFrame, row: pd.Series) -> float:
    close = pd.to_numeric(history["close"], errors="coerce")
    daily_ret = close.pct_change()
    volatility = float(daily_ret.tail(20).std()) if len(daily_ret.dropna()) >= 5 else 0.0
    recent = close.tail(20)
    max_drawdown = 0.0
    if not recent.empty:
        max_drawdown = float((recent / recent.cummax() - 1).min())
    distance_ma20 = abs(_num(row.get("distance_above_ma20")))
    ret5 = _num(row.get("ret5"))
    score = 15.0
    score -= _scale(volatility, 0.015, 0.06) * 4.0
    score -= _scale(abs(max_drawdown), 0.03, 0.18) * 4.0
    score -= _scale(distance_ma20, 0.03, 0.15) * 4.0
    score -= _scale(ret5, 0.06, 0.12) * 3.0
    return max(0.0, min(score, 15.0))


def _resonance_score(mid: Signal, short: Signal, cycle: dict | None) -> float:
    if mid.signal == "BUY" and short.signal == "BUY":
        return 10.0
    if mid.signal == "BUY" and short.signal == "WATCH":
        return 5.0
    if mid.signal == "WATCH" and short.signal == "BUY":
        return 4.0
    if cycle and str(cycle.get("resonance_type")) in {"STRONG_RESONANCE", "MID_HOLD", "SHORT_TRIAL"}:
        return 3.0
    return 0.0


def _data_quality_score(history: pd.DataFrame, row: pd.Series, run_date: str, caution_flags: list[str]) -> float:
    if history.empty:
        return 0.0
    score = 5.0
    latest_date = pd.to_datetime(row.get("date"), errors="coerce")
    if pd.isna(latest_date) or latest_date.strftime("%Y-%m-%d") != run_date:
        score -= 2.0
    if len(history) < 120:
        score -= 1.0
    required = ["open", "high", "low", "close", "volume"]
    if any(pd.isna(row.get(col)) for col in required):
        score -= 3.0
    if caution_flags:
        score = min(score, 3.0)
    return max(0.0, min(score, 5.0))


def _liquidity_metrics(history: pd.DataFrame, row: pd.Series) -> dict:
    recent = history.tail(20).copy()
    volume = pd.to_numeric(recent.get("volume", pd.Series(dtype=float)), errors="coerce")
    avg_volume = float(volume.mean()) if not volume.empty else 0.0
    amount_col = "amount" if "amount" in recent.columns else "money" if "money" in recent.columns else ""
    if amount_col:
        amount = pd.to_numeric(recent[amount_col], errors="coerce")
        avg_amount = float(amount.mean()) if not amount.empty else 0.0
    else:
        close = pd.to_numeric(recent.get("close", pd.Series(dtype=float)), errors="coerce")
        avg_amount = float((close * volume).mean()) if not close.empty and not volume.empty else 0.0
    return {
        "avg_volume_20d": avg_volume,
        "avg_amount_20d": avg_amount,
        "liquidity_failed": avg_amount < MIN_AVG_AMOUNT and avg_volume < MIN_AVG_VOLUME,
    }


def _caution_flags(group: str, row: pd.Series, run_date: str) -> list[str]:
    flags: list[str] = []
    group_text = str(group)
    if any(key in group_text for key in ["QDII", "跨境", "港股", "海外"]):
        flags.append("QDII/跨境溢价或净值滞后风险未纳入")
    latest_date = pd.to_datetime(row.get("date"), errors="coerce")
    if pd.isna(latest_date) or latest_date.strftime("%Y-%m-%d") != run_date:
        flags.append("最新行情日期与运行日期不一致")
    return flags


def _excluded_expansion_codes() -> set[str]:
    root = Path(__file__).resolve().parents[1]
    excluded: set[str] = set()
    candidates = root / "data" / "etf_pool_expansion_candidates.csv"
    if candidates.exists():
        df = pd.read_csv(candidates, dtype=str).fillna("")
        if "status" in df.columns and "code" in df.columns:
            bad = df["status"].isin(["failed_validation", "failed_dry_run", "unresolved", "excluded"])
            excluded.update(df.loc[bad, "code"].astype(str).str.extract(r"(\d{6})", expand=False).dropna().tolist())
    quarantine_dir = root / "data" / "staging" / "jqdata_expanded_failed"
    if quarantine_dir.exists():
        for path in quarantine_dir.glob("*.csv"):
            code = path.name.split(".")[0]
            if len(code) == 6 and code.isdigit():
                excluded.add(code)
    return excluded


def _num(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return numeric


def _bool(value: object) -> bool:
    try:
        return bool(value)
    except Exception:
        return False


def _scale(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))
