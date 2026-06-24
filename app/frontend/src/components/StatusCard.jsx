export default function StatusCard({ label, value, hint, status = "neutral" }) {
  return (
    <div className={`status-card ${status}`}>
      <div className="status-label">{label}</div>
      <div className="status-value">{value ?? "暂无"}</div>
      {hint ? <div className="status-hint">{hint}</div> : null}
    </div>
  );
}
