# Market Exposure Data Contract

## Scope

This contract defines the future research-only data requirements for `market_exposure_vector`. It supersedes the single-benchmark interpretation of `market_beta`, but does not change any existing formula or code.

## Exposure Name

```text
market_exposure_vector
```

## Exposure Category

```text
Market / Size / Board Exposure
```

## Economic Meaning

Sensitivity profile to multiple A-share market segments, including broad large/core, mega-cap, mid-cap, small-cap, growth board, STAR/hard-technology, and defensive/dividend segments.

## Required Fields

ETF fields:

```text
symbol
name
calculation_date
universe_version
etf_daily_close
etf_daily_return
```

Benchmark fields:

```text
benchmark_id
benchmark_name
benchmark_family
benchmark_proxy_symbol
benchmark_daily_close
benchmark_daily_return
benchmark_effective_date
benchmark_available_date
benchmark_source_data
```

Calculation fields:

```text
lookback_window
window_start_date
window_end_date
observations
beta
correlation
r_squared
point_in_time_status
confidence_level
missing_data_flag
missing_data_reason
research_only
execution_allowed
```

## Optional Fields

```text
benchmark_index_code
benchmark_index_provider
benchmark_methodology_url
tracking_etf_liquidity
tracking_etf_history_start
benchmark_family_priority
benchmark_deprecation_date
replacement_benchmark_id
```

## Benchmark Requirements

Each benchmark must have:

- A stable benchmark family.
- A versioned registry entry.
- Clear proxy symbol or official index series.
- Daily price series available from the unified project data source or approved future benchmark source.
- Known effective date.
- Known available date for strict replay.
- Minimum observations for each approved lookback window.

If a benchmark proxy is an ETF rather than an official index series, the contract must label it as `ETF_PROXY`.

## Point-in-Time Rules

The future calculation must obey:

```text
Only data known at or before calculation_date may be used.
ETF and benchmark returns must be <= T.
Benchmark registry entries must have effective_date <= T.
If available_date is unknown, the benchmark may be used for current research but must be marked PIT_SAFE_WITH_PROXY or DESCRIPTIVE_ONLY for historical replay.
No future benchmark replacement, future component change, future return, or future classification can define current exposure.
```

## Minimum History Requirement

```text
60d beta: at least 60 paired ETF/benchmark return observations.
120d beta: at least 120 paired observations.
240d beta: optional; at least 240 paired observations.
```

If observations are below threshold:

```text
missing_data_flag = true
missing_data_reason = INSUFFICIENT_PAIRED_HISTORY
confidence_level = LOW or NOT_AVAILABLE
```

## Update Frequency

Recommended:

```text
Daily after ETF and benchmark daily data refresh.
Benchmark registry review monthly or whenever a benchmark is added, replaced, or deprecated.
```

## Missing Data Policy

| condition | policy |
| --- | --- |
| ETF data missing | Do not calculate that ETF/benchmark/window row. |
| Benchmark data missing | Mark benchmark row missing; do not substitute silently. |
| Insufficient paired history | Mark missing or LOW confidence depending on prototype design. |
| Benchmark metadata missing available date | Mark `PIT_SAFE_WITH_PROXY` or `NOT_PIT_SAFE_FOR_REPLAY`. |
| Proxy ETF exists but history is short | Allow current research row with confidence cap; block strict long-window replay row. |

## Confidence Policy

| confidence | requirement |
| --- | --- |
| HIGH | Benchmark identity versioned, paired history complete, correlation/r_squared calculable, PIT metadata complete. |
| MEDIUM | Paired history complete, but benchmark is ETF proxy or available-date metadata is incomplete. |
| LOW | Short history, weak correlation, missing benchmark metadata, or proxy uncertainty. |
| NOT_AVAILABLE | Required data missing or benchmark not valid for the calculation date. |

## Current Database Support

Local proxy availability review:

| benchmark_family | local proxy | current support |
| --- | --- | --- |
| large_core | `sh_510300.csv` | SUPPORTED_NOW |
| large_blue_chip | `sh_510050.csv` | PARTIALLY_SUPPORTED |
| mid_cap | `sh_510500.csv` | PARTIALLY_SUPPORTED; local history risk |
| small_cap | `sh_512100.csv` | PARTIALLY_SUPPORTED; local history risk |
| growth_board | `sz_159915.csv` | SUPPORTED_NOW |
| star_technology | `sh_588000.csv` | PARTIALLY_SUPPORTED |
| dividend_defensive | `sh_510880.csv` / `sz_159547.csv` | PARTIALLY_SUPPORTED; proxy choice unresolved |
| resource_cyclical | not selected | NEEDS_BENCHMARK_SELECTION |

## Engineering Prototype Readiness

```text
Engineering Prototype Readiness = READY_FOR_RESEARCH_ONLY_PROTOTYPE_DESIGN
Engineering Prototype = NOT_STARTED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Reasons:

- The contract is defined.
- Candidate benchmark families are identified.
- Several proxy series exist in the unified ETF database.
- The remaining work is implementation design, not theory discovery.

Blocking conditions for any non-research use:

- No final benchmark basket.
- No multi-benchmark validation.
- No evidence that vector exposure improves research observation.
- No Main approval for Preview or Formal Execution.

## Non-Authorization Statement

This contract does not authorize:

- BUY ranking changes.
- Score changes.
- Strategy changes.
- Preview creation.
- Formal execution.
- Replay launch.
- Exposure formula replacement in current prototype.
