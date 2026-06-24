# Backtest Trade Distribution 2026-06-19 00:52:44

| strategy | round_trips | win_rate | avg_win | avg_loss | max_win | max_loss | profit_factor | avg_holding_days | median_holding_days | short_loss_count_le_5d | cost_total | gross_pnl | net_pnl | cost_drag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adjusted_preview_baseline | 118 | 0.398305 | 296.989664 | -166.740006 | 1310.606800 | -532.336900 | 1.179074 | 29.093220 | 29.000000 | 3 | 1454.925000 | 3574.900000 | 2119.973800 | 1454.926200 |
| original_ranking_baseline | 117 | 0.384615 | 308.432398 | -175.995346 | 1310.606800 | -614.362000 | 1.095314 | 29.367521 | 29.000000 | 2 | 1442.606300 | 2650.400000 | 1207.793000 | 1442.607000 |

## 诊断
- 若 profit_factor 接近 1，说明策略更多是在成本后勉强打平。
- 若短持有亏损较多，应优先测试 cooldown / minimum holding days。
- 小盈利容易被最低佣金吞掉，移动止盈要等 ranking 有效性确认后再测。
