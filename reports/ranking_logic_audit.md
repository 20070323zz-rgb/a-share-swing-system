# Ranking Logic Audit 2026-06-18 20:26:19

本报告审计 ranking 逻辑差异，不修改执行层。

## Daily Signal 因子
- mid_trend / short_swing signals
- MA10/MA20/MA60 trend
- 5/10/20/60 day returns
- relative strength vs benchmark
- RSI14
- volume ratio / liquidity proxy
- 20d volatility and drawdown
- group/category metadata
- data_health filter

## Phase 4A Simplified Backtest 因子
- momentum 10/20/60d
- MA20/MA60 distance and slope
- 20d volatility penalty
- 20d drawdown penalty
- 20d amount liquidity proxy

## 关键差异
- Phase 4A backtest does not replay full mid_trend/short_swing signal engine.
- Phase 4A adjusted preview is a lightweight type/risk proxy, not the full daily preview layer.
- Current daily preview is mostly risk penalty / exposure adjustment, not a pure alpha forecast.
- Historical data_health and portfolio_exposure were not fully replayed date-by-date.

## 结论
- 当前 Phase 4A 回测能否代表完整模型：否。
- adjusted preview 是否主要是风险降权：是。
- 是否存在短期动量权重过高风险：是。
- 是否存在趋势确认不足：是。
- 是否存在换手惩罚不足：是。
- 是否存在不同 ETF 类型横向比较不公平：是。
