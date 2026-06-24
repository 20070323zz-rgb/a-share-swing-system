# Backtest Expand Pool Decision 2026-06-19 00:53:15

- expand_pool_now: false

## 原因
- first fix backtest consistency/timing issues
- cost drag is too high at 10k capital
- 13 symbols have meaningful negative contribution

## 扩池前必须完成
- resolve unknown classifications
- keep QDII observe-only until premium/fx/calendar checks exist
- keep low-liquidity ETFs excluded
- prove ranking edge on filtered 39 ETF pool
- reduce turnover/cost drag

## 下一步建议
- fix/confirm Phase 4A timing and return calculation before judging strategy edge
- test lower turnover rules: minimum holding days, cooldown, wider ranking exit threshold
- separate cost model by capital size and minimum trade amount
- review negative-contribution symbols before expanding trade_pool
- validate ranking effectiveness before adding complex exit rules

## 安全边界
- 本报告只做研究诊断，不修改模拟交易，不接实盘。
