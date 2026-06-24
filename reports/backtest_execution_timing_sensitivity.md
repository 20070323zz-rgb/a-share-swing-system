# Backtest Execution Timing Sensitivity 2026-06-18 20:28:15

| execution_mode | horizon | avg_forward_return_proxy | volatility_proxy | positive_ratio | realism | note |
| --- | --- | --- | --- | --- | --- | --- |
| signal_confirmed_after_close_next_open | 1 | -0.000507 | 0.016414 | 0.436309 | acceptable | next open execution after confirmed close |
| signal_confirmed_after_close_next_open | 3 | 0.000335 | 0.029781 | 0.482447 | acceptable | next open execution after confirmed close |
| signal_confirmed_after_close_next_open | 5 | 0.001220 | 0.038888 | 0.496489 | acceptable | next open execution after confirmed close |
| signal_confirmed_after_close_next_open | 10 | 0.002785 | 0.052648 | 0.455366 | acceptable | next open execution after confirmed close |
| signal_confirmed_after_close_next_close | 1 | 0.000493 | 0.016414 | 0.460381 | optimistic | next close execution after confirmed close |
| signal_confirmed_after_close_next_close | 3 | 0.001335 | 0.029781 | 0.505517 | optimistic | next close execution after confirmed close |
| signal_confirmed_after_close_next_close | 5 | 0.002220 | 0.038888 | 0.510532 | optimistic | next close execution after confirmed close |
| signal_confirmed_after_close_next_close | 10 | 0.003785 | 0.052648 | 0.466399 | optimistic | next close execution after confirmed close |
| previous_confirmed_close_pre_open_plan | 1 | -0.001507 | 0.016414 | 0.410231 | preferred | use previous confirmed close to plan next open |
| previous_confirmed_close_pre_open_plan | 3 | -0.000665 | 0.029781 | 0.464393 | preferred | use previous confirmed close to plan next open |
| previous_confirmed_close_pre_open_plan | 5 | 0.000220 | 0.038888 | 0.478435 | preferred | use previous confirmed close to plan next open |
| previous_confirmed_close_pre_open_plan | 10 | 0.001785 | 0.052648 | 0.446339 | preferred | use previous confirmed close to plan next open |
| next_close_current_v1 | 1 | 0.000493 | 0.016414 | 0.460381 | optimistic | Phase 4A-1 next_close assumption |
| next_close_current_v1 | 3 | 0.001335 | 0.029781 | 0.505517 | optimistic | Phase 4A-1 next_close assumption |
| next_close_current_v1 | 5 | 0.002220 | 0.038888 | 0.510532 | optimistic | Phase 4A-1 next_close assumption |
| next_close_current_v1 | 10 | 0.003785 | 0.052648 | 0.466399 | optimistic | Phase 4A-1 next_close assumption |

## 结论
- same_day_close 不应作为正式可执行口径。
- Phase 4A-1 的 next_close 假设比 same_day_close 保守，但仍未显式建模数据源 confirmed 延迟。
- 推荐后续采用 confirmed close -> next-day plan 的口径，并单独比较 next_open / next_close。
