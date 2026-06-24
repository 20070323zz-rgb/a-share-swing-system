# 数据源 Provider 分层设计 2026-06-21 20:14:02

本设计只描述未来数据接入层，不替换当前自动化，不接入交易执行。

## 目标
- 所有行情数据先进入 staging 或本地缓存检查层。
- 统一 schema：`date, open, high, low, close, volume, amount, source, fetch_time, available_date`。
- 合并时永远本地高可信旧行优先，不允许旧源覆盖更新、更可信数据。
- 每个 provider 必须暴露 status、fetch_daily、错误原因和源状态。

## 已新增轻实现骨架
- `src/data_providers/base.py`
- `src/data_providers/local_cache_provider.py`
- `src/data_providers/baostock_provider.py`
- `src/data_providers/tushare_provider.py`
- `src/data_providers/akshare_provider.py`
- `src/data_providers/jqdata_provider.py`

## 数据源职责
| 数据源 | 建议角色 | 备注 |
| --- | --- | --- |
| local_cache | 第一读取层 | 回测/研究优先读本地正式 CSV |
| BaoStock | 日更 fallback/低频补齐 | 当前可用但延迟较高，必须估算调用量 |
| Tushare | 可配置日线候选 | 需要 token，仅环境变量，不打印 |
| JQData | 历史/staging 候选 | 当前不宜强行作为日常主源 |
| AKShare | 情报/特殊数据/低频 fallback | 不适合高频并发或主源，需看诊断结果 |

## 必须实现的工程保护
- retry：有限次数，记录错误类型。
- timeout：每个请求必须有上限。
- backoff：失败后退避，不能死循环重试。
- rate_limit：每天调用量上限，BaoStock 远低于 50000。
- circuit_breaker：连续失败时停止该源，切换 fallback 或停止。
- local_cache_first：能用本地已确认数据就不重复请求。
- no_overwrite_newer_data：不允许旧数据源覆盖本地高可信行。
- source_status_report：每次更新写机器可读 JSON 和 Markdown。

## 明确禁止
- 高频并发暴力请求。
- 没有 source / fetch_time / available_date 的新数据进入研究因子。
- 旧源覆盖新源或正式高可信数据。
- 情报数据直接进入 BUY 主因子或自动卖出执行层。
- 任何券商 API、真实下单、真实账户读取。