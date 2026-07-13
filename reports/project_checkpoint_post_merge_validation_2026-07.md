# July 2026 Project Checkpoint Post-Merge Validation

验证时间：2026-07-13 09:51:50 CST

## 结论

- Project Checkpoint Cleanup：`COMPLETE`
- PR #1：`MERGED`
- Post-Merge Validation：`PASS`
- Main Branch：`STABLE`
- Tushare 5000 Data Foundation Audit：`COMPLETE`
- Tushare Minimal Staging Proof & PIT Contract：`NEXT_CANDIDATE`，本 Batch 未启动
- Data Foundation Upgrade：`NOT_STARTED`
- Reports Governance Phase A：`NOT_STARTED`
- Formal Execution Logic：`UNCHANGED`

## 合并记录

| 项目 | 结果 |
| --- | --- |
| PR | #1 |
| Base | `main` |
| Head | `agent/project-checkpoint-july-2026` |
| PR head SHA | `746916cd47cf4bdd99286b985a78268c7c35aa8d` |
| 合并方式 | GitHub merge commit（非 squash、非 rebase） |
| Merge commit | `40a6017402456d62609169325cb5f1d31a1a140b` |
| 合并时间 | 2026-07-13 09:49:26 CST |
| PR 状态 | `MERGED` |

合并前 GitHub 状态为 `MERGEABLE / CLEAN`，PR 不是 Draft，未配置或未报告 CI checks。远端 PR head 与本地审计 head 一致，没有合并前新增未审查 commit。

## 合并前最终检查

- `git diff --check origin/main...HEAD`：`CLEAN`，0 warning。
- PR 变更文件中的 `/Users/dayin`：0 个文件命中。
- PR 新增行明显 secret/key 模式：0 命中；未读取或输出 `.env`。
- `src/paper_trade_engine.py` 与 merge base 的 SHA-256 一致。
- `data/paper_trades.csv` 与 `data/paper_positions.csv` 的 PR 变化属于既有、已审计的 paper simulation checkpoint；本 Batch 未重写两份账本。
- `data/manual_import`：52 valid，0 failed。
- 正式 ETF 日线文件：183 个，SSOT 仍为 `data/etf_daily/`。
- `data/staging/jqdata*` 与历史 `data/staging/tushare/` 是已有 staging 输入层，不是正式 ETF SSOT；本 Batch 未创建、运行或扩展 staging。

## Post-Merge 测试与构建

| 验证项 | 结果 |
| --- | --- |
| 全量 pytest | `23 passed, 2 warnings, 8 subtests passed` |
| Freshness Gate / guarded wrapper / equity curve 定向测试 | `18 passed, 8 subtests passed` |
| manual_import 下载器回归测试 | `3 passed` |
| manual_import 全量数据校验 | `52 valid, 0 failed` |
| Dashboard build | `PASS` |
| Frontend production build | `PASS`，1835 modules transformed |
| App release check | `PASS`（Result: OK） |
| Context validation | `VALID_WITH_WARNINGS` |
| Context bootstrap | `VALID_WITH_WARNINGS` |

两条 PytestCollectionWarning 来自带 `__init__` 的工具脚本数据类，不是测试失败。Context 唯一 warning 为 Regime snapshot stale：`latest_known_regime_date=2026-07-06`，必须继续带日期描述，不能称为当前实时 Regime。

## 主分支落地内容

主分支已包含并验证以下 checkpoint 产物：

- Paper Execution Freshness Gate；
- guarded paper execution wrapper；
- 2026-07-10 stale trade 非破坏性审计；
- manual_import 按日期合并保护及回归测试；
- Tushare 5000 capability/gap audit；
- performance、Dashboard 与 App UI 修复；
- 项目权威状态与 checkpoint 治理报告。

## 受保护文件

工作区文件哈希与 `HEAD` blob 哈希一致：

```text
src/paper_trade_engine.py  93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926
data/paper_trades.csv       db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5
data/paper_positions.csv    a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906
```

结论：`src/paper_trade_engine.py` 未修改；Formal Execution Logic 未改变；两份 paper ledger 未被本 Batch 重写。

## ETF 数据库与路径治理

- `data/etf_daily/`：183 个 CSV，继续作为唯一正式 ETF 日线 SSOT。
- 没有创建第二套正式行情库。
- 合并增量私人绝对路径命中：0。
- 全仓 `HEAD` 仍有 39 个合并前已存在的 `/Users/dayin` 引用；合并前远端基线为 54 个。剩余引用集中在旧 launcher、launchd、运维脚本和旧报告，本 PR 没有新增。为避免破坏本机调度且不扩大本 Batch，未做无边界重写。

## 历史 warning 处理口径

早期历史 CSV/生成物行尾 warning 已在 PR 后续治理 commit 中以语义保持方式修复，并修正生成器；最终全 PR `git diff --check` 为 0 warning。因此本次不需要保留 `ACCEPTED_HISTORICAL_ARTIFACT_WARNING`，也没有批量重写既有业务语义。

## 本地工作区说明

Batch 开始时存在 7 个已跟踪但未提交的运行快照/生成报告修改：

```text
dashboard/index.html
data/automation_state.json
reports/catchup_scheduler_status.md
reports/dashboard_data.json
reports/launchd_catchup_upgrade_report.md
reports/open_check.json
reports/open_check.md
```

它们不在 PR、不含唯一正式成果、不涉及源码或受保护账本。同步和验证期间已隔离保全，Batch 结束前恢复；不会纳入 post-merge governance commit。

## 下一阶段边界

项目已具备由 Main 另行授权 `Tushare Minimal Staging Proof & PIT Contract` 的条件，但本 Batch 只将其标记为 `NEXT_CANDIDATE`。以下工作均未启动：Tushare Minimal Staging/PIT、Data Foundation Upgrade、Reports Governance Phase A、Exposure Phase 2、Universe V3、Exit Logic。

最终判定：`POST_MERGE_VALIDATION_PASS`。
