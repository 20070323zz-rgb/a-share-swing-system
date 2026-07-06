import { useState } from "react";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { pct, score, text } from "../format.js";

function statusCn(value) {
  const raw = String(value ?? "").toLowerCase();
  const map = {
    insufficient: "证据不足",
    continue_observation: "继续观察",
    false: "否",
    true: "是",
    disabled: "禁用",
    ok: "正常",
    shadow_observation: "影子观察"
  };
  return map[raw] || text(value, "暂无数据");
}

function badgeVariant(value) {
  const raw = String(value ?? "").toLowerCase();
  if (raw === "true" || raw.includes("execution")) return "danger";
  if (raw.includes("insufficient") || raw.includes("observation") || raw.includes("false")) return "warning";
  if (raw.includes("ok") || raw.includes("locked")) return "success";
  return "neutral";
}

function SummaryRow({ label, value, note, variant = "neutral" }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value}</strong>
      <Badge variant={variant}>{note}</Badge>
    </div>
  );
}

export default function Research({ research, onNavigate }) {
  const [view, setView] = useState("shadow");
  const control = research?.app_control_center || {};
  const weekly = research?.shadow_observation_weekly || {};
  const missed = research?.missed_opportunity_tracking || {};
  const rankingV2 = research?.ranking_model_v2_backtest || {};
  const persistence = research?.persistence_breakout_shadow || {};
  const broadBase = research?.broad_base_balance_preview || {};
  const weeklyPacket = research?.chatgpt_weekly_packet || {};
  const weeklyPacketSummary = research?.chatgpt_weekly_packet_summary || weeklyPacket.summary || {};
  const weeklyPacketConclusions = Array.isArray(weeklyPacketSummary.core_conclusions) ? weeklyPacketSummary.core_conclusions : [];
  const reports = research?.report_summaries || {};
  const evidenceLevel = weekly.evidence_level || control.evidence_level || "insufficient";
  const maturedCount = Number(weekly.matured_forward_return_count ?? 0);
  const maturedGoal = Math.max(20, maturedCount);
  const maturedPct = Math.min(maturedCount / maturedGoal, 1) * 100;
  const shadowRows = [
    {
      model: "top10_diversified_filter_v2",
      phase: "低回撤候选",
      selected: rankingV2.best_candidate || "top10_diversified_filter_v2",
      evidence: rankingV2.beat_510300 ? "待复核" : "未跑赢基准",
      action: "仅 shadow tracking"
    },
    {
      model: "persistence_breakout_v2",
      phase: "影子观察",
      selected: persistence.selected_count ?? 0,
      evidence: statusCn(evidenceLevel),
      action: "继续观察"
    },
    {
      model: "adjusted preview",
      phase: "宽基平衡观察",
      selected: (broadBase.top_balance_candidates || broadBase.rows || []).length,
      evidence: "不接执行层",
      action: "只展示"
    }
  ];
  const missedRows = [
    ["候选数", missed.candidate_count ?? 0, "被过滤但值得观察"],
    ["主要过滤原因", text(missed.top_missed_filter_reason || "trend_not_confirmed"), "不代表应放宽规则"],
    ["错失比例", score(weekly.missed_opportunity_rate, 2), "样本不足不下结论"],
    ["过滤有效率", score(weekly.filter_effective_rate, 2), "等待后续收益"]
  ];

  return (
    <main className="page-grid research-control">
      <section className="page-compact-head">
        <div>
          <div className="eyebrow">模型观察</div>
          <h2>正式模型保持锁定，研究模型继续观察。</h2>
          <p>这里只回答模型是否改变、shadow 成熟度和下一步观察重点；不改变自动买卖规则。</p>
        </div>
        <Button variant="secondary" onClick={() => onNavigate?.("portfolio")} type="button">查看模拟仓</Button>
      </section>

      <section className="summary-row-grid">
        <SummaryRow label="当前阶段" value="影子观察期" note="研究专用" variant="warning" />
        <SummaryRow label="证据等级" value={statusCn(evidenceLevel)} note="样本不足" variant="warning" />
        <SummaryRow label="进入预览层" value={weekly.ready_for_preview ? "是" : "否"} note="当前保持否" variant={weekly.ready_for_preview ? "danger" : "success"} />
        <SummaryRow label="接执行层" value={weekly.ready_for_execution ? "是" : "否"} note="必须为否" variant={weekly.ready_for_execution ? "danger" : "success"} />
      </section>

      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="shadow">影子模型</TabsTrigger>
          <TabsTrigger value="evidence">证据成熟度</TabsTrigger>
          <TabsTrigger value="missed">错失机会</TabsTrigger>
          <TabsTrigger value="reports">研究报告</TabsTrigger>
        </TabsList>

        <TabsContent value="shadow">
          <Section title="影子模型" eyebrow="研究模型">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>模型</TableHead>
                  <TableHead>阶段</TableHead>
                  <TableHead>最新 selected</TableHead>
                  <TableHead>证据</TableHead>
                  <TableHead>动作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shadowRows.map((row) => (
                  <TableRow key={row.model}>
                    <TableCell><strong>{row.model}</strong></TableCell>
                    <TableCell>{row.phase}</TableCell>
                    <TableCell>{row.selected}</TableCell>
                    <TableCell><Badge variant={badgeVariant(row.evidence)}>{row.evidence}</Badge></TableCell>
                    <TableCell>{row.action}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="inline-alert">继续观察，不放宽规则，不进入正式执行层。</div>
          </Section>
          <Section title="周报分析包" eyebrow="给 ChatGPT / Main">
            <div className="document-list">
              <ReportCard title="周报分析包" file={weeklyPacket.markdown_path || "reports/chatgpt_weekly_analysis_packet_latest.md"} status={weeklyPacket.status || "present"} summary={(weeklyPacketConclusions.length ? weeklyPacketConclusions.slice(0, 5) : ["暂无周报分析包，请先运行每周复盘。"]).join("\n")} />
            </div>
          </Section>
        </TabsContent>

        <TabsContent value="evidence">
          <Section title="证据成熟度" eyebrow="后续收益">
            <div className="maturity-list">
              <div className="maturity-row">
                <span>真实观察日</span>
                <strong>{weekly.observation_days ?? "暂无"}</strong>
                <Progress value={maturedPct} />
              </div>
              <div className="maturity-row">
                <span>10 日后续收益样本</span>
                <strong>{maturedCount} / {maturedGoal}</strong>
                <Progress value={maturedPct} />
              </div>
              <div className="maturity-row">
                <span>20 日后续收益样本</span>
                <strong>{weekly.matured_forward_return_20d_count ?? "暂无"}</strong>
                <Progress value={0} />
              </div>
              <div className="maturity-row">
                <span>完整交易闭环</span>
                <strong>{weekly.completed_trade_loop_count ?? "暂无"}</strong>
                <Progress value={0} />
              </div>
            </div>
            <div className="inline-alert">样本成熟前，只展示研究结果，不进入执行层。</div>
          </Section>
        </TabsContent>

        <TabsContent value="missed">
          <Section title="错失机会追踪" eyebrow="观察记录">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>指标</TableHead>
                  <TableHead>值</TableHead>
                  <TableHead>说明</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {missedRows.map(([label, value, note]) => (
                  <TableRow key={label}>
                    <TableCell>{label}</TableCell>
                    <TableCell>{value}</TableCell>
                    <TableCell>{note}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Section>
        </TabsContent>

        <TabsContent value="reports">
          <Section title="研究报告" eyebrow="文档列表">
            <div className="document-list">
              {Object.entries(reports).slice(0, 12).map(([key, report]) => (
                <ReportCard key={key} title={report.display_name || key} file={report.path} status={report.status} summary={String(report.tail || "").split("\n").slice(0, 5).join("\n")} />
              ))}
            </div>
          </Section>
        </TabsContent>
      </Tabs>
    </main>
  );
}
