# Report Metadata Standard V1

## Status

`PROPOSED_ACTIVE_ON_MERGE`。本标准约束 Reports Governance Phase A 之后的新治理产物和后续明确接入的生成链，不要求批量改写历史报告。

## Required fields

所有日期版 Markdown 使用 YAML front matter：

```yaml
report_id: report_<stable_hash>
report_type: <controlled_type>
business_date: YYYY-MM-DD
created_at: YYYY-MM-DDTHH:MM:SS+08:00
status: <controlled_status>
phase: <phase_id>
producer: <entrypoint>
source_run_id: <stable_run_id>
retention_class: <retention_class>
schema_version: <integer>
```

CSV 必须由同业务日期的 JSON 或 `<artifact>.metadata.json` 伴随；JSON 顶层必须包含：

```text
generated_at
business_date
generator_version
source_tree_commit
record_count
schema_version
```

如存在稳定机器入口，还必须记录：

```text
runtime_alias
current_dated_path
content_sha256
supersedes
atomic_update_required
```

## Date semantics

- `business_date` 是文件代表的业务/审计日期，不来自 mtime。
- `created_at` 必须带 Asia/Shanghai 的 `+08:00` offset。
- 文件名日期必须等于 `business_date`。
- `source_tree_commit` 标识生成器实际扫描的最后一个非控制产物提交；控制产物提交本身不进入扫描输入，避免自引用提交哈希循环。
- `report_id` 由规范化目标路径稳定派生，不依赖行号、mtime 或扫描顺序。

## Retention classes

- `PERMANENT`
- `PROJECT_LIFETIME`
- `ROLLING_WINDOW`
- `UNTIL_MIGRATION_VALIDATED`
- `TEMPORARY_AUDIT`
- `MANUAL_REVIEW`

Phase A Catalog、Dependency Registry、Naming Audit、Summary 与 Remediation 均为 `PERMANENT`，且不可覆盖。

## Alias contract

稳定 alias 只是一项运行时接口，不是历史证据。更新必须执行：临时文件写入 -> schema/business-date/hash 验证 -> `os.replace` 原子切换。失败时保留旧 alias，不得把任意旧日期文件静默当作最新数据。
