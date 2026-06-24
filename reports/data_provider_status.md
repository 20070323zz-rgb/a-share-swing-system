# Data provider 状态 2026-06-21 21:00:03

本报告只做 provider 诊断，不切换正式日更主源，不写入 data/etf_daily。

## 优先级
- daily_source_priority: baostock, tushare_if_configured, akshare_fallback
- history_source_priority: jqdata, baostock, tushare_if_configured
- special_data_priority: akshare, tushare, manual
- daily_source_priority_candidate: tushare_if_configured, baostock, akshare_fallback
- recommended_daily_source: baostock
- candidate_daily_source: tushare
- formal_source_switched: False

## Provider 明细
| provider | configured | usable | message |
| --- | --- | --- | --- |
| local_cache | True | True | local cache dir: /Users/dayin/Code/a-share-swing-system/data/etf_daily |
| baostock | False | False | baostock import failed |
| tushare | True | True | tushare package missing; HTTP API fallback will be used |
| akshare | True | True | akshare import ok; run akshare_connectivity_check for endpoint health |
| jqdata | False | False | jqdatasdk import ok; credential values are never printed |

## 安全边界
- 不打印 token
- 不接券商 API
- 不真实下单
- 不修改执行层