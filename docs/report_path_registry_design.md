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
