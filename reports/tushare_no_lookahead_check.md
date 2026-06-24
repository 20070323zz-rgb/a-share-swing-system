# Tushare no-lookahead 检查 2026-06-21 20:58:01

- Tushare staging 数据包含 `available_date` 字段。
- 当前 `available_date` 规则为 `estimated_t_plus_1_calendar_day`，属于估算，不是真实确认的可得时间。
- 因此 Tushare staging 数据当前不能进入正式 alpha、BUY ranking、paper_trade_engine 或正式回测。
- T 日数据只能在 T+1 或以后使用；若后续接入研究因子，必须先确认真实可得时间。
- 本轮数据只写入 `data/staging/tushare/`，不覆盖 `data/etf_daily/`。

- staging_status: completed
- rows_written: 150
- available_date_estimated: True