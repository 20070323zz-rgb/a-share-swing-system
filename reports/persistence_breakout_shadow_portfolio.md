# persistence_breakout_v2 Shadow Portfolio 2026-06-24

本影子组合只用于观察，不执行交易，不写模拟盘正式持仓。

- initial_cash: 20000
- max_holdings: 3
- target_weight_per_etf: 20%
- target_total_weight: 60%
- min_trade_value: 3000
- execution_enabled: false

| date       | model_name              |   symbol | name        |   rank |   final_score |   target_weight |   target_value |   shadow_price |   lot_size |   shadow_quantity |   estimated_position_value |   min_trade_value | execution_enabled   | paper_trade_engine_enabled   | real_trade_enabled   | shadow_action        | selection_reason                                                                 |
|:-----------|:------------------------|---------:|:------------|-------:|--------------:|----------------:|---------------:|---------------:|-----------:|------------------:|---------------------------:|------------------:|:--------------------|:-----------------------------|:---------------------|:---------------------|:---------------------------------------------------------------------------------|
| 2026-06-24 | persistence_breakout_v2 |   512400 | 有色ETF       |     10 |       65.8119 |             0.2 |           4000 |          1.98  |        100 |              2000 |                     3960   |              3000 | False               | False                        | False                | OPEN_SHADOW_POSITION | rank_10; final_score_65.81; persistence_0.0; trend_confirmed                     |
| 2026-06-24 | persistence_breakout_v2 |   159352 | 南方中证A500ETF |     11 |       61.8524 |             0.2 |           4000 |          1.373 |        100 |              2900 |                     3981.7 |              3000 | False               | False                        | False                | OPEN_SHADOW_POSITION | rank_11; final_score_61.85; persistence_0.0; breakout_confirmed; trend_confirmed |
