# Tushare staging dry-run 2026-06-21 20:58:01

本报告只检查 Tushare 小样本 staging，不覆盖 data/etf_daily，不接执行层。

## 摘要
- status: completed
- tushare_token_configured: True
- provider_ready: True
- tested: 5
- success: 5
- failed: 0
- rows_written: 150
- staging_csv: data/staging/tushare/tushare_etf_daily_sample.csv
- recommended_next_step: Tushare small sample looks good; next step can expand staging to 20-30 ETFs, still no formal overwrite.

## 明细
| symbol | name | status | rows | start | end | failure_reason |
| --- | --- | --- | ---: | --- | --- | --- |
| 510300 | 沪深300ETF | success | 30 | 2026-05-08 | 2026-06-18 |  |
| 159915 | 创业板ETF | success | 30 | 2026-05-08 | 2026-06-18 |  |
| 512880 | 证券ETF | success | 30 | 2026-05-08 | 2026-06-18 |  |
| 518880 | 黄金ETF | success | 30 | 2026-05-08 | 2026-06-18 |  |
| 515790 | 光伏ETF | success | 30 | 2026-05-08 | 2026-06-18 |  |

## 质量判断
- ETF 日线接口可用：True
- 字段 schema 完整：True
- available_date 当前按 T+1 自然日估算，尚不可直接进入 alpha。
- 本轮不扩大到 183 只，不切换正式主源。

## 安全边界
- 不覆盖正式数据
- 不接 BUY ranking / paper_trade_engine / 正式回测
- 不打印 token