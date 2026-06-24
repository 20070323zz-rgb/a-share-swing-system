# 自动化数据更新修复报告 2026-06-15 19:20

本报告记录本轮 ETF 日线自动更新链路修复。范围仅限本地行情数据更新、报告和只读看板同步；不接券商 API，不真实下单，不读取真实账户，不保存密码或 token。

## 本轮发现

- `data/etf_daily/` 扩池后共有 183 个 ETF CSV。
- 修复前最新数据停在 `2026-06-12`，但看板仍可能因为 `daily_close` 主流程完成而显示自动化完成。
- 原 `daily_close` 使用 BaoStock 隔离子进程、单标的 8 秒超时。扩池后该阈值过短，容易导致大量请求超时或 Broken pipe。
- `scripts/update_etf_data.py` 原来没有机器可读的更新健康状态，也没有在“新增行数为 0 / 失败过多 / 数据仍过期”时向自动化返回 warning/error。

## 已修复

- `scripts/update_etf_data.py`
  - 新增 `--strict-exit`。
  - 新增 `--status-json`，默认写入 `reports/data_update_status.json`。
  - 新增更新健康判断：`OK / CAUTION / ERROR`。
  - 新增 `reports/data_update_diagnosis_report.md`。
  - 明确记录 `latest_local_date`、`requested_end`、`added_rows`、`status_counts`、`failed_ratio`、`pending_ratio`。
- `scripts/run_daily_close.sh`
  - 日更命令改为项目 `.venv` 下 BaoStock 单会话查询。
  - 超时从 8 秒提高到 25 秒。
  - 启用 1 次重试、每 30 个 ETF 主动重登、严格状态退出。
  - 数据更新失败时不再被误标为完全成功，后续报告仍可用本地缓存继续生成。
- `dashboard/build_dashboard.py`
  - 读取 `reports/data_update_status.json`。
  - 第一屏显示“日线更新 OK/CAUTION/ERROR”。
  - 自动化时间轴新增“ETF 日线更新”节点。
  - `daily_close` 会在数据更新异常时显示 CAUTION。
  - 系统健康面板显示最新数据日、新增行数、请求次数和诊断原因。

## 本轮真实补齐结果

- 更新区间：`2026-06-13` 到 `2026-06-15`。
- 当前正式 ETF 数据文件数：183。
- 当前 183 个 ETF 全部最新到：`2026-06-15`。
- 第二轮正式更新结果：
  - `success_appended`: 143
  - `up_to_date`: 40
  - `failed`: 0
  - `added_rows`: 143
  - BaoStock query calls: 143
- 前置验证阶段已先补齐 40 只或确认已最新；最终全池 183 只均已覆盖到 `2026-06-15`。

## 关于 BaoStock / Tushare / JQData

- BaoStock 在本机 `.venv` 可用，但扩池后单次全池日更耗时明显上升，且可能出现连接重置、Broken pipe 或超时。
- BaoStock 仍可作为免费日常源，但必须配合健康状态、严格退出和看板告警，不能再把“流程跑完”当作“数据已更新”。
- Tushare 可以作为后续备用日更源候选，前提是 token 只从环境变量读取，数据先进入 staging，再 validate/dry-run/import。
- JQData 可继续用于授权范围内的历史补齐或候选扩池；若试用权限区间有限，不应强行用于无权限的日常日期。

## 安全边界

- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未保存密码或 token。
- 未修改交易规则或仓位规则。
- 数据合并仍保持本地原行优先。
- 看板仍为只读静态 HTML。
