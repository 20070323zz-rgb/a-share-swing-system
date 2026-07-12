# Checkpoint Commit Scope Notes

## 42f6fd2 — `Update app UI, data reports, and project hygiene`

该提交是此前多个本地阶段尚未推送成果的 checkpoint，不是单一 UI feature commit。其标题概括了主要工作，但没有完整表达实际范围。

实际包含：

- App UI、组件库与前端构建产物；
- Dashboard/readers 和绩效、估值、风险展示支持；
- ETF 与 paper portfolio 运行快照；
- dated/latest reports、低风险报告归档和项目 hygiene 产物；
- research/preview 辅助代码与研究报告；
- 项目文件地图、索引和周报入口调整。

形成原因：这些变更源自 Draft PR 建立前积累的本地 checkpoint 工作。当时远端 `main` 尚未包含该本地提交；Draft PR #1 因此把它作为历史基线的首个 commit 纳入。

## 后续 commit 边界

后续 checkpoint commits 已按职责拆分：

- `09c8085`：Paper Execution Freshness Gate 与非破坏性审计；
- `bdbba3e`：Regime、Style Fit、Universe V2、Exposure、Tushare 审计及上下文基础设施；
- `fc3097b`：绩效链、App 与 Dashboard UI 同步修复；
- `e6dc6a5`：ETF、manual import、paper portfolio 数据快照；
- `a92547b`：2026-07-10 生成报告 checkpoint；
- `d651057`：权威项目状态收口。

## 审阅与合并原则

- 不通过 rebase、squash、drop 或 force-push 改写 `42f6fd2`。
- 对发现的具体问题使用后续修复 commit，保留审计链。
- Draft PR #1 应被视为一次跨阶段 baseline checkpoint，而不是普通小型 feature PR。
- 本说明只解释历史范围，不授权 Tushare Staging/PIT、Formal Execution 变更或主分支合并。
