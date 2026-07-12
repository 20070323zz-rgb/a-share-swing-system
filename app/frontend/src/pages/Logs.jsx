import { Activity, CheckCircle2, Clock3, TerminalSquare } from "lucide-react";
import LogsPanel from "../components/LogsPanel.jsx";
import TaskPanel from "../components/TaskPanel.jsx";
import Section from "../components/Section.jsx";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function statusVariant(value) {
  if (value === "success") return "success";
  if (value === "running") return "blue";
  if (value === "failed") return "danger";
  if (value === "warning") return "warning";
  return "neutral";
}

export default function Logs({ logName, setLogName, logData, taskStatus, onRun }) {
  const history = taskStatus?.history || [];
  const successCount = history.filter((row) => row.status === "success").length;
  const warningCount = history.filter((row) => row.status === "warning" || row.status === "failed").length;

  return (
    <main className="page-grid task-center-page">
      <section className="page-action-head task-center-head">
        <div>
          <div className="eyebrow">Automation workspace</div>
          <h2>任务与自动化中心</h2>
          <p>在这里运行白名单本地任务、查看最近结果和诊断日志。所有动作都限定在研究数据与报告层。</p>
        </div>
        <div className="action-head-side"><Badge variant={taskStatus?.running ? "blue" : "success"}><Activity size={13} aria-hidden="true" />{taskStatus?.running ? "任务运行中" : "系统空闲"}</Badge></div>
      </section>

      <section className="task-center-summary">
        <div><TerminalSquare size={18} aria-hidden="true" /><span>任务记录</span><strong>{history.length}</strong><small>最近白名单任务</small></div>
        <div><CheckCircle2 size={18} aria-hidden="true" /><span>成功</span><strong>{successCount}</strong><small>已完成的本地任务</small></div>
        <div><Clock3 size={18} aria-hidden="true" /><span>需复核</span><strong>{warningCount}</strong><small>warning / failed</small></div>
      </section>

      <TaskPanel taskStatus={taskStatus} onRun={onRun} />
      <Section title="任务历史" eyebrow="最近安全任务">
        <Table>
          <TableHeader><TableRow><TableHead>任务</TableHead><TableHead>状态</TableHead><TableHead>开始</TableHead><TableHead>结束</TableHead><TableHead>耗时</TableHead><TableHead>日志</TableHead></TableRow></TableHeader>
          <TableBody>
            {history.slice(0, 12).map((row) => (
              <TableRow key={row.task_id || `${row.task_name}-${row.started_at}`}>
                <TableCell><strong>{row.description || row.task_name}</strong><small>{row.safe_note || "只运行本地研究任务"}</small></TableCell>
                <TableCell><Badge variant={statusVariant(row.status)}>{row.status || "暂无"}</Badge></TableCell>
                <TableCell>{row.started_at || "暂无"}</TableCell>
                <TableCell>{row.finished_at || "暂无"}</TableCell>
                <TableCell>{row.duration_label || "暂无"}</TableCell>
                <TableCell>{row.log_path || "暂无"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!history.length ? <div className="v2-empty">暂无任务历史。</div> : null}
      </Section>
      <LogsPanel logName={logName} setLogName={setLogName} logData={logData} />
    </main>
  );
}
