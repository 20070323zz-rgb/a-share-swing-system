import { ArrowDownRight, ArrowUpRight, BarChart3, GitCompareArrows, Radar, ShieldCheck } from "lucide-react";
import SignalsPanel from "../components/SignalsPanel.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { score } from "../format.js";

function SignalMetric({ icon: Icon, label, value, note, tone = "blue" }) {
  return (
    <div className={`signal-metric ${tone}`}>
      <Icon size={18} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export default function Signals({ signals }) {
  const buyRows = signals?.buy_ranking || [];
  const entered = signals?.top3_entered || [];
  const exited = signals?.top3_exited || [];
  const trackingRows = signals?.tracking_rows || [];
  const pendingCount = trackingRows.filter((row) => String(row.forward_returns_status || "").toLowerCase() === "pending").length;

  return (
    <main className="page-grid signals-page">
      <section className="page-action-head signal-page-head">
        <div>
          <div className="eyebrow">Signal workspace</div>
          <h2>双周期信号观察</h2>
          <p>把原始排名、影子调整与后续收益回收放在同一个视图中。影子结果只用于研究，不改变正式模拟盘规则。</p>
        </div>
        <div className="action-head-side"><Badge variant="success"><ShieldCheck size={13} aria-hidden="true" />执行层锁定</Badge><Badge variant="blue">Preview only</Badge></div>
      </section>

      <section className="signal-metric-grid">
        <SignalMetric icon={Radar} label="原始候选" value={`${buyRows.length}`} note={buyRows[0] ? `Top 1 · ${buyRows[0].symbol}` : "等待生成"} />
        <SignalMetric icon={ArrowUpRight} label="进入调整后 Top3" value={`${entered.length}`} note={entered.join(" / ") || "无变化"} tone="positive" />
        <SignalMetric icon={ArrowDownRight} label="退出调整后 Top3" value={`${exited.length}`} note={exited.join(" / ") || "无变化"} tone="warning" />
        <SignalMetric icon={GitCompareArrows} label="待回收样本" value={`${pendingCount}`} note={`${trackingRows.length} 条追踪记录`} tone="violet" />
      </section>

      <SignalsPanel signals={signals} />

      <div className="split signal-detail-grid">
        <Section title="Top3 变化" eyebrow="影子排名差异">
          <div className="matrix compact-matrix">
            <div><span>进入调整后 top3</span><strong>{entered.join(" / ") || "无"}</strong></div>
            <div><span>退出调整后 top3</span><strong>{exited.join(" / ") || "无"}</strong></div>
            <div><span>执行开关</span><strong>{signals?.adjusted_rank_score_execution_enabled ? "开启" : "关闭"}</strong></div>
            <div><span>预览状态</span><strong>{signals?.preview_only ? "仅预览" : "暂无"}</strong></div>
          </div>
        </Section>
        <Section title="最大加减分" eyebrow="加分 / 惩罚">
          <div className="tracking-list">
            {(signals?.score_delta_extremes || []).slice(0, 8).map((row) => (
              <div className="tracking-row" key={`${row.symbol}-${row.score_delta}`}>
                <strong>{row.symbol} {row.name}</strong>
                <span>分差 {score(row.score_delta, 1)} · {row.enhancement_reason || row.difference_reason || "暂无原因"}</span>
              </div>
            ))}
            {!(signals?.score_delta_extremes || []).length ? <div className="v2-empty">暂无加减分差异。</div> : null}
          </div>
        </Section>
      </div>

      <Section title="最近影子跟踪" eyebrow="后续收益：等待 / 部分 / 完成">
        <div className="tracking-list signal-tracking-list">
          {trackingRows.slice(-16).reverse().map((row) => (
            <div className="tracking-row" key={`${row.snapshot_date}-${row.symbol}`}>
              <strong>{row.snapshot_date} · {row.symbol} {row.name}</strong>
              <span>{row.difference_reason || "已跟踪"} · {row.forward_returns_status || "等待"} · 1日 {score(row.forward_1d_return, 4)}</span>
            </div>
          ))}
          {!trackingRows.length ? <div className="v2-empty">暂无影子跟踪记录。</div> : null}
        </div>
      </Section>
    </main>
  );
}
