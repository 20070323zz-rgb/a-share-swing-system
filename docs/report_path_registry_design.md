# Future Report Path Registry Design

## Status and boundary

`COMPLETE_PENDING_QC / RUNTIME_NOT_STARTED`。本设计不创建 `configs/report_paths.yaml`，不接入 reader/writer，不迁移文件，也不授权 Phase B。

## Complete entry contract

```yaml
registry_schema_version: 1
report_id: paper_performance_summary
report_type: PAPER_PERFORMANCE
cadence: DAILY
dated_path_template: reports/paper_performance_summary_{business_date}.json
current_dated_path: reports/paper_performance_summary_2026-07-14.json
runtime_alias: reports/paper_performance_summary.json
producer_id: paper_performance
producer_entrypoint: src/paper_performance.py
consumers: [dashboard, app_backend]
schema_reference: schemas/paper_performance_v1.json
retention_class: PROJECT_LIFETIME
retention_days: null
retention_rule: keep_all_validated_business_dates
archive_policy: MANUAL_AFTER_COMPATIBILITY_GATE
deletion_policy: NEVER_AUTOMATIC
immutable_history: true
atomic_update_required: true
fallback_policy: DATA_NOT_READY
compatibility_paths: [reports/paper_performance_summary.json]
migration_status: NOT_STARTED
rollback_target: reports/paper_performance_summary.json
owner: reports_governance
last_validated_at: null
```

## Retention policy

允许值：

- `PERMANENT`
- `PROJECT_LIFETIME`
- `ROLLING_WINDOW`
- `UNTIL_MIGRATION_VALIDATED`
- `TEMPORARY_AUDIT`
- `MANUAL_REVIEW`

`ROLLING_WINDOW` 必须提供 `retention_days`；其他类别必须提供可审计 `retention_rule`。删除始终需要独立授权，Registry 不得自动删除不可覆盖历史。

## Availability temporary audit data contract

当前临时调查目录的治理登记如下；这是设计契约，不创建运行时 Registry，也不改变 PR #3 数据：

```yaml
path: data/staging/tushare_etf_availability/
data_class: TEMPORARY_AUDIT_DATA
retention_class: UNTIL_MIGRATION_VALIDATED
secondary_tag: TEMPORARY_AUDIT
runtime_role: SHADOW_EVIDENCE_ONLY
canonical: false
writable_by_formal_pipeline: false
deletable_during_active_audit: false
promotion_allowed: false
retirement_status: RETIREMENT_PENDING_AUTHORIZATION
```

`data/etf_daily/` 始终是唯一 Canonical SSOT。临时目录不得被 Formal pipeline 写入、读取或提升；`ACTIVE_COLLECTING` 期间禁止删除。本契约不授权当前清理，也不创建自动定时清理任务。

### Lifecycle

状态只能按以下顺序推进，并由长期日期版证据支持：

```text
ACTIVE_COLLECTING
-> AUDIT_COMPLETE
-> MAIN_DECISION_RECORDED
-> PRIMARY_SOURCE_MIGRATION_COMPLETE
-> POST_MIGRATION_VALIDATION_PASS
-> FINAL_AUDIT_ARCHIVE_COMPLETE
-> RETIREMENT_AUTHORIZED
-> TEMPORARY_DATA_DELETED
-> DELETION_AUDIT_PASS
```

跳过、倒序或缺少证据的迁移均 fail closed。任一删除前置条件不满足时：`RETIREMENT = BLOCKED`。

### Mandatory retirement prerequisites

以下 14 项必须全部满足：

1. `RETIREMENT-PRE-01`：ETF Daily Availability Timing Audit 已完成并记录 `AUDIT_COMPLETE`。
2. `RETIREMENT-PRE-02`：Main 已记录数据源迁移决策。
3. `RETIREMENT-PRE-03`：Tushare Primary Upstream Migration 已完成。
4. `RETIREMENT-PRE-04`：Post-Migration Validation = `PASS`。
5. `RETIREMENT-PRE-05`：正式 `data/etf_daily/` 仍是唯一 Canonical SSOT。
6. `RETIREMENT-PRE-06`：关键统计已保存到长期日期版报告。
7. `RETIREMENT-PRE-07`：FIRST_AVAILABLE、FIRST_COMPLETE、FIRST_STABLE 已归档。
8. `RETIREMENT-PRE-08`：Tushare 与 BaoStock 对照结论已归档。
9. `RETIREMENT-PRE-09`：P50、P90、worst case 与安全执行时点已归档。
10. `RETIREMENT-PRE-10`：必要 manifest hash 与数据质量证据已归档。
11. `RETIREMENT-PRE-11`：代码、测试、报告和正式链对临时目录的读取依赖为 0。
12. `RETIREMENT-PRE-12`：Path Registry 或 Dependency Registry 确认临时目录 consumer 为 0。
13. `RETIREMENT-PRE-13`：回滚所需配置、代码版本和决策记录完整。
14. `RETIREMENT-PRE-14`：用户/Main 明确授权 Retirement。

