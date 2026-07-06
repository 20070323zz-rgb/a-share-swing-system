import { useState } from "react";
import LogsPanel from "../components/LogsPanel.jsx";
import Section from "../components/Section.jsx";
import TaskPanel from "../components/TaskPanel.jsx";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function booleanLabel(value, okWhen = false) {
  const ok = Boolean(value) === okWhen;
  return { ok, label: Boolean(value) ? "开启" : "关闭" };
}

function SettingRow({ label, value, note, okWhen = false }) {
  const state = booleanLabel(value, okWhen);
  return (
    <div className="setting-row">
      <div>
        <strong>{label}</strong>
        <small>{note}</small>
      </div>
      <Badge variant={state.ok ? "success" : "warning"}>{state.label}</Badge>
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
  return (
    <main className="page-grid settings-page">
      <section className="page-compact-head">
        <div>
          <div className="eyebrow">设置与安全</div>
          <h2>L2 本地研究边界</h2>
          <p>启动环境、白名单任务和安全边界集中在这里。所有任务都是本地研究任务，不会真实交易。</p>
        </div>
        <Badge variant="success">不连接券商 · 不真实交易</Badge>
      </section>

      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="safety">系统安全</TabsTrigger>
          <TabsTrigger value="launch">App 启动</TabsTrigger>
          <TabsTrigger value="tasks">常用任务</TabsTrigger>
          <TabsTrigger value="diagnostics">高级任务</TabsTrigger>
          <TabsTrigger value="logs">日志与诊断</TabsTrigger>
        </TabsList>

        <TabsContent value="safety">
          <Section title="系统安全" eyebrow="永久边界">
            <div className="settings-list">
              <div className="setting-row">
                <div><strong>权限等级</strong><small>本地工程和数据权限</small></div>
                <Badge variant="blue">L2</Badge>
              </div>
              <SettingRow label="真实交易" value={safety?.real_trade_enabled} note="必须关闭" />
              <SettingRow label="券商接口" value={safety?.broker_api_enabled} note="必须未连接" />
              <SettingRow label="真实账户读取" value={safety?.real_account_read_enabled} note="必须关闭" />
              <SettingRow label="Shadow 执行" value={safety?.shadow_model_execution_enabled} note="必须关闭" />
              <SettingRow label="真实下单按钮" value={safety?.real_order_buttons_enabled} note="必须不存在" />
              <SettingRow label="网页任意命令" value={safety?.arbitrary_command_enabled} note="必须关闭" />
              <div className="setting-row">
                <div><strong>执行层</strong><small>正式模型未被 shadow 替代</small></div>
                <Badge variant="success">锁定</Badge>
              </div>
            </div>
            <div className="rule-list compact-rules">
              <span>禁止登录券商账户</span><span>禁止真实买入</span><span>禁止真实卖出</span><span>禁止读取真实账户</span><span>禁止同步真实持仓</span><span>禁止 shadow 接执行层</span>
            </div>
          </Section>
        </TabsContent>

        <TabsContent value="launch">
          <Section title="App 启动" eyebrow="本地应用">
            <div className="settings-list">
              <div className="setting-row"><div><strong>App 路径</strong><small>{appShortcut?.app_bundle || "dist/量化研究控制台.app"}</small></div><Badge variant={appShortcut?.status === "active" ? "success" : "warning"}>{appShortcut?.status === "active" ? "已支持" : "待修复"}</Badge></div>
              <div className="setting-row"><div><strong>本地地址</strong><small>http://127.0.0.1:8000</small></div><Badge variant="blue">本机访问</Badge></div>
              <div className="setting-row"><div><strong>日志路径</strong><small>logs/app_server.log</small></div><Badge variant="neutral">本地文件</Badge></div>
              <div className="setting-row"><div><strong>环境检查</strong><small>不会显示 token / 密码</small></div><Badge variant={String(appEnv?.status || "").toLowerCase() === "ok" ? "success" : "warning"}>{appEnv?.status || "等待检查"}</Badge></div>
              <div className="setting-row"><div><strong>最近启动</strong><small>{launchStatus?.started_at || "暂无启动诊断记录"}</small></div><Badge variant={launchStatus?.status === "running" || launchStatus?.status === "already_running" ? "success" : launchStatus?.status === "error" ? "warning" : "neutral"}>{launchStatus?.status || "暂无记录"}</Badge></div>
            </div>
            <div className="inline-alert">历史权益回填数据由交易流水和 ETF 历史收盘价估算生成；它是派生数据，不是真实每日账户快照。</div>
            <Button variant="secondary" onClick={refreshAppEnv} type="button">重新检查环境</Button>
            <Collapsible className="settings-collapsible">
              <CollapsibleTrigger asChild><Button variant="ghost" size="sm" type="button">查看环境检查输出</Button></CollapsibleTrigger>
              <CollapsibleContent>
                <ScrollArea className="settings-log-box"><pre>{appEnv?.output || "暂无环境检查输出"}</pre></ScrollArea>
              </CollapsibleContent>
            </Collapsible>
          </Section>
        </TabsContent>

        <TabsContent value="tasks">
          <TaskPanel taskStatus={taskStatus} onRun={onRun} allowedTasks={allowedTaskNames} compact />
        </TabsContent>

        <TabsContent value="diagnostics">
          <Section title="高级任务" eyebrow="诊断与修复">
            <Collapsible className="settings-collapsible" defaultOpen>
              <CollapsibleTrigger asChild><Button variant="secondary" size="sm" type="button">启动诊断</Button></CollapsibleTrigger>
              <CollapsibleContent>
                <div className="settings-list">
                  <div className="setting-row"><div><strong>诊断状态</strong><small>{diagnostics?.checked_at || "请先运行一键诊断"}</small></div><Badge variant={diagnostics?.overall_status === "OK" ? "success" : diagnostics?.overall_status ? "warning" : "neutral"}>{diagnostics?.overall_status || "暂无诊断"}</Badge></div>
                  <div className="setting-row"><div><strong>最近启动</strong><small>{launchStatus?.error_summary || launchStatus?.started_at || "暂无启动诊断记录"}</small></div><Badge variant="neutral">{launchStatus?.status || "暂无记录"}</Badge></div>
                  <div className="setting-row"><div><strong>8000 端口</strong><small>被占用时不会强杀进程</small></div><Badge variant={diagnostics?.port_status === "free" || diagnostics?.port_status === "project_app" ? "success" : diagnostics?.port_status ? "warning" : "neutral"}>{diagnostics?.port_status || "未知"}</Badge></div>
                  <div className="setting-row"><div><strong>macOS 拦截</strong><small>如打不开，请右键 App 选择“打开”</small></div><Badge variant={diagnostics?.gatekeeper_status === "clear" ? "success" : diagnostics?.gatekeeper_status ? "warning" : "neutral"}>{diagnostics?.gatekeeper_status || "未检查"}</Badge></div>
                </div>
                <div className="inline-alert">{diagnostics?.recommendation || "暂无启动诊断记录。可以运行“诊断 App 启动问题”。"}</div>
                <div className="task-action-list compact">
                  <div className="task-action-row"><div><strong>诊断 App 启动问题</strong><p>检查 .app、权限、端口、依赖和日志</p></div><Button size="sm" onClick={() => onRun?.("diagnose_app_launch")} type="button">运行</Button></div>
                  <div className="task-action-row"><div><strong>修复 App 启动权限</strong><p>补权限、重建 .app、检查日志可写</p></div><Button size="sm" variant="secondary" onClick={() => onRun?.("fix_app_launch_permissions")} type="button">运行</Button></div>
                </div>
                {Array.isArray(diagnostics?.items) && diagnostics.items.length ? (
                  <Table>
                    <TableHeader><TableRow><TableHead>状态</TableHead><TableHead>项目</TableHead><TableHead>详情</TableHead></TableRow></TableHeader>
                    <TableBody>
                      {diagnostics.items.map((item) => (
                        <TableRow key={item.key || item.label}>
                          <TableCell><Badge variant={item.status === "OK" ? "success" : item.status === "ERROR" ? "danger" : "warning"}>{item.status}</Badge></TableCell>
                          <TableCell>{item.label}</TableCell>
                          <TableCell>{item.detail}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : null}
              </CollapsibleContent>
            </Collapsible>
          </Section>
        </TabsContent>

        <TabsContent value="logs">
          <Section title="最近任务记录" eyebrow="任务日志">
            <Table>
              <TableHeader><TableRow><TableHead>任务</TableHead><TableHead>状态</TableHead><TableHead>开始</TableHead><TableHead>结束</TableHead><TableHead>日志位置</TableHead></TableRow></TableHeader>
              <TableBody>
                {history.slice(0, 8).map((row) => (
                  <TableRow key={row.task_id || `${row.task_name}-${row.started_at}`}>
                    <TableCell>{row.description || row.task_name}<small>研究任务，不会真实交易</small></TableCell>
                    <TableCell><Badge variant={row.status === "success" ? "success" : row.status === "warning" ? "warning" : "danger"}>{row.status}</Badge></TableCell>
                    <TableCell>{row.started_at || "暂无"}</TableCell>
                    <TableCell>{row.finished_at || "暂无"}</TableCell>
                    <TableCell>{row.log_path || "暂无"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {!history.length ? <div className="empty-note">当前没有需要处理的任务。</div> : null}
          </Section>
          <Collapsible className="settings-collapsible" defaultOpen>
            <CollapsibleTrigger asChild><Button variant="secondary" size="sm" type="button">查看运行日志</Button></CollapsibleTrigger>
            <CollapsibleContent><LogsPanel logName={logName} setLogName={setLogName} logData={logData} /></CollapsibleContent>
          </Collapsible>
        </TabsContent>
      </Tabs>
    </main>
  );
}
