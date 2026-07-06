import Section from "./Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { money, pct, text } from "../format.js";

function statusVariant(value) {
  const upper = String(value || "").toUpperCase();
  if (upper.includes("SELL") || upper === "REDUCE" || upper.includes("ELEVATED")) return "danger";
  if (upper.includes("CAUTION")) return "warning";
  if (upper.includes("LOCK_CANDIDATE") || upper.includes("REDUCE_CANDIDATE") || upper.includes("REVIEW") || upper.includes("WATCH")) return "warning";
  return "success";
}

export default function PortfolioPanel({ portfolio }) {
  const rows = portfolio?.positions || [];
  return (
    <Section title="当前持仓" eyebrow="组合决策视图">
      <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ETF</TableHead>
              <TableHead>数量</TableHead>
              <TableHead>类型 / group</TableHead>
              <TableHead>持仓市值</TableHead>
              <TableHead>成本价</TableHead>
              <TableHead>最新价</TableHead>
              <TableHead>浮盈亏</TableHead>
              <TableHead>目标 / 当前权重</TableHead>
              <TableHead>信号状态</TableHead>
              <TableHead>观察状态</TableHead>
              <TableHead>浮盈保护</TableHead>
              <TableHead>高波动风险</TableHead>
              <TableHead>止损距离</TableHead>
              <TableHead>风险标签</TableHead>
              <TableHead>动作建议</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.symbol}>
                <TableCell>
                  <strong>{row.symbol}</strong>
                  <small>{text(row.name, "ETF")}</small>
                </TableCell>
                <TableCell className="num">{row.quantity ?? "暂无"}</TableCell>
                <TableCell>{text(row.etf_type)}<small>{text(row.group)}</small></TableCell>
                <TableCell className="num">{money(row.market_value)}<small>{pct(row.position_ratio)}</small></TableCell>
                <TableCell className="num">{row.avg_cost ?? row.entry_price ?? "暂无"}</TableCell>
                <TableCell className="num">{row.last_price ?? row.current_price ?? "暂无"}</TableCell>
                <TableCell className={`num ${Number(row.unrealized_pnl) >= 0 ? "cn-profit" : "cn-loss"}`}>
                  {money(row.unrealized_pnl)}<small>{pct(row.unrealized_pnl_pct)}</small>
                </TableCell>
                <TableCell className="num">{pct(row.target_weight ?? row.target_position_pct)}<small>{pct(row.position_ratio)}</small></TableCell>
                <TableCell>
                  <Badge variant={statusVariant(row.signal_status)}>{row.signal_status || row.sell_review_status || "暂无"}</Badge>
                  <small>{row.current_signal || row.buy_signal || "暂无"}</small>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant(row.review_state)}>{row.review_state_cn || row.review_state || "暂无"}</Badge>
                  <small>{row.execution_allowed === true ? "需复核" : "观察状态，不会自动交易"}</small>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant(row.profit_protection_state)}>{row.profit_protection_state_cn || row.profit_protection_state || "暂无"}</Badge>
                  <small>峰值回撤 {pct(row.drawdown_from_profit_peak_pct)} · 不自动止盈</small>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant(row.high_beta_risk_state)}>{row.high_beta_risk_state || "暂无"}</Badge>
                  <small>10日波动 {pct(row.high_beta_recent_volatility_10d)} · 回撤 {pct(row.high_beta_recent_drawdown_10d)}</small>
                </TableCell>
                <TableCell className="num">{pct(row.distance_to_stop_pct ?? row.stop_distance_pct)}<small>止损 {row.stop_loss_price || row.stop_loss || "暂无"}</small></TableCell>
                <TableCell><Badge variant={statusVariant(row.risk_tag || row.health_status)}>{row.risk_tag || row.health_status || "正常"}</Badge></TableCell>
                <TableCell>
                  <strong>{row.action_suggestion || row.sell_review_status || "HOLD"}</strong>
                  <small>{row.high_beta_risk_reasons || row.profit_protection_reasons || row.review_reasons || row.research_note || row.health_note || row.buy_reason_short || ""}</small>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
      </Table>
    </Section>
  );
}
