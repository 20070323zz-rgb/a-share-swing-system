# AKShare 可用性诊断 2026-06-21 20:13:30

本报告仅做低频连通性诊断，不写入 data/etf_daily，不接券商 API，不真实下单。

## 结论
- akshare_status: partially_usable
- akshare_version: 1.18.64
- proxy_env_present: none
- 推荐角色：Use AKShare only as an optional fallback and intelligence-data probe with retry/backoff and local cache; do not use it as primary daily ETF update source.

## 接口探测
| test | status | rows | elapsed_seconds | error_type | error |
| --- | --- | ---: | ---: | --- | --- |
| trade_calendar_light | success | 8797 | 0.837 |  |  |
| etf_history_small_range | failed | 0 | 0.526 | ProxyError | HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf |
| a_share_history_small_range | success | 14 | 0.486 |  |  |
| etf_spot_latest | success | 1514 | 17.014 |  |  |

## 可能原因
- proxy configuration may be interfering with Eastmoney/Sina endpoints.
- remote endpoints may close connections or rate-limit requests from the current network.

## 安全边界
- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存或打印任何账号密码/token
- 不写入正式行情目录