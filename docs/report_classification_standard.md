# Report Classification Standard V1

Batch Name: Reports Governance Phase A - Catalog, Dependency Registry & Naming Standard

Batch Type: Governance + Low-Risk Engineering + Validation

Scope: Zero Move / Zero Rename / Zero Delete

## Purpose

本标准为 `reports/**` 建立统一角色、依赖、风险与元数据语言。分类结果用于审阅和未来迁移设计，不是移动授权。Phase A 不修改 App、Dashboard、launchd、周报链或任何现有报告路径。

## Role taxonomy

| Role | Definition | Default handling |
| --- | --- | --- |
| `RUNTIME_INPUT` | 被 App、Dashboard、脚本或执行前检查作为机器输入读取 | 保持稳定路径 |
| `CURRENT_ALIAS` | `latest_*`、`current_*` 或其他稳定人机入口 | 保持稳定路径；未来由日期版验证后更新 |
| `DATED_DAILY` | 业务日期明确的日报 | Phase A 只登记 |
| `DATED_WEEKLY` | 周期截止日明确的周报 | Phase A 只登记 |
| `DATED_MONTHLY` | 月份明确的月报 | Phase A 只登记 |
| `RESEARCH_ARTIFACT` | Regime、Style、Exposure、Universe、模型等研究产物 | 按主题和依赖复核 |
| `AUDIT_ARTIFACT` | 审计、诊断、证据与完整性检查 | 保留证据链，迁移前检查引用 |
| `GOVERNANCE_ARTIFACT` | Catalog、Registry、Context、权限与阶段治理 | 保持可恢复性和状态引用 |
| `VALIDATION_ARTIFACT` | 测试、readiness、release、post-merge 验证 | 保留验证上下文 |
| `GENERATED_SNAPSHOT` | 可再生成但可能被运行时读取的快照 | 先按运行时依赖治理 |
| `ARCHIVED_ARTIFACT` | 已位于 `reports/archive/**` 的历史产物 | 不重复迁移 |
| `UNKNOWN` | 现有证据不足 | `UNKNOWN_REQUIRES_REVIEW`，不得自动归档 |

分类优先级为：已归档路径 → 明确 runtime lock → stable alias → 明确日期周期 → governance/validation/audit/research 语义 → 可识别运行时读取 → `UNKNOWN`。高风险分类优先于低风险分类。

## Independent migration, naming and retention dimensions

`NOT_DATED_ARTIFACT` is retired as a migration-safety conclusion. A missing date is a naming concern, not evidence that a report is unsafe to migrate. Every Catalog record is evaluated independently along these dimensions:

| Dimension | Controlled values |
| --- | --- |
| `dependency_safety` | `ACTIVE_PRODUCER`, `ACTIVE_CONSUMER`, `RUNTIME_LOCKED`, `NO_ACTIVE_DEPENDENCY`, `UNKNOWN_DEPENDENCY` |
| `naming_status` | `COMPLIANT_DATED`, `LEGACY_STABLE_ALIAS`, `NEEDS_DATE_NORMALIZATION`, `NOT_APPLICABLE`, `UNKNOWN` |
| `retention_status` | `PERMANENT`, `PROJECT_LIFETIME`, `ROLLING_WINDOW`, `UNTIL_MIGRATION_VALIDATED`, `TEMPORARY_AUDIT`, `MANUAL_REVIEW` |
| `migration_eligibility` | `SAFE_TO_MIGRATE`, `SAFE_TO_MIGRATE_RENAME_REQUIRED`, `MIGRATION_BLOCKED_ACTIVE_DEPENDENCY`, `MIGRATION_BLOCKED_RUNTIME`, `MIGRATION_BLOCKED_UNKNOWN`, `MIGRATION_BLOCKED_RETENTION` |
| `deletion_eligibility` | `NOT_DELETION_CANDIDATE`, `DELETION_REVIEW_REQUIRED`, `SAFE_TO_DELETE_AFTER_AUTHORIZATION`, `DELETION_BLOCKED` |

An undated legacy report with no active dependency may be `SAFE_TO_MIGRATE_RENAME_REQUIRED`. Unknown dependency or role is never promoted automatically. Phase A never emits `SAFE_TO_DELETE_AFTER_AUTHORIZATION`; deletion remains a separately authorized future decision.

## Multiple archive-block evidence

`archive_candidate` and `archive_block_reason` remain compatibility fields only and must not drive migration or deletion. The authoritative evidence fields are:

```text
archive_block_reasons: list[str]
primary_archive_block_reason: str
archive_block_evidence_ids: list[str]
archive_block_evidence: dict[str, list[str]]
```

Reasons coexist and are ordered by: `ACTIVE_STATIC_PRODUCER`, `ACTIVE_DYNAMIC_PRODUCER`, `RUNTIME_CONSUMER`, `CURRENT_ALIAS`, `STATE_OR_GOVERNANCE_LOCKED`, `ACTIVE_AUDIT_ARTIFACT`, `RETENTION_BLOCKED`, `UNKNOWN_ROLE`, `NEEDS_DATE_NORMALIZATION`, `NO_ACTIVE_DEPENDENCY`. Producer and consumer reasons point to Registry `reference_id` values; rule-derived reasons use deterministic `rule_*` evidence IDs.

