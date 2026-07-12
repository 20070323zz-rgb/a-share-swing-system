import {
  ArrowRight,
  BarChart3,
  BellRing,
  BookOpenCheck,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Database,
  FlaskConical,
  Gauge,
  Layers3,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
  WalletCards,
  Zap
} from "lucide-react";
import Sparkline from "../components/Sparkline.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { money, pct, score, text } from "../format.js";

function statusCn(value) {
  const raw = String(value ?? "").toLowerCase();
  const map = {
    insufficient: "证据不足",
    normal: "正常",
    caution: "观察",
    error: "异常",
    generated: "已生成",
    active: "观察中",
    success: "已完成",
    failed: "失败",
    running: "运行中",
    pending: "等待回收"
  };
  return map[raw] || text(value, "暂无数据");
}

function metricTone(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number === 0) return "neutral";
  return number > 0 ? "positive" : "negative";
}

function MetricCard({ icon: Icon, label, value, note, tone = "blue" }) {
  return (
    <article className={`v2-metric-card ${tone}`}>
      <div className="v2-metric-icon"><Icon size={18} strokeWidth={1.9} aria-hidden="true" /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
    </article>
  );
}

function JourneyItem({ icon: Icon, label, title, note, state = "ready" }) {
  return (
    <div className={`journey-item ${state}`}>
      <div className="journey-icon"><Icon size={17} aria-hidden="true" /></div>
      <div>
        <span>{label}</span>
        <strong>{title}</strong>
        <small>{note}</small>
      </div>
      {state === "ready" ? <CheckCircle2 size={17} aria-label="就绪" /> : <Clock3 size={17} aria-label="等待" />}
    </div>
  );
}

function EmptyState({ children }) {
  return <div className="v2-empty">{children}</div>;
}

