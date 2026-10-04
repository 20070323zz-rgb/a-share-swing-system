# P2风险调整动量稳健性硬化与前瞻冻结

1. 判定：`P2_NOT_INCREMENTAL_TO_RET20`；仅RESEARCH，不Promotion。
2. 基线：`baseline_replay_exact=true`，243笔完整往返；公式和D/D+1语义检查通过。
3. 冻结契约：`SIGNAL_V2_P2_CONTRACT_V1` / `898716bf3f28ed64fe93ce42abad67a8c5cdd5cc7f80385604946206f0653738`。
4. Shadow：`created=false`，原因：`ALL_HARDENING_GATES_NOT_PASSED`。

## 决策门

| gate                          | passed   | detail                                    |
|:------------------------------|:---------|:------------------------------------------|
| rolling_direction_consistency | True     | 3/3                                       |
| start_path_no_flip            | True     | flips=0                                   |
| cost_1_25x_positive           | True     | breakeven=1.518987x                       |
| full_reallocation_loo_no_flip | False    | flips=50                                  |
| incremental_to_ret20          | False    | net_ann_delta=-0.017449;ic_delta=0.052278 |

## 滚动时间验证

| window                          | observation_start   | observation_end   | test_start   | test_end   |   observation_rank_ic |   test_rank_ic |   test_top_bottom_spread |   test_top5_return |   test_candidate_cost_coverage |   gross_return |   net_return |   maximum_drawdown |   trade_count |   transaction_cost_cny |   gross_profit_cost_coverage | direction_consistent   |
|:--------------------------------|:--------------------|:------------------|:-------------|:-----------|----------------------:|---------------:|-------------------------:|-------------------:|-------------------------------:|---------------:|-------------:|-------------------:|--------------:|-----------------------:|-----------------------------:|:-----------------------|
| OBS_2022_2023_TEST_2024         | 2022-04-07          | 2023-12-31        | 2024-01-01   | 2024-12-31 |              0.089069 |       0.016534 |                 0.00691  |           0.013977 |                       0.47619  |       0.015509 |    -0.035723 |          -0.112932 |            58 |                769.252 |                     0.277119 | True                   |
| OBS_2022_2024_TEST_2025         | 2022-04-07          | 2024-12-31        | 2025-01-01   | 2025-12-31 |              0.060564 |       0.012553 |                 0.01145  |           0.037173 |                       0.630471 |       0.416331 |     0.424503 |          -0.081132 |            56 |                764.702 |                     9.66611  | True                   |
| OBS_2022_2025_TEST_2026_TO_0706 | 2022-04-07          | 2025-12-31        | 2026-01-01   | 2026-07-06 |              0.047312 |       0.140371 |                 0.058645 |           0.023807 |                       0.488889 |       0.105301 |     0.098718 |          -0.111613 |            30 |                434.622 |                     3.41101  | True                   |

## 起始路径敏感性

|   start_offset_trading_days | start_date   |   net_annualized_return |   maximum_drawdown |   trade_count |   trade_jaccard_vs_original |   net_profit_cny | conclusion_positive   | conclusion_flip_vs_original   |
|----------------------------:|:-------------|------------------------:|-------------------:|--------------:|----------------------------:|-----------------:|:----------------------|:------------------------------|
|                           0 | 2022-04-07   |                0.019737 |          -0.340899 |           243 |                    1        |          1731.93 | True                  | False                         |
|                           5 | 2022-04-14   |                0.129071 |          -0.218936 |           244 |                    0.13785  |         13422.5  | True                  | False                         |
|                          10 | 2022-04-21   |                0.018467 |          -0.179976 |           240 |                    0.139151 |          1601.98 | True                  | False                         |
|                          20 | 2022-05-10   |                0.052582 |          -0.306654 |           238 |                    0.979424 |          4750.69 | True                  | False                         |

## 成本压力

|   cost_multiplier | path_and_quantity_frozen   |   net_annualized_return |   net_profit_cny |   maximum_drawdown |   gross_profit_cost_coverage |   breakeven_cost_multiplier | advantage_positive   |   first_tested_multiplier_advantage_disappears |
|------------------:|:---------------------------|------------------------:|-----------------:|-------------------:|-----------------------------:|----------------------------:|:---------------------|-----------------------------------------------:|
|              0.5  | True                       |                0.037646 |        3400.51   |          -0.295075 |                     3.03797  |                     1.51899 | True                 |                                              2 |
|              1    | True                       |                0.019737 |        1731.93   |          -0.340899 |                     1.51899  |                     1.51899 | True                 |                                              2 |
|              1.25 | True                       |                0.010386 |         897.648  |          -0.365043 |                     1.21519  |                     1.51899 | True                 |                                              2 |
|              1.5  | True                       |                0.000745 |          63.3608 |          -0.393213 |                     1.01266  |                     1.51899 | True                 |                                              2 |
|              2    | True                       |               -0.019497 |       -1605.21   |          -0.449617 |                     0.759493 |                     1.51899 | False                |                                              2 |

