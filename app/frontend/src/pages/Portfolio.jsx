import { useState } from "react";
import PortfolioPanel from "../components/PortfolioPanel.jsx";
import Section from "../components/Section.jsx";
import SegmentedControl from "../components/SegmentedControl.jsx";
import Sparkline from "../components/Sparkline.jsx";
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

function Metric({ label, value, note, tone = "" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function TradePnlTable({ rows = [] }) {
  if (!rows.length) return <div className="empty-note">暂无足够交易盈亏数据。</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ETF</th><th>买入 / 卖出</th><th>数量</th><th>价格</th><th>净盈亏</th><th>收益率</th><th>状态</th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(-20).map((row) => (
            <tr key={`${row.trade_id}-${row.symbol}`}>
              <td><strong>{row.symbol}</strong><small>{text(row.name, "ETF")}</small></td>
              <td>{text(row.buy_date)}<small>{row.sell_date || "未平仓"}</small></td>
              <td className="num">{shown(row.quantity)}</td>
              <td className="num">{shown(row.buy_price)} / {shown(row.sell_price)}</td>
              <td className={`num ${pnlClass(row.net_pnl)}`}>{signedMoney(row.net_pnl)}</td>
              <td className="num">{pct(row.return_pct)}</td>
              <td><span className={`badge ${row.status === "closed" ? "ok" : "warn"}`}>{text(row.status)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DailyTable({ rows = [] }) {
  if (!rows.length) return <div className="empty-note">暂无历史权益数据。</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>日期</th><th>总资产</th><th>每日盈亏</th><th>累计收益</th><th>回撤</th></tr></thead>
        <tbody>
          {rows.slice(-20).reverse().map((row) => (
            <tr key={row.date}>
              <td>{row.date}</td>
              <td className="num">{money(row.total_equity)}</td>
              <td className={`num ${pnlClass(row.daily_pnl)}`}>{signedMoney(row.daily_pnl)}</td>
              <td className="num">{pct(row.cumulative_return)}</td>
              <td className="num">{pct(row.drawdown)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
  const caution = positions.filter((row) => String(row.risk_tag || row.health_status || "").includes("CAUTION") || String(row.health_status || "").includes("提醒"));
  const options = [
    { value: "overview", label: "概览" },
    { value: "positions", label: "持仓" },
    { value: "history", label: "历史盈亏" },
    { value: "trades", label: "交易记录" }
  ];

  return (
    <main className="page-grid">
      <section className="apple-hero compact">
        <div>
          <div className="eyebrow">模拟仓</div>
          <h2>当前总资产 {money(performance.current_total_equity ?? summary.total_equity)}</h2>
          <p>这里展示模拟交易账户表现，不是真实账户。不会读取真实账户，不会真实下单。</p>
          <div className="hero-pills">
            <span className="status-pill ok">券商接口未连接</span>
            <span className="status-pill muted">真实交易禁用</span>
            <span className="status-pill blue">只读绩效展示</span>
          </div>
        </div>
        <div className="hero-orb-card">
          <span>总盈亏</span>
          <strong className={pnlClass(performance.total_pnl_amount)}>{signedMoney(performance.total_pnl_amount)}</strong>
          <small>总收益率 {pct(performance.total_return_pct)}</small>
        </div>
      </section>

      <SegmentedControl options={options} value={view} onChange={setView} />

      {view === "overview" ? (
        <>
          <section className="metric-grid">
            <Metric label="初始本金" value={money(performance.initial_cash)} note="正式模拟仓实际口径" />
            <Metric label="现金" value={money(performance.current_cash ?? summary.cash)} note={pct(summary.cash_ratio)} />
            <Metric label="持仓市值" value={money(performance.current_position_value ?? summary.market_value)} note={pct(summary.position_ratio)} />
            <Metric label="风险持仓" value={String(caution.length)} note={caution.map((row) => row.symbol).join(" / ") || "无"} tone={caution.length ? "warn" : "ok"} />
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
      ) : null}

      {view === "positions" ? (
        <>
          <PortfolioPanel portfolio={portfolio} />
          <Section title="持仓风险提示" eyebrow="Risk Notes">
            <div className="focus-grid">
              {positions.map((row) => (
                <div className="focus-card" key={row.symbol}>
                  <strong>{row.symbol} {row.name}</strong>
                  <span>{row.etf_type || "暂无"} · {row.group || "暂无"}</span>
                  <p>{row.action_suggestion || row.sell_review_status || "HOLD"} · 距离止损 {pct(row.distance_to_stop_pct ?? row.stop_distance_pct)}</p>
                  <small>{row.health_note || row.research_note || "暂无额外风险说明"}</small>
                </div>
              ))}
              {!positions.length ? <div className="empty-note">当前无模拟持仓。</div> : null}
            </div>
          </Section>
        </>
      ) : null}

      {view === "history" ? (
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
      ) : null}

      {view === "trades" ? (
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
                  <table>
                    <thead><tr><th>代码</th><th>买入日期</th><th>浮盈亏</th><th>MFE</th><th>MAE</th><th>复盘结论</th></tr></thead>
                    <tbody>
                      {tradeReviewOpen.map((row) => (
                        <tr key={`open-${row.symbol}`}>
                          <td><strong>{row.symbol}</strong><small>{text(row.name)}</small></td>
                          <td>{text(row.entry_date)}</td>
                          <td className={`num ${pnlClass(row.unrealized_pnl)}`}>{signedMoney(row.unrealized_pnl)}</td>
                          <td className="num">{signedMoney(row.max_favorable_excursion)}</td>
                          <td className="num">{signedMoney(row.max_adverse_excursion)}</td>
                          <td>{text(row.review_comment)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </div>
          </Section>
        </>
      ) : null}
    </main>
  );
}
