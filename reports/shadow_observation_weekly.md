# Shadow Observation Weekly Review

本报告只做 shadow observation / reporting，不修改任何模型规则，不接执行层，不真实交易。

## 结论字段
- evidence_level: insufficient
- ready_to_relax_filters: false
- ready_for_preview: false
- ready_for_execution: false
- recommended_action: continue_observation
- summary: Forward returns are mostly pending; evidence is insufficient. Keep all filters unchanged and continue weekly observation.

## A. Shadow 模型状态
- top10_diversified_filter_v2 active: True
- persistence_breakout_v2 active: True
- all_models_research_only: true
- any_model_execution_enabled: false
- ready_for_execution: false

## 文件状态
| file                              | status   |
|:----------------------------------|:---------|
| persistence_tracking              | present  |
| missed_tracking                   | present  |
| persistence_signal                | present  |
| model_comparison                  | present  |
| persistence_portfolio             | present  |
| ranking_model_v2_shadow_signal    | missing  |
| ranking_model_v2_shadow_portfolio | missing  |
| strategy_preview_tracking_report  | present  |

## B. persistence_breakout_v2 最近观察
|   signal_days_5d |   selected_days_5d |   empty_signal_days_5d |   risk_on_empty_days_5d |   avg_selected_count_5d |   high_beta_selected_count_5d |   data_health_caution_selected_count_5d |   signal_days_10d |   selected_days_10d |   empty_signal_days_10d |   risk_on_empty_days_10d |   avg_selected_count_10d |   high_beta_selected_count_10d |   data_health_caution_selected_count_10d |   signal_days_20d |   selected_days_20d |   empty_signal_days_20d |   risk_on_empty_days_20d |   avg_selected_count_20d |   high_beta_selected_count_20d |   data_health_caution_selected_count_20d | top_filter_reasons                      |
|-----------------:|-------------------:|-----------------------:|------------------------:|------------------------:|------------------------------:|----------------------------------------:|------------------:|--------------------:|------------------------:|-------------------------:|-------------------------:|-------------------------------:|-----------------------------------------:|------------------:|--------------------:|------------------------:|-------------------------:|-------------------------:|-------------------------------:|-----------------------------------------:|:----------------------------------------|
|                1 |                  1 |                      0 |                       1 |                       1 |                             0 |                                       0 |                 1 |                   1 |                       0 |                        1 |                        1 |                              0 |                                        0 |                 1 |                   1 |                       0 |                        1 |                        1 |                              0 |                                        0 | trend_not_confirmed, liquidity_filtered |

重点判断：当前可用样本显示 selected_count 为 0；risk_on 空仓次数为 1。主要过滤原因：trend_not_confirmed, liquidity_filtered。

## C. missed opportunity 观察
|   candidate_count |   matured_1d_count |   matured_3d_count |   matured_5d_count |   matured_10d_count |   matured_20d_count |   pending_count |   missed_opportunity_count |   missed_opportunity_rate |   filter_effective_count |   filter_effective_rate | top_missed_filter_reason   |
|------------------:|-------------------:|-------------------:|-------------------:|--------------------:|--------------------:|----------------:|---------------------------:|--------------------------:|-------------------------:|------------------------:|:---------------------------|
|               123 |                114 |                 96 |                 77 |                  49 |                   0 |              74 |                         23 |                  0.186992 |                       26 |                0.211382 | trend_not_confirmed        |

如果大部分 forward return 仍 pending，则证据不足，不允许据此放宽规则。

## D. selected vs filtered vs benchmark
| selected_forward_5d_mean   | selected_forward_10d_mean   | filtered_forward_5d_mean   | filtered_forward_10d_mean   | benchmark_510300_forward_5d_mean   | benchmark_510300_forward_10d_mean   |
|:---------------------------|:----------------------------|:---------------------------|:----------------------------|:-----------------------------------|:------------------------------------|
|                            |                             |                            |                             |                                    |                                     |

## E. original / adjusted / v2 对比
| available   | original_symbols     | adjusted_symbols     | top10_symbols   |   persistence_symbols | more_aggressive_model   | more_diversified_model      | health_best_model       |
|:------------|:---------------------|:---------------------|:----------------|----------------------:|:------------------------|:----------------------------|:------------------------|
| True        | 516510 159929 515000 | 516510 159929 515000 |                 |                511030 | persistence_breakout_v2 | top10_diversified_filter_v2 | persistence_breakout_v2 |

| date       | model_name                  | selected_symbols     |   selected_count |   overlap_with_persistence |   overlap_symbols |   high_beta_count |   data_health_caution_count | forward_return_1d_mean   | forward_return_3d_mean   | forward_return_5d_mean   | forward_return_10d_mean   | excess_return_vs_510300_10d_mean   | execution_enabled   | research_only   |
|:-----------|:----------------------------|:---------------------|-----------------:|---------------------------:|------------------:|------------------:|----------------------------:|:-------------------------|:-------------------------|:-------------------------|:--------------------------|:-----------------------------------|:--------------------|:----------------|
| 2026-07-09 | persistence_breakout_v2     | 511030               |                1 |                          1 |            511030 |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-07-09 | original_ranking            | 516510 159929 515000 |                3 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-07-09 | adjusted_preview_ranking    | 516510 159929 515000 |                3 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-07-09 | top10_diversified_filter_v2 |                      |                0 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-07-09 | buy_and_hold_510300         | 510300               |                1 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |

## 安全边界
- 不接券商 API
- 不真实下单
- 不修改 paper_trades.csv
- 不修改 paper_positions.csv
- 不改变 paper_trade_engine.py
- 不修改 persistence_breakout_v2 或 top10_diversified_filter_v2 规则
- forward return 只作为事后 label，不作为当日特征
