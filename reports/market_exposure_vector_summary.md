# Market Exposure Vector Summary

## Status

- Phase: Exposure Framework Phase E-B - Multi-Benchmark Market Exposure Prototype
- Multi-Benchmark Market Exposure Prototype: COMPLETE
- Market Exposure Vector: RESEARCH_ONLY
- Universe Version: universe_v2_qualified_research
- Calculation Date: 2026-07-08
- ETF Count: 16
- Benchmark Basket Version: market_benchmark_basket_v1
- Available Benchmarks: 6/6
- Vector Rows: 192
- Missing Rows: 0
- Preview Research: NOT_STARTED
- Formal Execution: BLOCKED

## Benchmark Basket Availability

| benchmark_code | family | status | data_start | data_end | return_observations | 60d | 120d |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| 159915 | growth | AVAILABLE | 2022-01-04 | 2026-07-08 | 1090 | True | True |
| 510300 | core_market | AVAILABLE | 2022-01-04 | 2026-07-08 | 1090 | True | True |
| 510500 | mid_cap | AVAILABLE | 2026-01-05 | 2026-07-08 | 121 | True | True |
| 510880 | defensive | AVAILABLE | 2026-01-05 | 2026-07-08 | 121 | True | True |
| 512100 | small_cap | AVAILABLE | 2026-01-05 | 2026-07-08 | 121 | True | True |
| 588000 | technology | AVAILABLE | 2025-03-03 | 2026-07-08 | 328 | True | True |

## Coverage Validation

- Expected grain rows: 192
- Actual rows: 192
- ETF coverage: 16
- Benchmark coverage: 6
- Lookback windows: 60d, 120d
- Missing rows: 0

## Single 510300 vs Multi-Benchmark

- Explanatory verdict: ADDS_EXPLANATORY_DIMENSION
- Comparison rows with non-core R-squared improvement >= 0.05: 20/32
- 120d rows with non-core R-squared improvement >= 0.05: 10/16
- Interpretation: the comparison measures contemporaneous return explanation only; it does not test or claim return prediction.

## 60d vs 120d Window Comparison

- Dominant benchmark consistency: 15/16 ETFs
- Beta rank stability by benchmark:

| benchmark | 60d vs 120d beta rank correlation |
| --- | ---: |
| 159915 | 0.985 |
| 510300 | 0.947 |
| 510500 | 0.976 |
| 510880 | 0.762 |
| 512100 | 0.965 |
| 588000 | 0.988 |

Window differences are retained as research information. The prototype does not average or overwrite 60d and 120d vectors.

## 120d ETF Differentiation

- Differentiation verdict: STRONG_DIFFERENTIATION
- Distinct dominant benchmark families: 6

| ETF | name | 510300 R2 | best benchmark | best family | best R2 | fit quality | non-core delta | added dimension |
| --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |
| 159516 | 半导体设备ETF国泰 | 0.037 | 588000 | technology | 0.049 | WEAK | 0.012 | False |
| 159531 | 中证2000ETF南方 | 0.426 | 512100 | small_cap | 0.868 | STRONG | 0.442 | True |
| 159547 | 红利低波ETF华夏 | 0.025 | 510880 | defensive | 0.480 | MODERATE | 0.455 | True |
| 159593 | 中证A50ETF | 0.864 | 510300 | core_market | 0.864 | STRONG | -0.234 | False |
| 159608 | 稀有金属ETF广发 | 0.423 | 510500 | mid_cap | 0.574 | MODERATE | 0.152 | True |
| 159638 | 高端装备ETF嘉实 | 0.221 | 512100 | small_cap | 0.544 | MODERATE | 0.322 | True |
| 159667 | 工业母机ETF国泰 | 0.090 | 159915 | growth | 0.159 | WEAK | 0.069 | True |
| 159732 | 消费电子ETF华夏 | 0.573 | 159915 | growth | 0.747 | STRONG | 0.173 | True |
| 510050 | 上证50ETF | 0.753 | 510300 | core_market | 0.753 | STRONG | -0.304 | False |
| 515260 | 电子ETF | 0.580 | 588000 | technology | 0.861 | STRONG | 0.281 | True |
| 515630 | 保险证券 | 0.375 | 510300 | core_market | 0.375 | MODERATE | -0.194 | False |
| 561360 | 石油ETF | 0.042 | 510880 | defensive | 0.306 | MODERATE | 0.264 | True |
| 561560 | 电力ETF | 0.154 | 510880 | defensive | 0.171 | WEAK | 0.017 | False |
| 562550 | 绿电ETF | 0.122 | 510880 | defensive | 0.168 | WEAK | 0.045 | False |
| 588200 | 科创芯片ETF | 0.441 | 588000 | technology | 0.959 | STRONG | 0.518 | True |
| 588220 | 科创100ETF基金 | 0.475 | 588000 | technology | 0.786 | STRONG | 0.311 | True |

## Confidence and PIT

| confidence | rows |
| --- | ---: |
| LOW | 56 |
| MEDIUM | 136 |

- All calculated rows are `PIT_SAFE_WITH_PROXY`.
- Rolling windows use trailing paired returns ending no later than calculation date.
- Beta values are raw sensitivities and are not normalized to sum to 1.

## Research Interpretation

The prototype adds explanatory dimensions when an ETF is more closely aligned with a non-core market segment than with 510300. The vector should be retained as a research artifact because it preserves broad, size, growth, technology, and defensive sensitivities without compressing them into one scalar.

Important limits:

- A highest R-squared benchmark is a relative statistical fit, not an economic classification.
- Resource/cyclical ETF 561360 lacks a dedicated resource benchmark in basket V1; its defensive benchmark fit must not be interpreted as a defensive label.
- ETF 159516 has weak maximum 120d R-squared, showing that basket V1 does not adequately explain every sector/thematic ETF.
- 510500 and 512100 are highly correlated in both windows; future validation should test whether their ETF-level differentiation justifies retaining both.

## Output Files

- Vector values: `data/research/exposure_prototype/market_exposure_vector_values.csv`
- Missing rows: `data/research/exposure_prototype/market_exposure_vector_missing.csv`
- Benchmark coverage: `data/research/exposure_prototype/market_exposure_vector_benchmark_coverage.csv`
- Benchmark redundancy data: `data/research/exposure_prototype/market_exposure_vector_benchmark_redundancy.csv`
- Single vs multi comparison: `data/research/exposure_prototype/market_exposure_vector_single_vs_multi.csv`
- Manifest: `data/research/exposure_prototype/market_exposure_vector_manifest.json`

## Boundary

- Research only: true
- Predictive claim: false
- Replay started: false
- Ranking changed: false
- Score changed: false
- Strategy changed: false
- Preview created: false
- Formal execution changed: false
- Paper execution affected: false
