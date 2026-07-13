# Exposure Framework Phase 1 Research Journal

Created: 2026-07-10

Purpose: preserve the repository-supported evolution, findings, uncertainty, and closure state of first-generation Exposure Framework research. This is not a run report and does not authorize implementation beyond current governance.

## 1. Research Origin

Style Fit 1.0 used compressed labels such as `HIGH_BETA_THEME`, `DIVIDEND`, `CORE_MID_CAP`, and `COMMODITY_CYCLICAL` to study regime-dependent ETF behavior.

Universe V2 generalization failed. Repository conclusions state:

```text
Style Fit 1.0 = V1-SPECIFIC_FINDING
Generalization Verdict = FAILED_GENERALIZATION
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

The failure did not show that all style information was useless. It showed that coarse, single-label Style Fit did not generalize reliably across the changed Universe and horizons.

The project therefore opened Exposure Framework research: replace one-label compression with measurable, multi-dimensional, point-in-time descriptions.

## 2. Phase Evolution

### Phase A - Feasibility

Defined Exposure as measurable sensitivity or structural linkage to economic drivers, risk factors, market segments, sectors, themes, or implementation properties.

Key conclusion:

```text
Exposure Framework Feasibility = POSITIVE_WITH_DATA_GAPS
```

The largest database gap was structured metadata, not price data.

### Phase B - Taxonomy, Contract, PIT Rules

Established exposure categories, required fields, confidence policy, missing-data policy, warm-up, and point-in-time rules.

Strict rule:

```text
Only data known or knowable at calculation date T may be used.
```

### Phase C - Narrow Prototype

Calculated five price/liquidity-derived exposures for 16 Universe V2 `QUALIFIED_RESEARCH` ETFs:

- `market_beta`
- `realized_volatility`
- `downside_drawdown_risk`
- `trading_liquidity`
- `return_momentum`

The prototype generated 240 values with zero missing rows and remained research-only.

### Phase D - Validation

Validated coverage, window stability, ETF differentiation, redundancy, interpretability, and the 510300 proxy.

Findings:

- `realized_volatility` and `trading_liquidity` were stable.
- `downside_drawdown_risk` and `return_momentum` were partially stable.
- Single-benchmark `market_beta` was stable but structurally incomplete.
- `market_beta` and realized volatility had high redundancy.
- All five exposures differentiated ETFs, but none was authorized for Signal or execution use.

### Phase E-A - Market Exposure Redesign

Reframed Market Exposure as a vector rather than one scalar beta.

```text
Single Benchmark Framework = RETAIN_AS_BASELINE_ONLY
Multi-Benchmark Framework = RECOMMENDED
```

### Phase E-B - Multi-Benchmark Prototype

Generated a six-benchmark vector for 16 ETFs over 60d/120d windows.

Preserved findings:

```text
Vector rows = 192
Missing rows = 0
Non-core R-squared improvement >= 0.05 = 20 / 32 comparisons
120d improvement = 10 / 16 ETFs
Dominant benchmark consistency = 15 / 16 ETFs
Benchmark redundancy = LOCALIZED_HIGH_REDUNDANCY
```

The prototype added explanatory dimensions but did not test future-return prediction.

### Phase F - Governance

Defined Exposure as a non-Alpha measurement layer, assigned readiness categories, established Portfolio Research permissions, and froze first-generation price-derived expansion.

## 3. Why Exposure Is Not Alpha

Current evidence validates measurement properties:

- PIT safety.
- Coverage.
- Stability or partial stability.
- Cross-ETF differentiation.
- Redundancy structure.
- Contemporaneous benchmark explanation.

Current evidence does not validate:

- Future-return prediction.
- Ranking improvement.
- BUY/WATCH/SELL improvement.
- Portfolio-weight improvement.
- Exit improvement.

Therefore Exposure belongs to the Exposure/Risk description layer, not the Alpha/Signal layer.

`return_momentum` remains particularly sensitive to this boundary. It is observable as a dynamic exposure, but its signal-like interpretation is blocked.

## 4. First-Generation Findings

Readiness after Phase F:

| Exposure | Verdict |
| --- | --- |
| `market_exposure_vector` | READY_FOR_PORTFOLIO_RESEARCH |
| `realized_volatility` | READY_FOR_PORTFOLIO_RESEARCH |
| `downside_drawdown_risk` | READY_FOR_PORTFOLIO_RESEARCH |
| `trading_liquidity` | READY_FOR_PORTFOLIO_RESEARCH |
| `return_momentum` | READY_FOR_RESEARCH_OBSERVATION |

`READY_FOR_PORTFOLIO_RESEARCH` means diagnostic research design only. It does not authorize allocation logic.

## 5. Preserved Uncertainty

- Market benchmark basket V1 lacks a resource/cyclical benchmark.
- 510500 and 512100 are highly correlated in both tested windows.
- Some sector/theme ETFs remain weakly explained by basket V1.
- 510500, 512100, and 510880 local proxy histories only slightly exceed the 120d minimum.
- Downside and momentum measures remain horizon-sensitive.
- Realized price behavior does not replace holdings, AUM, spread, fundamentals, duration, commodity, or FX data.
- No longitudinal/out-of-sample Exposure observation has been completed.
- No Portfolio Construction or Exit Logic effect has been tested.

These uncertainties are preserved from repository artifacts. No missing conversational reasoning is reconstructed.

## 6. Why First-Generation Expansion Is Frozen

The first generation has answered its original feasibility and governance questions. Adding more price-derived labels now would increase overlap and maintenance cost before current exposures are used in a disciplined research design.

Freeze permits the project to:

- Preserve a stable first-generation baseline.
- Move to Portfolio or Exit research without repeatedly reopening Exposure definitions.
- Wait for higher-value data gaps to close.
- Avoid turning every measurable price statistic into a new exposure.

Freeze does not mean the framework failed. It means the research scope is complete enough to stop expanding.

## 7. Reopen Conditions

Exposure Framework Phase 1 may be reopened only through a new Main-approved batch when:

- Structured benchmark metadata becomes PIT-safe.
- Holdings, AUM, shares, spreads, fundamentals, duration, commodity, or FX data becomes available.
- A future validation finds material failure in an existing exposure.
- A new portfolio/exit research question demonstrates a specific missing exposure requirement.

Fundamental Exposure development is not started automatically.

## 8. Closure State

```text
Exposure Framework Phase F = COMPLETE
Exposure Governance = COMPLETE
Exposure Framework Phase 1 = COMPLETE
Price-Derived Exposure Expansion = FROZEN
Portfolio Research Integration = ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research = NOT_STARTED
Signal Integration = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

The Exposure Framework Phase 1 research loop is complete. Repository governance now permits Main to choose a different primary research line, including Exit Logic Research, without treating Exposure as an implicit signal or exit rule.
