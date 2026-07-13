import { useState } from "react";
import ReportCard from "../components/ReportCard.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
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

const STYLE_LABELS = {
  GROWTH_THEME: "成长主题",
  GROWTH_BROAD: "成长宽基",
  SECTOR_CYCLICAL: "周期行业",
  SECTOR_DEFENSIVE: "防御行业",
  CORE_LARGE_CAP: "大盘核心",
  CORE_MID_CAP: "中盘核心",
  DIVIDEND: "红利",
  LOW_VOL: "低波",
  BOND: "债券",
  HIGH_BETA_THEME: "高弹性主题",
  COMMODITY_CYCLICAL: "商品周期",
  QDII_OBSERVATION: "QDII观察",
  UNKNOWN: "未知"
};

const STYLE_MATRIX_ORDER = [
  "GROWTH_THEME",
  "GROWTH_BROAD",
  "SECTOR_CYCLICAL",
  "SECTOR_DEFENSIVE",
  "CORE_LARGE_CAP",
  "CORE_MID_CAP",
  "DIVIDEND",
  "LOW_VOL",
  "BOND",
  "HIGH_BETA_THEME"
];

const EVIDENCE_LABELS = {
  SUPPORTED: "支持",
  WEAK_SUPPORT: "弱支持",
  NEUTRAL: "中性",
  WEAK_CONFLICT: "弱冲突",
  CONFLICT: "冲突",
  INSUFFICIENT: "样本不足"
};

function boolCn(value) {
  return value ? "是" : "否";
}

function regimeCn(value) {
  const raw = String(value ?? "");
  const map = { OFFENSIVE: "进攻", NEUTRAL: "中性", DEFENSIVE: "防御" };
  return map[raw] || text(value, "暂无");
}

function styleCn(value) {
  return STYLE_LABELS[String(value ?? "")] || text(value, "未知");
}

function evidenceCn(value) {
  return EVIDENCE_LABELS[String(value ?? "")] || text(value, "暂无");
}

function evidenceClass(value) {
  return String(value ?? "INSUFFICIENT").toLowerCase();
}

function isConflictEvidence(value) {
  return ["CONFLICT", "WEAK_CONFLICT"].includes(String(value ?? ""));
}

