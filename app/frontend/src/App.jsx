import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAppEnv,
  getDataHealth,
  getLog,
  getPortfolio,
  getResearch,
  getSafety,
  getSignals,
  getStatus,
  getTaskStatus,
  getTasks,
  runTask
} from "./api.js";
import DataCenter from "./pages/DataCenter.jsx";
import Home from "./pages/Home.jsx";
import Portfolio from "./pages/Portfolio.jsx";
import Research from "./pages/Research.jsx";
import SettingsSafety from "./pages/SettingsSafety.jsx";
import { appVersion } from "./designTokens.js";

const tabs = [
  ["home", "首页"],
  ["portfolio", "模拟仓"],
  ["research", "模型观察"],
  ["data", "数据中心"],
  ["safety", "设置与安全"]
];

const confirmTasks = new Set(["backfill_etf_data", "backfill_recent_data", "update_daily_data", "refresh_all_reports", "run_daily_close_dryrun"]);

export default function App() {
  const [tab, setTab] = useState("home");
  const [status, setStatus] = useState({});
  const [dataHealth, setDataHealth] = useState({});
  const [portfolio, setPortfolio] = useState({});
  const [signals, setSignals] = useState({});
  const [research, setResearch] = useState({});
  const [taskStatus, setTaskStatus] = useState({});
  const [tasks, setTasks] = useState({});
  const [safety, setSafety] = useState({});
  const [appEnv, setAppEnv] = useState({});
  const [logName, setLogName] = useState("latest_app_task.log");
  const [logData, setLogData] = useState({});
  const [warning, setWarning] = useState("");

  const refreshCore = useCallback(async () => {
    try {
      const [nextStatus, nextHealth, nextPortfolio, nextSignals, nextResearch, nextTask, nextTasks, nextSafety] = await Promise.all([
        getStatus(),
        getDataHealth(),
        getPortfolio(),
        getSignals(),
        getResearch(),
        getTaskStatus(),
        getTasks(),
        getSafety()
      ]);
      setStatus(nextStatus);
      setDataHealth(nextHealth);
      setPortfolio(nextPortfolio);
      setSignals(nextSignals);
      setResearch(nextResearch);
      setTaskStatus(nextTask);
      setTasks(nextTasks);
      setSafety(nextSafety);
      setWarning("");
    } catch (error) {
      setWarning(`后端接口暂时不可用：${error.message}`);
    }
  }, []);

  const refreshAppEnv = useCallback(async () => {
    try {
      setAppEnv(await getAppEnv());
    } catch (error) {
      setAppEnv({ status: "ERROR", output: `环境检查失败：${error.message}` });
    }
  }, []);

  const refreshLog = useCallback(async () => {
    try {
      setLogData(await getLog(logName));
    } catch (error) {
      setLogData({ tail: `日志读取失败：${error.message}` });
    }
  }, [logName]);

  useEffect(() => {
    refreshCore();
    refreshAppEnv();
    const timer = setInterval(refreshCore, taskStatus?.running ? 3000 : 20000);
    return () => clearInterval(timer);
  }, [refreshCore, refreshAppEnv, taskStatus?.running]);

  useEffect(() => {
    refreshLog();
    const timer = setInterval(refreshLog, taskStatus?.running ? 3000 : 20000);
    return () => clearInterval(timer);
  }, [refreshLog, taskStatus?.running]);

  const handleRun = useCallback(async (taskName) => {
    const task = (tasks?.tasks || []).find((row) => row.task_name === taskName);
    if (confirmTasks.has(taskName)) {
      const ok = window.confirm(`确认运行：${task?.description || taskName}\n\n${task?.safe_note || "只允许白名单本地任务，不真实下单。"}`);
      if (!ok) return;
    }
    try {
      const result = await runTask(taskName);
      if (!result.accepted) {
        setWarning(result.error || "任务未被接受");
      } else {
        setWarning(`任务已启动：${task?.description || taskName}。可在“任务与日志”查看实时状态。`);
        setLogName("latest_app_task.log");
      }
      await refreshCore();
      await refreshLog();
    } catch (error) {
      setWarning(`任务启动失败：${error.message}`);
    }
  }, [tasks, refreshCore, refreshLog]);

  const pageProps = useMemo(() => ({
    status,
    dataHealth,
    portfolio,
    signals,
    research,
    taskStatus,
    tasks,
    safety,
    appEnv,
    logName,
    setLogName,
    logData,
    onRun: handleRun,
    onNavigate: setTab,
    refreshAppEnv
  }), [status, dataHealth, portfolio, signals, research, taskStatus, tasks, safety, appEnv, logName, logData, handleRun, refreshAppEnv]);

  const currentLabel = tabs.find(([key]) => key === tab)?.[1] || "首页";
  const pageDescription = {
    home: "今天最重要的系统状态、模拟仓、数据和安全边界。",
    portfolio: "这里展示模拟交易账户表现，不是真实账户。",
    research: "这里用于观察 shadow 模型表现和证据成熟度，不影响正式模拟仓。",
    data: "这里查看本地 ETF 日线数据、数据源和健康状态。",
    safety: "这里管理白名单本地任务、启动环境和永久安全边界。"
  }[tab];

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">
          <span className="brand-mark">ETF</span>
          <div>
            <strong>A 股 ETF 控制室</strong>
            <small>本地研究应用 · {appVersion}</small>
          </div>
        </div>
        <nav>
          {tabs.map(([key, label]) => (
            <button className={tab === key ? "active" : ""} key={key} onClick={() => setTab(key)}>{label}</button>
          ))}
        </nav>
        <div className="safety-rail">
          <span>仅模拟盘</span>
          <span>券商接口未连接</span>
          <span>真实交易禁用</span>
        </div>
      </aside>
      <div className="main-shell">
        <div className="global-status-bar">
          <span>本地研究系统</span>
          <button type="button" onClick={() => setTab("safety")}>{appVersion}</button>
          <span>执行禁用</span>
          <span>未接券商</span>
          <span>仅模拟盘</span>
        </div>
        <header className="topbar">
          <div>
            <div className="eyebrow">本地模拟盘研究控制台</div>
            <h1>{currentLabel}</h1>
            <p>{pageDescription || "只读展示与白名单本地任务，所有真实交易入口关闭。"}</p>
          </div>
          <div className="top-actions">
            <span className={`pill ${String(status?.system_status || "NORMAL").toLowerCase()}`}>{status?.system_status === "ERROR" ? "异常" : status?.system_status === "CAUTION" ? "观察" : "正常"}</span>
            <span className="pill">数据日 {status?.latest_data_date || "暂无"}</span>
            <span className="pill">{appVersion}</span>
            <button className="ghost-button" onClick={refreshCore}>刷新</button>
          </div>
        </header>
        {warning ? <div className="top-warning">{warning}</div> : null}
        {tab === "home" ? <Home {...pageProps} /> : null}
        {tab === "portfolio" ? <Portfolio {...pageProps} /> : null}
        {tab === "research" ? <Research {...pageProps} /> : null}
        {tab === "data" ? <DataCenter {...pageProps} /> : null}
        {tab === "safety" ? <SettingsSafety {...pageProps} /> : null}
        <footer>本地模拟盘学习系统：不接券商 API，不真实下单，不读取真实账户，不暴露账号密码。</footer>
      </div>
    </div>
  );
}
