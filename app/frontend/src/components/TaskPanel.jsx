import ActionButton from "./ActionButton.jsx";
import Section from "./Section.jsx";

const actions = [
  ["一键补齐 ETF 数据", "补最近缺口，只写本地行情和报告", "backfill_etf_data", "common"],
  ["刷新研究报告", "刷新信号、研究报告和看板", "refresh_all_reports", "common"],
  ["刷新模拟仓绩效", "只生成绩效报告，不改交易和持仓", "run_paper_performance", "common"],
  ["一键日更数据", "更新正式 ETF 池，只写本地行情", "update_daily_data", "advanced"],
  ["生成交易复盘报告", "只生成复盘报告，不改交易和持仓", "run_trade_review", "advanced"],
  ["回填历史权益曲线", "只生成派生曲线，不改交易和持仓", "run_paper_equity_backfill", "advanced"],
  ["刷新突破影子模型", "研究任务，不写正式持仓", "run_persistence_breakout_shadow", "advanced"],
  ["更新错失机会追踪", "研究任务，不改交易规则", "run_missed_opportunity_tracker", "advanced"],
  ["生成每周影子观察报告", "研究任务，不接执行层", "run_shadow_observation_weekly", "advanced"],
  ["更新策略预览跟踪", "研究任务，不执行交易", "run_strategy_preview_tracking", "advanced"],
  ["重建静态看板", "生成本地 HTML 和数据快照", "run_dashboard_build", "advanced"],
  ["创建本地 App 图标", "生成本地启动包装器", "create_app_shortcut", "advanced"],
  ["诊断 App 启动问题", "检查启动环境、端口和日志", "diagnose_app_launch", "advanced"],
  ["修复 App 启动权限", "修复本地权限和包装器", "fix_app_launch_permissions", "advanced"],
  ["检查 App 环境", "只读检查启动条件", "check_app_env", "advanced"],
  ["检查数据源", "小样本检查，不写正式数据", "check_data_source", "advanced"]
];

function statusCn(value) {
  const map = {
    success: "成功",
    warning: "注意",
    failed: "失败",
    running: "运行中",
    idle: "空闲"
  };
  return map[value] || value || "暂无";
}

export default function TaskPanel({ taskStatus, onRun, compact = false, allowedTasks = null }) {
  const running = Boolean(taskStatus?.running);
  const latest = taskStatus?.latest_task;
  const history = taskStatus?.history || [];
  const visibleActions = allowedTasks ? actions.filter(([, , taskName]) => allowedTasks.includes(taskName)) : actions;
  const commonActions = visibleActions.filter(([, , , group]) => group === "common");
  const advancedActions = visibleActions.filter(([, , , group]) => group !== "common");

  return (
    <Section title="安全快捷操作" eyebrow="白名单任务">
      <div className="task-safe-note">以下任务只会更新本地研究数据和报告，不会连接券商，不会真实交易。</div>
      <div className={compact ? "action-grid compact" : "action-grid compact"}>
        {commonActions.map(([title, note, taskName]) => (
          <ActionButton key={taskName} title={title} note={note} taskName={taskName} disabled={running} onRun={onRun} primary={taskName === "backfill_etf_data"} />
        ))}
      </div>

      {advancedActions.length ? (
        <details className="report-preview task-advanced">
          <summary><span>高级研究任务</span><em>默认折叠</em></summary>
          <div className="action-grid compact task-advanced-grid">
            {advancedActions.map(([title, note, taskName]) => (
              <ActionButton key={taskName} title={title} note={note} taskName={taskName} disabled={running} onRun={onRun} />
            ))}
          </div>
        </details>
      ) : null}

      <div className={`task-status ${running ? "running" : latest?.status || "idle"}`}>
        <div>
          <strong>{running ? "任务运行中" : "最近任务"}</strong>
          <span>{latest ? `${latest.description || latest.task_name} · ${statusCn(latest.status)} · ${latest.duration_label || "暂无耗时"}` : "暂无任务记录"}</span>
        </div>
        {latest ? (
          <div>
            <span>开始 {latest.started_at || "暂无"}</span>
            <span>结束 {latest.finished_at || "暂无"}</span>
            <span>退出码 {latest.exit_code ?? "暂无"}</span>
          </div>
        ) : null}
        {latest?.log_path ? <pre>{`日志路径：${latest.log_path}`}</pre> : null}
        {latest?.warning ? <pre>{latest.warning}</pre> : null}
        {latest?.data_update_status ? (
          <pre>{`数据更新：${latest.data_update_severity || "暂无"} / ${latest.data_update_status} · 本地最新 ${latest.data_update_latest_local_date || "暂无"} · 目标 ${latest.data_update_requested_end || "暂无"} · 新增 ${latest.data_update_added_rows ?? "暂无"}`}</pre>
        ) : null}
        {latest?.stdout_tail ? <pre>{latest.stdout_tail}</pre> : null}
        {latest?.stderr_tail ? <pre>{latest.stderr_tail}</pre> : null}
      </div>
      {history.length ? (
        <div className="task-history">
          {history.slice(0, 6).map((item) => (
            <div className="history-row" key={item.task_id || `${item.task_name}-${item.started_at}`}>
              <span>{item.description || item.task_name}</span>
              <b className={`mini-status ${item.status}`}>{statusCn(item.status)}</b>
              <em>{item.finished_at || item.started_at} · {item.duration_label || "暂无耗时"}</em>
            </div>
          ))}
        </div>
      ) : null}
    </Section>
  );
}
