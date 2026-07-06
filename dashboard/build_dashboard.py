"""Build a read-only local paper-trading dashboard.

The output is a self-contained HTML console for Safari and mobile browsers.
It only reads local CSV/Markdown/JSON reports. It never connects to broker
APIs, never places orders, and never reads or stores account credentials.
"""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
HTML_FILE = DASHBOARD_DIR / "index.html"
SNAPSHOT_FILE = REPORT_DIR / "dashboard_data.json"
SRC_DIR = PROJECT_ROOT / "src"
APP_VERSION_FILE = PROJECT_ROOT / "APP_VERSION"
APP_VERSION = APP_VERSION_FILE.read_text(encoding="utf-8").strip() if APP_VERSION_FILE.exists() else "0.1.0-local"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from valuation import load_latest_position_valuation  # type: ignore
except Exception:
    load_latest_position_valuation = None  # type: ignore

try:
    from config import (  # type: ignore
        BROKER_API_ENABLED,
        PAPER_AUTO_EXECUTE,
        PAPER_COMMISSION_RATE,
        PAPER_DEFAULT_MARKET_STATE,
        PAPER_INITIAL_CASH,
        PAPER_EXECUTION_PRICE_TYPE,
        PAPER_MAX_HOLDINGS,
        PAPER_MAX_SINGLE_POSITION_PCT,
        PAPER_MIN_COMMISSION,
        PAPER_MODE,
        PAPER_SLIPPAGE_RATE,
        PAPER_STAMP_TAX_RATE,
        PAPER_TARGET_POSITION_NEUTRAL,
        PAPER_TRANSFER_FEE_RATE,
        PAPER_USE_MARKET_STATE_POSITION,
        REAL_TRADE_ENABLED,
    )
except Exception:
    BROKER_API_ENABLED = False
    PAPER_AUTO_EXECUTE = False
    PAPER_COMMISSION_RATE = 0.00012
    PAPER_DEFAULT_MARKET_STATE = "neutral"
    PAPER_INITIAL_CASH = 10_000.0
    PAPER_EXECUTION_PRICE_TYPE = "close_price_with_slippage"
    PAPER_MAX_HOLDINGS = 3
    PAPER_MAX_SINGLE_POSITION_PCT = 0.20
    PAPER_MIN_COMMISSION = 5.0
    PAPER_MODE = "rule_validation"
    PAPER_SLIPPAGE_RATE = 0.0003
    PAPER_STAMP_TAX_RATE = 0.0
    PAPER_TARGET_POSITION_NEUTRAL = 0.30
    PAPER_TRANSFER_FEE_RATE = 0.0
    PAPER_USE_MARKET_STATE_POSITION = False
    REAL_TRADE_ENABLED = False

INITIAL_CASH = float(PAPER_INITIAL_CASH)
SINGLE_ETF_LIMIT = INITIAL_CASH * float(PAPER_MAX_SINGLE_POSITION_PCT)
TARGET_POSITION_RANGE = (0.20, 0.40)
ENGINE_STATE_FILE = DATA_DIR / "paper_trade_engine_state.json"
PAPER_TRADE_PLAN_FILE = REPORT_DIR / "paper_trade_plan.csv"


def main() -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_snapshot()
    SNAPSHOT_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_FILE.write_text(render_html(snapshot), encoding="utf-8")
    print(f"已生成静态看板：{HTML_FILE}")
    print(f"已生成看板快照：{SNAPSHOT_FILE}")


def build_snapshot() -> dict:
    positions = _valuation_positions_snapshot()
    if positions.empty:
        positions = _read_csv(DATA_DIR / "paper_positions.csv")
    trades = _read_csv(DATA_DIR / "paper_trades.csv")
    watchlist = _read_csv(PROJECT_ROOT / "watchlist.csv")
    candidates = _read_csv(DATA_DIR / "etf_pool_expansion_candidates.csv")
    classification = _read_classification_csv()
    ranking_rows = _read_buy_ranking()
    sell_review_rows = _read_csv(REPORT_DIR / "sell_signal_review.csv").to_dict(orient="records")
    position_review_state = _position_review_state_snapshot()
    profit_protection_preview = _profit_protection_preview_snapshot()
    high_beta_risk_watch = _high_beta_risk_watch_snapshot()
    paper_trade_plan_rows = _read_csv(PAPER_TRADE_PLAN_FILE).to_dict(orient="records")
    strategy_preview = _strategy_enhancement_preview_snapshot()
    broad_base_balance_preview = _broad_base_balance_preview_snapshot()
    preview_tracking = _strategy_preview_tracking_snapshot()
    type_aware_review = _type_aware_review_snapshot(sell_review_rows)
    market_state = _market_state_snapshot()
    portfolio_exposure = _portfolio_exposure_snapshot()
    model_research = _model_research_snapshot()
    research_quality = _research_quality_snapshot()
    universe_quality = _universe_quality_review_snapshot()
    phase4c_data = _phase4c_data_snapshot()
    phase4c_tushare_staging = _phase4c_tushare_staging_snapshot()
    phase4c_alpha = _phase4c_alpha_snapshot()
    persistence_breakout_shadow = _persistence_breakout_shadow_snapshot()
    missed_opportunity_tracking = _missed_opportunity_tracking_snapshot()
    shadow_observation_weekly = _shadow_observation_weekly_snapshot()
    chatgpt_weekly_packet = _chatgpt_weekly_packet_snapshot()
    exit_rule_research = _exit_rule_research_snapshot()
    backtest_phase4a = _backtest_phase4a_snapshot()
    backtest_diagnostics = _backtest_diagnostics_snapshot()
    ranking_signal_research = _ranking_signal_research_snapshot()
    ranking_model_v2_backtest = _ranking_model_v2_backtest_snapshot()
    paper_performance = _paper_performance_snapshot()
    paper_equity_backfill = _paper_equity_backfill_snapshot(paper_performance)
    app_shortcut = _app_shortcut_snapshot()
    trade_review = _trade_review_snapshot()
    execution_layer_integration = _execution_layer_integration_snapshot(paper_trade_plan_rows, market_state, portfolio_exposure, research_quality)
    health_rows, health_summary = _read_health_report()
    latest_data_date = _latest_data_date()
    data_update_status = _data_update_status_snapshot()
    data_sources = _data_sources_snapshot(data_update_status)
    engine_state = _latest_engine_state(_read_json(ENGINE_STATE_FILE), latest_data_date, pd.Timestamp.now().strftime("%Y-%m-%d"))

    meta = _build_meta_map(watchlist, candidates, classification)
    enriched_positions = _enrich_positions(
        positions,
        meta,
        ranking_rows,
        health_rows,
        sell_review_rows,
        position_review_state.get("rows", []),
        profit_protection_preview.get("rows", []),
        high_beta_risk_watch.get("rows", []),
    )
    summary = _merge_performance_summary(_paper_summary(enriched_positions, trades), paper_performance.get("summary", {}), portfolio_exposure)
    paper_trade_engine = _paper_trade_engine_snapshot(engine_state, paper_trade_plan_rows, summary)
    exposure = _group_exposure(enriched_positions)
    classification_summary = _classification_summary(classification, enriched_positions)
    failed_counts = _failed_counts()
    automation_nodes = _automation_nodes(data_update_status)
    risk_alerts = _risk_alerts(enriched_positions, failed_counts)
    console = _console_status(summary, risk_alerts, automation_nodes, health_summary, data_update_status)
    review = _review_snapshot()
    dashboard_links = _dashboard_links()
    link_health = _link_health(dashboard_links)
    dashboard_sources = _dashboard_sources()

    app_task_status = _read_json(REPORT_DIR / "app_task_status.json") or {"running": False, "latest_task": None, "history": []}
    execution_safety = _execution_safety_snapshot()
    app_control_room = {
        "system_status": console.get("system_status", "NORMAL"),
        "today_conclusion": console.get("today_conclusion", "HOLD_PLAN"),
        "today_summary": console.get("decision_reason", ""),
        "key_warnings": risk_alerts,
        "key_actions": [
            "先确认日线数据是否更新到最新交易日",
            "复核 sell_review 中的 REVIEW/CAUTION 持仓",
            "adjusted preview 只作研究展示，不进入执行层",
        ],
        "automation_health": "OK" if all(node.get("status") in {"OK", "WAITING"} for node in automation_nodes) else "CAUTION",
        "paper_only": True,
    }
    app_control_center = _app_control_center_snapshot(
        ranking_model_v2_backtest,
        phase4c_tushare_staging,
        phase4c_alpha,
        persistence_breakout_shadow,
        missed_opportunity_tracking,
        shadow_observation_weekly,
        data_sources,
    )

    return {
        "app_ready_snapshot_version": "step6_chatgpt_weekly_packet_v1",
        "local_app_version": f"v{APP_VERSION}",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "app_control_center": app_control_center,
        "dynamic_app": {
            "enabled": True,
            "tech_stack": "FastAPI + React/Vite",
            "local_url": "http://127.0.0.1:8000",
            "lan_supported": True,
            "public_deploy_supported": False,
            "task_buttons_enabled": True,
            "real_trade_buttons_enabled": False,
        },
        "app_launch": {
            "pycharm_required": False,
            "terminal_launch_supported": True,
            "double_click_launch_supported": True,
            "app_bundle_supported": app_shortcut.get("status") == "active",
            "app_bundle": app_shortcut.get("app_bundle"),
            "launcher_file": "打开量化研究控制台.command",
            "legacy_launcher_file": "A-Share Swing App.command",
            "local_url": "http://127.0.0.1:8000",
            "lan_supported": True,
        },
        "app_shortcut": app_shortcut,
        "desktop_app": {
            "enabled": True,
            "tech_stack": "Tauri + FastAPI + React/Vite",
            "web_app_url": "http://127.0.0.1:8000",
            "auto_start_backend_supported": True,
            "real_trade_buttons_enabled": False,
            "broker_api_enabled": False,
            "paper_only": True,
        },
        "app_task_status": app_task_status,
        "app_control_room": app_control_room,
        "latest_data_date": latest_data_date,
        "data_update_status": data_update_status,
        "data_sources": data_sources,
        "console": console,
        "market_state": market_state,
        "paper_summary": summary,
        "valuation_consistency": _valuation_consistency_snapshot(),
        "position_review_state": position_review_state.get("rows", []),
        "review_summary": position_review_state.get("summary", {}),
        "reduce_candidate_count": position_review_state.get("summary", {}).get("reduce_candidate_count", 0),
        "review_2_count": position_review_state.get("summary", {}).get("review_2_count", 0),
        "high_beta_watch_count": position_review_state.get("summary", {}).get("high_beta_watch_count", 0),
        "profit_protection_watch_count": position_review_state.get("summary", {}).get("profit_protection_watch_count", 0),
        "profit_protection_preview": profit_protection_preview.get("rows", []),
        "profit_protection_summary": profit_protection_preview.get("summary", {}),
        "profit_watch_count": profit_protection_preview.get("summary", {}).get("profit_watch_count", 0),
        "profit_protection_review_count": profit_protection_preview.get("summary", {}).get("profit_protection_review_count", 0),
        "profit_lock_candidate_count": profit_protection_preview.get("summary", {}).get("profit_lock_candidate_count", 0),
        "high_beta_risk_watch": high_beta_risk_watch.get("rows", []),
        "high_beta_risk_summary": high_beta_risk_watch.get("summary", {}),
        "high_beta_position_count": high_beta_risk_watch.get("summary", {}).get("high_beta_position_count", 0),
        "high_beta_weight_of_equity": high_beta_risk_watch.get("summary", {}).get("high_beta_weight_of_equity", 0),
        "high_beta_weight_of_holdings": high_beta_risk_watch.get("summary", {}).get("high_beta_weight_of_holdings", 0),
        "high_beta_exposure_state": high_beta_risk_watch.get("summary", {}).get("high_beta_exposure_state", "HB_NORMAL"),
        "finance_real_estate_weight": high_beta_risk_watch.get("summary", {}).get("finance_real_estate_weight_of_equity", 0),
        "paper_performance": paper_performance.get("summary", {}),
        "paper_equity_curve": paper_performance.get("equity_curve", []),
        "paper_equity_backfill": paper_equity_backfill,
        "paper_trade_pnl": paper_performance.get("trade_pnl", []),
        "trade_review": trade_review.get("summary", {}),
        "trade_review_details": trade_review.get("details", []),
        "trade_review_open_positions": trade_review.get("open_positions", []),
        "risk_alerts": risk_alerts,
        "positions": enriched_positions,
        "trades": trades.to_dict(orient="records"),
        "buy_ranking": ranking_rows,
        "sell_review": sell_review_rows,
        "strategy_enhancement_preview": strategy_preview,
        "broad_base_balance_preview": broad_base_balance_preview,
        "broad_base_balance_summary": broad_base_balance_preview.get("summary", {}),
        "broad_base_weight": broad_base_balance_preview.get("summary", {}).get("broad_base_weight", 0),
        "theme_weight": broad_base_balance_preview.get("summary", {}).get("theme_weight", 0),
        "tech_growth_weight": broad_base_balance_preview.get("summary", {}).get("tech_growth_weight", 0),
        "balance_candidate_count": broad_base_balance_preview.get("summary", {}).get("balance_candidate_count", 0),
        "top_balance_candidates": broad_base_balance_preview.get("top_balance_candidates", []),
        "strategy_preview_tracking": preview_tracking,
        "forward_return_comparison": preview_tracking.get("forward_return_comparison", {}),
        "shadow_model": preview_tracking.get("shadow_model", {}),
        "type_aware_review": type_aware_review,
        "paper_trade_engine": paper_trade_engine,
        "paper_trade_plan": paper_trade_plan_rows,
        "positions_enhanced": enriched_positions,
        "trading_costs": _trading_costs_snapshot(trades, paper_trade_plan_rows, paper_trade_engine),
        "exposure": exposure,
        "portfolio_exposure": portfolio_exposure,
        "classification_summary": classification_summary,
        "etf_classification": classification.to_dict(orient="records"),
        "model_research": model_research,
        "research_quality_review": research_quality,
        "universe_quality_review": universe_quality,
        "phase4c_data": phase4c_data,
        "phase4c_tushare_staging": phase4c_tushare_staging,
        "phase4c_alpha": phase4c_alpha,
        "persistence_breakout_shadow": persistence_breakout_shadow,
        "missed_opportunity_tracking": missed_opportunity_tracking,
        "shadow_observation_weekly": shadow_observation_weekly,
        "chatgpt_weekly_packet": chatgpt_weekly_packet,
        "chatgpt_weekly_packet_summary": chatgpt_weekly_packet.get("summary", {}),
        "exit_rule_research": exit_rule_research,
        "backtest_phase4a": backtest_phase4a,
        "backtest_diagnostics": backtest_diagnostics,
        "ranking_signal_research": ranking_signal_research,
        "ranking_model_v2_backtest": ranking_model_v2_backtest,
        "execution_layer_integration": execution_layer_integration,
        "health_summary": health_summary,
        "failed_counts": failed_counts,
        "automation_nodes": automation_nodes,
        "automation_status": automation_nodes,
        "review": review,
        "dashboard_links": dashboard_links,
        "link_health": link_health,
        "dashboard_sources": dashboard_sources,
        "risk_limits": {
            "mode": PAPER_MODE,
            "auto_execute": PAPER_AUTO_EXECUTE,
            "real_trade_enabled": REAL_TRADE_ENABLED,
            "broker_api_enabled": BROKER_API_ENABLED,
            "market_state": PAPER_DEFAULT_MARKET_STATE,
            "target_position_pct": PAPER_TARGET_POSITION_NEUTRAL,
            "max_holdings": PAPER_MAX_HOLDINGS,
            "max_single_position_pct": PAPER_MAX_SINGLE_POSITION_PCT,
            "single_etf_limit": SINGLE_ETF_LIMIT,
            "commission_rate": PAPER_COMMISSION_RATE,
            "min_commission": PAPER_MIN_COMMISSION,
            "stamp_tax_rate": PAPER_STAMP_TAX_RATE,
            "transfer_fee_rate": PAPER_TRANSFER_FEE_RATE,
            "slippage_rate": PAPER_SLIPPAGE_RATE,
            "execution_price_type": PAPER_EXECUTION_PRICE_TYPE,
            "use_market_state_position": PAPER_USE_MARKET_STATE_POSITION,
        },
        "execution_safety": execution_safety,
        "system_safety": {
            "real_trade_enabled": bool(REAL_TRADE_ENABLED),
            "broker_api_enabled": bool(BROKER_API_ENABLED),
            "paper_only": True,
            "real_order_buttons": False,
            "credentials_saved": False,
        },
        "safety": {
            "permission": "L2 local paper data/report dashboard",
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "credentials_saved": False,
            "strategy_rule_change": False,
        },
    }


