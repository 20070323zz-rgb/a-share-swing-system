# Report Naming Standard V1

## Purpose

本标准适用于 Phase A 之后新建或新一代生成链产生的报告。现有文件全部 grandfathered：本阶段不移动、不重命名、不删除，也不为追求命名合规而改写运行时入口。

## Required naming forms

时间敏感报告默认使用小写 `snake_case`，日期位于扩展名前的文件名末尾。

### Daily and dated reports

```text
<descriptive_name>_<YYYY-MM-DD>.<ext>
```

Examples:

- `tushare_etf_availability_status_2026-07-15.md`
- `paper_execution_audit_2026-07-15.json`
- `project_checkpoint_validation_2026-07-14.md`

### Weekly reports

周报日期使用 week-end date：

- `trading_weekly_report_2026-07-17.md`
- `project_weekly_report_2026-07-17.md`

### Monthly reports

```text
<descriptive_name>_<YYYY-MM>.<ext>
```

Example: `monthly_model_review_2026-07.md`。

### Research, audit, and validation reports

```text
<topic>_<purpose_or_stage>_<YYYY-MM-DD>.<ext>
```

Examples:

- `exposure_phase1_completion_2026-07-10.md`
- `pr2_merge_readiness_qc_2026-07-13.md`

## Mandatory rules

1. 使用 ISO `YYYY-MM-DD`；月报可使用 `YYYY-MM`。
2. 日期必须位于扩展名前的末尾。
3. 文件名使用小写 `snake_case`；不使用空格或难以排序的中文日期。
4. 禁止 `final2`、`new`、`latest2`、`最新版` 等模糊版本名。
5. 同一天多个不可覆盖正式版本优先使用稳定 `run_id` 或时间戳；必要时可用 `_v2`，但 metadata 必须写明 `supersedes`。
6. 不得把用户本机路径、临时目录名、Token 或环境标识写入文件名。
7. `business_date` 与 `generated_at` 必须分开；生成时间不能替代业务日期。

## Date archive plus stable alias

机器读取的稳定入口可以继续使用：

- `latest_*`
- `current_*`
- `dashboard_data.json`
- `paper_performance_summary.json`
- Catalog 中标记为 `runtime_locked` 的其他入口

未来双轨生成顺序：

```text
生成不可覆盖的日期版文件
        ↓
结构、业务日期和内容验证通过
        ↓
以原子方式更新稳定别名
        ↓
记录 alias -> dated artifact、内容哈希与 supersedes
```

若日期版验证失败，稳定别名不得更新。稳定别名是接口，不是历史归档；日期版是审计证据，不应被静默覆盖。

## Recommended metadata

新生成链必须遵守 `docs/report_metadata_standard.md`，至少记录：

```text
report_id
business_date / period_end_date
generated_at
producer
source_inputs
content_sha256
stable_alias (if any)
runtime_alias (if any)
supersedes (if any)
source_run_id
retention_class
schema_version
```

## Legacy treatment

Catalog 的 `naming_compliance=NON_COMPLIANT` 是未来治理信号，不是 Phase A 修复任务。任何现有文件的 rename/move 必须进入单独迁移 Batch，带依赖更新、兼容期、回滚清单和 App/Dashboard 验证。
