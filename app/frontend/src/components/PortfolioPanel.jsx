import Section from "./Section.jsx";
import { money, pct, text } from "../format.js";

function statusClass(value) {
  const upper = String(value || "").toUpperCase();
  if (upper.includes("SELL") || upper.includes("REDUCE") || upper.includes("CAUTION")) return "danger";
  if (upper.includes("REVIEW") || upper.includes("WATCH")) return "warn";
  return "ok";
}

export default function PortfolioPanel({ portfolio }) {
  const rows = portfolio?.positions || [];
  return (
    <Section title="当前持仓" eyebrow="组合决策视图">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ETF</th>
              <th>数量</th>
              <th>类型 / group</th>
              <th>持仓市值</th>
              <th>成本价</th>
              <th>最新价</th>
              <th>浮盈亏</th>
              <th>目标 / 当前权重</th>
              <th>信号状态</th>
              <th>止损距离</th>
              <th>风险标签</th>
              <th>动作建议</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.symbol}>
                <td>
                  <strong>{row.symbol}</strong>
                  <small>{text(row.name, "ETF")}</small>
                </td>
                <td className="num">{row.quantity ?? "暂无"}</td>
                <td>{text(row.etf_type)}<small>{text(row.group)}</small></td>
                <td className="num">{money(row.market_value)}<small>{pct(row.position_ratio)}</small></td>
                <td className="num">{row.avg_cost ?? row.entry_price ?? "暂无"}</td>
                <td className="num">{row.last_price ?? row.current_price ?? "暂无"}</td>
                <td className={`num ${Number(row.unrealized_pnl) >= 0 ? "cn-profit" : "cn-loss"}`}>
                  {money(row.unrealized_pnl)}<small>{pct(row.unrealized_pnl_pct)}</small>
                </td>
                <td className="num">{pct(row.target_weight ?? row.target_position_pct)}<small>{pct(row.position_ratio)}</small></td>
                <td>
                  <span className={`badge ${statusClass(row.signal_status)}`}>{row.signal_status || row.sell_review_status || "暂无"}</span>
                  <small>{row.current_signal || row.buy_signal || "暂无"}</small>
                </td>
                <td className="num">{pct(row.distance_to_stop_pct ?? row.stop_distance_pct)}<small>止损 {row.stop_loss_price || row.stop_loss || "暂无"}</small></td>
                <td><span className={`badge ${statusClass(row.risk_tag || row.health_status)}`}>{row.risk_tag || row.health_status || "正常"}</span></td>
                <td>
                  <strong>{row.action_suggestion || row.sell_review_status || "HOLD"}</strong>
                  <small>{row.research_note || row.health_note || row.buy_reason_short || ""}</small>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}
