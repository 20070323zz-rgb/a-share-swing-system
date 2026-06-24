import { text } from "../format.js";

export default function ReportCard({ title, file, status = "present", summary, children }) {
  const body = typeof summary === "string" ? summary : summary ? JSON.stringify(summary, null, 2) : "";
  return (
    <details className="report-preview">
      <summary>
        <span>{title}</span>
        <em>{status === "present" ? "已生成" : text(status, "等待更新")}</em>
      </summary>
      {children ? children : <pre>{body || "报告暂时不可用，请稍后刷新。"}</pre>}
      <small>{file || "本地报告"}</small>
    </details>
  );
}
