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

## Migration risk taxonomy

| Risk | Rule |
| --- | --- |
| `RUNTIME_LOCKED` | 明确锁定路径，或被 App/Dashboard runtime 读取 |
| `HIGH_DEPENDENCY` | 十处及以上可定位引用，需先做兼容层 |
| `ACTIVE_REFERENCED` | 当前别名且存在活跃引用 |
| `MEDIUM_DEPENDENCY` | 存在静态引用，但未达到 runtime/high 门槛 |
| `LOW_RISK_ARCHIVE_CANDIDATE` | 明确日期产物、无引用、非 runtime、非 alias |
| `UNKNOWN_REQUIRES_REVIEW` | 无足够证据支持安全迁移 |

`LOW_RISK_ARCHIVE_CANDIDATE` 只表示可进入未来人工验证清单，不表示 Phase A 已批准移动。

## Dependency reference taxonomy

Registry 使用以下引用类型：

- `PRODUCER_WRITE`
- `CONSUMER_READ`
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

每条记录必须包含稳定 `reference_id`、`source_line_start/end`、`normalized_target`、`direction`、`parser_type`、`source_excerpt_hash`、`generator_version` 和 `source_tree_commit`。`reference_id` 不依赖行号；无关前置空行只能改变当前行号，不能改变引用身份。

## Catalog metadata contract

每条 Catalog 记录必须包含：

```text
report_id, current_path, filename, extension, role, cadence, topic, status,
business_date, created_date, modified_at, producer_candidates,
consumer_candidates, reference_count, runtime_locked, current_alias,
dated_artifact, archive_candidate, migration_risk, naming_compliance,
metadata_compliance, confidence, notes
```

规则：

1. `report_id` 是规范化相对路径的 SHA-256 派生稳定 ID，不依赖扫描顺序。
2. `business_date` 只接受文件名中的明确 ISO 日期，或结构化字段/明确标注的业务日期。
3. Git 日期或文件系统修改时间只能用于 `created_date` / `modified_at`，不得冒充业务日期。
4. 无法确认时写 `UNKNOWN`，不作推断。
5. 输出按 `current_path`、引用路径和源位置稳定排序。
6. runtime lock 与未知分类均采用保守处理，不得成为自动归档候选。

## Confidence

- `HIGH`：角色可判定且有可定位依赖证据。
- `MEDIUM`：角色可判定但依赖证据有限，或路径通过可识别拼接解析。
- `LOW`：角色或动态依赖仍需人工复核。

## Control-plane exclusions

Catalog/Registry 自身及 Phase A summary 不进入自身 inventory，避免自引用导致每次生成新增记录。该排除只适用于控制平面产物，其他 `reports/**` 文件全部扫描，并在 JSON 中列出排除清单。

## Boundary

本标准不授权 Report Migration Phase B、Data Layout Migration 或 Scripts Migration；不修改任何策略、Freshness Gate、Availability Audit、ETF SSOT 或受保护文件。
