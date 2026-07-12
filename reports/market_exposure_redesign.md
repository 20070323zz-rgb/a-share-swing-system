# Market Exposure Redesign

## Batch Header

- Batch Name: Exposure Framework Phase E-A - Market Exposure Redesign
- Batch Type: Research
- Current Phase: Exposure Framework Phase E-A
- Current Batch: Market Exposure Redesign
- Objective: Redefine market exposure after Phase D found single-benchmark beta insufficient.
- Scope: Research design only; no code, exposure formula, strategy, ranking, preview, formal execution, or replay changes.

## 1. Context

Exposure Framework Phase D validated five Phase C prototype exposures. Four exposures were marked `READY_FOR_RESEARCH_OBSERVATION`; `market_beta` was marked `NEEDS_REFINEMENT`.

The issue is not that beta is mathematically invalid. The issue is that the current prototype uses a single 510300 proxy, which represents a broad large/core A-share benchmark. Universe V2 contains ETFs with materially different systematic drivers: broad large-cap, mid/small-cap, STAR/technology, sector/theme, dividend/low-volatility, and resource/cyclical exposures.

Academic and practitioner factor-model literature supports this diagnosis: market sensitivity is important, but one broad market factor is not enough to describe shared return variation across size, style, sector, and momentum dimensions. Fama and French identify market, size, and value-related common factors; Carhart extends fund-return attribution with momentum; MSCI Barra describes risk measurement through transparent factor exposure frameworks rather than a single index lens. Public index descriptions also show that CSI 300, CSI 500, CSI 1000, ChiNext, STAR 50, SSE 50, and dividend-style indices represent different segments of the China equity market.

## 2. Objective

This batch answers:

1. Market Exposure should be a vector of sensitivities to multiple market segments, not a single scalar beta.
2. Single benchmark beta is insufficient because ETF universes are heterogeneous.
3. A multi-benchmark framework is recommended.
4. Exposure Vector should preserve multiple loadings and confidence metadata.
5. Engineering Prototype is recommended only after Main approves a research-only implementation batch.

## 3. Scope

Allowed:

- Theory research.
- Framework design.
- Data requirement analysis.
- Repository-based data availability review.

Forbidden:

- Code changes.
- Exposure formula changes.
- Strategy, ranking, preview, formal execution, universe, or replay changes.

## 4. Inputs

- `reports/exposure_validation_summary.md`
- `reports/exposure_research_readiness.md`
- `reports/exposure_data_contract.md`
- `data/etf_daily/`
- Public references listed in References.

## 5. Method

The redesign uses three evidence sources:

1. Phase D repository evidence: 510300 beta was PIT-safe and stable but proxy-limited.
2. Financial modeling principle: systematic risk is multi-dimensional.
3. A-share ETF market structure: benchmark families represent different economic segments.

This report does not calculate new beta values.

## 6. Single Benchmark Limitation

## Broad ETF

For a CSI 300 or SSE 50-like ETF, 510300 can be a reasonable broad large/core proxy. But even here, it does not distinguish mega-cap concentration, financial/consumer weight, or state-owned/dividend tilt.

## Mid/Small-Cap ETF

Mid/small-cap ETFs can have different liquidity, volatility, retail participation, and earnings-cycle sensitivity. A 510300 beta may understate small-cap systematic exposure or misclassify small-cap rallies as idiosyncratic behavior.

## STAR ETF

STAR and semiconductor-related ETFs often have higher technology, duration, innovation, and sentiment exposure. They can move with growth/technology conditions even when 510300 is neutral.

## Industry ETF

Industry ETFs have sector-specific beta. A securities ETF, utilities ETF, chip ETF, or machinery ETF can be strongly systematic, but its systematic driver may not be captured by the broad-market proxy.

## Dividend ETF

Dividend and low-volatility ETFs can be equity-market sensitive while also defensive, yield-oriented, and value-biased. A single broad beta misses this defensive structure.

## Cyclical Resource ETF

