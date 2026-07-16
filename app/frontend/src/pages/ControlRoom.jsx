import TaskPanel from "../components/TaskPanel.jsx";
import DataHealthPanel from "../components/DataHealthPanel.jsx";
import PortfolioPanel from "../components/PortfolioPanel.jsx";
import SignalsPanel from "../components/SignalsPanel.jsx";
import Section from "../components/Section.jsx";
import { money, pct, text } from "../format.js";

function Metric({ label, value, note, tone = "neutral" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function RiskBanner({ warnings = [] }) {
  if (!warnings.length) {
    return <div className="risk-banner ok"><strong>当前无硬风险触发。</strong><span>仍需按收盘后复核节奏观察持仓和数据健康。</span></div>;
  }
  return (
    <div className="risk-banner warn">
      <strong>风险提醒 {warnings.length} 项</strong>
      {warnings.slice(0, 4).map((item, index) => (
        <span key={index}>{item.symbol || "SYSTEM"} · {item.reason || item}</span>
      ))}
    </div>
  );
}

export default function ControlRoom({ status, dataHealth, portfolio, signals, research, taskStatus, onRun }) {
  const summary = portfolio?.summary || {};
  const warnings = Array.isArray(status?.key_warnings) ? status.key_warnings : [];
  return (
    <main className="page-grid">
      <section className="control-hero">
        <div>
          <div className="eyebrow">动态研究控制台</div>
          <h2>{status?.today_conclusion || "持有观察"}</h2>
          <p>{status?.today_summary || "日线数据、模拟盘、研究预览和自动化状态聚合在同一个只读控制台。"}</p>
        </div>
        <div className="hero-stack">
          <span className={`pill ${String(status?.system_status || "NORMAL").toLowerCase()}`}>{status?.system_status === "ERROR" ? "异常" : status?.system_status === "CAUTION" ? "观察" : "正常"}</span>
          <span className="pill">数据源：{status?.actual_source_used || "暂无"}</span>
          <span className="pill">模拟引擎：{status?.paper_trade_engine_status || "暂无"}</span>
        </div>
      </section>

      <div className="metric-grid">
        <Metric label="总资产" value={money(summary.total_equity || status?.total_equity)} note={`现金 ${money(summary.cash || status?.cash)}`} />
        <Metric label="持仓市值" value={money(summary.market_value || status?.position_value)} note={`仓位 ${pct(summary.position_ratio || status?.position_pct)}`} />
        <Metric label="最新数据日" value={status?.latest_data_date || "暂无"} note={`${status?.data_update_status || "未知"} · 新增 ${status?.data_update_new_rows ?? 0}`} />
        <Metric label="风险提醒" value={String(warnings.length)} note={warnings.length ? "需要复核" : "无硬触发"} tone={warnings.length ? "warn" : "ok"} />
      </div>

      <RiskBanner warnings={warnings} />

      <div className="split">
        <TaskPanel taskStatus={taskStatus} onRun={onRun} compact />
        <Section title="今日系统摘要" eyebrow="系统状态带">
          <div className="tape-grid">
            <div><span>市场状态</span><strong>{text(status?.market_state)}</strong></div>
            <div><span>组合暴露</span><strong>{text(status?.portfolio_exposure?.status || status?.portfolio_exposure?.exposure_status)}</strong></div>
            <div><span>Tushare</span><strong>PRIMARY_UPSTREAM</strong></div>
            <div><span>正式数据</span><strong>data/etf_daily/</strong></div>
            <div><span>研究样本</span><strong>{research?.sample_count ?? 0}</strong></div>
            <div><span>调整后排名执行</span><strong>{status?.execution_safety?.adjusted_rank_score_execution_enabled ? "开启" : "关闭"}</strong></div>
          </div>
        </Section>
      </div>

      <DataHealthPanel data={dataHealth} />
      <PortfolioPanel portfolio={portfolio} />
      <SignalsPanel signals={signals} />
    </main>
  );
}
