# Future Report Migration Plan

## Current state

- Phase A：Catalog、Dependency Registry、分类标准、命名标准与 Path Registry 设计。
- Report File Migration：`BLOCKED`。
- Phase B / Data Layout Migration / Scripts Migration：`NOT_STARTED`。

## Non-negotiable Phase A boundary

```text
Zero Move
Zero Rename
Zero Delete
Zero Runtime Path Change
```

Phase A 产生的 `LOW_RISK_ARCHIVE_CANDIDATE` 只供未来审阅，不自动执行。

## Future phases

### Phase B - Dated artifact pilot

候选范围仅限 Catalog 中满足全部条件的记录：

1. `dated_artifact=true`；
2. `reference_count=0`；
3. `runtime_locked=false`；
4. `current_alias=false`；
5. `migration_risk=LOW_RISK_ARCHIVE_CANDIDATE`；
6. Availability Audit 和其他活跃观测没有使用该文件。

每批只处理一个报告族，保留清单、目标路径、内容哈希和 rollback 映射。Phase B 仍需独立 Main 授权。

### Phase C - Registry-backed compatibility

实现并验证 Path Registry，让 producer/consumer 使用逻辑 ID。旧路径至少保留一个发布周期；App、Dashboard、周报、release check 和 context bootstrap 全部通过后才能缩小兼容面。

### Phase D - Topic and lifecycle migration

按 `daily / weekly / monthly / research / audit / governance` 小批迁移。每个批次必须从 Dependency Registry 重新扫描，禁止使用过期引用计数。

## Candidate families

- 优先候选：无依赖的 `daily_signal_<date>`、`weekly_review_<date>` 等明确日期版。
- 暂缓：`latest_*`、`current_*`、`dashboard_data.json`、绩效/组合/执行前检查等 runtime locked 文件。
- 人工复核：研究、审计、治理和 `UNKNOWN` 文件。
- 永不作为普通归档候选：受保护账本、ETF SSOT、Availability Audit staging/evidence。

## Per-batch gate

迁移前后至少验证：

- Catalog 与 Dependency Registry 重建；
- 旧/新文件内容哈希或结构语义一致；
- `git diff --check`；
- 目标测试；
- Dashboard build；
- frontend production build；
- App release check；
- context validation/bootstrap；
- 受保护文件与 `data/etf_daily/` Git-tree hash 不变。

失败时只使用新 commit 修复或 registry rollback；不 force-push、不重写历史、不删除证据。
