import Section from "../components/Section.jsx";
import Sparkline from "../components/Sparkline.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
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

function InlineMetric({ title, value, note }) {
  return (
    <div className="mono-metric">
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function PrimaryAction({ title, note, onClick, primary = false }) {
  return (
    <Button className="workbench-action" variant={primary ? "default" : "secondary"} onClick={onClick} type="button">
      <span>{title}</span>
      <small>{note}</small>
    </Button>
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
  const reviewSummary = status?.review_summary || portfolio?.review_summary || {};
  const reduceCandidateCount = Number(reviewSummary.reduce_candidate_count ?? status?.reduce_candidate_count ?? 0);
  const profitSummary = status?.profit_protection_summary || portfolio?.profit_protection_summary || {};
  const profitWatchCount = Number(profitSummary.profit_watch_count ?? status?.profit_watch_count ?? 0);
  const highBetaSummary = status?.high_beta_risk_summary || portfolio?.high_beta_risk_summary || {};
  const highBetaState = highBetaSummary.high_beta_exposure_state || status?.high_beta_exposure_state || "HB_NORMAL";
  const highBetaCount = Number(highBetaSummary.high_beta_position_count ?? status?.high_beta_position_count ?? 0);
  const broadBaseSummary = status?.broad_base_balance_summary || portfolio?.broad_base_balance_summary || {};
  const broadBaseState = broadBaseSummary.broad_base_balance_state || status?.broad_base_balance_state || "UNKNOWN";
  const broadBaseWeight = broadBaseSummary.broad_base_weight ?? status?.broad_base_weight;
  const weeklyPacket = status?.chatgpt_weekly_packet_summary || research?.chatgpt_weekly_packet_summary || {};
  const weeklyPacketDate = weeklyPacket.as_of_date || "待生成";
  const positionRatio = summary.position_ratio ?? performance.current_position_ratio ?? 0;
  const positions = portfolio?.positions || [];

  return (
    <main className="page-grid app-home">
      <section className="mono-page-head">
        <div>
          <h2>量化研究控制台</h2>
          <p>本地模拟盘研究应用。只更新本地数据和报告，不连接券商，不真实交易。</p>
        </div>
        <div className="mono-head-actions">
          <Badge variant={systemTone === "ok" ? "success" : "warning"}>{systemTone === "ok" ? "系统正常" : "需要观察"}</Badge>
          <Badge variant="neutral">数据截至 {text(latestDate, "等待更新")}</Badge>
          <Button size="sm" onClick={() => onRun?.("backfill_etf_data")} type="button">一键补齐 ETF 数据</Button>
        </div>
      </section>

      <section className="mono-metric-row">
        <InlineMetric title="总资产" value={money(totalEquity)} note={`仓位 ${pct(positionRatio)}`} />
        <InlineMetric title="总收益" value={pct(totalReturn)} note={`盈亏 ${money(totalPnl)}`} />
        <InlineMetric title="数据状态" value={dataStatus} note={text(latestDate, "等待更新")} />
        <InlineMetric title="最大观察" value={`${reduceCandidateCount + profitWatchCount + highBetaCount}`} note="复核 / 浮盈 / 高波动" />
      </section>

      <Separator />

      <section className="mono-chart-section">
        <div className="mono-section-title">
          <h3>权益</h3>
          <span>模拟仓权益曲线</span>
        </div>
        <Sparkline rows={curve} label="模拟仓权益曲线" />
        <Progress value={Math.min(100, Math.max(0, Number(positionRatio || 0) * 100))} />
      </section>

      <Separator />

      <Section title="持仓观察" eyebrow="当前持仓">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ETF</TableHead>
              <TableHead>市值</TableHead>
              <TableHead>收益</TableHead>
              <TableHead>观察状态</TableHead>
              <TableHead>风险</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.slice(0, 6).map((row) => (
              <TableRow key={row.symbol}>
                <TableCell><strong>{row.symbol}</strong><small>{text(row.name, "ETF")}</small></TableCell>
                <TableCell className="num">{money(row.market_value)}<small>{pct(row.position_ratio)}</small></TableCell>
                <TableCell className={`num ${Number(row.unrealized_pnl) >= 0 ? "cn-profit" : "cn-loss"}`}>{money(row.unrealized_pnl)}<small>{pct(row.unrealized_pnl_pct)}</small></TableCell>
                <TableCell><Badge variant={String(row.review_state || "").includes("REVIEW") ? "warning" : "neutral"}>{row.review_state_cn || row.review_state || "观察"}</Badge></TableCell>
                <TableCell>{row.high_beta_risk_state || row.profit_protection_state || row.health_status || "正常"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Section>

      <Separator />

      <Section title="当前结论" eyebrow="今日摘要">
        <div className="next-action">
          <strong>{status?.today_summary || "先保持观察，等待数据和信号完成更新。"}</strong>
          <p>数据源：{statusCn(sources.primary_source || dataHealth?.primary_source || "baostock")}。正式模型未被影子模型替代，所有交易相关入口仍然禁用。</p>
          <p>研究状态：{statusCn(weekly.evidence_level || "insufficient")} · 周报 {weeklyPacketDate} · {broadBaseState} · {safeText} · {appVersion}</p>
          <div className="mono-inline-actions">
            <Button size="sm" variant="secondary" onClick={() => onRun?.("refresh_all_reports")} type="button">刷新研究报告</Button>
            <Button size="sm" variant="ghost" onClick={() => onNavigate?.("portfolio")} type="button">打开模拟仓</Button>
          </div>
        </div>
      </Section>
    </main>
  );
}
