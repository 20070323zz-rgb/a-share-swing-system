# persistence_breakout_v2 Shadow Portfolio 2026-07-03

本影子组合只用于观察，不执行交易，不写模拟盘正式持仓。

- initial_cash: 20000
- max_holdings: 3
- target_weight_per_etf: 20%
- target_total_weight: 60%
- min_trade_value: 3000
- execution_enabled: false

| date       | model_name              |   symbol | name   |   rank |   final_score |   target_weight |   target_value |   shadow_price |   lot_size |   shadow_quantity |   estimated_position_value |   min_trade_value | execution_enabled   | paper_trade_engine_enabled   | real_trade_enabled   | shadow_action        | selection_reason                                                                 |
|:-----------|:------------------------|---------:|:-------|-------:|--------------:|----------------:|---------------:|---------------:|-----------:|------------------:|---------------------------:|------------------:|:--------------------|:-----------------------------|:---------------------|:---------------------|:---------------------------------------------------------------------------------|
| 2026-07-03 | persistence_breakout_v2 |   511030 | 公司债ETF |     11 |       68.9719 |             0.2 |           4000 |         108.06 |        100 |                 0 |                          0 |              3000 | False               | False                        | False                | SKIP_MIN_TRADE_VALUE | rank_11; final_score_68.97; persistence_0.0; breakout_confirmed; trend_confirmed |