Resource and commodity-linked equity ETFs may respond to commodity cycles, inflation expectations, global demand, and policy themes. 510300 beta can confuse commodity-cycle sensitivity with weak or unstable market exposure.

## Phase D Evidence

Phase D found 510300 correlations across V2 ETFs were dispersed:

```text
60d correlation: min -0.140, median 0.609, max 0.933
120d correlation: min 0.159, median 0.631, max 0.930
```

This dispersion is the key project-specific reason to redesign `market_beta`.

## 7. Proposed Definition

Market Exposure should mean:

```text
The ETF's point-in-time sensitivity profile to multiple broad market segments that represent size, board, core growth, defensive/dividend, and major systematic equity buckets.
```

It should not mean:

```text
One beta against one default broad benchmark.
```

The first redesigned unit should be named `market_exposure_vector`, not a replacement scalar score.

## 8. Exposure Vector Design

Recommended representation:

```text
calculation_date
universe_version
symbol
benchmark_id
benchmark_name
benchmark_family
lookback_window
beta
correlation
r_squared
tracking_overlap_status
point_in_time_status
confidence_level
missing_data_flag
research_only=true
execution_allowed=false
```

An ETF should be allowed to have multiple high exposures. For example:

- A STAR semiconductor ETF may have high STAR/technology beta and high broad-market beta.
- A dividend ETF may have moderate broad beta and high dividend/defensive beta.
- A resource ETF may have broad equity beta plus resource/cyclical beta.

Multiple high exposures are information, not an error.

## 9. Standardization and Normalization

Recommended:

- Keep raw beta and correlation as primary research values.
- Add z-score or percentile only as a secondary cross-sectional view.
- Do not force loadings to sum to 1.
- Do not normalize away absolute market sensitivity.
- Use benchmark-family tags to avoid comparing unrelated beta values too mechanically.

Rationale:

```text
Beta is a sensitivity, not an allocation weight.
An ETF can be simultaneously sensitive to several systematic drivers.
Forced normalization would hide total risk sensitivity.
```

## 10. Engineering Readiness

Verdict:

```text
READY_FOR_ENGINEERING_PROTOTYPE_DESIGN
```

The project is ready for a research-only engineering prototype design because:

- The problem is well-defined.
- Candidate benchmark families are identified.
- PIT rules are inherited from Phase B/C.
- Several local ETF proxy series already exist in the unified ETF database.

However, it is not ready for Preview, Ranking, Score, Strategy, or Formal Execution.

Engineering prototype prerequisites:

- Main must approve a separate Engineering Batch.
- Benchmark registry must be versioned.
- The prototype must remain research-only.
- It must output vector rows, not a final score.
- It must preserve missing/confidence flags.

## 11. Deliverables

Generated by this batch:

- `reports/market_exposure_redesign.md`
- `reports/multi_benchmark_framework.md`
- `reports/market_exposure_data_contract.md`

## 12. Validation

This batch:

- Did not modify code.
- Did not modify exposure formulas.
- Did not modify strategy, ranking, preview, formal execution, universe, or replay.
- Did not calculate new exposure values.

## 13. State Transition

```text
Exposure Framework Phase E-A = COMPLETE
Market Exposure Redesign = COMPLETE
Engineering Prototype = NOT_STARTED
```

## 14. References

- Fama and French, "Common risk factors in the returns on stocks and bonds": https://www.sciencedirect.com/science/article/pii/0304405X93900235
- Kenneth French Data Library factor descriptions: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html
- Carhart, "On Persistence in Mutual Fund Performance": https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1997.tb03808.x
- MSCI Barra equity factor models overview: https://www.msci.com/data-and-analytics/factor-investing/equity-factor-models
- SSE index methodology page: https://english.sse.com.cn/markets/indices/index/
- CSOP CSI 500 ETF index description: https://www.csopasset.com/en/products/csi-500-etf
- HKEX ChiNext Market Overview: https://www.hkex.com.hk/Mutual-Market/Stock-Connect/Getting-Started/Information-Booklet-and-FAQ/ChiNext-Market-Overview?sc_lang=en
