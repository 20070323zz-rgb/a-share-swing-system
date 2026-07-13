# Multi-Benchmark Framework

## Scope

This report designs a research-only benchmark basket for future `market_exposure_vector` work. It does not select a final production list, does not calculate beta, and does not authorize strategy or execution use.

## Why Multi-Benchmark

Single benchmark beta answers only:

```text
How sensitive is this ETF to one chosen market proxy?
```

A multi-benchmark framework asks:

```text
Which market segments explain this ETF's systematic behavior, and with what strength and confidence?
```

This is more appropriate for an ETF universe that includes broad index, size, board, sector, dividend, and cyclical/resource products.

## Candidate Benchmark Basket

| benchmark_family | candidate_index_or_proxy | role | expected usefulness | current local proxy evidence | status |
| --- | --- | --- | --- | --- | --- |
| large_core | CSI 300 / 510300 | Broad A-share large/mid core market proxy. | Baseline equity market exposure. | `data/etf_daily/sh_510300.csv` exists with long history. | CORE_CANDIDATE |
| large_blue_chip | SSE 50 / 510050 | Mega-cap, financial/consumer/state-owned tilt proxy. | Distinguish mega-cap defensive/core exposure from broader CSI 300. | `data/etf_daily/sh_510050.csv` exists. | CANDIDATE |
| mid_cap | CSI 500 / 510500 | Mid-cap A-share segment proxy. | Captures non-CSI300 size exposure. | `data/etf_daily/sh_510500.csv` exists but local history is shorter. | CANDIDATE_WITH_HISTORY_RISK |
| small_cap | CSI 1000 / 512100 or equivalent | Small-cap segment proxy. | Captures small-cap/high-dispersion market behavior. | `data/etf_daily/sh_512100.csv` exists but local history is shorter. | CANDIDATE_WITH_HISTORY_RISK |
| growth_board | ChiNext / 159915 | Growth, innovation, Shenzhen high-growth board proxy. | Captures growth-board beta missed by 510300. | `data/etf_daily/sz_159915.csv` exists with long history. | CORE_CANDIDATE |
| star_technology | STAR 50 / 588000 | STAR board and hard-technology proxy. | Captures STAR/semiconductor-like systematic movement. | `data/etf_daily/sh_588000.csv` exists. | CANDIDATE |
| dividend_defensive | Dividend / 510880 or dividend-low-vol proxy | Yield/value/defensive equity segment proxy. | Captures defensive/dividend market exposure. | `data/etf_daily/sh_510880.csv` and `data/etf_daily/sz_159547.csv` exist with varying history. | CANDIDATE_WITH_HISTORY_RISK |
| resource_cyclical | Resource/commodity equity proxy | Cyclical resource equity market segment. | Useful for resource and commodity-cyclical ETFs. | Needs explicit benchmark selection from existing universe. | NEEDS_SELECTION |
| sector_family | Sector benchmark proxies | Industry-specific systematic movement. | Useful for securities, banks, utilities, chips, machinery. | Some sector ETFs exist, but basket needs governance. | DEFER_TO_SECTOR_FRAMEWORK |

## Recommended Initial Engineering Basket

For a narrow research-only prototype, the first basket should be:

```text
510300 - large/core broad A-share
510050 - mega-cap blue-chip
510500 - mid-cap
512100 - small-cap proxy if accepted after history check
159915 - ChiNext/growth board
588000 - STAR 50/hard technology
510880 or 159547 - dividend/defensive
```

This list is not final. It is a candidate engineering basket for research-only prototype design.

## Benchmark Roles

## CSI 300 / 510300

Use as the broad default A-share equity anchor. It remains necessary, but should no longer be the only market benchmark.

## SSE 50 / 510050

Use to identify mega-cap/blue-chip concentration. It can help separate broad-market beta from large financial/consumer/state-linked exposure.

## CSI 500 / 510500

Use to identify mid-cap exposure. This is important because V2 includes ETFs whose behavior can diverge from large-cap CSI 300.

## CSI 1000 / 512100

Use to identify small-cap exposure. It should be included only if local history and liquidity are adequate for the selected lookback windows.

## ChiNext / 159915

Use for growth-board and innovation-driven exposure. This is important for high-growth and technology-related ETFs.

## STAR 50 / 588000

Use for hard-technology and STAR-board exposure. It should help explain semiconductor and STAR-style ETF behavior that broad 510300 beta cannot.

## Dividend / 510880 or 159547

Use for defensive/dividend and low-volatility market exposure. This prevents dividend ETFs from being described only as low broad beta.

## Resource/Cyclical Proxy

Potentially useful, but not ready for the first basket without a separate benchmark-selection rule. Resource exposure may overlap commodity/resource sensitivity, so the benchmark must be governed carefully.

## Sector Proxies

Sector proxies are valuable but should not be collapsed into generic Market Exposure too quickly. They may become a second layer:

```text
market_exposure_vector = broad/size/board/dividend benchmark loadings
sector_exposure_vector = sector-specific systematic benchmark loadings
```

## Vector Interpretation

Do:

- Interpret beta and correlation together.
- Keep multiple benchmark loadings per ETF.
- Preserve benchmark family metadata.
- Mark history/confidence per benchmark.

Do not:

- Pick the highest beta as the ETF's only market exposure.
- Force benchmark weights to sum to 1.
- Treat a high beta to one benchmark as a trading signal.
- Mix QDII, commodity, bond, and A-share equity benchmarks without separate taxonomy.

## Prototype Output Shape

Recommended output row grain:

```text
one ETF x one benchmark x one lookback window x one calculation date
```

Recommended windows:

```text
60d
120d
optional 240d only when history supports it
```

Recommended metrics:

```text
beta
correlation
r_squared
observations
confidence_level
point_in_time_status
missing_data_flag
```

## Framework Verdict

```text
Multi-Benchmark Framework = RECOMMENDED
Single Benchmark Framework = RETAIN_AS_BASELINE_ONLY
Final Benchmark Basket = NOT_FINALIZED
Engineering Prototype = NOT_STARTED
```
