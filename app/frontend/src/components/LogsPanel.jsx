import Section from "./Section.jsx";

export default function LogsPanel({ logName, setLogName, logData }) {
  return (
    <Section title="运行日志" eyebrow="只读日志">
      <div className="log-tabs">
        {["latest_app_task.log", "app_server.log", "daily_close.log", "catchup_check.log", "app_tasks.log", "data_update_log.md"].map((name) => (
          <button className={name === logName ? "active" : ""} key={name} onClick={() => setLogName(name)}>{name}</button>
        ))}
      </div>
      <pre className="log-view">{logData?.tail || "暂无日志"}</pre>
    </Section>
  );
}
