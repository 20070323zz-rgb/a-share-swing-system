export function money(value) {
  if (value === null || value === undefined || value === "") return "暂无";
  const number = Number(value);
  if (!Number.isFinite(number)) return "暂无";
  return number.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function pct(value) {
  if (value === null || value === undefined || value === "") return "暂无";
  const number = Number(value);
  if (!Number.isFinite(number)) return "暂无";
  return `${(number * 100).toFixed(2)}%`;
}

export function score(value, digits = 1) {
  if (value === null || value === undefined || value === "") return "暂无";
  const number = Number(value);
  if (Number.isNaN(number)) return "暂无";
  return number.toFixed(digits);
}

export function text(value, fallback = "暂无") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}
