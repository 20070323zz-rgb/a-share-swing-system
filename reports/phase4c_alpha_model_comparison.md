# Phase 4C Alpha 模型综合对比 2026-06-21 21:17:52

- best_candidate: persistence_breakout_v2
- candidate_type: strong_shadow
- ready_for_shadow: True
- ready_for_execution: False

| strategy | return | max_drawdown | calmar | trades | cost | beat_510300 | beat_v2 | shadow | weakness |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| original_baseline_v2 | 1.64% | -9.63% | 0.16 | 76 | 470.26 | False | False | False | does_not_beat_510300 |
| adjusted_preview_baseline_v2 | 5.05% | -8.42% | 0.57 | 76 | 470.44 | False | False | False | does_not_beat_510300 |
| top10_diversified_filter_v2 | 11.31% | -4.86% | 2.21 | 62 | 384.01 | False | False | False | does_not_beat_510300 |
| buy_and_hold_510300 | 19.94% | -6.58% | 2.87 | 1 | 8.59 | False | True | False | does_not_beat_510300 |
| risk_off_defensive_v2 | 16.54% | -4.07% | 3.85 | 64 | 396.40 | False | True | True | does_not_beat_510300 |
| single_score_v2_baseline | 14.03% | -4.61% | 2.88 | 68 | 421.04 | False | True | True | does_not_beat_510300 |
| persistence_breakout_v2 | 20.19% | -3.43% | 5.58 | 76 | 469.96 | True | True | True | research_only_not_executed |