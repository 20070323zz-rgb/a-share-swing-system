# 数据源状态报告 2026-07-04 00:00:48

本报告只记录行情数据源状态，不包含任何账号密码/token，不接券商 API，不真实下单。

- primary_source: baostock
- fallback_source: jqdata
- actual_source_used: baostock
- jqdata_status: SKIPPED
- baostock_status: UPDATED
- fallback_triggered: False
- latest_data_date: 2026-07-03
- new_rows: 366
- pending_symbols: none
- failed_symbols: none
- unresolved_symbols: none

## 安全边界

- 不打印 JQData 密码/token
- 不保存账号密码到代码或报告
- staging-first
- 本地原行优先
