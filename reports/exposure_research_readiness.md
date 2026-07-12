# Exposure Research Readiness

## Overall Gate

- Exposure Research Readiness: PARTIAL_READY
- Phase D recommends research observation only. No Preview, Ranking, Score, Strategy, or Formal Execution integration is authorized.

## Readiness Matrix

| exposure_name | readiness_verdict | stability | differentiation | pit_safety | redundancy_note | reason |
| --- | --- | --- | --- | --- | --- | --- |
| market_beta | NEEDS_REFINEMENT | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE_WITH_PROXY | risk-cluster overlap | PIT-safe and stable, but 510300 is only a broad proxy; small-cap/STAR/theme ETF proxy bias and high redundancy with volatility require multi-benchmark review. |
| realized_volatility | READY_FOR_RESEARCH_OBSERVATION | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | risk-cluster overlap | PIT-safe, stable across 20d/60d, interpretable, and differentiates high-beta themes from defensive/core ETFs. |
| downside_drawdown_risk | READY_FOR_RESEARCH_OBSERVATION | PARTIALLY_STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | risk-cluster overlap | PIT-safe and interpretable as tail/downside risk; max drawdown is only partially stable but adds information beyond simple volatility. |
| trading_liquidity | READY_FOR_RESEARCH_OBSERVATION | STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | mostly independent | PIT-safe, very stable across 20d/60d, highly interpretable, and not redundant with the risk cluster. |
| return_momentum | READY_FOR_RESEARCH_OBSERVATION | PARTIALLY_STABLE | STRONG_DIFFERENTIATION | PIT_SAFE | moderate independence | PIT-safe and differentiating; horizon dependence is expected for a dynamic exposure, so observe with separate 20d/60d/120d windows. |

## Ready Set

```text
realized_volatility
downside_drawdown_risk
trading_liquidity
return_momentum
```

## Needs Refinement

```text
market_beta
```

## Market Beta Refinement Requirement

`market_beta` should remain provisional until a future batch tests multi-benchmark beta. Candidate benchmark families should include large-cap/core, small-cap/mid-cap, STAR/technology, resource/commodity, and defensive/dividend benchmarks. This report does not change the formula.

## Next Research Gate

A next phase may validate these exposures over time or across universes, but must remain research-only unless Main explicitly approves a separate preview governance gate.
