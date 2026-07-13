# Exposure Data Contract

## Scope

This document defines Phase B data contracts for candidate exposures. It is a design artifact only.

No exposure score is calculated here. No ranking, strategy, preview, formal execution, universe, regime, or style-mapping logic is changed.

## Contract Status Labels

| Status | Meaning |
| --- | --- |
| SUPPORTED_NOW | Current repository data can support point-in-time prototype calculation. |
| PARTIALLY_SUPPORTED | Current data supports a proxy or metadata tag, but important data is missing. |
| NOT_SUPPORTED | Current repository lacks core data required for reliable calculation. |
| DESCRIPTIVE_ONLY | Can be used for description or manual review, not strict PIT calculation. |

## Confidence Policy

| Confidence | Requirement |
| --- | --- |
| HIGH | Directly measurable from local point-in-time data or structured metadata with available date. |
| MEDIUM | Partially measurable, or uses stable metadata but has missing supporting fields. |
| LOW | Inferred from ETF name/group/manual tag, or lacks data availability dates. |
| NOT_PIT_SAFE | Missing reliable available date or uses non-time-versioned current metadata for historical computation. |

## Priority Exposure Contracts

| exposure_name | exposure_category | economic_meaning | required_data_fields | optional_data_fields | calculation_frequency | minimum_history_requirement | point_in_time_requirement | missing_data_policy | confidence_level_policy | current_support | data_gap_if_any | phase_c_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_beta | Market / Size Exposure | Sensitivity to broad equity market movement. | ETF daily close, benchmark daily close, calculation_date. | beta_60d, beta_120d, benchmark_id. | Daily or after data refresh. | >= 60 trading days for short beta; >= 120 for stronger confidence. | Use only returns <= T; benchmark identity must be known as of T. | If benchmark unavailable, mark PARTIALLY_SUPPORTED or NOT_SUPPORTED for that ETF. | HIGH if benchmark and history present; MEDIUM if using default broad benchmark. | SUPPORTED_NOW for A-share equity proxy. | Structured benchmark registry for non-equity/QDII/bond ETFs. | READY_FOR_PHASE_C |
| realized_volatility | Risk / Volatility Exposure | Recent realized return variability and risk state. | ETF daily close, calculation_date. | volatility_20d, volatility_60d, volatility_120d, downside_volatility_60d. | Daily or after data refresh. | >= 20 trading days; >= 60 preferred. | Rolling window must end at T. | If history insufficient, mark INSUFFICIENT_HISTORY. | HIGH when rolling window complete. | SUPPORTED_NOW | None for basic realized volatility. | READY_FOR_PHASE_C |
| downside_drawdown_risk | Risk / Volatility Exposure | Downside risk, drawdown pressure, loss asymmetry. | ETF daily close, high/low optional, calculation_date. | max_drawdown_60d, max_drawdown_120d, downside_volatility_60d, down_capture_60d. | Daily or after data refresh. | >= 60 trading days; >= 120 preferred. | Rolling window must end at T; no future troughs. | If incomplete window, mark INSUFFICIENT_HISTORY. | HIGH for realized drawdown from daily prices; MEDIUM for benchmark capture if benchmark is default. | SUPPORTED_NOW | Benchmark registry improves capture metrics. | READY_FOR_PHASE_C |
| trading_liquidity | Liquidity / Tradability Exposure | Tradability, capacity, and implementation risk. | ETF daily amount or volume, calculation_date. | avg_amount_20d, avg_amount_60d, avg_volume_20d, fund_aum, bid_ask_spread. | Daily or after data refresh. | >= 20 trading days; >= 60 preferred. | Amount/volume rolling windows must end at T. | If amount missing, fall back to volume with LOW confidence; if both missing, NOT_SUPPORTED. | HIGH for amount-based liquidity; MEDIUM without AUM/spread. | SUPPORTED_NOW | Fund AUM, shares, bid/ask spread. | READY_FOR_PHASE_C |
| return_momentum | Momentum / Trend Exposure | Recent relative strength and price persistence. | ETF daily close, calculation_date. | return_20d, return_60d, return_120d, trend_slope_20, trend_slope_60, benchmark relative strength. | Daily or after data refresh. | >= 60 trading days; >= 120 for long momentum. | Use only prices <= T; no forward returns. | If history insufficient, mark INSUFFICIENT_HISTORY. | HIGH for own-return momentum; MEDIUM for relative momentum if benchmark is default. | SUPPORTED_NOW | Benchmark registry improves relative strength. | READY_FOR_PHASE_C |
| dividend_intent | Dividend / Value Exposure | ETF is designed around dividend, yield, or dividend-low-vol exposure. | ETF metadata/name/group, is_dividend flag, calculation_date or metadata_effective_date. | dividend_yield, index methodology, constituent yield. | On metadata update; not necessarily daily. | No price-history minimum; metadata must be effective at T. | Metadata must have effective date and available date for historical replay. | If no available date, mark DESCRIPTIVE_ONLY for history. | MEDIUM if stable ETF/index metadata exists; LOW if name-only. | PARTIALLY_SUPPORTED | Dividend yield history, index rules, holdings yield, metadata available date. | NEEDS_DATA_BEFORE_PHASE_C for quantitative yield; DESCRIPTIVE_ONLY proxy allowed. |
| size_segment | Market / Size Exposure | Large/mid/small-cap exposure through benchmark or holdings. | Benchmark/index metadata or ETF name/group with effective date. | constituent market-cap distribution, index methodology. | On metadata update; daily only if holdings/benchmark updates. | No price-history minimum for metadata; holdings as of date required for quantitative size. | Benchmark/holdings data must be effective and available as of T. | Name-only size labels are DESCRIPTIVE_ONLY. | MEDIUM with benchmark mapping; LOW with name-only. | PARTIALLY_SUPPORTED | Benchmark index mapping, constituent market caps, index methodology. | NEEDS_DATA_BEFORE_PHASE_C except coarse metadata. |
| commodity_resource_sensitivity | Commodity / Resource Exposure | Sensitivity to oil, metals, gold, resource equities, or commodity cycles. | ETF daily close, commodity/resource metadata, calculation_date. | commodity benchmark returns, resource sector benchmark, futures/spot proxy. | Daily for return beta; metadata update for structural tag. | >= 120 trading days for benchmark sensitivity. | Use only ETF and commodity benchmark returns <= T. | Without commodity benchmark, label as DESCRIPTIVE_ONLY or proxy-only. | MEDIUM if commodity benchmark exists; LOW for name-only. | PARTIALLY_SUPPORTED | Commodity benchmark library, resource-sector benchmark mapping. | NEEDS_DATA_BEFORE_PHASE_C for beta; metadata proxy only. |
| interest_rate_bond_sensitivity | Interest Rate / Bond Sensitivity | Sensitivity to rates, duration, credit spreads, or cash-like stability. | ETF daily close, bond/cash metadata, calculation_date. | duration, yield to maturity, credit spread, yield curve bucket, rate benchmark returns. | Daily for return proxy; metadata update for duration/yield. | >= 120 trading days for rate-beta proxy; no history requirement for dated duration metadata. | Duration/yield/curve data must have data_as_of and available_date. | Without duration/yield, use only DESCRIPTIVE_ONLY bond/cash tag or realized stability proxy. | HIGH with duration/yield fields; LOW-MEDIUM with price-only proxy. | PARTIALLY_SUPPORTED | Bond duration/yield, credit spread, yield curve benchmark. | NEEDS_DATA_BEFORE_PHASE_C for precise rate exposure; limited proxy deferred. |
| concentration_proxy | Concentration / Diversification Exposure | Single-driver, theme, sector, or constituent concentration risk. | concentration_profile or duplicate_exposure_group with calculation_date. | holdings top-N weights, sector weights, benchmark concentration, HHI. | Metadata update; holdings-based update when holdings refresh. | No price-history minimum for metadata; holdings date required for robust measure. | Holdings/benchmark concentration must be available at T; current static tags are not replay-safe. | Static concentration tags are DESCRIPTIVE_ONLY unless versioned. | MEDIUM with holdings; LOW with current profile only. | PARTIALLY_SUPPORTED | Fund holdings, constituent weights, sector weights, index HHI. | NEEDS_DATA_BEFORE_PHASE_C; weak metadata proxy only. |

