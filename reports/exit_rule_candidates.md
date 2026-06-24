# Exit Rule Candidate Library 2026-06-18 16:01:13

本候选库只用于后续回测，不接入执行层。

- 规则族数量：8
- execution_enabled: false
- backtest_required: true

## 规则族
### Fixed Stop / Fixed Take Profit
- family: `fixed_stop_fixed_take_profit`
- fit: baseline only
- risk: 固定百分比容易忽略 ETF 类型差异，可能过拟合，也可能过早止盈卖飞。
- backtest_note: 作为 baseline，不建议直接作为最终规则。
```json
{
  "stop_loss_pct": [
    -0.03,
    -0.05,
    -0.08,
    -0.1
  ],
  "take_profit_pct": [
    0.05,
    0.08,
    0.12,
    0.15
  ]
}
```

### Fixed Stop + Trailing Take Profit
- family: `fixed_stop_trailing_take_profit`
- fit: good candidate for sector/theme ETF
- risk: 趋势强时较适合保护利润，但震荡市容易被洗出。
- backtest_note: 重点观察 profit giveback 和 whipsaw count。
```json
{
  "profit_protection_start_pct": [
    0.03,
    0.05,
    0.08
  ],
  "trailing_drawdown_pct": [
    0.025,
    0.03,
    0.04,
    0.05,
    0.06
  ]
}
```

### ATR Stop + ATR Trailing
- family: `atr_stop_atr_trailing`
- fit: strong candidate
- risk: ATR 参数太多，需防止按历史噪声调参。
- backtest_note: 适合作为跨 ETF 类型的波动自适应退出规则。
```json
{
  "atr_window": [
    14,
    20
  ],
  "initial_stop_atr_multiple": [
    1.5,
    2.0,
    2.5,
    3.0
  ],
  "trailing_stop_atr_multiple": [
    1.5,
    2.0,
    2.5,
    3.0
  ]
}
```

### Trend Breakdown Exit
- family: `trend_breakdown_exit`
- fit: strong candidate
- risk: MA10 易噪声，MA30 可能退出滞后。
- backtest_note: 适合与 ranking exit 组合，而不是单独使用。
```json
{
  "ma_break": [
    "MA10",
    "MA20",
    "MA30"
  ],
  "confirm_days": [
    1,
    2,
    3
  ]
}
```

### Ranking Drop Exit
- family: `ranking_drop_exit`
- fit: core candidate
- risk: 如果排名日内/日间抖动大，1 日确认会过度换手。
- backtest_note: 最符合横截面轮动逻辑，需重点测试换手和成本。
```json
{
  "exit_if_rank_below": [
    10,
    15,
    20,
    30
  ],
  "score_drop_threshold": [
    0.1,
    0.2,
    0.3
  ],
  "consecutive_days": [
    1,
    2,
    3
  ]
}
```

### Time Stop / Capital Efficiency Exit
- family: `time_stop_capital_efficiency_exit`
- fit: secondary candidate
- risk: 容易把慢趋势卖飞，尤其宽基和红利风格。
- backtest_note: 适合检验资金效率，不应单独作为硬退出。
```json
{
  "max_holding_days": [
    10,
    15,
    20,
    25,
    30
  ],
  "min_return_required": [
    0.0,
    0.01,
    0.02,
    0.03
  ]
}
```

### Market State Exit
- family: `market_state_exit`
- fit: risk overlay only
- risk: 市场状态误判会导致系统性踏空。
- backtest_note: 第一版只做 review only 或分组统计，不直接强制清仓。
```json
{
  "if_market_state": [
    "risk_off",
    "weak"
  ],
  "reduce_or_exit": [
    "review_only"
  ]
}
```

### Portfolio Exposure Exit
- family: `portfolio_exposure_exit`
- fit: risk review only
- risk: 组合暴露规则应先影响新买入和复核，不宜直接强制卖出。
- backtest_note: 观察集中度、回撤贡献和错失收益。
```json
{
  "if_same_group_overexposed": [
    "review_only"
  ],
  "if_high_beta_overexposed": [
    "review_only"
  ],
  "if_no_broad_based_anchor": [
    "review_only"
  ]
}
```
