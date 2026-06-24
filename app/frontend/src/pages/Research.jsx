import { useState } from "react";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import SegmentedControl from "../components/SegmentedControl.jsx";
import Timeline from "../components/Timeline.jsx";
import { pct, score, text } from "../format.js";

function statusCn(value) {
  const raw = String(value ?? "").toLowerCase();
  const map = {
    insufficient: "证据不足",
    continue_observation: "继续观察",
    false: "否",
    true: "是",
    disabled: "禁用",
    ok: "正常"
  };
  return map[raw] || text(value, "暂无数据");
}

function ObserveCard({ label, value, note, tone = "" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export default function Research({ research, onNavigate }) {
  const [view, setView] = useState("overview");
  const control = research?.app_control_center || {};
  const weekly = research?.shadow_observation_weekly || {};
  const missed = research?.missed_opportunity_tracking || {};
  const rankingV2 = research?.ranking_model_v2_backtest || {};
  const persistence = research?.persistence_breakout_shadow || {};
  const reports = research?.report_summaries || {};
  const evidenceLevel = weekly.evidence_level || control.evidence_level || "insufficient";
  const maturedCount = Number(weekly.matured_forward_return_count ?? 0);
  const maturedGoal = Math.max(20, maturedCount);
  const maturedPct = Math.min(maturedCount / maturedGoal, 1) * 100;
  const options = [
    { value: "overview", label: "概览" },
    { value: "shadow", label: "影子模型" },
    { value: "evidence", label: "证据成熟度" },
    { value: "missed", label: "错失机会" },
    { value: "reports", label: "报告" }
  ];
  const timeline = [
    { title: "top10 v2", note: "低回撤候选，收益未充分证明", tone: "warn" },
    { title: "Persistence Breakout", note: "shadow tracking 中", tone: "warn" },
    { title: "Missed Opportunity", note: "等待后续收益样本", tone: "warn" },
    { title: "执行层", note: "正式模型锁定，不接入 shadow", tone: "ok" }
  ];

  return (
    <main className="page-grid research-control">
      <section className="apple-hero compact">
        <div>
          <div className="eyebrow">模型观察</div>
          <h2>正式模型锁定，影子模型继续观察。</h2>
          <p>这里用于观察 shadow 模型表现和证据成熟度，不影响正式模拟仓，不改变自动买卖规则。</p>
          <div className="hero-pills">
            <span className="status-pill muted">正式模型锁定</span>
            <span className="status-pill blue">影子模型观察</span>
            <span className="status-pill warn">证据不足</span>
          </div>
        </div>
        <button className="mac-button" onClick={() => onNavigate?.("portfolio")} type="button">查看模拟仓</button>
      </section>

      <SegmentedControl options={options} value={view} onChange={setView} />

      {view === "overview" ? (
        <>
          <section className="metric-grid">
            <ObserveCard label="当前阶段" value="影子观察期" note="研究专用，不改执行层" tone="warn" />
            <ObserveCard label="证据等级" value={statusCn(evidenceLevel)} note="样本不足时只展示" tone="warn" />
            <ObserveCard label="是否进入 preview" value={weekly.ready_for_preview ? "是" : "否"} note="当前应保持否" tone={weekly.ready_for_preview ? "danger" : "ok"} />
            <ObserveCard label="是否接执行层" value={weekly.ready_for_execution ? "是" : "否"} note="必须为否" tone={weekly.ready_for_execution ? "danger" : "ok"} />
          </section>
          <Section title="观察阶段" eyebrow="时间线">
            <Timeline items={timeline} />
          </Section>
          <Section title="结论" eyebrow="研究判断">
            <div className="research-alert">继续观察，不放宽规则，不进入预览层，不接入正式执行层。</div>
          </Section>
        </>
      ) : null}

      {view === "shadow" ? (
        <Section title="影子模型状态" eyebrow="研究模型">
          <div className="model-grid compact-model-grid">
            <div className="model-card">
              <div className="model-head"><div><h3>top10_diversified_filter_v2</h3><p>低回撤候选模型，只进入 shadow tracking。</p></div><span className="control-badge warn">研究专用</span></div>
              <div className="model-metrics">
                <div><span>主资金</span><strong>{rankingV2.initial_cash_main || 20000}</strong><small>研究假设</small></div>
                <div><span>收益</span><strong>{pct(rankingV2.best_candidate_total_return)}</strong><small>未跑赢 510300 不接执行层</small></div>
                <div><span>最大回撤</span><strong>{pct(rankingV2.best_candidate_max_drawdown)}</strong><small>低回撤观察</small></div>
                <div><span>执行接入</span><strong>{rankingV2.candidate_ready_for_execution ? "是" : "否"}</strong><small>必须为否</small></div>
              </div>
            </div>
            <div className="model-card">
              <div className="model-head"><div><h3>persistence_breakout_v2</h3><p>收益增强候选模型，仍处于影子观察。</p></div><span className="control-badge warn">观察中</span></div>
              <div className="model-metrics">
                <div><span>选中数量</span><strong>{persistence.selected_count ?? 0}</strong><small>最新信号</small></div>
                <div><span>信号日</span><strong>{text(persistence.latest_signal_date)}</strong><small>等待成熟样本</small></div>
                <div><span>执行接入</span><strong>{persistence.ready_for_execution ? "是" : "否"}</strong><small>必须为否</small></div>
                <div><span>状态</span><strong>影子观察</strong><small>不写正式持仓</small></div>
              </div>
            </div>
          </div>
        </Section>
      ) : null}

      {view === "evidence" ? (
        <Section title="证据成熟度" eyebrow="后续收益">
          <div className="progress-block">
            <div className="progress-top">
              <strong>后续收益样本成熟度</strong>
              <span>{maturedCount} / {maturedGoal}</span>
            </div>
            <div className="progress-track"><div className="progress-fill" style={{ width: `${maturedPct}%` }} /></div>
            <small>样本成熟前，只展示研究结果，不进入执行层。</small>
          </div>
          <div className="control-card-grid">
            <ObserveCard label="证据等级" value={statusCn(evidenceLevel)} note="当前不足以接入执行层" tone="warn" />
            <ObserveCard label="成熟样本" value={weekly.matured_forward_return_count ?? 0} note="10 日后续收益样本" />
            <ObserveCard label="Risk-on 空信号" value={weekly.risk_on_empty_days ?? 0} note="需要继续观察" />
            <ObserveCard label="观察天数" value={weekly.observation_days ?? "暂无"} note="样本期" />
          </div>
        </Section>
      ) : null}

      {view === "missed" ? (
        <Section title="错失机会追踪" eyebrow="观察记录">
          <div className="control-card-grid">
            <ObserveCard label="候选数" value={missed.candidate_count ?? 0} note="被过滤但值得观察" />
            <ObserveCard label="主要过滤原因" value={text(missed.top_missed_filter_reason || "trend_not_confirmed")} note="不代表应放宽规则" />
            <ObserveCard label="错失比例" value={score(weekly.missed_opportunity_rate, 2)} note="样本不足时不下结论" />
            <ObserveCard label="过滤有效率" value={score(weekly.filter_effective_rate, 2)} note="等待后续收益" />
          </div>
        </Section>
      ) : null}

      {view === "reports" ? (
        <Section title="报告摘要" eyebrow="折叠查看">
          <div className="report-preview-grid">
            {Object.entries(reports).slice(0, 12).map(([key, report]) => (
              <ReportCard key={key} title={report.display_name || key} file={report.path} status={report.status} summary={String(report.tail || "").split("\n").slice(0, 5).join("\n")} />
            ))}
          </div>
        </Section>
      ) : null}
    </main>
  );
}
