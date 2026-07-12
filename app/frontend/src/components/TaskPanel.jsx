import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import Section from "./Section.jsx";

const actions = [
  ["一键补齐 ETF 数据", "先核对价格日期，只在发现缺口时下载", "backfill_etf_data", "common"],
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

function statusVariant(value) {
  if (value === "success") return "success";
  if (value === "running") return "blue";
  if (value === "failed") return "danger";
  if (value === "warning") return "warning";
  return "neutral";
}

function latestTaskDisplay(latest, running) {
  if (running) return { title: "任务运行中", label: "运行中", variant: "blue" };
  if (latest?.data_update_status === "up_to_date") return { title: "数据检查完成", label: "已是最新", variant: "success" };
  if (latest?.data_update_status === "updated") return { title: "数据补齐完成", label: "有新增", variant: "success" };
  return { title: "最近任务", label: statusCn(latest?.status || "idle"), variant: statusVariant(latest?.status || "idle") };
}

function ActionRow({ title, note, taskName, running, primary, onRun }) {
  return (
    <div className="task-action-row">
      <div>
        <strong>{title}</strong>
        <p>{note}</p>
        <small title={taskName}>{taskName}</small>
      </div>
      <Button size="sm" variant={primary ? "default" : "secondary"} disabled={running} onClick={() => onRun?.(taskName)} type="button">
        运行
      </Button>
    </div>
  );
}

export default function TaskPanel({ taskStatus, onRun, compact = false, allowedTasks = null }) {
  const running = Boolean(taskStatus?.running);
  const latest = taskStatus?.latest_task;
  const history = taskStatus?.history || [];
  const visibleActions = allowedTasks ? actions.filter(([, , taskName]) => allowedTasks.includes(taskName)) : actions;
  const commonActions = visibleActions.filter(([, , , group]) => group === "common");
  const advancedActions = visibleActions.filter(([, , , group]) => group !== "common");
  const latestDisplay = latestTaskDisplay(latest, running);

  return (
    <Section title="安全快捷操作" eyebrow="白名单任务">
      <div className="task-safe-note">以下任务只更新本地研究数据和报告，不连接券商，不真实交易。</div>
      <div className={compact ? "task-action-list compact" : "task-action-list"}>
        {commonActions.map(([title, note, taskName]) => (
          <ActionRow key={taskName} title={title} note={note} taskName={taskName} running={running} onRun={onRun} primary={taskName === "backfill_etf_data"} />
        ))}
      </div>

      {advancedActions.length ? (
        <Collapsible className="task-advanced-panel">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" type="button">展开高级任务</Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="task-action-list compact">
              {advancedActions.map(([title, note, taskName]) => (
                <ActionRow key={taskName} title={title} note={note} taskName={taskName} running={running} onRun={onRun} />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ) : null}

      <Separator />
      <div className={`task-status ${running ? "running" : latest?.status || "idle"}`}>
        <div>
          <strong>{latestDisplay.title}</strong>
          <Badge variant={latestDisplay.variant}>{latestDisplay.label}</Badge>
        </div>
        <p>{latest ? `${latest.description || latest.task_name} · ${latest.duration_label || "暂无耗时"}` : "暂无任务记录"}</p>
        {latest?.data_update_status ? (
          <small>{`价格日 ${latest.data_update_latest_local_date || "暂无"} / 目标 ${latest.data_update_requested_end || "暂无"} · 检查 ${latest.data_update_processed_symbols ?? "暂无"} 只 · 已更新 ${latest.data_update_up_to_date_count ?? "暂无"} 只 · 新增 ${latest.data_update_added_rows ?? "暂无"} 行 · 请求 ${latest.data_update_actual_api_calls ?? "暂无"} 次`}</small>
        ) : null}
        {latest?.log_path ? <small>{`日志路径：${latest.log_path}`}</small> : null}
        {latest?.warning ? <pre>{latest.warning}</pre> : null}
        {latest?.stdout_tail || latest?.stderr_tail ? (
          <ScrollArea className="task-tail">
            <pre>{[latest.stdout_tail, latest.stderr_tail].filter(Boolean).join("\n")}</pre>
          </ScrollArea>
        ) : null}
      </div>
      {history.length ? (
        <div className="task-history-list">
          {history.slice(0, 6).map((item) => (
            <div className="task-history-row" key={item.task_id || `${item.task_name}-${item.started_at}`}>
              <span>{item.description || item.task_name}</span>
              <Badge variant={statusVariant(item.status)}>{statusCn(item.status)}</Badge>
              <small>{item.finished_at || item.started_at} · {item.duration_label || "暂无耗时"}</small>
            </div>
          ))}
        </div>
      ) : null}
    </Section>
  );
}
