# Exposure Validation Summary

## Scope

- Batch: Exposure Framework Phase D - Exposure Validation
- Inputs: Phase C research-only exposure prototype outputs.
- No exposure formula was modified.
- No replay, preview, ranking, score, strategy, or formal execution was started.

## Overall Verdict

- Exposure Validation: COMPLETE
- Exposure Research Readiness: PARTIAL_READY
- Universe Version: universe_v2_qualified_research
- Calculation Date: 2026-07-08
- ETF Count: 16
- Value Rows: 240
- Missing Rows: 0

## Part A - Coverage Validation

| exposure_name | etf_covered | value_rows | missing_rows | confidence_counts | pit_status_counts |
| --- | --- | --- | --- | --- | --- |
| market_beta | 16 | 32 | 0 | HIGH=16, MEDIUM=16 | PIT_SAFE_WITH_PROXY=32 |
| realized_volatility | 16 | 32 | 0 | HIGH=32 | PIT_SAFE=32 |
| downside_drawdown_risk | 16 | 64 | 0 | HIGH=64 | PIT_SAFE=64 |
| trading_liquidity | 16 | 64 | 0 | HIGH=64 | PIT_SAFE=64 |
| return_momentum | 16 | 48 | 0 | HIGH=48 | PIT_SAFE=48 |

Coverage verdict: PASS. All five approved exposures cover all 16 ETFs. Missing rows are zero. `market_beta` is correctly marked `PIT_SAFE_WITH_PROXY`; the other four exposure families are marked `PIT_SAFE`.

## Part B - Window Stability Summary

| exposure_name | stability_verdict |
| --- | --- |
| market_beta | STABLE |
| realized_volatility | STABLE |
| downside_drawdown_risk | PARTIALLY_STABLE |
| trading_liquidity | STABLE |
| return_momentum | PARTIALLY_STABLE |

## Part C - Cross-ETF Differentiation Summary

| exposure_name | primary_metric | min | median | max | iqr | cv | extreme_z_gt_3 | top_symbol | top_name | bottom_symbol | bottom_name | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_beta | beta_120d | 0.120 | 1.019 | 1.755 | 1.023 | 0.508 | 0 | 588200 | 科创芯片ETF | 159547 | 红利低波ETF华夏 | STRONG_DIFFERENTIATION |
| realized_volatility | annualized_volatility_60d | 0.135 | 0.303 | 1.455 | 0.242 | 0.773 | 1 | 159667 | 工业母机ETF国泰 | 159547 | 红利低波ETF华夏 | STRONG_DIFFERENTIATION |
| downside_drawdown_risk | max_drawdown_120d | -0.681 | -0.195 | -0.076 | 0.109 | 0.693 | 0 | 159593 | 中证A50ETF | 159667 | 工业母机ETF国泰 | STRONG_DIFFERENTIATION |
| trading_liquidity | avg_amount_60d | 52260532.033 | 171844169.031 | 5276323342.933 | 428130184.748 | 1.742 | 0 | 588200 | 科创芯片ETF | 515630 | 保险证券 | STRONG_DIFFERENTIATION |
| return_momentum | past_return_60d | -0.565 | 0.006 | 1.021 | 0.460 | 2.948 | 0 | 159516 | 半导体设备ETF国泰 | 159667 | 工业母机ETF国泰 | STRONG_DIFFERENTIATION |

## Part D - Redundancy Summary

| pair | spearman_corr | redundancy_level |
| --- | --- | --- |
| market_beta / realized_volatility | 0.874 | HIGH |
| market_beta / downside_drawdown_risk | 0.232 | LOW |
| market_beta / trading_liquidity | 0.409 | LOW |
| market_beta / return_momentum | 0.594 | LOW |
| realized_volatility / downside_drawdown_risk | 0.559 | LOW |
| realized_volatility / trading_liquidity | 0.406 | LOW |
| realized_volatility / return_momentum | 0.385 | LOW |
| downside_drawdown_risk / trading_liquidity | -0.038 | LOW |
| downside_drawdown_risk / return_momentum | -0.294 | LOW |
| trading_liquidity / return_momentum | 0.379 | LOW |

## Part E - Market Beta Proxy Review

510300 is usable as a provisional A-share broad-market proxy, but not sufficient as a final market exposure for this V2 universe. The V2 universe contains small-cap, STAR, semiconductor, equipment, resource, utilities, and sector ETFs. Several of these can have weak or unstable correlation to 510300, so future validation should introduce multi-benchmark beta.

| lookback_window | min | median | max | mean |
| --- | --- | --- | --- | --- |
| 60 | -0.140 | 0.609 | 0.933 | 0.554 |
| 120 | 0.159 | 0.631 | 0.930 | 0.541 |

## Part F - Research Readiness Gate

| exposure_name | readiness_verdict | stability | differentiation | pit_safety | redundancy_note | reason |
| --- | --- | --- | --- | --- | --- | --- |
| market_beta | NEEDS_REFINEMENT | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE_WITH_PROXY | risk-cluster overlap | PIT-safe and stable, but 510300 is only a broad proxy; small-cap/STAR/theme ETF proxy bias and high redundancy with volatility require multi-benchmark review. |
| realized_volatility | READY_FOR_RESEARCH_OBSERVATION | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | risk-cluster overlap | PIT-safe, stable across 20d/60d, interpretable, and differentiates high-beta themes from defensive/core ETFs. |
| downside_drawdown_risk | READY_FOR_RESEARCH_OBSERVATION | PARTIALLY_STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | risk-cluster overlap | PIT-safe and interpretable as tail/downside risk; max drawdown is only partially stable but adds information beyond simple volatility. |
| trading_liquidity | READY_FOR_RESEARCH_OBSERVATION | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | mostly independent | PIT-safe, very stable across 20d/60d, highly interpretable, and not redundant with the risk cluster. |
| return_momentum | READY_FOR_RESEARCH_OBSERVATION | PARTIALLY_STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | moderate independence | PIT-safe and differentiating; horizon dependence is expected for a dynamic exposure, so observe with separate 20d/60d/120d windows. |

## Boundary

- Preview Research: NOT_STARTED
- Formal Execution: BLOCKED
- BUY Ranking / Score / Strategy: unchanged
- Universe V1/V2: unchanged
- Formula changes: none
