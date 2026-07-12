# Reports 目录分类可行性调研

生成日期：2026-07-11
调研性质：只读目录与依赖调查；本报告不移动、不重命名、不删除任何现有报告。
建议状态：`FEASIBLE_AFTER_PATH_REGISTRY`

## 1. 调研目标

本报告回答四个问题：

1. `reports/` 是否适合按日报、周报、月报等周期分类。
2. 哪些报告可以低风险归档，哪些必须继续保留固定路径。
3. 如果后续实施分类，推荐采用什么目录和迁移顺序。
4. 现有自动报告链是否还需要增加每周五 ChatGPT Work 综合报告。

本轮没有执行实际分类，也没有修改任何自动化、launchd、报告生成器或 App 读取路径。

## 2. 当前目录规模

截至 2026-07-11，`reports/` 根目录统计如下：

| 类型 | 数量 |
| --- | ---: |
| 根目录文件总数 | 569 |
| Markdown | 325 |
| CSV | 93 |
| JSON | 150 |
| 其他（`.gitkeep`） | 1 |
| `reports/archive/` 已归档文件 | 45 |
| 根目录日期版 `daily_signal_YYYY-MM-DD.md` | 8 |
| 根目录日期版 `weekly_review_YYYY-MM-DD.md` | 2 |
| 根目录文件名含完整 2026 日期 | 14 |

目录体量已经超过“平铺文件夹”适合人工浏览的范围，分类具有明确价值。但根目录同时承担运行时数据总线职责，不能直接按文件名批量移动。

## 3. 当前报告的实际角色

当前 `reports/` 不是单纯的文档归档目录，而是四类职责混合：

| 角色 | 典型文件 | 特点 |
| --- | --- | --- |
| App / Dashboard 运行时输入 | `dashboard_data.json`、`paper_performance_summary.json`、`portfolio_exposure.json` | 固定路径、高耦合、不可直接移动 |
| 最新状态别名 | `latest_brief.md`、`latest_daily.md`、`latest_weekly.md`、`latest_data_health.md` | 面向人和程序的稳定入口 |
| 日期版周期报告 | `daily_signal_YYYY-MM-DD.md`、`weekly_review_YYYY-MM-DD.md` | 最适合归档与按周期分类 |
| 一次性研究、审计与阶段决策 | `style_*`、`regime_*`、`exposure_*`、`project_context_*` | 数量最多，周期属性弱，依赖差异大 |

现有依赖审计记录了 547 处 `reports/` 路径引用；`dashboard/build_dashboard.py`、App readers、周报打包器和发布检查脚本均直接读取固定文件名。因此“按日报/周报直接移动全部文件”不可行。

## 4. 推荐分类模型

建议采用“生命周期/周期为主，主题为辅”的两层模型，而不是只按日报、周报分类。

```text
reports/
  current/                 # 最新稳定入口与机器可读快照
  daily/
    signals/               # 每日信号、排名、风险摘要
    data/                  # 数据更新、覆盖、健康
    portfolio/             # 模拟仓、绩效、交易复盘
    execution/             # 执行前检查与非破坏性审计
  weekly/
    review/                # weekly_review、weekly_full_review
    portfolio/             # 模拟交易周报
    research/              # 持有期、退出规则、参数扫描、shadow 周报
    ai-packets/            # ChatGPT/Main 输入包与综合报告
  monthly/                 # 月度模型与因子复盘
  research/
    regime/
    style-fit/
    exposure/
    universe/
    model/
  audit/
    data/
    execution/
    app-release/
    project-structure/
  governance/              # phase decision、permission、context 状态
  archive/                 # 已封存日期版和历史阶段产物
```

这只是目标结构，不是本轮执行结果。

## 5. 按周期的建议归属

### 5.1 日报类

建议纳入日报体系的生成链包括：

- 每日信号：`daily_signal_YYYY-MM-DD.md`、`latest_daily.md`、`latest_brief.md`
- 排名与信号：`buy_signal_ranking.md`、`latest_ranking.md`、`sell_signal_review.md`、`latest_short_swing.md`
- 数据状态：`data_update_status.json`、`latest_data_coverage.md`、`latest_data_health.md`
- 模拟仓：`latest_paper_portfolio.md`、`paper_performance_summary.*`、`paper_equity_curve.md`、`paper_trade_pnl.*`
- 交易复盘：`trade_review_summary.*`、`trade_review_details.*`、`trade_review_open_positions.*`
- 轻量研究：`daily_rolling_backtest.*`、`market_state.*`、`portfolio_exposure.*`
- 执行安全：`paper_execution_preflight.*`

其中带 `latest_` 或被 App 固定读取的文件，第一阶段应继续保留原路径。

### 5.2 周报类

建议纳入周报体系的生成链包括：

- `weekly_review_YYYY-MM-DD.md` 与 `latest_weekly.md`
- `weekly_full_review.md` 与 `weekly_full_backtest_results.csv`
- `holding_period_research_*`
- `exit_rule_research_*`
- `parameter_sweep.*`
- `shadow_observation_weekly.*`
- `chatgpt_weekly_analysis_packet_latest.*` 及其日期归档
- `project_weekly_report_YYYY-MM-DD.md`
- `trading_weekly_report_YYYY-MM-DD.md`

现有 `reports/archive/weekly/` 和 `reports/archive/chatgpt_packets/` 已证明日期版周报归档路线可行。

### 5.3 月报类

建议纳入月报体系的文件包括：

- `monthly_model_review.md`
- 当月 `factor_analysis_report.md`
- 当月 `model_research_report.md`
- ETF 池质量与参数稳定性摘要

当前月报数量较少，可以在日报/周报完成路径注册后再处理。

