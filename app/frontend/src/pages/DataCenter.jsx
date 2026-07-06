import { useState } from "react";
import DataHealthPanel from "../components/DataHealthPanel.jsx";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { text } from "../format.js";

function statusVariant(value) {
  const raw = String(value || "").toLowerCase();
  if (raw.includes("fail") || raw.includes("error") || raw.includes("异常")) return "danger";
  if (raw.includes("warn") || raw.includes("caution") || raw.includes("提醒")) return "warning";
  if (raw.includes("up_to_date") || raw.includes("ok") || raw.includes("normal") || raw.includes("正常")) return "success";
  return "neutral";
}

export default function DataCenter({ dataHealth, status, onRun }) {
  const [view, setView] = useState("status");
  const sources = dataHealth?.data_sources || status?.data_sources || {};
  const universe = dataHealth?.universe_quality_review || {};
  const latestDate = dataHealth?.latest_data_date || status?.latest_data_date;
  const updatedAt = dataHealth?.generated_at || status?.updated_at || status?.generated_at;
  const coverageRows = [
    ["ETF 总数", universe.total_etf ?? dataHealth?.etf_file_count ?? "暂无", "正式数据目录"],
    ["建议交易池", universe.recommended_trade_pool ?? "暂无", "仅为回测前审查建议"],
    ["建议观察池", universe.recommended_observe_pool ?? "暂无", "不等于正式买入"],
    ["建议排除池", universe.recommended_exclude_pool ?? "暂无", "不进入研究/交易池"]
  ];
  const healthRows = [
    ["正常", dataHealth?.normal_count ?? dataHealth?.healthy_count ?? "暂无", "可用于研究"],
    ["提醒", dataHealth?.caution_count ?? dataHealth?.warning_count ?? "暂无", "需要标注 caution"],
    ["异常", dataHealth?.abnormal_count ?? dataHealth?.error_count ?? dataHealth?.failed_count ?? 0, "不应进入交易池"],
    ["缺失", dataHealth?.missing_count ?? "暂无", "等待补齐或排查"]
  ];

  return (
    <main className="page-grid data-center">
      <section className="page-action-head">
        <div>
          <div className="eyebrow">数据中心</div>
          <h2>一键补齐 ETF 数据</h2>
          <p>更新本地行情数据，不会交易，不连接券商。</p>
        </div>
        <div className="action-head-side">
          <Badge variant="blue">最新数据日 {text(latestDate, "等待更新")}</Badge>
          <Badge variant="neutral">最近更新 {text(updatedAt, "暂无记录")}</Badge>
          <Button type="button" onClick={() => onRun?.("backfill_etf_data")}>一键补齐 ETF 数据</Button>
        </div>
      </section>

      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="status">数据状态</TabsTrigger>
          <TabsTrigger value="coverage">数据覆盖</TabsTrigger>
          <TabsTrigger value="health">数据健康</TabsTrigger>
          <TabsTrigger value="reports">报告</TabsTrigger>
        </TabsList>

        <TabsContent value="status">
          <Section title="数据状态" eyebrow="本地行情">
            <div className="description-list">
              <div><span>正式数据源</span><strong>{text(sources.primary_source || dataHealth?.primary_source || "BaoStock")}</strong><small>日常更新主链路</small></div>
              <div><span>候选数据源</span><strong>{text(sources.candidate_daily_source || "Tushare")}</strong><small>只用于研究验证</small></div>
              <div><span>备用状态</span><strong>{sources.fallback_triggered ? "已触发" : "未触发"}</strong><small>自动化状态</small></div>
              <div><span>券商连接</span><strong>未连接</strong><small>数据任务不接券商</small></div>
            </div>
            <div className="inline-alert">{text(universe.readiness_summary || dataHealth?.diagnosis, "暂无额外诊断。")}</div>
          </Section>
        </TabsContent>

        <TabsContent value="coverage">
          <Section title="数据覆盖" eyebrow="Universe">
            <Table>
              <TableHeader>
                <TableRow><TableHead>指标</TableHead><TableHead>数量</TableHead><TableHead>说明</TableHead></TableRow>
              </TableHeader>
              <TableBody>
                {coverageRows.map(([label, value, note]) => (
                  <TableRow key={label}>
                    <TableCell>{label}</TableCell>
                    <TableCell>{value}</TableCell>
                    <TableCell>{note}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="maturity-row">
              <span>回测准备度</span>
              <strong>{universe.backtest_ready ? "可开始基础回测" : "需要继续审查"}</strong>
              <Progress value={universe.backtest_ready ? 100 : 60} />
            </div>
          </Section>
        </TabsContent>

        <TabsContent value="health">
          <DataHealthPanel data={dataHealth} />
          <Section title="健康摘要" eyebrow="检查结果">
            <Table>
              <TableHeader>
                <TableRow><TableHead>类别</TableHead><TableHead>数量</TableHead><TableHead>说明</TableHead></TableRow>
              </TableHeader>
              <TableBody>
                {healthRows.map(([label, value, note]) => (
                  <TableRow key={label}>
                    <TableCell><Badge variant={statusVariant(label)}>{label}</Badge></TableCell>
                    <TableCell>{value}</TableCell>
                    <TableCell>{note}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Section>
        </TabsContent>

        <TabsContent value="reports">
          <Section title="数据报告" eyebrow="文档列表">
            <div className="document-list">
              <ReportCard title="数据覆盖报告" file="latest_data_coverage.md" summary={dataHealth?.coverage_tail} />
              <ReportCard title="数据健康报告" file="latest_data_health.md" summary={dataHealth?.health_tail} />
              <ReportCard title="数据源状态" file="data_source_status_report.md" summary={dataHealth?.data_sources || { status: "等待更新" }} />
            </div>
          </Section>
        </TabsContent>
      </Tabs>
    </main>
  );
}
