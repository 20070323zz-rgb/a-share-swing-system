# Future Report Path Registry Design

## Status

`DESIGNED_NOT_IMPLEMENTED`。Phase A 只建立 Catalog 与 Dependency Registry，不创建运行时 Path Registry，不修改任何 reader/writer。

## Design goal

未来 Path Registry 以逻辑报告 ID 解耦机器入口、日期归档路径和兼容旧路径。它必须支持审阅、逐批迁移和回滚，不能成为隐藏的自动移动器。

建议未来独立 Batch 创建 `configs/report_paths.yaml`，每个 entry 包含：

```yaml
paper_performance_summary:
  schema_version: 1
  role: RUNTIME_INPUT
  current_path: reports/paper_performance_summary.json
  stable_alias: reports/paper_performance_summary.json
  archive_template: reports/daily/portfolio/paper_performance_summary_{business_date}.json
  producer_ids: [paper_performance]
  consumer_ids: [dashboard, app_backend]
  compatibility_paths: []
  validation_profile: paper_performance_v1
  migration_status: NOT_STARTED
```

## Resolution contract

未来 resolver 应只提供：

- `resolve_current(report_id)`：稳定机器入口；
- `resolve_dated(report_id, business_date, run_id=None)`：不可覆盖日期版；
- `resolve_compatibility(report_id)`：迁移窗口内的旧入口；
- `validate_registration(report_id)`：路径、schema、producer/consumer 和冲突检查。

未知 ID、缺失日期、路径越界、重复 writer 或未注册 runtime reader 必须 fail closed。Registry 不得自动把 research artifact 接入 Formal Execution。

## Adoption sequence

1. 以当前 Dependency Registry 建立候选 entry，人工确认 producer/consumer。
2. 先让单一低风险生成器写日期版，但继续保留原稳定 alias。
3. 让 reader 从 registry 解析，保留至少一个发布周期的旧路径兼容。
4. 对 App、Dashboard、周报和 release check 分别验证。
5. 只有引用计数归零且 rollback evidence 完整后，才可在独立迁移 Batch 讨论旧路径处置。

## Validation and rollback

每个 entry 必须有：

- 旧路径与新路径内容哈希/语义一致性；
- producer 单写者约束；
- consumer coverage；
- stable alias 原子更新；
- 缺失文件 fail-closed 行为；
- 一键回到旧 `current_path` 的 registry-only rollback；
- Dashboard build、frontend build、App release check 与 context validation。

## Concurrent audit boundary

PR #3 的 `tushare_etf_availability_*` 观测文件、配置、脚本和报告在 audit 收集期间全部冻结为独立边界。未来 Registry 设计不得把其 staging snapshot 变成正式报告输入，也不得改写或迁移其 append-only evidence。
