# Style Fit Robustness Source Audit

- stable_regime_source: data/market_regime_stabilization_replay.csv candidate_d_regime from Phase 2.5 ASYMMETRIC_CONFIRM replay
- selected_regime_candidate: ASYMMETRIC_CONFIRM
- style_profile_source: reports/etf_risk_profile.csv style_profile
- signal_source: ranking_model_v2_backtest.build_daily_rows + rank_rows(top10_diversified_filter_v2), top 30, matching Phase 3 signal interaction
- benchmark_label_join: same T-date join; point_in_time_safe_for_evaluation
- replay range: 2025-05-30 to 2026-07-06
- etf_count: 39
- style_count: 11
- regime_count: 3
- phase3_sample_unit: ETF-day pooling for style matrix; ranked ETF-day pooling for signal interaction
- overlapping_forward_windows_present: True
- cross_sectional_dependence_possible: True
- regime_segment_dependence_possible: True
- future_leakage_found: False
- blocking_conflict_found: False