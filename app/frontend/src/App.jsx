import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  BookOpenCheck,
  BriefcaseBusiness,
  Database,
  FlaskConical,
  HomeIcon,
  Menu,
  RefreshCw,
  ShieldCheck,
  TerminalSquare,
  X
} from "lucide-react";
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
import Logs from "./pages/Logs.jsx";
import Portfolio from "./pages/Portfolio.jsx";
import Research from "./pages/Research.jsx";
import SettingsSafety from "./pages/SettingsSafety.jsx";
import Signals from "./pages/Signals.jsx";
import { appVersion } from "./designTokens.js";

const tabs = [
  { key: "home", label: "总览", hint: "今日研究工作台", icon: HomeIcon },
  { key: "portfolio", label: "模拟仓", hint: "资产与持仓复盘", icon: BriefcaseBusiness },
  { key: "signals", label: "信号观察", hint: "排名与影子预览", icon: BarChart3 },
  { key: "research", label: "研究图谱", hint: "模型、风险与证据", icon: FlaskConical },
  { key: "data", label: "数据中心", hint: "覆盖、来源与质量", icon: Database },
  { key: "tasks", label: "任务中心", hint: "自动化与运行记录", icon: TerminalSquare },
  { key: "safety", label: "设置与安全", hint: "边界与本地环境", icon: ShieldCheck }
];

const confirmTasks = new Set(["backfill_etf_data", "backfill_recent_data", "update_daily_data", "refresh_all_reports", "run_daily_close_dryrun"]);

export default function App() {
  const initialTab = typeof window === "undefined" ? "home" : window.location.hash.replace("#", "");
  const [tab, setTab] = useState(tabs.some((item) => item.key === initialTab) ? initialTab : "home");
  const [navOpen, setNavOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
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

  const navigate = useCallback((nextTab) => {
    setTab(nextTab);
    setNavOpen(false);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `#${nextTab}`);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([refreshCore(), refreshLog()]);
    } finally {
      setRefreshing(false);
    }
  }, [refreshCore, refreshLog]);

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
    onNavigate: navigate,
    refreshAppEnv
  }), [status, dataHealth, portfolio, signals, research, taskStatus, tasks, safety, appEnv, logName, logData, handleRun, refreshAppEnv, navigate]);

  const currentItem = tabs.find((item) => item.key === tab) || tabs[0];
  const CurrentIcon = currentItem.icon;
  const currentLabel = currentItem.label;
  const pageDescription = {
    home: "把资产、信号、数据、研究与任务状态收进一张清晰的工作台。",
    portfolio: "复盘模拟交易账户、持仓结构与风险观察，不读取真实账户。",
    signals: "查看原始排名、影子预览与后续跟踪，所有结果均不进入执行层。",
    research: "沿研究图谱查看模型、Regime、风险画像与证据成熟度。",
    data: "集中查看 ETF 日线覆盖、数据来源、质量与更新状态。",
    tasks: "运行白名单本地任务，查看自动化状态、任务历史与诊断日志。",
    safety: "管理本地启动环境与永久安全边界。"
  }[tab];

  const statusText = status?.system_status === "ERROR" ? "需要处理" : status?.system_status === "CAUTION" ? "观察中" : "运行正常";
  const marketLabel = {
    market_neutral: "中性快照",
    market_offensive: "进攻快照",
    market_defensive: "防御快照"
  }[String(status?.market_state || "").toLowerCase()] || "市场快照待更新";

  return (
    <div className={`app-shell ${navOpen ? "nav-is-open" : ""}`}>
      <button className="nav-backdrop" aria-hidden={!navOpen} aria-label="关闭导航" onClick={() => setNavOpen(false)} tabIndex={navOpen ? 0 : -1} type="button" />
      <aside className={`side-nav ${navOpen ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-mark"><Activity size={18} aria-hidden="true" /></span>
          <div>
            <strong>弦图 Quant Lab</strong>
            <small>A 股 ETF 研究工作台</small>
          </div>
        </div>
        <div className="nav-label">研究空间</div>
        <nav aria-label="主导航">
          {tabs.map(({ key, label, hint, icon: Icon }) => (
            <button
              aria-current={tab === key ? "page" : undefined}
              className={tab === key ? "active" : ""}
              key={key}
              onClick={() => navigate(key)}
              type="button"
            >
              <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
              <span><strong>{label}</strong><small>{hint}</small></span>
            </button>
          ))}
        </nav>
        <div className="safety-rail">
          <div className="safety-rail-head"><ShieldCheck size={16} aria-hidden="true" /><strong>本地安全边界</strong></div>
          <p>仅模拟盘研究，不连接券商，不提供真实交易入口。</p>
          <div className="safety-rail-tags"><span>执行锁定</span><span>L2 本地</span></div>
        </div>
      </aside>
      <div className="main-shell">
        <div className="global-status-bar">
          <div className="status-live"><i className={String(status?.system_status || "normal").toLowerCase()} />{statusText}</div>
          <span>{marketLabel}</span>
          <span>数据截至 {status?.latest_data_date || "待更新"}</span>
          <button type="button" onClick={() => navigate("safety")}>{appVersion}</button>
        </div>
        <header className="topbar">
          <button className="mobile-nav-toggle" aria-expanded={navOpen} aria-label={navOpen ? "关闭导航" : "打开导航"} onClick={() => setNavOpen((value) => !value)} type="button">
            {navOpen ? <X size={19} aria-hidden="true" /> : <Menu size={19} aria-hidden="true" />}
          </button>
          <div className="topbar-copy">
            <div className="topbar-icon"><CurrentIcon size={19} aria-hidden="true" /></div>
            <div>
              <div className="eyebrow">A 股 ETF · 本地模拟研究</div>
              <h1>{currentLabel}</h1>
              <p>{pageDescription || "只读展示与白名单本地任务，所有真实交易入口关闭。"}</p>
            </div>
          </div>
          <div className="top-actions">
            {taskStatus?.running ? <span className="pill running">任务运行中</span> : null}
            <button className="ghost-button refresh-button" disabled={refreshing} onClick={refreshAll} type="button">
              <RefreshCw className={refreshing ? "spinning" : ""} size={16} aria-hidden="true" />
              {refreshing ? "刷新中" : "刷新数据"}
            </button>
          </div>
        </header>
        {warning ? <div className="top-warning"><Activity size={16} aria-hidden="true" /><span>{warning}</span></div> : null}
        {tab === "home" ? <Home {...pageProps} /> : null}
        {tab === "portfolio" ? <Portfolio {...pageProps} /> : null}
        {tab === "signals" ? <Signals {...pageProps} /> : null}
        {tab === "research" ? <Research {...pageProps} /> : null}
        {tab === "data" ? <DataCenter {...pageProps} /> : null}
        {tab === "tasks" ? <Logs {...pageProps} /> : null}
        {tab === "safety" ? <SettingsSafety {...pageProps} /> : null}
        <footer><BookOpenCheck size={14} aria-hidden="true" /> 本地模拟盘学习系统 · 不接券商 API · 不真实下单 · 不读取真实账户</footer>
      </div>
    </div>
  );
}
