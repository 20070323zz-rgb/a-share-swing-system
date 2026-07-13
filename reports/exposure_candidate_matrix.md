# Exposure Candidate Matrix

## Scope

- Batch: Style Framework 2.0 Phase A - Exposure Framework Feasibility Study
- Purpose: identify candidate ETF exposure variables for future research.
- Status: research-only feasibility matrix.
- Development: NOT_STARTED
- Preview: NOT_STARTED
- Formal execution: BLOCKED

This matrix does not authorize scoring, ranking, preview, or execution changes.

## Candidate Matrix

| Exposure Candidate | Concept Type | Economic Meaning | Point-in-Time Feasibility | Stability | Maintainability | Measurability | Current Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Market Beta | Factor / risk exposure | Sensitivity to broad equity market movement. | High if calculated from historical ETF returns against a benchmark available at T. | Medium; beta drifts but meaning is stable. | High with ETF daily data. | Supported by `beta_60d`, `beta_120d` in `reports/etf_risk_profile.csv`. | Worth studying as core exposure. |
| Size | Factor / benchmark exposure | Large-cap, mid-cap, small-cap, micro-cap economic scale tilt. | Medium; can use ETF metadata/index names now, holdings would be better. | Medium; ETF benchmark intent is stable, constituent size changes. | Medium. | Partially supported by ETF names/groups and broad index labels; no constituent market-cap distribution. | Worth studying, needs benchmark/holdings data for high confidence. |
| Growth | Factor / style exposure | Tilt toward high growth expectations, innovation, or growth-heavy industries. | Medium; currently name/style inferred. | Medium-low for themes, medium for broad growth indexes. | Medium if benchmark metadata exists; low if manual. | Partially supported by `is_growth`, style labels, ETF names; no valuation/profit growth data. | Worth studying as secondary exposure only. |
| Value | Factor / style exposure | Tilt toward cheaper valuation or value index construction. | Low-medium; current database lacks valuation constituents. | Medium if index methodology available. | Medium with benchmark metadata. | Weakly supported by dividend/value names; no book-to-market, earnings yield, or index factor score. | Candidate, but not yet feasible as primary exposure. |
| Dividend / Yield | Factor / income exposure | Tilt toward dividend yield, dividend stability, or shareholder return. | Medium-high for named dividend ETFs; stronger with index rules. | Medium-high for dividend-index ETFs. | Medium. | Partially supported by `is_dividend`, style labels, names; no dividend yield history. | Worth studying as primary or secondary exposure. |
| Low Volatility | Factor / risk exposure | Lower realized volatility or explicit low-vol index construction. | High for realized-volatility proxy; medium for index-intent exposure. | Medium; realized volatility changes but low-vol construction is interpretable. | High for realized data, medium for index metadata. | Supported by realized vol columns; partially supported by `is_low_vol`. | Worth studying as dual exposure: realized and structural. |
| Liquidity | Trading / microstructure exposure | Ease of entering/exiting ETF; proxy for capacity and implementation risk. | High with daily amount/volume available at T. | Medium; liquidity regimes change but measurement is objective. | High. | Supported by `amount`, `volume`, `avg_amount_20d`, `avg_amount_60d` in quality review. | Worth studying as gating/risk exposure, not return style. |
| Momentum | Statistical / factor exposure | Recent relative strength or trend persistence. | High using historical returns up to T. | Medium-low; signal varies, but definition is objective. | High. | Supported by `return_20d`, `return_60d`, `return_120d` and ranking features. | Worth studying as dynamic exposure, not static identity. |
| Commodity Sensitivity | Asset / macro exposure | Sensitivity to commodity/resource cycles such as oil, metals, gold. | Medium with named commodity/resource ETFs; high with commodity benchmarks. | Medium; ETF mandate stable, commodity beta varies. | Medium. | Partially supported by ETF labels and return behavior; no futures/spot commodity benchmark set. | Worth studying with benchmark additions. |
| Interest Rate Sensitivity | Macro / fixed-income exposure | Sensitivity to rates, bond duration, credit spread, cash-like behavior. | Medium for bond ETF labels; low for duration precision. | Medium-high if duration data exists. | Medium-low until duration/yield data exists. | Partially supported by bond/cash labels and ETF returns; no duration, yield curve, credit spread metadata. | Important, but needs data expansion. |
| Cyclical | Macro / sector exposure | Sensitivity to economic expansion, credit cycle, industrial/consumer cycle. | Medium-low now; mostly inferred by industry/theme names. | Medium; sector cyclicality is stable but ETF composition varies. | Medium with sector benchmark mapping. | Partially supported by current style labels and groups. | Worth studying, but should be multi-exposure not single style. |
| Defensive | Macro / sector exposure | Lower economic-cycle sensitivity, utilities, consumer staples, low-vol, dividend. | Medium-low now; label-inferred. | Medium. | Medium with industry mapping and holdings. | Partially supported by dividend/low-vol/utilities names and risk profile. | Worth studying with explicit sector/industry support. |
| Concentration | Portfolio-structure exposure | Degree to which ETF is concentrated by industry, theme, top constituents, or single macro driver. | Low-medium now; strong only with holdings. | Medium; theme concentration is persistent, but constituents move. | Medium with holdings; low manually. | Partially supported by `concentration_profile`; no top-holdings weights. | Highly important after V2 failure, but current data is incomplete. |
| Technology Innovation | Theme / economic narrative exposure | Exposure to semiconductor, AI, software, computing, STAR growth, innovation capex. | Medium-low; current labels are mostly name-based. | Low-medium; theme definitions shift quickly. | Low-medium without benchmark taxonomy. | Partially supported by ETF names/style labels; no holdings or benchmark industry weights. | Candidate, but should be governed as theme exposure with confidence cap. |
| Manufacturing / Industrial Upgrade | Theme / industry exposure | Exposure to high-end equipment, industrial machine tools, robotics, automation. | Medium-low; name-based now. | Low-medium. | Low-medium. | Partially supported by registry exposure categories; no constituent industry weights. | Candidate, needs taxonomy and holdings support. |
| AI / Digital Economy | Theme exposure | Exposure to AI, compute, data, software, digital infrastructure. | Low-medium; theme definitions are unstable. | Low. | Low unless benchmark taxonomy is maintained. | Weakly supported by names only for many ETFs. | Observe-only candidate until taxonomy and data improve. |
| QDII / FX / Cross-Border | Asset / market-access exposure | Offshore equity, HK/US/Japan/other market and currency/calendar exposure. | Medium with ETF metadata; low for FX/calendar decomposition. | Medium. | Medium-low. | Partially supported by QDII labels; no FX return, premium/discount, or holiday calendar integration. | Separate research track, not mixed with A-share exposure. |

## Interpretation

The strongest near-term candidates are those that are objective and already measurable from the unified ETF database: Market Beta, Volatility, Liquidity, and Momentum. Dividend/Yield, Size, Commodity Sensitivity, and Interest Rate Sensitivity are promising but require stronger metadata or benchmark support. Theme exposures such as Technology Innovation, Manufacturing, and AI should not be primary research exposures until they have a controlled taxonomy, point-in-time metadata, and confidence scoring.

## Literature Anchors

- Fama/French risk-factor research supports the idea that size, value, profitability, and investment-related characteristics can explain return differences.
- MSCI and BlackRock/iShares describe factor investing as exposure to persistent, economically grounded characteristics such as value, quality, momentum, size, yield/dividend, and low volatility.
- MSCI's public factor material also shows multi-factor construction, which supports allowing one ETF to carry more than one exposure rather than forcing a single label.
