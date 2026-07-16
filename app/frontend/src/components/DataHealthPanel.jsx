import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Section from "./Section.jsx";

function sourceVariant(status) {
  const raw = String(status || "").toLowerCase();
  if (raw.includes("updated") || raw === "ok" || raw.includes("ready")) return "success";
  if (raw.includes("skip") || raw.includes("up_to_date")) return "blue";
  if (raw.includes("fail") || raw.includes("error")) return "danger";
  return "warning";
}

export default function DataHealthPanel({ data }) {
  const priority = data?.source_priority || [];
  const rows = [
    ["主数据源", data?.primary_provider || "TUSHARE", `优先级：${priority.join(" → ") || "TUSHARE"}`],
    ["Fallback", data?.fallback_enabled ? "ENABLED" : "DISABLED", "正式更新链无自动回退"],
    ["BaoStock", data?.baostock_role || "RECONCILIATION_ONLY", "仅保留对账角色"],
    ["JQData fallback", data?.jqdata_fallback || "DISABLED", "不进入正式更新链"]
  ];
  return (
    <Section title="数据健康" eyebrow="ETF 日线数据源">
      <div className="description-grid">
        <div><span>ETF 文件</span><strong>{data?.etf_file_count ?? "暂无"}</strong></div>
        <div><span>最新数据日</span><strong>{data?.latest_data_date ?? "暂无"}</strong></div>
        <div><span>新增行</span><strong>{data?.new_rows ?? 0}</strong></div>
        <div><span>失败数</span><strong>{data?.failed_count ?? 0}</strong></div>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>数据源</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>说明</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map(([title, status, note]) => (
            <TableRow key={title}>
              <TableCell>{title}</TableCell>
              <TableCell><Badge variant={sourceVariant(status)}>{status}</Badge></TableCell>
              <TableCell>{note}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="diagnosis">{data?.diagnosis || "暂无诊断摘要"}</div>
      {(data?.failed_symbols || []).length ? <div className="warning-line">失败标的：{data.failed_symbols.join(" / ")}</div> : null}
    </Section>
  );
}
