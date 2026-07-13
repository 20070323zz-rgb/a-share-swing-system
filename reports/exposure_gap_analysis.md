# Exposure Gap Analysis

## Scope

- Batch: Style Framework 2.0 Phase A
- Question: can the current repository database support candidate ETF exposures?
- Evidence sources: `data/etf_daily/`, `reports/etf_risk_profile.csv`, `reports/universe_quality_review.csv`, `configs/universe_versions/universe_v2_registry.yaml`, and Phase 5.2/5.3 reports.
- This is a data-type gap analysis, not a data-source vendor search.

## Current Database Inventory

Current repository support:

| Data Type | Current Status | Evidence |
| --- | --- | --- |
| ETF daily OHLCV / amount | Supported | `data/etf_daily/*.csv` |
| ETF realized return / volatility / beta / drawdown | Supported | `reports/etf_risk_profile.csv` |
| ETF liquidity summary | Supported | `reports/universe_quality_review.csv` |
| ETF style flags and coarse style profile | Supported, but Style Fit 1.0 failed cross-universe generalization | `reports/etf_risk_profile.csv` |
| Universe versioning and selection metadata | Supported | `configs/universe_versions/*.yaml` |
| V2 exposure category notes | Partially supported | `configs/universe_versions/universe_v2_registry.yaml` |
| Benchmark index identity / methodology | Partial / mostly absent | some names imply benchmark, but no structured benchmark registry |
| ETF fund holdings / constituent weights | Not supported | no holdings table found |
| Fund AUM / shares outstanding | Not supported | no AUM table found |
| Industry index matrix | Not supported | no systematic industry index table found |
| Factor valuation data | Not supported | no book-to-market, earnings yield, sales growth, profitability fields |
| Bond duration / yield / credit spread | Not supported | no duration/yield-curve metadata |
| Commodity benchmark returns | Not supported as a separate benchmark library | commodity ETFs exist, but no spot/futures benchmark set |
| FX / cross-border calendar / premium-discount | Not supported | QDII labels exist, but no FX/calendar/premium data |

## Candidate-Level Gap Matrix

| Exposure Candidate | Current Support | What Exists Now | Missing Data Types | Feasibility Implication |
| --- | --- | --- | --- | --- |
| Market Beta | Supported | `beta_60d`, `beta_120d`; ETF daily returns. | More benchmark choices for non-A-share or bond ETFs. | Feasible immediately for A-share equity ETFs; needs benchmark registry for multi-asset use. |
| Size | Partial | ETF/index names and broad/core labels. | Benchmark index mapping, constituent market caps, index methodology. | Usable as coarse metadata exposure, not yet objective factor exposure. |
| Growth | Partial | `is_growth`, `style_profile`, ETF names. | Holdings growth metrics, benchmark factor score, index methodology. | Keep as low-confidence exposure until measurable fields exist. |
| Value | Not supported / weak partial | Some dividend/value-like names. | Valuation ratios, index factor definitions, holdings valuation. | Not ready as independent exposure. |
| Dividend / Yield | Partial | `is_dividend`, dividend/low-vol ETF names, style profile. | Dividend yield history, dividend index rule metadata, constituent yield. | Feasible as named structural exposure; not yet quantitative yield exposure. |
| Low Volatility | Supported / partial | Realized volatility fields and `is_low_vol`. | Index low-vol methodology, holdings risk. | Feasible as realized exposure; structural low-vol requires metadata. |
| Liquidity | Supported | amount/volume and average amount fields. | Fund AUM, bid/ask spread, creation/redemption data. | Feasible as trading/risk exposure; not a style return driver by itself. |
| Momentum | Supported | 20d/60d/120d returns and ranking features. | None required for basic price momentum. | Feasible as dynamic exposure. |
| Commodity Sensitivity | Partial | commodity/resource ETF names and style labels. | Commodity futures/spot benchmark returns, resource-sector benchmark mapping. | Feasible only as label-based exposure until benchmarks are added. |
| Interest Rate Sensitivity | Partial | bond ETF labels and return history. | duration, yield to maturity, credit spread, curve buckets. | Not ready for precise rate exposure. |
| Cyclical | Partial | sector/cyclical labels and ETF groups. | industry benchmark taxonomy, constituent industry weights. | Feasible as coarse tag; not robust enough for predictive framework. |
| Defensive | Partial | dividend, low-vol, utilities-like tags and realized risk. | industry/sector taxonomy, holdings, dividend/earnings stability. | Feasible as composite candidate, needs formal data hierarchy. |
| Concentration | Partial | `concentration_profile`, duplicate exposure groups. | top holdings, constituent weights, index concentration statistics. | Important but under-supported; should be a Phase B data priority. |
| Technology Innovation | Partial | technology/chip/electronics ETF names and registry categories. | standardized theme taxonomy, holdings industry weights, benchmark rules. | Candidate only with confidence cap. |
| Manufacturing / Industrial Upgrade | Partial | high-end equipment / machine-tool registry categories. | industry taxonomy, holdings, benchmark methodology. | Candidate only with confidence cap. |
| AI / Digital Economy | Not supported / weak partial | names may imply AI or digital themes. | theme taxonomy, index constituents, revenue/activity classification. | Observe-only until data support improves. |
| QDII / FX / Cross-Border | Partial | QDII labels and ETF prices. | FX returns, foreign market benchmark, local holiday calendar, premium/discount. | Should be separate exposure family and not mixed with A-share ETF exposure. |

## Largest Gaps

The largest gap is not ETF price data. The project already has enough OHLCV data to measure realized beta, momentum, volatility, drawdown, and liquidity. The largest missing layer is structured metadata:

1. Benchmark index mapping for every ETF.
2. Index methodology or rule family.
3. Fund holdings and constituent weights.
4. Industry / sector / theme taxonomy.
5. Factor fundamentals such as valuation, growth, dividend yield, profitability, and leverage.
6. Fund AUM and trading-friction data beyond amount/volume.
7. Bond duration/yield and commodity/FX benchmark data for non-equity exposures.

## Current Feasibility Verdict

The current database can support a narrow Exposure Framework prototype for realized and price-derived exposures:

```text
Supported now:
Market Beta
Realized Volatility
Liquidity
Momentum
Drawdown / downside risk
```

The current database can partially support structural exposures:

```text
Partially supported:
Size
Dividend
Low Volatility structural intent
Commodity Sensitivity
Interest Rate Sensitivity
Cyclical / Defensive
Concentration
Technology Innovation
Manufacturing
QDII / FX / Cross-Border
```

The current database does not yet support robust factor-fundamental or theme-constituent exposures:

```text
Not yet supported:
Value as valuation factor
Growth as fundamental growth factor
AI / Digital Economy as objective exposure
Precise rate duration exposure
Precise commodity beta exposure
Holdings-based concentration
```

## Research Boundary

No additional data was downloaded for this analysis. No replay was started. No model, strategy, ranking, score, universe, preview, or execution files were modified.
