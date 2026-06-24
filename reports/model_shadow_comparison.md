# Model Shadow Comparison 2026-06-24

对比 persistence_breakout_v2 与 original / adjusted preview / top10_diversified_filter_v2 / 510300。仅研究，不接执行层。

- overlap_with_original: 0
- overlap_with_adjusted: 0
- overlap_with_top10_diversified: 0
- execution_enabled: false

| date       | model_name                  | selected_symbols     |   selected_count |   overlap_with_persistence | overlap_symbols   |   high_beta_count |   data_health_caution_count | forward_return_1d_mean   | forward_return_3d_mean   | forward_return_5d_mean   | forward_return_10d_mean   | excess_return_vs_510300_10d_mean   | execution_enabled   | research_only   |
|:-----------|:----------------------------|:---------------------|-----------------:|---------------------------:|:------------------|------------------:|----------------------------:|:-------------------------|:-------------------------|:-------------------------|:--------------------------|:-----------------------------------|:--------------------|:----------------|
| 2026-06-24 | persistence_breakout_v2     | 512400 159352        |                2 |                          2 | 159352 512400     |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-06-24 | original_ranking            | 512880 159819 515070 |                3 |                          0 |                   |                 1 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-06-24 | adjusted_preview_ranking    | 512880 159819 515070 |                3 |                          0 |                   |                 1 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-06-24 | top10_diversified_filter_v2 |                      |                0 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
| 2026-06-24 | buy_and_hold_510300         | 510300               |                1 |                          0 |                   |                 0 |                           0 |                          |                          |                          |                           |                                    | False               | True            |