## 完整重新分配LOO（选择项）

| dimension   | entity          | selected_for_detailed_report   |   net_annualized_return |   maximum_drawdown |   total_cost_cny |   net_profit_cny |   trade_count |   substitute_buy_count |   candidate_rank_ic_20d | conclusion_flip   |
|:------------|:----------------|:-------------------------------|------------------------:|-------------------:|-----------------:|-----------------:|--------------:|-----------------------:|------------------------:|:------------------|
| ETF         | 515880          | True                           |               -0.046586 |          -0.318082 |          3323.22 |         -3669.73 |           242 |                     68 |                0.050662 | True              |
| ETF         | 518880          | True                           |                0.10207  |          -0.233448 |          3687.17 |         10226.1  |           241 |                    148 |                0.055504 | False             |
| FAMILY      | SECTOR_CYCLICAL | True                           |               -0.048621 |          -0.327661 |          3391.18 |         -3817.26 |           241 |                    194 |                0.050775 | True              |
| YEAR        | 2025            | True                           |               -0.05739  |          -0.355251 |          2536.86 |         -4441.67 |           187 |                     18 |                0.071703 | True              |

## 风险来源

| drawdown_start   | drawdown_end   |   net_maximum_drawdown |   gross_drawdown_at_net_trough |   cost_drawdown_gap |   cost_in_window_cny | market_state_day_counts                              |   loss_making_etf_count |   top2_loss_share | risk_breadth       |   entry_raw_rank_mean |   entry_candidate_rank_mean |   new_position_net_pnl_cny |   existing_position_net_pnl_cny |
|:-----------------|:---------------|-----------------------:|-------------------------------:|--------------------:|---------------------:|:-----------------------------------------------------|------------------------:|------------------:|:-------------------|----------------------:|----------------------------:|---------------------------:|--------------------------------:|
| 2022-04-08       | 2024-09-11     |              -0.340899 |                      -0.249319 |             0.09158 |              1899.27 | {"DEFENSIVE": 362, "NEUTRAL": 127, "OFFENSIVE": 104} |                      37 |           0.17361 | BROAD_SYNCHRONIZED |                9.1194 |                     2.32836 |                   -6276.81 |                               0 |

## 简单基准

| method                                     |   run_count |   candidate_rank_ic_20d |   gross_annualized_return |   net_annualized_return |   maximum_drawdown |   turnover |   total_cost_cny |   gross_profit_cost_coverage |   net_profit_cny |   incremental_net_ann_vs_ret20 |   incremental_rank_ic_vs_ret20 |
|:-------------------------------------------|------------:|------------------------:|--------------------------:|------------------------:|-------------------:|-----------:|-----------------:|-----------------------------:|-----------------:|-------------------------------:|-------------------------------:|
| P2_RISK_ADJUSTED_MOMENTUM_ALL              |           1 |                0.057092 |                  0.054603 |                0.019737 |          -0.340899 |    84.2499 |          3337.15 |                     1.51899  |        1731.93   |                      -0.017449 |                       0.052278 |
| BENCHMARK_RET20                            |           1 |                0.004814 |                  0.071907 |                0.037186 |          -0.278505 |    82.8848 |          3507.54 |                     1.95693  |        3356.48   |                       0        |                       0        |
| BENCHMARK_ELIGIBLE_EQUAL_WEIGHT_EXECUTABLE |           1 |                0        |                  0.081426 |                0.048072 |          -0.345879 |    85.6434 |          3476.53 |                     2.27022  |        4415.97   |                       0.010885 |                      -0.004814 |
| BENCHMARK_FIXED_RANDOM_MEAN                |          10 |                0.001205 |                  0.032758 |               -0.006546 |          -0.319436 |    83.7669 |          3441.46 |                     0.922099 |         -25.2808 |                      -0.043733 |                      -0.003609 |

## 保护边界

正式Score/Ranking、生产策略、Universe、分配器、卖出规则和paper ledgers均未修改；未搜索窗口、权重、阈值或新因子；未使用Regime；未Promotion。
