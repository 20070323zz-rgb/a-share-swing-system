import { useState } from "react";
import PortfolioPanel from "../components/PortfolioPanel.jsx";
import Section from "../components/Section.jsx";
import Sparkline from "../components/Sparkline.jsx";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { money, pct, text } from "../format.js";

function safeNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function signedMoney(value) {
  if (value === null || value === undefined || value === "" || Number.isNaN(value)) return "暂无";
  const number = safeNumber(value);
  const sign = number > 0 ? "+" : "";
  return `${sign}${money(number)}`;
}

function pnlClass(value) {
  const number = safeNumber(value);
  if (number > 0) return "cn-profit";
  if (number < 0) return "cn-loss";
  return "";
}

function shown(value, fallback = "暂无") {
  if (value === null || value === undefined || value === "" || Number.isNaN(value)) return fallback;
  return String(value);
}

function Metric({ label, value, note }) {
  return (
    <div className="mono-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function TradePnlTable({ rows = [] }) {
  if (!rows.length) return <div className="empty-note">暂无足够交易盈亏数据。</div>;
  return (
    <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ETF</TableHead><TableHead>买入 / 卖出</TableHead><TableHead>数量</TableHead><TableHead>价格</TableHead><TableHead>净盈亏</TableHead><TableHead>收益率</TableHead><TableHead>状态</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.slice(-20).map((row) => (
            <TableRow key={`${row.trade_id}-${row.symbol}`}>
              <TableCell><strong>{row.symbol}</strong><small>{text(row.name, "ETF")}</small></TableCell>
              <TableCell>{text(row.buy_date)}<small>{row.sell_date || "未平仓"}</small></TableCell>
              <TableCell className="num">{shown(row.quantity)}</TableCell>
              <TableCell className="num">{shown(row.buy_price)} / {shown(row.sell_price)}</TableCell>
              <TableCell className={`num ${pnlClass(row.net_pnl)}`}>{signedMoney(row.net_pnl)}</TableCell>
              <TableCell className="num">{pct(row.return_pct)}</TableCell>
              <TableCell><Badge variant={row.status === "closed" ? "success" : "warning"}>{text(row.status)}</Badge></TableCell>
            </TableRow>
          ))}
        </TableBody>
    </Table>
  );
}

