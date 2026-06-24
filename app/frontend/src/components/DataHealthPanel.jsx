import Section from "./Section.jsx";

function SourceCard({ title, status, note }) {
  const cls = String(status || "").toLowerCase().includes("updated") || String(status || "").toLowerCase() === "ok" ? "ok" : String(status || "").toLowerCase().includes("skip") ? "neutral" : "warn";
  return (
    <div className={`source-card ${cls}`}>
      <span>{title}</span>
      <strong>{status || "暂无"}</strong>
      <small>{note || "暂无说明"}</small>
    </div>
  );
}

export default function DataHealthPanel({ data }) {
  const priority = data?.source_priority || [];
  return (
    <Section title="数据中心" eyebrow="ETF 日线数据源">
      <div className="metric-grid">
        <div><span>ETF 文件</span><strong>{data?.etf_file_count ?? "暂无"}</strong></div>
        <div><span>最新数据日</span><strong>{data?.latest_data_date ?? "暂无"}</strong></div>
        <div><span>新增行</span><strong>{data?.new_rows ?? 0}</strong></div>
        <div><span>失败数</span><strong>{data?.failed_count ?? 0}</strong></div>
      </div>
      <div className="source-grid">
        <SourceCard title="实际数据源" status={data?.actual_source_used || "暂无"} note={`优先级：${priority.join(" → ") || "暂无"}`} />
        <SourceCard title="BaoStock" status={data?.baostock_status || "暂无"} note={data?.data_sources?.baostock_message || "日常主源"} />
        <SourceCard title="JQData" status={data?.jqdata_status || "暂无"} note={data?.data_sources?.jqdata_message || "备用 / 历史源"} />
        <SourceCard title="备用切换" status={data?.fallback_triggered ? "已触发" : "未触发"} note="本轮不接券商接口" />
      </div>
      <div className="diagnosis">{data?.diagnosis || "暂无诊断摘要"}</div>
      {(data?.failed_symbols || []).length ? <div className="warning-line">失败标的：{data.failed_symbols.join(" / ")}</div> : null}
    </Section>
  );
}
