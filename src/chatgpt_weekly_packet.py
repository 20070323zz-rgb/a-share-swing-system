"""Generate the standard ChatGPT/Main weekly analysis packet.

This script is read-only with respect to the paper account. It summarizes local
reports into Markdown and JSON for review, and never changes trading rules,
paper trades, paper positions, broker state, or credentials.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, PROJECT_ROOT, REPORT_DIR


LATEST_MD = REPORT_DIR / "chatgpt_weekly_analysis_packet_latest.md"
LATEST_JSON = REPORT_DIR / "chatgpt_weekly_analysis_packet_latest.json"
DATED_ARCHIVE_DIR = REPORT_DIR / "archive" / "chatgpt_packets"

SOURCE_FILES = {
    "dashboard_data": REPORT_DIR / "dashboard_data.json",
    "paper_performance": REPORT_DIR / "paper_performance_summary.json",
    "paper_performance_md": REPORT_DIR / "paper_performance_summary.md",
    "portfolio_exposure": REPORT_DIR / "portfolio_exposure.json",
    "portfolio_exposure_md": REPORT_DIR / "portfolio_exposure.md",
    "position_review": REPORT_DIR / "position_review_state.json",
    "position_review_md": REPORT_DIR / "position_review_state.md",
    "profit_protection": REPORT_DIR / "profit_protection_preview.json",
    "profit_protection_md": REPORT_DIR / "profit_protection_preview.md",
    "high_beta": REPORT_DIR / "high_beta_risk_watch.json",
    "high_beta_md": REPORT_DIR / "high_beta_risk_watch.md",
    "broad_base": REPORT_DIR / "broad_base_balance_preview.json",
    "broad_base_md": REPORT_DIR / "broad_base_balance_preview.md",
    "data_coverage": REPORT_DIR / "latest_data_coverage.md",
    "data_health": REPORT_DIR / "latest_data_health.md",
    "data_download": REPORT_DIR / "data_download_report.md",
    "model_data_maturity": REPORT_DIR / "model_data_maturity_analysis.json",
    "shadow_weekly": REPORT_DIR / "shadow_observation_weekly.json",
    "shadow_weekly_md": REPORT_DIR / "shadow_observation_weekly.md",
    "missed_opportunity": REPORT_DIR / "missed_opportunity_tracker.md",
    "persistence_signal": REPORT_DIR / "persistence_breakout_shadow_signal.csv",
    "model_shadow_comparison": REPORT_DIR / "model_shadow_comparison.csv",
    "ranking_report_csv": REPORT_DIR / "ranking_report.csv",
    "latest_ranking_csv": REPORT_DIR / "latest_ranking.csv",
    "adjusted_preview_csv": REPORT_DIR / "adjusted_preview.csv",
    "paper_trades": PAPER_TRADES_FILE,
    "paper_positions": PAPER_POSITIONS_FILE,
    "paper_equity_curve": DATA_DIR / "paper_equity_curve.csv",
    "paper_equity_curve_backfilled": DATA_DIR / "paper_equity_curve_backfilled.csv",
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATED_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    generated_date = packet["as_of_date"] or pd.Timestamp.now().strftime("%Y-%m-%d")
    dated_md = DATED_ARCHIVE_DIR / f"chatgpt_weekly_analysis_packet_{generated_date}.md"
    dated_json = DATED_ARCHIVE_DIR / f"chatgpt_weekly_analysis_packet_{generated_date}.json"

    markdown = normalize_markdown(render_markdown(packet))
    payload = _clean_json(packet)

    for path in [LATEST_MD, dated_md]:
        path.write_text(markdown, encoding="utf-8")
    for path in [LATEST_JSON, dated_json]:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"written: {LATEST_MD}")
    print(f"written: {LATEST_JSON}")
    print(f"written: {dated_md}")
    print(f"written: {dated_json}")


def normalize_markdown(text: str) -> str:
    """Remove non-semantic line-end whitespace and keep one final newline."""
    cleaned = "\n".join(line.rstrip(" \t") for line in text.splitlines())
    return cleaned.rstrip("\n") + "\n"


def build_packet() -> dict[str, Any]:
    dashboard = _read_json(SOURCE_FILES["dashboard_data"])
    performance = _read_json(SOURCE_FILES["paper_performance"])
    exposure = _read_json(SOURCE_FILES["portfolio_exposure"])
    review = _read_json(SOURCE_FILES["position_review"])
    profit = _read_json(SOURCE_FILES["profit_protection"])
    high_beta = _read_json(SOURCE_FILES["high_beta"])
    broad = _read_json(SOURCE_FILES["broad_base"])
    maturity = _read_json(SOURCE_FILES["model_data_maturity"])
    shadow = _read_json(SOURCE_FILES["shadow_weekly"])
    trades = _read_csv(SOURCE_FILES["paper_trades"])
    positions = _read_csv(SOURCE_FILES["paper_positions"])
    equity_curve = _read_csv(SOURCE_FILES["paper_equity_curve"])
    equity_curve_backfilled = _read_csv(SOURCE_FILES["paper_equity_curve_backfilled"])

    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    as_of_date = str(
        dashboard.get("latest_data_date")
        or performance.get("latest_data_date")
        or performance.get("valuation_as_of_date")
        or (exposure.get("summary") or {}).get("as_of_date")
        or pd.Timestamp.now().strftime("%Y-%m-%d")
    )

    data_status = _data_status(dashboard, maturity)
    paper_account = _paper_account(performance, dashboard, equity_curve, equity_curve_backfilled)
    position_rows = _positions(positions, dashboard, review, profit, high_beta)
    weekly_trades = _weekly_trades(trades, generated_at)
    buy_ranking = _buy_ranking(dashboard)
    adjusted_preview = _adjusted_preview(dashboard)
    review_states = _review_states(review)
    profit_protection = _profit_protection(profit)
    high_beta_risk = _high_beta_risk(high_beta)
    broad_base_balance = _broad_base_balance(broad)
    shadow_status = _shadow_status(shadow, dashboard)
    valuation_consistency = _valuation_consistency(dashboard, exposure)
    data_health = _data_health(dashboard)
    questions = _chatgpt_questions()
    safety = _safety_boundary()
    missing_sources = _missing_sources()
    core_conclusions = _core_conclusions(
        paper_account,
        review_states,
        profit_protection,
        high_beta_risk,
        broad_base_balance,
        shadow_status,
        data_status,
    )

    return {
        "as_of_date": as_of_date,
        "generated_at": generated_at,
        "packet_type": "chatgpt_main_weekly_analysis_packet",
        "research_only": True,
        "data_status": data_status,
        "paper_account": paper_account,
        "positions": position_rows,
        "weekly_trades": weekly_trades,
        "buy_ranking": buy_ranking,
        "adjusted_preview": adjusted_preview,
        "review_states": review_states,
        "profit_protection": profit_protection,
        "high_beta_risk": high_beta_risk,
        "broad_base_balance": broad_base_balance,
        "shadow_status": shadow_status,
        "valuation_consistency": valuation_consistency,
        "data_health": data_health,
        "core_conclusions": core_conclusions,
        "chatgpt_questions": questions,
        "chatgpt_questions_markdown": _chatgpt_questions_markdown(questions),
        "safety_boundary": safety,
        "missing_sources": missing_sources,
        "source_classification": {
            "formal_paper_account": ["data/paper_trades.csv", "data/paper_positions.csv", "reports/paper_performance_summary.json"],
            "research_preview": ["reports/strategy_enhancement_preview.csv", "reports/broad_base_balance_preview.json"],
            "shadow": ["reports/shadow_observation_weekly.json", "reports/persistence_breakout_shadow_signal.csv"],
            "backtest_or_research": ["reports/model_shadow_comparison.csv", "reports/model_data_maturity_analysis.json"],
            "estimated_backfill": ["data/paper_equity_curve_backfilled.csv"],
        },
    }


def render_markdown(packet: dict[str, Any]) -> str:
    p = packet["paper_account"]
    ds = packet["data_status"]
    review = packet["review_states"]
    profit = packet["profit_protection"]
    hb = packet["high_beta_risk"]
    bb = packet["broad_base_balance"]
    shadow = packet["shadow_status"]
    val = packet["valuation_consistency"]
    health = packet["data_health"]
    safety = packet["safety_boundary"]
    buy_ranking = packet["buy_ranking"]
    adjusted_preview = packet["adjusted_preview"]

    lines = [
        "# ChatGPT / Main 分析包：A 股 ETF 双周期模拟盘周报",
        "",
        "> 本报告用于研究分析，不是交易指令。",
        "> 安全边界：不接券商 API、不真实下单、不读取真实账户、不保存密码/token。",
        "> adjusted preview / shadow / profit protection / high_beta / broad base balance 均为观察层，不接执行层。",
        "",
        "---",
        "",
        "# 一、本周核心结论",
        "",
    ]
    lines.extend([f"- {item}" for item in packet["core_conclusions"]])
    lines += [
        "",
        "---",
        "",
        "# 二、数据与系统状态",
        "",
        f"- ETF 数据文件数量：{_na(ds.get('etf_file_count'))}",
        f"- 最新数据日：{_na(ds.get('latest_data_date'))}",
        f"- 本周数据更新状态：{_na(ds.get('data_update_status'))}",
        f"- 数据健康：{_na(health.get('status'))}",
        f"- 估值日期：{_na(p.get('valuation_as_of_date'))}",
        f"- 价格警告数量：{_na(val.get('price_warning_count'))}",
        f"- dashboard 更新时间：{_na(ds.get('dashboard_generated_at'))}",
        f"- App / dashboard 是否同步：{'是' if ds.get('dashboard_synced') else '否/待确认'}",
        "",
        "---",
        "",
        "# 三、正式模拟仓账户",
        "",
        f"- 当前现金：{_money(p.get('current_cash'))}",
        f"- 当前持仓市值：{_money(p.get('current_position_value'))}",
        f"- 当前总资产：{_money(p.get('current_total_equity'))}",
        f"- 总盈亏：{_money(p.get('total_pnl_amount'))}",
        f"- 总收益率：{_pct(p.get('total_return_pct'))}",
        f"- 已实现盈亏：{_money(p.get('realized_pnl'))}",
        f"- 未实现盈亏：{_money(p.get('unrealized_pnl'))}",
        f"- 最大回撤：{_pct(p.get('max_drawdown'))}",
        f"- 交易次数：{_na(p.get('trade_count'))}",
        f"- 胜率：{_pct(p.get('win_rate'))}",
        f"- 原始权益曲线条数：{_na(p.get('original_equity_curve_rows'))}",
        f"- 回填权益曲线条数：{_na(p.get('backfilled_equity_curve_rows'))}",
        f"- 当前盈利来源判断：{p.get('profit_source_note')}",
        "",
        "---",
        "",
        "# 四、当前持仓与观察状态",
        "",
        "| 代码 | 名称 | 组别 | 类型 | 市值 | 权重 | mid_trend | short_swing | review_state | profit_protection_state | high_beta_risk_state | recommended_review_action | 是否允许执行 |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in packet["positions"]:
        lines.append(
            f"| {row.get('symbol')} | {row.get('name')} | {row.get('group')} | {row.get('type')} | "
            f"{_money(row.get('market_value'))} | {_pct(row.get('weight'))} | {row.get('mid_trend')} | {row.get('short_swing')} | "
            f"{row.get('review_state')} | {row.get('profit_protection_state')} | {row.get('high_beta_risk_state')} | "
            f"{_escape_pipe(row.get('recommended_review_action'))} | {str(row.get('execution_allowed')).lower()} |"
        )
    if not packet["positions"]:
        lines.append("|  | 当前无持仓 |  |  |  |  |  |  |  |  |  |  | false |")
    lines += [
        "",
        "---",
        "",
        "# 五、本周交易记录",
        "",
    ]
    if packet["weekly_trades"]["rows"]:
        lines += [
            "| 日期 | 代码 | 名称 | 动作 | 金额 | 原因 | 本地模拟 | 真实交易 |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
        for row in packet["weekly_trades"]["rows"]:
            lines.append(
                f"| {row.get('date')} | {row.get('symbol')} | {row.get('name')} | {row.get('action')} | "
                f"{_money(row.get('amount'))} | {_escape_pipe(row.get('reason'))} | 是 | 否 |"
            )
    else:
        lines.append("- 本周无模拟交易。")
    lines += [
        "",
        "- 是否真实交易：否。",
        "",
        "---",
        "",
        "# 六、BUY Ranking 与 adjusted preview",
        "",
        "## 原始 BUY ranking Top 10",
        "",
        "| rank | code | name | group | mid | short | rank_score |",
        "| ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in buy_ranking.get("top10", []):
        lines.append(f"| {row.get('rank')} | {row.get('symbol')} | {row.get('name')} | {row.get('group')} | {row.get('mid_trend')} | {row.get('short_swing')} | {_fmt(row.get('rank_score'))} |")
    lines += [
        "",
        "## adjusted preview Top 10",
        "",
        "| adjusted_rank | code | name | group | original_score | adjusted_score | execution_status |",
        "| ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in adjusted_preview.get("top10", []):
        lines.append(
            f"| {row.get('adjusted_rank_preview')} | {row.get('symbol')} | {row.get('name')} | {row.get('group')} | "
            f"{_fmt(row.get('original_rank_score'))} | {_fmt(row.get('adjusted_rank_score_preview'))} | {row.get('execution_status')} |"
        )
    lines += [
        "",
        f"- preview_only_not_executed 数量：{adjusted_preview.get('preview_only_count', 0)}",
        f"- 是否过度集中在主题/行业：{bb.get('theme_concentration_state')}",
        f"- 宽基/准宽基候选：{_join_symbols(bb.get('top_candidates', []))}",
        "- 是否接执行层：否。",
        "",
        "---",
        "",
        "# 七、卖出复核与减仓候选",
        "",
        f"- REVIEW_1：{_join_symbols(review.get('REVIEW_1', [])) or '无'}",
        f"- REVIEW_2：{_join_symbols(review.get('REVIEW_2', [])) or '无'}",
        f"- REDUCE_CANDIDATE：{_join_symbols(review.get('REDUCE_CANDIDATE', [])) or '无'}",
        f"- REDUCE：{_join_symbols(review.get('REDUCE', [])) or '无'}",
        f"- SELL：{_join_symbols(review.get('SELL', [])) or '无'}",
        "- REDUCE_CANDIDATE 只是观察状态，不自动卖出。",
        "",
        "---",
        "",
        "# 八、浮盈保护 Preview",
        "",
        f"- PROFIT_WATCH：{_join_symbols(profit.get('PROFIT_WATCH', [])) or '无'}",
        f"- PROFIT_PROTECTION_REVIEW：{_join_symbols(profit.get('PROFIT_PROTECTION_REVIEW', [])) or '无'}",
        f"- PROFIT_LOCK_CANDIDATE：{_join_symbols(profit.get('PROFIT_LOCK_CANDIDATE', [])) or '无'}",
        f"- 515000 当前状态：{_na(profit.get('focus_515000', {}).get('profit_protection_state'))}",
        f"- 515000 当前浮盈：{_money(profit.get('focus_515000', {}).get('current_unrealized_pnl'))}",
        f"- 515000 峰值浮盈：{_money(profit.get('focus_515000', {}).get('peak_unrealized_pnl'))}",
        f"- 515000 峰值回撤：{_money(profit.get('focus_515000', {}).get('drawdown_from_profit_peak'))} / {_pct(profit.get('focus_515000', {}).get('drawdown_from_profit_peak_pct'))}",
        "- 是否自动止盈：否。",
        "",
        "---",
        "",
        "# 九、high_beta 风险观察",
        "",
        f"- high_beta 持仓数量：{_na(hb.get('high_beta_position_count'))}",
        f"- high_beta 占总资产比例：{_pct(hb.get('high_beta_weight_of_equity'))}",
        f"- high_beta 占持仓市值比例：{_pct(hb.get('high_beta_weight_of_holdings'))}",
        f"- 金融地产组暴露：总资产 {_pct(hb.get('finance_real_estate_weight_of_equity'))} / 持仓 {_pct(hb.get('finance_real_estate_weight_of_holdings'))}",
        f"- 512880 当前状态：{_na(hb.get('focus_512880', {}).get('high_beta_risk_state'))}",
        f"- 是否 HB_CAUTION / HB_ELEVATED：{'是' if hb.get('is_caution_or_elevated') else '否'}",
        "- 是否自动减仓：否。",
        "",
        "---",
        "",
        "# 十、宽基平衡 Preview",
        "",
        f"- 当前宽基占比：{_pct(bb.get('broad_base_weight'))}",
        f"- 行业/主题占比：{_pct(bb.get('theme_weight'))}",
        f"- 金融地产组占比：{_pct(bb.get('finance_real_estate_weight'))}",
        f"- 科技成长组占比：{_pct(bb.get('tech_growth_weight'))}",
        f"- high_beta 占比：{_pct(bb.get('high_beta_weight'))}",
        f"- Top 宽基候选：{_join_symbols(bb.get('top_candidates', []))}",
        f"- 588000 状态：{_focus_text(bb.get('focus_588000'))}",
        f"- 159915 状态：{_focus_text(bb.get('focus_159915'))}",
        f"- 510300 状态：{_focus_text(bb.get('focus_510300'))}",
        f"- 500 元 hypothetic preview 改善：宽基到 {_pct(bb.get('preview_new_broad_base_weight'))}，金融地产到 {_pct(bb.get('preview_new_finance_real_estate_weight'))}，科技成长到 {_pct(bb.get('preview_new_tech_growth_weight'))}，high_beta 到 {_pct(bb.get('preview_new_high_beta_weight'))}。",
        "- 是否自动买入：否。",
        "",
        "---",
        "",
        "# 十一、Shadow / 研究模型状态",
        "",
        f"- 当前阶段：{_na(shadow.get('current_phase'))}",
        f"- evidence_level：{_na(shadow.get('evidence_level'))}",
        f"- ready_for_preview：{str(shadow.get('ready_for_preview')).lower()}",
        f"- ready_for_execution：{str(shadow.get('ready_for_execution')).lower()}",
        f"- persistence_breakout_v2 最新 selected：{_na(shadow.get('persistence_selected_count'))}",
        f"- missed opportunity 数量：{_na(shadow.get('missed_opportunity_candidate_count'))}",
        f"- matured forward return 样本：{_na(shadow.get('matured_forward_return_count'))}",
        f"- 是否允许放宽过滤：{str(shadow.get('ready_to_relax_filters')).lower()}",
        "- 是否允许接执行层：false",
        f"- 推荐动作：{_na(shadow.get('recommended_action'))}",
        "",
        "---",
        "",
        "# 十二、系统口径与风险提示",
        "",
        f"- 估值口径一致性：{_na(val.get('status'))}",
        f"- paper_performance vs portfolio_exposure 差异：{_money(val.get('paper_vs_exposure_diff'))}",
        f"- 是否有价格警告：{'是' if _float(val.get('price_warning_count')) else '否'}",
        f"- 是否有数据健康问题：{_na(health.get('status'))}",
        "- dashboard 是否可能误导：当前已分离正式模拟仓、观察层、shadow 和回填估算；仍需人工理解观察层不等于执行层。",
        "- 正式模拟仓与研究预览是否分离展示：是。",
        "",
        "---",
        "",
        "# 十三、需要 ChatGPT / Main 判断的问题",
        "",
        *packet["chatgpt_questions_markdown"],
        "",
        "---",
        "",
        "# 十四、禁止误读",
        "",
    ]
    lines.extend([f"- {item}" for item in safety["must_not_misread"]])
    lines += [
        "",
        "## 缺失来源文件",
        "",
    ]
    if packet["missing_sources"]:
        lines.extend([f"- {item}" for item in packet["missing_sources"]])
    else:
        lines.append("- 无关键来源缺失。")
    return "\n".join(lines) + "\n"


def _data_status(dashboard: dict, maturity: dict) -> dict:
    update = dashboard.get("data_update_status", {}) if isinstance(dashboard.get("data_update_status"), dict) else {}
    health = dashboard.get("health_summary", {}) if isinstance(dashboard.get("health_summary"), dict) else {}
    return {
        "etf_file_count": update.get("universe_size") or health.get("etf_file_count") or (maturity.get("etf_data", {}) or {}).get("etf_file_count"),
        "latest_data_date": dashboard.get("latest_data_date") or update.get("latest_local_date"),
        "data_update_status": update.get("status") or update.get("severity") or "unknown",
        "new_rows": update.get("added_rows", 0),
        "failed_count": update.get("failed_count", 0),
        "dashboard_generated_at": dashboard.get("generated_at"),
        "dashboard_synced": bool(dashboard.get("generated_at")),
    }


def _paper_account(performance: dict, dashboard: dict, equity_curve: list[dict], backfilled_curve: list[dict]) -> dict:
    summary = dashboard.get("paper_summary", {}) if isinstance(dashboard.get("paper_summary"), dict) else {}
    out = {
        "current_cash": performance.get("current_cash", summary.get("cash")),
        "current_position_value": performance.get("current_position_value", summary.get("position_value", summary.get("market_value"))),
        "current_total_equity": performance.get("current_total_equity", summary.get("total_equity")),
        "total_pnl_amount": performance.get("total_pnl_amount", summary.get("total_pnl")),
        "total_return_pct": performance.get("total_return_pct", summary.get("total_return_pct")),
        "realized_pnl": performance.get("realized_pnl"),
        "unrealized_pnl": performance.get("unrealized_pnl"),
        "max_drawdown": performance.get("max_drawdown"),
        "trade_count": performance.get("trade_count"),
        "win_rate": performance.get("win_rate"),
        "valuation_as_of_date": performance.get("valuation_as_of_date") or performance.get("latest_data_date") or dashboard.get("latest_data_date"),
        "original_equity_curve_rows": len(equity_curve),
        "backfilled_equity_curve_rows": len(backfilled_curve),
    }
    realized = _float(out.get("realized_pnl"))
    unrealized = _float(out.get("unrealized_pnl"))
    if abs(unrealized) > abs(realized):
        out["profit_source_note"] = "当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。"
    else:
        out["profit_source_note"] = "当前盈亏不主要由未实现浮盈驱动，但样本仍很少。"
    return out


def _positions(positions: list[dict], dashboard: dict, review: dict, profit: dict, high_beta: dict) -> list[dict]:
    dashboard_positions = dashboard.get("positions") or dashboard.get("positions_enhanced") or []
    base = dashboard_positions if dashboard_positions else positions
    review_map = _map_by_symbol(review.get("rows", []))
    profit_map = _map_by_symbol(profit.get("rows", []))
    hb_map = _map_by_symbol(high_beta.get("rows", []))
    rows = []
    for item in base:
        symbol = str(item.get("symbol") or item.get("code") or "")
        rv = review_map.get(symbol, {})
        pp = profit_map.get(symbol, {})
        hb = hb_map.get(symbol, {})
        mid, short = _parse_signals(item)
        rows.append(
            {
                "symbol": symbol,
                "name": item.get("name"),
                "group": item.get("group"),
                "type": item.get("etf_type") or item.get("type"),
                "market_value": item.get("market_value"),
                "weight": item.get("portfolio_weight", item.get("position_ratio")),
                "mid_trend": mid,
                "short_swing": short,
                "review_state": rv.get("review_state") or item.get("review_state") or item.get("sell_review_status"),
                "profit_protection_state": pp.get("profit_protection_state") or item.get("profit_protection_state") or "N/A",
                "high_beta_risk_state": hb.get("high_beta_risk_state") or item.get("high_beta_risk_state") or "N/A",
                "recommended_review_action": rv.get("recommended_review_action") or hb.get("recommended_review_action") or item.get("action_suggestion") or "观察，不自动交易。",
                "execution_allowed": False,
            }
        )
    return rows


def _weekly_trades(trades: list[dict], generated_at: str) -> dict:
    now = pd.Timestamp(generated_at)
    start = now - pd.Timedelta(days=7)
    rows = []
    for item in trades:
        date_text = str(item.get("trade_date") or item.get("date") or "")
        try:
            date = pd.Timestamp(date_text)
        except Exception:
            continue
        if not (start <= date <= now):
            continue
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "action": item.get("action") or item.get("order_type"),
                "amount": item.get("gross_amount", item.get("amount")),
                "reason": item.get("reason"),
                "is_simulated": True,
                "real_trade": False,
            }
        )
    return {"lookback_days": 7, "rows": rows, "count": len(rows), "real_trade": False}


def _buy_ranking(dashboard: dict) -> dict:
    rows = dashboard.get("buy_ranking", []) if isinstance(dashboard, dict) else []
    out = []
    for item in rows[:10]:
        out.append(
            {
                "rank": item.get("rank"),
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "group": item.get("group"),
                "mid_trend": item.get("mid_trend_signal"),
                "short_swing": item.get("short_swing_signal"),
                "rank_score": item.get("rank_score"),
                "risk_note": item.get("risk_note"),
            }
        )
    return {"top10": out, "execution_allowed": False}


def _adjusted_preview(dashboard: dict) -> dict:
    preview = dashboard.get("strategy_enhancement_preview", {}) if isinstance(dashboard.get("strategy_enhancement_preview"), dict) else {}
    rows = preview.get("rows", [])
    top10 = sorted(rows, key=lambda item: _float(item.get("adjusted_rank_preview"), 999999))[:10]
    return {
        "top10": top10,
        "preview_only_count": sum(1 for item in rows if item.get("execution_status") == "preview_only_not_executed"),
        "execution_allowed": False,
        "adjusted_rank_score_execution_enabled": False,
    }


def _review_states(review: dict) -> dict:
    rows = review.get("rows", [])
    states = {key: [] for key in ["HOLD", "WATCH", "REVIEW_1", "REVIEW_2", "REDUCE_CANDIDATE", "REDUCE", "SELL"]}
    for row in rows:
        state = str(row.get("review_state") or "N/A")
        states.setdefault(state, []).append(row)
    summary = review.get("summary", {})
    return {**states, "summary": summary, "execution_allowed": False}


def _profit_protection(profit: dict) -> dict:
    rows = profit.get("rows", [])
    states = {key: [] for key in ["NO_PROFIT", "PROFIT_WATCH", "PROFIT_PROTECTION_REVIEW", "PROFIT_LOCK_CANDIDATE"]}
    for row in rows:
        state = str(row.get("profit_protection_state") or "N/A")
        states.setdefault(state, []).append(row)
    focus = next((row for row in rows if str(row.get("symbol")) == "515000"), {})
    return {**states, "summary": profit.get("summary", {}), "focus_515000": focus, "execution_allowed": False}


def _high_beta_risk(high_beta: dict) -> dict:
    summary = high_beta.get("summary", {})
    rows = high_beta.get("rows", [])
    focus = next((row for row in rows if str(row.get("symbol")) == "512880"), {})
    state = str(focus.get("high_beta_risk_state") or summary.get("high_beta_exposure_state") or "")
    return {
        **summary,
        "rows": rows,
        "focus_512880": focus,
        "is_caution_or_elevated": state in {"HB_CAUTION", "HB_ELEVATED"},
        "execution_allowed": False,
    }


def _broad_base_balance(broad: dict) -> dict:
    summary = broad.get("summary", {})
    rows = broad.get("rows", [])
    focus = {f"focus_{symbol}": next((row for row in rows if str(row.get("symbol")) == symbol), {}) for symbol in ["588000", "159915", "510300"]}
    top = broad.get("top_balance_candidates") or rows[:5]
    first = top[0] if top else {}
    return {
        **summary,
        "rows": rows,
        "top_candidates": top,
        "preview_new_broad_base_weight": first.get("new_broad_base_weight"),
        "preview_new_finance_real_estate_weight": first.get("new_finance_real_estate_weight"),
        "preview_new_tech_growth_weight": first.get("new_tech_growth_weight"),
        "preview_new_high_beta_weight": first.get("new_high_beta_weight"),
        **focus,
        "execution_allowed": False,
    }


def _shadow_status(shadow: dict, dashboard: dict) -> dict:
    control = dashboard.get("app_control_center", {}) if isinstance(dashboard.get("app_control_center"), dict) else {}
    return {
        "current_phase": control.get("current_phase", "Shadow Observation Period"),
        "evidence_level": shadow.get("evidence_level", control.get("evidence_level", "insufficient")),
        "ready_for_preview": bool(shadow.get("ready_for_preview", False)),
        "ready_for_execution": bool(shadow.get("ready_for_execution", False)),
        "ready_to_relax_filters": bool(shadow.get("ready_to_relax_filters", False)),
        "persistence_selected_count": control.get("persistence_selected_count", shadow.get("persistence_selected_count")),
        "missed_opportunity_candidate_count": shadow.get("missed_opportunity_candidate_count", control.get("missed_opportunity_candidate_count")),
        "matured_forward_return_count": shadow.get("matured_forward_return_count", control.get("matured_forward_return_count")),
        "recommended_action": shadow.get("recommended_action", control.get("recommended_action", "Continue observation.")),
        "execution_allowed": False,
    }


def _valuation_consistency(dashboard: dict, exposure: dict) -> dict:
    val = dashboard.get("valuation_consistency", {}) if isinstance(dashboard.get("valuation_consistency"), dict) else {}
    perf = dashboard.get("paper_performance", {}) if isinstance(dashboard.get("paper_performance"), dict) else {}
    exp_summary = exposure.get("summary", {}) if isinstance(exposure.get("summary"), dict) else {}
    diff = _float(perf.get("current_position_value")) - _float(exp_summary.get("market_value"))
    return {
        "status": val.get("status", "derived"),
        "paper_vs_exposure_diff": diff,
        "price_warning_count": val.get("price_warning_count", perf.get("valuation_price_warning_count", 0)),
        "formal_and_preview_separated": True,
    }


def _data_health(dashboard: dict) -> dict:
    health = dashboard.get("health_summary", {}) if isinstance(dashboard.get("health_summary"), dict) else {}
    update = dashboard.get("data_update_status", {}) if isinstance(dashboard.get("data_update_status"), dict) else {}
    return {
        "status": health.get("status") or update.get("status") or "unknown",
        "warning_count": health.get("warning_count", 0),
        "error_count": health.get("error_count", 0),
        "failed_count": update.get("failed_count", 0),
    }


def _core_conclusions(paper: dict, review: dict, profit: dict, hb: dict, bb: dict, shadow: dict, data_status: dict) -> list[str]:
    conclusions = [
        f"正式模拟仓总资产 {_money(paper.get('current_total_equity'))}，总盈亏 {_money(paper.get('total_pnl_amount'))}，总收益率 {_pct(paper.get('total_return_pct'))}。",
        paper.get("profit_source_note", "当前盈利来源仍需复核。"),
        f"当前持仓结构：宽基占比 {_pct(bb.get('broad_base_weight'))}，科技成长 {_pct(bb.get('tech_growth_weight'))}，金融地产 {_pct(bb.get('finance_real_estate_weight'))}。",
        f"REVIEW/REDUCE 观察：REDUCE_CANDIDATE={len(review.get('REDUCE_CANDIDATE', []))}，REVIEW_2={len(review.get('REVIEW_2', []))}。",
        f"浮盈保护：PROFIT_WATCH={len(profit.get('PROFIT_WATCH', []))}，PROFIT_LOCK_CANDIDATE={len(profit.get('PROFIT_LOCK_CANDIDATE', []))}，不自动止盈。",
        f"high_beta：状态 {_na(hb.get('high_beta_exposure_state'))}，high_beta 占持仓 {_pct(hb.get('high_beta_weight_of_holdings'))}，不自动减仓。",
        f"宽基平衡：{_na(bb.get('broad_base_balance_state'))} / { _na(bb.get('theme_concentration_state'))}，候选 {_join_symbols(bb.get('top_candidates', [])[:3])}。",
        f"shadow 模型 evidence_level={_na(shadow.get('evidence_level'))}，ready_for_preview={shadow.get('ready_for_preview')}，ready_for_execution={shadow.get('ready_for_execution')}。",
        f"本周最需要判断：512800 是否继续 REDUCE_CANDIDATE、515000 是否需要浮盈保护升级、512880 high_beta 是否升高、宽基候选是否继续观察。",
    ]
    if data_status.get("data_update_status") not in {"success", "SUCCESS", "ok", "OK"}:
        conclusions.append(f"数据更新状态为 {_na(data_status.get('data_update_status'))}，需要确认最新数据是否足够。")
    return conclusions


def _chatgpt_questions() -> dict[str, list[str]]:
    return {
        "formal_paper_account": [
            "当前持仓是否继续观察？",
            "是否有持仓需要升级复核？",
            "512800 是否仍为 REDUCE_CANDIDATE？",
            "515000 是否需要进入浮盈保护复核？",
            "512880 high_beta 风险是否升高？",
        ],
        "portfolio_structure": [
            "当前是否过度主题集中？",
            "是否应继续观察宽基平衡候选？",
            "588000 / 159915 / 510300 谁更值得观察？",
            "是否应维持 adjusted preview 不接执行层？",
        ],
        "model_research": [
            "shadow 模型是否仍 evidence insufficient？",
            "是否有足够 forward return 样本？",
            "是否可以放宽过滤？",
            "是否可以进入 preview？",
            "是否可以接 paper_trade_engine？",
        ],
        "system_engineering": [
            "是否还有口径差异？",
            "是否需要优化 App 展示？",
            "是否需要更新报告字段？",
            "是否需要加入新的观察指标？",
        ],
    }


def _safety_boundary() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "real_trade_enabled": False,
        "broker_api_enabled": False,
        "real_account_read_enabled": False,
        "credentials_saved": False,
        "paper_trade_engine_changed": False,
        "paper_trades_changed": False,
        "paper_positions_changed": False,
        "adjusted_preview_execution_enabled": False,
        "shadow_execution_enabled": False,
        "must_not_misread": [
            "本项目是模拟盘和量化学习系统。",
            "不接券商 API。",
            "不真实下单。",
            "不读取真实账户。",
            "不保存密码/token。",
            "adjusted preview 不接执行层。",
            "shadow 不接执行层。",
            "REDUCE_CANDIDATE 不是减仓指令。",
            "PROFIT_LOCK_CANDIDATE 不是止盈指令。",
            "high_beta 风险观察不是卖出指令。",
            "当前小幅盈利不能证明策略成熟。",
        ],
    }


def _chatgpt_questions_markdown(questions: dict[str, list[str]]) -> list[str]:
    sections = [
        ("## A. 正式模拟仓", "formal_paper_account"),
        ("## B. 组合结构", "portfolio_structure"),
        ("## C. 模型研究", "model_research"),
        ("## D. 系统工程", "system_engineering"),
    ]
    lines: list[str] = []
    for title, key in sections:
        lines += [title, ""]
        lines.extend([f"{idx}. {item}" for idx, item in enumerate(questions[key], start=1)])
        lines.append("")
    return lines


def _missing_sources() -> list[str]:
    return [str(path.relative_to(PROJECT_ROOT)) for path in SOURCE_FILES.values() if not path.exists()]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
    except Exception:
        return []
    return rows


def _map_by_symbol(rows: list[dict]) -> dict[str, dict]:
    return {str(row.get("symbol") or row.get("code")): row for row in rows}


def _parse_signals(item: dict) -> tuple[str, str]:
    current = str(item.get("current_signal") or "")
    if "/" in current:
        left, right = current.split("/", 1)
        return left or "N/A", right or "N/A"
    reason = str(item.get("reason") or "")
    mid = "N/A"
    short = "N/A"
    for part in reason.split(";"):
        if "mid_trend=" in part:
            mid = part.split("mid_trend=", 1)[1].strip()
        if "short_swing=" in part:
            short = part.split("short_swing=", 1)[1].strip()
    return mid, short


def _join_symbols(rows: list[dict]) -> str:
    parts = []
    for row in rows:
        symbol = row.get("symbol") or row.get("code") or ""
        name = row.get("name") or ""
        if symbol:
            parts.append(f"{symbol} {name}".strip())
    return "、".join(parts)


def _focus_text(row: dict | None) -> str:
    if not row:
        return "暂无"
    return f"{row.get('mid_trend', 'N/A')}/{row.get('short_swing', 'N/A')}，rank={row.get('balance_candidate_rank', 'N/A')}，raw={_fmt(row.get('raw_score'))}，adjusted={_fmt(row.get('adjusted_score'))}"


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def _na(value: object) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)


def _fmt(value: object) -> str:
    try:
        return f"{_float(value):.4f}".rstrip("0").rstrip(".")
    except Exception:
        return "N/A"


def _money(value: object) -> str:
    return f"{_float(value):.2f}"


def _pct(value: object) -> str:
    return f"{_float(value):.2%}"


def _escape_pipe(value: object) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")


if __name__ == "__main__":
    main()
