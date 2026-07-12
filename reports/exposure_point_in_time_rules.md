# Exposure Point-in-Time Rules

## Scope

This document defines point-in-time rules for the future Exposure Framework. It is a governance and data-contract artifact, not a model implementation.

No replay is started here. No exposure scores are calculated.

## Core Rule

For any calculation date `T`, an exposure may use only data that was known or knowable at `T`.

```text
Allowed: data with data_available_date <= T
Forbidden: data with data_available_date > T
Forbidden: current static metadata backfilled into historical T without effective-date and available-date tracking
```

## Required Date Fields

Every non-price field used in strict historical replay should distinguish:

| Field | Meaning | Required For |
| --- | --- | --- |
| event_date | Date the underlying fact occurred or became economically effective. | holdings date, index rebalance date, benchmark change, fund size date. |
| data_as_of_date | Date the data describes. | holdings report date, AUM date, duration date, index constituent date. |
| data_available_date | Date the project could have known the data. | all metadata/holdings/fundamental fields used in replay. |
| ingestion_date | Date the project stored the data locally. | auditability and reproducibility. |
| calculation_date | Date exposure is calculated. | all exposure outputs. |

If a field lacks reliable `data_available_date`, it may not be used for strict replay calculation. It must be marked `DESCRIPTIVE_ONLY` or `NOT_PIT_SAFE`.

## Data-Type Rules

### ETF Daily Price / Volume / Amount

Allowed for Phase C prototypes if:

```text
price_date <= T
rolling window ends at T
minimum history is satisfied
missing dates are handled explicitly
```

Examples:

- market_beta
- realized_volatility
- downside_drawdown_risk
- trading_liquidity
- return_momentum

### Benchmark Returns

Benchmark beta, correlation, relative strength, and commodity/rate sensitivity must use:

```text
benchmark return window <= T
benchmark identity known as of T
no future benchmark constituents or reclassifications
```

If benchmark identity is unknown as of T, the exposure must use a documented default benchmark with capped confidence, or be marked `PARTIALLY_SUPPORTED`.

### ETF Metadata

ETF name, type, group, style flags, benchmark index, fund category, and similar metadata may be used in strict replay only when the record has:

```text
metadata_effective_date <= T
metadata_available_date <= T
source_version
```

If the project only has a current static metadata file, the field is allowed only for:

```text
DESCRIPTIVE_ONLY
manual review
current-date analysis
non-replay documentation
```

### Fund Holdings / Index Constituents

Holdings and constituents require publication-lag control:

```text
holdings_as_of_date <= T
holdings_available_date <= T
constituent_effective_date <= T
constituent_available_date <= T
```

Forbidden:

- using latest holdings to classify historical dates;
- using future rebalance constituents for prior dates;
- using current top holdings for old replay periods.

### Fund AUM / Shares / Scale

AUM and shares must have:

```text
aum_as_of_date
aum_available_date
shares_as_of_date
shares_available_date
```

Without these fields, AUM/scale cannot enter strict historical exposure calculations.

### Fundamentals / Factor Data

Valuation, growth, profitability, dividend yield, leverage, and similar data must use the later of:

```text
financial_statement_period_end
announcement_date
data_available_date
```

If only current fundamentals are available, the exposure is `NOT_PIT_SAFE`.

### Bond / Rate Fields

Duration, yield, credit spread, and curve bucket require:

```text
data_as_of_date
data_available_date
rate_benchmark_date <= T
```

Price-only bond stability proxies can be calculated, but must not be described as precise duration exposure.

### Commodity / FX Fields

Commodity and FX exposures require benchmark series with:

```text
benchmark_date <= T
calendar alignment rule
asset-class mapping rule
```

QDII/cross-border exposures require separate foreign market calendar, FX return, and premium/discount governance before strict replay.

## Rolling Window Rules

All rolling calculations must define:

```text
window_length
minimum_observations
warmup_policy
calculation_frequency
missing_data_policy
```

Standard warm-up recommendations:

| Exposure | Minimum Window | Preferred Window |
| --- | --- | --- |
| realized_volatility | 20 trading days | 60 trading days |
| downside_drawdown_risk | 60 trading days | 120 trading days |
| market_beta | 60 trading days | 120 trading days |
| trading_liquidity | 20 trading days | 60 trading days |
| return_momentum | 20 trading days | 60 / 120 trading days |
| commodity/resource beta | 120 trading days | 240 trading days |
| interest-rate proxy beta | 120 trading days | 240 trading days |

Warm-up failures must produce `INSUFFICIENT_HISTORY`, not silently imputed values.

## Forbidden Inputs

The following are not allowed in strict point-in-time exposure calculation:

1. Future returns.
2. Future ETF classifications.
3. Future index constituents.
4. Future holdings.
5. Latest static metadata backfilled across history.
6. Current benchmark mapping applied to all historical dates without effective dating.
7. Current theme labels applied to historical periods without taxonomy versioning.
8. Forward label maturity information used as an exposure input.
9. Phase 5.2/5.3 outcome labels used to define exposures.

## PIT Status Labels

| PIT Status | Meaning |
| --- | --- |
| PIT_SAFE | All required fields are known as of T and warm-up is satisfied. |
| PIT_SAFE_WITH_PROXY | Calculation is point-in-time, but uses a documented proxy/default benchmark. |
| DESCRIPTIVE_ONLY | Useful for current description/manual review, but not strict replay. |
| NOT_PIT_SAFE | Missing available-date or uses future/static backfilled data. |
| INSUFFICIENT_HISTORY | Data is PIT-safe but warm-up/minimum history is not met. |

## Missing Data Policy

Missing data must not be silently filled in a way that creates false precision.

Recommended policies:

| Situation | Required Handling |
| --- | --- |
| insufficient rolling window | `INSUFFICIENT_HISTORY` |
| missing benchmark | proxy allowed only with `PIT_SAFE_WITH_PROXY`, otherwise `PARTIALLY_SUPPORTED` |
| missing metadata available date | `DESCRIPTIVE_ONLY` or `NOT_PIT_SAFE` |
| missing holdings | do not compute holdings-based concentration |
| missing duration/yield | do not compute precise rate sensitivity |
| missing commodity benchmark | do not compute commodity beta |
| missing FX benchmark/calendar | do not compute QDII FX exposure |

## Audit Requirements For Phase C

Every Phase C prototype output should include:

```text
exposure_name
symbol
calculation_date
window_start_date
window_end_date
source_fields
data_as_of_date
data_available_date
point_in_time_status
confidence_level
missing_data_reason
research_only=true
execution_allowed=false
```

## Governance Boundary

An exposure that cannot be made point-in-time safe must not enter replay, robustness, preview, ranking, score, or formal execution. It can remain a descriptive metadata tag or manual review attribute.

