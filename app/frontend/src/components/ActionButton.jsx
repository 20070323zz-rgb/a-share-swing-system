export default function ActionButton({ title, note, taskName, disabled, onRun, primary = false }) {
  return (
    <button className={`action-button ${primary ? "primary" : ""}`} disabled={disabled} onClick={() => onRun(taskName)}>
      <span>{title}</span>
      <small>{note}</small>
      <em>研究任务 · 不会真实交易</em>
    </button>
  );
}