### 5.4 非周期报告

以下报告不适合强行放入日报或周报：

- Regime / Style Fit / Exposure / Universe 阶段研究
- Project Context 持久化与恢复审计
- App 发布、UI 迁移和目录结构审计
- 数据源迁移、连接诊断和批次状态文件
- 阶段决策、权限矩阵与治理文件

这些应按研究主题或审计类型分类，并保留阶段状态与来源引用。

## 6. 移动风险分级

| 风险级别 | 文件类型 | 处理建议 |
| --- | --- | --- |
| 极高 | `dashboard_data.json`、`latest_*`、App 固定读取 JSON/MD | 暂不移动；先建立路径注册表和兼容读取 |
| 高 | 周报输入包、绩效、组合暴露、风险状态 | 需同步修改 dashboard、App、脚本和检查项 |
| 中 | 活跃研究报告、审计输出 | 先扫描代码引用，再迁移并保留兼容别名 |
| 低 | 已完成日期版日报/周报、无引用历史报告 | 可在验证后归档 |

不建议用一次性 shell 批量移动，因为这会同时破坏 App、Dashboard、周报打包器和发布检查。

## 7. 推荐实施顺序

### Phase A：零移动索引

1. 定义报告元数据字段：`report_id`、`cadence`、`topic`、`status`、`as_of_date`、`producer`、`current_alias`、`dependencies`。
2. 生成只读 catalog 和人类可读索引。
3. 标记 `runtime_locked`、`current_alias`、`archive_candidate`。

### Phase B：日期版归档

1. 只处理无程序依赖的 `daily_signal_YYYY-MM-DD.md` 和 `weekly_review_YYYY-MM-DD.md`。
2. 保留 latest/current 文件在根目录。
3. 每批执行 dashboard build、App build 和 release check。

### Phase C：路径注册表

1. 建立统一 report path registry。
2. 让 Dashboard、App、周报打包器和脚本从注册表取路径。
3. 为旧路径保留一个发布周期的兼容读取。

### Phase D：主题目录迁移

按 daily、weekly、monthly、research、audit、governance 分批迁移，每批单独验证和回滚。

## 8. ChatGPT Work 周五自动报告评估

### 8.1 当前链路已经具备的能力

系统目前每周会自动生成：

- 周度完整复盘与回测；
- 持有期、退出规则和参数扫描研究；
- Shadow 周度观察；
- 交易复盘；
- `chatgpt_weekly_analysis_packet_latest.md/json`。

现有 ChatGPT/Main 文件本质上是确定性“输入包”，不会自动完成跨报告推理、异常优先级判断和面向用户的简洁总结。`scripts/run_codex_weekly_research.sh` 也只生成提示文件，没有调用模型或创建 ChatGPT 定时任务。

### 8.2 必要性结论

建议增加，但定位为第二层只读综合分析，不替代本地 launchd 报告链。

建议状态：`RECOMMENDED_AFTER_FRESHNESS_GATE`。

主要价值：

1. 把数十份日报、周报、绩效和研究状态压缩成一个可读结论。
2. 自动检查数据、信号、排名、绩效曲线是否同日。
3. 对 `NEEDS_REVIEW`、stale snapshot、执行阻断和研究边界做优先级排序。
4. 将“事实摘要”和“下周需 Main 决定的问题”分开。

不应让 ChatGPT Work：

- 修改策略、排名、评分、仓位或交易账本；
- 自动放宽 freshness gate；
- 在数据日期不一致时给出方向性交易结论；
- 重复生成已有的底层计算报告。

### 8.3 推荐运行时间和前置门槛

不建议沿用当前周五 15:40 立即分析。2026-07-10 已出现收盘数据与后续报告生成顺序不一致，说明这一时间点过早。

推荐时间：周五 20:30（或周六 09:00）。

运行前必须满足：

1. `latest_data_date == 当周最后交易日`；
2. failed/pending 均为 0；
3. signal date 与 ranking date 等于行情日期；
4. performance valuation date 等于 equity curve end date；
5. ChatGPT weekly packet 的生成时间晚于当周最终 dashboard/performance 刷新。

任一条件失败时，自动报告只应输出 `DATA_NOT_READY / NEEDS_REVIEW` 和缺失项，不输出下周方向判断。

### 8.4 推荐交付方式

优先使用 ChatGPT 桌面端的本地项目 Scheduled task：

- 每周独立运行；
- 只读当前本地项目；
- 结果直接进入 Scheduled 收件箱；
- 不写主分支、不创建 worktree、不提交 Git；
- 先人工测试提示词，并观察前 3 次运行后再固定模板。

由于 Web Scheduled task 不能直接读取本机文件夹，若需要读取本仓库，应使用桌面端本地项目任务，并保持电脑开机、ChatGPT App 运行且项目路径可用。

## 9. 最终建议

1. `reports/` 分类具有高价值，但必须先做路径注册与索引，不能直接移动。
2. 第一批仅考虑日期版日报、周报的低风险归档。
3. `latest_*`、`dashboard_data.json` 及 App 固定读取文件继续保留原路径。
4. 推荐建立周五 20:30 的 ChatGPT Work 只读综合报告，但必须放在最终数据与周报包完成之后。
5. ChatGPT Work 只负责解释、异常排序和决策问题清单；本地 launchd 继续负责确定性数据与报告生成。

## 10. 本轮边界确认

- 未移动 reports 文件。
- 未创建任何 reports 子目录。
- 未修改 launchd 定时任务。
- 未创建 ChatGPT Scheduled task。
- 未修改策略、信号、排名、评分或正式执行逻辑。
- 未修改 `src/paper_trade_engine.py`、`data/paper_trades.csv`、`data/paper_positions.csv`。
