import LogsPanel from "../components/LogsPanel.jsx";
import TaskPanel from "../components/TaskPanel.jsx";
import Section from "../components/Section.jsx";

export default function Logs({ logName, setLogName, logData, taskStatus, onRun }) {
  const history = taskStatus?.history || [];
  return (
    <main className="page-grid">
      <TaskPanel taskStatus={taskStatus} onRun={onRun} />
      <Section title="任务历史" eyebrow="最近安全任务">
        <div className="table-wrap">
          <table>
            <thead><tr><th>任务</th><th>状态</th><th>开始</th><th>结束</th><th>耗时</th><th>日志</th></tr></thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.task_id}>
                  <td>{row.task_name}<small>{row.description}</small></td>
                  <td><span className={`badge ${row.status === "success" ? "ok" : row.status === "warning" ? "warn" : "danger"}`}>{row.status}</span></td>
                  <td>{row.started_at}</td>
                  <td>{row.finished_at}</td>
                  <td>{row.duration_label || "暂无"}</td>
                  <td>{row.log_path}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <LogsPanel logName={logName} setLogName={setLogName} logData={logData} />
    </main>
  );
}