export default function Home({ status, portfolio, signals, research, dataHealth, safety, taskStatus, onNavigate, onRun }) {
  const performance = portfolio?.performance || {};
  const summary = portfolio?.summary || {};
  const curve = portfolio?.equity_curve || [];
  const equityMeta = portfolio?.equity_curve_meta || {};
  const positions = portfolio?.positions || [];
  const signalRows = signals?.buy_ranking || [];
  const taskHistory = taskStatus?.history || [];
  const latestTask = taskStatus?.latest_task || {};
  const weekly = research?.shadow_observation_weekly || {};
  const styleFit = research?.style_regime_fit || {};
  const totalEquity = performance.current_total_equity ?? summary.total_equity ?? status?.total_equity;
  const totalPnl = performance.total_pnl_amount ?? summary.total_pnl;
  const totalReturn = performance.total_return_pct;
  const positionRatio = summary.position_ratio ?? performance.current_position_ratio ?? status?.position_pct ?? 0;
  const latestDate = dataHealth?.latest_data_date || status?.latest_data_date;
  const curveDate = equityMeta.curve_end_date || equityMeta.end_date || curve[curve.length - 1]?.date;
  const curveFresh = equityMeta.freshness_status !== "stale" && curveDate && (!latestDate || curveDate >= latestDate);
  const systemState = String(status?.system_status || "NORMAL").toUpperCase();
  const systemTitle = systemState === "ERROR" ? "数据链路需要处理" : systemState === "CAUTION" ? "进入谨慎观察模式" : "研究环境已经就绪";
  const systemNote = status?.today_summary || "资产、信号、研究与数据状态已汇总完成。";

  const reviewCount = Number(status?.review_summary?.reduce_candidate_count ?? status?.reduce_candidate_count ?? 0);
  const profitCount = Number(status?.profit_protection_summary?.profit_protection_review_count ?? status?.profit_protection_review_count ?? 0);
  const highBetaCount = Number(status?.high_beta_risk_summary?.high_beta_position_count ?? status?.high_beta_position_count ?? 0);
  const alertCount = reviewCount + profitCount + highBetaCount;
  const dataHealthy = !String(dataHealth?.status || status?.data_update_status || "").toLowerCase().match(/error|fail|stale/);
  const safetyHealthy = !safety?.real_trade_enabled && !safety?.broker_api_enabled && !safety?.real_order_buttons_enabled;
  const signalHealthy = signalRows.length > 0;
  const portfolioHealthy = positions.length > 0 || Number(totalEquity || 0) > 0;
  const healthChecks = [dataHealthy, safetyHealthy, signalHealthy, portfolioHealthy];
  const readyCount = healthChecks.filter(Boolean).length;
  const readiness = Math.round((readyCount / healthChecks.length) * 100);
  const dataTaskUpToDate = latestTask.data_update_status === "up_to_date";

  const broadBase = status?.broad_base_balance_summary || {};
  const researchCards = [
    {
      label: "影子观察",
      value: statusCn(weekly.status),
      note: `证据：${statusCn(weekly.evidence_level)}`,
      icon: FlaskConical,
      tone: weekly.evidence_level === "insufficient" ? "warning" : "success"
    },
    {
      label: "风格适配",
      value: statusCn(styleFit.status),
      note: "研究层，不影响排名",
      icon: Layers3,
      tone: "blue"
    },
    {
      label: "风险画像",
      value: statusCn(research?.etf_risk_profile?.status),
      note: `${research?.etf_risk_profile?.row_count ?? 0} 只 ETF`,
      icon: Gauge,
      tone: "violet"
    }
  ];

  return (
    <main className="page-grid app-home v2-home">
      <section className={`v2-hero ${systemState.toLowerCase()}`}>
        <div className="v2-hero-copy">
          <div className="v2-hero-kicker"><Sparkles size={15} aria-hidden="true" /> 今日研究工作台 · 数据截至 {text(latestDate, "等待更新")}</div>
          <h2>{systemTitle}</h2>
          <p>{systemNote}</p>
          <div className="v2-hero-actions">
            <Button onClick={() => onRun?.("backfill_etf_data")} type="button"><RefreshCw size={16} aria-hidden="true" />{dataTaskUpToDate ? "再次检查数据" : "检查并补齐 ETF 数据"}</Button>
            <Button variant="secondary" onClick={() => onNavigate?.("signals")} type="button">查看信号雷达<ArrowRight size={15} aria-hidden="true" /></Button>
          </div>
          {latestTask.data_update_status ? <div className="v2-data-proof"><Database size={14} aria-hidden="true" />上次检查：{latestTask.data_update_up_to_date_count ?? 0}/{latestTask.data_update_processed_symbols ?? 0} 只已更新 · 价格日 {latestTask.data_update_latest_local_date || latestDate || "暂无"} · 新增 {latestTask.data_update_added_rows ?? 0} 行</div> : null}
          <div className="v2-hero-boundary"><ShieldCheck size={15} aria-hidden="true" />只更新本地研究数据和报告，不连接券商，不真实交易。</div>
        </div>
        <div className="v2-readiness-card">
          <div className="readiness-ring" style={{ "--readiness-angle": `${readiness * 3.6}deg` }}>
            <div><strong>{readiness}%</strong><span>工作台就绪</span></div>
          </div>
          <div className="readiness-list">
            <span className={dataHealthy ? "ready" : "wait"}>数据链路 <b>{dataHealthy ? "就绪" : "待更新"}</b></span>
            <span className={signalHealthy ? "ready" : "wait"}>信号排名 <b>{signalHealthy ? "已生成" : "等待"}</b></span>
            <span className={portfolioHealthy ? "ready" : "wait"}>模拟仓 <b>{portfolioHealthy ? "可复盘" : "暂无"}</b></span>
            <span className={safetyHealthy ? "ready" : "wait"}>安全边界 <b>{safetyHealthy ? "已锁定" : "需复核"}</b></span>
          </div>
        </div>
      </section>

      <section className="v2-kpi-grid" aria-label="核心指标">
        <MetricCard icon={WalletCards} label="模拟总资产" value={money(totalEquity)} note={`仓位 ${pct(positionRatio)} · 价格日 ${text(latestDate, "暂无")}`} tone="blue" />
        <MetricCard icon={TrendingUp} label="累计收益" value={pct(totalReturn)} note={`累计盈亏 ${money(totalPnl)} · 价格日 ${text(latestDate, "暂无")}`} tone={metricTone(totalReturn)} />
        <MetricCard icon={Target} label="信号候选" value={`${signalRows.length} 个`} note={signalRows[0] ? `Top 1 · ${signalRows[0].symbol} ${signalRows[0].name}` : "等待生成排名"} tone="violet" />
        <MetricCard icon={BellRing} label="组合观察项" value={`${alertCount} 项`} note={`减仓 ${reviewCount} · 保护 ${profitCount} · 高波 ${highBetaCount}`} tone={alertCount ? "warning" : "positive"} />
      </section>

      <section className="v2-workbench-grid">
        <article className="v2-surface v2-equity-card">
          <header className="v2-section-head">
            <div><span>Portfolio pulse</span><h3>模拟仓权益脉搏</h3><p>观察权益变化与资金使用，不接入真实账户。</p></div>
            <div className="v2-section-actions">
              <Badge variant={curveFresh ? "success" : "warning"}>{curveFresh ? `曲线已同步 · ${curveDate}` : `曲线待同步 · ${curveDate || "暂无"}`}</Badge>
              <Button size="sm" variant="ghost" onClick={() => onNavigate?.("portfolio")} type="button">完整复盘<ArrowRight size={14} aria-hidden="true" /></Button>
            </div>
          </header>
          <div className="v2-equity-summary">
            <div><span>当前权益</span><strong>{money(totalEquity)}</strong><small className={metricTone(totalReturn)}>{pct(totalReturn)} 累计收益</small></div>
            <div className="v2-position-progress"><span>资金使用率 <b>{pct(positionRatio)}</b></span><Progress value={Math.min(100, Math.max(0, Number(positionRatio || 0) * 100))} /></div>
          </div>
          <div className="v2-chart-freshness"><Database size={14} aria-hidden="true" /><span>{equityMeta.display_note || "使用正式模拟仓绩效曲线。"}</span><strong>估值日 {performance.valuation_as_of_date || latestDate || "暂无"}</strong></div>
          <Sparkline rows={curve} label="模拟仓权益曲线" xLabel="日期" xUnit="交易日" yLabel="模拟仓权益" yUnit="元" />
        </article>

        <article className="v2-surface v2-journey-card">
          <header className="v2-section-head compact"><div><span>Daily flow</span><h3>今日研究路径</h3></div></header>
          <div className="journey-list">
            <JourneyItem icon={Database} label="01 · 数据" title={dataHealthy ? "行情覆盖已就绪" : "数据等待补齐"} note={`截至 ${text(latestDate, "待更新")}`} state={dataHealthy ? "ready" : "wait"} />
            <JourneyItem icon={BarChart3} label="02 · 信号" title={signalHealthy ? `${signalRows.length} 个候选已排名` : "等待生成排名"} note="原始规则仍为执行依据" state={signalHealthy ? "ready" : "wait"} />
            <JourneyItem icon={BriefcaseBusiness} label="03 · 组合" title={`${positions.length} 个持仓待复盘`} note={`${alertCount} 项观察提醒`} state={portfolioHealthy ? "ready" : "wait"} />
            <JourneyItem icon={BookOpenCheck} label="04 · 研究" title={statusCn(weekly.status)} note={`证据成熟度：${statusCn(weekly.evidence_level)}`} state={weekly.status ? "ready" : "wait"} />
          </div>
        </article>
      </section>

      <section className="v2-two-column">
        <article className="v2-surface">
          <header className="v2-section-head">
            <div><span>Holdings watch</span><h3>持仓热区</h3><p>聚焦收益、权重与观察状态。</p></div>
            <Badge variant={alertCount ? "warning" : "success"}>{alertCount ? `${alertCount} 项需观察` : "无硬风险触发"}</Badge>
          </header>
          <div className="holding-list">
            {positions.slice(0, 5).map((row) => (
              <button className="holding-row" key={row.symbol} onClick={() => onNavigate?.("portfolio")} type="button">
                <span className="holding-symbol">{String(row.symbol).slice(-2)}</span>
                <span className="holding-name"><strong>{row.symbol} · {text(row.name, "ETF")}</strong><small>{text(row.group || row.etf_type, "未分类")} · {row.review_state_cn || row.review_state || "常规观察"}</small></span>
                <span className="holding-weight"><strong>{pct(row.position_ratio)}</strong><small>组合权重</small></span>
                <span className={`holding-pnl ${metricTone(row.unrealized_pnl)}`}><strong>{money(row.unrealized_pnl)}</strong><small>{pct(row.unrealized_pnl_pct)}</small></span>
              </button>
            ))}
            {!positions.length ? <EmptyState>暂无持仓数据，完成模拟仓更新后会显示在这里。</EmptyState> : null}
          </div>
        </article>

        <article className="v2-surface">
          <header className="v2-section-head">
            <div><span>Signal radar</span><h3>信号雷达</h3><p>原始 BUY 排名与双周期状态。</p></div>
            <Badge variant="blue">Preview 不执行</Badge>
          </header>
          <div className="signal-radar-list">
            {signalRows.slice(0, 5).map((row, index) => (
              <button className="signal-radar-row" key={`${row.symbol}-${index}`} onClick={() => onNavigate?.("signals")} type="button">
                <span className="signal-rank">#{row.rank || index + 1}</span>
                <span className="signal-name"><strong>{row.symbol} · {row.name}</strong><small>{row.group || "ETF"}</small></span>
                <span className="signal-cycle"><i className={row.mid_trend_signal === "BUY" ? "buy" : "watch"} />{row.mid_trend_signal || "N/A"}<small>中周期</small></span>
                <span className="signal-cycle"><i className={row.short_swing_signal === "BUY" ? "buy" : "watch"} />{row.short_swing_signal || "N/A"}<small>短周期</small></span>
                <span className="signal-score">{score(row.rank_score, 1)}</span>
              </button>
            ))}
            {!signalRows.length ? <EmptyState>暂无排名数据，刷新研究报告后会显示候选。</EmptyState> : null}
          </div>
        </article>
      </section>

      <section className="v2-insight-grid">
        <article className="v2-surface v2-research-radar">
          <header className="v2-section-head">
            <div><span>Research radar</span><h3>研究进度雷达</h3><p>从证据、风格和风险三个角度查看研究成熟度。</p></div>
            <Button size="sm" variant="ghost" onClick={() => onNavigate?.("research")} type="button">进入研究图谱<ArrowRight size={14} aria-hidden="true" /></Button>
          </header>
          <div className="research-card-grid">
            {researchCards.map(({ label, value, note, icon: Icon, tone }) => (
              <button className={`research-mini-card ${tone}`} key={label} onClick={() => onNavigate?.("research")} type="button">
                <Icon size={18} aria-hidden="true" /><span>{label}</span><strong>{value}</strong><small>{note}</small>
              </button>
            ))}
          </div>
          <div className="v2-insight-note"><TriangleAlert size={16} aria-hidden="true" /><span>最新 Regime 结论必须按日期理解；过期快照不会在这里被描述为实时市场状态。</span></div>
        </article>

        <article className="v2-surface v2-allocation-card">
          <header className="v2-section-head compact"><div><span>Allocation lens</span><h3>组合结构镜头</h3></div></header>
          <div className="allocation-figure">
            <div className="allocation-bar">
              <i className="tech" style={{ width: `${Math.max(0, Math.min(100, Number(broadBase.tech_growth_weight || 0) * 100))}%` }} />
              <i className="finance" style={{ width: `${Math.max(0, Math.min(100, Number(broadBase.finance_real_estate_weight || 0) * 100))}%` }} />
              <i className="broad" style={{ width: `${Math.max(0, Math.min(100, Number(broadBase.broad_base_weight || 0) * 100))}%` }} />
            </div>
            <div className="allocation-legend">
              <span><i className="tech" />科技成长 <b>{pct(broadBase.tech_growth_weight)}</b></span>
              <span><i className="finance" />金融地产 <b>{pct(broadBase.finance_real_estate_weight)}</b></span>
              <span><i className="broad" />宽基底仓 <b>{pct(broadBase.broad_base_weight)}</b></span>
            </div>
          </div>
          <p className="allocation-summary">{broadBase.summary_text || "组合结构数据将在刷新报告后显示。"}</p>
        </article>
      </section>

      <section className="v2-two-column bottom-row">
        <article className="v2-surface">
          <header className="v2-section-head compact"><div><span>Safe actions</span><h3>常用研究动作</h3></div></header>
          <div className="quick-action-grid">
            <button onClick={() => onRun?.("backfill_etf_data")} type="button"><span><Database size={18} aria-hidden="true" /></span><strong>补齐数据</strong><small>更新本地 ETF 日线</small><ArrowRight size={15} aria-hidden="true" /></button>
            <button onClick={() => onRun?.("refresh_all_reports")} type="button"><span><Zap size={18} aria-hidden="true" /></span><strong>刷新报告</strong><small>重建信号与研究摘要</small><ArrowRight size={15} aria-hidden="true" /></button>
            <button onClick={() => onNavigate?.("tasks")} type="button"><span><Clock3 size={18} aria-hidden="true" /></span><strong>任务中心</strong><small>查看运行记录与日志</small><ArrowRight size={15} aria-hidden="true" /></button>
          </div>
        </article>

        <article className="v2-surface">
          <header className="v2-section-head compact"><div><span>Recent activity</span><h3>最近任务</h3></div><Badge variant={taskStatus?.running ? "blue" : "neutral"}>{taskStatus?.running ? "运行中" : "当前空闲"}</Badge></header>
          <div className="activity-list">
            {taskHistory.slice(0, 3).map((item) => (
              <div className="activity-row" key={item.task_id || `${item.task_name}-${item.started_at}`}>
                <span className={`activity-dot ${item.status || "idle"}`} />
                <div><strong>{item.description || item.task_name}</strong><small>{item.finished_at || item.started_at || "暂无时间"} · {item.duration_label || "暂无耗时"}</small></div>
                <Badge variant={item.status === "success" ? "success" : item.status === "failed" ? "danger" : "warning"}>{statusCn(item.status)}</Badge>
              </div>
            ))}
            {!taskHistory.length ? <EmptyState>暂无任务记录。</EmptyState> : null}
          </div>
        </article>
      </section>
    </main>
  );
}
