import Section from "./Section.jsx";
import { score, text } from "../format.js";

function MiniBar({ value }) {
  const width = Math.max(0, Math.min(100, Number(value || 0)));
  return <span className="mini-bar"><i style={{ width: `${width}%` }} /></span>;
}

function RankList({ title, rows, rankKey, scoreKey }) {
  return (
    <div className="rank-box">
      <h3>{title}</h3>
      {(rows || []).slice(0, 10).map((row) => (
        <div className="rank-row" key={`${title}-${row.symbol}`}>
          <span className="rank-no">#{row[rankKey] || "暂无"}</span>
          <span className="rank-name"><strong>{row.symbol}</strong> {row.name}<small>{row.group || row.etf_type || row.difference_reason || ""}</small></span>
          <span className="rank-score">{score(row[scoreKey], 1)}</span>
        </div>
      ))}
    </div>
  );
}

export default function SignalsPanel({ signals }) {
  const buyRows = signals?.buy_ranking || [];
  const topDiff = signals?.top3_difference || [];
  return (
    <Section title="买入排名与影子预览" eyebrow="原始排名与调整后预览">
      <div className="preview-banner">
        <strong>调整后排名当前只展示，不进入执行层。</strong>
        <span>Top3 差异：{topDiff.length ? topDiff.join(" / ") : "暂无"}；执行层仍使用原规则。</span>
      </div>
      <div className="split">
        <RankList title="原始排名 Top 10" rows={signals?.original_top10} rankKey="original_rank" scoreKey="original_rank_score" />
        <RankList title="调整后预览 Top 10" rows={signals?.adjusted_preview_top10} rankKey="adjusted_rank_preview" scoreKey="adjusted_rank_score_preview" />
      </div>
      <div className="table-wrap compact-table">
        <table>
          <thead>
            <tr>
              <th>排名</th>
              <th>ETF</th>
              <th>总分</th>
              <th>mid</th>
              <th>short</th>
              <th>流动性</th>
              <th>风险</th>
              <th>共振</th>
              <th>质量</th>
              <th>风险提示</th>
            </tr>
          </thead>
          <tbody>
            {buyRows.slice(0, 12).map((row, index) => (
              <tr key={`${row.symbol}-${index}`}>
                <td>#{row.rank || index + 1}</td>
                <td><strong>{row.symbol}</strong><small>{text(row.name)} · {text(row.group)}</small></td>
                <td>{score(row.rank_score, 1)}</td>
                <td><MiniBar value={row.mid_trend_score} />{score(row.mid_trend_score, 0)}</td>
                <td><MiniBar value={row.short_momentum_score} />{score(row.short_momentum_score, 0)}</td>
                <td><MiniBar value={row.liquidity_score} />{score(row.liquidity_score, 0)}</td>
                <td><MiniBar value={row.risk_score} />{score(row.risk_score, 0)}</td>
                <td>{row.resonance ? <span className="badge ok">共振</span> : score(row.resonance_score, 0)}</td>
                <td>{score(row.data_quality_score, 0)}</td>
                <td>{row.risk_note || row.candidate_action || "暂无提示"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}
