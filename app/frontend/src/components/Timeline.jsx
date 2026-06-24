export default function Timeline({ items = [] }) {
  if (!items.length) {
    return <div className="empty-note">暂无项目阶段记录。</div>;
  }
  return (
    <div className="timeline-soft">
      {items.map((item) => (
        <div className={`timeline-soft-item ${item.tone || ""}`} key={item.title}>
          <span>{item.date || "当前"}</span>
          <strong>{item.title}</strong>
          <small>{item.note}</small>
        </div>
      ))}
    </div>
  );
}
