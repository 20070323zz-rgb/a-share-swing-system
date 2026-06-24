# 数据源状态报告 2026-06-24 15:44:47

本报告只记录行情数据源状态，不包含任何账号密码/token，不接券商 API，不真实下单。

- primary_source: baostock
- fallback_source: jqdata
- actual_source_used: baostock
- jqdata_status: SKIPPED
- baostock_status: STALE_NO_NEW_ROWS
- fallback_triggered: False
- latest_data_date: 2026-06-23
- new_rows: 0
- pending_symbols: none
- failed_symbols: none
- unresolved_symbols: none

## 安全边界

- 不打印 JQData 密码/token
- 不保存账号密码到代码或报告
- staging-first
- 本地原行优先