function DailyTable({ rows = [] }) {
  if (!rows.length) return <div className="empty-note">暂无历史权益数据。</div>;
  return (
    <Table>
        <TableHeader><TableRow><TableHead>日期</TableHead><TableHead>总资产</TableHead><TableHead>每日盈亏</TableHead><TableHead>累计收益</TableHead><TableHead>回撤</TableHead></TableRow></TableHeader>
        <TableBody>
          {rows.slice(-20).reverse().map((row) => (
            <TableRow key={row.date}>
              <TableCell>{row.date}</TableCell>
              <TableCell className="num">{money(row.total_equity)}</TableCell>
              <TableCell className={`num ${pnlClass(row.daily_pnl)}`}>{signedMoney(row.daily_pnl)}</TableCell>
              <TableCell className="num">{pct(row.cumulative_return)}</TableCell>
              <TableCell className="num">{pct(row.drawdown)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
    </Table>
  );
}

export default function Portfolio({ portfolio }) {
  const [view, setView] = useState("overview");
  const summary = portfolio?.summary || {};
  const performance = portfolio?.performance || {};
  const equityMeta = portfolio?.equity_curve_meta || {};
  const equityCurve = portfolio?.equity_curve || [];
  const tradePnl = portfolio?.trade_pnl || [];
  const tradeReview = portfolio?.trade_review || {};
  const tradeReviewDetails = portfolio?.trade_review_details || [];
  const tradeReviewOpen = portfolio?.trade_review_open_positions || [];
  const positions = portfolio?.positions || [];
  const reviewRows = portfolio?.position_review_state || [];
  const reviewSummary = portfolio?.review_summary || {};
  const profitRows = portfolio?.profit_protection_preview || [];
  const profitSummary = portfolio?.profit_protection_summary || {};
  const highBetaRows = portfolio?.high_beta_risk_watch || [];
  const highBetaSummary = portfolio?.high_beta_risk_summary || {};
  const broadBasePreview = portfolio?.broad_base_balance_preview || {};
  const broadBaseSummary = portfolio?.broad_base_balance_summary || {};
  const caution = positions.filter((row) => String(row.risk_tag || row.health_status || "").includes("CAUTION") || String(row.health_status || "").includes("提醒"));
  return (
    <main className="page-grid">
      <section className="mono-page-head">
        <div>
          <h2>模拟仓</h2>
          <p>只读展示模拟交易账户表现，不读取真实账户，不真实下单。</p>
        </div>
        <div className="mono-head-actions">
          <Badge variant="success">券商接口未连接</Badge>
          <Badge variant="neutral">真实交易禁用</Badge>
          <Badge variant={Number(performance.total_pnl_amount || 0) >= 0 ? "success" : "warning"}>{signedMoney(performance.total_pnl_amount)}</Badge>
        </div>
      </section>

      <section className="mono-metric-row">
        <Metric label="总资产" value={money(performance.current_total_equity ?? summary.total_equity)} note="正式模拟仓" />
        <Metric label="收益" value={pct(performance.total_return_pct)} note={signedMoney(performance.total_pnl_amount)} />
        <Metric label="现金" value={money(performance.current_cash ?? summary.cash)} note={pct(summary.cash_ratio)} />
        <Metric label="持仓市值" value={money(performance.current_position_value ?? summary.market_value)} note={pct(summary.position_ratio)} />
      </section>

      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="positions">持仓</TabsTrigger>
          <TabsTrigger value="history">历史盈亏</TabsTrigger>
          <TabsTrigger value="trades">交易记录</TabsTrigger>
        </TabsList>

      <TabsContent value="overview">
        <>
          <section className="mono-metric-row secondary">
            <Metric label="风险持仓" value={String(caution.length)} note={caution.map((row) => row.symbol).join(" / ") || "无"} tone={caution.length ? "warn" : "ok"} />
            <Metric label="减仓候选观察" value={String(reviewSummary.reduce_candidate_count ?? 0)} note="观察状态，不会自动交易" tone={(reviewSummary.reduce_candidate_count ?? 0) ? "warn" : "ok"} />
            <Metric label="浮盈保护观察" value={String(profitSummary.profit_watch_count ?? 0)} note="研究指标，不自动止盈" tone={(profitSummary.profit_watch_count ?? 0) ? "warn" : "ok"} />
            <Metric label="高波动观察" value={shown(highBetaSummary.high_beta_exposure_state, "HB_NORMAL")} note={`${highBetaSummary.high_beta_position_count ?? 0} 只 · 权益 ${pct(highBetaSummary.high_beta_weight_of_equity)}`} tone={highBetaSummary.high_beta_exposure_state && highBetaSummary.high_beta_exposure_state !== "HB_NORMAL" ? "warn" : "ok"} />
            <Metric label="宽基平衡观察" value={shown(broadBaseSummary.broad_base_balance_state, "UNKNOWN")} note={`宽基 ${pct(broadBaseSummary.broad_base_weight)} · 候选 ${broadBaseSummary.balance_candidate_count ?? 0}`} tone={broadBaseSummary.broad_base_balance_state === "BROAD_BASE_BALANCED" ? "ok" : "warn"} />
            <Metric label="已实现盈亏" value={signedMoney(performance.realized_pnl)} note="来自卖出交易" tone={pnlClass(performance.realized_pnl)} />
            <Metric label="未实现盈亏" value={signedMoney(performance.unrealized_pnl)} note="当前持仓估值" tone={pnlClass(performance.unrealized_pnl)} />
            <Metric label="最大回撤" value={pct(performance.max_drawdown)} note={`最高权益 ${money(performance.max_equity)}`} />
            <Metric label="交易次数" value={String(performance.trade_count ?? 0)} note={`买 ${performance.buy_count ?? 0} · 卖 ${performance.sell_count ?? 0}`} />
          </section>
          <Section title="绩效曲线" eyebrow="Equity Curve">
            {equityMeta?.app_uses_backfilled_curve ? (
              <div className="empty-note">历史回填数据（估算）：由交易流水和 ETF 历史收盘价重建，早期模拟仓未持续保存每日账户快照。</div>
            ) : null}
            <Sparkline rows={equityCurve} label="模拟仓权益曲线" />
          </Section>
          <Section title="交易复盘摘要" eyebrow="Trade Review">
            <div className="metric-grid">
              <Metric label="最大浮盈（MFE）" value={pct(tradeReview.largest_mfe_pct)} note="日线 high 估算" />
              <Metric label="最大浮亏（MAE）" value={pct(tradeReview.largest_mae_pct)} note="日线 low 估算" />
              <Metric label="已平仓 / 未平仓" value={`${tradeReview.closed_trade_count ?? 0} / ${tradeReview.open_position_count ?? 0}`} note="完整闭环仍少" />
              <Metric label="样本提醒" value="证据不足" note={text(tradeReview.sample_warning, "样本较少，不能判断策略稳定盈利。")} tone="warn" />
            </div>
          </Section>
        </>
      </TabsContent>

      <TabsContent value="positions">
        <>
          <PortfolioPanel portfolio={portfolio} />
          <Section title="持仓风险提示" eyebrow="Risk Notes">
            <div className="empty-note">以下为模拟仓观察状态，不会自动交易；REDUCE_CANDIDATE 不是减仓指令。</div>
            <div className="empty-note">浮盈保护为研究观察指标，不会自动止盈；PROFIT_LOCK_CANDIDATE 也不是卖出信号。</div>
            <div className="empty-note">高波动风险为观察指标；证券类 ETF 对市场情绪敏感，页面不会提供真实交易按钮。</div>
            <div className="empty-note">宽基平衡观察：仅为 preview，不会自动买入。{broadBaseSummary.summary_text || ""}</div>
            <div className="focus-grid">
              {(broadBasePreview.top_balance_candidates || broadBasePreview.rows || []).slice(0, 3).map((row) => (
                <div className="focus-card" key={`broad-${row.symbol}`}>
                  <strong>{row.symbol} {row.name}</strong>
                  <span>宽基候选 · {row.mid_trend || "N/A"} / {row.short_swing || "N/A"} · balance rank {row.balance_candidate_rank}</span>
                  <p>假设加入后宽基占比 {pct(row.new_broad_base_weight)} · 集中度改善 {pct(row.concentration_change)}</p>
                  <small>{row.candidate_reason || "宽基平衡 preview，观察用，不自动交易。"}</small>
                </div>
              ))}
              {positions.map((row) => {
                const review = reviewRows.find((item) => String(item.symbol) === String(row.symbol)) || row;
                const profit = profitRows.find((item) => String(item.symbol) === String(row.symbol)) || row;
                const highBeta = highBetaRows.find((item) => String(item.symbol) === String(row.symbol)) || row;
                return (
                <div className="focus-card" key={row.symbol}>
                  <strong>{row.symbol} {row.name}</strong>
                  <span>{row.etf_type || "暂无"} · {row.group || "暂无"} · {review.review_state_cn || review.review_state || "暂无"} · {profit.profit_protection_state_cn || profit.profit_protection_state || "暂无"} · {highBeta.high_beta_risk_state || "高波动暂无"}</span>
                  <p>{review.recommended_review_action || row.action_suggestion || row.sell_review_status || "HOLD"} · 距离止损 {pct(row.distance_to_stop_pct ?? row.stop_distance_pct)}</p>
                  <small>{highBeta.high_beta_risk_reasons || profit.profit_protection_reasons || review.review_reasons || row.health_note || row.research_note || "暂无额外风险说明"}</small>
                </div>
              );})}
              {!positions.length ? <div className="empty-note">当前无模拟持仓。</div> : null}
            </div>
          </Section>
        </>
      </TabsContent>

      <TabsContent value="history">
        <>
          <Section title="历史盈亏" eyebrow="Equity & Drawdown">
            <div className="empty-note">
              {equityMeta?.display_note || "早期模拟仓未持续保存每日账户快照；如存在回填曲线，页面会明确标注估算口径。"}
            </div>
            <Sparkline rows={equityCurve} label="历史盈亏曲线" />
          </Section>
          <Section title="每日权益记录" eyebrow="Daily">
            <DailyTable rows={equityCurve} />
          </Section>
        </>
      </TabsContent>

      <TabsContent value="trades">
        <>
          <Section title="交易记录与 PnL" eyebrow="Trades">
            <TradePnlTable rows={tradePnl} />
          </Section>
          <Section title="交易复盘详情" eyebrow="Details">
            <div className="report-preview-grid">
              <details className="report-preview">
                <summary><span>已平仓交易复盘</span><em>点击展开</em></summary>
                <TradePnlTable rows={tradeReviewDetails.filter((row) => row.status === "closed")} />
              </details>
              <details className="report-preview">
                <summary><span>未平仓持仓复盘</span><em>点击展开</em></summary>
                <div className="table-wrap">
                  <Table>
                    <TableHeader><TableRow><TableHead>代码</TableHead><TableHead>买入日期</TableHead><TableHead>浮盈亏</TableHead><TableHead>MFE</TableHead><TableHead>MAE</TableHead><TableHead>复盘结论</TableHead></TableRow></TableHeader>
                    <TableBody>
                      {tradeReviewOpen.map((row) => (
                        <TableRow key={`open-${row.symbol}`}>
                          <TableCell><strong>{row.symbol}</strong><small>{text(row.name)}</small></TableCell>
                          <TableCell>{text(row.entry_date)}</TableCell>
                          <TableCell className={`num ${pnlClass(row.unrealized_pnl)}`}>{signedMoney(row.unrealized_pnl)}</TableCell>
                          <TableCell className="num">{signedMoney(row.max_favorable_excursion)}</TableCell>
                          <TableCell className="num">{signedMoney(row.max_adverse_excursion)}</TableCell>
                          <TableCell>{text(row.review_comment)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </details>
            </div>
          </Section>
        </>
      </TabsContent>
      </Tabs>
    </main>
  );
}
