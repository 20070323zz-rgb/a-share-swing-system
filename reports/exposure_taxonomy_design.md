# Exposure Taxonomy Design

## Scope

- Batch: Exposure Framework Phase B - Taxonomy + Data Contract + Point-in-Time Rules
- Purpose: define how ETF exposures should be classified and named before any prototype development.
- Development: NOT_STARTED
- Preview Research: NOT_STARTED
- Formal Execution: BLOCKED

This design does not modify Style Mapping, Ranking, Strategy, Regime Logic, Universe V1/V2, Preview, or Formal Execution.

## Taxonomy Principles

Exposure is multi-dimensional. One ETF can and should carry multiple exposures with separate source, confidence, and point-in-time status.

The taxonomy should avoid one-label compression. A semiconductor ETF, for example, may simultaneously have:

```text
Market / Size Exposure = high beta, mid/small or STAR growth
Risk / Volatility Exposure = high realized volatility
Momentum / Trend Exposure = dynamic
Sector / Industry Exposure = semiconductor
Theme / Innovation Exposure = technology innovation
Concentration Exposure = high
Liquidity / Tradability Exposure = measurable from amount/volume
```

Industry or theme names are not automatically stable exposures. They become framework exposures only when definition, maintenance, measurement, and point-in-time status are explicit.

## Level-1 Taxonomy

| Level-1 Category | Economic Meaning | Applicable ETF Types | Candidate Level-2 Exposures | Phase C Calculation Fit | Metadata-Only Fit |
| --- | --- | --- | --- | --- | --- |
| Market / Size Exposure | Sensitivity to broad equity risk and capitalization segment. | Broad index, sector, theme, equity QDII after separate rules. | market_beta, beta_to_a_share_core, large_cap, mid_cap, small_cap, broad_market_anchor. | Market beta is ready; size is partial until benchmark/constituent data exists. | Size labels can be metadata now. |
| Risk / Volatility Exposure | Realized risk, downside behavior, and low-vol characteristics. | All ETFs with sufficient daily history; structural low-vol requires metadata. | realized_volatility, downside_volatility, max_drawdown, low_vol_structural_intent, beta_instability. | Realized volatility/drawdown are ready. | Structural low-vol intent is metadata until index methodology exists. |
| Liquidity / Tradability Exposure | Capacity, tradability, implementation risk. | All listed ETFs. | trading_amount, trading_volume, liquidity_rank, liquidity_stability, stale_data_risk. | Ready using current amount/volume summaries and rolling windows. | AUM and bid/ask based liquidity remain metadata gap. |
| Momentum / Trend Exposure | Recent relative strength, persistence, trend quality. | All ETFs with sufficient daily history. | return_momentum_20d, return_momentum_60d, relative_strength, trend_slope, trend_confirmation. | Ready as dynamic exposure with warm-up. | Not suitable as static metadata. |
| Dividend / Value Exposure | Income/value tilt, shareholder yield, valuation sensitivity. | Dividend, value, low-vol dividend, bank/utility-like ETFs. | dividend_intent, dividend_yield, value_factor, shareholder_yield, dividend_low_vol. | Dividend intent is partial; quantitative yield/value not ready. | Dividend/value tags are metadata until yield/valuation data exists. |
| Commodity / Resource Exposure | Sensitivity to commodity/resource cycles and commodity-linked sectors. | Commodity ETFs, resource-sector ETFs, gold/oil/metals-related ETFs. | oil_sensitivity, metals_sensitivity, gold_sensitivity, resource_equity_sensitivity. | Label-based partial only; benchmark beta needs commodity benchmark data. | Commodity/resource tags are metadata now. |
| Interest Rate / Bond Sensitivity | Sensitivity to rates, duration, credit spread, cash-like behavior. | Bond, money market, rate-sensitive dividend/utility ETFs. | bond_cash, duration_sensitivity, credit_spread_sensitivity, rate_proxy_beta, cash_like_stability. | Bond/cash labels and realized behavior partial; precise duration not ready. | Duration/credit categories are metadata until fields exist. |
| Sector / Industry Exposure | Business activity and sector risk. | Sector ETFs, broad ETFs with holdings, thematic ETFs with industry concentration. | financials, bank, broker, consumer, medicine, semiconductor, utilities, energy, industrials. | Not ready as objective calculation without taxonomy/holdings; coarse tags only. | Suitable for controlled metadata with confidence levels. |
| Theme / Innovation Exposure | Thematic economic narrative such as innovation, AI, computing, manufacturing upgrade. | Theme ETFs and high-beta technology ETFs. | technology_innovation, semiconductor_chain, ai_compute, robotics, manufacturing_upgrade, digital_economy. | Not ready for quantitative exposure without taxonomy/holdings/benchmark methodology. | Metadata/research candidate only, confidence-capped. |
| Concentration / Diversification Exposure | Degree of exposure concentration by constituents, sector, theme, or single driver. | All ETFs; especially theme, sector, commodity, QDII. | holdings_concentration, sector_concentration, theme_concentration, duplicate_exposure, single_driver_risk. | Duplicate/label concentration partial; holdings-based concentration not ready. | Important metadata now; Phase C can prototype only a weak proxy. |

## Naming Rules

Use stable snake_case names for future machine-readable fields.

Naming format:

```text
exposure_category.exposure_name
```

Examples:

```text
market_size.market_beta
risk_volatility.realized_volatility
liquidity_tradability.trading_amount_liquidity
momentum_trend.return_momentum
dividend_value.dividend_intent
commodity_resource.resource_sensitivity
interest_rate_bond.bond_cash_sensitivity
sector_industry.industry_tag
theme_innovation.theme_tag
concentration_diversification.concentration_proxy
```

Each exposure record should eventually include:

```text
exposure_name
exposure_category
exposure_value
exposure_bucket
measurement_method
source_fields
calculation_date
data_as_of_date
data_available_date
point_in_time_status
confidence_level
missing_data_flag
research_only
execution_allowed=false
```

## Phase C Suitability By Category

| Level-1 Category | Phase C Status | Rationale |
| --- | --- | --- |
| Market / Size | PARTIAL | Market beta is ready; size is metadata-only until benchmark/holdings support improves. |
| Risk / Volatility | READY | Current database has rolling volatility, drawdown, downside risk fields. |
| Liquidity / Tradability | READY | Current database has volume/amount and quality-review liquidity fields. |
| Momentum / Trend | READY | Current database has returns and ranking features based on past prices. |
| Dividend / Value | PARTIAL | Dividend intent is available; value/yield fundamentals are missing. |
| Commodity / Resource | PARTIAL | Current labels exist; benchmark commodity sensitivity is missing. |
| Interest Rate / Bond | PARTIAL | Bond labels and returns exist; duration/yield/credit spread missing. |
| Sector / Industry | DESCRIPTIVE_ONLY | Requires controlled taxonomy and/or holdings before calculation. |
| Theme / Innovation | DESCRIPTIVE_ONLY | Theme definitions are unstable without taxonomy/benchmark/holdings. |
| Concentration / Diversification | PARTIAL | Weak proxies exist; robust holdings-based concentration missing. |

## Governance Boundary

This taxonomy is a research design artifact. It does not replace Style Fit 1.0, does not create new style labels for execution, and does not authorize exposure scoring.
