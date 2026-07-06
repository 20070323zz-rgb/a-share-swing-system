# 模拟仓估值一致性审计

本报告只读取本地模拟仓和 ETF 日线数据，不接券商 API，不真实下单，不修改 paper_positions / paper_trades。

## 结论
- status：PASS
- 正式估值口径：data/paper_positions.csv + data/etf_daily/{symbol}.csv latest close
- 估值日期：2026-06-26
- 持仓数量：3
- 统一最新 close 持仓市值：3008.10
- paper_performance 持仓市值：3008.10
- portfolio_exposure 持仓市值：3008.10
- 统一后差异：0.00
- 原持仓快照旧市值与绩效差异：66.70

## 持仓估值明细
| symbol | name | quantity | latest_close | market_value | position_file_market_value | diff_vs_position_file | as_of_date | price_status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 512800 | 银行ETF | 1100 | 0.7460 | 820.60 | 828.30 | -7.70 | 2026-06-26 | ok |
| 515000 | 科技ETF | 1000 | 1.6340 | 1634.00 | 1672.00 | -38.00 | 2026-06-26 | ok |
| 512880 | 证券ETF | 500 | 1.1070 | 553.50 | 574.50 | -21.00 | 2026-06-26 | ok |

## 差异解释
- paper_positions.csv 内的 market_value 是持仓快照字段，可能滞后于最新 ETF 日线 close。
- paper_performance 使用本地 ETF close 生成权益曲线和当前持仓市值。
- portfolio_exposure 已改为使用统一估值模块，避免继续引用旧快照市值。

## 安全边界
- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未修改 paper_positions.csv / paper_trades.csv。