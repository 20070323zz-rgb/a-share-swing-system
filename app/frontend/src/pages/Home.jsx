import Section from "../components/Section.jsx";
import Sparkline from "../components/Sparkline.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { appVersion } from "../designTokens.js";
import { money, pct, text } from "../format.js";

function statusCn(value) {
  const raw = String(value ?? "").toLowerCase();
  const map = {
    insufficient: "证据不足",
    normal: "正常",
    caution: "观察",
    error: "异常",
    baostock: "BaoStock 本地数据源",
    tushare: "Tushare 候选源",
    disabled: "已禁用",
    success: "已完成",
    failed: "失败",
    running: "运行中"
  };
  return map[raw] || text(value, "暂无数据");
}

function HomeCard({ title, value, note, tone = "" }) {
  return (
    <div className={`home-card ${tone}`}>
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function PrimaryAction({ title, note, onClick, primary = false }) {
  return (
    <button className={`quick-action ${primary ? "primary" : ""}`} onClick={onClick} type="button">
      <span>{title}</span>
      <small>{note}</small>
    </button>
  );
}

export default function Home({ status, portfolio, research, dataHealth, safety, onNavigate, onRun }) {
  const performance = portfolio?.performance || {};
  const summary = portfolio?.summary || {};
  const curve = portfolio?.equity_curve || [];
  const weekly = research?.shadow_observation_weekly || {};
  const sources = dataHealth?.data_sources || status?.data_sources || {};
  const totalEquity = performance.current_total_equity ?? summary.total_equity ?? status?.total_equity;
  const totalPnl = performance.total_pnl_amount ?? summary.total_pnl;
  const totalReturn = performance.total_return_pct;
  const latestDate = dataHealth?.latest_data_date || status?.latest_data_date;
  const systemTone = status?.system_status === "ERROR" ? "warn" : status?.system_status === "CAUTION" ? "warn" : "ok";
  const dataStatus = statusCn(dataHealth?.status || status?.data_update_status || "normal");
  const safeText = safety?.real_trade_enabled || safety?.broker_api_enabled ? "需要复核" : "边界正常";

  return (
    <main className="page-grid app-home">
      <section className="apple-hero home-hero-minimal">
        <div>
          <div className="eyebrow">今日总览</div>
          <h2>先补数据，再看信号。</h2>
          <p>这是本地模拟盘研究应用。所有操作只更新本地数据和报告，不连接券商，不真实交易。</p>
          <div className="hero-pills">
            <StatusPill tone={systemTone}>{systemTone === "ok" ? "系统正常" : "需要观察"}</StatusPill>
            <StatusPill tone="blue">数据日 {text(latestDate, "等待更新")}</StatusPill>
            <StatusPill tone="muted">L2 本地研究</StatusPill>
            <StatusPill tone="muted">{appVersion}</StatusPill>
          </div>
        </div>
        <div className="hero-orb-card">
          <span>模拟仓总资产</span>
          <strong>{money(totalEquity)}</strong>
          <small>总盈亏 {money(totalPnl)} · 收益率 {pct(totalReturn)}</small>
          <Sparkline rows={curve} label="模拟仓权益曲线" />
        </div>
      </section>

      <section className="today-actions">
        <div>
          <span>今日操作</span>
          <strong>先确认本地 ETF 数据是否补齐</strong>
          <small>补齐任务只会运行白名单脚本，更新行情、覆盖和健康报告。</small>
        </div>
        <div className="today-action-buttons">
          <PrimaryAction title="一键补齐 ETF 数据" note="更新本地行情数据，不会交易" primary onClick={() => onRun?.("backfill_etf_data")} />
          <PrimaryAction title="刷新研究报告" note="重新生成信号和看板" onClick={() => onRun?.("refresh_all_reports")} />
          <PrimaryAction title="打开模拟仓" note="查看持仓和盈亏" onClick={() => onNavigate?.("portfolio")} />
        </div>
      </section>

      <section className="home-card-grid slim">
        <HomeCard title="模拟仓盈亏" value={money(totalPnl)} note={`${money(totalEquity)} · ${pct(totalReturn)}`} tone={Number(totalPnl || 0) >= 0 ? "ok" : "warn"} />
        <HomeCard title="数据状态" value={dataStatus} note={`最新数据日 ${text(latestDate, "等待更新")}`} />
        <HomeCard title="模型观察" value={statusCn(weekly.evidence_level || "insufficient")} note="影子模型只观察，不接执行层" tone="warn" />
        <HomeCard title="安全状态" value={safeText} note="不接券商，不真实下单" tone={safeText === "边界正常" ? "ok" : "warn"} />
      </section>

      <Section title="当前结论" eyebrow="今日摘要">
        <div className="next-action">
          <strong>{status?.today_summary || "先保持观察，等待数据和信号完成更新。"}</strong>
          <p>数据源：{statusCn(sources.primary_source || dataHealth?.primary_source || "baostock")}。正式模型未被影子模型替代，所有交易相关入口仍然禁用。</p>
        </div>
      </Section>
    </main>
  );
}
