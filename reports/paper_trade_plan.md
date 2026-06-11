# 规则验证版模拟交易计划 2026-06-10

本报告只针对本地模拟盘，不接券商 API，不真实下单。

## 引擎状态
- PAPER_MODE：rule_validation
- PAPER_AUTO_EXECUTE：True
- REAL_TRADE_ENABLED：False
- BROKER_API_ENABLED：False
- status：executed
- dry_run：False
- buy_count：0
- sell_count：0
- skipped_duplicate：False
- skip_reason：

## 账户摘要
- 执行前现金：7124.30
- 执行前仓位：28.29%
- 执行后现金：7124.30
- 执行后仓位：28.29%

## 交易计划与结果
| date | symbol | name | action | status | price | quantity | amount | reason |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-06-10 | 515220 | 煤炭ETF | SELL | skipped_no_sell_signal | 1.305 | 1100 | 0 | sell rules not triggered |
| 2026-06-10 | 512800 | 银行ETF | SELL | skipped_no_sell_signal | 0.806 | 1100 | 0 | sell rules not triggered |
| 2026-06-10 | 515880 | 证券公司ETF | SELL | skipped_no_sell_signal | 1.63 | 300 | 0 | sell rules not triggered |
| 2026-06-10 | 512800 | 银行ETF | BUY | skipped_rule_blocked | 0.806 | 0 | 0 | already held |
| 2026-06-10 | 515220 | 煤炭ETF | BUY | skipped_rule_blocked | 1.305 | 0 | 0 | already held |
| 2026-06-10 | 515880 | 证券公司ETF | BUY | skipped_rule_blocked | 1.63 | 0 | 0 | already held; data_health caution amount * 0.5 |

## 安全边界
- 只写本地模拟盘。
- 不接真实交易。
- 不添加真实交易按钮。