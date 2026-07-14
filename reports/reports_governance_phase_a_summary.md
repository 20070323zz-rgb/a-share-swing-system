# Reports Governance Phase A Summary

完成时间：2026-07-14 17:03:41 CST  
Base：`origin/main@8d145b4`  
Branch：`agent/reports-governance-phase-a`  
Result：`COMPLETE_PENDING_DRAFT_PR_REVIEW`

## Objective completed

Phase A 已建立五项基础能力：

1. Report Catalog；
2. Report Dependency Registry；
3. Report Classification Standard；
4. Report Naming Standard；
5. Future Path Registry Design 与 Migration Plan。

本 Batch 是控制平面建设，不是迁移 Batch。

## Inventory results

| Metric | Result |
| --- | ---: |
| Catalog records | 645 |
| Runtime locked | 228 |
| Current aliases | 36 |
| Dated artifacts | 12 |
| Low-risk archive candidates | 10 |
| Unknown roles requiring review | 104 |
| Dependency records | 5,999 |
| Distinct referenced paths/patterns | 719 |
| Dynamic path patterns | 23 |
| Critical runtime references | 412 |

Catalog inventory 覆盖 Phase A 开始时的全部 645 个 `reports/**` 文件。Catalog、Dependency Registry 和本 summary 是 control-plane exclusions，避免自引用导致重复运行漂移；排除清单写入 Catalog JSON。

Catalog SHA-256：`6eda1128386c4074320e168bce1286722d077eed4f138d4227bea67a4483e783`。  
Dependency Registry SHA-256：`a815a079f5ef50ce04cdc38ced445556976d0e6a0b0fcad7b7506ef0f5cadf53`。

## Classification and safety behavior

- `report_id` 由规范化相对路径稳定派生，与扫描顺序无关。
- `business_date` 只从明确文件名、结构化字段或明确标注的业务日期解析；Git/文件系统时间不作为业务日期。
- 静态字符串、`Path` `/` 拼接、`os.path.join`、`joinpath`、shell report-dir 变量和前端/文档路径均可定位。
- glob、f-string 与其他动态模板保留为 `DYNAMIC_PATH_PATTERN`，不展开为虚构文件。
- App/Dashboard runtime reader 采用保守锁定；真实 runtime input 不会成为 archive candidate。
- `LOW_RISK_ARCHIVE_CANDIDATE` 只表示未来人工复核候选，不授权移动。

## Dual-track standard

新时间敏感报告默认使用末尾 ISO 日期：

```text
<descriptive_name>_<YYYY-MM-DD>.<ext>
```

月报可用 `<YYYY-MM>`。未来正式生成链采用：日期版生成 → 验证 → 原子更新稳定 alias → 记录 alias/内容哈希/supersedes。现有 `latest_*`、`current_*` 与 runtime locked 文件保持原路径。

## Validation

| Check | Result |
| --- | --- |
| Governance targeted tests | `6 passed` |
| Full pytest | `59 passed`, `8 subtests passed`, 2 existing collection warnings |
| Generator repeated-run byte stability | PASS |
| Python compilation | PASS |
| Dashboard build | PASS |
| Frontend production build | PASS, 1,835 modules transformed |
| App release check | PASS |
| Context validation/bootstrap | `VALID_WITH_WARNINGS` |
| `git diff --check` | PASS |

Context 唯一 warning 是既有 2026-07-06 Regime snapshot stale；没有新的 context error 或 blocking conflict。

## Protected boundaries

Protected file hashes 与 `origin/main` 一致：

```text
src/paper_trade_engine.py  93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926
data/paper_trades.csv       db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5
data/paper_positions.csv    a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906
```

ETF SSOT：183 个 CSV；canonical manifest SHA-256 为 `21702d2d2760c9c10ac62708c45fcaff35fb53aabfec13c8e474458b319d8855`，与 `origin/main` 一致。

## Zero-change attestation

- Existing reports moved：0
- Existing reports renamed：0
- Existing reports deleted：0
- App/Dashboard/launchd/weekly reader paths changed：0
- `data/etf_daily/` changed：0
- Freshness Gate changed：0
- Formal Execution changed：0
- Protected files changed：0
- Report Migration Phase B started：no
- Data Layout Migration started：no
- Scripts Migration started：no

## PR #3 isolation

Draft PR #3 branch `agent/tushare-etf-availability-audit` remains independent and `ACTIVE_COLLECTING`. Phase A did not modify its observer code, config, launchd template, staging or timing reports. The only common files are the three required authority surfaces (`PROJECT_INDEX.md`, `docs/current_project_state.md`, `docs/current_phase_status.json`); Phase A changes there are restricted to reports-governance status. Merge order may require a small fix-forward context reconciliation, but no Availability Audit evidence is duplicated or overwritten.

## State transition

```text
Reports Governance Phase A = COMPLETE
Report Catalog = ACTIVE_V1
Report Dependency Registry = ACTIVE_V1
Report Classification Standard = ACTIVE_V1
Report Naming Standard = ACTIVE_V1
Future Report Path Registry = DESIGNED_NOT_IMPLEMENTED
Report File Migration = BLOCKED
Report Migration Phase B = NOT_STARTED
Formal Execution Logic = UNCHANGED
```

完成后停止；未启动下一迁移阶段。
