import { useId } from "react";

function toNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatAxisValue(value) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: Math.abs(value) >= 100 ? 0 : 2 }).format(value);
}

function formatDate(value) {
  const text = String(value || "");
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text.slice(5);
  return text || "暂无";
}

function formatFullDate(value) {
  const text = String(value || "");
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : text || "暂无";
}

export default function Sparkline({
  rows = [],
  valueKey = "total_equity",
  dateKey = "date",
  label = "趋势图",
  yLabel = "账户权益",
  yUnit = "元",
  xLabel = "日期",
  xUnit = "交易日"
}) {
  const reactId = useId();
  const gradientId = `sparkline-area-${reactId.replace(/:/g, "")}`;
  const series = rows
    .slice(-80)
    .map((row, index) => ({ value: toNumber(row[valueKey]), date: row[dateKey], index }))
    .filter((row) => row.value !== null);
  const points = series.map((row) => row.value);
  if (points.length < 2 || Math.max(...points) === Math.min(...points)) {
    return <div className="empty-note">暂无足够数据绘制{label}。</div>;
  }
  const width = 560;
  const height = 230;
  const plot = { left: 66, right: 18, top: 27, bottom: 42 };
  const plotWidth = width - plot.left - plot.right;
  const plotHeight = height - plot.top - plot.bottom;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const padding = Math.max((max - min) * 0.08, Math.abs(max) * 0.002);
  const axisMin = min - padding;
  const axisMax = max + padding;
  const yTicks = [axisMax, (axisMax + axisMin) / 2, axisMin];
  const xTickIndexes = [0, Math.floor((series.length - 1) / 2), series.length - 1];
  const path = points.map((value, index) => {
    const x = plot.left + (index * plotWidth) / Math.max(points.length - 1, 1);
    const y = plot.top + ((axisMax - value) / (axisMax - axisMin)) * plotHeight;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
  const lastValue = points[points.length - 1];
  const firstValue = points[0];
  const intervalReturn = firstValue ? (lastValue / firstValue - 1) * 100 : 0;
  const lastX = plot.left + plotWidth;
  const lastY = plot.top + ((axisMax - lastValue) / (axisMax - axisMin)) * plotHeight;
  const areaPath = `${path} L ${lastX.toFixed(2)} ${(height - plot.bottom).toFixed(2)} L ${plot.left.toFixed(2)} ${(height - plot.bottom).toFixed(2)} Z`;
  return (
    <div className="sparkline-frame">
      <div className="sparkline-context" aria-hidden="true">
        <span>{formatFullDate(series[0]?.date)} — {formatFullDate(series[series.length - 1]?.date)} · {series.length} 个有效点</span>
        <strong className={intervalReturn >= 0 ? "is-positive" : "is-negative"}>区间 {intervalReturn >= 0 ? "+" : ""}{intervalReturn.toFixed(2)}%</strong>
      </div>
      <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${gradientId}-title ${gradientId}-desc`}>
        <title id={`${gradientId}-title`}>{label}</title>
        <desc id={`${gradientId}-desc`}>{`${xLabel}轴单位为${xUnit}，${yLabel}轴单位为${yUnit}，数据从${formatFullDate(series[0]?.date)}到${formatFullDate(series[series.length - 1]?.date)}，最新值${formatAxisValue(lastValue)}${yUnit}。`}</desc>
        <defs>
          <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
            <stop className="sparkline-area-start" offset="0%" />
            <stop className="sparkline-area-end" offset="100%" />
          </linearGradient>
        </defs>
        <text className="sparkline-axis-title" x={plot.left} y="14">{yLabel}（{yUnit}）</text>
        {yTicks.map((tick, index) => {
          const y = plot.top + (index * plotHeight) / 2;
          return (
            <g key={`y-${tick}`}>
              <path className="sparkline-grid" d={`M ${plot.left} ${y} L ${width - plot.right} ${y}`} />
              <text className="sparkline-tick" x={plot.left - 8} y={y + 4} textAnchor="end">{formatAxisValue(tick)}</text>
            </g>
          );
        })}
        <path className="sparkline-axis" d={`M ${plot.left} ${plot.top} L ${plot.left} ${height - plot.bottom} L ${width - plot.right} ${height - plot.bottom}`} />
        {xTickIndexes.map((seriesIndex, index) => {
          const x = plot.left + (seriesIndex * plotWidth) / Math.max(series.length - 1, 1);
          return (
            <g key={`x-${seriesIndex}`}>
              <path className="sparkline-tick-mark" d={`M ${x} ${height - plot.bottom} L ${x} ${height - plot.bottom + 5}`} />
              <text className="sparkline-tick" x={x} y={height - 20} textAnchor={index === 0 ? "start" : index === 2 ? "end" : "middle"}>{formatDate(series[seriesIndex]?.date)}</text>
            </g>
          );
        })}
        <text className="sparkline-axis-title" x={width - plot.right} y={height - 5} textAnchor="end">{xLabel}（{xUnit}）</text>
        <path className="sparkline-area" d={areaPath} fill={`url(#${gradientId})`} />
        <path className="sparkline-latest-guide" d={`M ${lastX} ${plot.top} L ${lastX} ${height - plot.bottom}`} />
        <path className="sparkline-line" d={path} />
        <circle className="sparkline-end-halo" cx={lastX} cy={lastY} r="7" />
        <circle className="sparkline-end-dot" cx={lastX} cy={lastY} r="3.5" />
        <text className="sparkline-latest" x={lastX - 7} y={Math.max(plot.top + 12, lastY - 9)} textAnchor="end">{formatAxisValue(lastValue)} {yUnit}</text>
      </svg>
    </div>
  );
}
