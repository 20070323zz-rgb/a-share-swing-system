# Benchmark Redundancy Analysis

## Verdict

- Benchmark Redundancy Verdict: LOCALIZED_HIGH_REDUNDANCY
- Available pair-window rows: 30
- HIGH redundancy rows (absolute correlation >= 0.90): 3
- HIGH redundancy share: 10.0%
- High correlation is evaluated as basket redundancy, not as evidence that two indices are economically identical.

## 60d Correlation Matrix

| benchmark | 510300 | 510500 | 512100 | 159915 | 588000 | 510880 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 510300 | 1.000 | 0.886 | 0.788 | 0.907 | 0.735 | 0.010 |
| 510500 | 0.886 | 1.000 | 0.954 | 0.881 | 0.805 | -0.156 |
| 512100 | 0.788 | 0.954 | 1.000 | 0.854 | 0.726 | -0.214 |
| 159915 | 0.907 | 0.881 | 0.854 | 1.000 | 0.736 | -0.228 |
| 588000 | 0.735 | 0.805 | 0.726 | 0.736 | 1.000 | -0.294 |
| 510880 | 0.010 | -0.156 | -0.214 | -0.228 | -0.294 | 1.000 |

## 120d Correlation Matrix

| benchmark | 510300 | 510500 | 512100 | 159915 | 588000 | 510880 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 510300 | 1.000 | 0.816 | 0.789 | 0.857 | 0.712 | 0.145 |
| 510500 | 0.816 | 1.000 | 0.961 | 0.815 | 0.793 | 0.013 |
| 512100 | 0.789 | 0.961 | 1.000 | 0.816 | 0.757 | -0.007 |
| 159915 | 0.857 | 0.815 | 0.816 | 1.000 | 0.764 | -0.116 |
| 588000 | 0.712 | 0.793 | 0.757 | 0.764 | 1.000 | -0.236 |
| 510880 | 0.145 | 0.013 | -0.007 | -0.116 | -0.236 | 1.000 |

## High and Medium Redundancy Pairs

| window | benchmark A | family A | benchmark B | family B | correlation | level |
| ---: | --- | --- | --- | --- | ---: | --- |
| 60 | 510500 | mid_cap | 512100 | small_cap | 0.954 | HIGH |
| 60 | 510300 | core_market | 159915 | growth | 0.907 | HIGH |
| 60 | 510300 | core_market | 510500 | mid_cap | 0.886 | MEDIUM |
| 60 | 510500 | mid_cap | 159915 | growth | 0.881 | MEDIUM |
| 60 | 512100 | small_cap | 159915 | growth | 0.854 | MEDIUM |
| 60 | 510500 | mid_cap | 588000 | technology | 0.805 | MEDIUM |
| 60 | 510300 | core_market | 512100 | small_cap | 0.788 | MEDIUM |
| 120 | 510500 | mid_cap | 512100 | small_cap | 0.961 | HIGH |
| 120 | 510300 | core_market | 159915 | growth | 0.857 | MEDIUM |
| 120 | 510300 | core_market | 510500 | mid_cap | 0.816 | MEDIUM |
| 120 | 512100 | small_cap | 159915 | growth | 0.816 | MEDIUM |
| 120 | 510500 | mid_cap | 159915 | growth | 0.815 | MEDIUM |
| 120 | 510500 | mid_cap | 588000 | technology | 0.793 | MEDIUM |
| 120 | 510300 | core_market | 512100 | small_cap | 0.789 | MEDIUM |
| 120 | 159915 | growth | 588000 | technology | 0.764 | MEDIUM |
| 120 | 512100 | small_cap | 588000 | technology | 0.757 | MEDIUM |

## Interpretation

- A redundant pair may still be retained when the benchmarks represent distinct size or board definitions and create different ETF-level loadings.
- If redundancy is severe across both windows, the next validation phase should test whether one benchmark can be removed without losing ETF differentiation.
- This report does not change the basket automatically.

## Boundary

- Calculation date: 2026-07-08
- Research only: true
- Predictive claim: false
- Strategy / Ranking / Score / Preview / Formal Execution: unchanged
