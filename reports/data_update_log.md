# 数据更新日志 2026-06-03 21:05:37

本日志只记录公开行情下载情况，不包含任何交易账号或下单信息。

## 本次运行参数

- batch-size：1
- sleep-seconds：3.0
- retry：1
- fetch-code：588000
- fetch-group：无
- fetch-source：baostock
- incremental：False
- lookback-days：10

## 成功统计

- fresh_download_success：1
- cached_success：0
- failed：0

## AKShare 接口诊断

| 接口 | 是否成功 | 行数 | 异常类型 | 异常文本 |
| --- | --- | ---: | --- | --- |

## 标的下载结果

| 代码 | 名称 | 类型 | 配置来源 | 尝试数据源 | 最终成功源 | enabled | 起始日期 | 结束日期 | 行数 | 状态 | 下载模式 | 使用本地缓存 | 失败原因 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| 588000 | 科创50ETF | ETF -> ETF | baostock | baostock | baostock | True -> True | 2025-01-01 | 2026-06-02 | 97 | fresh_download_success | full_download | 否 |  |

## 字段映射和保存诊断

| 代码 | 实际接口 | 最终成功源 | AKShare/BaoStock/公开接口原始字段 | 原始返回行数 | 标准 CSV 行数 | 字段映射 | 保存 CSV |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| 588000 | BaoStock query_history_k_data_plus | baostock | date, open, high, low, close, volume | 97 | 97 | 成功 | 成功 |

## 每次尝试明细

### 588000 科创50ETF
- 读取字段：code=588000，type=ETF -> ETF，source=baostock，enabled=True -> True
- 下载模式：full_download；本地缓存行数=0；请求日期：2025-01-01 -> 2026-06-02
- 日期转换：2025-01-01 -> 20250101，2026-06-02 -> 20260602
- 接口 1 / 重试 1：实际调用接口=BaoStock query_history_k_data_plus；原始字段=['date', 'open', 'high', 'low', 'close', 'volume']；返回行数=97
- 接口 1 / 重试 1：字段映射成功；保存 CSV=成功；标准字段=['date', 'open', 'high', 'low', 'close', 'volume']；保存后行数=97