# Tushare vs BaoStock 数据对比 2026-06-21 21:00:03

本报告只对比 Tushare staging 样本和本地正式 ETF CSV，不覆盖正式数据。

## 摘要
- status: completed
- symbols_compared: 5
- close_consistent_count: 5
- recommended_daily_source: baostock
- candidate_daily_source: tushare
- formal_source_switched: False

## 明细
| symbol | overlap | open_pct | high_pct | low_pct | close_pct | volume_pct | amount_pct | volume_ratio | amount_ratio | missing_tushare | missing_baostock | quality_note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 159915 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.999 | 100.0 | 1000.0 | 0 | 0 | OHLC basically consistent; volume likely differs by 100x; amount likely differs by 1000x |
| 510300 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.999 | 100.0 | 1000.0 | 0 | 0 | OHLC basically consistent; volume likely differs by 100x; amount likely differs by 1000x |
| 512880 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.999 | 100.0 | 1000.0 | 0 | 0 | OHLC basically consistent; volume likely differs by 100x; amount likely differs by 1000x |
| 515790 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.999 | 100.0 | 1000.0 | 0 | 0 | OHLC basically consistent; volume likely differs by 100x; amount likely differs by 1000x |
| 518880 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.999 | 100.0 | 1000.0 | 0 | 0 | OHLC basically consistent; volume likely differs by 100x; amount likely differs by 1000x |

## 口径判断
- close 若差异接近 0，可初步认为价格口径一致。
- open/high/low/close 若差异接近 0，可初步认为价格口径一致。
- volume / amount 若差异大，需确认 Tushare 单位、BaoStock 单位、是否手/股、千元/元口径。
- 本轮不切换正式日更主源，不进入 BUY ranking 或正式回测。