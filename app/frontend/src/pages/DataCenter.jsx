import { useState } from "react";
import DataHealthPanel from "../components/DataHealthPanel.jsx";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import SegmentedControl from "../components/SegmentedControl.jsx";
import { text } from "../format.js";

function SourceCard({ label, value, note, tone = "" }) {
  return (
    <div className={`source-card ${tone}`}>
      <span>{label}</span>
      <strong>{text(value, "暂无数据")}</strong>
      <small>{note}</small>
    </div>
  );
}

export default function DataCenter({ dataHealth, status, onRun }) {
  const [view, setView] = useState("summary");
  const sources = dataHealth?.data_sources || status?.data_sources || {};
  const universe = dataHealth?.universe_quality_review || {};
  const options = [
    { value: "summary", label: "概览" },
    { value: "health", label: "健康" },
    { value: "reports", label: "报告" }
  ];
  const latestDate = dataHealth?.latest_data_date || status?.latest_data_date;

  return (
    <main className="page-grid data-center">
      <section className="apple-hero compact data-hero">
        <div>
          <div className="eyebrow">数据中心</div>
          <h2>管理本地 ETF 行情数据。</h2>
          <p>补齐、检查和查看本地数据。这里不会连接券商，也不会生成真实交易。</p>
        </div>
        <span className="status-pill blue">最新数据日 {text(latestDate, "等待更新")}</span>
      </section>

      <section className="data-primary-action">
        <div>
          <span>常用操作</span>
          <strong>一键补齐 ETF 数据</strong>
          <small>只更新本地研究数据，并刷新覆盖、健康和看板快照。</small>
        </div>
        <button className="quick-action primary" type="button" onClick={() => onRun?.("backfill_etf_data")}>
          <span>一键补齐 ETF 数据</span>
          <small>不会交易，不会连接券商</small>
        </button>
      </section>

      <SegmentedControl options={options} value={view} onChange={setView} />

      {view === "summary" ? (
        <>
          <section className="source-grid compact-sources">
            <SourceCard label="正式数据源" value={sources.primary_source || dataHealth?.primary_source || "BaoStock"} note="日常更新主链路" tone="ok" />
            <SourceCard label="候选数据源" value={sources.candidate_daily_source || "Tushare"} note="只用于研究验证" />
            <SourceCard label="备用状态" value={sources.fallback_triggered ? "已触发" : "未触发"} note="自动化状态" />
            <SourceCard label="券商连接" value="未连接" note="数据任务不接券商" tone="ok" />
          </section>
          <Section title="数据覆盖" eyebrow="概览">
            <div className="matrix compact-matrix">
              <div><span>ETF 总数</span><strong>{universe.total_etf ?? dataHealth?.etf_file_count ?? "暂无"}</strong></div>
              <div><span>建议交易池</span><strong>{universe.recommended_trade_pool ?? "暂无"}</strong></div>
              <div><span>建议观察池</span><strong>{universe.recommended_observe_pool ?? "暂无"}</strong></div>
              <div><span>建议排除池</span><strong>{universe.recommended_exclude_pool ?? "暂无"}</strong></div>
            </div>
            <div className="warning-line">{text(universe.readiness_summary || dataHealth?.diagnosis, "暂无额外诊断。")}</div>
          </Section>
        </>
      ) : null}

      {view === "health" ? (
        <>
          <DataHealthPanel data={dataHealth} />
          <Section title="健康摘要" eyebrow="检查结果">
            <div className="matrix compact-matrix">
              <div><span>更新状态</span><strong>{text(dataHealth?.status, "等待更新")}</strong></div>
              <div><span>新增行数</span><strong>{dataHealth?.new_rows ?? 0}</strong></div>
              <div><span>失败数量</span><strong>{dataHealth?.failed_count ?? 0}</strong></div>
              <div><span>BaoStock 调用</span><strong>{dataHealth?.baostock_api_calls ?? 0}</strong></div>
            </div>
          </Section>
        </>
      ) : null}

      {view === "reports" ? (
        <Section title="数据报告" eyebrow="折叠查看">
          <div className="report-preview-grid">
            <ReportCard title="数据覆盖报告" file="latest_data_coverage.md" summary={dataHealth?.coverage_tail} />
            <ReportCard title="数据健康报告" file="latest_data_health.md" summary={dataHealth?.health_tail} />
            <ReportCard title="数据源状态" file="data_source_status_report.md" summary={dataHealth?.data_sources || { status: "等待更新" }} />
          </div>
        </Section>
      ) : null}
    </main>
  );
}
