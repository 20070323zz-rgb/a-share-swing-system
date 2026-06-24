import SignalsPanel from "../components/SignalsPanel.jsx";
import Section from "../components/Section.jsx";
import { score } from "../format.js";

export default function Signals({ signals }) {
  return (
    <main className="page-grid">
      <SignalsPanel signals={signals} />
      <div className="split">
        <Section title="Top3 差异" eyebrow="影子排名差异">
          <div className="matrix">
            <div><span>进入调整后 top3</span><strong>{(signals?.top3_entered || []).join(" / ") || "无"}</strong></div>
            <div><span>退出调整后 top3</span><strong>{(signals?.top3_exited || []).join(" / ") || "无"}</strong></div>
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
          </div>
        </Section>
      </div>
      <Section title="最近影子跟踪" eyebrow="后续收益：等待 / 部分 / 完成">
        <div className="tracking-list">
          {(signals?.tracking_rows || []).slice(-16).reverse().map((row) => (
            <div className="tracking-row" key={`${row.snapshot_date}-${row.symbol}`}>
              <strong>{row.snapshot_date} · {row.symbol} {row.name}</strong>
              <span>{row.difference_reason || "已跟踪"} · {row.forward_returns_status || "等待"} · 1日 {score(row.forward_1d_return, 4)}</span>
            </div>
          ))}
        </div>
      </Section>
    </main>
  );
}
