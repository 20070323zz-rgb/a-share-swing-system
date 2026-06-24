# Phase 4C-Data 下一步建议 2026-06-21 20:14:02

## 当前结论
- AKShare 状态：partially_usable
- 推荐下一步：先把 AKShare 接为低频情报/特殊数据源候选；日线主源仍保留现有验证链路。

## 建议路线
1. 不替换当前日常更新主链路，先保留 BaoStock/local cache 的稳定路径。
2. 若 Tushare token 可用，下一阶段只做 staging dry-run，不直接正式写入。
3. AKShare 若可用，优先做情报/特殊数据和低频补充，不做 183 只 ETF 日更主源。
4. 新 provider 层先做 dry-run 报告，对比现有 update_etf_data.py 的结果。
5. 所有情报数据先进入 dashboard 解释层和 research/shadow，不接执行层。

## Phase 4D 候选任务
- 建立 provider dry-run orchestrator。
- 建立 intelligence_staging schema 和关键词映射样例。
- 对 Tushare 日线做 5-10 只 ETF staging 对比测试。
- 对 AKShare 做一周低频稳定性监控。
- 在 dashboard 增加 source freshness / provider circuit breaker 展示。