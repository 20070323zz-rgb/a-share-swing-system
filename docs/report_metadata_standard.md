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
snapshot_revision: <v1|v2|...>
supersedes: <prior revision path or null>
immutable: true
```

CSV 必须由同业务日期的 JSON 或 `<artifact>.metadata.json` 伴随；JSON 顶层必须包含：

```text
generated_at
business_date
generator_version
source_tree_commit
record_count
schema_version
snapshot_revision
supersedes
immutable
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

## Immutable dated snapshot contract

Dated governance artifacts are append-only snapshots. A revision marker, when needed, is placed before the date: `<name>_v2_YYYY-MM-DD.<ext>`. The writer follows exactly these rules:

1. If the target does not exist, create it atomically.
2. If it exists with byte-identical content, treat the rebuild as an idempotent success.
3. If it exists with different bytes, fail fast; no `force` overwrite option exists.
4. Changed content requires a new revision whose metadata names the prior snapshot in `supersedes`.
5. Previously published snapshots, including 2026-07-14 and the v1 2026-07-15 set, are never regenerated in place.

Control-plane scan exclusions are determined by recognized artifact family and metadata, not by a hard-coded file count. Every revision records `snapshot_revision`, `supersedes`, `source_tree_commit`, `generated_at`, and `immutable=true`.

## Retention classes

- `PERMANENT`
- `PROJECT_LIFETIME`
- `ROLLING_WINDOW`
- `UNTIL_MIGRATION_VALIDATED`
- `TEMPORARY_AUDIT`
- `MANUAL_REVIEW`

Phase A Catalog、Dependency Registry、Naming Audit、Summary 与 Remediation 均为 `PERMANENT`，且不可覆盖。

Availability 临时调查数据必须额外登记：

```yaml
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

这些字段用于阻止误提升和误删除，不代表运行时 Path Registry 已接入。日期版长期统计、决策、迁移、retirement readiness/validation 报告及必要 hash/manifest 摘要使用 `PERMANENT`。

## Alias contract

稳定 alias 只是一项运行时接口，不是历史证据。更新必须执行：临时文件写入 -> schema/business-date/hash 验证 -> `os.replace` 原子切换。失败时保留旧 alias，不得把任意旧日期文件静默当作最新数据。
