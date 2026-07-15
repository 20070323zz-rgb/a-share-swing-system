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

## Phase B complete consumer migration contract

Phase B remains `BLOCKED`. The following contract is a prerequisite, not an authorization to migrate.

Each report-family batch must migrate and validate the complete graph together:

1. Producer;
2. immutable dated artifact path;
3. runtime alias or Report Path Registry ID;
4. Backend API;
5. Dashboard consumer;
6. App consumer;
7. App补齐数据按钮;
8. launchd and shell automation;
9. daily/weekly report chain;
10. tests and fixtures;
11. Work/Codex context discovery;
12. deprecated old paths;
13. compatibility period;
14. rollback target and procedure.

A file-only move is invalid. The per-family `consumer-completeness` gate must enumerate every known Producer and Consumer from the current Dependency Registry, prove each replacement path, and fail when any entry is missing.

### App backfill end-to-end contract

```text
App补齐数据按钮
-> Backend API
-> generator
-> immutable dated artifact write
-> schema / business-date / hash validation
-> atomic runtime alias update
-> Dashboard and App reread
-> page displays the newest validated business date
```

Failure rules:

- `DATA_NOT_READY` must not read an arbitrary older file.
- Alias update failure preserves the previous validated alias.
- Generator failure leaves no partial artifact or half-updated alias.
- The flow must not bypass the Freshness Gate.
- The flow must not write Availability staging.
- No component may silently fallback to a deprecated path.

Build success alone is insufficient. A real fixture or end-to-end read must verify Backend API, Dashboard consumer, App consumer, alias resolution and displayed business date.

### Dashboard and automation contract

- Dashboard must not bind directly to an arbitrary dated filename after migration.
- Dashboard reads through the Report Path Registry, a stable alias, or a stable Backend API.
- launchd, shell automation, daily close and weekly review chains are Consumers and must be included in `consumer-completeness`.
- Runtime-read validation is required in addition to Dashboard/frontend builds.

### Work/Codex contract

Every migration task must first read `PROJECT_INDEX.md`, `docs/current_project_state.md`, `docs/current_phase_status.json`, `docs/operational_playbook.md`, `docs/project_batch_standard.md`, and the Report Path Registry or approved migration mapping. Work/Codex must not guess a historical path from memory, bypass the Registry, or create a second directory convention.

### Deprecated path and compatibility contract

- Each batch owns a versioned deprecated-path inventory.
- CI/tests run a `deprecated-path` scan for newly introduced hard-coded paths.
- During the compatibility period, old-path use emits a warning identifying the replacement and deadline.
- After the compatibility period, old-path resolution fails fast.
- No old path is removed until every consumer is migrated and the `consumer-completeness` gate passes.

### Completion state

Only when the file, Producer, every Consumer, App button, Dashboard, automation, Work/Codex and rollback are all switched and validated may the family become `MIGRATION_COMPLETE`.

If any item remains, the only valid state is `MIGRATION_PARTIAL`. Formal Execution inputs migrate last or remain `RUNTIME_LOCKED`.
