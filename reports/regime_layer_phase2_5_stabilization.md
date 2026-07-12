# Regime Layer Phase 2.5 - Stabilization Research

本报告是 research-only / shadow-only。现有 market_regime 保持正式 baseline，不接 BUY ranking、不接执行层。

## Candidate Metrics
| candidate | switch_count | median_duration | whipsaw | avg_detection_lag | missed_segment_ratio |
| --- | --- | --- | --- | --- | --- |
| RAW | 44 | 2 | 30 | 0 | 0 |
| CONFIRM_2D | 25 | 5 | 8 | 0.714286 | 0.222222 |
| CONFIRM_3D | 17 | 10.5 | 2 | 1.259259 | 0.4 |
| ASYMMETRIC_CONFIRM | 22 | 5 | 5 | 0.818182 | 0.266667 |

## Research Score
| candidate | candidate_research_score | whipsaw_reduction | median_duration_gain | switch_reduction | detection_lag_score | missed_segment_score | style_fit_preservation | style_fit_clarity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONFIRM_3D | 84.021697 | 0.933333 | 1 | 0.613636 | 0.748148 | 0.6 | 0.858904 | 1 |
| ASYMMETRIC_CONFIRM | 76.724889 | 0.833333 | 0.5 | 0.5 | 0.836364 | 0.733333 | 0.933095 | 1 |
| CONFIRM_2D | 74.312871 | 0.733333 | 0.5 | 0.431818 | 0.857143 | 0.777778 | 0.924072 | 1 |
| RAW | 50 | 0 | 0 | 0 | 1 | 1 | 1 | 1 |

## Decision
- selected_candidate: ASYMMETRIC_CONFIRM
- selected_reason: ASYMMETRIC_CONFIRM selected by fixed research score: switch 44 -> 22, median duration 2.0 -> 5.0, 3d whipsaw 30 -> 5, avg detection lag 0.818182, missed ratio 0.26666666666666666; style_fit_preserved=True.
- current_raw_regime: NEUTRAL
- current_selected_shadow_regime: NEUTRAL
- ready_for_style_regime_fit_research: True
- ready_for_preview: False
- ready_for_execution: False

## Safety
- research_only=true
- shadow_only=true
- ready_for_execution=false
- forward return is label only
- no broker API / no real order / no paper trade mutation