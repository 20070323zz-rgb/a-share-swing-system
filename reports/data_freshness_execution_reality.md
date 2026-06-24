# Data Freshness and Execution Reality 2026-06-18 20:28:15

本报告将数据源现实约束纳入 ranking 和回测评估。

## 当前事实

1. BaoStock 当日日线可能晚更新。
2. JQData 当前不能作为日常主源，只能作为历史源或阶段性补齐。
3. Tushare 尚未正式进入日常源。
4. 因此正式信号必须基于 confirmed 数据生成次日计划。
5. 不应假设 15:30 一定能拿到完整当日日线。

## 对回测的影响

- `next_close` 不使用 same-day close 成交，方向上比 same-day 更保守。
- 但如果真实数据源要 T+1 才 confirmed，则回测还需要加入信号确认延迟。
- 卖出策略不能假设日线刚收盘马上可执行；应采用“盘前计划 + 盘中人工观察 + 收盘确认”。

## 调度建议

- `open_check`：只做风险观察和昨日报告复核。
- `daily_close`：先检查数据源是否 confirmed；未 confirmed 时不生成正式新信号。
- `catchup`：次日或数据源可用后补齐日线，再生成正式次日计划。
- App 看板应显示数据 confirmed 状态，避免把 stale 数据误判为最新交易计划。

## 安全边界

本报告不接券商 API、不真实下单、不读取真实账户。
