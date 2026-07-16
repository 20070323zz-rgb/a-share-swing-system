# Tushare Primary App Update Implementation — 2026-07-16

## 修改入口

- App 任务名与按钮保持 `backfill_etf_data`；后端命令由 BaoStock primary + JQData fallback 改为 `scripts/update_etf_data_tushare.py`。
- 正式 CLI 固定读取项目内 `configs/tushare_primary_app_update.yaml`，不再接受任意 `--config`；实现入口：`src/data_sources/tushare/app_update.py`。
- App 返回 `provider=TUSHARE`、`business_date`、`updated_count`、`result_code` 与 `ssot_manifest_hash`。

## 更新链结构

`Tushare fund_daily → 独立 staging → 183/183 universe 与字段校验 → Freshness Gate → 完整 candidate_etf_daily → 目录级事务切换 → data/etf_daily/`。

`data/etf_daily/` 继续是 App、Dashboard、模型的唯一正式 SSOT；candidate 标记为 `EPHEMERAL_NON_SSOT`，没有任何正式读取入口。BaoStock 仅保留 `RECONCILIATION_ONLY` 角色，JQData fallback 为 `DISABLED`，新链路不静默 fallback。

## Promotion 与回滚

- candidate、backup、SSOT 位于同一文件系统；本次核对设备号均为 `16777231`。
- 切换前持久化 before manifest；candidate、after、rollback manifest 写入独立 append-only manifest 目录。
- Promotion 仅使用目录 rename 事务，不逐文件覆盖正式 SSOT。切换失败自动恢复 backup，并复核 183 个文件及 before manifest hash。
- 已验证回滚后清理失败 candidate；未验证的 rollback 会保留 recovery 目录和旧备份供人工恢复，不自动删除。Availability audit staging 不在清理范围。

## 成功 / 失败测试

- 专项测试：`30 passed`。覆盖原有 17 项，以及严格布尔解析、正式配置路径锁定、异常脱敏和 App 主状态口径。
- 失败覆盖：182/183 与空响应 `DATA_NOT_READY`；认证、网络、限流、字段、Freshness、candidate 生成、目录切换、rollback 主路径失败。
- `PROMOTION_FAILED` 已验证自动回滚；`ROLLBACK_FAILED` 明确上报，并验证应急恢复后旧 SSOT manifest 不变。
- 全量：`105 passed, 2 warnings, 8 subtests passed`；Dashboard build、Frontend production build、App release 均通过。Context validation 为 `VALID_WITH_WARNINGS`，唯一 warning 是既有 dated stale-regime snapshot。

## SSOT 保护

- 基线 SSOT：183 个 CSV；当前 manifest hash `ece51649ea17bd3cc7f866f57d7c05eb504b072dfdbf80a2a91f5a96ed673d23`。
- 所有失败测试均逐文件验证 SSOT manifest 不变；BaoStock/JQData 调用计数均为 0。
- 保护文件与基线一致：`src/paper_trade_engine.py`、`data/paper_trades.csv`、`data/paper_positions.csv` 均未修改。

## 默认禁用与限制

- `formal_promotion_enabled` 只接受布尔值 `true/false` 与精确字符串 `"true"/"false"`；缺失、空值、非法字符串、大小写变体和其他类型均 fail-closed 为 `false`。
- App 与正式 CLI 均固定正式配置路径；没有 `--config` 或环境变量形式的隐式激活入口，测试仅直接调用 Python 函数注入内存配置。
- Promotion、回滚与 provider 异常对外只返回稳定错误码和通用 `reason`；Token、用户目录、worktree 绝对路径和堆栈不进入 App/API 主状态。
- App 主状态固定为 `primary_provider=TUSHARE`、`fallback_enabled=false`、BaoStock `RECONCILIATION_ONLY`、JQData fallback `DISABLED`；旧状态仅保留在 `legacy_reconciliation` 区域。
- 本次未调用真实 Production Promotion，未真实写入 `data/etf_daily/`，未启动 Reports Phase B，未修改模型、Ranking、Score 或 Exposure。
- 当前具备聚焦 QC 与隔离 Canary 条件，但在正式授权前只生成候选目录，不激活 Production Promotion。