The generator must publish distributions for all independent dimensions and explain why the deletion candidate count remains zero or differs. It must never use a large `NOT_DATED_ARTIFACT` bucket to conceal dependency safety.

## Dependency reference taxonomy

Registry 使用以下引用类型：

- `PRODUCER_WRITE`
- `CONSUMER_READ`
- `FILE_COPY_SOURCE`
- `FILE_MOVE_SOURCE`
- `APP_RUNTIME_READ`
- `DASHBOARD_RUNTIME_READ`
- `TEST_REFERENCE`
- `DOCUMENTATION_LINK`
- `STATIC_LINK`
- `EXAMPLE_REFERENCE`
- `HISTORICAL_REFERENCE`
- `STATE_INDEX_REFERENCE`
- `DYNAMIC_PATH_PATTERN`
- `PATH_DECLARATION`
- `UNKNOWN_REFERENCE`

Python 优先使用 AST 识别实际 IO call；Shell 只在明确重定向、tee、读命令或输出参数存在时判断方向；Frontend/App 将 fetch/axios 与 href 分开；Markdown fenced code、历史报告路径和测试 fixture 保持独立类型。静态路径保留具体文件名与源码跨度。动态 glob、f-string、变量模板只记录原模式并标记 `DYNAMIC_PATH_PATTERN`，不得展开或伪造具体依赖。

Shell `cp/mv` 必须按参数位置分类，不得因为命令中出现报告路径就统一视为写入：

- `cp` source 使用 `FILE_COPY_SOURCE / READ`，兼容 actor 为 `CONSUMER`；destination 使用 `PRODUCER_WRITE / WRITE`。
- `mv` source 使用 `FILE_MOVE_SOURCE / MOVE_SOURCE`，兼容 actor 为 `CONSUMER`；destination 使用 `PRODUCER_WRITE / WRITE`。
- `-p/-f/-a/--/-t`、多 source、目录 destination、引号、变量和 glob 必须保留 source/destination 语义。
- 无法可靠推导目录内最终文件名时，只记录动态目录模式并降低 confidence，不得伪造具体文件。
- `FILE_MOVE_SOURCE` 表示活跃 mutation source；Catalog 必须将其视为依赖，禁止进入无依赖归档候选。

`data/staging/tushare_etf_availability/` 的数据类是 `TEMPORARY_AUDIT_DATA`，只属于 Shadow evidence，不是报告运行时输入或正式数据源。其 lifecycle 与 retirement 权限以 `docs/report_path_registry_design.md` 为唯一治理契约。

每条记录必须包含稳定 `reference_id`、`source_line_start/end`、`normalized_target`、`direction`、`parser_type`、`source_excerpt_hash`、`generator_version` 和 `source_tree_commit`。`reference_id` 不依赖行号；无关前置空行只能改变当前行号，不能改变引用身份。

## Catalog metadata contract

每条 Catalog 记录必须包含：

```text
report_id, current_path, filename, extension, role, cadence, topic, status,
business_date, created_date, modified_at, producer_candidates,
consumer_candidates, reference_count, runtime_locked, current_alias,
dated_artifact, dependency_safety, naming_status, retention_status,
migration_eligibility, deletion_eligibility, archive_block_reasons,
primary_archive_block_reason, archive_block_evidence_ids,
archive_candidate, migration_risk, naming_compliance, metadata_compliance,
confidence, notes
```

规则：

1. `report_id` 是规范化相对路径的 SHA-256 派生稳定 ID，不依赖扫描顺序。
2. `business_date` 只接受文件名中的明确 ISO 日期，或结构化字段/明确标注的业务日期。
3. Git 日期或文件系统修改时间只能用于 `created_date` / `modified_at`，不得冒充业务日期。
4. 无法确认时写 `UNKNOWN`，不作推断。
5. 输出按 `current_path`、引用路径和源位置稳定排序。
6. runtime lock 与未知分类均采用保守处理，不得成为自动归档候选。
7. `archive_candidate=false` is retained during Phase A for compatibility; it is not an eligibility result.

## Confidence

- `HIGH`：角色可判定且有可定位依赖证据。
- `MEDIUM`：角色可判定但依赖证据有限，或路径通过可识别拼接解析。
- `LOW`：角色或动态依赖仍需人工复核。

## Control-plane exclusions

Catalog/Registry 自身及 Phase A summary 不进入自身 inventory，避免自引用导致每次生成新增记录。该排除只适用于控制平面产物，其他 `reports/**` 文件全部扫描，并在 JSON 中列出排除清单。

## Boundary

本标准不授权 Report Migration Phase B、Data Layout Migration 或 Scripts Migration；不修改任何策略、Freshness Gate、Availability Audit、ETF SSOT 或受保护文件。
