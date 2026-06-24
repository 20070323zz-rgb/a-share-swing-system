import { useState } from "react";
import LogsPanel from "../components/LogsPanel.jsx";
import Section from "../components/Section.jsx";
import SegmentedControl from "../components/SegmentedControl.jsx";
import TaskPanel from "../components/TaskPanel.jsx";

function SafetyCard({ label, value, okWhen = false, note }) {
  const ok = Boolean(value) === okWhen;
  return (
    <div className={`metric-card ${ok ? "ok" : "warn"}`}>
      <span>{label}</span>
      <strong>{Boolean(value) ? "开启" : "关闭"}</strong>
      <small>{note}</small>
    </div>
  );
}

const allowedTaskNames = [
  "backfill_etf_data",
  "refresh_all_reports",
  "run_paper_performance",
  "run_persistence_breakout_shadow",
  "run_missed_opportunity_tracker",
  "run_shadow_observation_weekly",
  "run_strategy_preview_tracking",
  "run_dashboard_build",
  "run_paper_equity_backfill",
  "run_trade_review",
  "create_app_shortcut",
  "diagnose_app_launch",
  "fix_app_launch_permissions"
];

export default function SettingsSafety({ safety, appEnv, refreshAppEnv, onRun, taskStatus, logName, setLogName, logData }) {
  const [view, setView] = useState("safety");
  const history = taskStatus?.history || [];
  const launchStatus = safety?.app_launch_status || {};
  const diagnostics = safety?.app_launch_diagnostics || {};
  const appShortcut = safety?.app_shortcut || {};
  const options = [
    { value: "safety", label: "安全边界" },
    { value: "launch", label: "启动方式" },
    { value: "tasks", label: "常用任务" },
    { value: "diagnostics", label: "高级诊断" },
    { value: "logs", label: "日志" }
  ];
  return (
    <main className="page-grid">
      <section className="apple-hero compact">
        <div>
          <div className="eyebrow">设置与安全</div>
          <h2>L2 本地研究边界。</h2>
          <p>这里集中展示启动环境、白名单任务和安全边界。所有任务都是本地研究任务，不会真实交易。</p>
        </div>
        <span className="status-pill ok">不连接券商 · 不真实交易</span>
      </section>

      <SegmentedControl options={options} value={view} onChange={setView} />

      {view === "safety" ? (
        <>
          <section className="metric-grid">
            <div className="metric-card ok"><span>当前权限等级</span><strong>L2</strong><small>本地工程和数据权限</small></div>
            <SafetyCard label="真实交易" value={safety?.real_trade_enabled} note="必须关闭" />
            <SafetyCard label="券商接口" value={safety?.broker_api_enabled} note="必须未连接" />
            <SafetyCard label="真实账户读取" value={safety?.real_account_read_enabled} note="必须关闭" />
            <SafetyCard label="Shadow 接执行层" value={safety?.shadow_model_execution_enabled} note="必须关闭" />
            <SafetyCard label="真实下单按钮" value={safety?.real_order_buttons_enabled} note="必须不存在" />
            <SafetyCard label="网页任意命令" value={safety?.arbitrary_command_enabled} note="必须关闭" />
            <div className="metric-card ok"><span>执行层</span><strong>锁定</strong><small>正式模型未被 shadow 替代</small></div>
          </section>
          <Section title="永久禁止事项" eyebrow="安全边界">
            <div className="rule-list">
              <span>禁止登录券商账户</span><span>禁止真实买入</span><span>禁止真实卖出</span><span>禁止读取真实账户</span><span>禁止同步真实持仓</span><span>禁止把 shadow 模型接入正式执行层</span>
            </div>
          </Section>
        </>
      ) : null}

      {view === "launch" ? (
        <Section title="启动方式" eyebrow="本地 App">
          <div className="metric-grid">
            <div className={`metric-card ${appShortcut?.status === "active" ? "ok" : "warn"}`}><span>本地 App 图标</span><strong>{appShortcut?.status === "active" ? "已支持" : "待修复"}</strong><small>{appShortcut?.app_bundle || "dist/量化研究控制台.app"}</small></div>
            <div className="metric-card"><span>双击启动器</span><strong>已支持</strong><small>打开量化研究控制台.command</small></div>
            <div className="metric-card"><span>本地地址</span><strong>127.0.0.1:8000</strong><small>只在本机访问</small></div>
            <div className="metric-card"><span>日志位置</span><strong>logs/app_server.log</strong><small>启动和错误信息</small></div>
            <div className={`metric-card ${String(appEnv?.status || "").toLowerCase() === "ok" ? "ok" : "warn"}`}><span>环境检查</span><strong>{appEnv?.status || "等待检查"}</strong><small>不会显示 token / 密码</small></div>
            <div className={`metric-card ${launchStatus?.status === "running" || launchStatus?.status === "already_running" ? "ok" : launchStatus?.status === "error" ? "warn" : ""}`}><span>最近启动状态</span><strong>{launchStatus?.status || "暂无记录"}</strong><small>{launchStatus?.started_at || "暂无启动诊断记录"}</small></div>
          </div>
          <div className="empty-note">历史权益回填数据由交易流水和 ETF 历史收盘价估算生成；它是派生数据，不是真实每日账户快照。</div>
          <button className="mac-button" onClick={refreshAppEnv} type="button">重新检查环境</button>
          <details className="report-preview">
            <summary><span>环境检查输出</span><em>check_app_env.sh</em></summary>
            <pre>{appEnv?.output || "暂无环境检查输出"}</pre>
          </details>
        </Section>
      ) : null}

      {view === "tasks" ? <TaskPanel taskStatus={taskStatus} onRun={onRun} allowedTasks={allowedTaskNames} /> : null}

      {view === "diagnostics" ? (
        <>
          <Section title="启动与诊断" eyebrow="高级工具">
            <div className="metric-grid">
              <div className={`metric-card ${diagnostics?.overall_status === "OK" ? "ok" : diagnostics?.overall_status ? "warn" : ""}`}>
                <span>诊断状态</span>
                <strong>{diagnostics?.overall_status || "暂无诊断"}</strong>
                <small>{diagnostics?.checked_at || "请先运行一键诊断"}</small>
              </div>
              <div className="metric-card">
                <span>最近启动</span>
                <strong>{launchStatus?.status || "暂无记录"}</strong>
                <small>{launchStatus?.error_summary || launchStatus?.started_at || "暂无启动诊断记录"}</small>
              </div>
              <div className={`metric-card ${diagnostics?.port_status === "free" || diagnostics?.port_status === "project_app" ? "ok" : diagnostics?.port_status ? "warn" : ""}`}>
                <span>8000 端口</span>
                <strong>{diagnostics?.port_status || "未知"}</strong>
                <small>被占用时不会强杀进程</small>
              </div>
              <div className={`metric-card ${diagnostics?.gatekeeper_status === "clear" ? "ok" : diagnostics?.gatekeeper_status ? "warn" : ""}`}>
                <span>macOS 拦截</span>
                <strong>{diagnostics?.gatekeeper_status || "未检查"}</strong>
                <small>如打不开，请右键 App 选择“打开”</small>
              </div>
            </div>
            <div className="empty-note">{diagnostics?.recommendation || "暂无启动诊断记录。可以运行“诊断 App 启动问题”。"}</div>
            <div className="action-grid compact">
              <button className="action-button primary" type="button" onClick={() => onRun?.("diagnose_app_launch")}><span>诊断 App 启动问题</span><small>检查 .app、权限、端口、依赖和日志</small><em>本地检查 · 不会真实交易</em></button>
              <button className="action-button" type="button" onClick={() => onRun?.("fix_app_launch_permissions")}><span>修复 App 启动权限</span><small>补权限、重建 .app、检查日志可写</small><em>本地修复 · 不会真实交易</em></button>
            </div>
            {Array.isArray(diagnostics?.items) && diagnostics.items.length ? (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>状态</th><th>项目</th><th>详情</th></tr></thead>
                  <tbody>
                    {diagnostics.items.map((item) => (
                      <tr key={item.key || item.label}>
                        <td><span className={`badge ${item.status === "OK" ? "ok" : item.status === "ERROR" ? "danger" : "warn"}`}>{item.status}</span></td>
                        <td>{item.label}</td>
                        <td>{item.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </Section>
        </>
      ) : null}

      {view === "logs" ? (
        <>
          <Section title="最近任务记录" eyebrow="任务日志">
            <div className="table-wrap">
              <table>
                <thead><tr><th>任务</th><th>状态</th><th>开始</th><th>结束</th><th>日志位置</th></tr></thead>
                <tbody>
                  {history.slice(0, 8).map((row) => (
                    <tr key={row.task_id || `${row.task_name}-${row.started_at}`}>
                      <td>{row.description || row.task_name}<small>研究任务，不会真实交易</small></td>
                      <td><span className={`badge ${row.status === "success" ? "ok" : row.status === "warning" ? "warn" : "danger"}`}>{row.status}</span></td>
                      <td>{row.started_at || "暂无"}</td>
                      <td>{row.finished_at || "暂无"}</td>
                      <td>{row.log_path || "暂无"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!history.length ? <div className="empty-note">当前没有需要处理的任务。</div> : null}
            </div>
          </Section>
          <LogsPanel logName={logName} setLogName={setLogName} logData={logData} />
        </>
      ) : null}
    </main>
  );
}
