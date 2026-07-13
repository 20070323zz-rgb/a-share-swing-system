# Exposure Phase C Readiness Gate

## Scope

Phase C is future Exposure Prototype Development. It is not started by this batch.

This gate defines what may enter Phase C, what needs data first, and what must remain descriptive.

## Phase C Admission Criteria

An exposure may enter Phase C only if all conditions are satisfied:

1. Economic meaning is clear.
2. Measurement method is objective or explicitly proxied.
3. Calculation can be point-in-time.
4. Current data at least partially supports required fields.
5. Missing data does not create severe future information leakage.
6. Warm-up and minimum history are defined.
7. Missing-data handling is explicit.
8. Confidence-level policy is defined.
9. It can be maintained automatically.
10. It remains research-only and does not connect to ranking, score, preview, or execution.

## Readiness Matrix

| Exposure | Readiness | Current Support | PIT Status | Phase C Treatment | Reason |
| --- | --- | --- | --- | --- | --- |
| market_beta | READY_FOR_PHASE_C | SUPPORTED_NOW | PIT_SAFE_WITH_PROXY | Prototype calculation allowed. | Daily ETF returns and beta fields exist; benchmark registry would improve precision but A-share proxy is feasible. |
| realized_volatility | READY_FOR_PHASE_C | SUPPORTED_NOW | PIT_SAFE | Prototype calculation allowed. | Rolling volatility is directly measurable from ETF daily prices. |
| downside_drawdown_risk | READY_FOR_PHASE_C | SUPPORTED_NOW | PIT_SAFE | Prototype calculation allowed. | Drawdown/downside fields already exist and can be recomputed from historical prices. |
| trading_liquidity | READY_FOR_PHASE_C | SUPPORTED_NOW | PIT_SAFE | Prototype calculation allowed. | Amount/volume and liquidity summaries exist. |
| return_momentum | READY_FOR_PHASE_C | SUPPORTED_NOW | PIT_SAFE | Prototype calculation allowed. | Return windows and trend features can use only past prices. |
| dividend_intent | DESCRIPTIVE_ONLY_OR_DEFER | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY unless metadata effective dates are added | Metadata tag only. | Current support is mostly name/flag based and lacks dividend yield/index methodology. |
| size_segment | NEEDS_DATA_BEFORE_PHASE_C | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY for historical replay | Metadata tag only until benchmark/constituent data exists. | Current names imply size but do not provide objective constituent market-cap distribution. |
| commodity_resource_sensitivity | NEEDS_DATA_BEFORE_PHASE_C | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY or PIT_SAFE_WITH_PROXY only after benchmark series exists | Do not calculate commodity beta yet. | Needs commodity benchmark or resource-sector benchmark. |
| interest_rate_bond_sensitivity | NEEDS_DATA_BEFORE_PHASE_C | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY for precise rate exposure | Do not calculate precise rate exposure yet. | Needs duration, yield, credit spread, and rate benchmark data. |
| concentration_proxy | NEEDS_DATA_BEFORE_PHASE_C | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY for current tags | Weak proxy only; holdings-based measure deferred. | Needs holdings, constituent weights, sector weights, or index concentration. |
| value_factor | NEEDS_DATA_BEFORE_PHASE_C | NOT_SUPPORTED | NOT_PIT_SAFE | Defer. | Needs valuation/fundamental or value-index methodology data. |
| growth_factor | NEEDS_DATA_BEFORE_PHASE_C | PARTIALLY_SUPPORTED | NOT_PIT_SAFE for fundamentals | Defer quantitative growth. | Needs growth fundamentals or benchmark methodology. |
| sector_industry_tag | DESCRIPTIVE_ONLY_OR_DEFER | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY | Controlled metadata design only. | Industry names are not stable exposures without taxonomy/effective dates. |
| technology_innovation_tag | DESCRIPTIVE_ONLY_OR_DEFER | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY | Metadata/research tag only. | Theme definitions drift and are mostly inferred from names. |
| manufacturing_upgrade_tag | DESCRIPTIVE_ONLY_OR_DEFER | PARTIALLY_SUPPORTED | DESCRIPTIVE_ONLY | Metadata/research tag only. | Needs taxonomy, benchmark, and/or holdings support. |
| ai_digital_theme_tag | DESCRIPTIVE_ONLY_OR_DEFER | NOT_SUPPORTED | NOT_PIT_SAFE | Defer. | No controlled theme taxonomy or objective measurement support. |
| qdii_fx_cross_border | DESCRIPTIVE_ONLY_OR_DEFER | PARTIALLY_SUPPORTED | NOT_PIT_SAFE for strict cross-border decomposition | Separate research track. | Needs FX benchmark, foreign market benchmark, calendar, premium/discount governance. |

## READY_FOR_PHASE_C Set

Phase C prototype may include only:

```text
market_beta
realized_volatility
downside_drawdown_risk
trading_liquidity
return_momentum
```

These exposures are price/amount-derived, can be calculated with rolling windows, and can be made point-in-time using current ETF daily data.

## NEEDS_DATA_BEFORE_PHASE_C Set

These exposures need additional structured data or stronger metadata before calculation:

```text
size_segment
commodity_resource_sensitivity
interest_rate_bond_sensitivity
concentration_proxy
value_factor
growth_factor
```

Required data types:

```text
ETF Benchmark Index
Index Methodology
Fund Holdings
Constituent Weights
Constituent Market Cap
Valuation / Growth Fundamentals
Bond Duration / Yield / Credit Spread
Commodity Benchmark
```

## DESCRIPTIVE_ONLY_OR_DEFER Set

These should not enter calculation yet:

```text
dividend_intent as quantitative yield exposure
sector_industry_tag
technology_innovation_tag
manufacturing_upgrade_tag
ai_digital_theme_tag
qdii_fx_cross_border
```

They may appear in reports as metadata only if clearly labeled:

```text
DESCRIPTIVE_ONLY
NOT_PIT_SAFE if used historically without available-date tracking
LOW confidence if inferred from name/group
```

## Phase C Prototype Boundary

If Main approves Phase C, Phase C should be limited to a research-only prototype for the `READY_FOR_PHASE_C` set.

Forbidden in Phase C unless separately approved:

- BUY ranking integration.
- Score changes.
- Preview creation.
- Formal execution changes.
- Universe mutation.
- Regime or Style Mapping changes.
- Using descriptive-only fields as calculation inputs.

## Recommended Phase C Deliverable Shape

Future Phase C should produce prototype artifacts such as:

```text
reports/exposure_prototype_source_audit.md
reports/exposure_prototype_matrix.csv
reports/exposure_prototype_summary.md
reports/exposure_pit_validation.md
```

Every output should remain:

```text
research_only = true
execution_allowed = false
preview_research_status = NOT_STARTED unless Main explicitly approves otherwise
```

## Readiness Verdict

Exposure Framework Phase B creates sufficient design foundation for a narrow Phase C prototype, but not for full Style Framework 2.0 development.

```text
Exposure Framework Phase B = COMPLETE
Exposure Taxonomy = DESIGNED
Exposure Data Contract = DESIGNED
Exposure Point-in-Time Rules = DESIGNED
Exposure Framework Development = NOT_STARTED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```