function FitEvidence({ value }) {
  const raw = String(value ?? "INSUFFICIENT");
  return (
    <span className={`fit-evidence fit-evidence-${evidenceClass(raw)}`}>
      <span className="fit-evidence-dot" />
      <Badge variant="neutral">{evidenceCn(raw)}</Badge>
    </span>
  );
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
  const etfRisk = research?.etf_risk_profile || {};
  const etfRiskSummary = research?.etf_risk_profile_summary || etfRisk.summary || {};
  const portfolioRisk = research?.portfolio_risk_profile || etfRisk.portfolio_risk_profile || {};
  const buyRisk = research?.buy_ranking_risk_profile || etfRisk.buy_ranking_risk_profile || {};
  const persistence = research?.persistence_breakout_shadow || {};
  const broadBase = research?.broad_base_balance_preview || {};
  const weeklyPacket = research?.chatgpt_weekly_packet || {};
  const weeklyPacketSummary = research?.chatgpt_weekly_packet_summary || weeklyPacket.summary || {};
  const weeklyPacketConclusions = Array.isArray(weeklyPacketSummary.core_conclusions) ? weeklyPacketSummary.core_conclusions : [];
  const regimeAudit = research?.market_regime_audit || {};
  const regimeDistribution = regimeAudit?.distribution?.distribution || {};
  const regimeStability = regimeAudit?.stability || {};
  const regimeDecision = regimeAudit?.decision || {};
  const regimeCurrent = regimeAudit?.current || {};
  const regimeCompactRows = Array.isArray(regimeAudit?.compact_fit_rows) ? regimeAudit.compact_fit_rows : [];
  const regimeStabilization = research?.market_regime_stabilization || {};
  const stabilizationDecision = regimeStabilization?.decision || {};
  const stabilizationRaw = regimeStabilization?.raw_metrics || {};
  const stabilizationSelected = regimeStabilization?.selected_metrics || {};
  const stabilizationLag = regimeStabilization?.selected_lag || {};
  const stabilizationRows = Array.isArray(regimeStabilization?.comparison_rows) ? regimeStabilization.comparison_rows : [];
  const styleFit = research?.style_regime_fit || {};
  const styleFitDecision = styleFit?.phase_decision || {};
  const styleFitMatrix = Array.isArray(styleFit?.matrix_rows) ? styleFit.matrix_rows : [];
  const styleFitMatrixByStyle = Object.fromEntries(styleFitMatrix.map((row) => [row.style_profile, row]));
  const styleFitMatrixRows = STYLE_MATRIX_ORDER.map((styleKey) => styleFitMatrixByStyle[styleKey] || { style_profile: styleKey });
  const styleFitBuy = styleFit?.buy_top10 || {};
  const styleFitBuyRows = Array.isArray(styleFitBuy?.rows) ? styleFitBuy.rows.slice(0, 10) : [];
  const styleFitPortfolio = styleFit?.portfolio || {};
  const styleFitPortfolioRows = Array.isArray(styleFitPortfolio?.rows) ? styleFitPortfolio.rows : [];
  const styleFitInteraction = styleFit?.signal_interaction || {};
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
          <TabsTrigger value="market-regime">市场状态</TabsTrigger>
          <TabsTrigger value="risk-profile">风险画像</TabsTrigger>
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

        <TabsContent value="market-regime">
          <Section title="市场状态审计" eyebrow="Regime Layer Phase 2">
            <div className="summary-row-grid">
              <SummaryRow label="当前回放状态" value={text(regimeCurrent.normalized_regime, "暂无")} note={text(regimeCurrent.raw_market_regime, "research")} variant="neutral" />
              <SummaryRow label="OFFENSIVE 占比" value={pct(regimeDistribution.OFFENSIVE?.percentage)} note={`${regimeDistribution.OFFENSIVE?.day_count ?? 0} 天`} variant="warning" />
              <SummaryRow label="NEUTRAL 占比" value={pct(regimeDistribution.NEUTRAL?.percentage)} note={`${regimeDistribution.NEUTRAL?.day_count ?? 0} 天`} variant="neutral" />
              <SummaryRow label="DEFENSIVE 占比" value={pct(regimeDistribution.DEFENSIVE?.percentage)} note={`${regimeDistribution.DEFENSIVE?.day_count ?? 0} 天`} variant="neutral" />
              <SummaryRow label="平均持续" value={`${score(regimeStability.average_regime_duration, 1)} 天`} note={`切换 ${regimeStability.regime_switch_count ?? 0} 次`} variant="warning" />
              <SummaryRow label="短周期反复" value={regimeStability.short_regime_whipsaw_count ?? "暂无"} note={regimeStability.needs_future_hysteresis_research ? "需研究滞后确认" : "暂可接受"} variant={regimeStability.needs_future_hysteresis_research ? "warning" : "success"} />
              <SummaryRow label="Regime Fit" value={regimeDecision.ready_for_regime_fit_phase ? "可进入下一研究阶段" : "继续观察"} note="不接执行层" variant={regimeDecision.ready_for_regime_fit_phase ? "success" : "warning"} />
              <SummaryRow label="执行层" value={regimeDecision.ready_for_execution ? "是" : "否"} note="必须为否" variant={regimeDecision.ready_for_execution ? "danger" : "success"} />
            </div>
            <div className="inline-alert">这里审计的是 Phase 4C 的 market_regime 历史回放，只用于研究判断，不修改 BUY ranking、不修改正式交易规则。</div>
          </Section>

          <Section title="稳定化研究" eyebrow="Regime Layer Phase 2.5">
            <div className="summary-row-grid">
              <SummaryRow label="原始状态" value={text(stabilizationDecision.current_raw_regime, "暂无")} note={text(stabilizationDecision.current_date, "raw")} variant="neutral" />
              <SummaryRow label="影子稳定状态" value={text(stabilizationDecision.current_selected_shadow_regime, "暂无")} note={text(stabilizationDecision.selected_candidate, "shadow only")} variant="warning" />
              <SummaryRow label="RAW Whipsaw" value={stabilizationRaw.three_day_whipsaw_count ?? "暂无"} note={`中位 ${score(stabilizationRaw.median_regime_duration, 1)} 天`} variant="warning" />
              <SummaryRow label="Candidate Whipsaw" value={stabilizationSelected.three_day_whipsaw_count ?? "暂无"} note={`中位 ${score(stabilizationSelected.median_regime_duration, 1)} 天`} variant="success" />
              <SummaryRow label="检测延迟" value={`${score(stabilizationLag.average_detection_lag, 2)} 天`} note={`漏检 ${pct(stabilizationLag.missed_segment_ratio)}`} variant="warning" />
              <SummaryRow label="执行层" value={stabilizationDecision.ready_for_execution ? "是" : "否"} note="必须为否" variant={stabilizationDecision.ready_for_execution ? "danger" : "success"} />
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>候选</TableHead>
                  <TableHead>切换次数</TableHead>
                  <TableHead>中位持续</TableHead>
                  <TableHead>Whipsaw</TableHead>
                  <TableHead>检测延迟</TableHead>
                  <TableHead>Style Fit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stabilizationRows.map((row) => (
                  <TableRow key={row.candidate}>
                    <TableCell><strong>{row.candidate}</strong></TableCell>
                    <TableCell>{row.regime_switch_count ?? "暂无"}</TableCell>
                    <TableCell>{score(row.median_regime_duration, 1)}</TableCell>
                    <TableCell>{row.three_day_whipsaw_count ?? "暂无"}</TableCell>
                    <TableCell>{score(row.average_detection_lag, 2)}</TableCell>
                    <TableCell><Badge variant={row.style_fit === "YES" ? "success" : "warning"}>{row.style_fit || "N/A"}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="inline-alert">影子稳定状态只用于研究观察，不影响正式模拟仓、不修改 market_regime、不修改 ranking。</div>
            <div className="document-list">
              <ReportCard title="市场状态稳定化 Phase 2.5" file={regimeStabilization.report_href || "reports/regime_layer_phase2_5_stabilization.md"} status={regimeStabilization.status || "missing"} summary={stabilizationDecision.selected_candidate_reason || "运行 src/market_regime_stabilization.py 后生成。"} />
            </div>
          </Section>

          <Section title="风格适配" eyebrow="Regime Layer Phase 3">
            <div className="summary-row-grid">
              <SummaryRow label="当前稳定状态" value={regimeCn(styleFit.current_stable_regime)} note={styleFit.selected_candidate || "shadow"} variant="neutral" />
              <SummaryRow label="Style Fit 历史支持" value={boolCn(styleFitDecision.style_fit_has_historical_support)} note="历史样本" variant={styleFitDecision.style_fit_has_historical_support ? "success" : "warning"} />
              <SummaryRow label="Fit 增量信息" value={boolCn(styleFitDecision.style_fit_has_incremental_signal_value)} note="signal interaction" variant={styleFitDecision.style_fit_has_incremental_signal_value ? "success" : "warning"} />
              <SummaryRow label="BUY Top10 冲突" value={styleFit.buy_conflict_count ?? styleFitDecision.buy_top10_conflict_count ?? 0} note={styleFitDecision.current_buy_top10_has_regime_conflict ? "存在冲突" : "暂无冲突"} variant="neutral" />
              <SummaryRow label="当前持仓冲突" value={styleFit.portfolio_conflict_count ?? styleFitDecision.portfolio_conflict_count ?? 0} note={styleFitDecision.current_portfolio_has_regime_conflict ? "存在冲突" : "暂无冲突"} variant="neutral" />
            </div>

            <Separator className="research-separator" />

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>风格</TableHead>
                  <TableHead>进攻</TableHead>
                  <TableHead>中性</TableHead>
                  <TableHead>防御</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {styleFitMatrixRows.map((row) => (
                  <TableRow key={row.style_profile}>
                    <TableCell><strong>{styleCn(row.style_profile)}</strong><div className="muted">{row.style_profile}</div></TableCell>
                    {["OFFENSIVE", "NEUTRAL", "DEFENSIVE"].map((regime) => (
                      <TableCell key={regime}>
                        <FitEvidence value={row[`${regime}_evidence`]} />
                        <div className="muted">10日 {pct(row[`${regime}_median_return_10d`])} · n={row[`${regime}_sample_count_10d`] ?? "暂无"}</div>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <Separator className="research-separator" />

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>排名</TableHead>
                  <TableHead>ETF</TableHead>
                  <TableHead>风格</TableHead>
                  <TableHead>原始得分</TableHead>
                  <TableHead>当前适配</TableHead>
                  <TableHead>解释</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {styleFitBuyRows.length ? styleFitBuyRows.map((row) => {
                  const strong = Number(row.raw_score) >= 75;
                  const conflict = isConflictEvidence(row.overall_fit_evidence);
                  return (
                    <TableRow key={`${row.rank}-${row.symbol}`}>
                      <TableCell>{row.rank}</TableCell>
                      <TableCell><strong>{row.symbol}</strong><div className="muted">{row.name}</div></TableCell>
                      <TableCell>{styleCn(row.style_profile)}<div className="muted">{row.style_profile}</div></TableCell>
                      <TableCell className="num">{score(row.raw_score, 2)}</TableCell>
                      <TableCell><FitEvidence value={row.overall_fit_evidence} /></TableCell>
                      <TableCell>{strong && conflict ? "强信号 + 适配冲突" : strong ? "强信号，继续观察适配" : "研究解释"}<div className="muted">{row.fit_interpretation}</div></TableCell>
                    </TableRow>
                  );
                }) : (
                  <TableRow><TableCell colSpan={6}>暂无 BUY Top10 风格适配快照。</TableCell></TableRow>
                )}
              </TableBody>
            </Table>

            <Separator className="research-separator" />

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ETF</TableHead>
                  <TableHead>风格</TableHead>
                  <TableHead>当前权重</TableHead>
                  <TableHead>稳定状态</TableHead>
                  <TableHead>风格适配</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {styleFitPortfolioRows.length ? styleFitPortfolioRows.map((row) => (
                  <TableRow key={row.symbol}>
                    <TableCell><strong>{row.symbol}</strong><div className="muted">{row.name}</div></TableCell>
                    <TableCell>{styleCn(row.style_profile)}<div className="muted">{row.style_profile}</div></TableCell>
                    <TableCell className="num">{pct(row.current_weight)}</TableCell>
                    <TableCell>{regimeCn(row.current_stable_regime)}</TableCell>
                    <TableCell><FitEvidence value={row.overall_fit_evidence} /><div className="muted">{row.fit_interpretation}</div></TableCell>
                  </TableRow>
                )) : (
                  <TableRow><TableCell colSpan={5}>暂无当前持仓风格适配快照。</TableCell></TableRow>
                )}
              </TableBody>
            </Table>

            <div className="inline-alert">风格适配为影子研究，不影响正式模拟仓。</div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Phase Decision</TableHead>
                  <TableHead>结果</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  ["style_fit_has_historical_support", styleFitDecision.style_fit_has_historical_support],
                  ["style_fit_has_incremental_signal_value", styleFitDecision.style_fit_has_incremental_signal_value],
                  ["current_buy_top10_has_regime_conflict", styleFitDecision.current_buy_top10_has_regime_conflict],
                  ["current_portfolio_has_regime_conflict", styleFitDecision.current_portfolio_has_regime_conflict],
                  ["ready_for_fit_shadow_observation", styleFitDecision.ready_for_fit_shadow_observation],
                  ["ready_for_adjusted_preview_research", styleFitDecision.ready_for_adjusted_preview_research],
                  ["ready_for_preview", styleFitDecision.ready_for_preview],
                  ["ready_for_execution", styleFitDecision.ready_for_execution]
                ].map(([label, value]) => (
                  <TableRow key={label}>
                    <TableCell>{label}</TableCell>
                    <TableCell><Badge variant={value ? (label === "ready_for_execution" ? "danger" : "success") : "neutral"}>{boolCn(value)}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="muted">增量信息说明：{styleFitInteraction.incremental_signal_reason || styleFitDecision.decision_reason || "暂无"}</div>
          </Section>

          <Section title="Regime Fit 10日表现" eyebrow="Style / Structural">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>市场状态</TableHead>
                  <TableHead>成长主题10日</TableHead>
                  <TableHead>高风险资产10日</TableHead>
                  <TableHead>核心宽基10日</TableHead>
                  <TableHead>防御资产10日</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {regimeCompactRows.map((row) => (
                  <TableRow key={row.market_state}>
                    <TableCell><strong>{row.market_state}</strong></TableCell>
                    <TableCell>{pct(row.growth_theme_10d)}</TableCell>
                    <TableCell>{pct(row.high_risk_asset_10d)}</TableCell>
                    <TableCell>{pct(row.core_broad_10d)}</TableCell>
                    <TableCell>{pct(row.defensive_asset_10d)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="document-list">
              <ReportCard title="市场状态 Phase 2 总报告" file={regimeAudit.report_href || "reports/regime_layer_phase2_market_audit.md"} status={regimeAudit.status || "missing"} summary={regimeDecision.decision_reason || "运行 src/market_regime_replay.py 后生成。"} />
            </div>
          </Section>
        </TabsContent>

        <TabsContent value="risk-profile">
          <Section title="ETF 双风险画像" eyebrow="Regime & Risk Allocation Phase 1.5">
            <div className="summary-row-grid">
              <SummaryRow label="有效画像 ETF" value={etfRiskSummary.valid_profile_count ?? etfRisk.row_count ?? 0} note={`总数 ${etfRiskSummary.total_etf ?? 0}`} variant="neutral" />
              <SummaryRow label="UNKNOWN style" value={etfRiskSummary.unknown_style_count ?? 0} note="目标 <= 15" variant={(etfRiskSummary.unknown_style_count ?? 0) <= 15 ? "success" : "warning"} />
              <SummaryRow label="组合近期风险" value={score(portfolioRisk.weighted_realized_risk_score ?? portfolioRisk.weighted_risk_score, 2)} note="realized" variant="warning" />
              <SummaryRow label="组合结构风险" value={score(portfolioRisk.weighted_structural_risk_score, 2)} note="structural" variant="warning" />
              <SummaryRow label="BUY Top 近期风险" value={score(buyRisk.top10_avg_realized_risk_score ?? buyRisk.top10_avg_risk_score, 2)} note={`进攻占比 ${pct(buyRisk.offensive_high_beta_ratio)}`} variant="warning" />
              <SummaryRow label="BUY Top 结构风险" value={score(buyRisk.top10_avg_structural_risk_score, 2)} note={`进攻占比 ${pct(buyRisk.structural_offensive_high_beta_ratio)}`} variant="warning" />
            </div>
            <div className="inline-alert">risk_score / risk_profile 是 realized risk 兼容别名；structural risk 独立描述 ETF 结构性风险。两者都只用于研究展示，不修改 BUY ranking、不接执行层。</div>
          </Section>

          <Section title="当前持仓画像" eyebrow="Portfolio Risk Profile">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ETF</TableHead>
                  <TableHead>style</TableHead>
                  <TableHead>近期风险</TableHead>
                  <TableHead>结构风险</TableHead>
                  <TableHead>权重</TableHead>
                  <TableHead>60日波动</TableHead>
                  <TableHead>beta</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(portfolioRisk.rows || []).map((row) => (
                  <TableRow key={row.symbol}>
                    <TableCell><strong>{row.symbol}</strong><div className="muted">{row.name}</div></TableCell>
                    <TableCell>{text(row.style_profile, "N/A")}</TableCell>
                    <TableCell><Badge variant={badgeVariant(row.realized_risk_profile || row.risk_profile)}>{row.realized_risk_profile || row.risk_profile || "N/A"}</Badge><div className="muted">{score(row.realized_risk_score ?? row.risk_score, 2)}</div></TableCell>
                    <TableCell><Badge variant={badgeVariant(row.structural_risk_profile)}>{row.structural_risk_profile || "N/A"}</Badge><div className="muted">{score(row.structural_risk_score, 2)}</div></TableCell>
                    <TableCell>{pct(row.current_weight)}</TableCell>
                    <TableCell>{pct(row.volatility_60d)}</TableCell>
                    <TableCell>{score(row.beta_60d, 2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Section>

          <Section title="BUY Top 风险结构" eyebrow="Ranking Risk">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>rank</TableHead>
                  <TableHead>ETF</TableHead>
                  <TableHead>group</TableHead>
                  <TableHead>rank_score</TableHead>
                  <TableHead>style</TableHead>
                  <TableHead>近期风险</TableHead>
                  <TableHead>结构风险</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(buyRisk.rows || []).slice(0, 10).map((row) => (
                  <TableRow key={`${row.rank}-${row.symbol}`}>
                    <TableCell>{row.rank}</TableCell>
                    <TableCell><strong>{row.symbol}</strong><div className="muted">{row.name}</div></TableCell>
                    <TableCell>{row.group}</TableCell>
                    <TableCell>{score(row.rank_score, 2)}</TableCell>
                    <TableCell>{text(row.style_profile, "N/A")}</TableCell>
                    <TableCell><Badge variant={badgeVariant(row.realized_risk_profile || row.risk_profile)}>{row.realized_risk_profile || row.risk_profile || "N/A"}</Badge><div className="muted">{score(row.realized_risk_score ?? row.risk_score_profile, 2)}</div></TableCell>
                    <TableCell><Badge variant={badgeVariant(row.structural_risk_profile)}>{row.structural_risk_profile || "N/A"}</Badge><div className="muted">{score(row.structural_risk_score, 2)}</div></TableCell>
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
