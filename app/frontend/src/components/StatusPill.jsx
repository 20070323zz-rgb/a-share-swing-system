import { text } from "../format.js";

export default function StatusPill({ children, tone = "neutral" }) {
  return <span className={`status-pill ${tone}`}>{text(children, "暂无数据")}</span>;
}