不得因为时间过去、磁盘占用、Audit 表面完成或 PR 已合并而自动删除。

### Authorization and responsibilities

- Main：判断迁移完成并验收、批准 Availability Audit Data Retirement、确定长期证据范围。
- Work：只读执行 retirement readiness audit，生成待删除清单，核对依赖、hash 与归档完整性；只有获得授权后才执行删除与 post-delete validation。
- Codex：不得在 Audit/Migration 完成时自行删除，不得配置自动删除；只可实现默认 `dry-run` 的受控清理工具。
- 用户：对最终删除拥有授权权。

受控状态：

- 未授权：`RETIREMENT_PENDING_AUTHORIZATION`
- 授权且全部检查通过：`RETIREMENT_APPROVED`
- 删除完成：`TEMPORARY_AUDIT_DATA_RETIRED`
- 删除后验证失败：`RETIREMENT_VALIDATION_FAILED`

### Retirement evidence

删除前必须生成 `availability_audit_data_retirement_readiness_<YYYY-MM-DD>.md`，至少记录目录、文件数、总大小、日期范围、audit IDs、manifest 数、聚合 hash、当前 consumer、长期归档文件、未满足条件、Main 授权记录和建议删除/保留清单。

删除后必须生成 `availability_audit_data_retirement_validation_<YYYY-MM-DD>.md`，至少记录实际删除数、删除前聚合 hash、删除后目录状态、正式 SSOT hash、正式下载链验证、测试、残余引用、rollback 材料和最终判定。

长期保留：方法文档、日期版统计、决策/迁移报告、readiness/validation 报告及必要 hash/manifest 摘要。经授权可删除：真实 probe 临时快照、中间 normalized、comparator 临时结果、debug 输出、重复 attempt 和本地调度临时日志。

### Post-retirement rollback

1. 删除前必须完成所有必要汇总；供应商原始 payload 删除后不保证可恢复。
2. 正式系统回滚不得依赖临时调查数据库。
3. 数据源迁移回滚目标是 BaoStock fallback/reconciliation 配置或既有正式 Canonical SSOT，而不是恢复 Audit staging。
4. 删除后发现报告缺失时，不得伪造历史 probe；标记 `EVIDENCE_NOT_RECONSTRUCTABLE`，必要时启动新的观察期。
5. 不为假设性回滚长期保留临时数据库。

## Resolution and missing-date behavior

- `resolve_current(report_id)` 只返回已验证 runtime alias。
- `resolve_dated(report_id, business_date, run_id=None)` 只返回精确业务日期产物。
- `resolve_compatibility(report_id)` 只在声明的兼容期返回旧路径。
- 未知 ID、缺失 business date、文件不存在、schema 不匹配或重复 writer 必须 fail closed。
- 指定日期产物不存在时返回 `DATA_NOT_READY`；禁止回退到任意旧文件、最新 mtime 或模糊 `latest`。
- Registry 文件不可用时，Formal/runtime consumer 必须停止；不得静默绕过 Registry。

## Atomic alias update

1. producer 写入同目录临时文件；
2. 验证 schema、business date、record count 与 content hash；
3. 验证 dated artifact 已不可覆盖落盘；
4. 使用 `os.replace` 原子更新 alias；
5. 更新失败时保留旧 alias 并返回失败，不修改 Registry 状态。

## Cycle prevention

- Registry 本身由固定 bootstrap 路径读取，不得通过 Registry 定位自己的唯一输入。
- Registry generator、dated artifact 与 runtime alias 建立有向图；提交前执行 DFS/topological cycle detection。
- 禁止 `registry -> alias -> generator input -> registry`、alias 自指、producer 双写和 consumer 反向生产边。
- 检测到 cycle 时 Registry 版本无效，所有迁移 fail closed。

## Migration order

1. 无运行时 consumer 的 low-risk dated artifacts；
2. governance/audit artifacts；
3. daily/weekly generators；
4. Dashboard noncritical inputs；
5. App runtime inputs；
6. Formal execution inputs 最后迁移，或继续永久锁定。

每一级必须完成一个发布周期的兼容验证后才能进入下一级。Availability Audit 收集期的 PR #3 路径保持冻结。

## Rollback

- 兼容路径至少保留一个完整发布周期；Formal/runtime 输入按风险延长。
- alias 可原子回退到已验证 dated artifact。
- Registry 采用版本化快照，可回退到上一有效版本。
- 原路径在兼容期内保持可恢复，不进行破坏性删除。
- Dashboard build、frontend build、App release、周报链、context validation 任一失败时，回退 Registry/alias 并 fail closed。

## Single-point-of-failure controls

Registry 是显式控制平面，不是静默 fallback。运行时发布必须同时保留上一有效 Registry 版本、内容哈希与本地只读 rollback copy；当前版本缺失或损坏时返回控制错误，由人工选择回退版本。系统不得自行猜测路径。