## Deferred / Metadata-Only Exposure Contracts

| exposure_name | exposure_category | treatment | reason | phase_c_candidate |
| --- | --- | --- | --- | --- |
| value_factor | Dividend / Value Exposure | NEEDS_DATA_BEFORE_PHASE_C | Requires valuation ratios, holdings valuation, or value-index methodology. | No |
| growth_factor | Dividend / Value / Theme boundary | NEEDS_DATA_BEFORE_PHASE_C | Requires growth fundamentals, benchmark methodology, or holdings attribution. | No |
| sector_industry_tag | Sector / Industry Exposure | DESCRIPTIVE_ONLY | Current labels are not a controlled PIT taxonomy. | No, unless taxonomy and effective dates are built first. |
| technology_innovation_tag | Theme / Innovation Exposure | DESCRIPTIVE_ONLY | Theme definitions drift and current data is mostly name/registry inferred. | No |
| ai_digital_theme_tag | Theme / Innovation Exposure | DESCRIPTIVE_ONLY_OR_DEFER | No controlled taxonomy, holdings, or benchmark methodology. | No |
| manufacturing_upgrade_tag | Theme / Innovation Exposure | DESCRIPTIVE_ONLY | Registry labels exist, but objective holdings/industry weights are missing. | No |
| qdii_fx_cross_border | Market / FX / Cross-Border | SEPARATE_RESEARCH_TRACK | Needs FX benchmark, foreign-market benchmark, calendar, and premium/discount rules. | No for A-share Phase C. |

## Minimum Contract Requirements For Phase C

Every Phase C prototype exposure must define:

```text
exposure_name
exposure_category
source_fields
calculation_date
data_as_of_date if metadata/holdings are used
data_available_date if metadata/holdings are used
warmup_window
minimum_history_requirement
missing_data_policy
confidence_level_policy
point_in_time_status
research_only=true
execution_allowed=false
```

## Non-Authorization Statement

This data contract does not authorize calculating final exposure scores. Phase C must create prototype outputs separately and must remain research-only unless Main approves a later governance gate.