def render_html(data: dict) -> str:
    console = data["console"]
    summary = data["paper_summary"]
    risk_alerts = data.get("risk_alerts", [])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A 股 ETF 模拟盘控制台</title>
  <style>
    :root {{
      --bg: #f4f5f7;
      --panel: rgba(255,255,255,.78);
      --ink: #1d1d1f;
      --muted: #6e6e73;
      --line: rgba(60,60,67,.14);
      --blue: #0a84ff;
      --blue-soft: #eef4ff;
      --profit-red: #d92d20;
      --loss-green: #079455;
      --warn: #b7791f;
      --warn-bg: #fffbeb;
      --danger: #8a1f11;
      --danger-bg: #fff1f0;
      --slate: #344054;
      --ok: #067647;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 12% 8%, rgba(10,132,255,.10), transparent 28%),
        linear-gradient(180deg, #fbfbfd 0%, var(--bg) 48%, #eef1f6 100%);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      font-variant-numeric: tabular-nums;
    }}
    header {{
      background: rgba(255,255,255,.76);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(22px) saturate(1.18);
    }}
    .topbar {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 14px 22px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
    }}
    h1 {{ margin: 0; font-size: 21px; letter-spacing: 0; }}
    .subtitle {{ color: var(--muted); font-size: 13px; margin-top: 3px; }}
    .status-strip {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--slate);
      font-size: 12px;
      white-space: nowrap;
    }}
    .badge.ok {{ background: #ecfdf3; border-color: #abefc6; color: var(--ok); }}
    .badge.warn {{ background: var(--warn-bg); border-color: #f6d48f; color: var(--warn); }}
    .badge.danger {{ background: var(--danger-bg); border-color: #f5b5aa; color: var(--danger); }}
    .badge.blue {{ background: var(--blue-soft); border-color: #bed5ff; color: var(--blue); }}
    main {{ max-width: 1500px; margin: 0 auto; padding: 22px; }}
    section {{ margin-top: 22px; }}
    .section-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: end; margin-bottom: 12px; }}
    h2 {{ margin: 0; font-size: 19px; letter-spacing: 0; }}
    h3 {{ margin: 0 0 10px; font-size: 15px; color: var(--slate); }}
    .hint {{ color: var(--muted); font-size: 13px; }}
    .grid {{ display: grid; gap: 14px; }}
    .overview-grid {{ grid-template-columns: 1.2fr repeat(4, minmax(150px, .7fr)); }}
    .two {{ grid-template-columns: 1.05fr .95fr; }}
    .three {{ grid-template-columns: repeat(3, minmax(220px, 1fr)); }}
    .four {{ grid-template-columns: repeat(4, minmax(160px, 1fr)); }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 18px 46px rgba(0,0,0,.08);
      backdrop-filter: blur(18px) saturate(1.12);
      padding: 16px;
    }}
    .decision {{
      background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
      border-color: #bed5ff;
    }}
    .decision-label {{ color: var(--muted); font-size: 13px; }}
    .decision-value {{ font-size: 30px; font-weight: 760; margin-top: 8px; color: var(--blue); }}
    .decision-sub {{ color: var(--slate); margin-top: 10px; }}
    .metric-label {{ color: var(--muted); font-size: 12px; }}
    .metric-value {{ font-size: 24px; font-weight: 760; margin-top: 5px; white-space: nowrap; }}
    .metric-sub {{ color: var(--muted); font-size: 12px; margin-top: 3px; }}
    .risk-banner {{
      border: 1px solid #f6d48f;
      background: var(--warn-bg);
      border-left: 6px solid var(--warn);
      border-radius: 14px;
      padding: 14px 16px;
      display: grid;
      gap: 8px;
    }}
    .risk-banner.danger {{ border-color: #f5b5aa; border-left-color: var(--danger); background: var(--danger-bg); }}
    .risk-title {{ font-weight: 760; color: var(--warn); }}
    .risk-banner.danger .risk-title {{ color: var(--danger); }}
    .risk-list {{ margin: 0; padding-left: 18px; }}
    .table-scroll {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 10px 9px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 650; background: #f8fafc; white-space: nowrap; }}
    .num {{ text-align: right; white-space: nowrap; }}
    .profit {{ color: var(--profit-red); font-weight: 700; }}
    .loss {{ color: var(--loss-green); font-weight: 700; }}
    .neutral {{ color: var(--slate); }}
    .tag {{
      display: inline-flex;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #fff;
      white-space: nowrap;
    }}
    .tag.ok {{ background: #ecfdf3; border-color: #abefc6; color: var(--ok); }}
    .tag.warn {{ background: var(--warn-bg); border-color: #f6d48f; color: var(--warn); }}
    .tag.danger {{ background: var(--danger-bg); border-color: #f5b5aa; color: var(--danger); }}
    .tag.blue {{ background: var(--blue-soft); border-color: #bed5ff; color: var(--blue); }}
    .muted {{ color: var(--muted); font-size: 12px; }}
    .reason {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
      max-width: 360px;
    }}
    .bar-bg {{ height: 9px; background: #eef2f7; border-radius: 999px; overflow: hidden; min-width: 72px; }}
    .bar-fill {{ height: 100%; background: var(--blue); }}
    .score-cell {{ min-width: 92px; }}
    .score-text {{ display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--muted); margin-bottom: 3px; }}
    .chart-grid {{ display: grid; grid-template-columns: repeat(2, minmax(280px, 1fr)); gap: 14px; }}
    .chart-card {{ border: 1px solid var(--line); border-radius: 14px; background: #fbfcfe; padding: 14px; min-height: 210px; }}
    .chart-card svg {{ width: 100%; height: auto; display: block; }}
    .chart-row {{ display: grid; grid-template-columns: 92px 1fr 82px; gap: 8px; align-items: center; margin: 10px 0; }}
    .chart-label {{ color: var(--slate); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .chart-value {{ color: var(--muted); font-size: 12px; text-align: right; }}
    .timeline {{ display: grid; grid-template-columns: repeat(6, minmax(150px, 1fr)); gap: 12px; }}
    .node-card {{
      position: relative;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 14px;
      padding: 13px;
      min-height: 132px;
    }}
    .node-time {{ color: var(--muted); font-size: 12px; }}
    .node-name {{ font-weight: 720; margin: 5px 0; }}
    .node-link {{ color: var(--blue); text-decoration: none; font-size: 12px; }}
    .node-link:hover {{ text-decoration: underline; }}
    .file-list {{ display: grid; gap: 8px; margin: 0; padding-left: 18px; }}
    .links a {{ color: var(--blue); text-decoration: none; margin-right: 14px; }}
    .links a:hover {{ text-decoration: underline; }}
    code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 5px; }}
    footer {{ max-width: 1500px; margin: 0 auto; padding: 8px 22px 34px; color: var(--muted); font-size: 12px; }}
    .quick-nav {{
      position: sticky;
      top: 60px;
      z-index: 9;
      background: rgba(244,246,249,.86);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid rgba(216,222,232,.75);
    }}
    .quick-nav-inner {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 9px 22px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }}
    .quick-nav a {{
      color: #344054;
      text-decoration: none;
      border: 1px solid #d8dee8;
      background: rgba(255,255,255,.84);
      border-radius: 999px;
      padding: 6px 11px;
      font-size: 12px;
      white-space: nowrap;
    }}
    .quick-nav a:hover {{ color: #1455d9; border-color: #9db8ff; }}
    .control-shell {{
      background: rgba(255,255,255,.74);
      color: #1d1d1f;
      border-radius: 26px;
      border: 1px solid rgba(60,60,67,.14);
      box-shadow: 0 24px 70px rgba(0,0,0,.09);
      backdrop-filter: blur(24px) saturate(1.18);
      padding: 20px;
      margin-bottom: 18px;
    }}
    .control-shell .muted, .control-shell .metric-sub {{ color: #6e6e73; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.15fr .85fr; gap: 16px; align-items: stretch; }}
    .brief-card {{
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 16px;
      padding: 18px;
      background: #172033;
    }}
    .eyebrow {{ color: #93c5fd; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; font-weight: 720; }}
    .hero-title {{ margin-top: 9px; font-size: 34px; font-weight: 780; letter-spacing: 0; line-height: 1.1; }}
    .hero-sub {{ margin-top: 10px; color: #cbd5e1; max-width: 780px; }}
    .decision-chip {{
      display: inline-flex;
      align-items: center;
      margin-top: 16px;
      padding: 8px 12px;
      border-radius: 999px;
      background: #eef4ff;
      color: #1455d9;
      font-weight: 760;
      border: 1px solid #bed5ff;
    }}
    .kpi-rack {{ display: grid; grid-template-columns: repeat(2, minmax(160px, 1fr)); gap: 12px; }}
    .kpi-card {{
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 14px;
      padding: 14px;
      background: #0f172a;
    }}
    .kpi-label {{ color: #a8b3c7; font-size: 12px; }}
    .kpi-value {{ font-size: 26px; font-weight: 780; margin-top: 5px; }}
    .kpi-note {{ color: #a8b3c7; font-size: 12px; margin-top: 4px; }}
    .market-tape {{
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      gap: 10px;
    }}
    .tape-item {{
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 12px;
      padding: 11px;
      background: rgba(255,255,255,.05);
    }}
    .tape-label {{ color: #a8b3c7; font-size: 12px; }}
    .tape-value {{ color: #f8fafc; font-weight: 760; margin-top: 4px; }}
    .ops-grid {{ display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 14px; }}
    .ops-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 14px;
    }}
    .ops-title {{ font-weight: 760; margin-bottom: 8px; }}
    .link-grid {{ display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; }}
    .link-card {{
      display: block;
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 14px;
      min-height: 92px;
    }}
    .link-card:hover {{ border-color: #9db8ff; box-shadow: 0 10px 30px rgba(20,85,217,.10); }}
    .link-card-title {{ font-weight: 760; }}
    .link-card-meta {{ margin-top: 6px; color: var(--muted); font-size: 12px; }}
    .source-grid {{ display: grid; grid-template-columns: repeat(4, minmax(190px, 1fr)); gap: 12px; }}
    .source-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 14px;
      min-height: 130px;
    }}
    .source-card a {{ color: var(--blue); text-decoration: none; }}
    .source-card a:hover {{ text-decoration: underline; }}
    .health-meter {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    @media (max-width: 1180px) {{
      .overview-grid, .two, .three, .four, .chart-grid, .timeline, .hero-grid, .market-tape, .ops-grid, .link-grid, .source-grid, .health-meter {{ grid-template-columns: 1fr; }}
      .topbar {{ grid-template-columns: 1fr; }}
      .status-strip {{ justify-content: flex-start; }}
      .quick-nav {{ top: 94px; }}
      main {{ padding: 14px; }}
      table {{ font-size: 12px; }}
      .decision-value {{ font-size: 25px; }}
      .hero-title {{ font-size: 27px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>A 股 ETF 双周期模拟盘</h1>
        <div class="subtitle">专业模拟盘量化交易控制台 · 只读本地数据 · 不接券商 API · 不真实下单</div>
      </div>
      <div class="status-strip">
        {_status_badge(console.get("today_conclusion"), "blue")}
        {_status_badge(console.get("system_status"), console.get("system_badge_class", "ok"))}
        <span class="badge">数据日 {escape(str(data.get("latest_data_date", "N/A")))}</span>
        <span class="badge">生成 {escape(str(data.get("generated_at", "N/A")))}</span>
        <span class="badge blue">v{escape(str(APP_VERSION))}</span>
        <span class="badge warn">L2 只读边界</span>
      </div>
    </div>
  </header>
  <nav class="quick-nav" aria-label="dashboard sections">
    <div class="quick-nav-inner">
      <a href="#overview">Overview</a>
      <a href="#paper-trade-engine">Paper Engine</a>
      <a href="#paper-performance">Performance</a>
      <a href="#trade-review">Trade Review</a>
      <a href="#portfolio">Portfolio</a>
      <a href="#sell-review">Sell Review</a>
      <a href="#ranking">BUY Ranking</a>
      <a href="#strategy-preview">B1 Preview</a>
      <a href="#preview-tracking">B2 Tracking</a>
      <a href="#type-aware-review">Type Review</a>
      <a href="#phase2c">Phase 2C</a>
      <a href="#risk">Risk</a>
      <a href="#automation">Automation</a>
      <a href="#quality-review">Quality Review</a>
      <a href="#phase4c-data">Data Sources</a>
      <a href="#phase4c-tushare">Tushare</a>
      <a href="#phase4c-alpha">Alpha</a>
      <a href="#review">Review</a>
      <a href="#links">Links</a>
    </div>
  </nav>
  <main>
    <section id="overview">
      {_executive_cockpit(data)}
      <div class="section-head">
        <div>
          <h2>交易控制台 Overview</h2>
          <div class="hint">先看结论、风险和仓位，再进入持仓与信号细节。</div>
        </div>
      </div>
      <div class="grid overview-grid">
        <div class="panel decision">
          <div class="decision-label">今日执行结论</div>
          <div class="decision-value">{escape(str(console.get("today_conclusion", "REVIEW_REQUIRED")))}</div>
          <div class="decision-sub">{escape(str(console.get("decision_reason", "")))}</div>
        </div>
        {_metric("总资产", _money(summary.get("total_equity")), f"总盈亏 {_money(summary.get('total_pnl'))}")}
        {_metric("现金", _money(summary.get("cash")), f"现金比例 {_pct(summary.get('cash_ratio'))}")}
        {_metric("持仓市值", _money(summary.get("market_value")), f"仓位 {_pct(summary.get('position_ratio'))}")}
        {_metric("风险提醒", str(len(risk_alerts)), console.get("risk_summary", "无"))}
      </div>
      {_risk_banner(risk_alerts)}
    </section>

    <section id="paper-trade-engine">
      <div class="section-head">
        <div>
          <h2>模拟交易引擎 Paper Engine</h2>
          <div class="hint">规则验证版自动买卖，只写本地模拟盘；所有真实交易开关保持关闭。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_paper_engine_panel(data.get("paper_trade_engine", {}), data.get("risk_limits", {}))}</div>
        <div class="panel">
          <h3>今日计划 / 执行 / 跳过原因</h3>
          {_paper_trade_plan_table(data.get("paper_trade_plan", []))}
        </div>
      </div>
    </section>

    <section id="paper-performance">
      <div class="section-head">
        <div>
          <h2>模拟仓绩效中心 Paper Performance</h2>
          <div class="hint">总盈亏、历史权益曲线、交易盈亏和成本统计。只读派生报告，不修改模拟交易和持仓。</div>
        </div>
      </div>
      {_paper_performance_panel(data.get("paper_performance", {}), data.get("paper_equity_curve", []), data.get("paper_trade_pnl", []))}
    </section>

    <section id="trade-review">
      <div class="section-head">
        <div>
          <h2>交易复盘中心 Trade Review</h2>
          <div class="hint">逐笔复盘为什么赚亏、MFE/MAE、卖出时机、成本影响和样本不足提醒。只读派生分析，不进入执行层。</div>
        </div>
      </div>
      {_trade_review_panel(data.get("trade_review", {}), data.get("trade_review_details", []), data.get("trade_review_open_positions", []))}
    </section>

    <section id="portfolio">
      <div class="section-head">
        <div>
          <h2>当前持仓 Portfolio</h2>
          <div class="hint">决策字段优先：信号是否有效、距离止损、风险标签和动作建议。</div>
        </div>
      </div>
      {_portfolio_table(data.get("positions", []))}
    </section>

    <section id="position-review-state">
      <div class="section-head">
        <div>
          <h2>持仓观察分层 Position Review State</h2>
          <div class="hint">REVIEW_1 / REVIEW_2 / REDUCE_CANDIDATE 均为模拟仓观察状态，不会自动交易。</div>
        </div>
      </div>
      {_position_review_state_panel(data.get("position_review_state", []), data.get("review_summary", {}))}
    </section>

    <section id="profit-protection-preview">
      <div class="section-head">
        <div>
          <h2>浮盈保护 Preview Profit Protection</h2>
          <div class="hint">只观察未实现盈利是否回吐，不自动止盈、不自动减仓。</div>
        </div>
      </div>
      {_profit_protection_panel(data.get("profit_protection_preview", []), data.get("profit_protection_summary", {}))}
    </section>

    <section id="high-beta-risk-watch">
      <div class="section-head">
        <div>
          <h2>高波动风险观察 High Beta Risk</h2>
          <div class="hint">重点观察证券/券商等高 beta 持仓的波动、回撤和金融地产暴露；只提示，不自动交易。</div>
        </div>
      </div>
      {_high_beta_risk_panel(data.get("high_beta_risk_watch", []), data.get("high_beta_risk_summary", {}))}
    </section>

    <section id="sell-review">
      <div class="section-head">
        <div>
          <h2>卖出复核 Sell Review</h2>
          <div class="hint">每日收盘后只读复核 HOLD / WATCH / REVIEW / REDUCE / SELL 候选，不自动交易。</div>
        </div>
      </div>
      {_sell_review_table(data.get("sell_review", []))}
    </section>

    <section id="ranking">
      <div class="section-head">
        <div>
          <h2>BUY Ranking</h2>
          <div class="hint">rank_score 拆解为趋势、动量、流动性、风险、共振和数据质量。</div>
        </div>
      </div>
      {_ranking_table(data.get("buy_ranking", []))}
    </section>

    <section id="strategy-preview">
      <div class="section-head">
        <div>
          <h2>Strategy Enhancement Preview</h2>
          <div class="hint">B1 预览层：展示组合平衡、ETF 类型、数据健康对 BUY ranking 的理论影响，不进入真实模拟买卖。</div>
        </div>
      </div>
      {_strategy_preview_panel(data.get("strategy_enhancement_preview", {}))}
    </section>

    <section id="broad-base-balance-preview">
      <div class="section-head">
        <div>
          <h2>宽基平衡观察 Broad-base Balance Preview</h2>
          <div class="hint">从 BUY ranking / adjusted preview 中筛选宽基候选，观察是否能降低行业主题集中度；只预览，不自动买入。</div>
        </div>
      </div>
      {_broad_base_balance_panel(data.get("broad_base_balance_preview", {}))}
    </section>

    <section id="preview-tracking">
      <div class="section-head">
        <div>
          <h2>Original vs Adjusted Tracking</h2>
          <div class="hint">B2 影子跟踪账本：记录 original ranking 与 adjusted preview ranking 的差异，并等待未来 1/3/5/10 日收益回填。</div>
        </div>
      </div>
      {_preview_tracking_panel(data.get("strategy_preview_tracking", {}))}
    </section>

    <section id="type-aware-review">
      <div class="section-head">
        <div>
          <h2>Type-aware Review</h2>
          <div class="hint">类型化持仓复核：止损、最大持有期、风险等级和 review note 仅作提示，不自动 SELL。</div>
        </div>
      </div>
      {_type_aware_review_panel(data.get("type_aware_review", {}), data.get("execution_safety", {}))}
    </section>

    <section id="phase2c">
      <div class="section-head">
        <div>
          <h2>执行层轻量接入 Execution Layer Integration</h2>
          <div class="hint">Phase 2C 只把研究结论接入解释字段和看板，不改变自动买卖结果。</div>
        </div>
      </div>
      {_phase2c_panel(data.get("execution_layer_integration", {}))}
    </section>

    <section id="risk">
      <div class="section-head">
        <div>
          <h2>组合风险 Risk & Exposure</h2>
          <div class="hint">仓位是否在目标区间、单只是否超限、主题是否集中、数据是否 caution。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_risk_exposure_panel(data)}</div>
        <div class="panel">{_exposure_chart(data.get("exposure", {}))}</div>
      </div>
    </section>

    <section id="system-health">
      <div class="section-head">
        <div>
          <h2>系统健康 System Health</h2>
          <div class="hint">将数据、交易引擎、自动化、链接可用性放到一个监控面板里。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_system_health_panel(data)}</div>
        <div class="panel">{_link_health_panel(data.get("link_health", {}))}</div>
      </div>
    </section>

    <section id="research-layer">
      <div class="section-head">
        <div>
          <h2>策略研究层 Research Layer</h2>
          <div class="hint">只读展示市场状态、ETF 类型、组合暴露、持有周期、退出规则和参数扫描，不改变交易规则。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_market_state_panel(data.get("market_state", {}))}</div>
        <div class="panel">{_classification_panel(data.get("classification_summary", {}))}</div>
        <div class="panel">{_portfolio_exposure_panel(data.get("portfolio_exposure", {}))}</div>
        <div class="panel">{_model_research_panel(data.get("model_research", {}))}</div>
      </div>
      <div class="panel" style="margin-top:14px;">
        {_research_layer_panel(data)}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_universe_quality_panel(data.get("universe_quality_review", {}))}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_exit_rule_research_panel(data.get("exit_rule_research", {}))}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_backtest_phase4a_panel(data.get("backtest_phase4a", {}))}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_backtest_diagnostics_panel(data.get("backtest_diagnostics", {}))}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_ranking_signal_research_panel(data.get("ranking_signal_research", {}))}
      </div>
      <div class="panel" style="margin-top:14px;">
        {_ranking_model_v2_backtest_panel(data.get("ranking_model_v2_backtest", {}))}
      </div>
    </section>

    <section id="automation">
      <div class="section-head">
        <div>
          <h2>自动化节点 Automation</h2>
          <div class="hint">交易日四节点 + 周/月复盘，以时间轴状态展示。</div>
        </div>
      </div>
      {_automation_timeline(data.get("automation_nodes", []))}
    </section>

    <section id="quality-review">
      <div class="section-head">
        <div>
          <h2>研究质量审查 Research Quality Review</h2>
          <div class="hint">审查 phase2 研究是否足够可靠，以及哪些结论可以进入执行层候选。</div>
        </div>
      </div>
      {_research_quality_panel(data.get("research_quality_review", {}))}
    </section>

    <section id="phase4c-data">
      <div class="section-head">
        <div>
          <h2>数据源架构审计 Data Sources</h2>
          <div class="hint">Phase 4C 只做数据源审计、AKShare 诊断和无未来函数规则，不接执行层。</div>
        </div>
      </div>
      {_phase4c_data_panel(data.get("phase4c_data", {}))}
    </section>

    <section id="phase4c-tushare">
      <div class="section-head">
        <div>
          <h2>Tushare Staging Dry-run</h2>
          <div class="hint">Phase 4C-1 小样本验证：只写 staging，不覆盖正式数据，不切换主源。</div>
        </div>
      </div>
      {_phase4c_tushare_panel(data.get("phase4c_tushare_staging", {}))}
    </section>

    <section id="phase4c-alpha">
      <div class="section-head">
        <div>
          <h2>Phase 4C Alpha 模型研究</h2>
          <div class="hint">v2 收益拖累归因、regime-aware、ETF type-aware 和 alpha 增强；只研究，不接执行层。</div>
        </div>
      </div>
      {_phase4c_alpha_panel(data.get("phase4c_alpha", {}))}
    </section>

    <section id="persistence-breakout-shadow">
      <div class="section-head">
        <div>
          <h2>Persistence Breakout Shadow</h2>
          <div class="hint">Phase 4C-2：persistence_breakout_v2 只进入 shadow tracking，不接 paper_trade_engine。</div>
        </div>
      </div>
      {_persistence_breakout_shadow_panel(data.get("persistence_breakout_shadow", {}))}
    </section>

    <section id="missed-opportunity">
      <div class="section-head">
        <div>
          <h2>Missed Opportunity Tracking</h2>
          <div class="hint">Phase 4C-2b：追踪高分但被过滤候选的事后表现，只作 diagnostics，不放宽规则。</div>
        </div>
      </div>
      {_missed_opportunity_tracking_panel(data.get("missed_opportunity_tracking", {}))}
    </section>

    <section id="shadow-observation-weekly">
      <div class="section-head">
        <div>
          <h2>Shadow Observation Weekly</h2>
          <div class="hint">Phase 4C-3：每周观察 shadow 模型、空仓、过滤原因和 forward return 成熟度。</div>
        </div>
      </div>
      {_shadow_observation_weekly_panel(data.get("shadow_observation_weekly", {}))}
    </section>

    <section id="chatgpt-weekly-packet">
      <div class="section-head">
        <div>
          <h2>ChatGPT / Main 周报分析包</h2>
          <div class="hint">固定格式 Markdown + JSON，用于复制给 ChatGPT / Main 分析；不是交易指令，不接执行层。</div>
        </div>
      </div>
      {_chatgpt_weekly_packet_panel(data.get("chatgpt_weekly_packet", {}))}
    </section>

    <section id="review">
      <div class="section-head">
        <div>
          <h2>回测与复盘 Review</h2>
          <div class="hint">每日轻量滚动回测、周度完整复盘、月度模型复盘。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_review_panel(data.get("review", {}))}</div>
        <div class="panel">
          <h3>图表工作台</h3>
          <div class="chart-grid">
            {_allocation_chart(data)}
            {_position_chart(data.get("positions", []))}
            {_ranking_chart(data.get("buy_ranking", []))}
            {_exposure_chart(data.get("exposure", {}), compact=True)}
          </div>
        </div>
      </div>
    </section>

    <section id="records">
      <div class="section-head">
        <div>
          <h2>交易记录与本地文件</h2>
          <div class="hint">只读展示模拟流水和本地报告路径。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">
          <h3>模拟交易记录</h3>
          {_trade_timeline(data.get("trades", []))}
          {_trades_table(data.get("trades", []))}
        </div>
        <div class="panel">
          <h3>本地文件与安全边界</h3>
          {_files_panel()}
          {_safety_panel(data)}
        </div>
      </div>
    </section>

    <section id="links">
      <div class="section-head">
        <div>
          <h2>报告中心 Links</h2>
          <div class="hint">所有内置链接在生成看板时做本地存在性检查；缺失会在系统健康里提示。</div>
        </div>
      </div>
      {_link_center(data.get("dashboard_links", []))}
    </section>

    <section id="design-research">
      <div class="section-head">
        <div>
          <h2>设计借鉴 Design References</h2>
          <div class="hint">本页借鉴专业交易台、组合风险系统、开源量化项目和券商平台的信息架构。</div>
        </div>
      </div>
      {_source_reference_panel(data.get("dashboard_sources", []))}
    </section>
  </main>
  <footer>静态只读 HTML。刷新方式：运行 <code>python3 dashboard/build_dashboard.py</code>；每日自动化完成后也会刷新。</footer>
</body>
</html>
"""


def _executive_cockpit(data: dict) -> str:
    console = data.get("console", {})
    summary = data.get("paper_summary", {})
    engine = data.get("paper_trade_engine", {}).get("state", {})
    link_health = data.get("link_health", {})
    risk_alerts = data.get("risk_alerts", [])
    market_state = data.get("market_state", {})
    data_update = data.get("data_update_status", {})
    data_sources = data.get("data_sources", {})
    top_buy = data.get("buy_ranking", [{}])[0] if data.get("buy_ranking") else {}
    sell_review = data.get("sell_review", [])
    review_flags = sum(1 for row in sell_review if str(row.get("sell_review_status", "")).upper() in {"REVIEW", "REDUCE", "SELL"})
    return f"""
      <div class="control-shell">
        <div class="hero-grid">
          <div class="brief-card">
            <div class="eyebrow">SIMULATED ETF CONTROL ROOM</div>
            <div class="hero-title">{escape(str(console.get("today_conclusion", "REVIEW_REQUIRED")))}</div>
            <div class="hero-sub">{escape(str(console.get("decision_reason", "")))}</div>
            <div class="decision-chip">系统状态：{escape(str(console.get("system_status", "N/A")))} · L2 本地模拟盘 · 无真实交易</div>
            <div class="market-tape">
              {_tape("最新数据日", data.get("latest_data_date"))}
              {_tape("实际数据源", f"{data_sources.get('actual_source_used','N/A')} / fallback={data_sources.get('fallback_triggered','N/A')}")}
              {_tape("日线更新", f"{data_update.get('severity','N/A')} / {data_update.get('status','N/A')}")}
              {_tape("市场状态", f"{market_state.get('market_state','N/A')} / {_score(market_state.get('market_score'))}")}
              {_tape("估值日期", f"{summary.get('valuation_as_of_date','N/A')} / price warnings={summary.get('valuation_price_warning_count', 0)}")}
              {_tape("模拟交易引擎", engine.get("status", "WAITING"))}
              {_tape("Top BUY", f"{top_buy.get('symbol','N/A')} / {_score(top_buy.get('rank_score'))}")}
            </div>
          </div>
          <div class="kpi-rack">
            {_dark_kpi("总资产", _money(summary.get("total_equity")), f"总盈亏 {_money(summary.get('total_pnl'))}")}
            {_dark_kpi("持仓仓位", _pct(summary.get("position_ratio")), f"持仓 {summary.get('position_count', 0)} / 3")}
            {_dark_kpi("现金", _money(summary.get("cash")), f"现金比例 {_pct(summary.get('cash_ratio'))}")}
            {_dark_kpi("风险提醒", str(len(risk_alerts)), console.get("risk_summary", "无"))}
          </div>
        </div>
      </div>
    """


def _tape(label: str, value: object) -> str:
    return f'<div class="tape-item"><div class="tape-label">{escape(label)}</div><div class="tape-value">{escape(str(value or "N/A"))}</div></div>'


def _dark_kpi(label: str, value: str, note: str) -> str:
    return f'<div class="kpi-card"><div class="kpi-label">{escape(label)}</div><div class="kpi-value">{escape(value)}</div><div class="kpi-note">{escape(str(note))}</div></div>'


def _metric(label: str, value: str, sub: str) -> str:
    return f'<div class="panel"><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(value)}</div><div class="metric-sub">{escape(str(sub))}</div></div>'


def _status_badge(text: object, cls: str = "") -> str:
    return f'<span class="badge {escape(cls)}">{escape(str(text or "N/A"))}</span>'


def _risk_banner(alerts: list[dict]) -> str:
    if not alerts:
        return '<div class="risk-banner" style="border-left-color:var(--ok);background:#ecfdf3;border-color:#abefc6;margin-top:14px;"><div class="risk-title" style="color:var(--ok);">当前未发现持仓级风险触发</div><div>继续按计划观察，不为了交易而交易。</div></div>'
    severe = any(item.get("severity") == "danger" for item in alerts)
    cls = "danger" if severe else ""
    items = []
    for item in alerts[:6]:
        items.append(
            f"<li><b>{escape(item.get('symbol',''))}</b> {escape(item.get('name',''))}：{escape(item.get('reason',''))}；建议：{escape(item.get('action',''))}</li>"
        )
    return f"""<div class="risk-banner {cls}" style="margin-top:14px;">
      <div class="risk-title">风险提示条：{len(alerts)} 项需要人工复核</div>
      <ul class="risk-list">{''.join(items)}</ul>
    </div>"""


def _paper_engine_panel(engine: dict, limits: dict) -> str:
    state = engine.get("state", {})
    status = state.get("status", "WAITING")
    rows = [
        _mini_stat("运行日", str(state.get("run_date", state.get("date", "N/A"))), "自动化执行日期"),
        _mini_stat("价格数据日", str(state.get("price_data_date", "N/A")), "close proxy 来源"),
        _mini_stat("执行状态", str(status), f"dry_run={state.get('dry_run', 'N/A')}"),
        _mini_stat("买入/卖出", f"{state.get('buy_count', 0)} / {state.get('sell_count', 0)}", "本地模拟数量"),
        _mini_stat("今日交易成本", _money(state.get("today_trade_cost")), f"佣金 {_money(state.get('today_commission'))}"),
        _mini_stat("滑点成本", _money(state.get("today_slippage_cost")), str(state.get("execution_price_type", PAPER_EXECUTION_PRICE_TYPE))),
        _mini_stat("重复跳过", str(state.get("skipped_duplicate", False)), str(state.get("skip_reason", "")) or "无"),
        _mini_stat("持仓数", str(state.get("position_count", engine.get("position_count", 0))), f"上限 {limits.get('max_holdings', PAPER_MAX_HOLDINGS)}"),
    ]
    disabled = "真实交易关闭" if not limits.get("real_trade_enabled") and not limits.get("broker_api_enabled") else "需要立刻复核"
    return (
        "<h3>今日模拟交易状态</h3>"
        + '<div class="grid four">'
        + "".join(rows)
        + "</div>"
        + '<div class="risk-banner" style="margin-top:14px;">'
        + f'<div class="risk-title">模式：{escape(str(limits.get("mode", PAPER_MODE)))}</div>'
        + f'<div>auto_execute={escape(str(limits.get("auto_execute", PAPER_AUTO_EXECUTE)))}；{escape(disabled)}；佣金率 {escape(str(limits.get("commission_rate", PAPER_COMMISSION_RATE)))}；最低佣金 {_money(limits.get("min_commission", PAPER_MIN_COMMISSION))}；滑点率 {escape(str(limits.get("slippage_rate", PAPER_SLIPPAGE_RATE)))}；ETF 模拟暂不计印花税。</div>'
        + "</div>"
    )


def _paper_trade_plan_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="muted">暂无今日模拟交易计划。daily_close 或手动运行 paper_trade_engine 后会刷新。</div>'
    body = []
    for row in rows:
        status = str(row.get("plan_status", "N/A"))
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('run_date') or row.get('date','')))}<div class=\"muted\">price data {escape(str(row.get('price_data_date','N/A')))}</div></td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('action','')))}</td>"
            f"<td>{_tag(status, _tag_class(status))}</td>"
            f"<td class=\"num\">{_number(row.get('raw_close', row.get('price')))}</td>"
            f"<td class=\"num\">{_number(row.get('execution_price', row.get('price')))}</td>"
            f"<td class=\"num\">{_number(row.get('quantity'))}</td>"
            f"<td class=\"num\">{_money(row.get('gross_amount', row.get('amount')))}</td>"
            f"<td class=\"num\">{_money(row.get('commission'))}</td>"
            f"<td class=\"num\">{_money(row.get('net_cash_change'))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('reason','')))[:180]}</div></td>"
            "</tr>"
        )
    return _table(["运行日 / 数据日", "ETF", "动作", "状态", "raw_close", "execution_price", "数量", "成交额", "佣金", "净现金变化", "原因"], body)


def _portfolio_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="panel">当前无模拟持仓。</div>'
    body = []
    for row in rows:
        pnl = _float(row.get("unrealized_pnl"))
        pnl_cls = "profit" if pnl > 0 else "loss" if pnl < 0 else "neutral"
        status_cls = _tag_class(row.get("signal_status"))
        action_cls = _tag_class(row.get("action_suggestion"))
        risk_cls = _tag_class(row.get("risk_tag"))
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b></td>"
            f"<td>{escape(str(row.get('name','')))}<div class=\"muted\">{escape(str(row.get('buy_reason_short','')))}</div></td>"
            f"<td>{escape(str(row.get('group','N/A')))}</td>"
            f"<td>{escape(str(row.get('etf_type','N/A')))}<div class=\"muted\">{escape(str(row.get('holding_profile','N/A')))} 天</div></td>"
            f"<td>{escape(str(row.get('holding_cycle_status','N/A')))}<div class=\"muted\">持仓 {escape(str(row.get('holding_days','N/A')))} / max {escape(str(row.get('max_holding_days','N/A')))} 天；保护期 {escape(str(row.get('protection_period','no')))}</div></td>"
            f"<td class=\"num\">{_money(row.get('market_value'))}</td>"
            f"<td class=\"num\">{_pct(row.get('position_ratio'))}</td>"
            f"<td class=\"num\">{_number(row.get('avg_cost', row.get('entry_price')))}<div class=\"muted\">佣金 {_money(row.get('commission_paid'))}</div></td>"
            f"<td class=\"num\">{_number(row.get('current_price'))}</td>"
            f"<td class=\"num {pnl_cls}\">{_money(row.get('unrealized_pnl'))}</td>"
            f"<td class=\"num {pnl_cls}\">{_pct(row.get('unrealized_pnl_pct'))}</td>"
            f"<td>{escape(str(row.get('buy_signal','N/A')))}</td>"
            f"<td>{escape(str(row.get('current_signal','N/A')))}</td>"
            f"<td>{_tag(row.get('short_swing_weakening'), _tag_class(row.get('short_swing_weakening')))}<div class=\"muted\">rank trend: {escape(str(row.get('rank_score_trend','N/A')))}</div></td>"
            f"<td>{_tag(row.get('signal_status'), status_cls)}<div class=\"muted\">sell: {escape(str(row.get('sell_review_status','N/A')))} / health: {escape(str(row.get('data_health_status','N/A')))}</div></td>"
            f"<td>{_tag(row.get('high_beta_risk_state') or 'N/A', _high_beta_state_class(row.get('high_beta_risk_state')))}<div class=\"muted\">10日波动 {_pct(row.get('high_beta_recent_volatility_10d'))} · 回撤 {_pct(row.get('high_beta_recent_drawdown_10d'))}</div></td>"
            f"<td class=\"num\">{_number(row.get('stop_loss'))}</td>"
            f"<td class=\"num\">{_pct(row.get('stop_distance_pct'))}</td>"
            f"<td>{_tag(row.get('risk_tag'), risk_cls)}</td>"
            f"<td>{_tag(row.get('sentiment_status'), _tag_class(row.get('sentiment_status')))}</td>"
            f"<td>{_tag(row.get('action_suggestion'), action_cls)}<div class=\"reason\">{escape(str(row.get('research_note','') or row.get('reason','')))[:150]}</div></td>"
            "</tr>"
        )
    headers = ["ETF", "名称", "group", "ETF 类型", "持仓周期", "仓位金额", "仓位比例", "成本价", "最新价", "浮盈亏", "浮盈亏率", "买入信号", "当前信号", "短周期/排名", "信号状态", "高波动风险", "止损价", "距离止损", "风险标签", "情绪占位", "动作建议"]
    return _table(headers, body)


def _paper_performance_panel(summary: dict, daily_rows: list[dict], trade_rows: list[dict]) -> str:
    if not summary or summary.get("status") in {"missing", "error"}:
        return '<div class="panel">暂无模拟仓绩效派生数据。运行 <code>python3 src/paper_performance.py</code> 后会生成。</div>'
    cards = [
        _metric("当前总资产", _money(summary.get("current_total_equity")), f"初始本金 {_money(summary.get('initial_cash'))}"),
        _metric("总盈亏", _signed_money(summary.get("total_pnl_amount")), f"总收益率 {_pct(summary.get('total_return_pct'))}"),
        _metric("现金 / 持仓", f"{_money(summary.get('current_cash'))} / {_money(summary.get('current_position_value'))}", "正式模拟仓口径"),
        _metric("已实现 / 未实现", f"{_signed_money(summary.get('realized_pnl'))} / {_signed_money(summary.get('unrealized_pnl'))}", "FIFO + 本地 close 估算"),
        _metric("最大回撤", _pct(summary.get("max_drawdown")), f"最高权益 {_money(summary.get('max_equity'))}"),
        _metric("交易 / 胜率", f"{summary.get('trade_count', 0)} / {_pct(summary.get('win_rate'))}", f"买 {summary.get('buy_count', 0)} 卖 {summary.get('sell_count', 0)}"),
        _metric("成本合计", _money(summary.get("total_cost")), f"佣金 {_money(summary.get('commission_total'))} · 滑点估算 {_money(summary.get('slippage_total'))}"),
        _metric("估值口径", str(summary.get("valuation_as_of_date", "N/A")), f"价格警告 {summary.get('valuation_price_warning_count', 0)} · 本地最新 close"),
        _metric("更新时间", str(summary.get("last_updated", "N/A")), f"数据日 {summary.get('latest_data_date', 'N/A')}"),
    ]
    return (
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + '<div class="grid two" style="margin-top:14px;">'
        + _paper_equity_curve_card(daily_rows)
        + _paper_trade_pnl_card(trade_rows)
        + "</div>"
        + '<div class="risk-banner" style="margin-top:14px;border-left-color:var(--blue);background:var(--blue-soft);border-color:#bed5ff;">'
        + '<div class="risk-title" style="color:var(--blue);">模拟仓绩效口径</div>'
        + "<div>这是 Paper Portfolio 派生统计，不是实盘账户；券商接口未连接，真实交易禁用。正式模拟仓使用实际交易流水初始权益，20000 只作为研究/回测主基准，不混入本账户绩效。</div>"
        + '<div class="links" style="margin-top:8px;"><a href="../reports/paper_performance_summary.md">绩效摘要</a><a href="../reports/paper_equity_curve.md">权益曲线</a><a href="../reports/paper_trade_pnl.md">交易盈亏</a><a href="../reports/paper_portfolio_metrics_audit.md">指标审计</a></div>'
        + "</div>"
    )


def _paper_equity_curve_card(rows: list[dict]) -> str:
    if not rows:
        return '<div class="chart-card"><h3>历史权益曲线</h3><div class="muted">暂无足够数据。</div></div>'
    points = rows[-80:]
    values = [_float(row.get("total_equity")) for row in points]
    if not values or max(values) == min(values):
        return '<div class="chart-card"><h3>历史权益曲线</h3><div class="muted">权益数据不足以绘制曲线。</div></div>'
    min_v, max_v = min(values), max(values)
    width, height = 320, 130
    coords = []
    for idx, value in enumerate(values):
        x = 12 + idx * (width - 24) / max(len(values) - 1, 1)
        y = 12 + (max_v - value) / (max_v - min_v) * (height - 24)
        coords.append(f"{x:.2f},{y:.2f}")
    last = points[-1]
    return f"""<div class="chart-card">
      <h3>历史权益曲线</h3>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="paper equity curve">
        <rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#fbfcfe"/>
        <polyline points="{' '.join(coords)}" fill="none" stroke="#1455d9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="12" y1="{height - 12}" x2="{width - 12}" y2="{height - 12}" stroke="#d8dee8"/>
      </svg>
      <div class="muted">最近 {len(points)} 个交易日 · 最新 {escape(str(last.get('date', 'N/A')))} · 总资产 {_money(last.get('total_equity'))} · 回撤 {_pct(last.get('drawdown'))}</div>
    </div>"""


def _paper_trade_pnl_card(rows: list[dict]) -> str:
    if not rows:
        return '<div class="chart-card"><h3>交易盈亏</h3><div class="muted">暂无交易盈亏配对数据。</div></div>'
    body = []
    for row in rows[-8:]:
        pnl = _float(row.get("net_pnl"))
        cls = "profit" if pnl > 0 else "loss" if pnl < 0 else "neutral"
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('symbol','')))}<div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('status','')))}</td>"
            f"<td>{escape(str(row.get('buy_date','')))}<div class=\"muted\">{escape(str(row.get('sell_date','未平仓')))}</div></td>"
            f"<td class=\"num\">{_number(row.get('quantity'))}</td>"
            f"<td class=\"num {cls}\">{_signed_money(row.get('net_pnl'))}</td>"
            f"<td class=\"num\">{_pct(row.get('return_pct'))}</td>"
            "</tr>"
        )
    return '<div class="chart-card"><h3>交易盈亏</h3>' + _table(["ETF", "状态", "买入 / 卖出", "数量", "净盈亏", "收益率"], body) + "</div>"


def _trade_review_panel(summary: dict, details: list[dict], open_positions: list[dict]) -> str:
    if not summary or summary.get("status") in {"missing", "error"}:
        return '<div class="panel">暂无交易复盘数据。运行 <code>python3 src/trade_review.py</code> 后会生成。</div>'
    cards = [
        _metric("交易总数", str(summary.get("trade_count", 0)), f"复盘单元 {summary.get('review_trade_count', 0)}"),
        _metric("已平仓 / 未平仓", f"{summary.get('closed_trade_count', 0)} / {summary.get('open_position_count', 0)}", "交易闭环仍少"),
        _metric("最大单笔盈利", _signed_money(summary.get("largest_net_profit")), "含未平仓浮盈"),
        _metric("最大单笔亏损", _signed_money(summary.get("largest_net_loss")), "已平仓/未平仓合计"),
        _metric("最大浮盈 MFE", _pct(summary.get("largest_mfe_pct")), "日线 high 估算"),
        _metric("最大浮亏 MAE", _pct(summary.get("largest_mae_pct")), "日线 low 估算"),
        _metric("成本影响", _money(summary.get("cost_impact_total")), "模拟交易成本"),
        _metric("更新时间", str(summary.get("last_updated", "N/A")), "trade_review"),
    ]
    return (
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + '<div class="risk-banner" style="margin-top:14px;">'
        + f'<div class="risk-title">主要问题：{escape(str(summary.get("main_issue", "N/A")))}</div>'
        + f'<div>正面信号：{escape(str(summary.get("positive_signal", "N/A")))}</div>'
        + f'<div>样本提醒：{escape(str(summary.get("sample_warning", "样本较少，不能判断策略稳定盈利。")))}</div>'
        + "</div>"
        + '<div class="grid two" style="margin-top:14px;">'
        + _trade_review_closed_card(details)
        + _trade_review_open_card(open_positions)
        + "</div>"
        + '<div class="links" style="margin-top:12px;"><a href="../reports/trade_review_summary.md">复盘摘要</a><a href="../reports/trade_review_details.md">逐笔明细</a><a href="../reports/trade_review_open_positions.md">未平仓复盘</a><a href="../reports/trade_review_lessons.md">经验总结</a><a href="../reports/trade_review_audit.md">数据审计</a></div>'
    )


def _trade_review_closed_card(rows: list[dict]) -> str:
    closed = [row for row in rows if str(row.get("status", "")).lower() == "closed"]
    if not closed:
        return '<div class="chart-card"><h3>已平仓交易复盘</h3><div class="muted">暂无足够已平仓样本。</div></div>'
    body = []
    for row in closed[-8:]:
        pnl = _float(row.get("net_pnl"))
        cls = "profit" if pnl > 0 else "loss" if pnl < 0 else "neutral"
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('symbol','')))}<div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('buy_date','')))}<div class=\"muted\">{escape(str(row.get('sell_date','')))}</div></td>"
            f"<td class=\"num\">{escape(str(row.get('holding_days','')))}</td>"
            f"<td class=\"num {cls}\">{_signed_money(row.get('net_pnl'))}</td>"
            f"<td class=\"num\">{_pct(row.get('return_pct'))}</td>"
            f"<td class=\"num\">{_money(row.get('max_favorable_excursion'))}</td>"
            f"<td class=\"num\">{_money(row.get('max_adverse_excursion'))}</td>"
            f"<td>{escape(str(row.get('sell_timing_assessment','')))}<div class=\"muted\">{escape(str(row.get('review_tag','')))[:120]}</div></td>"
            "</tr>"
        )
    return '<div class="chart-card"><h3>已平仓交易复盘</h3>' + _table(["ETF", "买入 / 卖出", "天数", "净盈亏", "收益率", "MFE", "MAE", "卖出评估 / 标签"], body) + "</div>"


def _trade_review_open_card(rows: list[dict]) -> str:
    if not rows:
        return '<div class="chart-card"><h3>未平仓持仓复盘</h3><div class="muted">当前无未平仓持仓。</div></div>'
    body = []
    for row in rows[-8:]:
        pnl = _float(row.get("unrealized_pnl"))
        cls = "profit" if pnl > 0 else "loss" if pnl < 0 else "neutral"
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('symbol','')))}<div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('entry_date','')))}</td>"
            f"<td class=\"num\">{_number(row.get('latest_price'))}</td>"
            f"<td class=\"num {cls}\">{_signed_money(row.get('unrealized_pnl'))}</td>"
            f"<td class=\"num\">{_pct(row.get('unrealized_return_pct'))}</td>"
            f"<td class=\"num\">{_money(row.get('max_favorable_excursion'))}</td>"
            f"<td class=\"num\">{_money(row.get('max_adverse_excursion'))}</td>"
            f"<td class=\"num\">{_pct(row.get('current_drawdown_from_best'))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('review_comment','')))[:160]}</div></td>"
            "</tr>"
        )
    return '<div class="chart-card"><h3>未平仓持仓复盘</h3>' + _table(["ETF", "买入日", "最新价", "浮盈亏", "收益率", "MFE", "MAE", "高点回撤", "复盘结论"], body) + "</div>"


def _ranking_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="panel">暂无 BUY ranking。</div>'
    body = []
    for row in rows[:12]:
        risk_note = str(row.get("risk_note") or "无")
        risk_cls = "warn" if risk_note != "无" else "ok"
        resonance = "双周期共振" if str(row.get("resonance_flag", "")) == "是" else "非共振"
        body.append(
            "<tr>"
            f"<td class=\"num\">{escape(str(row.get('rank','')))}</td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b></td>"
            f"<td>{escape(str(row.get('name','')))}</td>"
            f"<td>{escape(str(row.get('group','N/A')))}</td>"
            f"<td>{escape(str(row.get('mid_trend_signal','N/A')))} / {escape(str(row.get('short_swing_signal','N/A')))}<div class=\"muted\">{resonance}</div></td>"
            f"<td class=\"num\"><b>{_score(row.get('rank_score'))}</b></td>"
            f"<td>{_score_bar('mid', row.get('mid_trend_score'), 30)}</td>"
            f"<td>{_score_bar('mom', row.get('short_momentum_score'), 25)}</td>"
            f"<td>{_score_bar('liq', row.get('liquidity_score'), 15)}</td>"
            f"<td>{_score_bar('risk', row.get('risk_score'), 15)}</td>"
            f"<td>{_score_bar('res', row.get('resonance_score'), 10)}</td>"
            f"<td>{_score_bar('dq', row.get('data_quality_score'), 5)}</td>"
            f"<td>{_tag(risk_note, risk_cls)}</td>"
            f"<td>{_tag(row.get('candidate_action'), 'blue' if row.get('candidate_action') == 'candidate' else 'warn')}</td>"
            "</tr>"
        )
    headers = ["rank", "symbol", "name", "group", "双周期", "rank_score", "mid", "momentum", "liquidity", "risk", "resonance", "data_quality", "risk_note", "candidate_action"]
    return _table(headers, body)


def _sell_review_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="panel">暂无卖出复核结果。</div>'
    body = []
    for row in rows:
        status = str(row.get("sell_review_status", "N/A"))
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b></td>"
            f"<td>{escape(str(row.get('name','')))}</td>"
            f"<td>{escape(str(row.get('etf_type','N/A')))}<div class=\"muted\">{escape(str(row.get('sell_sensitivity','N/A')))}</div></td>"
            f"<td class=\"num\">{escape(str(row.get('holding_days','N/A')))}</td>"
            f"<td class=\"num\">{_score(row.get('rank_score'))}</td>"
            f"<td class=\"num\">{_score(row.get('rank_score_change'))}<div class=\"muted\">连续 {escape(str(row.get('rank_decline_days','N/A')))} 天</div></td>"
            f"<td>{escape(str(row.get('mid_trend_signal','N/A')))} / {escape(str(row.get('short_swing_signal','N/A')))}</td>"
            f"<td class=\"num\">{_number(row.get('stop_loss'))}</td>"
            f"<td class=\"num\">{_pct(row.get('stop_distance_pct'))}</td>"
            f"<td>{_tag(str(row.get('data_health_status','N/A')), _tag_class(row.get('data_health_status')))}<div class=\"muted\">{escape(str(row.get('data_health_note','')))[:80]}</div></td>"
            f"<td>{_tag(status, _sell_status_class(status))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('action_note','')))[:160]}</div></td>"
            "</tr>"
        )
    headers = ["ETF", "名称", "类型/敏感度", "持仓天数", "rank_score", "rank变化", "mid/short", "止损价", "距离止损", "data_health", "复核状态", "动作说明"]
    return '<div class="panel">' + _table(headers, body) + '<div class="muted" style="margin-top:10px;">只生成候选复核，不提供真实交易按钮，不写 paper_trades。</div></div>'


def _position_review_state_panel(rows: list[dict], summary: dict) -> str:
    if not rows:
        return '<div class="panel">暂无持仓观察分层结果。运行 <code>python3 src/position_review_state.py</code> 后刷新。</div>'
    cards = [
        _mini_stat("REDUCE_CANDIDATE", str(summary.get("reduce_candidate_count", 0)), "观察状态，不自动减仓"),
        _mini_stat("REVIEW_2", str(summary.get("review_2_count", 0)), "重点复核"),
        _mini_stat("high_beta 观察", str(summary.get("high_beta_watch_count", 0)), "高波动标签"),
        _mini_stat("浮盈保护", str(summary.get("profit_protection_watch_count", 0)), "只提示不止盈"),
    ]
    body = []
    for row in rows:
        state = str(row.get("review_state", "N/A"))
        state_label = f"{state} / {row.get('review_state_cn', '')}"
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{_tag(state_label, _review_state_class(state))}<div class=\"muted\">level {escape(str(row.get('review_level','N/A')))}</div></td>"
            f"<td>{escape(str(row.get('mid_trend','N/A')))} / {escape(str(row.get('short_swing','N/A')))}</td>"
            f"<td class=\"num\">{_score(row.get('rank'))}<div class=\"muted\">变化 {_score(row.get('rank_change'))} · {escape(str(row.get('rank_decay_days','0')))} 天</div></td>"
            f"<td class=\"num\">{_signed_money(row.get('unrealized_pnl'))}<div class=\"muted\">{_pct(row.get('unrealized_pnl_pct'))}</div></td>"
            f"<td>{escape(str(row.get('group','N/A')))}<div class=\"muted\">{escape(str(row.get('type','N/A')))} · high_beta={escape(str(row.get('high_beta_flag', False)))}</div></td>"
            f"<td>{escape(str(row.get('review_reasons','')))[:260]}</td>"
            f"<td>{escape(str(row.get('recommended_review_action','')))[:180]}<div class=\"muted\">execution_allowed={escape(str(row.get('execution_allowed', False))).lower()}</div></td>"
            "</tr>"
        )
    return (
        '<div class="panel"><div class="risk-banner" style="margin-bottom:14px;"><div class="risk-title">观察状态，不会自动交易</div>'
        '<div>REDUCE_CANDIDATE 不是减仓指令；REVIEW_2 不是卖出指令；所有动作都需要人工复核。</div></div>'
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + _table(["ETF", "观察状态", "mid/short", "rank", "浮盈亏", "分组/类型", "复核原因", "观察动作"], body)
        + '<div class="links" style="margin-top:12px;"><a href="../reports/position_review_state.md">持仓观察分层报告</a><a href="../reports/review_state_audit.md">REVIEW 审计报告</a></div>'
        + "</div>"
    )


def _profit_protection_panel(rows: list[dict], summary: dict) -> str:
    if not rows:
        return '<div class="panel">暂无浮盈保护 Preview。运行 <code>python3 src/profit_protection_preview.py</code> 后刷新。</div>'
    cards = [
        _mini_stat("PROFIT_WATCH", str(summary.get("profit_watch_count", 0)), "浮盈观察"),
        _mini_stat("PROTECTION_REVIEW", str(summary.get("profit_protection_review_count", 0)), "保护复核"),
        _mini_stat("LOCK_CANDIDATE", str(summary.get("profit_lock_candidate_count", 0)), "不是卖出信号"),
        _mini_stat("峰值回撤合计", _money(summary.get("total_drawdown_from_profit_peak", 0)), "只读估算"),
    ]
    body = []
    for row in rows:
        state = str(row.get("profit_protection_state", "N/A"))
        label = f"{state} / {row.get('profit_protection_state_cn', '')}"
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{_tag(label, _profit_state_class(state))}<div class=\"muted\">level {escape(str(row.get('profit_protection_level','N/A')))}</div></td>"
            f"<td class=\"num\">{_signed_money(row.get('current_unrealized_pnl'))}<div class=\"muted\">{_pct(row.get('current_unrealized_pnl_pct'))}</div></td>"
            f"<td class=\"num\">{_signed_money(row.get('peak_unrealized_pnl'))}<div class=\"muted\">{escape(str(row.get('peak_date','N/A')))}</div></td>"
            f"<td class=\"num\">{_signed_money(row.get('drawdown_from_profit_peak'))}<div class=\"muted\">{_pct(row.get('drawdown_from_profit_peak_pct'))}</div></td>"
            f"<td>{escape(str(row.get('mid_trend','N/A')))} / {escape(str(row.get('short_swing','N/A')))}<div class=\"muted\">rank decline {escape(str(row.get('rank_decay_days','0')))} 天</div></td>"
            f"<td>{escape(str(row.get('profit_protection_reasons','')))[:260]}</td>"
            f"<td>{escape(str(row.get('recommended_review_action','')))[:180]}<div class=\"muted\">execution_allowed={escape(str(row.get('execution_allowed', False))).lower()}</div></td>"
            "</tr>"
        )
    return (
        '<div class="panel"><div class="risk-banner" style="margin-bottom:14px;"><div class="risk-title">浮盈保护为研究观察指标，不会自动交易</div>'
        '<div>PROFIT_LOCK_CANDIDATE 不是卖出信号；本模块不会自动止盈、自动减仓或写交易记录。</div></div>'
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + _table(["ETF", "浮盈状态", "当前浮盈", "峰值浮盈", "峰值回撤", "mid/short", "原因", "观察动作"], body)
        + '<div class="links" style="margin-top:12px;"><a href="../reports/profit_protection_preview.md">浮盈保护 Preview 报告</a></div>'
        + "</div>"
    )


def _high_beta_risk_panel(rows: list[dict], summary: dict) -> str:
    if not rows:
        return '<div class="panel">暂无高波动持仓观察结果。运行 <code>python3 src/high_beta_risk_watch.py</code> 后刷新。</div>'
    state = str(summary.get("high_beta_exposure_state", "HB_NORMAL"))
    cards = [
        _mini_stat("高波动持仓", str(summary.get("high_beta_position_count", 0)), "只观察不交易"),
        _mini_stat("高波动/总权益", _pct(summary.get("high_beta_weight_of_equity", 0)), state),
        _mini_stat("高波动/持仓", _pct(summary.get("high_beta_weight_of_holdings", 0)), "组合内占比"),
        _mini_stat("金融地产/持仓", _pct(summary.get("finance_real_estate_weight_of_holdings", 0)), "集中度观察"),
    ]
    body = []
    for row in rows:
        risk_state = str(row.get("high_beta_risk_state", "N/A"))
        label = f"{risk_state} / {row.get('high_beta_risk_level', '')}"
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('group','N/A')))}<div class=\"muted\">{escape(str(row.get('type','N/A')))}</div></td>"
            f"<td>{_tag(label, _high_beta_state_class(risk_state))}<div class=\"muted\">execution_allowed={escape(str(row.get('execution_allowed', False))).lower()}</div></td>"
            f"<td class=\"num\">{_money(row.get('market_value'))}<div class=\"muted\">权益 {_pct(row.get('position_weight_of_equity'))} · 持仓 {_pct(row.get('position_weight_of_holdings'))}</div></td>"
            f"<td class=\"num\">{_pct(row.get('recent_return_5d'))}<div class=\"muted\">10日 {_pct(row.get('recent_return_10d'))}</div></td>"
            f"<td class=\"num\">{_pct(row.get('recent_volatility_10d'))}<div class=\"muted\">回撤 {_pct(row.get('recent_drawdown_10d'))}</div></td>"
            f"<td>{escape(str(row.get('mid_trend','N/A')))} / {escape(str(row.get('short_swing','N/A')))}<div class=\"muted\">rank {escape(str(row.get('rank','N/A')))} · decay {escape(str(row.get('rank_decay_days','0')))} 天</div></td>"
            f"<td>{escape(str(row.get('high_beta_risk_reasons','')))[:260]}</td>"
            f"<td>{escape(str(row.get('recommended_review_action','')))[:180]}</td>"
            "</tr>"
        )
    reasons = summary.get("high_beta_exposure_reasons", "")
    return (
        '<div class="panel"><div class="risk-banner" style="margin-bottom:14px;"><div class="risk-title">高波动观察不会触发自动交易</div>'
        f'<div>{escape(str(reasons or "当前无高波动暴露异常。"))}</div>'
        '<div>512880 证券类 ETF 对市场情绪敏感；若金融地产组暴露偏高，需观察组合集中度。</div></div>'
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + _table(["ETF", "分组/类型", "高波动状态", "市值/权重", "5/10日收益", "10日波动/回撤", "mid/short", "原因", "观察动作"], body)
        + '<div class="links" style="margin-top:12px;"><a href="../reports/high_beta_risk_watch.md">高波动风险观察报告</a></div>'
        + "</div>"
    )


def _strategy_preview_panel(data: dict) -> str:
    if not data or not data.get("rows"):
        return '<div class="panel">暂无 B1 策略增强预览。运行 <code>python3 src/strategy_enhancement_preview.py</code> 后刷新。</div>'
    rows = data.get("rows", [])
    original = data.get("original_top3", [])
    adjusted = data.get("adjusted_top3", [])
    safety = data.get("execution_safety", {})
    cards = [
        _mini_stat("Top 3 是否变化", "是" if data.get("top3_changed") else "否", "preview only"),
        _mini_stat("market_state", str(data.get("market_state", "N/A")), f"score {_score(data.get('market_score'))}"),
        _mini_stat("组合暴露", str(data.get("portfolio_exposure_status", "N/A")), "不硬阻断"),
        _mini_stat("执行开关", str(safety.get("adjusted_rank_score_execution_enabled", False)), "adjusted 不执行"),
    ]
    original_rows = _preview_top_rows(original, "original_rank", "original_rank_score")
    adjusted_rows = _preview_top_rows(adjusted, "adjusted_rank_preview", "adjusted_rank_score_preview")
    delta_rows = []
    for row in sorted(rows, key=lambda item: abs(_float(item.get("score_delta"))), reverse=True)[:8]:
        delta = _float(row.get("score_delta"))
        delta_cls = "ok" if delta > 0 else "danger" if delta < 0 else "blue"
        delta_rows.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('etf_type','N/A')))}<div class=\"muted\">{escape(str(row.get('group','N/A')))}</div></td>"
            f"<td class=\"num\">{_score(row.get('original_rank_score'))}</td>"
            f"<td class=\"num\">{_score(row.get('adjusted_rank_score_preview'))}</td>"
            f"<td>{_tag(_score(row.get('score_delta')), delta_cls)}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('enhancement_reason','')))[:180]}</div></td>"
            f"<td>{_tag(row.get('execution_status'), 'blue')}</td>"
            "</tr>"
        )
    hit_summary = [
        _mini_stat("宽基 bonus", str(len(data.get("broad_index_bonus_hits", []))), "缺宽基 +3"),
        _mini_stat("防御 bonus", str(len(data.get("defensive_bonus_hits", []))), "非 strong +1.5"),
        _mini_stat("high_beta 降权", str(len(data.get("high_beta_penalty_hits", []))), "-2"),
        _mini_stat("data_health 降权", str(len(data.get("data_health_penalty_hits", []))), "-3 / -999"),
    ]
    return (
        '<div class="grid two">'
        + '<div class="panel"><h3>B1 Preview Summary</h3><div class="grid four">'
        + "".join(cards)
        + "</div></div>"
        + '<div class="panel"><h3>Hit Summary</h3><div class="grid four">'
        + "".join(hit_summary)
        + "</div></div>"
        + '<div class="panel"><h3>Original Top 3</h3>'
        + _table(["rank", "ETF", "score", "原因"], original_rows)
        + "</div>"
        + '<div class="panel"><h3>Adjusted Preview Top 3</h3>'
        + _table(["rank", "ETF", "score", "原因"], adjusted_rows)
        + "</div>"
        + '<div class="panel" style="grid-column:1/-1;"><h3>Score Delta 最大项</h3>'
        + _table(["ETF", "类型/group", "original", "adjusted", "delta", "原因", "执行状态"], delta_rows)
        + '<div class="muted" style="margin-top:10px;">adjusted_rank_score_preview_enabled=true；adjusted_rank_score_execution_enabled=false；本模块不改变 paper_trade_engine。</div>'
        + '<div class="links" style="margin-top:12px;"><a href="../reports/strategy_enhancement_preview.md">预览报告</a><a href="../reports/b1_strategy_enhancement_preview_report.md">B1 报告</a></div>'
        + "</div></div>"
    )


def _broad_base_balance_panel(data: dict) -> str:
    if not data or not data.get("rows"):
        return '<div class="panel">暂无宽基平衡 preview。运行 <code>python3 src/broad_base_balance_preview.py</code> 后刷新。</div>'
    summary = data.get("summary", {})
    rows = data.get("rows", [])
    cards = [
        _mini_stat("宽基占比", _pct(summary.get("broad_base_weight", 0)), str(summary.get("broad_base_balance_state", "N/A"))),
        _mini_stat("行业/主题占比", _pct(summary.get("theme_weight", 0)), str(summary.get("theme_concentration_state", "N/A"))),
        _mini_stat("金融地产", _pct(summary.get("finance_real_estate_weight", 0)), "持仓内权重"),
        _mini_stat("科技成长", _pct(summary.get("tech_growth_weight", 0)), "持仓内权重"),
        _mini_stat("high_beta", _pct(summary.get("high_beta_weight", 0)), "观察风险"),
        _mini_stat("候选数", str(summary.get("balance_candidate_count", 0)), "preview only"),
        _mini_stat("假设金额", _money(data.get("preview_add_amount", summary.get("preview_add_amount", 500))), "不写交易"),
        _mini_stat("执行开关", str(summary.get("execution_allowed", False)), "必须为 false"),
    ]
    body = []
    for row in rows[:10]:
        state_cls = "ok" if row.get("mid_trend") == "BUY" and row.get("short_swing") == "BUY" else "warn"
        body.append(
            "<tr>"
            f"<td class=\"num\">{escape(str(row.get('balance_candidate_rank','')))}</td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('type','')))}<div class=\"muted\">{escape(str(row.get('group','')))}</div></td>"
            f"<td>{_tag(str(row.get('mid_trend','N/A')) + '/' + str(row.get('short_swing','N/A')), state_cls)}</td>"
            f"<td class=\"num\">{_score(row.get('raw_score'))}<div class=\"muted\">rank {escape(str(row.get('raw_rank','N/A')))}</div></td>"
            f"<td class=\"num\">{_score(row.get('adjusted_score'))}<div class=\"muted\">rank {escape(str(row.get('adjusted_rank','N/A')))}</div></td>"
            f"<td class=\"num\">{_score(row.get('balance_improvement_score'))}</td>"
            f"<td class=\"num\">{_pct(row.get('new_broad_base_weight'))}<div class=\"muted\">集中度改善 {_pct(row.get('concentration_change'))}</div></td>"
            f"<td>{escape(str(row.get('candidate_reason','')))[:240]}</td>"
            f"<td>{_tag('preview_only_not_executed', 'blue')}<div class=\"muted\">execution_allowed={escape(str(row.get('execution_allowed', False))).lower()}</div></td>"
            "</tr>"
        )
    return (
        '<div class="panel"><div class="risk-banner" style="margin-bottom:14px;"><div class="risk-title">宽基平衡只做观察，不自动买入</div>'
        f'<div>{escape(str(summary.get("summary_text", "当前暂无宽基平衡摘要。")))}</div></div>'
        '<div class="grid four">'
        + "".join(cards)
        + "</div>"
        + _table(["rank", "ETF", "类型/group", "mid/short", "raw", "adjusted", "balance_score", "假设加入后宽基", "原因", "状态"], body)
        + '<div class="links" style="margin-top:12px;"><a href="../reports/broad_base_balance_preview.md">宽基平衡观察报告</a><a href="../reports/broad_base_balance_preview.csv">候选 CSV</a></div>'
        + "</div>"
    )


def _preview_top_rows(rows: list[dict], rank_key: str, score_key: str) -> list[str]:
    out = []
    for row in rows[:3]:
        out.append(
            "<tr>"
            f"<td class=\"num\">{escape(str(row.get(rank_key, '')))}</td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td class=\"num\">{_score(row.get(score_key))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('enhancement_reason','original ranking')))[:160]}</div></td>"
            "</tr>"
        )
    return out


def _preview_tracking_panel(data: dict) -> str:
    if not data or not data.get("rows"):
        return '<div class="panel">暂无 B2 影子跟踪账本。运行 <code>python3 src/strategy_preview_tracking.py</code> 后刷新。</div>'
    summary = data.get("summary", {})
    comparison = data.get("forward_return_comparison", {})
    safety = data.get("execution_safety", {})
    cards = [
        _mini_stat("样本数", str(summary.get("sample_count", 0)), f"completed {summary.get('completed_count', 0)}"),
        _mini_stat("pending", str(summary.get("pending_count", 0)), f"partial {summary.get('partial_count', 0)}"),
        _mini_stat("only original / adjusted", f"{summary.get('only_original_count', 0)} / {summary.get('only_adjusted_count', 0)}", "Top 3 差异"),
        _mini_stat("Top 3 变化", "是" if summary.get("top3_changed") else "否", "今日 snapshot"),
    ]
    original_rows = _tracking_top_rows(summary.get("original_top3", []), "original_rank", "original_rank_score")
    adjusted_rows = _tracking_top_rows(summary.get("adjusted_top3", []), "adjusted_rank_preview", "adjusted_rank_score_preview")
    return_rows = []
    for group_name, row in comparison.get("returns", {}).items():
        return_rows.append(
            "<tr>"
            f"<td>{escape(str(group_name))}</td>"
            f"<td class=\"num\">{escape(str(row.get('sample_count', 0)))}</td>"
            f"<td class=\"num\">{_pct(row.get('forward_1d_mean'))}<div class=\"muted\">n={escape(str(row.get('forward_1d_n', 0)))}</div></td>"
            f"<td class=\"num\">{_pct(row.get('forward_3d_mean'))}<div class=\"muted\">n={escape(str(row.get('forward_3d_n', 0)))}</div></td>"
            f"<td class=\"num\">{_pct(row.get('forward_5d_mean'))}<div class=\"muted\">n={escape(str(row.get('forward_5d_n', 0)))}</div></td>"
            f"<td class=\"num\">{_pct(row.get('forward_10d_mean'))}<div class=\"muted\">n={escape(str(row.get('forward_10d_n', 0)))}</div></td>"
            "</tr>"
        )
    penalty = data.get("penalty_bonus_review", {})
    penalty_cards = [
        _mini_stat("high_beta penalty", _pct(penalty.get("high_beta_penalty", {}).get("forward_1d_mean")), f"n={penalty.get('high_beta_penalty', {}).get('forward_1d_n', 0)}"),
        _mini_stat("data_health penalty", _pct(penalty.get("data_health_penalty", {}).get("forward_1d_mean")), f"n={penalty.get('data_health_penalty', {}).get('forward_1d_n', 0)}"),
        _mini_stat("concentration penalty", _pct(penalty.get("concentration_penalty", {}).get("forward_1d_mean")), f"n={penalty.get('concentration_penalty', {}).get('forward_1d_n', 0)}"),
        _mini_stat("bonus hits", str(data.get("bonus_hit_count", 0)), "broad/defensive"),
    ]
    return (
        '<div class="grid two">'
        + '<div class="panel"><h3>Tracking Summary</h3><div class="grid four">'
        + "".join(cards)
        + f'</div><div class="risk-banner" style="margin-top:14px;"><div class="risk-title">结论</div><div>{escape(str(summary.get("conclusion", "当前样本不足，不能证明 adjusted preview 优于 original ranking。")))}</div></div></div>'
        + '<div class="panel"><h3>Execution Safety</h3><div class="grid four">'
        + _mini_stat("preview enabled", str(safety.get("adjusted_rank_score_preview_enabled", True)), "只展示")
        + _mini_stat("adjusted execution", str(safety.get("adjusted_rank_score_execution_enabled", False)), "必须 false")
        + _mini_stat("shadow enabled", str(safety.get("shadow_model_enabled", True)), "research only")
        + _mini_stat("shadow execution", str(safety.get("shadow_model_execution_enabled", False)), "必须 false")
        + "</div></div>"
        + '<div class="panel"><h3>Original Top 3</h3>'
        + _table(["rank", "ETF", "score", "status"], original_rows)
        + "</div>"
        + '<div class="panel"><h3>Adjusted Preview Top 3</h3>'
        + _table(["rank", "ETF", "score", "status"], adjusted_rows)
        + "</div>"
        + '<div class="panel" style="grid-column:1/-1;"><h3>Forward Return Comparison</h3>'
        + _table(["group", "sample", "1d mean", "3d mean", "5d mean", "10d mean"], return_rows)
        + '<div class="muted" style="margin-top:10px;">forward returns 只在未来交易日数据已存在后回填；pending 不是失败。</div></div>'
        + '<div class="panel" style="grid-column:1/-1;"><h3>Penalty / Bonus Review</h3><div class="grid four">'
        + "".join(penalty_cards)
        + '</div><div class="links" style="margin-top:12px;"><a href="../reports/strategy_preview_tracking_report.md">跟踪报告</a><a href="../reports/strategy_preview_shadow_portfolio.md">影子组合</a><a href="../reports/b2_strategy_preview_tracking_report.md">B2 报告</a></div></div>'
        + "</div>"
    )


def _tracking_top_rows(rows: list[dict], rank_key: str, score_key: str) -> list[str]:
    out = []
    for row in rows[:3]:
        status = str(row.get("forward_returns_status", "pending"))
        out.append(
            "<tr>"
            f"<td class=\"num\">{escape(str(row.get(rank_key, '')))}</td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td class=\"num\">{_score(row.get(score_key))}</td>"
            f"<td>{_tag(status, 'blue' if status == 'pending' else 'ok' if status == 'completed' else 'warn')}</td>"
            "</tr>"
        )
    return out


def _type_aware_review_panel(data: dict, safety: dict) -> str:
    rows = data.get("rows", []) if data else []
    if not rows:
        return '<div class="panel">暂无类型化复核结果。运行 sell_signal_review 后刷新。</div>'
    cards = [
        _mini_stat("持仓数", str(data.get("position_count", len(rows))), "paper positions"),
        _mini_stat("elevated", str(data.get("elevated_count", 0)), "类型化高关注"),
        _mini_stat("只提示不交易", "true", "不自动 SELL"),
        _mini_stat("真实交易", str(safety.get("real_trade_enabled", False)), "broker_api=false"),
    ]
    body = []
    for row in rows:
        severity = str(row.get("type_review_severity", "N/A"))
        body.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('etf_type','N/A')))}<div class=\"muted\">{escape(str(row.get('type_risk_level','N/A')))}</div></td>"
            f"<td class=\"num\">{escape(str(row.get('type_max_holding_days','N/A')))}</td>"
            f"<td class=\"num\">{_pct(row.get('type_holding_day_progress'))}</td>"
            f"<td>{escape(str(row.get('type_distance_to_stop_status','N/A')))}</td>"
            f"<td>{_tag(severity, 'warn' if severity == 'elevated' else 'ok')}</td>"
            f"<td>{_tag(row.get('sell_review_status'), _sell_status_class(row.get('sell_review_status')))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('etf_type_review_note','')))[:220]}</div></td>"
            "</tr>"
        )
    return (
        '<div class="panel"><div class="grid four">'
        + "".join(cards)
        + "</div>"
        + _table(["ETF", "类型/风险", "type_max_days", "持仓进度", "距离止损状态", "type_severity", "sell_review", "类型化说明"], body)
        + '<div class="muted" style="margin-top:10px;">类型化 REVIEW 不改变 SELL 判定，不写 paper_trades，不修改 paper_positions。</div></div>'
    )


def _phase2c_panel(data: dict) -> str:
    if not data:
        return '<div class="panel">暂无 Phase 2C 轻量接入数据。运行 paper_trade_engine dry-run 后刷新。</div>'
    market = data.get("market_state_vs_position", {})
    type_risk = data.get("etf_type_risk", [])
    balance = data.get("portfolio_balance", {})
    confidence = data.get("research_confidence", {})
    integrated = data.get("integrated", [])
    display_only = data.get("display_only", [])
    not_integrated = data.get("not_integrated", [])
    rows = [
        _mini_stat("market_state", str(market.get("market_state", "N/A")), f"score {_score(market.get('market_score'))}"),
        _mini_stat("建议仓位", str(market.get("suggested_position_pct", "N/A")), f"当前 {_pct(market.get('current_position_pct'))}"),
        _mini_stat("仓位匹配", str(market.get("position_alignment", "N/A")), f"use_market_state={data.get('use_market_state_position', False)}"),
        _mini_stat("组合状态", str(balance.get("portfolio_exposure_status", "N/A")), f"提示 {len(balance.get('warnings', []))}"),
    ]
    type_rows = []
    for row in type_risk:
        type_rows.append(
            "<tr>"
            f"<td>{escape(str(row.get('symbol','')))}</td>"
            f"<td>{escape(str(row.get('name','')))}</td>"
            f"<td>{escape(str(row.get('etf_type','')))}</td>"
            f"<td>{escape(str(row.get('risk_profile','')))}</td>"
            f"<td class=\"num\">{escape(str(row.get('max_holding_days','')))}</td>"
            f"<td class=\"num\">{_pct(row.get('stop_loss_pct'))}</td>"
            f"<td class=\"num\">{_pct(row.get('distance_to_stop_pct'))}</td>"
            f"<td>{_tag(row.get('holding_period_status'), _tag_class(row.get('holding_period_status')))}</td>"
            "</tr>"
        )
    balance_items = balance.get("suggestions", []) + balance.get("warnings", [])
    balance_html = "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in balance_items[:6]) + "</ul>" if balance_items else '<div class="muted">暂无组合平衡提示。</div>'
    confidence_text = ", ".join(f"{k}: {v}" for k, v in confidence.items()) or "N/A"
    return (
        '<div class="grid two">'
        + '<div class="panel"><h3>Market State vs Position</h3><div class="grid four">'
        + "".join(rows)
        + "</div></div>"
        + '<div class="panel"><h3>Research Confidence</h3>'
        + f'<div class="muted">{escape(confidence_text)}</div>'
        + _recommendation_list("已轻量接入", integrated, "ok")
        + _recommendation_list("只展示不执行", display_only, "warn")
        + _recommendation_list("仍未接入", not_integrated, "danger")
        + "</div>"
        + '<div class="panel"><h3>ETF Type Risk</h3>'
        + (_table(["ETF", "名称", "类型", "risk_profile", "max_days", "stop_loss_pct", "距离止损", "持有期状态"], type_rows) if type_rows else '<div class="muted">暂无持仓类型风险。</div>')
        + "</div>"
        + '<div class="panel"><h3>Portfolio Balance Suggestions</h3>'
        + balance_html
        + '<div class="links" style="margin-top:12px;"><a href="../reports/phase2c_execution_layer_light_integration_report.md">Phase 2C 报告</a><a href="../reports/paper_trade_plan.md">交易计划</a></div>'
        + "</div></div>"
    )


def _risk_exposure_panel(data: dict) -> str:
    summary = data.get("paper_summary", {})
    failed = data.get("failed_counts", {})
    exposure = data.get("exposure", {})
    position_ratio = _float(summary.get("position_ratio"))
    lower, upper = TARGET_POSITION_RANGE
    range_status = "低于目标区间，适合继续观察" if position_ratio < lower else "高于目标区间，谨慎加仓" if position_ratio > upper else "在目标区间内"
    single_over = [row for row in data.get("positions", []) if _float(row.get("market_value")) > SINGLE_ETF_LIMIT]
    caution_count = sum(1 for row in data.get("positions", []) if "caution" in str(row.get("risk_tag", "")).lower() or "提醒" in str(row.get("risk_tag", "")))
    dominant = exposure.get("dominant_group", "N/A")
    lines = [
        "<h3>风险摘要</h3>",
        '<div class="grid four">',
        _mini_stat("当前仓位", _pct(position_ratio), range_status),
        _mini_stat("目标区间", "20%-40%", "market_neutral"),
        _mini_stat("单只超限", str(len(single_over)), "上限 20%"),
        _mini_stat("数据 caution", str(caution_count), "持仓内提醒"),
        "</div>",
        "<div style=\"margin-top:14px;\" class=\"risk-banner\">",
        f"<div class=\"risk-title\">主题集中度：{escape(str(dominant))}</div>",
        f"<div>{escape(str(exposure.get('concentration_note', '暂无集中度提示')))}</div>",
        "</div>",
        "<ul>",
        f"<li>quarantine ETF：{failed.get('quarantine', 0)}</li>",
        f"<li>unresolved ETF：{failed.get('unresolved', 0)}</li>",
        "<li>新增 ETF 数据不等于自动进入 trade_pool。</li>",
        "</ul>",
    ]
    return "".join(lines)


def _system_health_panel(data: dict) -> str:
    engine = data.get("paper_trade_engine", {}).get("state", {})
    health = data.get("health_summary", {})
    failed = data.get("failed_counts", {})
    links = data.get("link_health", {})
    nodes = data.get("automation_nodes", [])
    data_update = data.get("data_update_status", {})
    data_sources = data.get("data_sources", {})
    node_errors = sum(1 for node in nodes if str(node.get("status", "")).upper() in {"ERROR", "FAILED"})
    node_waiting = sum(1 for node in nodes if str(node.get("status", "")).upper() == "WAITING")
    cells = [
        _mini_stat("日线更新", str(data_update.get("severity", "N/A")), str(data_update.get("status", "unknown"))),
        _mini_stat("实际数据源", str(data_sources.get("actual_source_used", "N/A")), f"primary {data_sources.get('primary_source', 'jqdata')}"),
        _mini_stat("JQData", str(data_sources.get("jqdata_status", "N/A")), f"fallback {data_sources.get('fallback_triggered', False)}"),
        _mini_stat("BaoStock", str(data_sources.get("baostock_status", "N/A")), str(data_sources.get("fallback_source", "baostock"))),
        _mini_stat("最新数据日", str(data_update.get("latest_local_date", data.get("latest_data_date", "N/A"))), f"请求至 {data_update.get('requested_end', 'N/A')}"),
        _mini_stat("新增行数", str(data_update.get("added_rows", "N/A")), f"calls {data_update.get('estimated_api_calls', 'N/A')}"),
        _mini_stat("数据健康", str(health.get("异常", "0")), "异常 ETF"),
        _mini_stat("数据提醒", str(health.get("提醒", "0")), "caution ETF"),
        _mini_stat("隔离数据", str(failed.get("quarantine", 0)), "不入池"),
        _mini_stat("自动化错误", str(node_errors), f"等待 {node_waiting}"),
        _mini_stat("模拟引擎", str(engine.get("status", "WAITING")), f"buy/sell {engine.get('buy_count', 0)}/{engine.get('sell_count', 0)}"),
        _mini_stat("真实交易", "disabled", "broker_api=false"),
        _mini_stat("链接体检", f"{links.get('valid', 0)}/{links.get('total', 0)}", "本地报告"),
        _mini_stat("更新模式", "static", "Safari 直接打开"),
    ]
    return (
        "<h3>运行质量矩阵</h3>"
        + '<div class="health-meter">'
        + "".join(cells)
        + "</div>"
        + '<div class="risk-banner" style="margin-top:14px;">'
        + '<div class="risk-title">稳定性策略</div>'
        + f"<div>看板为单文件静态 HTML，不依赖 Streamlit 或本地服务；每日报告生成后自动刷新 dashboard_data.json 和 index.html。数据更新诊断：{escape(str(data_update.get('reason', '暂无状态')))}</div>"
        + "</div>"
    )


def _link_health_panel(health: dict) -> str:
    missing = health.get("missing_items", [])
    status = "OK" if not missing else "REVIEW"
    rows = [
        _mini_stat("链接状态", status, f"{health.get('valid', 0)} / {health.get('total', 0)} 可用"),
        _mini_stat("缺失链接", str(len(missing)), "生成时检查"),
    ]
    if missing:
        detail = "<ul>" + "".join(f"<li>{escape(str(item.get('name','')))}：{escape(str(item.get('path','')))}</li>" for item in missing[:8]) + "</ul>"
    else:
        detail = "<div class=\"muted\">核心内置链接均能定位到本地文件。</div>"
    return "<h3>内置链接可用性</h3>" + '<div class="grid two">' + "".join(rows) + "</div>" + detail


def _market_state_panel(market: dict) -> str:
    components = market.get("components", [])
    range_text = f"{_pct(market.get('suggested_total_position_min'))} - {_pct(market.get('suggested_total_position_max'))}"
    rows = [
        _mini_stat("market_state", str(market.get("market_state", "N/A")), "研究代理"),
        _mini_stat("market_score", _score(market.get("market_score")), f"trend {_score(market.get('trend_score'))}"),
        _mini_stat("建议仓位区间", range_text, "不自动改仓"),
        _mini_stat("BUY / 风险", f"{market.get('buy_count', 'N/A')} / {market.get('risk_alert_count', 'N/A')}", "排名与健康代理"),
    ]
    body = []
    for row in components[:6]:
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('symbol','')))}</td>"
            f"<td>{escape(str(row.get('name','')))}</td>"
            f"<td class=\"num\">{_score(row.get('market_score'))}</td>"
            f"<td class=\"num\">{_pct(row.get('ret20'))}</td>"
            f"<td class=\"num\">{_pct(row.get('drawdown60'))}</td>"
            "</tr>"
        )
    table = _table(["symbol", "name", "score", "ret20", "dd60"], body) if body else '<div class="muted">暂无市场状态组件。</div>'
    return (
        "<h3>市场状态</h3>"
        + '<div class="grid four">'
        + "".join(rows)
        + "</div>"
        + "<div style=\"margin-top:12px;\">"
        + table
        + "</div>"
        + '<div class="links" style="margin-top:12px;"><a href="../reports/market_state_report.md">市场状态报告</a></div>'
    )


def _portfolio_exposure_panel(exposure: dict) -> str:
    summary = exposure.get("summary", {})
    warnings = exposure.get("warnings", [])
    buckets = exposure.get("buckets", [])
    rows = [
        _mini_stat("overall_status", str(summary.get("overall_status", "N/A")), "组合暴露"),
        _mini_stat("持仓市值", _money(summary.get("market_value")), f"仓位 {_pct(summary.get('position_ratio'))}"),
        _mini_stat("风险提示", str(len(warnings)), "集中度/数据健康"),
        _mini_stat("暴露桶", str(len(buckets)), "group/type/profile"),
    ]
    warning_html = "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in warnings[:5]) + "</ul>" if warnings else '<div class="muted">暂无组合暴露风险提示。</div>'
    top = []
    for row in buckets[:8]:
        top.append(
            "<tr>"
            f"<td>{escape(str(row.get('dimension','')))}</td>"
            f"<td>{escape(str(row.get('bucket','')))}</td>"
            f"<td class=\"num\">{_money(row.get('market_value'))}</td>"
            f"<td class=\"num\">{_pct(row.get('portfolio_weight'))}</td>"
            "</tr>"
        )
    table = _table(["维度", "桶", "市值", "占持仓"], top) if top else '<div class="muted">暂无暴露汇总。</div>'
    return (
        "<h3>组合暴露研究</h3>"
        + '<div class="grid four">'
        + "".join(rows)
        + "</div>"
        + warning_html
        + table
        + '<div class="links" style="margin-top:12px;"><a href="../reports/portfolio_exposure_report.md">组合暴露报告</a></div>'
    )


def _model_research_panel(model: dict) -> str:
    holding = model.get("holding_period", {})
    exit_rule = model.get("exit_rule", {})
    sweep = model.get("parameter_sweep", {})
    rows = [
        _mini_stat("持有周期行数", str(holding.get("row_count", 0)), str(holding.get("best_note", "N/A"))),
        _mini_stat("退出规则行数", str(exit_rule.get("row_count", 0)), str(exit_rule.get("best_note", "N/A"))),
        _mini_stat("参数扫描行数", str(sweep.get("row_count", 0)), str(sweep.get("best_note", "N/A"))),
        _mini_stat("研究版本", "phase2", "research_only"),
    ]
    links = (
        '<div class="links" style="margin-top:12px;">'
        '<a href="../reports/holding_period_research_report.md">持有周期</a>'
        '<a href="../reports/exit_rule_research_report.md">退出规则</a>'
        '<a href="../reports/parameter_sweep_report.md">参数扫描</a>'
        "</div>"
    )
    return "<h3>模型研究摘要</h3>" + '<div class="grid four">' + "".join(rows) + "</div>" + links


def _research_quality_panel(review: dict) -> str:
    if not review:
        return '<div class="panel">暂无模型研究质量审查。运行 <code>python3 src/model_research_quality_review.py</code> 后刷新。</div>'
    hp = review.get("holding_period", {})
    er = review.get("exit_rule", {})
    ps = review.get("parameter_sweep", {})
    ms = review.get("market_state", {})
    cls = review.get("etf_classification", {})
    exp = review.get("portfolio_exposure", {})
    rec = review.get("integration_recommendations", {})
    cards = [
        _mini_stat("holding_period", str(hp.get("quality", "N/A")), f"rows {hp.get('row_count', 0)}"),
        _mini_stat("exit_rule", str(er.get("quality", "N/A")), f"rows {er.get('row_count', 0)}"),
        _mini_stat("parameter_sweep", str(ps.get("quality", "N/A")), f"rows {ps.get('row_count', 0)}"),
        _mini_stat("market_state", str(ms.get("quality", "N/A")), f"{ms.get('market_state', 'N/A')} / {_score(ms.get('market_score'))}"),
        _mini_stat("ETF 分类", str(cls.get("quality", "N/A")), f"unknown {cls.get('unknown_count', 'N/A')}/{cls.get('row_count', 'N/A')}"),
        _mini_stat("组合暴露", str(exp.get("quality", "N/A")), str(exp.get("overall_status", "N/A"))),
    ]
    immediate = rec.get("immediate", [])
    observe = rec.get("observe", [])
    not_recommended = rec.get("not_recommended", [])
    return (
        '<div class="grid two">'
        + '<div class="panel"><h3>可信度矩阵</h3><div class="grid three">'
        + "".join(cards)
        + "</div></div>"
        + '<div class="panel"><h3>执行层接入建议</h3>'
        + _recommendation_list("可以立即接入", immediate, "ok")
        + _recommendation_list("需要观察后接入", observe, "warn")
        + _recommendation_list("暂不建议接入", not_recommended, "danger")
        + '<div class="links" style="margin-top:12px;"><a href="../reports/model_research_quality_review.md">质量审查报告</a><a href="../reports/execution_layer_integration_plan.md">执行层接入计划</a></div>'
        + "</div></div>"
    )


def _recommendation_list(title: str, items: list, cls: str) -> str:
    if not items:
        return f'<div class="muted">{escape(title)}：暂无</div>'
    html = f'<div style="margin-top:10px;">{_tag(title, cls)}</div><ul>'
    html += "".join(f"<li>{escape(str(item))}</li>" for item in items[:6])
    html += "</ul>"
    return html


def _research_layer_panel(data: dict) -> str:
    positions = data.get("positions", [])
    rows = []
    for row in positions:
        rows.append(
            "<tr>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('etf_type','N/A')))}</td>"
            f"<td>{escape(str(row.get('holding_profile','N/A')))} 天</td>"
            f"<td>{escape(str(row.get('holding_days','N/A')))}</td>"
            f"<td>{_tag(row.get('holding_cycle_status'), _tag_class(row.get('holding_cycle_status')))}</td>"
            f"<td>{escape(str(row.get('exit_sensitivity','N/A')))}</td>"
            f"<td>{_tag(row.get('sentiment_status'), _tag_class(row.get('sentiment_status')))}</td>"
            "</tr>"
        )
    table = _table(["ETF", "类型", "研究周期", "已持有天", "周期状态", "退出敏感度", "情绪状态"], rows) if rows else '<div class="muted">当前无持仓研究层数据。</div>'
    return (
        "<h3>持仓研究周期</h3>"
        + table
        + "<div class=\"risk-banner\" style=\"margin-top:14px;\">"
        + "<div class=\"risk-title\">研究说明</div>"
        + "<div>rank_score 历史趋势当前为 proxy/unavailable；新闻情绪只显示 framework_only/no_data，占位展示，不进入 BUY 主分。</div>"
        + "</div>"
    )


def _universe_quality_panel(review: dict) -> str:
    if not review:
        return "<h3>ETF 池质量审查</h3><div class=\"muted\">暂无 universe quality review 数据。</div>"
    ready_cls = "ok" if review.get("backtest_ready") else "warn"
    stats = [
        _mini_stat("ETF 总数", str(review.get("total_etf", 0)), f"最新 {review.get('latest_data_date', 'N/A')}"),
        _mini_stat("建议 trade", str(review.get("recommended_trade_pool", 0)), "第一版回测候选"),
        _mini_stat("建议 observe", str(review.get("recommended_observe_pool", 0)), "观察/研究，不自动交易"),
        _mini_stat("建议 exclude", str(review.get("recommended_exclude_pool", 0)), "低流动性或分类风险"),
        _mini_stat("低流动性", str(review.get("low_liquidity_count", 0)), "含 low / ultra_low"),
        _mini_stat("unknown 分类", str(review.get("unknown_classification_count", 0)), "回测前优先补分类"),
        _mini_stat("QDII", str(review.get("qdii_count", 0)), "暂不自动交易"),
        _mini_stat("短历史", str(review.get("short_history_count", 0)), "< 120 交易日"),
    ]
    issues = review.get("top_issues", [])
    issue_html = "".join(f"<li>{escape(str(item))}</li>" for item in issues[:6]) or "<li>暂无主要问题</li>"
    return (
        "<h3>ETF 池质量审查与回测准备度</h3>"
        + f"<div style=\"margin-bottom:10px;\">{_tag('BACKTEST_READY' if review.get('backtest_ready') else 'REVIEW_REQUIRED', ready_cls)}</div>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('readiness_summary', '')))}</div>"
        + f"<ul>{issue_html}</ul>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("report_href", "../reports/universe_quality_review.md")))}">池质量报告</a>'
        + f'<a href="{escape(str(review.get("strategy_research_report_href", "../reports/etf_rotation_strategy_research.md")))}">轮动策略调研</a>'
        + f'<a href="{escape(str(review.get("readiness_report_href", "../reports/backtest_readiness_report.md")))}">回测准备报告</a>'
        + "</div>"
    )


def _phase4c_data_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4C 数据源审计</h3><div class=\"muted\">暂无 Phase 4C 数据源审计结果。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("AKShare", str(review.get("akshare_status", "not_checked")), "connectivity"),
        _mini_stat("Provider 设计", "READY" if review.get("data_provider_design_ready") else "MISSING", "staged ingestion"),
        _mini_stat("情报计划", "READY" if review.get("intelligence_data_plan_ready") else "MISSING", "news/special data"),
        _mini_stat("无未来函数", "READY" if review.get("no_lookahead_rules_ready") else "MISSING", "available_date required"),
        _mini_stat("执行接入", "NO", "paper engine unchanged"),
    ]
    return (
        "<h3>Phase 4C 数据源架构审计</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">下一步</div>"
        + f"<div>{escape(str(review.get('recommended_next_step', 'N/A')))}</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("report_href", "../reports/data_source_architecture_audit.md")))}">架构审计</a>'
        + f'<a href="{escape(str(review.get("akshare_report_href", "../reports/akshare_connectivity_check.md")))}">AKShare 诊断</a>'
        + f'<a href="{escape(str(review.get("provider_design_href", "../reports/data_provider_design.md")))}">Provider 设计</a>'
        + f'<a href="{escape(str(review.get("intelligence_plan_href", "../reports/intelligence_data_source_plan.md")))}">情报数据规划</a>'
        + f'<a href="{escape(str(review.get("no_lookahead_href", "../reports/no_lookahead_data_rules.md")))}">无未来函数规则</a>'
        + "</div>"
    )


def _phase4c_tushare_panel(review: dict) -> str:
    if not review:
        return "<h3>Tushare staging</h3><div class=\"muted\">暂无 Tushare staging 结果。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research/staging only"),
        _mini_stat("凭据配置", "YES" if review.get("tushare_token_configured") else "NO", "密钥不展示"),
        _mini_stat("Staging 成功", "YES" if review.get("tushare_staging_success") else "NO", "sample dry-run"),
        _mini_stat("测试样本", str(review.get("sample_symbols_tested", 0)), f"成功 {review.get('sample_symbols_success', 0)} / 失败 {review.get('sample_symbols_failed', 0)}"),
        _mini_stat("BaoStock 对比", "READY" if review.get("baostock_compare_ready") else "NO", "formal data untouched"),
        _mini_stat("正式切换", "NO" if not review.get("formal_source_switched") else "YES", "no formal overwrite"),
        _mini_stat("推荐主源", str(review.get("recommended_daily_source", "baostock")), "current formal"),
        _mini_stat("候选源", str(review.get("candidate_daily_source") or "none"), "future only"),
    ]
    return (
        "<h3>Phase 4C-1 Tushare staging dry-run</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">边界</div>"
        + "<div>research-only / staging-only / no formal overwrite；不接 BUY ranking、paper_trade_engine 或正式回测。</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("staging_report_href", "../reports/tushare_staging_check.md")))}">Staging 报告</a>'
        + f'<a href="{escape(str(review.get("config_report_href", "../reports/tushare_config_check.md")))}">配置检查</a>'
        + f'<a href="{escape(str(review.get("compare_report_href", "../reports/tushare_baostock_compare.md")))}">BaoStock 对比</a>'
        + f'<a href="{escape(str(review.get("provider_status_href", "../reports/data_provider_status.md")))}">Provider 状态</a>'
        + f'<a href="{escape(str(review.get("no_lookahead_href", "../reports/tushare_no_lookahead_check.md")))}">No-lookahead</a>'
        + "</div>"
    )


def _phase4c_alpha_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4C Alpha</h3><div class=\"muted\">暂无 alpha 模型研究结果。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("最佳候选", str(review.get("best_candidate") or "N/A"), str(review.get("candidate_type") or "")),
        _mini_stat("收益", _pct(review.get("best_total_return")), "best total return"),
        _mini_stat("最大回撤", _pct(review.get("best_max_drawdown")), "best drawdown"),
        _mini_stat("跑赢 510300", "YES" if review.get("beat_510300") else "NO", "benchmark"),
        _mini_stat("跑赢 v2", "YES" if review.get("beat_v2_baseline") else "NO", "top10 diversified"),
        _mini_stat("Shadow", "YES" if review.get("ready_for_shadow") else "NO", "research candidate"),
        _mini_stat("执行接入", "NO", "paper engine unchanged"),
    ]
    return (
        "<h3>Phase 4C Alpha / Regime-aware 研究</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">过拟合与边界</div>"
        + f"<div>overfit_guardrails_passed={review.get('overfit_guardrails_passed')}; ready_for_execution=false；所有结果仅用于 research/shadow 判断。</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("attribution_href", "../reports/v2_underperformance_attribution.md")))}">v2 归因</a>'
        + f'<a href="{escape(str(review.get("regime_href", "../reports/regime_aware_model_research.md")))}">Regime-aware</a>'
        + f'<a href="{escape(str(review.get("type_href", "../reports/etf_type_aware_model_research.md")))}">Type-aware</a>'
        + f'<a href="{escape(str(review.get("alpha_href", "../reports/alpha_factor_enhancement_research.md")))}">Alpha 增强</a>'
        + f'<a href="{escape(str(review.get("comparison_href", "../reports/phase4c_alpha_model_comparison.md")))}">综合对比</a>'
        + f'<a href="{escape(str(review.get("decision_href", "../reports/phase4c_alpha_model_decision.md")))}">决策报告</a>'
        + "</div>"
    )


def _persistence_breakout_shadow_panel(review: dict) -> str:
    if not review:
        return "<h3>Persistence Breakout Shadow</h3><div class=\"muted\">暂无 persistence_breakout_v2 shadow 结果。</div>"
    selected_symbols = review.get("selected_symbols") or []
    if isinstance(selected_symbols, str):
        selected_symbols = [selected_symbols]
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "shadow tracking only"),
        _mini_stat("模型", str(review.get("model_name", "persistence_breakout_v2")), "research-only"),
        _mini_stat("主资金假设", str(int(float(review.get("initial_cash_assumption", 20000)))), "不代表真实投入"),
        _mini_stat("Selected", str(review.get("selected_count", 0)), "max 3"),
        _mini_stat("Original 重合", str(review.get("overlap_with_original", 0)), "top3 overlap"),
        _mini_stat("Adjusted 重合", str(review.get("overlap_with_adjusted", 0)), "top3 overlap"),
        _mini_stat("V2 重合", str(review.get("overlap_with_top10_diversified", 0)), "top10 diversified"),
        _mini_stat("执行接入", "NO", "ready_for_execution=false"),
    ]
    return (
        "<h3>persistence_breakout_v2 Shadow Tracking</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + f"<div class=\"warning-line\">Selected symbols: {escape(', '.join(map(str, selected_symbols)) or 'N/A')}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">研究边界</div>"
        + "<div>execution_enabled=false；paper_trade_engine_enabled=false；real_trade_enabled=false；只写 shadow CSV/报告。</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("signal_report_href", "../reports/persistence_breakout_shadow_signal.md")))}">Shadow 信号</a>'
        + f'<a href="{escape(str(review.get("portfolio_report_href", "../reports/persistence_breakout_shadow_portfolio.md")))}">Shadow 组合</a>'
        + f'<a href="{escape(str(review.get("comparison_report_href", "../reports/model_shadow_comparison.md")))}">模型对比</a>'
        + f'<a href="{escape(str(review.get("observation_rules_href", "../reports/persistence_breakout_shadow_observation_rules.md")))}">观察规则</a>'
        + "</div>"
    )


def _missed_opportunity_tracking_panel(review: dict) -> str:
    if not review:
        return "<h3>Missed Opportunity Tracking</h3><div class=\"muted\">暂无 missed opportunity tracking 结果。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "diagnostics only"),
        _mini_stat("候选数", str(review.get("candidate_count", 0)), "filtered high-score"),
        _mini_stat("跟踪日", str(review.get("tracking_days", 0)), "unique signal days"),
        _mini_stat("Missed", str(review.get("missed_opportunity_count", 0)), f"rate {review.get('missed_opportunity_rate', 0)}"),
        _mini_stat("Filter effective", str(review.get("filter_effective_rate", 0)), "10d label"),
        _mini_stat("Risk-on 空仓", str(review.get("risk_on_empty_signal_count", 0)), "selected_count=0"),
        _mini_stat("主要原因", str(review.get("top_missed_filter_reason") or "pending"), "by filter reason"),
        _mini_stat("执行接入", "NO", "ready_for_execution=false"),
    ]
    return (
        "<h3>Missed Opportunity Diagnostics</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">观察结论</div>"
        + f"<div>ready_to_relax_filters={str(review.get('ready_to_relax_filters', False)).lower()}；ready_for_preview=false；ready_for_execution=false。forward return 只作为事后 label，不进入当日模型。</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("tracker_report_href", "../reports/missed_opportunity_tracker.md")))}">Tracker 报告</a>'
        + f'<a href="{escape(str(review.get("by_reason_report_href", "../reports/missed_opportunity_by_filter_reason.md")))}">过滤原因归因</a>'
        + f'<a href="{escape(str(review.get("risk_on_report_href", "../reports/risk_on_empty_signal_analysis.md")))}">Risk-on 空仓</a>'
        + f'<a href="{escape(str(review.get("selected_vs_filtered_href", "../reports/selected_vs_filtered_forward_return.md")))}">Selected vs Filtered</a>'
        + f'<a href="{escape(str(review.get("observation_rules_href", "../reports/missed_opportunity_observation_rules.md")))}">观察规则</a>'
        + "</div>"
    )


def _shadow_observation_weekly_panel(review: dict) -> str:
    if not review:
        return "<h3>Shadow Observation Weekly</h3><div class=\"muted\">暂无 weekly shadow observation。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "weekly observation"),
        _mini_stat("证据等级", str(review.get("evidence_level") or "insufficient"), "forward labels"),
        _mini_stat("空仓日", str(review.get("persistence_empty_signal_days", 0)), "persistence breakout"),
        _mini_stat("Risk-on 空仓", str(review.get("risk_on_empty_days", 0)), "risk_on selected=0"),
        _mini_stat("Missed 候选", str(review.get("missed_opportunity_candidate_count", 0)), "filtered top candidates"),
        _mini_stat("成熟样本", str(review.get("matured_forward_return_count", 0)), "10d matured"),
        _mini_stat("放宽过滤", "NO", "ready_to_relax_filters=false"),
        _mini_stat("执行接入", "NO", "ready_for_execution=false"),
    ]
    return (
        "<h3>Shadow Observation Weekly Review</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">每周结论</div>"
        + f"<div>recommended_action={escape(str(review.get('recommended_action', 'continue_observation')))}；ready_for_preview=false；ready_for_execution=false。</div>"
        + "</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("report_href", "../reports/shadow_observation_weekly.md")))}">Weekly 报告</a>'
        + f'<a href="{escape(str(review.get("csv_href", "../reports/shadow_observation_weekly.csv")))}">Weekly CSV</a>'
        + "</div>"
    )


def _chatgpt_weekly_packet_panel(packet: dict) -> str:
    if not packet:
        return "<h3>ChatGPT / Main 周报分析包</h3><div class=\"muted\">暂无周报分析包。运行 <code>python3 src/chatgpt_weekly_packet.py</code> 后刷新。</div>"
    summary = packet.get("summary", {}) if isinstance(packet.get("summary"), dict) else {}
    safety = packet.get("safety_boundary", {}) if isinstance(packet.get("safety_boundary"), dict) else {}
    missing = packet.get("missing_sources", []) if isinstance(packet.get("missing_sources"), list) else []
    conclusions = summary.get("core_conclusions") or packet.get("core_conclusions") or []
    if not isinstance(conclusions, list):
        conclusions = [str(conclusions)]
    stats = [
        _mini_stat("报告日期", str(packet.get("as_of_date") or summary.get("as_of_date") or "N/A"), "as_of_date"),
        _mini_stat("生成时间", str(packet.get("generated_at") or summary.get("generated_at") or "N/A"), "generated_at"),
        _mini_stat("缺失来源", str(len(missing)), "missing recorded"),
        _mini_stat("执行接入", "NO", "execution_allowed=false"),
    ]
    conclusion_html = "".join(f"<li>{escape(str(item))}</li>" for item in conclusions[:8])
    if not conclusion_html:
        conclusion_html = "<li>暂无核心结论，请重新生成周报分析包。</li>"
    missing_text = "、".join(escape(str(item)) for item in missing[:6]) if missing else "无"
    return (
        "<h3>标准周报分析包</h3>"
        + '<div class="grid four">'
        + "".join(stats)
        + "</div>"
        + "<div class=\"risk-banner\" style=\"margin-top:12px;\">"
        + "<div class=\"risk-title\">使用边界</div>"
        + f"<div>不是交易指令；execution_allowed={str(safety.get('execution_allowed', False)).lower()}；real_trade_enabled={str(safety.get('real_trade_enabled', False)).lower()}；adjusted preview / shadow / profit protection / high_beta / broad base balance 均为观察层。</div>"
        + "</div>"
        + "<ul class=\"mini-list\" style=\"margin-top:12px;\">"
        + conclusion_html
        + "</ul>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">缺失但不致命的数据源：{missing_text}</div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(packet.get("markdown_href", "../reports/chatgpt_weekly_analysis_packet_latest.md")))}">Markdown 分析包</a>'
        + f'<a href="{escape(str(packet.get("json_href", "../reports/chatgpt_weekly_analysis_packet_latest.json")))}">JSON 分析包</a>'
        + "</div>"
    )


def _classification_panel(summary: dict) -> str:
    type_counts = summary.get("type_counts", {})
    pool_counts = summary.get("pool_counts", {})
    items = []
    for key, value in type_counts.items():
        items.append(f'<div class="chart-row"><div class="chart-label">{escape(str(key))}</div><div class="bar-bg"><div class="bar-fill" style="width:{min(int(value) * 2, 100):.2f}%"></div></div><div class="chart-value">{escape(str(value))}</div></div>')
    pool_text = ", ".join(f"{key}: {value}" for key, value in pool_counts.items()) or "N/A"
    return (
        "<h3>ETF 类型分类摘要</h3>"
        + "<div class=\"muted\">用于研究分层和看板提示，不代表自动交易池调整。</div>"
        + "".join(items)
        + f"<div class=\"muted\" style=\"margin-top:12px;\">pool 分布：{escape(pool_text)}</div>"
        + "<div class=\"links\" style=\"margin-top:12px;\">"
        + '<a href="../reports/etf_classification_report.md">类型报告</a>'
        + '<a href="../reports/holding_period_research_report.md">持有周期研究</a>'
        + '<a href="../reports/exit_rule_research_report.md">退出规则研究</a>'
        + '<a href="../reports/parameter_sweep_report.md">参数扫描</a>'
        + '<a href="../reports/news_sentiment_framework.md">情绪框架</a>'
        + "</div>"
    )


def _mini_stat(label: str, value: str, sub: str) -> str:
    return f'<div><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(value)}</div><div class="metric-sub">{escape(sub)}</div></div>'


def _automation_timeline(nodes: list[dict]) -> str:
    if not nodes:
        return '<div class="panel">暂无自动化节点状态。</div>'
    cards = []
    for node in nodes:
        cls = _tag_class(node.get("status"))
        cards.append(
            f"""<div class="node-card">
              <div class="node-time">{escape(str(node.get('time_label','')))}</div>
              <div class="node-name">{escape(str(node.get('title','')))}</div>
              {_tag(node.get('status'), cls)}
              <div class="muted" style="margin-top:8px;">结论：{escape(str(node.get('conclusion','N/A')))}</div>
              <div class="muted">更新：{escape(str(node.get('generated_at','N/A')))}</div>
              <a class="node-link" href="{escape(str(node.get('report_href','#')))}">查看报告</a>
            </div>"""
        )
    return '<div class="timeline">' + "".join(cards) + "</div>"


def _review_panel(review: dict) -> str:
    items = review.get("items", [])
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('name','')))}</td>"
            f"<td>{_tag(item.get('status'), _tag_class(item.get('status')))}</td>"
            f"<td>{escape(str(item.get('updated_at','')))}</td>"
            f"<td><a class=\"node-link\" href=\"{escape(str(item.get('href','#')))}\">打开</a></td>"
            "</tr>"
        )
    return "<h3>最近报告</h3>" + _table(["报告", "状态", "更新时间", "链接"], rows)


def _allocation_chart(data: dict) -> str:
    summary = data.get("paper_summary", {})
    cash = max(_float(summary.get("cash")), 0.0)
    market_value = max(_float(summary.get("market_value")), 0.0)
    total = cash + market_value
    if total <= 0:
        return '<div class="chart-card"><h3>资产分布</h3><div class="muted">暂无资产数据。</div></div>'
    position_width = market_value / total * 260
    cash_width = cash / total * 260
    return f"""<div class="chart-card">
      <h3>资产分布</h3>
      <svg viewBox="0 0 320 160" role="img">
        <rect x="30" y="38" width="260" height="30" rx="8" fill="#eef2f7"/>
        <rect x="30" y="38" width="{position_width:.2f}" height="30" rx="8" fill="#1455d9"/>
        <rect x="{30 + position_width:.2f}" y="38" width="{cash_width:.2f}" height="30" rx="8" fill="#667085"/>
        <text x="30" y="98" fill="#344054" font-size="13">持仓 {_money(market_value)} / {_pct(market_value / total)}</text>
        <text x="30" y="122" fill="#344054" font-size="13">现金 {_money(cash)} / {_pct(cash / total)}</text>
      </svg>
    </div>"""


def _position_chart(rows: list[dict]) -> str:
    if not rows:
        return '<div class="chart-card"><h3>持仓规模</h3><div class="muted">当前无持仓。</div></div>'
    max_value = max(_float(row.get("market_value")) for row in rows) or 1
    items = []
    for row in sorted(rows, key=lambda item: _float(item.get("market_value")), reverse=True):
        value = _float(row.get("market_value"))
        width = min(value / max_value * 100, 100)
        items.append(f'<div class="chart-row"><div class="chart-label">{escape(str(row.get("symbol","")))}</div><div class="bar-bg"><div class="bar-fill" style="width:{width:.2f}%"></div></div><div class="chart-value">{_money(value)}</div></div>')
    return '<div class="chart-card"><h3>持仓规模</h3>' + "".join(items) + "</div>"


def _ranking_chart(rows: list[dict]) -> str:
    if not rows:
        return '<div class="chart-card"><h3>BUY ranking 强度</h3><div class="muted">暂无排名。</div></div>'
    items = []
    for row in rows[:8]:
        score = _float(row.get("rank_score"))
        color = "#d92d20" if score >= 85 else "#1455d9" if score >= 70 else "#b7791f"
        items.append(f'<div class="chart-row"><div class="chart-label">{escape(str(row.get("symbol","")))}</div><div class="bar-bg"><div class="bar-fill" style="width:{min(score,100):.2f}%;background:{color};"></div></div><div class="chart-value">{score:.1f}</div></div>')
    return '<div class="chart-card"><h3>BUY ranking 强度</h3>' + "".join(items) + "</div>"


def _exposure_chart(exposure: dict, compact: bool = False) -> str:
    groups = exposure.get("groups", [])
    if not groups:
        return '<div class="chart-card"><h3>group 暴露</h3><div class="muted">暂无持仓暴露。</div></div>'
    items = []
    max_ratio = max(_float(row.get("ratio")) for row in groups) or 1
    for row in groups:
        ratio = _float(row.get("ratio"))
        width = min(ratio / max_ratio * 100, 100)
        items.append(f'<div class="chart-row"><div class="chart-label">{escape(str(row.get("group","")))}</div><div class="bar-bg"><div class="bar-fill" style="width:{width:.2f}%;background:#1455d9;"></div></div><div class="chart-value">{_pct(ratio)}</div></div>')
    title = "group 暴露" if compact else "持仓行业/主题暴露"
    return f'<div class="chart-card"><h3>{title}</h3>' + "".join(items) + f'<div class="muted">{escape(str(exposure.get("concentration_note","")))}</div></div>'


def _trade_timeline(rows: list[dict]) -> str:
    if not rows:
        return '<div class="muted">暂无模拟交易。</div>'
    cards = []
    for row in rows[-4:][::-1]:
        cards.append(
            f"""<div class="node-card" style="min-height:auto;margin-bottom:8px;">
              <div class="node-time">{escape(str(row.get('trade_date') or row.get('date') or ''))}</div>
              <div class="node-name">{escape(str(row.get('symbol','')))} {escape(str(row.get('action','')))}</div>
              <div class="muted">{escape(str(row.get('name','')))} · {_number(row.get('price'))} · {_money(row.get('amount'))} · {escape(str(row.get('execution_price_type','')))}</div>
            </div>"""
        )
    return "".join(cards)


def _trades_table(rows: list[dict]) -> str:
    if not rows:
        return ""
    body = []
    for row in rows[-20:]:
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('trade_date') or row.get('date') or ''))}</td>"
            f"<td>{escape(str(row.get('symbol','')))}</td>"
            f"<td>{escape(str(row.get('name','')))}</td>"
            f"<td>{escape(str(row.get('action','')))}</td>"
            f"<td class=\"num\">{_number(row.get('price'))}</td>"
            f"<td class=\"num\">{_number(row.get('quantity'))}</td>"
            f"<td class=\"num\">{_money(row.get('amount'))}</td>"
            f"<td>{escape(str(row.get('execution_price_type','')))}</td>"
            "</tr>"
        )
    return _table(["日期", "ETF", "名称", "动作", "价格", "数量", "金额", "价格类型"], body)


def _files_panel() -> str:
    return """<ul class="file-list">
      <li><code>dashboard/index.html</code>：静态看板</li>
      <li><code>reports/dashboard_data.json</code>：看板快照</li>
      <li><code>data/paper_positions.csv</code>：模拟持仓</li>
      <li><code>data/paper_trades.csv</code>：模拟流水</li>
      <li><code>data/etf_type_classification.csv</code>：ETF 类型分层 sidecar</li>
      <li><code>data/etf_theme_keywords.csv</code>：主题关键词库</li>
      <li><code>reports/latest_paper_portfolio.md</code>：模拟盘报告</li>
      <li><code>reports/automation_four_node_sync_report.md</code>：自动化同步报告</li>
      <li><code>reports/next_stage_strategy_optimization_report.md</code>：下一阶段策略研究总报告</li>
      <li><code>reports/sell_signal_review.md</code>：卖出复核报告</li>
      <li><code>reports/paper_trade_plan.md</code>：模拟交易计划</li>
      <li><code>reports/paper_trade_engine_report.md</code>：模拟交易引擎报告</li>
      <li><code>data/paper_trade_engine_state.json</code>：模拟交易引擎状态</li>
    </ul>"""


def _link_center(rows: list[dict]) -> str:
    if not rows:
        return '<div class="panel">暂无链接。</div>'
    cards = []
    for row in rows:
        cls = "ok" if row.get("exists") else "warn"
        href = escape(str(row.get("href", "#")))
        cards.append(
            f"""<a class="link-card" href="{href}">
              <div class="link-card-title">{escape(str(row.get('name','')))}</div>
              <div class="link-card-meta">{escape(str(row.get('category','')))} · {_tag('OK' if row.get('exists') else 'MISSING', cls)}</div>
              <div class="link-card-meta"><code>{escape(str(row.get('path','')))}</code></div>
            </a>"""
        )
    return '<div class="link-grid">' + "".join(cards) + "</div>"


def _source_reference_panel(rows: list[dict]) -> str:
    if not rows:
        return '<div class="panel">暂无设计参考。</div>'
    cards = []
    for row in rows:
        cards.append(
            f"""<div class="source-card">
              <div class="eyebrow" style="color:#1455d9;">{escape(str(row.get('type','reference')))}</div>
              <h3>{escape(str(row.get('name','')))}</h3>
              <div class="muted">{escape(str(row.get('lesson','')))}</div>
              <div style="margin-top:10px;"><a href="{escape(str(row.get('url','#')))}">来源链接</a></div>
            </div>"""
        )
    return '<div class="source-grid">' + "".join(cards) + "</div>"


def _safety_panel(data: dict) -> str:
    safety = data.get("safety", {})
    rows = [
        ("权限", safety.get("permission")),
        ("券商 API", safety.get("broker_api")),
        ("真实下单", safety.get("real_order")),
        ("真实账户", safety.get("real_account")),
        ("保存密钥", safety.get("credentials_saved")),
        ("修改策略规则", safety.get("strategy_rule_change")),
    ]
    return "<ul class=\"file-list\">" + "".join(f"<li>{escape(str(k))}：{escape(str(v))}</li>" for k, v in rows) + "</ul>"


def _table(headers: list[str], body_rows: list[str]) -> str:
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    return f'<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def _score_bar(label: str, value: object, max_score: float) -> str:
    if value in ("", None, "N/A"):
        return '<span class="muted">N/A</span>'
    numeric = _float(value)
    width = min(max(numeric / max_score * 100, 0), 100) if max_score else 0
    return f'<div class="score-cell"><div class="score-text"><span>{escape(label)}</span><span>{numeric:.1f}</span></div><div class="bar-bg"><div class="bar-fill" style="width:{width:.2f}%"></div></div></div>'


def _tag(text: object, cls: str = "") -> str:
    return f'<span class="tag {escape(cls)}">{escape(str(text or "N/A"))}</span>'


def _tag_class(value: object) -> str:
    text = str(value or "").upper()
    if any(token in text for token in ["ERROR", "INVALID", "SELL", "REDUCE", "DANGER", "RISK_REDUCE"]):
        return "danger"
    if any(token in text for token in ["CAUTION", "WAITING", "WATCH", "REVIEW", "WEAKENING", "提醒"]):
        return "warn"
    if any(token in text for token in ["OK", "NORMAL", "VALID", "HOLD"]):
        return "ok"
    return "blue"


def _sell_status_class(value: object) -> str:
    text = str(value or "").upper()
    if text == "HOLD":
        return "ok"
    if text == "WATCH":
        return "blue"
    if text == "REVIEW":
        return "warn"
    if text in {"REDUCE", "SELL"}:
        return "danger"
    return _tag_class(value)


def _review_state_class(value: object) -> str:
    text = str(value or "").upper()
    if text in {"SELL", "REDUCE"}:
        return "danger"
    if text == "REDUCE_CANDIDATE":
        return "warn"
    if text in {"REVIEW_2", "REVIEW"}:
        return "warn"
    if text == "REVIEW_1":
        return "blue"
    if text == "HOLD":
        return "ok"
    return _tag_class(value)


def _profit_state_class(value: object) -> str:
    text = str(value or "").upper()
    if text == "PROFIT_LOCK_CANDIDATE":
        return "warn"
    if text == "PROFIT_PROTECTION_REVIEW":
        return "warn"
    if text == "PROFIT_WATCH":
        return "blue"
    if text == "NO_PROFIT":
        return "ok"
    return _tag_class(value)


def _high_beta_state_class(value: object) -> str:
    text = str(value or "").upper()
    if text == "HB_ELEVATED":
        return "danger"
    if text == "HB_CAUTION":
        return "warn"
    if text == "HB_WATCH":
        return "warn"
    if text == "HB_NORMAL":
        return "ok"
    return _tag_class(value)


def _read_buy_ranking() -> list[dict]:
    rows = _read_markdown_table(REPORT_DIR / "buy_signal_ranking.md", "Top BUY Ranking")
    result = []
    for row in rows:
        result.append(
            {
                "rank": row.get("rank", ""),
                "symbol": row.get("code", row.get("ETF 代码", "")),
                "name": row.get("name", row.get("ETF 名称", "")),
                "group": row.get("group", "N/A") or "N/A",
                "mid_trend_signal": row.get("mid", row.get("mid_trend_signal", "N/A")) or "N/A",
                "short_swing_signal": row.get("short", row.get("short_swing_signal", "N/A")) or "N/A",
                "rank_score": _maybe_float(row.get("rank_score")),
                "mid_trend_score": _maybe_float(row.get("mid_trend")),
                "short_momentum_score": _maybe_float(row.get("short_momentum")),
                "liquidity_score": _maybe_float(row.get("liquidity")),
                "risk_score": _maybe_float(row.get("risk")),
                "resonance_score": _maybe_float(row.get("resonance")),
                "data_quality_score": _maybe_float(row.get("data_quality")),
                "resonance_flag": row.get("双周期共振", "N/A") or "N/A",
                "risk_note": row.get("风险提示", "") or "无",
                "candidate_action": "candidate" if row.get("进入模拟买入候选") == "是" else "watch",
            }
        )
    return result


def _enrich_positions(
    positions: pd.DataFrame,
    meta: dict[str, dict],
    ranking: list[dict],
    health: dict[str, dict],
    sell_review: list[dict] | None = None,
    position_review: list[dict] | None = None,
    profit_protection: list[dict] | None = None,
    high_beta_risk: list[dict] | None = None,
) -> list[dict]:
    ranking_map = {str(row.get("symbol")): row for row in ranking}
    review_map = {str(row.get("symbol")): row for row in (sell_review or [])}
    layer_map = {str(row.get("symbol")): row for row in (position_review or [])}
    profit_map = {str(row.get("symbol")): row for row in (profit_protection or [])}
    high_beta_map = {str(row.get("symbol")): row for row in (high_beta_risk or [])}
    result = []
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", "")).strip()
        rank = ranking_map.get(symbol, {})
        meta_row = meta.get(symbol, {})
        health_row = health.get(symbol, {})
        review_row = review_map.get(symbol, {})
        layer_row = layer_map.get(symbol, {})
        profit_row = profit_map.get(symbol, {})
        high_beta_row = high_beta_map.get(symbol, {})
        current_price = _float(item.get("last_price"), _float(item.get("current_price"), _float(item.get("entry_price"))))
        stop_loss = _float(item.get("stop_loss_price"), _float(item.get("stop_loss")))
        market_value = _float(item.get("market_value"), current_price * _float(item.get("quantity")))
        total_cost = _float(item.get("total_cost"), _float(item.get("cost")))
        pnl = _float(item.get("unrealized_pnl"), market_value - total_cost)
        stop_distance = (current_price - stop_loss) / current_price if current_price and stop_loss else None
        mid = rank.get("mid_trend_signal", _parse_reason_signal(item.get("reason"), "mid_trend") or "N/A")
        short = rank.get("short_swing_signal", _parse_reason_signal(item.get("reason"), "short_swing") or "N/A")
        health_status = str(health_row.get("status", "") or "")
        health_note = str(health_row.get("note", "") or "")
        signal_status = _signal_status(mid, short, health_status, current_price, stop_loss)
        risk_tag = _risk_tag(health_status, health_note, market_value, current_price, stop_loss)
        action = _action_suggestion(signal_status, risk_tag)
        min_days = _int(meta_row.get("default_holding_min_days"))
        max_days = _int(meta_row.get("default_holding_max_days"))
        holding_days = _int(item.get("holding_days"))
        holding_cycle_status = _holding_cycle_status(holding_days, min_days, max_days)
        short_weakening = _short_swing_weakening(item.get("reason"), short)
        sentiment_status = _sentiment_status(meta_row)
        result.append(
            {
                **item,
                "symbol": symbol,
                "name": item.get("name") or meta_row.get("name") or symbol,
                "group": meta_row.get("group", rank.get("group", "N/A")) or "N/A",
                "etf_type": meta_row.get("etf_type", "N/A") or "N/A",
                "holding_profile": meta_row.get("holding_profile", "N/A") or "N/A",
                "default_holding_min_days": min_days,
                "default_holding_max_days": max_days,
                "holding_cycle_status": holding_cycle_status,
                "exit_sensitivity": meta_row.get("exit_sensitivity", "N/A") or "N/A",
                "news_required": meta_row.get("news_required", "N/A") or "N/A",
                "sentiment_filter_required": meta_row.get("sentiment_filter_required", "N/A") or "N/A",
                "sentiment_status": sentiment_status,
                "rank_score_trend": "unavailable",
                "short_swing_weakening": short_weakening,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": _float(item.get("unrealized_pnl_pct"), _float(item.get("unrealized_return"))),
                "position_ratio": market_value / INITIAL_CASH,
                "stop_loss": stop_loss,
                "stop_distance_pct": stop_distance,
                "avg_cost": _float(item.get("avg_cost"), _float(item.get("entry_price"))),
                "total_cost": total_cost,
                "commission_paid": _float(item.get("commission_paid")),
                "max_holding_days": item.get("max_holding_days", ""),
                "sell_review_status": review_row.get("sell_review_status") or item.get("sell_review_status", "N/A"),
                "review_state": layer_row.get("review_state") or review_row.get("sell_review_status") or item.get("sell_review_status", "N/A"),
                "review_state_cn": layer_row.get("review_state_cn", ""),
                "review_level": layer_row.get("review_level", ""),
                "is_reduce_candidate": layer_row.get("is_reduce_candidate", False),
                "review_reasons": layer_row.get("review_reasons", ""),
                "recommended_review_action": layer_row.get("recommended_review_action", ""),
                "execution_allowed": layer_row.get("execution_allowed", False),
                "profit_protection_state": profit_row.get("profit_protection_state", ""),
                "profit_protection_state_cn": profit_row.get("profit_protection_state_cn", ""),
                "profit_protection_level": profit_row.get("profit_protection_level", ""),
                "profit_protection_reasons": profit_row.get("profit_protection_reasons", ""),
                "profit_recommended_review_action": profit_row.get("recommended_review_action", ""),
                "peak_unrealized_pnl": profit_row.get("peak_unrealized_pnl", ""),
                "peak_unrealized_pnl_pct": profit_row.get("peak_unrealized_pnl_pct", ""),
                "peak_profit_date": profit_row.get("peak_date", ""),
                "drawdown_from_profit_peak": profit_row.get("drawdown_from_profit_peak", ""),
                "drawdown_from_profit_peak_pct": profit_row.get("drawdown_from_profit_peak_pct", ""),
                "high_beta_risk_state": high_beta_row.get("high_beta_risk_state", ""),
                "high_beta_risk_level": high_beta_row.get("high_beta_risk_level", ""),
                "high_beta_risk_reasons": high_beta_row.get("high_beta_risk_reasons", ""),
                "high_beta_recommended_review_action": high_beta_row.get("recommended_review_action", ""),
                "high_beta_execution_allowed": high_beta_row.get("execution_allowed", False),
                "high_beta_recent_return_5d": high_beta_row.get("recent_return_5d", ""),
                "high_beta_recent_return_10d": high_beta_row.get("recent_return_10d", ""),
                "high_beta_recent_volatility_10d": high_beta_row.get("recent_volatility_10d", ""),
                "high_beta_recent_drawdown_10d": high_beta_row.get("recent_drawdown_10d", ""),
                "data_health_status": review_row.get("data_health_status") or item.get("data_health_status", health_status or "N/A"),
                "protection_period": review_row.get("protection_period") or item.get("protection_period", "no"),
                "buy_signal": _buy_signal_from_reason(item.get("reason"), mid, short),
                "current_signal": f"{mid}/{short}",
                "signal_status": signal_status,
                "risk_tag": risk_tag,
                "health_status": health_status or "N/A",
                "health_note": health_note,
                "action_suggestion": action,
                "buy_reason_short": _short_reason(item.get("reason")),
                "research_note": _research_note(meta_row, holding_cycle_status, short_weakening, risk_tag),
            }
        )
    return result


def _build_meta_map(watchlist: pd.DataFrame, candidates: pd.DataFrame, classification: pd.DataFrame) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for df in [watchlist, candidates]:
        if df.empty or "code" not in df.columns:
            continue
        for row in df.to_dict(orient="records"):
            code = str(row.get("code", "")).strip()
            if not code:
                continue
            meta.setdefault(code, {})
            meta[code].update({"name": row.get("name", meta[code].get("name", code)), "group": row.get("group", meta[code].get("group", "N/A")), "pool": row.get("pool", row.get("role", meta[code].get("pool", "")))})
    if not classification.empty and "code" in classification.columns:
        for row in classification.to_dict(orient="records"):
            code = str(row.get("code", "")).strip()
            if not code:
                continue
            meta.setdefault(code, {})
            for key in [
                "name",
                "group",
                "pool",
                "etf_type",
                "holding_profile",
                "default_holding_min_days",
                "default_holding_max_days",
                "exit_sensitivity",
                "news_required",
                "sentiment_filter_required",
                "qdii_check_required",
                "liquidity_check_required",
                "classification_reason",
            ]:
                value = row.get(key)
                if value not in ("", None):
                    meta[code][key] = value
    return meta


def _classification_summary(classification: pd.DataFrame, positions: list[dict]) -> dict:
    if classification.empty:
        return {"total": 0, "type_counts": {}, "pool_counts": {}, "held_types": {}}
    type_counts = classification["etf_type"].value_counts().to_dict() if "etf_type" in classification.columns else {}
    pool_counts = classification["pool"].value_counts().to_dict() if "pool" in classification.columns else {}
    held_types: dict[str, int] = {}
    for row in positions:
        key = str(row.get("etf_type", "unknown"))
        held_types[key] = held_types.get(key, 0) + 1
    return {"total": int(len(classification)), "type_counts": type_counts, "pool_counts": pool_counts, "held_types": held_types}


def _paper_summary(positions: list[dict], trades: pd.DataFrame) -> dict:
    market_value = sum(_float(row.get("market_value")) for row in positions)
    cost = sum(_float(row.get("cost")) for row in positions)
    cash = _latest_trade_value(trades, "simulated_cash", INITIAL_CASH - cost)
    total_equity = _latest_trade_value(trades, "total_equity", cash + market_value)
    total_pnl = total_equity - INITIAL_CASH
    return {
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "total_equity": round(total_equity, 2),
        "total_pnl": round(total_pnl, 2),
        "realized_pnl": 0.0,
        "unrealized_pnl": round(market_value - cost, 2),
        "position_count": len(positions),
        "trade_count": len(trades),
        "position_ratio": market_value / INITIAL_CASH if INITIAL_CASH else 0,
        "cash_ratio": cash / total_equity if total_equity else 0,
    }


def _merge_performance_summary(summary: dict, performance: dict, exposure: dict) -> dict:
    if not isinstance(performance, dict) or not performance:
        return summary
    merged = dict(summary)
    cash = _float(performance.get("current_cash"), merged.get("cash", 0.0))
    market_value = _float(performance.get("current_position_value"), merged.get("market_value", 0.0))
    total_equity = _float(performance.get("current_total_equity"), cash + market_value)
    initial_cash = _float(performance.get("initial_cash"), INITIAL_CASH)
    merged.update(
        {
            "cash": round(cash, 2),
            "current_cash": round(cash, 2),
            "market_value": round(market_value, 2),
            "position_value": round(market_value, 2),
            "current_position_value": round(market_value, 2),
            "total_equity": round(total_equity, 2),
            "current_total_equity": round(total_equity, 2),
            "total_pnl": round(_float(performance.get("total_pnl_amount"), total_equity - initial_cash), 2),
            "realized_pnl": round(_float(performance.get("realized_pnl")), 2),
            "unrealized_pnl": round(_float(performance.get("unrealized_pnl"), merged.get("unrealized_pnl", 0.0)), 2),
            "position_ratio": market_value / initial_cash if initial_cash else 0.0,
            "cash_ratio": cash / total_equity if total_equity else 0.0,
            "valuation_as_of_date": performance.get("valuation_as_of_date") or performance.get("latest_data_date"),
            "valuation_source": performance.get("valuation_source", "paper_positions + etf_daily latest close"),
            "valuation_price_warning_count": performance.get("valuation_price_warning_count", 0),
        }
    )
    exposure_summary = exposure.get("summary", {}) if isinstance(exposure, dict) else {}
    if exposure_summary:
        merged["portfolio_exposure_market_value"] = _float(exposure_summary.get("market_value"))
    return merged


def _paper_performance_snapshot() -> dict:
    summary = _read_json(REPORT_DIR / "paper_performance_summary.json")
    if not summary:
        summary = {"status": "missing", "reason": "paper_performance_summary.json not generated"}
    daily = _read_csv(DATA_DIR / "paper_equity_curve.csv")
    if daily.empty:
        daily = _read_csv(REPORT_DIR / "paper_performance_daily.csv")
    original_rows = len(daily)
    backfilled = _read_csv(DATA_DIR / "paper_equity_curve_backfilled.csv")
    uses_backfilled = not backfilled.empty and len(backfilled) >= len(daily)
    if uses_backfilled:
        daily = backfilled
    trade_pnl = _read_csv(REPORT_DIR / "paper_trade_pnl.csv")
    return {
        "summary": summary,
        "equity_curve": daily.to_dict(orient="records"),
        "equity_curve_source": "backfilled_estimated" if uses_backfilled else "original",
        "original_equity_curve_rows": original_rows,
        "backfilled_equity_curve_rows": len(backfilled),
        "trade_pnl": trade_pnl.to_dict(orient="records"),
    }


def _valuation_positions_snapshot() -> pd.DataFrame:
    if load_latest_position_valuation is None:
        return pd.DataFrame()
    try:
        valuation = load_latest_position_valuation()
        positions = valuation.get("positions", pd.DataFrame())
    except Exception:
        return pd.DataFrame()
    return positions if isinstance(positions, pd.DataFrame) else pd.DataFrame()


def _valuation_consistency_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "valuation_consistency_audit.json")
    if payload:
        return payload
    if load_latest_position_valuation is None:
        return {"status": "missing", "reason": "valuation module unavailable"}
    try:
        valuation = load_latest_position_valuation()
        summary = valuation.get("summary", {})
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}
    return {
        "status": summary.get("status", "unknown"),
        "official_valuation_basis": summary.get("valuation_source", "paper_positions + etf_daily latest close"),
        "unified_latest_close_market_value": summary.get("total_market_value", 0.0),
        "as_of_date": summary.get("as_of_date", ""),
        "price_warning_count": summary.get("price_warning_count", 0),
    }


def _paper_equity_backfill_snapshot(paper_performance: dict) -> dict:
    original = _read_csv(DATA_DIR / "paper_equity_curve.csv")
    backfilled = _read_csv(DATA_DIR / "paper_equity_curve_backfilled.csv")
    quality = {}
    if not backfilled.empty and "quality_flag" in backfilled.columns:
        quality = {str(k): int(v) for k, v in backfilled["quality_flag"].value_counts().to_dict().items()}
    uses_backfilled = bool(not backfilled.empty and len(backfilled) >= len(original))
    summary = paper_performance.get("summary", {}) if isinstance(paper_performance, dict) else {}
    return {
        "status": "active" if not backfilled.empty else "missing",
        "backfilled_records": int(len(backfilled)),
        "original_records": int(len(original)),
        "start_date": str(backfilled["date"].iloc[0]) if not backfilled.empty and "date" in backfilled.columns else "",
        "end_date": str(backfilled["date"].iloc[-1]) if not backfilled.empty and "date" in backfilled.columns else "",
        "initial_cash": float(summary.get("initial_cash") or PAPER_INITIAL_CASH),
        "quality": quality,
        "estimated": True,
        "app_uses_backfilled_curve": uses_backfilled,
        "display_note": "历史回填数据（估算）：由交易流水和 ETF 历史收盘价重建。" if uses_backfilled else "使用原始权益曲线。",
        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") if not backfilled.empty else "",
    }


def _app_shortcut_snapshot() -> dict:
    app_bundle = PROJECT_ROOT / "dist" / "量化研究控制台.app"
    command_launcher = PROJECT_ROOT / "打开量化研究控制台.command"
    legacy_launcher = PROJECT_ROOT / "A-Share Swing App.command"
    svg = PROJECT_ROOT / "assets" / "app_icon.svg"
    png = PROJECT_ROOT / "assets" / "app_icon.png"
    return {
        "status": "active" if app_bundle.exists() else "fallback_command",
        "app_bundle": "dist/量化研究控制台.app" if app_bundle.exists() else "unavailable",
        "command_launcher": "打开量化研究控制台.command",
        "legacy_launcher": "A-Share Swing App.command",
        "command_launcher_exists": command_launcher.exists(),
        "legacy_launcher_exists": legacy_launcher.exists(),
        "app_icon_svg": "assets/app_icon.svg" if svg.exists() else "unavailable",
        "app_icon_png": "assets/app_icon.png" if png.exists() else "unavailable",
        "log_path": "logs/app_server.log",
        "version": f"v{APP_VERSION}",
        "safe_note": "本地启动包装器；不包含账号密码；不接券商；不真实交易。",
    }


def _trade_review_snapshot() -> dict:
    summary = _read_json(REPORT_DIR / "trade_review_summary.json")
    if not summary:
        summary = {"status": "missing", "reason": "trade_review_summary.json not generated"}
    details = _read_csv(REPORT_DIR / "trade_review_details.csv")
    open_positions = _read_csv(REPORT_DIR / "trade_review_open_positions.csv")
    return {
        "summary": summary,
        "details": details.to_dict(orient="records"),
        "open_positions": open_positions.to_dict(orient="records"),
    }


def _group_exposure(positions: list[dict]) -> dict:
    total = sum(_float(row.get("market_value")) for row in positions)
    groups = {}
    for row in positions:
        group = str(row.get("group") or "其他")
        groups[group] = groups.get(group, 0.0) + _float(row.get("market_value"))
    rows = [{"group": group, "market_value": value, "ratio": value / total if total else 0.0} for group, value in sorted(groups.items(), key=lambda item: item[1], reverse=True)]
    dominant = rows[0]["group"] if rows else "N/A"
    dominant_ratio = rows[0]["ratio"] if rows else 0.0
    note = "当前组合偏金融/周期；继续观察行业集中度。" if any(row["group"] in ["金融地产", "周期资源"] and row["ratio"] >= 0.35 for row in rows) else "当前未发现单一主题过度集中。"
    if dominant_ratio >= 0.60:
        note = f"{dominant} 占比超过 60%，主题集中度较高，后续不宜继续同方向加仓。"
    return {"groups": rows, "dominant_group": dominant, "dominant_ratio": dominant_ratio, "concentration_note": note}


def _risk_alerts(positions: list[dict], failed_counts: dict) -> list[dict]:
    alerts = []
    for row in positions:
        risk_tag = str(row.get("risk_tag", ""))
        if risk_tag not in ("NORMAL", "N/A", ""):
            action = "禁止加仓，继续观察；若连续异常则触发复核或 RISK_REDUCE。"
            if "STOP" in risk_tag:
                action = "触发人工复核，必要时按模拟规则 REDUCE。"
            alerts.append({"symbol": row.get("symbol"), "name": row.get("name"), "reason": risk_tag, "action": action, "severity": "danger" if "STOP" in risk_tag else "warn"})
    if failed_counts.get("quarantine", 0):
        alerts.append({"symbol": "DATA", "name": "staging", "reason": f"quarantine ETF {failed_counts.get('quarantine')}", "action": "不纳入交易池或模拟候选。", "severity": "warn"})
    return alerts


def _console_status(summary: dict, alerts: list[dict], nodes: list[dict], health_summary: dict, data_update_status: dict) -> dict:
    severe = any(item.get("severity") == "danger" for item in alerts)
    waiting_data = health_summary.get("缺失") not in ("", "0", 0, None)
    data_update_severity = str(data_update_status.get("severity", "")).upper()
    midday = next((node for node in nodes if node.get("node") == "midday_check"), {})
    if data_update_severity == "ERROR":
        conclusion = "DATA_UPDATE_ERROR"
        reason = str(data_update_status.get("reason", "ETF 日线更新失败或未完成，需要复核数据源。"))
    elif severe:
        conclusion = "RISK_REDUCE"
        reason = "存在止损或严重风险触发，需要人工复核减仓。"
    elif data_update_severity == "CAUTION":
        conclusion = "DATA_UPDATE_CAUTION"
        reason = str(data_update_status.get("reason", "ETF 日线更新存在延迟或无新增，信号依赖本地缓存数据。"))
    elif alerts:
        conclusion = "REVIEW_REQUIRED"
        reason = "存在 data_health caution 或组合风险提醒，禁止加仓，继续观察。"
    elif midday.get("conclusion") == "EXECUTE_AFTERNOON":
        conclusion = "EXECUTE_AFTERNOON"
        reason = "午盘节点提示下午需要执行模拟计划。"
    elif waiting_data:
        conclusion = "DATA_PROXY"
        reason = "存在数据缺失，结论依赖本地已有 close proxy。"
    elif summary.get("position_count", 0):
        conclusion = "HOLD_PLAN"
        reason = "当前持仓无风险触发，按模拟计划持有观察。"
    else:
        conclusion = "WATCH_ONLY"
        reason = "当前无持仓或无合格动作。"
    status = "ERROR" if severe or data_update_severity == "ERROR" else "CAUTION" if alerts or waiting_data or data_update_severity == "CAUTION" else "NORMAL"
    return {
        "today_conclusion": conclusion,
        "decision_reason": reason,
        "system_status": status,
        "system_badge_class": "danger" if status == "ERROR" else "warn" if status == "CAUTION" else "ok",
        "risk_summary": f"{len(alerts)} 项需复核" if alerts else "无风险触发",
        "data_update_status": data_update_status.get("status", "unknown"),
    }


def _automation_nodes(data_update_status: dict | None = None) -> list[dict]:
    now = pd.Timestamp.now()
    specs = [
        ("catchup_check", "login", "开机/登录补偿", "reports/catchup_scheduler_status.md", ""),
        ("open_check", "09:40", "开盘风险观察", "reports/open_check.md", "open_check.json"),
        ("midday_check", "12:40", "午盘模拟执行检查", "reports/midday_check.md", "midday_check.json"),
        ("afternoon_open_check", "13:10", "下午开盘复核", "reports/afternoon_open_check.md", "afternoon_open_check.json"),
        ("paper_trade_engine", "15:25", "模拟交易引擎", "reports/paper_trade_engine_report.md", ""),
        ("data_update", "15:30", "ETF 日线更新", "reports/data_download_report.md", "data_update_status.json"),
        ("daily_close", "15:30", "收盘更新", "reports/latest_brief.md", ""),
        ("weekly_review", "Friday", "周度完整复盘", "reports/weekly_full_review.md", ""),
        ("monthly_model_review", "Monthly", "月度模型复盘", "reports/monthly_model_review.md", ""),
    ]
    rows = []
    for node, time_label, title, report, json_name in specs:
        report_path = PROJECT_ROOT / report
        json_path = REPORT_DIR / json_name if json_name else None
        payload = _read_json(json_path) if json_path else {}
        exists = report_path.exists()
        status = "OK" if exists else "WAITING"
        if _time_is_future_today(time_label, now):
            status = "WAITING"
        if payload.get("alerts"):
            status = "CAUTION"
        if node == "data_update" and payload:
            status = _data_update_badge_status(payload)
        if node == "daily_close" and data_update_status:
            update_status = _data_update_badge_status(data_update_status)
            if update_status in {"CAUTION", "ERROR"} and status == "OK":
                status = "CAUTION"
        rows.append(
            {
                "node": node,
                "time_label": time_label,
                "title": title,
                "status": status,
                "conclusion": _automation_conclusion(node, payload, data_update_status, exists),
                "generated_at": payload.get("generated_at", _mtime(report_path)),
                "report_href": "../" + report,
            }
        )
    return rows


def _automation_conclusion(node: str, payload: dict, data_update_status: dict | None, exists: bool) -> str:
    if node == "data_update" and payload:
        return f"{payload.get('status', 'unknown')}：{payload.get('reason', '')}"
    if node == "daily_close" and data_update_status:
        update_status = _data_update_badge_status(data_update_status)
        if update_status in {"CAUTION", "ERROR"}:
            return "报告已生成，但 ETF 日线更新未完全成功；请查看数据更新诊断。"
    return payload.get("conclusion", "见报告" if exists else "等待生成")


def _data_update_badge_status(payload: dict) -> str:
    severity = str(payload.get("severity", "")).upper()
    if severity == "ERROR":
        return "ERROR"
    if severity == "CAUTION":
        return "CAUTION"
    if severity == "INFO":
        return "WAITING" if str(payload.get("status", "")).lower() == "dry_run" else "OK"
    return "OK" if payload else "WAITING"


def _review_snapshot() -> dict:
    specs = [
        ("每日轻量滚动回测", REPORT_DIR / "daily_rolling_backtest.md", "../reports/daily_rolling_backtest.md"),
        ("周度完整复盘", REPORT_DIR / "weekly_full_review.md", "../reports/weekly_full_review.md"),
        ("月度模型复盘", REPORT_DIR / "monthly_model_review.md", "../reports/monthly_model_review.md"),
        ("因子分析", REPORT_DIR / "factor_analysis_report.md", "../reports/factor_analysis_report.md"),
        ("模型研究", REPORT_DIR / "model_research_report.md", "../reports/model_research_report.md"),
        ("市场状态研究", REPORT_DIR / "market_state_report.md", "../reports/market_state_report.md"),
        ("组合暴露研究", REPORT_DIR / "portfolio_exposure_report.md", "../reports/portfolio_exposure_report.md"),
        ("参数扫描研究", REPORT_DIR / "parameter_sweep_report.md", "../reports/parameter_sweep_report.md"),
        ("模型研究质量审查", REPORT_DIR / "model_research_quality_review.md", "../reports/model_research_quality_review.md"),
        ("执行层接入计划", REPORT_DIR / "execution_layer_integration_plan.md", "../reports/execution_layer_integration_plan.md"),
        ("ETF 分类研究", REPORT_DIR / "etf_classification_report.md", "../reports/etf_classification_report.md"),
        ("ETF 类型分层", REPORT_DIR / "etf_type_classification_report.md", "../reports/etf_type_classification_report.md"),
        ("持有周期研究", REPORT_DIR / "holding_period_research_report.md", "../reports/holding_period_research_report.md"),
        ("退出规则研究", REPORT_DIR / "exit_rule_research_report.md", "../reports/exit_rule_research_report.md"),
        ("新闻情绪框架", REPORT_DIR / "news_sentiment_framework.md", "../reports/news_sentiment_framework.md"),
        ("新闻数据源计划", REPORT_DIR / "news_data_source_plan.md", "../reports/news_data_source_plan.md"),
        ("当前持仓适配", REPORT_DIR / "current_positions_strategy_fit_report.md", "../reports/current_positions_strategy_fit_report.md"),
        ("下一阶段总报告", REPORT_DIR / "next_stage_strategy_optimization_report.md", "../reports/next_stage_strategy_optimization_report.md"),
        ("catchup 修复报告", REPORT_DIR / "launchd_catchup_bugfix_report.md", "../reports/launchd_catchup_bugfix_report.md"),
        ("日线更新诊断", REPORT_DIR / "daily_data_update_diagnosis_report.md", "../reports/daily_data_update_diagnosis_report.md"),
        ("卖出复核报告", REPORT_DIR / "sell_signal_review.md", "../reports/sell_signal_review.md"),
        ("卖出复核设计", REPORT_DIR / "sell_signal_review_design_report.md", "../reports/sell_signal_review_design_report.md"),
        ("模拟交易计划", REPORT_DIR / "paper_trade_plan.md", "../reports/paper_trade_plan.md"),
        ("模拟交易引擎报告", REPORT_DIR / "paper_trade_engine_report.md", "../reports/paper_trade_engine_report.md"),
        ("模拟交易引擎设计", REPORT_DIR / "paper_trade_engine_design_report.md", "../reports/paper_trade_engine_design_report.md"),
        ("Phase 2C 轻量接入", REPORT_DIR / "phase2c_execution_layer_light_integration_report.md", "../reports/phase2c_execution_layer_light_integration_report.md"),
    ]
    return {"items": [{"name": name, "status": "OK" if path.exists() else "WAITING", "updated_at": _mtime(path), "href": href} for name, path, href in specs]}


def _read_health_report() -> tuple[dict[str, dict], dict]:
    path = REPORT_DIR / "latest_data_health.md"
    summary: dict[str, str] = {}
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows, summary
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        match = re.match(r"^- ([^：:]+)[：:]\s*(.+)$", line.strip())
        if match:
            summary[match.group(1).strip()] = match.group(2).strip()
    table = [line for line in lines if line.strip().startswith("|")]
    if len(table) >= 3:
        headers = [cell.strip() for cell in table[0].strip("|").split("|")]
        for line in table[2:]:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            code = row.get("代码", "")
            if code:
                rows[code] = {"status": row.get("状态", ""), "note": row.get("提醒", ""), "hard_issue": row.get("硬问题", ""), "group": row.get("group", "")}
    return rows, summary


def _read_markdown_table(path: Path, section_title: str) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        if line.strip().startswith("## "):
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


def _latest_data_date() -> str:
    latest = ""
    for path in (DATA_DIR / "etf_daily").glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"])
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or "unknown"


def _failed_counts() -> dict:
    quarantine_dir = DATA_DIR / "staging" / "jqdata_expanded_failed"
    quarantine = len(list(quarantine_dir.glob("*.csv"))) if quarantine_dir.exists() else 0
    unresolved = 0
    results = REPORT_DIR / "etf_expansion_import_results.csv"
    if results.exists():
        df = _read_csv(results)
        if "final_action" in df.columns:
            unresolved = int((df["final_action"] == "unresolved").sum())
    return {"quarantine": quarantine, "unresolved": unresolved}


def _data_update_status_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "data_update_status.json")
    if payload:
        return payload
    return {
        "generated_at": "",
        "source": "baostock",
        "mode": "unknown",
        "requested_end": "unknown",
        "latest_local_date": _latest_data_date(),
        "severity": "CAUTION",
        "status": "missing_status_file",
        "reason": "reports/data_update_status.json 尚未生成；无法确认本轮日线更新是否真正完成。",
        "added_rows": 0,
        "estimated_api_calls": "N/A",
        "status_counts": {},
        "recommendation": "Run scripts/update_etf_data.py or daily_close to generate a machine-readable update status.",
    }


def _data_sources_snapshot(data_update_status: dict | None = None) -> dict:
    payload = _read_json(REPORT_DIR / "data_source_status.json")
    if payload:
        return payload
    data_update_status = data_update_status or {}
    return data_update_status.get("data_sources") or {
        "primary_source": "jqdata",
        "fallback_source": "baostock",
        "actual_source_used": data_update_status.get("actual_source_used", data_update_status.get("source_used", data_update_status.get("source", "unknown"))),
        "jqdata_status": data_update_status.get("jqdata_status", "UNKNOWN"),
        "baostock_status": data_update_status.get("baostock_status", "UNKNOWN"),
        "fallback_triggered": bool(data_update_status.get("fallback_triggered", False)),
        "source_priority": ["jqdata", "baostock", "tushare"],
        "latest_data_date": data_update_status.get("latest_data_date", data_update_status.get("latest_local_date", _latest_data_date())),
        "new_rows": data_update_status.get("new_rows", data_update_status.get("added_rows", 0)),
        "failed_symbols": data_update_status.get("failed_symbols", []),
        "unresolved_symbols": data_update_status.get("unresolved_symbols", []),
    }


def _strategy_enhancement_preview_snapshot() -> dict:
    df = _read_csv(REPORT_DIR / "strategy_enhancement_preview.csv")
    if df.empty:
        return {
            "enabled": True,
            "execution_enabled": False,
            "rows": [],
            "original_top3": [],
            "adjusted_top3": [],
            "top3_changed": False,
            "execution_safety": _execution_safety_snapshot(),
        }
    rows = df.to_dict(orient="records")
    original = sorted(rows, key=lambda item: _float(item.get("original_rank") or 999))[:3]
    adjusted = sorted(rows, key=lambda item: _float(item.get("adjusted_rank_preview") or 999))[:3]
    top3_changed = [row.get("symbol") for row in original] != [row.get("symbol") for row in adjusted]
    return {
        "enabled": True,
        "execution_enabled": False,
        "generated_at": _mtime(REPORT_DIR / "strategy_enhancement_preview.csv"),
        "rows": rows,
        "original_top3": original,
        "adjusted_top3": adjusted,
        "top3_changed": top3_changed,
        "score_delta_largest": max(rows, key=lambda item: abs(_float(item.get("score_delta")))) if rows else {},
        "broad_index_bonus_hits": [row for row in rows if _float(row.get("broad_index_balance_bonus")) > 0],
        "defensive_bonus_hits": [row for row in rows if _float(row.get("defensive_balance_bonus")) > 0],
        "same_group_penalty_hits": [row for row in rows if _float(row.get("same_group_concentration_penalty")) < 0],
        "high_beta_penalty_hits": [row for row in rows if _float(row.get("high_beta_penalty")) < 0],
        "data_health_penalty_hits": [row for row in rows if _float(row.get("data_health_penalty")) < 0],
        "execution_safety": _execution_safety_snapshot(),
        "report_href": "../reports/strategy_enhancement_preview.md",
    }


def _type_aware_review_snapshot(rows: list[dict]) -> dict:
    elevated = [row for row in rows if str(row.get("type_review_severity", "")).lower() == "elevated"]
    return {
        "enabled": True,
        "execution_enabled": False,
        "position_count": len(rows),
        "elevated_count": len(elevated),
        "rows": rows,
        "status_counts": _value_counts(rows, "type_review_severity"),
        "note": "Type-aware review is display-only and does not trigger automatic SELL.",
    }


def _strategy_preview_tracking_snapshot() -> dict:
    df = _read_csv(REPORT_DIR / "strategy_preview_tracking.csv")
    shadow_df = _read_csv(REPORT_DIR / "strategy_preview_shadow_portfolio.csv")
    if df.empty:
        safety = _execution_safety_snapshot()
        return {
            "enabled": True,
            "rows": [],
            "summary": {
                "sample_count": 0,
                "completed_count": 0,
                "partial_count": 0,
                "pending_count": 0,
                "missing_count": 0,
                "top3_changed": False,
                "conclusion": "当前样本不足，不能证明 adjusted preview 优于 original ranking。",
            },
            "forward_return_comparison": {"returns": {}},
            "penalty_bonus_review": {},
            "shadow_model": {
                "enabled": True,
                "execution_enabled": False,
                "paper_trade_engine_enabled": False,
                "real_trade_enabled": False,
                "initial_cash_assumption": 20000,
                "max_holdings": 3,
                "single_position_target": 0.20,
                "total_target_position": 0.60,
                "min_trade_value": 3000,
                "description": "research only",
                "rows": [],
            },
            "execution_safety": safety,
        }
    rows = df.to_dict(orient="records")
    latest_date = max(str(row.get("snapshot_date", "")) for row in rows)
    latest = [row for row in rows if str(row.get("snapshot_date", "")) == latest_date]
    original_top3 = sorted([row for row in latest if row.get("in_original_top3") == "yes"], key=lambda row: _float(row.get("original_rank")))
    adjusted_top3 = sorted([row for row in latest if row.get("in_adjusted_top3") == "yes"], key=lambda row: _float(row.get("adjusted_rank_preview")))
    returns = {
        "original_top3": _dashboard_avg_returns(rows, lambda row: row.get("in_original_top3") == "yes"),
        "adjusted_top3": _dashboard_avg_returns(rows, lambda row: row.get("in_adjusted_top3") == "yes"),
        "only_original_top3": _dashboard_avg_returns(rows, lambda row: row.get("only_in_original_top3") == "yes"),
        "only_adjusted_top3": _dashboard_avg_returns(rows, lambda row: row.get("only_in_adjusted_top3") == "yes"),
        "high_beta_penalty": _dashboard_avg_returns(rows, lambda row: "high_beta" in str(row.get("penalty_reason", ""))),
        "data_health_penalty": _dashboard_avg_returns(rows, lambda row: "data_health" in str(row.get("penalty_reason", ""))),
        "concentration_penalty": _dashboard_avg_returns(rows, lambda row: "same_group" in str(row.get("penalty_reason", "")) or "concentration" in str(row.get("penalty_reason", ""))),
        "broad_index_bonus": _dashboard_avg_returns(rows, lambda row: "broad_index" in str(row.get("bonus_reason", ""))),
        "defensive_bonus": _dashboard_avg_returns(rows, lambda row: "defensive" in str(row.get("bonus_reason", ""))),
    }
    completed = sum(1 for row in rows if row.get("forward_returns_status") == "completed")
    top3_changed = [row.get("symbol") for row in original_top3] != [row.get("symbol") for row in adjusted_top3]
    conclusion = "当前样本不足，不能证明 adjusted preview 优于 original ranking。" if completed < 30 else "样本已开始积累，仍需周/月度复盘判断。"
    safety = _execution_safety_snapshot()
    safety["shadow_model_enabled"] = True
    safety["shadow_model_execution_enabled"] = False
    return {
        "enabled": True,
        "generated_at": _mtime(REPORT_DIR / "strategy_preview_tracking.csv"),
        "rows": rows,
        "summary": {
            "latest_snapshot_date": latest_date,
            "sample_count": len(rows),
            "completed_count": completed,
            "partial_count": sum(1 for row in rows if row.get("forward_returns_status") == "partial"),
            "pending_count": sum(1 for row in rows if row.get("forward_returns_status") == "pending"),
            "missing_count": sum(1 for row in rows if row.get("forward_returns_status") == "missing_data"),
            "original_top3": original_top3,
            "adjusted_top3": adjusted_top3,
            "top3_changed": top3_changed,
            "only_original_count": sum(1 for row in latest if row.get("only_in_original_top3") == "yes"),
            "only_adjusted_count": sum(1 for row in latest if row.get("only_in_adjusted_top3") == "yes"),
            "sample_sufficient": completed >= 30,
            "conclusion": conclusion,
        },
        "forward_return_comparison": {"returns": returns, "sample_sufficient": completed >= 30, "conclusion": conclusion},
        "penalty_bonus_review": {
            "high_beta_penalty": returns["high_beta_penalty"],
            "data_health_penalty": returns["data_health_penalty"],
            "concentration_penalty": returns["concentration_penalty"],
            "broad_index_bonus": returns["broad_index_bonus"],
            "defensive_bonus": returns["defensive_bonus"],
        },
        "bonus_hit_count": sum(1 for row in rows if str(row.get("bonus_reason", "")).strip()),
        "shadow_model": {
            "enabled": True,
            "execution_enabled": False,
            "paper_trade_engine_enabled": False,
            "real_trade_enabled": False,
            "initial_cash_assumption": 20000,
            "max_holdings": 3,
            "single_position_target": 0.20,
            "total_target_position": 0.60,
            "min_trade_value": 3000,
            "description": "research only",
            "rows": shadow_df.to_dict(orient="records") if not shadow_df.empty else [],
            "report_href": "../reports/strategy_preview_shadow_portfolio.md",
        },
        "execution_safety": safety,
        "report_href": "../reports/strategy_preview_tracking_report.md",
    }


def _dashboard_avg_returns(rows: list[dict], selector) -> dict:
    selected = [row for row in rows if selector(row)]
    out = {"sample_count": len(selected)}
    for window in [1, 3, 5, 10]:
        values = [_float(row.get(f"forward_{window}d_return"), fallback=float("nan")) for row in selected]
        values = [value for value in values if pd.notna(value)]
        out[f"forward_{window}d_mean"] = sum(values) / len(values) if values else ""
        out[f"forward_{window}d_n"] = len(values)
    return out


def _execution_safety_snapshot() -> dict:
    return {
        "paper_only": True,
        "adjusted_rank_score_preview_enabled": True,
        "adjusted_rank_score_execution_enabled": False,
        "paper_use_market_state_position": PAPER_USE_MARKET_STATE_POSITION,
        "shadow_model_enabled": True,
        "shadow_model_execution_enabled": False,
        "real_trade_enabled": False,
        "broker_api_enabled": False,
        "real_account_read_enabled": False,
        "real_order_buttons_enabled": False,
        "arbitrary_command_enabled": False,
        "task_whitelist_only": True,
        "app_launch_status": _read_json(PROJECT_ROOT / "logs" / "app_launch_status.json"),
        "app_launch_diagnostics": _read_json(REPORT_DIR / "app_launch_diagnostics.json"),
    }


def _value_counts(rows: list[dict], field: str) -> dict:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, "N/A") or "N/A")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _dashboard_links() -> list[dict]:
    specs = [
        ("控制台快照", "data", REPORT_DIR / "dashboard_data.json", "../reports/dashboard_data.json"),
        ("项目结构审计", "audit", REPORT_DIR / "project_structure_audit.md", "../reports/project_structure_audit.md"),
        ("路径依赖审计", "audit", REPORT_DIR / "path_dependency_audit.md", "../reports/path_dependency_audit.md"),
        ("文件分类计划", "audit", REPORT_DIR / "file_classification_plan.md", "../reports/file_classification_plan.md"),
        ("推荐目录结构", "audit", REPORT_DIR / "recommended_project_layout.md", "../reports/recommended_project_layout.md"),
        ("项目整理路线", "audit", REPORT_DIR / "project_cleanup_roadmap.md", "../reports/project_cleanup_roadmap.md"),
        ("报告索引", "audit", REPORT_DIR / "report_index.md", "../reports/report_index.md"),
        ("归档候选清单", "audit", REPORT_DIR / "archive_candidate_list.md", "../reports/archive_candidate_list.md"),
        ("归档前 Manifest", "audit", REPORT_DIR / "archive_manifest_before.md", "../reports/archive_manifest_before.md"),
        ("归档后 Manifest", "audit", REPORT_DIR / "archive_manifest_after.md", "../reports/archive_manifest_after.md"),
        ("日线更新状态", "data", REPORT_DIR / "data_update_status.json", "../reports/data_update_status.json"),
        ("日线更新诊断", "data", REPORT_DIR / "data_update_diagnosis_report.md", "../reports/data_update_diagnosis_report.md"),
        ("日线更新修复报告", "data", REPORT_DIR / "data_update_automation_fix_report.md", "../reports/data_update_automation_fix_report.md"),
        ("数据下载明细", "data", REPORT_DIR / "data_download_report.md", "../reports/data_download_report.md"),
        ("数据源架构审计", "data", REPORT_DIR / "data_source_architecture_audit.md", "../reports/data_source_architecture_audit.md"),
        ("AKShare 可用性诊断", "data", REPORT_DIR / "akshare_connectivity_check.md", "../reports/akshare_connectivity_check.md"),
        ("Provider 分层设计", "data", REPORT_DIR / "data_provider_design.md", "../reports/data_provider_design.md"),
        ("情报数据规划", "data", REPORT_DIR / "intelligence_data_source_plan.md", "../reports/intelligence_data_source_plan.md"),
        ("无未来函数数据规则", "data", REPORT_DIR / "no_lookahead_data_rules.md", "../reports/no_lookahead_data_rules.md"),
        ("Phase 4C 下一步", "data", REPORT_DIR / "phase4c_data_next_step.md", "../reports/phase4c_data_next_step.md"),
        ("Tushare 配置检查", "data", REPORT_DIR / "tushare_config_check.md", "../reports/tushare_config_check.md"),
        ("Tushare staging dry-run", "data", REPORT_DIR / "tushare_staging_check.md", "../reports/tushare_staging_check.md"),
        ("Tushare/BaoStock 对比", "data", REPORT_DIR / "tushare_baostock_compare.md", "../reports/tushare_baostock_compare.md"),
        ("Provider 状态总览", "data", REPORT_DIR / "data_provider_status.md", "../reports/data_provider_status.md"),
        ("Tushare no-lookahead", "data", REPORT_DIR / "tushare_no_lookahead_check.md", "../reports/tushare_no_lookahead_check.md"),
        ("v2 收益拖累归因", "research", REPORT_DIR / "v2_underperformance_attribution.md", "../reports/v2_underperformance_attribution.md"),
        ("模型防过拟合护栏", "research", REPORT_DIR / "model_overfit_guardrails.md", "../reports/model_overfit_guardrails.md"),
        ("Regime-aware 研究", "research", REPORT_DIR / "regime_aware_model_research.md", "../reports/regime_aware_model_research.md"),
        ("ETF type-aware 研究", "research", REPORT_DIR / "etf_type_aware_model_research.md", "../reports/etf_type_aware_model_research.md"),
        ("Alpha 因子增强", "research", REPORT_DIR / "alpha_factor_enhancement_research.md", "../reports/alpha_factor_enhancement_research.md"),
        ("Phase 4C Alpha 综合对比", "research", REPORT_DIR / "phase4c_alpha_model_comparison.md", "../reports/phase4c_alpha_model_comparison.md"),
        ("Phase 4C Alpha 决策", "research", REPORT_DIR / "phase4c_alpha_model_decision.md", "../reports/phase4c_alpha_model_decision.md"),
        ("Persistence Breakout 信号", "research", REPORT_DIR / "persistence_breakout_shadow_signal.md", "../reports/persistence_breakout_shadow_signal.md"),
        ("Persistence Breakout 组合", "research", REPORT_DIR / "persistence_breakout_shadow_portfolio.md", "../reports/persistence_breakout_shadow_portfolio.md"),
        ("Shadow 模型对比", "research", REPORT_DIR / "model_shadow_comparison.md", "../reports/model_shadow_comparison.md"),
        ("Persistence Breakout 观察规则", "research", REPORT_DIR / "persistence_breakout_shadow_observation_rules.md", "../reports/persistence_breakout_shadow_observation_rules.md"),
        ("Missed Opportunity Tracker", "research", REPORT_DIR / "missed_opportunity_tracker.md", "../reports/missed_opportunity_tracker.md"),
        ("Missed Opportunity 过滤归因", "research", REPORT_DIR / "missed_opportunity_by_filter_reason.md", "../reports/missed_opportunity_by_filter_reason.md"),
        ("Risk-on 空仓分析", "research", REPORT_DIR / "risk_on_empty_signal_analysis.md", "../reports/risk_on_empty_signal_analysis.md"),
        ("Selected vs Filtered", "research", REPORT_DIR / "selected_vs_filtered_forward_return.md", "../reports/selected_vs_filtered_forward_return.md"),
        ("Missed Opportunity 观察规则", "research", REPORT_DIR / "missed_opportunity_observation_rules.md", "../reports/missed_opportunity_observation_rules.md"),
        ("Shadow 每周观察", "research", REPORT_DIR / "shadow_observation_weekly.md", "../reports/shadow_observation_weekly.md"),
        ("ChatGPT/Main 周报分析包", "research", REPORT_DIR / "chatgpt_weekly_analysis_packet_latest.md", "../reports/chatgpt_weekly_analysis_packet_latest.md"),
        ("每日最简摘要", "daily", REPORT_DIR / "latest_brief.md", "../reports/latest_brief.md"),
        ("模拟盘持仓", "paper", REPORT_DIR / "latest_paper_portfolio.md", "../reports/latest_paper_portfolio.md"),
        ("BUY Ranking", "signal", REPORT_DIR / "buy_signal_ranking.md", "../reports/buy_signal_ranking.md"),
        ("卖出复核", "risk", REPORT_DIR / "sell_signal_review.md", "../reports/sell_signal_review.md"),
        ("模拟交易计划", "paper", REPORT_DIR / "paper_trade_plan.md", "../reports/paper_trade_plan.md"),
        ("模拟交易引擎", "paper", REPORT_DIR / "paper_trade_engine_report.md", "../reports/paper_trade_engine_report.md"),
        ("B1 策略增强预览", "research", REPORT_DIR / "strategy_enhancement_preview.md", "../reports/strategy_enhancement_preview.md"),
        ("宽基平衡观察", "research", REPORT_DIR / "broad_base_balance_preview.md", "../reports/broad_base_balance_preview.md"),
        ("B1 执行层渐进优化", "research", REPORT_DIR / "b1_strategy_enhancement_preview_report.md", "../reports/b1_strategy_enhancement_preview_report.md"),
        ("B2 预览跟踪账本", "research", REPORT_DIR / "strategy_preview_tracking_report.md", "../reports/strategy_preview_tracking_report.md"),
        ("B2 影子组合", "research", REPORT_DIR / "strategy_preview_shadow_portfolio.md", "../reports/strategy_preview_shadow_portfolio.md"),
        ("B2 跟踪总结", "research", REPORT_DIR / "b2_strategy_preview_tracking_report.md", "../reports/b2_strategy_preview_tracking_report.md"),
        ("Phase 2C 轻量接入", "research", REPORT_DIR / "phase2c_execution_layer_light_integration_report.md", "../reports/phase2c_execution_layer_light_integration_report.md"),
        ("市场状态研究", "research", REPORT_DIR / "market_state_report.md", "../reports/market_state_report.md"),
        ("ETF 分类研究", "research", REPORT_DIR / "etf_classification_report.md", "../reports/etf_classification_report.md"),
        ("组合暴露研究", "research", REPORT_DIR / "portfolio_exposure_report.md", "../reports/portfolio_exposure_report.md"),
        ("持有周期研究", "research", REPORT_DIR / "holding_period_research_report.md", "../reports/holding_period_research_report.md"),
        ("退出规则研究", "research", REPORT_DIR / "exit_rule_research_report.md", "../reports/exit_rule_research_report.md"),
        ("参数扫描研究", "research", REPORT_DIR / "parameter_sweep_report.md", "../reports/parameter_sweep_report.md"),
        ("模型研究质量审查", "research", REPORT_DIR / "model_research_quality_review.md", "../reports/model_research_quality_review.md"),
        ("执行层接入计划", "research", REPORT_DIR / "execution_layer_integration_plan.md", "../reports/execution_layer_integration_plan.md"),
        ("ETF 轮动成熟框架参考", "research", REPORT_DIR / "etf_rotation_mature_model_reference.md", "../reports/etf_rotation_mature_model_reference.md"),
        ("Ranking v2 执行口径", "research", REPORT_DIR / "ranking_model_v2_execution_assumption.md", "../reports/ranking_model_v2_execution_assumption.md"),
        ("Ranking v2 历史回测", "research", REPORT_DIR / "ranking_model_v2_backtest_report.md", "../reports/ranking_model_v2_backtest_report.md"),
        ("Ranking v2 决策报告", "research", REPORT_DIR / "ranking_model_v2_decision_report.md", "../reports/ranking_model_v2_decision_report.md"),
        ("Top10 过滤分析", "research", REPORT_DIR / "top10_candidate_filter_analysis.md", "../reports/top10_candidate_filter_analysis.md"),
        ("数据覆盖", "data", REPORT_DIR / "latest_data_coverage.md", "../reports/latest_data_coverage.md"),
        ("数据健康", "data", REPORT_DIR / "latest_data_health.md", "../reports/latest_data_health.md"),
        ("每日滚动回测", "review", REPORT_DIR / "daily_rolling_backtest.md", "../reports/daily_rolling_backtest.md"),
        ("周度完整复盘", "review", REPORT_DIR / "weekly_full_review.md", "../reports/weekly_full_review.md"),
        ("月度模型复盘", "review", REPORT_DIR / "monthly_model_review.md", "../reports/monthly_model_review.md"),
        ("四节点同步", "automation", REPORT_DIR / "automation_four_node_sync_report.md", "../reports/automation_four_node_sync_report.md"),
        ("catchup 状态", "automation", REPORT_DIR / "catchup_scheduler_status.md", "../reports/catchup_scheduler_status.md"),
        ("因子分析", "research", REPORT_DIR / "factor_analysis_report.md", "../reports/factor_analysis_report.md"),
        ("模型研究", "research", REPORT_DIR / "model_research_report.md", "../reports/model_research_report.md"),
        ("策略新闻情绪研究", "research", REPORT_DIR / "etf_strategy_news_sentiment_research.md", "../reports/etf_strategy_news_sentiment_research.md"),
        ("看板升级设计说明", "dashboard", REPORT_DIR / "dashboard_redesign_research.md", "../reports/dashboard_redesign_research.md"),
    ]
    return [{"name": name, "category": category, "path": str(path.relative_to(PROJECT_ROOT)), "href": href, "exists": path.exists()} for name, category, path, href in specs]


def _link_health(rows: list[dict]) -> dict:
    missing = [row for row in rows if not row.get("exists")]
    return {"total": len(rows), "valid": len(rows) - len(missing), "missing": len(missing), "missing_items": missing}


def _dashboard_sources() -> list[dict]:
    return [
        {
            "type": "open-source",
            "name": "Freqtrade / FreqUI",
            "url": "https://github.com/freqtrade/frequi",
            "lesson": "开源交易台把持仓、订单、策略状态和日志放在同一个操作视图；本看板借鉴其“执行状态可见”的思路。",
        },
        {
            "type": "platform",
            "name": "QuantConnect Backtest Results",
            "url": "https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/results",
            "lesson": "专业量化平台强调回测、交易、持仓、统计指标的可追溯，本看板把 Review 与 Paper Engine 固化为一等模块。",
        },
        {
            "type": "charting",
            "name": "TradingView Watchlists / Alerts / Charts",
            "url": "https://www.tradingview.com/features/",
            "lesson": "观察列表、信号和图表需要并列呈现；本看板将 BUY Ranking、持仓和风险提示放到同一决策链。",
        },
        {
            "type": "broker",
            "name": "Interactive Brokers PortfolioAnalyst",
            "url": "https://www.interactivebrokers.com/en/software/portfolioanalyst.php",
            "lesson": "券商组合分析强调资产、表现、风险和归因，本看板增加系统健康、暴露和链接体检。",
        },
        {
            "type": "risk",
            "name": "BlackRock Aladdin",
            "url": "https://www.blackrock.com/aladdin",
            "lesson": "风险平台的核心是先看风险与运行状态，再看细节；本看板把风险条与系统健康放在前部。",
        },
        {
            "type": "broker",
            "name": "thinkorswim Platform",
            "url": "https://www.schwab.com/trading/thinkorswim",
            "lesson": "券商终端重视可扫读布局、监控列表和多模块工作区；本看板采用导航锚点和工作台分区。",
        },
    ]


def _latest_engine_state(state: dict, latest_data_date: str, run_date: str) -> dict:
    if not isinstance(state, dict) or not state:
        return {}
    if run_date in state and isinstance(state.get(run_date), dict):
        payload = state[run_date]
        return {"run_date": run_date, **payload}
    if latest_data_date in state and isinstance(state.get(latest_data_date), dict):
        payload = state[latest_data_date]
        return {"run_date": payload.get("run_date", latest_data_date), **payload}
    latest_key = sorted(state.keys())[-1]
    payload = state.get(latest_key, {})
    if isinstance(payload, dict):
        return {"date": latest_key, **payload}
    return {}


def _paper_trade_engine_snapshot(state: dict, plan_rows: list[dict], summary: dict) -> dict:
    buy_count = sum(1 for row in plan_rows if str(row.get("action", "")).upper() == "BUY" and str(row.get("plan_status", "")).lower() == "executed")
    sell_count = sum(1 for row in plan_rows if str(row.get("action", "")).upper() == "SELL" and str(row.get("plan_status", "")).lower() == "executed")
    skipped = [row for row in plan_rows if str(row.get("plan_status", "")).lower().startswith("skipped")]
    return {
        "state": state,
        "plan_count": len(plan_rows),
        "executed_buy_count": buy_count,
        "executed_sell_count": sell_count,
        "skipped_count": len(skipped),
        "skip_reasons": [row.get("reason", "") for row in skipped[:8]],
        "position_count": summary.get("position_count", 0),
    }


def _trading_costs_snapshot(trades: pd.DataFrame, plan_rows: list[dict], engine: dict) -> dict:
    today = str(engine.get("state", {}).get("run_date") or pd.Timestamp.now().strftime("%Y-%m-%d"))
    trade_records = trades.to_dict(orient="records") if not trades.empty else []
    today_trades = [row for row in trade_records if str(row.get("date", row.get("trade_date", "")))[:10] == today]
    today_plan = [row for row in plan_rows if str(row.get("run_date", row.get("date", "")))[:10] == today]
    return {
        "commission_rate": PAPER_COMMISSION_RATE,
        "min_commission": PAPER_MIN_COMMISSION,
        "stamp_tax_rate": PAPER_STAMP_TAX_RATE,
        "transfer_fee_rate": PAPER_TRANSFER_FEE_RATE,
        "slippage_rate": PAPER_SLIPPAGE_RATE,
        "execution_price_type": PAPER_EXECUTION_PRICE_TYPE,
        "etf_stamp_tax_note": "ETF 模拟暂不计印花税",
        "today_commission": sum(_float(row.get("commission", row.get("fee"))) for row in today_trades),
        "today_plan_commission": sum(_float(row.get("commission")) for row in today_plan),
        "today_trade_cost": _float(engine.get("state", {}).get("today_trade_cost")),
        "today_slippage_cost": _float(engine.get("state", {}).get("today_slippage_cost")),
    }


def _signal_status(mid: object, short: object, health_status: str, current_price: float, stop_loss: float) -> str:
    if stop_loss > 0 and current_price <= stop_loss:
        return "INVALID"
    if health_status == "提醒":
        return "REVIEW"
    if mid == "BUY" and short == "BUY":
        return "VALID"
    if mid == "BUY" or short == "BUY":
        return "WEAKENING"
    return "REVIEW"


def _risk_tag(health_status: str, health_note: str, market_value: float, current_price: float, stop_loss: float) -> str:
    if stop_loss > 0 and current_price <= stop_loss:
        return "STOP_LOSS_ALERT"
    if market_value > SINGLE_ETF_LIMIT:
        return "POSITION_LIMIT_ALERT"
    if health_status == "提醒":
        return f"DATA_HEALTH_CAUTION: {health_note}" if health_note else "DATA_HEALTH_CAUTION"
    if health_status == "异常":
        return "DATA_HEALTH_ERROR"
    return "NORMAL"


def _action_suggestion(signal_status: str, risk_tag: str) -> str:
    if "STOP" in risk_tag or "ERROR" in risk_tag:
        return "REDUCE"
    if "CAUTION" in risk_tag or signal_status == "REVIEW":
        return "REVIEW"
    if signal_status == "WEAKENING":
        return "WATCH"
    return "HOLD"


def _holding_cycle_status(holding_days: int, min_days: int, max_days: int) -> str:
    if min_days <= 0 or max_days <= 0:
        return "N/A"
    if holding_days < min_days:
        return "EARLY"
    if holding_days <= max_days:
        return "IN_PROFILE"
    return "OVER_PROFILE"


def _short_swing_weakening(reason: object, current_short: object) -> str:
    prior_buy = "short_swing=BUY" in str(reason or "")
    current = str(current_short or "").upper()
    if prior_buy and current in {"WATCH", "SELL", "N/A", ""}:
        return "WEAKENING"
    return "NO"


def _sentiment_status(meta_row: dict) -> str:
    if str(meta_row.get("sentiment_filter_required", "")).strip() in {"1", "True", "true", "yes"}:
        return "framework_only"
    if str(meta_row.get("news_required", "")).strip() in {"medium", "medium_high", "high"}:
        return "framework_only"
    return "no_data"


def _research_note(meta_row: dict, holding_cycle_status: str, short_weakening: str, risk_tag: str) -> str:
    notes = [
        f"type={meta_row.get('etf_type','N/A')}",
        f"profile={meta_row.get('holding_profile','N/A')} days",
        f"cycle={holding_cycle_status}",
    ]
    if short_weakening == "WEAKENING":
        notes.append("short_swing weakening -> REVIEW candidate")
    if risk_tag != "NORMAL":
        notes.append(str(risk_tag))
    notes.append("sentiment is framework-only, not a BUY factor")
    return "; ".join(notes)


def _buy_signal_from_reason(reason: object, mid: object, short: object) -> str:
    text = str(reason or "")
    if "mid_trend=BUY" in text and "short_swing=BUY" in text:
        return "BUY/BUY"
    return f"{mid}/{short}"


def _parse_reason_signal(reason: object, key: str) -> str:
    match = re.search(rf"{re.escape(key)}=([A-Z_]+)", str(reason or ""))
    return match.group(1) if match else ""


def _short_reason(reason: object) -> str:
    text = str(reason or "")
    score = re.search(r"rank_score=([0-9.]+)", text)
    if score:
        return f"rank_score={_score(score.group(1))}"
    return text[:40]


def _latest_trade_value(trades: pd.DataFrame, col: str, fallback: float) -> float:
    if trades.empty or col not in trades.columns:
        return float(fallback)
    values = pd.to_numeric(trades[col], errors="coerce").dropna()
    return float(values.iloc[-1]) if not values.empty else float(fallback)


def _time_is_future_today(label: str, now: pd.Timestamp) -> bool:
    if ":" not in label:
        return False
    hour, minute = [int(part) for part in label.split(":", 1)]
    target = now.normalize() + pd.Timedelta(hours=hour, minutes=minute)
    return target > now


def _read_classification_csv() -> pd.DataFrame:
    primary = DATA_DIR / "etf_classification.csv"
    legacy = DATA_DIR / "etf_type_classification.csv"
    df = _read_csv(primary)
    if df.empty:
        df = _read_csv(legacy)
    if not df.empty and "symbol" not in df.columns and "code" in df.columns:
        df["symbol"] = df["code"]
    if not df.empty and "code" not in df.columns and "symbol" in df.columns:
        df["code"] = df["symbol"]
    return df


def _market_state_snapshot() -> dict:
    df = _read_csv(REPORT_DIR / "market_state.csv")
    if df.empty or "row_type" not in df.columns:
        return {"market_state": "N/A", "market_score": "N/A", "components": []}
    summary = df[df["row_type"] == "summary"].head(1)
    payload = summary.iloc[0].to_dict() if not summary.empty else {}
    components = df[df["row_type"] == "component"].head(12).to_dict(orient="records")
    payload["components"] = components
    payload["report_href"] = "../reports/market_state_report.md"
    return payload


def _portfolio_exposure_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "portfolio_exposure.json")
    if isinstance(payload, dict) and payload:
        payload.setdefault("report_href", "../reports/portfolio_exposure_report.md")
        return payload
    df = _read_csv(REPORT_DIR / "portfolio_exposure.csv")
    if df.empty or "row_type" not in df.columns:
        return {"summary": {}, "positions": [], "buckets": [], "warnings": []}
    summary_df = df[df["row_type"] == "summary"].head(1)
    summary = summary_df.iloc[0].to_dict() if not summary_df.empty else {}
    warnings = []
    raw = summary.get("warnings_json", "")
    if raw:
        try:
            warnings = json.loads(raw)
        except Exception:
            warnings = [str(raw)]
    return {
        "summary": summary,
        "positions": df[df["row_type"] == "position"].to_dict(orient="records"),
        "buckets": df[df["row_type"].isin(["group", "etf_type", "risk_profile"])].to_dict(orient="records"),
        "warnings": warnings,
        "report_href": "../reports/portfolio_exposure_report.md",
    }


def _position_review_state_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "position_review_state.json")
    if isinstance(payload, dict) and payload:
        payload.setdefault("report_href", "../reports/position_review_state.md")
        payload.setdefault("audit_href", "../reports/review_state_audit.md")
        return payload
    df = _read_csv(REPORT_DIR / "position_review_state.csv")
    if df.empty:
        return {
            "summary": {
                "position_count": 0,
                "reduce_candidate_count": 0,
                "review_2_count": 0,
                "high_beta_watch_count": 0,
                "profit_protection_watch_count": 0,
                "execution_allowed": False,
                "safety_note": "以下为模拟仓观察状态，不会自动交易。",
            },
            "rows": [],
            "report_href": "../reports/position_review_state.md",
            "audit_href": "../reports/review_state_audit.md",
        }
    rows = df.to_dict(orient="records")
    counts = df.get("review_state", pd.Series(dtype=str)).value_counts().to_dict()
    state_series = df.get("review_state", pd.Series([""] * len(df))).astype(str)
    high_beta_series = df.get("high_beta_flag", pd.Series([""] * len(df))).astype(str)
    pnl_series = pd.to_numeric(df.get("unrealized_pnl_pct", pd.Series([0.0] * len(df))), errors="coerce").fillna(0)
    return {
        "summary": {
            "position_count": int(len(df)),
            "state_counts": counts,
            "reduce_candidate_count": int((state_series == "REDUCE_CANDIDATE").sum()),
            "review_2_count": int((state_series == "REVIEW_2").sum()),
            "high_beta_watch_count": int(high_beta_series.str.lower().isin(["true", "1", "yes"]).sum()),
            "profit_protection_watch_count": int(pnl_series.gt(0.08).sum()),
            "execution_allowed": False,
            "safety_note": "以下为模拟仓观察状态，不会自动交易。",
        },
        "rows": rows,
        "report_href": "../reports/position_review_state.md",
        "audit_href": "../reports/review_state_audit.md",
    }


def _profit_protection_preview_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "profit_protection_preview.json")
    if isinstance(payload, dict) and payload:
        payload.setdefault("report_href", "../reports/profit_protection_preview.md")
        return payload
    df = _read_csv(REPORT_DIR / "profit_protection_preview.csv")
    if df.empty:
        return {
            "summary": {
                "position_count": 0,
                "profit_watch_count": 0,
                "profit_protection_review_count": 0,
                "profit_lock_candidate_count": 0,
                "execution_allowed": False,
                "safety_note": "浮盈保护为研究观察指标，不会自动交易。",
            },
            "rows": [],
            "report_href": "../reports/profit_protection_preview.md",
        }
    state_series = df.get("profit_protection_state", pd.Series([""] * len(df))).astype(str)
    return {
        "summary": {
            "position_count": int(len(df)),
            "state_counts": state_series.value_counts().to_dict(),
            "profit_watch_count": int((state_series == "PROFIT_WATCH").sum()),
            "profit_protection_review_count": int((state_series == "PROFIT_PROTECTION_REVIEW").sum()),
            "profit_lock_candidate_count": int((state_series == "PROFIT_LOCK_CANDIDATE").sum()),
            "total_current_unrealized_pnl": float(pd.to_numeric(df.get("current_unrealized_pnl", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).sum()),
            "total_drawdown_from_profit_peak": float(pd.to_numeric(df.get("drawdown_from_profit_peak", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).sum()),
            "execution_allowed": False,
            "safety_note": "浮盈保护为研究观察指标，不会自动交易。",
        },
        "rows": df.to_dict(orient="records"),
        "report_href": "../reports/profit_protection_preview.md",
    }


def _high_beta_risk_watch_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "high_beta_risk_watch.json")
    if isinstance(payload, dict) and payload:
        payload.setdefault("report_href", "../reports/high_beta_risk_watch.md")
        return payload
    df = _read_csv(REPORT_DIR / "high_beta_risk_watch.csv")
    if df.empty:
        return {
            "summary": {
                "high_beta_position_count": 0,
                "high_beta_market_value": 0,
                "high_beta_weight_of_equity": 0,
                "high_beta_weight_of_holdings": 0,
                "finance_real_estate_market_value": 0,
                "finance_real_estate_weight_of_equity": 0,
                "finance_real_estate_weight_of_holdings": 0,
                "max_single_high_beta_weight": 0,
                "high_beta_exposure_state": "HB_NORMAL",
                "high_beta_exposure_reasons": "暂无高波动持仓观察数据。",
                "execution_allowed": False,
                "safety_note": "高波动风险观察只提示，不自动交易。",
            },
            "rows": [],
            "report_href": "../reports/high_beta_risk_watch.md",
        }
    state_series = df.get("high_beta_risk_state", pd.Series([""] * len(df))).astype(str)
    return {
        "summary": {
            "high_beta_position_count": int(len(df)),
            "state_counts": state_series.value_counts().to_dict(),
            "high_beta_market_value": float(pd.to_numeric(df.get("market_value", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).sum()),
            "high_beta_weight_of_equity": float(pd.to_numeric(df.get("position_weight_of_equity", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).sum()),
            "high_beta_weight_of_holdings": float(pd.to_numeric(df.get("position_weight_of_holdings", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).sum()),
            "finance_real_estate_market_value": 0,
            "finance_real_estate_weight_of_equity": 0,
            "finance_real_estate_weight_of_holdings": 0,
            "max_single_high_beta_weight": float(pd.to_numeric(df.get("position_weight_of_equity", pd.Series([0.0] * len(df))), errors="coerce").fillna(0).max()),
            "high_beta_exposure_state": "HB_WATCH" if not df.empty else "HB_NORMAL",
            "high_beta_exposure_reasons": "CSV fallback: 高波动持仓存在，需观察。",
            "execution_allowed": False,
            "safety_note": "高波动风险观察只提示，不自动交易。",
        },
        "rows": df.to_dict(orient="records"),
        "report_href": "../reports/high_beta_risk_watch.md",
    }


def _broad_base_balance_preview_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "broad_base_balance_preview.json")
    if isinstance(payload, dict) and payload:
        payload.setdefault("report_href", "../reports/broad_base_balance_preview.md")
        return payload
    df = _read_csv(REPORT_DIR / "broad_base_balance_preview.csv")
    if df.empty:
        return {
            "summary": {
                "broad_base_weight": 0,
                "theme_weight": 0,
                "finance_real_estate_weight": 0,
                "tech_growth_weight": 0,
                "high_beta_weight": 0,
                "broad_base_balance_state": "UNKNOWN",
                "theme_concentration_state": "UNKNOWN",
                "balance_candidate_count": 0,
                "execution_allowed": False,
                "summary_text": "broad_base_balance_preview 尚未生成。",
            },
            "rows": [],
            "top_balance_candidates": [],
            "report_href": "../reports/broad_base_balance_preview.md",
            "observation_only": True,
            "execution_allowed": False,
        }
    rows = df.to_dict(orient="records")
    return {
        "summary": {
            "broad_base_weight": 0,
            "theme_weight": 0,
            "finance_real_estate_weight": 0,
            "tech_growth_weight": 0,
            "high_beta_weight": 0,
            "broad_base_balance_state": "BROAD_BASE_MISSING",
            "theme_concentration_state": "THEME_CONCENTRATED",
            "balance_candidate_count": int(len(df)),
            "execution_allowed": False,
            "summary_text": "CSV fallback: 当前有宽基平衡候选，但缺少 JSON 摘要。",
        },
        "rows": rows,
        "top_balance_candidates": rows[:5],
        "report_href": "../reports/broad_base_balance_preview.md",
        "observation_only": True,
        "execution_allowed": False,
    }


def _model_research_snapshot() -> dict:
    return {
        "holding_period": _research_csv_summary(REPORT_DIR / "holding_period_research.csv", "return_drawdown_ratio", descending=True),
        "exit_rule": _research_csv_summary(REPORT_DIR / "exit_rule_research.csv", "avg_forward_return_10d", descending=False),
        "parameter_sweep": _research_csv_summary(REPORT_DIR / "parameter_sweep.csv", "sharpe_proxy", descending=True),
    }


def _universe_quality_review_snapshot() -> dict:
    df = _read_csv(REPORT_DIR / "universe_quality_review.csv")
    if df.empty:
        return {
            "total_etf": 0,
            "recommended_trade_pool": 0,
            "recommended_observe_pool": 0,
            "recommended_exclude_pool": 0,
            "low_liquidity_count": 0,
            "short_history_count": 0,
            "qdii_count": 0,
            "unknown_classification_count": 0,
            "backtest_ready": False,
            "readiness_summary": "universe_quality_review.csv 尚未生成。",
            "report_href": "../reports/universe_quality_review.md",
            "readiness_report_href": "../reports/backtest_readiness_report.md",
        }

    recommended = df.get("recommended_pool", pd.Series(dtype=str)).fillna("unknown").astype(str)
    liquidity = df.get("liquidity_status", pd.Series(dtype=str)).fillna("unknown").astype(str)
    length = df.get("data_length_status", pd.Series(dtype=str)).fillna("unknown").astype(str)
    classification = df.get("classification_status", pd.Series(dtype=str)).fillna("unknown").astype(str)
    latest_ok = df.get("is_latest_to_unified_date", pd.Series([False] * len(df))).map(_boolish)

    recommended_trade_pool = int((recommended == "trade_pool").sum())
    recommended_observe_pool = int((recommended == "observe_pool").sum())
    recommended_exclude_pool = int((recommended == "exclude_pool").sum())
    not_latest_count = int((~latest_ok).sum())
    low_liquidity_count = int(liquidity.isin(["low", "ultra_low", "unknown"]).sum())
    short_history_count = int((length == "short_history").sum())
    qdii_count = int(df.get("qdii_flag", pd.Series([False] * len(df))).map(_boolish).sum())
    unknown_classification_count = int((classification != "classified").sum())
    backtest_ready = recommended_trade_pool >= 30 and not_latest_count == 0

    latest_date = ""
    if "latest_data_date" in df.columns and not df["latest_data_date"].dropna().empty:
        latest_date = str(df["latest_data_date"].dropna().astype(str).max())

    top_issues = [
        f"unknown classification: {unknown_classification_count}",
        f"low/ultra-low liquidity: {low_liquidity_count}",
        f"QDII observe-only: {qdii_count}",
        f"short history: {short_history_count}",
    ]
    readiness_summary = (
        f"{len(df)} 只 ETF 中建议交易池 {recommended_trade_pool} 只、观察池 {recommended_observe_pool} 只、"
        f"剔除池 {recommended_exclude_pool} 只；最新数据日 {latest_date or 'N/A'}。"
        f"{'可以进入第一版回测，但应使用筛选后的 trade_pool。' if backtest_ready else '暂不建议直接进入第一版回测。'}"
    )
    return {
        "total_etf": int(len(df)),
        "recommended_trade_pool": recommended_trade_pool,
        "recommended_observe_pool": recommended_observe_pool,
        "recommended_exclude_pool": recommended_exclude_pool,
        "low_liquidity_count": low_liquidity_count,
        "short_history_count": short_history_count,
        "qdii_count": qdii_count,
        "unknown_classification_count": unknown_classification_count,
        "not_latest_count": not_latest_count,
        "latest_data_date": latest_date,
        "backtest_ready": bool(backtest_ready),
        "readiness_summary": readiness_summary,
        "top_issues": top_issues,
        "report_href": "../reports/universe_quality_review.md",
        "strategy_research_report_href": "../reports/etf_rotation_strategy_research.md",
        "readiness_report_href": "../reports/backtest_readiness_report.md",
    }


def _phase4c_data_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "phase4c_data_summary.json")
    if isinstance(payload, dict) and payload:
        return payload
    akshare = _read_json(REPORT_DIR / "akshare_connectivity_check.json")
    status = akshare.get("akshare_status", "not_checked") if isinstance(akshare, dict) else "not_checked"
    return {
        "status": "pending",
        "research_only": True,
        "akshare_status": status,
        "data_provider_design_ready": (REPORT_DIR / "data_provider_design.md").exists(),
        "intelligence_data_plan_ready": (REPORT_DIR / "intelligence_data_source_plan.md").exists(),
        "no_lookahead_rules_ready": (REPORT_DIR / "no_lookahead_data_rules.md").exists(),
        "recommended_next_step": "Run src/data_source_architecture_audit.py and src/akshare_connectivity_check.py.",
        "summary": "Phase 4C data-source audit has not been fully generated yet.",
        "report_href": "../reports/data_source_architecture_audit.md",
        "provider_design_href": "../reports/data_provider_design.md",
        "akshare_report_href": "../reports/akshare_connectivity_check.md",
        "intelligence_plan_href": "../reports/intelligence_data_source_plan.md",
        "no_lookahead_href": "../reports/no_lookahead_data_rules.md",
        "next_step_href": "../reports/phase4c_data_next_step.md",
    }


def _phase4c_tushare_staging_snapshot() -> dict:
    staging = _read_json(REPORT_DIR / "tushare_staging_check.json")
    compare = _read_json(REPORT_DIR / "tushare_baostock_compare.json")
    provider = _read_json(REPORT_DIR / "data_provider_status.json")
    config = _read_json(REPORT_DIR / "tushare_config_check.json")
    token_configured = bool(staging.get("tushare_token_configured", config.get("tushare_token_configured", False)))
    success = int(staging.get("sample_symbols_success", 0) or 0)
    tested = int(staging.get("sample_symbols_tested", 0) or 0)
    failed = int(staging.get("sample_symbols_failed", 0) or 0)
    compare_ready = bool(compare.get("baostock_compare_ready", False))
    candidate = compare.get("candidate_daily_source") or provider.get("candidate_daily_source", "")
    recommended = compare.get("recommended_daily_source") or provider.get("recommended_daily_source", "baostock")
    status = "completed" if staging or compare or provider else "pending"
    return {
        "status": status,
        "research_only": True,
        "tushare_token_configured": token_configured,
        "tushare_staging_success": bool(success > 0),
        "sample_symbols_tested": tested,
        "sample_symbols_success": success,
        "sample_symbols_failed": failed,
        "baostock_compare_ready": compare_ready,
        "recommended_daily_source": recommended,
        "candidate_daily_source": candidate,
        "formal_source_switched": False,
        "summary": staging.get("recommended_next_step") or compare.get("summary") or "Tushare staging dry-run has not been executed.",
        "sample_symbols": staging.get("sample_symbols", []),
        "rows_written": staging.get("rows_written", 0),
        "close_consistent_count": compare.get("close_consistent_count", 0),
        "staging_report_href": "../reports/tushare_staging_check.md",
        "config_report_href": "../reports/tushare_config_check.md",
        "compare_report_href": "../reports/tushare_baostock_compare.md",
        "provider_status_href": "../reports/data_provider_status.md",
        "no_lookahead_href": "../reports/tushare_no_lookahead_check.md",
    }


def _phase4c_alpha_snapshot() -> dict:
    decision = _read_json(REPORT_DIR / "phase4c_alpha_summary.json")
    if isinstance(decision, dict) and decision:
        return {
            **decision,
            "attribution_href": "../reports/v2_underperformance_attribution.md",
            "guardrails_href": "../reports/model_overfit_guardrails.md",
            "regime_href": "../reports/regime_aware_model_research.md",
            "type_href": "../reports/etf_type_aware_model_research.md",
            "alpha_href": "../reports/alpha_factor_enhancement_research.md",
            "comparison_href": "../reports/phase4c_alpha_model_comparison.md",
            "decision_href": "../reports/phase4c_alpha_model_decision.md",
        }
    return {
        "status": "pending",
        "research_only": True,
        "execution_enabled": False,
        "best_candidate": "",
        "candidate_type": "",
        "best_total_return": 0,
        "best_max_drawdown": 0,
        "beat_510300": False,
        "beat_v2_baseline": False,
        "ready_for_shadow": False,
        "ready_for_execution": False,
        "overfit_guardrails_passed": False,
        "summary": "Phase 4C alpha model research has not been generated.",
        "attribution_href": "../reports/v2_underperformance_attribution.md",
        "regime_href": "../reports/regime_aware_model_research.md",
        "type_href": "../reports/etf_type_aware_model_research.md",
        "alpha_href": "../reports/alpha_factor_enhancement_research.md",
        "comparison_href": "../reports/phase4c_alpha_model_comparison.md",
        "decision_href": "../reports/phase4c_alpha_model_decision.md",
    }


def _persistence_breakout_shadow_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "persistence_breakout_shadow_summary.json")
    default = {
        "status": "pending",
        "model_name": "persistence_breakout_v2",
        "research_only": True,
        "execution_enabled": False,
        "paper_trade_engine_enabled": False,
        "real_trade_enabled": False,
        "initial_cash_assumption": 20000,
        "selected_count": 0,
        "selected_symbols": [],
        "overlap_with_original": 0,
        "overlap_with_adjusted": 0,
        "overlap_with_top10_diversified": 0,
        "high_beta_count": 0,
        "data_health_caution_count": 0,
        "tracking_days": 0,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "summary": "persistence_breakout_v2 shadow tracking has not been generated.",
        "signal_report_href": "../reports/persistence_breakout_shadow_signal.md",
        "portfolio_report_href": "../reports/persistence_breakout_shadow_portfolio.md",
        "comparison_report_href": "../reports/model_shadow_comparison.md",
        "observation_rules_href": "../reports/persistence_breakout_shadow_observation_rules.md",
    }
    if isinstance(payload, dict) and payload:
        default.update(payload)
        default["research_only"] = True
        default["execution_enabled"] = False
        default["paper_trade_engine_enabled"] = False
        default["real_trade_enabled"] = False
        default["ready_for_preview"] = False
        default["ready_for_execution"] = False
        default["generated_at"] = _mtime(REPORT_DIR / "persistence_breakout_shadow_summary.json")
    return default


def _missed_opportunity_tracking_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "missed_opportunity_tracker.json")
    default = {
        "status": "pending",
        "research_only": True,
        "execution_enabled": False,
        "model_name": "persistence_breakout_v2",
        "tracking_days": 0,
        "candidate_count": 0,
        "missed_opportunity_count": 0,
        "missed_opportunity_rate": 0,
        "filter_effective_rate": 0,
        "risk_on_empty_signal_count": 0,
        "top_missed_filter_reason": "",
        "ready_to_relax_filters": False,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "summary": "missed opportunity tracking has not been generated.",
        "tracker_report_href": "../reports/missed_opportunity_tracker.md",
        "by_reason_report_href": "../reports/missed_opportunity_by_filter_reason.md",
        "risk_on_report_href": "../reports/risk_on_empty_signal_analysis.md",
        "selected_vs_filtered_href": "../reports/selected_vs_filtered_forward_return.md",
        "observation_rules_href": "../reports/missed_opportunity_observation_rules.md",
    }
    if isinstance(payload, dict) and payload:
        default.update(payload)
        default["research_only"] = True
        default["execution_enabled"] = False
        default["ready_to_relax_filters"] = False
        default["ready_for_preview"] = False
        default["ready_for_execution"] = False
        default["generated_at"] = _mtime(REPORT_DIR / "missed_opportunity_tracker.json")
    return default


def _shadow_observation_weekly_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "shadow_observation_weekly.json")
    default = {
        "status": "pending",
        "research_only": True,
        "execution_enabled": False,
        "evidence_level": "",
        "persistence_empty_signal_days": 0,
        "risk_on_empty_days": 0,
        "missed_opportunity_candidate_count": 0,
        "matured_forward_return_count": 0,
        "missed_opportunity_rate": 0,
        "filter_effective_rate": 0,
        "ready_to_relax_filters": False,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "recommended_action": "",
        "summary": "shadow observation weekly has not been generated.",
        "report_href": "../reports/shadow_observation_weekly.md",
        "csv_href": "../reports/shadow_observation_weekly.csv",
    }
    if isinstance(payload, dict) and payload:
        default.update(payload)
        default["research_only"] = True
        default["execution_enabled"] = False
        default["ready_to_relax_filters"] = False
        default["ready_for_preview"] = False
        default["ready_for_execution"] = False
        default["generated_at"] = _mtime(REPORT_DIR / "shadow_observation_weekly.json")
    return default


def _chatgpt_weekly_packet_snapshot() -> dict:
    path = REPORT_DIR / "chatgpt_weekly_analysis_packet_latest.json"
    payload = _read_json(path)
    default = {
        "status": "missing",
        "as_of_date": "",
        "generated_at": "",
        "summary": {
            "as_of_date": "",
            "generated_at": "",
            "core_conclusions": ["周报分析包尚未生成。"],
            "execution_allowed": False,
            "real_trade_enabled": False,
        },
        "markdown_path": "reports/chatgpt_weekly_analysis_packet_latest.md",
        "json_path": "reports/chatgpt_weekly_analysis_packet_latest.json",
        "markdown_href": "../reports/chatgpt_weekly_analysis_packet_latest.md",
        "json_href": "../reports/chatgpt_weekly_analysis_packet_latest.json",
        "missing_sources": [],
        "safety_boundary": {
            "execution_allowed": False,
            "real_trade_enabled": False,
            "broker_api_enabled": False,
            "paper_trade_engine_changed": False,
        },
    }
    if isinstance(payload, dict) and payload:
        default.update(payload)
        summary = default.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        core = summary.get("core_conclusions") or default.get("core_conclusions") or []
        if not isinstance(core, list):
            core = [str(core)]
        summary.update(
            {
                "as_of_date": default.get("as_of_date", ""),
                "generated_at": default.get("generated_at", ""),
                "core_conclusions": core[:8],
                "execution_allowed": False,
                "real_trade_enabled": False,
            }
        )
        default["summary"] = summary
        default["status"] = "ready"
        default["markdown_href"] = "../reports/chatgpt_weekly_analysis_packet_latest.md"
        default["json_href"] = "../reports/chatgpt_weekly_analysis_packet_latest.json"
        default["generated_at"] = default.get("generated_at") or _mtime(path)
    return default


def _app_control_center_snapshot(
    ranking_v2: dict,
    tushare: dict,
    phase4c_alpha: dict,
    persistence_shadow: dict,
    missed: dict,
    weekly: dict,
    data_sources: dict,
) -> dict:
    shadow_models = [
        name
        for name, active in {
            "top10_diversified_filter_v2": bool(ranking_v2.get("candidate_ready_for_shadow_tracking") or ranking_v2.get("status") == "completed"),
            "persistence_breakout_v2": bool(persistence_shadow.get("status") == "active"),
        }.items()
        if active
    ]
    evidence_level = weekly.get("evidence_level") or "insufficient"
    recommended = weekly.get("recommended_action") or "continue_observation"
    if recommended == "continue_observation":
        action = "Continue observation; do not relax filters; do not enter preview."
    else:
        action = str(recommended)
    return {
        "current_phase": "Shadow Observation Period",
        "formal_model_changed": False,
        "official_model_status": "LOCKED / unchanged",
        "shadow_to_execution": "disabled",
        "execution_enabled": False,
        "real_trade_enabled": False,
        "broker_api_connected": False,
        "paper_trade_engine_changed": False,
        "shadow_writes_paper_trades": False,
        "shadow_writes_paper_positions": False,
        "default_research_initial_cash": ranking_v2.get("initial_cash_main", 20000),
        "shadow_model_count": len(shadow_models),
        "shadow_models": shadow_models,
        "evidence_level": evidence_level,
        "ready_for_execution": False,
        "ready_for_preview": False,
        "ready_to_relax_filters": False,
        "formal_source_switched": bool(tushare.get("formal_source_switched", False)),
        "formal_daily_source": data_sources.get("primary_source") or tushare.get("recommended_daily_source") or "baostock",
        "candidate_daily_source": tushare.get("candidate_daily_source") or "tushare",
        "recommended_action": action,
        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "live_evidence_summary": weekly.get("summary", ""),
        "missed_opportunity_candidate_count": missed.get("candidate_count", 0),
        "matured_forward_return_count": weekly.get("matured_forward_return_count", 0),
        "persistence_selected_count": persistence_shadow.get("selected_count", 0),
        "persistence_latest_signal_date": persistence_shadow.get("latest_signal_date", ""),
        "phase4c_best_candidate": phase4c_alpha.get("best_candidate", ""),
        "safety_badges": [
            "研究专用（Research Only）",
            "影子观察（Shadow Only）",
            "执行禁用（Execution Disabled）",
            "未接券商接口（No Broker API）",
            "不真实交易（No Real Trade）",
        ],
    }


def _exit_rule_research_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "exit_rule_candidates.json")
    families = payload.get("rule_families", []) if isinstance(payload, dict) else []
    type_framework = payload.get("etf_type_parameter_framework", {}) if isinstance(payload, dict) else {}
    status = payload.get("status", "missing") if isinstance(payload, dict) else "missing"
    return {
        "status": status,
        "execution_enabled": bool(payload.get("execution_enabled", False)) if isinstance(payload, dict) else False,
        "rule_families_count": int(len(families)),
        "etf_type_aware": bool(type_framework),
        "volatility_profile_ready": (REPORT_DIR / "etf_volatility_profile.csv").exists(),
        "backtest_required": bool(payload.get("backtest_required", True)) if isinstance(payload, dict) else True,
        "summary": (
            f"退出规则候选库包含 {len(families)} 个规则族；当前为 research_only，"
            "未接入 paper_trade_engine，正式使用前必须回测。"
            if families
            else "exit_rule_candidates.json 尚未生成。"
        ),
        "rule_families": [row.get("family", "") for row in families],
        "report_href": "../reports/etf_rotation_exit_rule_research.md",
        "volatility_report_href": "../reports/etf_volatility_profile.md",
        "candidate_report_href": "../reports/exit_rule_candidates.md",
        "by_type_report_href": "../reports/exit_rule_by_etf_type.md",
        "backtest_design_report_href": "../reports/exit_rule_backtest_design.md",
    }


def _exit_rule_research_panel(review: dict) -> str:
    if not review:
        return "<h3>退出规则研究</h3><div class=\"muted\">暂无 exit rule research 数据。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("规则族", str(review.get("rule_families_count", 0)), "候选参数库"),
        _mini_stat("类型分层", "YES" if review.get("etf_type_aware") else "NO", "ETF type-aware"),
        _mini_stat("波动画像", "READY" if review.get("volatility_profile_ready") else "MISSING", "volatility profile"),
        _mini_stat("执行接入", "NO" if not review.get("execution_enabled") else "YES", "paper_trade_engine unchanged"),
        _mini_stat("回测要求", "YES" if review.get("backtest_required") else "NO", "must validate first"),
    ]
    families = review.get("rule_families", [])
    family_html = "".join(f"<li>{escape(str(item))}</li>" for item in families) or "<li>暂无规则族</li>"
    return (
        "<h3>退出规则研究与参数框架</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + f"<ul>{family_html}</ul>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("report_href", "../reports/etf_rotation_exit_rule_research.md")))}">退出规则调研</a>'
        + f'<a href="{escape(str(review.get("volatility_report_href", "../reports/etf_volatility_profile.md")))}">波动画像</a>'
        + f'<a href="{escape(str(review.get("candidate_report_href", "../reports/exit_rule_candidates.md")))}">候选参数库</a>'
        + f'<a href="{escape(str(review.get("by_type_report_href", "../reports/exit_rule_by_etf_type.md")))}">类型分层参数</a>'
        + f'<a href="{escape(str(review.get("backtest_design_report_href", "../reports/exit_rule_backtest_design.md")))}">回测设计</a>'
        + "</div>"
    )


def _backtest_phase4a_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "backtest_metrics.json")
    summary = _read_csv(REPORT_DIR / "backtest_summary.csv")
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "missing",
            "research_only": True,
            "execution_enabled": False,
            "trade_pool_count": 0,
            "strategies_compared": [],
            "best_strategy": "",
            "best_strategy_total_return": 0,
            "best_strategy_max_drawdown": 0,
            "baseline_510300_return": 0,
            "summary": "Phase 4A backtest has not been generated.",
        }
    strategies = payload.get("strategies", {})
    if not summary.empty and "total_return" in summary.columns:
        temp = summary.copy()
        temp["total_return_num"] = pd.to_numeric(temp["total_return"], errors="coerce")
        best_row = temp.sort_values("total_return_num", ascending=False).head(1).to_dict(orient="records")
        best = best_row[0] if best_row else {}
    else:
        best_name, best_metrics = max(strategies.items(), key=lambda item: _float(item[1].get("total_return")), default=("", {}))
        best = {"strategy": best_name, **best_metrics}
    baseline = strategies.get("buy_and_hold_510300", {})
    best_strategy = str(best.get("strategy", ""))
    best_return = _float(best.get("total_return"))
    best_dd = _float(best.get("max_drawdown"))
    baseline_return = _float(baseline.get("total_return"))
    return {
        "status": "completed",
        "research_only": True,
        "execution_enabled": False,
        "trade_pool_count": int(payload.get("trade_pool_count", 0)),
        "strategies_compared": list(strategies.keys()),
        "best_strategy": best_strategy,
        "best_strategy_total_return": best_return,
        "best_strategy_max_drawdown": best_dd,
        "baseline_510300_return": baseline_return,
        "summary": (
            f"Phase 4A-1 compared {len(strategies)} strategies on {payload.get('trade_pool_count', 0)} ETFs; "
            f"best total return: {best_strategy} ({best_return:.2%}); 510300 baseline: {baseline_return:.2%}."
        ),
        "metrics": strategies,
        "report_href": "../reports/backtest_phase4a_report.md",
        "summary_csv_href": "../reports/backtest_summary.csv",
        "equity_curve_href": "../reports/backtest_equity_curve.csv",
    }


def _backtest_phase4a_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4A-1 回测</h3><div class=\"muted\">暂无回测数据。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("交易池", str(review.get("trade_pool_count", 0)), "filtered trade_pool"),
        _mini_stat("策略数", str(len(review.get("strategies_compared", []))), "strategy comparison"),
        _mini_stat("最佳策略", str(review.get("best_strategy", "N/A")), _pct(review.get("best_strategy_total_return"))),
        _mini_stat("最大回撤", _pct(review.get("best_strategy_max_drawdown")), "best strategy drawdown"),
        _mini_stat("510300", _pct(review.get("baseline_510300_return")), "buy-and-hold baseline"),
    ]
    rows = []
    for name, metrics in (review.get("metrics", {}) or {}).items():
        rows.append(
            "<tr>"
            f"<td>{escape(str(name))}</td>"
            f"<td>{_pct(metrics.get('total_return'))}</td>"
            f"<td>{_pct(metrics.get('max_drawdown'))}</td>"
            f"<td>{escape(str(metrics.get('trade_count', 0)))}</td>"
            f"<td>{escape(str(metrics.get('cost_total', 0)))}</td>"
            "</tr>"
        )
    table = _table(["策略", "总收益", "最大回撤", "交易数", "成本"], rows) if rows else "<div class=\"muted\">暂无策略明细。</div>"
    return (
        "<h3>Phase 4A-1 基础 ETF 轮动回测</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('summary', '')))}</div>"
        + table
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("report_href", "../reports/backtest_phase4a_report.md")))}">回测报告</a>'
        + f'<a href="{escape(str(review.get("summary_csv_href", "../reports/backtest_summary.csv")))}">summary CSV</a>'
        + f'<a href="{escape(str(review.get("equity_curve_href", "../reports/backtest_equity_curve.csv")))}">equity curve</a>'
        + "</div>"
    )


def _backtest_diagnostics_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "backtest_diagnostics_summary.json")
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "missing",
            "research_only": True,
            "execution_enabled": False,
            "capital_sensitivity_ready": False,
            "cost_is_major_issue": False,
            "turnover_is_major_issue": False,
            "ranking_effectiveness_summary": "",
            "expand_pool_now": False,
            "main_failure_reasons": [],
            "next_recommended_actions": [],
        }
    return {
        "status": payload.get("status", "completed"),
        "research_only": True,
        "execution_enabled": False,
        "capital_sensitivity_ready": bool(payload.get("capital_sensitivity_ready", False)),
        "cost_is_major_issue": bool(payload.get("cost_is_major_issue", False)),
        "turnover_is_major_issue": bool(payload.get("turnover_is_major_issue", False)),
        "ranking_effectiveness_summary": payload.get("ranking_effectiveness_summary", ""),
        "expand_pool_now": bool(payload.get("expand_pool_now", False)),
        "main_failure_reasons": payload.get("main_failure_reasons", []),
        "next_recommended_actions": payload.get("next_recommended_actions", []),
        "required_before_expansion": payload.get("required_before_expansion", []),
        "capital_10k_original_return": payload.get("capital_10k_original_return", 0),
        "capital_100k_original_return": payload.get("capital_100k_original_return", 0),
        "report_href": "../reports/backtest_expand_pool_decision.md",
        "consistency_href": "../reports/backtest_consistency_check.md",
        "capital_href": "../reports/backtest_capital_sensitivity.md",
        "cost_href": "../reports/backtest_cost_diagnostics.md",
        "ranking_href": "../reports/backtest_ranking_effectiveness.md",
    }


def _backtest_diagnostics_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4A-1.5 归因诊断</h3><div class=\"muted\">暂无诊断数据。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("扩池", "NO" if not review.get("expand_pool_now") else "YES", "expand_pool_now"),
        _mini_stat("成本问题", "YES" if review.get("cost_is_major_issue") else "NO", "cost drag"),
        _mini_stat("换手问题", "YES" if review.get("turnover_is_major_issue") else "NO", "turnover"),
        _mini_stat("10k original", _pct(review.get("capital_10k_original_return")), "capital sensitivity"),
        _mini_stat("100k original", _pct(review.get("capital_100k_original_return")), "capital sensitivity"),
    ]
    reasons = "".join(f"<li>{escape(str(item))}</li>" for item in review.get("main_failure_reasons", [])) or "<li>暂无主要问题</li>"
    actions = "".join(f"<li>{escape(str(item))}</li>" for item in review.get("next_recommended_actions", [])) or "<li>暂无建议</li>"
    return (
        "<h3>Phase 4A-1.5 基础回测归因诊断</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"muted\" style=\"margin-top:12px;\">{escape(str(review.get('ranking_effectiveness_summary', '')))}</div>"
        + "<h3 style=\"margin-top:14px;\">主要失败原因</h3><ul>"
        + reasons
        + "</ul><h3>下一步建议</h3><ul>"
        + actions
        + "</ul>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("consistency_href", "../reports/backtest_consistency_check.md")))}">一致性检查</a>'
        + f'<a href="{escape(str(review.get("capital_href", "../reports/backtest_capital_sensitivity.md")))}">本金敏感性</a>'
        + f'<a href="{escape(str(review.get("cost_href", "../reports/backtest_cost_diagnostics.md")))}">成本诊断</a>'
        + f'<a href="{escape(str(review.get("ranking_href", "../reports/backtest_ranking_effectiveness.md")))}">ranking 诊断</a>'
        + f'<a href="{escape(str(review.get("report_href", "../reports/backtest_expand_pool_decision.md")))}">扩池判断</a>'
        + "</div>"
    )


def _ranking_signal_research_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "ranking_signal_research_summary.json")
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "missing",
            "research_only": True,
            "execution_enabled": False,
            "top3_not_strong_enough": True,
            "model_enhancement_needed": True,
            "data_freshness_constraint_considered": False,
            "recommended_next_step": "Run python3 src/ranking_factor_diagnostics.py",
            "summary": "Phase 4B ranking signal research has not been generated.",
            "best_factors_10d": [],
            "noisy_factors_10d": [],
            "top3_avg_10d": 0,
            "top10_avg_10d": 0,
            "daily_full_model_replay_needed": True,
            "execution_reality": "",
        }
    return {
        "status": payload.get("status", "completed"),
        "research_only": True,
        "execution_enabled": False,
        "top3_not_strong_enough": bool(payload.get("top3_not_strong_enough", True)),
        "model_enhancement_needed": bool(payload.get("model_enhancement_needed", True)),
        "data_freshness_constraint_considered": bool(payload.get("data_freshness_constraint_considered", True)),
        "recommended_next_step": payload.get("recommended_next_step", ""),
        "summary": payload.get("summary", ""),
        "best_factors_10d": payload.get("best_factors_10d", []),
        "noisy_factors_10d": payload.get("noisy_factors_10d", []),
        "top3_avg_10d": payload.get("top3_avg_10d", 0),
        "top10_avg_10d": payload.get("top10_avg_10d", 0),
        "daily_full_model_replay_needed": bool(payload.get("daily_full_model_replay_needed", True)),
        "execution_reality": payload.get("execution_reality", ""),
        "logic_audit_href": "../reports/ranking_logic_audit.md",
        "factor_diagnostics_href": "../reports/ranking_factor_diagnostics.md",
        "topn_diagnostics_href": "../reports/topn_selection_diagnostics.md",
        "freshness_href": "../reports/data_freshness_execution_reality.md",
        "timing_href": "../reports/backtest_execution_timing_sensitivity.md",
        "model_v2_href": "../reports/ranking_model_v2_design.md",
        "decision_href": "../reports/model_enhancement_decision_report.md",
    }


def _ranking_signal_research_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4B Ranking 信号研究</h3><div class=\"muted\">暂无 ranking signal research 数据。</div>"
    best_factors = review.get("best_factors_10d", []) or []
    noisy_factors = review.get("noisy_factors_10d", []) or []
    best_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('factor', '')))}</td>"
        f"<td class=\"num\">{_score(row.get('rank_ic'))}</td>"
        f"<td class=\"num\">{_pct(row.get('spread'))}</td>"
        f"<td class=\"num\">{_pct(row.get('positive_ic_ratio'))}</td>"
        "</tr>"
        for row in best_factors[:5]
    ) or '<tr><td colspan="4" class="muted">暂无</td></tr>'
    noisy_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('factor', '')))}</td>"
        f"<td class=\"num\">{_score(row.get('rank_ic'))}</td>"
        f"<td class=\"num\">{_pct(row.get('spread'))}</td>"
        f"<td class=\"num\">{_pct(row.get('positive_ic_ratio'))}</td>"
        "</tr>"
        for row in noisy_factors[:5]
    ) or '<tr><td colspan="4" class="muted">暂无</td></tr>'
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("Top3 强度", "WEAK" if review.get("top3_not_strong_enough") else "OK", "vs Top10 candidate"),
        _mini_stat("模型增强", "YES" if review.get("model_enhancement_needed") else "NO", "before execution change"),
        _mini_stat("数据时点", "CONSIDERED" if review.get("data_freshness_constraint_considered") else "MISSING", "confirmed close only"),
        _mini_stat("Top3 10d", _pct(review.get("top3_avg_10d")), "forward proxy"),
        _mini_stat("Top10 10d", _pct(review.get("top10_avg_10d")), "candidate pool proxy"),
    ]
    return (
        "<h3>Phase 4B Ranking Signal Enhancement Research</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"risk-banner\" style=\"margin-top:14px;\"><div class=\"risk-title\">研究结论</div><div>{escape(str(review.get('summary', '')))}</div>"
        + f"<div class=\"muted\">下一步：{escape(str(review.get('recommended_next_step', '')))}</div>"
        + f"<div class=\"muted\">执行约束：{escape(str(review.get('execution_reality', '')))}</div></div>"
        + '<div class="grid two" style="margin-top:14px;">'
        + '<div><h3>10 日较强候选因子</h3>'
        + _table(["factor", "rank_ic", "spread", "positive_ic_ratio"], [best_rows])
        + "</div>"
        + '<div><h3>10 日噪音/弱因子</h3>'
        + _table(["factor", "rank_ic", "spread", "positive_ic_ratio"], [noisy_rows])
        + "</div></div>"
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("logic_audit_href", "../reports/ranking_logic_audit.md")))}">逻辑审计</a>'
        + f'<a href="{escape(str(review.get("factor_diagnostics_href", "../reports/ranking_factor_diagnostics.md")))}">因子诊断</a>'
        + f'<a href="{escape(str(review.get("topn_diagnostics_href", "../reports/topn_selection_diagnostics.md")))}">TopN 诊断</a>'
        + f'<a href="{escape(str(review.get("freshness_href", "../reports/data_freshness_execution_reality.md")))}">数据时点</a>'
        + f'<a href="{escape(str(review.get("model_v2_href", "../reports/ranking_model_v2_design.md")))}">V2 设计</a>'
        + f'<a href="{escape(str(review.get("decision_href", "../reports/model_enhancement_decision_report.md")))}">决策报告</a>'
        + "</div>"
    )


def _ranking_model_v2_backtest_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "ranking_model_v2_metrics.json")
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "missing",
            "research_only": True,
            "execution_enabled": False,
            "initial_cash_main": 20000,
            "mature_model_reference_ready": (REPORT_DIR / "etf_rotation_mature_model_reference.md").exists(),
            "candidates_tested": [],
            "best_candidate": "",
            "best_candidate_total_return": 0,
            "best_candidate_max_drawdown": 0,
            "beat_510300": False,
            "top10_diversified_effective": False,
            "candidate_ready_for_shadow_tracking": False,
            "candidate_ready_for_execution": False,
            "expand_pool_now": False,
            "summary": "Phase 4B-1 ranking_model_v2 backtest has not been generated.",
            "report_href": "../reports/ranking_model_v2_backtest_report.md",
            "decision_href": "../reports/ranking_model_v2_decision_report.md",
        }
    decision = payload.get("decision", {}) if isinstance(payload.get("decision"), dict) else {}
    strategies = payload.get("strategies", {}) if isinstance(payload.get("strategies"), dict) else {}
    best = decision.get("best_candidate", "")
    benchmark = strategies.get("buy_and_hold_510300", {}) if isinstance(strategies.get("buy_and_hold_510300"), dict) else {}
    original = strategies.get("original_baseline_v2", {}) if isinstance(strategies.get("original_baseline_v2"), dict) else {}
    return {
        "status": payload.get("status", "completed"),
        "research_only": True,
        "execution_enabled": False,
        "initial_cash_main": payload.get("initial_cash_main", 20000),
        "initial_cash_comparison": 10000,
        "mature_model_reference_ready": (REPORT_DIR / "etf_rotation_mature_model_reference.md").exists(),
        "candidates_tested": payload.get("candidates_tested", []),
        "trade_pool_count": payload.get("trade_pool_count", 0),
        "backtest_start_date": payload.get("backtest_start_date", ""),
        "backtest_end_date": payload.get("backtest_end_date", ""),
        "total_trading_days": payload.get("total_trading_days", 0),
        "execution_price_assumption": payload.get("execution_price_assumption", ""),
        "best_candidate": best,
        "best_candidate_total_return": _float(decision.get("best_candidate_total_return")),
        "best_candidate_max_drawdown": _float(decision.get("best_candidate_max_drawdown")),
        "best_candidate_calmar": _float(decision.get("best_candidate_calmar")),
        "best_candidate_trade_count": decision.get("best_candidate_trade_count", 0),
        "beat_510300": bool(decision.get("beat_510300", False)),
        "beat_original": bool(decision.get("beat_original", False)),
        "reduce_drawdown_vs_original": bool(decision.get("reduce_drawdown_vs_original", False)),
        "top10_diversified_effective": bool(decision.get("top10_diversified_effective", False)),
        "candidate_ready_for_shadow_tracking": bool(decision.get("candidate_ready_for_shadow_tracking", False)),
        "candidate_ready_for_execution": False,
        "expand_pool_now": False,
        "strategy_quality_label": decision.get("strategy_quality_label", payload.get("strategy_quality_label", "low_drawdown_candidate_not_alpha_proven")),
        "benchmark_510300_return": _float(benchmark.get("total_return")),
        "benchmark_510300_max_drawdown": _float(benchmark.get("max_drawdown")),
        "original_return": _float(original.get("total_return")),
        "original_max_drawdown": _float(original.get("max_drawdown")),
        "summary": decision.get(
            "strategy_quality_summary",
            payload.get(
                "summary",
                "v2 improves drawdown and turnover, but return does not beat 510300; keep in shadow tracking only.",
            ),
        ),
        "next_step": decision.get("next_step", ""),
        "report_href": payload.get("report_href", "../reports/ranking_model_v2_backtest_report.md"),
        "decision_href": payload.get("decision_href", "../reports/ranking_model_v2_decision_report.md"),
        "summary_csv_href": payload.get("summary_csv_href", "../reports/ranking_model_v2_summary.csv"),
        "top10_analysis_href": payload.get("top10_analysis_href", "../reports/top10_candidate_filter_analysis.md"),
        "reference_href": "../reports/etf_rotation_mature_model_reference.md",
        "execution_assumption_href": "../reports/ranking_model_v2_execution_assumption.md",
        "strategies": strategies,
    }


def _ranking_model_v2_backtest_panel(review: dict) -> str:
    if not review:
        return "<h3>Phase 4B-1 Ranking Model v2 回测</h3><div class=\"muted\">暂无 ranking_model_v2 回测数据。</div>"
    stats = [
        _mini_stat("状态", str(review.get("status", "N/A")), "research only"),
        _mini_stat("交易池", str(review.get("trade_pool_count", 0)), "backtest_trade_pool"),
        _mini_stat("主资金", _money(review.get("initial_cash_main", 20000)), "research/backtest basis"),
        _mini_stat("区间", f"{review.get('backtest_start_date', 'N/A')} → {review.get('backtest_end_date', 'N/A')}", str(review.get("execution_price_assumption", ""))),
        _mini_stat("最佳候选", str(review.get("best_candidate", "N/A")), _pct(review.get("best_candidate_total_return"))),
        _mini_stat("最大回撤", _pct(review.get("best_candidate_max_drawdown")), f"Calmar {_number(review.get('best_candidate_calmar'))}"),
        _mini_stat("510300", _pct(review.get("benchmark_510300_return")), "buy-and-hold baseline"),
        _mini_stat("Top10 Filter", "有效" if review.get("top10_diversified_effective") else "待验证", "diversified candidate"),
        _mini_stat("Shadow", "YES" if review.get("candidate_ready_for_shadow_tracking") else "NO", "execution=false"),
        _mini_stat("扩池", "NO" if not review.get("expand_pool_now") else "YES", "Phase 4B-1 不扩池"),
    ]
    rows = []
    for name, metrics in (review.get("strategies", {}) or {}).items():
        rows.append(
            "<tr>"
            f"<td>{escape(str(name))}</td>"
            f"<td>{_pct(metrics.get('total_return'))}</td>"
            f"<td>{_pct(metrics.get('max_drawdown'))}</td>"
            f"<td>{_number(metrics.get('calmar'))}</td>"
            f"<td>{escape(str(metrics.get('trade_count', 0)))}</td>"
            f"<td>{_number(metrics.get('turnover'))}</td>"
            "</tr>"
        )
    table = _table(["策略", "收益", "最大回撤", "Calmar", "交易数", "换手"], rows) if rows else "<div class=\"muted\">暂无策略明细。</div>"
    return (
        "<h3>Phase 4B-1 Benchmark-Informed Ranking Model v2</h3>"
        + '<div class="grid three">'
        + "".join(stats)
        + "</div>"
        + f"<div class=\"risk-banner\" style=\"margin-top:14px;\"><div class=\"risk-title\">研究结论</div><div>{escape(str(review.get('summary', '')))}</div>"
        + f"<div class=\"muted\">质量标签：{escape(str(review.get('strategy_quality_label', 'low_drawdown_candidate_not_alpha_proven')))}</div>"
        + "<div class=\"muted\">收益率仍不够理想，未跑赢 510300；只允许 shadow tracking，不允许接入执行层。</div>"
        + f"<div class=\"muted\">下一步：{escape(str(review.get('next_step', '')))}</div>"
        + "<div class=\"muted\">当前只允许进入 shadow tracking 候选，不接入 paper_trade_engine。</div></div>"
        + table
        + '<div class="links" style="margin-top:12px;">'
        + f'<a href="{escape(str(review.get("reference_href", "../reports/etf_rotation_mature_model_reference.md")))}">成熟框架参考</a>'
        + f'<a href="{escape(str(review.get("execution_assumption_href", "../reports/ranking_model_v2_execution_assumption.md")))}">执行口径</a>'
        + f'<a href="{escape(str(review.get("report_href", "../reports/ranking_model_v2_backtest_report.md")))}">回测报告</a>'
        + f'<a href="{escape(str(review.get("decision_href", "../reports/ranking_model_v2_decision_report.md")))}">决策报告</a>'
        + f'<a href="{escape(str(review.get("summary_csv_href", "../reports/ranking_model_v2_summary.csv")))}">summary CSV</a>'
        + f'<a href="{escape(str(review.get("top10_analysis_href", "../reports/top10_candidate_filter_analysis.md")))}">Top10 过滤分析</a>'
        + "</div>"
    )


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "y", "ok"}:
        return True
    if text in {"0", "false", "no", "n", "", "none", "nan"}:
        return False
    return bool(value)


def _research_quality_snapshot() -> dict:
    payload = _read_json(REPORT_DIR / "model_research_quality_review.json")
    return payload if isinstance(payload, dict) else {}


def _execution_layer_integration_snapshot(plan_rows: list[dict], market_state: dict, portfolio_exposure: dict, research_quality: dict) -> dict:
    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    classification = _read_classification_csv()
    class_map = classification.set_index(classification["symbol"].astype(str)).to_dict(orient="index") if not classification.empty and "symbol" in classification.columns else {}
    summary = portfolio_exposure.get("summary", {})
    warnings = portfolio_exposure.get("warnings", [])
    current_position_pct = _float(summary.get("position_ratio"), _float(market_state.get("position_ratio")))
    low = _float(market_state.get("suggested_total_position_min"), float("nan"))
    high = _float(market_state.get("suggested_total_position_max"), float("nan"))
    if pd.isna(low) or pd.isna(high):
        suggested = "N/A"
        alignment = "unknown"
    else:
        suggested = f"{low:.0%}-{high:.0%}"
        alignment = "below_suggested_range" if current_position_pct < low else "above_suggested_range" if current_position_pct > high else "aligned"

    type_rows = []
    for row in positions.to_dict(orient="records"):
        symbol = str(row.get("symbol", ""))
        meta = class_map.get(symbol, {})
        holding_days = _int(row.get("holding_days"), 0)
        max_days = _int(meta.get("max_holding_days", row.get("max_holding_days", 0)), 0)
        status = "OVER_PROFILE" if max_days and holding_days > max_days else "IN_PROFILE" if max_days else "N/A"
        type_rows.append(
            {
                "symbol": symbol,
                "name": row.get("name", meta.get("name", symbol)),
                "etf_type": meta.get("etf_type", row.get("etf_type", "")),
                "risk_profile": meta.get("risk_profile", row.get("risk_profile", "")),
                "holding_profile": meta.get("holding_profile", row.get("holding_profile", "")),
                "holding_days": holding_days,
                "max_holding_days": max_days,
                "stop_loss_pct": meta.get("stop_loss_pct", row.get("stop_loss_pct", "")),
                "distance_to_stop_pct": row.get("distance_to_stop_pct", ""),
                "classification_reason": meta.get("classification_reason", row.get("classification_reason", "")),
                "holding_period_status": status,
                "display_only": True,
            }
        )

    plan_suggestions = []
    for row in plan_rows:
        for key in ["portfolio_balance_suggestion", "concentration_warning", "buy_candidate_context"]:
            value = str(row.get(key, "")).strip()
            if value and value not in plan_suggestions:
                plan_suggestions.append(value)

    confidence = {
        "holding_period": research_quality.get("holding_period", {}).get("quality", "MEDIUM"),
        "exit_rule": research_quality.get("exit_rule", {}).get("quality", "LOW_MEDIUM"),
        "parameter_sweep": research_quality.get("parameter_sweep", {}).get("quality", "LOW_MEDIUM"),
        "market_state": research_quality.get("market_state", {}).get("quality", "MEDIUM"),
        "etf_type": "light_integration_allowed",
        "portfolio_exposure": "prompt_only_allowed",
    }
    return {
        "version": "phase2c_execution_layer_light_integration_v1",
        "integrated": [
            "etf_type -> plan/explanation/dashboard",
            "max_holding_days -> review/display only",
            "stop_loss_pct -> review/display only",
            "market_state -> plan/dashboard display",
            "portfolio_exposure -> balance/concentration prompt",
        ],
        "display_only": [
            "market_state suggested position does not change amount",
            "portfolio_exposure does not block buys or force sells",
            "max_holding_days does not trigger automatic sell by itself in this phase",
        ],
        "not_integrated": [
            "dynamic max_holdings",
            "market_state target-position execution",
            "portfolio_exposure hard block",
            "news sentiment BUY",
        ],
        "use_market_state_position": PAPER_USE_MARKET_STATE_POSITION,
        "market_state_vs_position": {
            "market_state": market_state.get("market_state", "N/A"),
            "market_score": market_state.get("market_score", ""),
            "suggested_position_pct": suggested,
            "current_position_pct": current_position_pct,
            "position_alignment": alignment,
        },
        "etf_type_risk": type_rows,
        "portfolio_balance": {
            "portfolio_exposure_status": summary.get("overall_status", "N/A"),
            "warnings": warnings,
            "suggestions": plan_suggestions,
        },
        "research_confidence": confidence,
        "paper_trade_plan_fields_present": sorted({key for row in plan_rows for key in row.keys()}),
    }


def _research_csv_summary(path: Path, score_col: str, descending: bool) -> dict:
    df = _read_csv(path)
    if df.empty:
        return {"row_count": 0, "best_rows": [], "best_note": "WAITING"}
    df_work = df.copy()
    if score_col in df_work.columns:
        df_work["_score"] = pd.to_numeric(df_work[score_col], errors="coerce")
        df_work = df_work.dropna(subset=["_score"]).sort_values("_score", ascending=not descending)
    best_rows = df_work.head(5).drop(columns=["_score"], errors="ignore").to_dict(orient="records")
    best_note = "research_only"
    if best_rows:
        first = best_rows[0]
        if "symbol" in first:
            best_note = f"{first.get('symbol')} / {first.get(score_col, 'N/A')}"
        elif "max_holdings" in first:
            best_note = f"holdings={first.get('max_holdings')} / {first.get(score_col, 'N/A')}"
    return {"row_count": int(len(df)), "best_rows": best_rows, "best_note": best_note}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def _read_json(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _maybe_float(value: object) -> float | str:
    if value in ("", None):
        return "N/A"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(numeric):
        return "N/A"
    return numeric


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _int(value: object, fallback: int = 0) -> int:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return numeric


def _money(value: object) -> str:
    return f"{_float(value):,.2f}"


def _signed_money(value: object) -> str:
    numeric = _float(value)
    sign = "+" if numeric > 0 else ""
    return f"{sign}{numeric:,.2f}"


def _number(value: object) -> str:
    numeric = _float(value)
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    if value in ("", None):
        return "N/A"
    return f"{_float(value):.2%}"


def _score(value: object) -> str:
    if value in ("", None, "N/A"):
        return "N/A"
    return f"{_float(value):.1f}"


def _mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return pd.Timestamp.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
