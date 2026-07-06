function toNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export default function Sparkline({ rows = [], valueKey = "total_equity", label = "趋势图" }) {
  const points = rows
    .slice(-80)
    .map((row) => toNumber(row[valueKey]))
    .filter((value) => value !== null);
  if (points.length < 2 || Math.max(...points) === Math.min(...points)) {
    return <div className="empty-note">暂无足够数据绘制{label}。</div>;
  }
  const width = 480;
  const height = 170;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const path = points.map((value, index) => {
    const x = 14 + (index * (width - 28)) / Math.max(points.length - 1, 1);
    const y = 14 + ((max - value) / (max - min)) * (height - 28);
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
      <path className="sparkline-grid" d={`M 14 14 L ${width - 14} 14`} />
      <path className="sparkline-grid" d={`M 14 ${Math.round(height / 2)} L ${width - 14} ${Math.round(height / 2)}`} />
      <path className="sparkline-grid" d={`M 14 ${height - 14} L ${width - 14} ${height - 14}`} />
      <path className="sparkline-line" d={path} />
    </svg>
  );
}
