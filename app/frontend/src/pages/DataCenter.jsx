import { useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, Database, RefreshCw, Search } from "lucide-react";
import DataHealthPanel from "../components/DataHealthPanel.jsx";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { text } from "../format.js";

function price(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toFixed(3)} 元` : "暂无";
}

function change(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "暂无涨跌";
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}

function statusVariant(value) {
  const raw = String(value || "").toLowerCase();
  if (raw.includes("fail") || raw.includes("error") || raw.includes("异常")) return "danger";
  if (raw.includes("warn") || raw.includes("caution") || raw.includes("提醒")) return "warning";
  if (raw.includes("up_to_date") || raw.includes("ok") || raw.includes("normal") || raw.includes("正常")) return "success";
  return "neutral";
}

export default function DataCenter({ dataHealth, status, onRun }) {
  const [view, setView] = useState("status");
  const [inventoryQuery, setInventoryQuery] = useState("");
  const sources = dataHealth?.data_sources || status?.data_sources || {};
  const universe = dataHealth?.universe_quality_review || {};
  const latestDate = dataHealth?.latest_data_date || status?.latest_data_date;
  const updatedAt = dataHealth?.generated_at || status?.updated_at || status?.generated_at;
  const inventoryRows = dataHealth?.etf_inventory || [];
  const inventorySummary = dataHealth?.inventory_summary || {};
  const filteredInventory = useMemo(() => {
    const query = inventoryQuery.trim().toLowerCase();
    if (!query) return inventoryRows;
    return inventoryRows.filter((row) => [row.symbol, row.name, row.group, row.etf_type, row.pool].some((value) => String(value || "").toLowerCase().includes(query)));
  }, [inventoryRows, inventoryQuery]);
  const updateStatus = String(dataHealth?.status || status?.data_update_status || "unknown").toLowerCase();
  const updateTitle = updateStatus === "up_to_date" ? "检查完成，数据已是最新" : updateStatus === "updated" ? "补齐完成，本次有新增" : updateStatus.includes("stale") ? "仍有数据落后" : "等待数据检查";
  const updateVariant = statusVariant(updateStatus);
  const liveInventorySummary = inventoryRows.length
    ? `本地库存 ${inventorySummary.total_count ?? inventoryRows.length} 只 ETF，已更新 ${inventorySummary.up_to_date_count ?? 0} 只、待补齐 ${inventorySummary.lagging_count ?? 0} 只；最新价格日 ${text(latestDate, "暂无")}。建议交易池 ${universe.recommended_trade_pool ?? "暂无"} 只，仅用于研究与回测审查。`
    : text(dataHealth?.diagnosis, "暂无额外诊断。");
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
          <p>先检查每只 ETF 的价格日期，仅在发现缺口时下载；不会交易，不连接券商。</p>
        </div>
        <div className="action-head-side">
          <Badge variant="blue">价格日 {text(latestDate, "等待更新")}</Badge>
          <Badge variant={inventorySummary.lagging_count ? "warning" : "success"}>{inventorySummary.up_to_date_count ?? 0}/{inventorySummary.total_count ?? 0} 已更新</Badge>
          <Badge variant="neutral">最近更新 {text(updatedAt, "暂无记录")}</Badge>
          <Button type="button" onClick={() => onRun?.("backfill_etf_data")}><RefreshCw size={15} aria-hidden="true" />检查并补齐</Button>
        </div>
      </section>

      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="status">数据状态</TabsTrigger>
          <TabsTrigger value="database">ETF 数据库</TabsTrigger>
          <TabsTrigger value="coverage">数据覆盖</TabsTrigger>
          <TabsTrigger value="health">数据健康</TabsTrigger>
          <TabsTrigger value="reports">报告</TabsTrigger>
        </TabsList>

        <TabsContent value="status">
          <section className={`data-update-proof ${updateVariant}`}>
            <div className="data-update-proof-icon">{updateStatus === "up_to_date" || updateStatus === "updated" ? <CheckCircle2 size={22} aria-hidden="true" /> : <RefreshCw size={22} aria-hidden="true" />}</div>
            <div><span>最近一次补齐结果</span><strong>{updateTitle}</strong><p>目标价格日 {text(dataHealth?.requested_end || inventorySummary.expected_price_date, "暂无")} · 检查 {dataHealth?.processed_symbols ?? inventorySummary.total_count ?? 0} 只 · 新增 {dataHealth?.new_rows ?? 0} 行 · 行情请求 {dataHealth?.actual_api_calls ?? 0} 次</p></div>
            <Badge variant={updateVariant}>{updateStatus === "up_to_date" ? "已是最新" : updateStatus === "updated" ? "有新增" : text(updateStatus)}</Badge>
          </section>
          <Section title="数据状态" eyebrow="本地行情">
            <div className="description-list">
              <div><span>主上游</span><strong>{text(dataHealth?.primary_source || "TUSHARE")}</strong><small>PRIMARY_UPSTREAM</small></div>
              <div><span>正式数据库</span><strong>data/etf_daily/</strong><small>唯一 SSOT</small></div>
              <div><span>Fallback</span><strong>已禁用</strong><small>BaoStock 仅对账，JQData 不回退</small></div>
              <div><span>券商连接</span><strong>未连接</strong><small>数据任务不接券商</small></div>
            </div>
            <div className="inline-alert">{liveInventorySummary}</div>
          </Section>
        </TabsContent>

        <TabsContent value="database">
          <Section title="ETF 数据库" eyebrow="183 只本地日线库存">
            <div className="inventory-toolbar">
              <div className="inventory-search">
                <Search size={15} aria-hidden="true" />
                <input aria-label="搜索 ETF 数据库" onChange={(event) => setInventoryQuery(event.target.value)} placeholder="搜索代码、名称、分类或数据池" type="search" value={inventoryQuery} />
              </div>
              <div className="inventory-meta"><Database size={15} aria-hidden="true" /><span>显示 {filteredInventory.length} / {inventoryRows.length} 只</span><CalendarDays size={15} aria-hidden="true" /><span>目标价格日 {text(inventorySummary.expected_price_date, "暂无")}</span></div>
            </div>
            <Table className="data-inventory-table">
              <TableHeader>
                <TableRow><TableHead>ETF</TableHead><TableHead>分类 / 数据池</TableHead><TableHead>最新收盘价</TableHead><TableHead>价格日期</TableHead><TableHead>覆盖起点</TableHead><TableHead>记录数</TableHead><TableHead>更新状态</TableHead></TableRow>
              </TableHeader>
              <TableBody>
                {filteredInventory.map((row) => (
                  <TableRow key={row.symbol}>
                    <TableCell><strong>{row.symbol}</strong><small>{row.name}</small></TableCell>
                    <TableCell>{row.group}<small>{row.etf_type} · {row.pool}</small></TableCell>
                    <TableCell className="num"><strong>{price(row.close)}</strong><small>{change(row.change_pct)}</small></TableCell>
                    <TableCell><strong>{text(row.price_date)}</strong><small>该收盘价对应日期</small></TableCell>
                    <TableCell>{text(row.data_start)}</TableCell>
                    <TableCell className="num">{row.row_count ?? "暂无"}</TableCell>
                    <TableCell><Badge variant={row.update_status === "up_to_date" ? "success" : "warning"}>{row.update_status === "up_to_date" ? "已更新" : "待补齐"}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {!filteredInventory.length ? <div className="v2-empty">没有匹配的 ETF 数据记录。</div> : null}
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
