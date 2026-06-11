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
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from config import (  # type: ignore
        BROKER_API_ENABLED,
        PAPER_AUTO_EXECUTE,
        PAPER_DEFAULT_MARKET_STATE,
        PAPER_INITIAL_CASH,
        PAPER_MAX_HOLDINGS,
        PAPER_MAX_SINGLE_POSITION_PCT,
        PAPER_MODE,
        PAPER_TARGET_POSITION_NEUTRAL,
        REAL_TRADE_ENABLED,
    )
except Exception:
    BROKER_API_ENABLED = False
    PAPER_AUTO_EXECUTE = False
    PAPER_DEFAULT_MARKET_STATE = "neutral"
    PAPER_INITIAL_CASH = 10_000.0
    PAPER_MAX_HOLDINGS = 3
    PAPER_MAX_SINGLE_POSITION_PCT = 0.20
    PAPER_MODE = "rule_validation"
    PAPER_TARGET_POSITION_NEUTRAL = 0.30
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
    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    trades = _read_csv(DATA_DIR / "paper_trades.csv")
    watchlist = _read_csv(PROJECT_ROOT / "watchlist.csv")
    candidates = _read_csv(DATA_DIR / "etf_pool_expansion_candidates.csv")
    classification = _read_csv(DATA_DIR / "etf_type_classification.csv")
    ranking_rows = _read_buy_ranking()
    sell_review_rows = _read_csv(REPORT_DIR / "sell_signal_review.csv").to_dict(orient="records")
    paper_trade_plan_rows = _read_csv(PAPER_TRADE_PLAN_FILE).to_dict(orient="records")
    health_rows, health_summary = _read_health_report()
    latest_data_date = _latest_data_date()
    engine_state = _latest_engine_state(_read_json(ENGINE_STATE_FILE), latest_data_date)

    meta = _build_meta_map(watchlist, candidates, classification)
    enriched_positions = _enrich_positions(positions, meta, ranking_rows, health_rows)
    summary = _paper_summary(enriched_positions, trades)
    paper_trade_engine = _paper_trade_engine_snapshot(engine_state, paper_trade_plan_rows, summary)
    exposure = _group_exposure(enriched_positions)
    classification_summary = _classification_summary(classification, enriched_positions)
    failed_counts = _failed_counts()
    automation_nodes = _automation_nodes()
    risk_alerts = _risk_alerts(enriched_positions, failed_counts)
    console = _console_status(summary, risk_alerts, automation_nodes, health_summary)
    review = _review_snapshot()
    dashboard_links = _dashboard_links()
    link_health = _link_health(dashboard_links)
    dashboard_sources = _dashboard_sources()

    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_data_date": latest_data_date,
        "console": console,
        "paper_summary": summary,
        "risk_alerts": risk_alerts,
        "positions": enriched_positions,
        "trades": trades.to_dict(orient="records"),
        "buy_ranking": ranking_rows,
        "sell_review": sell_review_rows,
        "paper_trade_engine": paper_trade_engine,
        "paper_trade_plan": paper_trade_plan_rows,
        "exposure": exposure,
        "classification_summary": classification_summary,
        "health_summary": health_summary,
        "failed_counts": failed_counts,
        "automation_nodes": automation_nodes,
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
      --bg: #f4f6f9;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #667085;
      --line: #d8dee8;
      --blue: #1455d9;
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
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      font-variant-numeric: tabular-nums;
    }}
    header {{
      background: rgba(255,255,255,.94);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(14px);
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
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(16,24,40,.06);
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
      background: #111827;
      color: #f8fafc;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: 0 22px 60px rgba(15,23,42,.22);
      padding: 20px;
      margin-bottom: 18px;
    }}
    .control-shell .muted, .control-shell .metric-sub {{ color: #a8b3c7; }}
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
        <span class="badge warn">L2 只读边界</span>
      </div>
    </div>
  </header>
  <nav class="quick-nav" aria-label="dashboard sections">
    <div class="quick-nav-inner">
      <a href="#overview">Overview</a>
      <a href="#paper-trade-engine">Paper Engine</a>
      <a href="#portfolio">Portfolio</a>
      <a href="#sell-review">Sell Review</a>
      <a href="#ranking">BUY Ranking</a>
      <a href="#risk">Risk</a>
      <a href="#automation">Automation</a>
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

    <section id="portfolio">
      <div class="section-head">
        <div>
          <h2>当前持仓 Portfolio</h2>
          <div class="hint">决策字段优先：信号是否有效、距离止损、风险标签和动作建议。</div>
        </div>
      </div>
      {_portfolio_table(data.get("positions", []))}
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
          <div class="hint">只读展示 ETF 类型、建议持有周期、退出敏感度和新闻情绪占位，不改变交易规则。</div>
        </div>
      </div>
      <div class="grid two">
        <div class="panel">{_research_layer_panel(data)}</div>
        <div class="panel">{_classification_panel(data.get("classification_summary", {}))}</div>
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
              {_tape("模拟交易引擎", engine.get("status", "WAITING"))}
              {_tape("Top BUY", f"{top_buy.get('symbol','N/A')} / {_score(top_buy.get('rank_score'))}")}
              {_tape("卖出复核", f"{review_flags} 项需复核")}
              {_tape("链接状态", f"{link_health.get('valid', 0)}/{link_health.get('total', 0)} OK")}
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
        _mini_stat("执行状态", str(status), f"dry_run={state.get('dry_run', 'N/A')}"),
        _mini_stat("买入/卖出", f"{state.get('buy_count', 0)} / {state.get('sell_count', 0)}", "本地模拟数量"),
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
        + f'<div>auto_execute={escape(str(limits.get("auto_execute", PAPER_AUTO_EXECUTE)))}；{escape(disabled)}；单只上限 {_pct(limits.get("max_single_position_pct", PAPER_MAX_SINGLE_POSITION_PCT))}；目标仓位 {_pct(limits.get("target_position_pct", PAPER_TARGET_POSITION_NEUTRAL))}。</div>'
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
            f"<td>{escape(str(row.get('date','')))}</td>"
            f"<td><b>{escape(str(row.get('symbol','')))}</b><div class=\"muted\">{escape(str(row.get('name','')))}</div></td>"
            f"<td>{escape(str(row.get('action','')))}</td>"
            f"<td>{_tag(status, _tag_class(status))}</td>"
            f"<td class=\"num\">{_number(row.get('price'))}</td>"
            f"<td class=\"num\">{_number(row.get('quantity'))}</td>"
            f"<td class=\"num\">{_money(row.get('amount'))}</td>"
            f"<td><div class=\"reason\">{escape(str(row.get('reason','')))[:180]}</div></td>"
            "</tr>"
        )
    return _table(["日期", "ETF", "动作", "状态", "价格", "数量", "金额", "原因"], body)


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
            f"<td>{escape(str(row.get('holding_cycle_status','N/A')))}<div class=\"muted\">持仓 {escape(str(row.get('holding_days','N/A')))} / {escape(str(row.get('holding_profile','N/A')))} 天</div></td>"
            f"<td class=\"num\">{_money(row.get('market_value'))}</td>"
            f"<td class=\"num\">{_pct(row.get('position_ratio'))}</td>"
            f"<td class=\"num\">{_number(row.get('entry_price'))}</td>"
            f"<td class=\"num\">{_number(row.get('current_price'))}</td>"
            f"<td class=\"num {pnl_cls}\">{_money(row.get('unrealized_pnl'))}</td>"
            f"<td class=\"num {pnl_cls}\">{_pct(row.get('unrealized_pnl_pct'))}</td>"
            f"<td>{escape(str(row.get('buy_signal','N/A')))}</td>"
            f"<td>{escape(str(row.get('current_signal','N/A')))}</td>"
            f"<td>{_tag(row.get('short_swing_weakening'), _tag_class(row.get('short_swing_weakening')))}<div class=\"muted\">rank trend: {escape(str(row.get('rank_score_trend','N/A')))}</div></td>"
            f"<td>{_tag(row.get('signal_status'), status_cls)}</td>"
            f"<td class=\"num\">{_number(row.get('stop_loss'))}</td>"
            f"<td class=\"num\">{_pct(row.get('stop_distance_pct'))}</td>"
            f"<td>{_tag(row.get('risk_tag'), risk_cls)}</td>"
            f"<td>{_tag(row.get('sentiment_status'), _tag_class(row.get('sentiment_status')))}</td>"
            f"<td>{_tag(row.get('action_suggestion'), action_cls)}<div class=\"reason\">{escape(str(row.get('research_note','') or row.get('reason','')))[:150]}</div></td>"
            "</tr>"
        )
    headers = ["ETF", "名称", "group", "ETF 类型", "持仓周期", "仓位金额", "仓位比例", "成本价", "最新价", "浮盈亏", "浮盈亏率", "买入信号", "当前信号", "短周期/排名", "信号状态", "止损价", "距离止损", "风险标签", "情绪占位", "动作建议"]
    return _table(headers, body)


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
    node_errors = sum(1 for node in nodes if str(node.get("status", "")).upper() in {"ERROR", "FAILED"})
    node_waiting = sum(1 for node in nodes if str(node.get("status", "")).upper() == "WAITING")
    cells = [
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
        + "<div>看板为单文件静态 HTML，不依赖 Streamlit 或本地服务；每日报告生成后自动刷新 dashboard_data.json 和 index.html。</div>"
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
        + '<a href="../reports/etf_type_classification_report.md">类型报告</a>'
        + '<a href="../reports/holding_period_research_report.md">持有周期研究</a>'
        + '<a href="../reports/exit_rule_research_report.md">退出规则研究</a>'
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


def _enrich_positions(positions: pd.DataFrame, meta: dict[str, dict], ranking: list[dict], health: dict[str, dict]) -> list[dict]:
    ranking_map = {str(row.get("symbol")): row for row in ranking}
    result = []
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", "")).strip()
        rank = ranking_map.get(symbol, {})
        meta_row = meta.get(symbol, {})
        health_row = health.get(symbol, {})
        current_price = _float(item.get("current_price"), _float(item.get("entry_price")))
        stop_loss = _float(item.get("stop_loss"))
        market_value = _float(item.get("market_value"), current_price * _float(item.get("quantity")))
        pnl = _float(item.get("unrealized_pnl"), market_value - _float(item.get("cost")))
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


def _console_status(summary: dict, alerts: list[dict], nodes: list[dict], health_summary: dict) -> dict:
    severe = any(item.get("severity") == "danger" for item in alerts)
    waiting_data = health_summary.get("缺失") not in ("", "0", 0, None)
    midday = next((node for node in nodes if node.get("node") == "midday_check"), {})
    if severe:
        conclusion = "RISK_REDUCE"
        reason = "存在止损或严重风险触发，需要人工复核减仓。"
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
    status = "ERROR" if severe else "CAUTION" if alerts or waiting_data else "NORMAL"
    return {
        "today_conclusion": conclusion,
        "decision_reason": reason,
        "system_status": status,
        "system_badge_class": "danger" if status == "ERROR" else "warn" if status == "CAUTION" else "ok",
        "risk_summary": f"{len(alerts)} 项需复核" if alerts else "无风险触发",
    }


def _automation_nodes() -> list[dict]:
    now = pd.Timestamp.now()
    specs = [
        ("catchup_check", "login", "开机/登录补偿", "reports/catchup_scheduler_status.md", ""),
        ("open_check", "09:40", "开盘风险观察", "reports/open_check.md", "open_check.json"),
        ("midday_check", "12:40", "午盘模拟执行检查", "reports/midday_check.md", "midday_check.json"),
        ("afternoon_open_check", "13:10", "下午开盘复核", "reports/afternoon_open_check.md", "afternoon_open_check.json"),
        ("paper_trade_engine", "15:25", "模拟交易引擎", "reports/paper_trade_engine_report.md", ""),
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
        rows.append(
            {
                "node": node,
                "time_label": time_label,
                "title": title,
                "status": status,
                "conclusion": payload.get("conclusion", "见报告" if exists else "等待生成"),
                "generated_at": payload.get("generated_at", _mtime(report_path)),
                "report_href": "../" + report,
            }
        )
    return rows


def _review_snapshot() -> dict:
    specs = [
        ("每日轻量滚动回测", REPORT_DIR / "daily_rolling_backtest.md", "../reports/daily_rolling_backtest.md"),
        ("周度完整复盘", REPORT_DIR / "weekly_full_review.md", "../reports/weekly_full_review.md"),
        ("月度模型复盘", REPORT_DIR / "monthly_model_review.md", "../reports/monthly_model_review.md"),
        ("因子分析", REPORT_DIR / "factor_analysis_report.md", "../reports/factor_analysis_report.md"),
        ("模型研究", REPORT_DIR / "model_research_report.md", "../reports/model_research_report.md"),
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


def _dashboard_links() -> list[dict]:
    specs = [
        ("控制台快照", "data", REPORT_DIR / "dashboard_data.json", "../reports/dashboard_data.json"),
        ("每日最简摘要", "daily", REPORT_DIR / "latest_brief.md", "../reports/latest_brief.md"),
        ("模拟盘持仓", "paper", REPORT_DIR / "latest_paper_portfolio.md", "../reports/latest_paper_portfolio.md"),
        ("BUY Ranking", "signal", REPORT_DIR / "buy_signal_ranking.md", "../reports/buy_signal_ranking.md"),
        ("卖出复核", "risk", REPORT_DIR / "sell_signal_review.md", "../reports/sell_signal_review.md"),
        ("模拟交易计划", "paper", REPORT_DIR / "paper_trade_plan.md", "../reports/paper_trade_plan.md"),
        ("模拟交易引擎", "paper", REPORT_DIR / "paper_trade_engine_report.md", "../reports/paper_trade_engine_report.md"),
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


def _latest_engine_state(state: dict, latest_data_date: str) -> dict:
    if not isinstance(state, dict) or not state:
        return {}
    if latest_data_date in state and isinstance(state.get(latest_data_date), dict):
        return state[latest_data_date]
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


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


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
