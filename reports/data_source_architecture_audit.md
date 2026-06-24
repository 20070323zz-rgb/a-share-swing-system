# 数据源架构审计 2026-06-21 20:14:02

本报告是 Phase 4C-Data 研究审计，不修改交易策略、不修改模拟持仓、不接券商 API、不真实下单。

## 摘要结论
- 当前正式 ETF 文件数量：183
- 最近数据源实际使用：baostock
- 最近最新数据日：2026-06-18
- 最近新增行数：183
- BaoStock API calls：183
- 当前运行层已具备状态报告和 fallback 记录，但 provider 抽象层仍处于设计/轻实现阶段。
- 新情报/新闻/资金数据必须先进入研究层，不能直接接入 BUY 或 SELL 执行层。

## 当前数据链路
| 环节 | 当前实现 | 审计判断 |
| --- | --- | --- |
| 日线更新入口 | scripts/update_etf_data.py | 可继续保留为稳定入口 |
| 数据源路由 | src/data_sources/source_router.py | 已记录 JQData/BaoStock 状态，但 Tushare 未正式实现 |
| JQData | src/data_sources/jqdata_source.py | 适合 staging/history，不应绕过 validate/dry-run |
| BaoStock | update_etf_data 主路径 | 当前可用但延迟较高，适合作 fallback/日更低频 |
| AKShare | 本轮新增诊断 | 先按诊断结果决定是否只能辅助 |
| 本地 CSV | data/etf_daily | 正式研究主库，本地原行优先 |

## 发现与建议
### daily_update
- 发现：scripts/update_etf_data.py is still the operational daily-update entry. It supports source selection and delegates non-BaoStock sources to src/data_sources/source_router.py.
- 风险：source priority and provider health are not yet managed by a formal provider abstraction.
- 建议：Keep current path stable, then introduce provider layer in staged dry-run mode.

### source_router
- 发现：src/data_sources/source_router.py records machine-readable source status and fallback decisions.
- 风险：Tushare is currently not implemented as a working daily source, and JQData may be unavailable for daily updates.
- 建议：Use Tushare only after explicit token/config tests; treat JQData as historical/staging unless daily access is proven.

### formal_data
- 发现：data_health/data_coverage read local CSVs only and are suitable downstream validators.
- 风险：source metadata columns are not consistently present in existing formal CSVs.
- 建议：Add source/fetch_time/available_date in future staging files; do not retroactively rewrite trusted old rows unless audited.

### research_model
- 发现：features and v2 backtest use local confirmed daily bars and do not require provider credentials.
- 风险：new intelligence data could introduce look-ahead if available_date is not tracked.
- 建议：Any non-price data must include publish_time, fetch_time, available_date, and confirmed_after_close flags.

## 目标统一字段
`date, open, high, low, close, volume, amount, source, fetch_time, available_date`

## 推荐数据源优先级
- 日更：tushare_if_configured, baostock, akshare_fallback
- 历史补齐：jqdata, baostock, tushare_if_configured, akshare_fallback
- 情报/特殊数据：akshare, tushare, manual

## 安全边界
- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不修改 paper_trades.csv / paper_positions.csv / paper_trade_engine.py
- 不把新数据因子直接接入正式执行层