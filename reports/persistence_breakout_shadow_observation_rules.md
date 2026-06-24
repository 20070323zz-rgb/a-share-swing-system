# persistence_breakout_v2 Shadow Observation Rules

本规则只用于研究观察，不修改 BUY ranking、paper_trade_engine、paper_trades.csv 或 paper_positions.csv。

## 观察期
- 最少连续观察 20 个交易日。
- 同时记录 1/3/5/10/20 日未来收益，并与 510300 对比。
- 至少完成一个包含 risk_on / neutral / risk_off 的市场状态样本后，再讨论是否进入 preview。

## 可进入 preview 的最低条件
- 10 日平均超额收益稳定为正。
- selected ETF 的 data_health caution 数量低。
- high_beta 暴露没有明显放大回撤。
- 与 original / adjusted / top10_diversified 的差异能解释，而不是随机换仓。

## 当前结论
- ready_for_preview=false。
- ready_for_execution=false。
- execution_enabled=false。
- paper_trade_engine_enabled=false。
- real_trade_enabled=false。
