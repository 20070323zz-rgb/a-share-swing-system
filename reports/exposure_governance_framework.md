# Exposure Governance Framework

## Batch Header

- Batch Name: Exposure Framework Phase F - Exposure Governance & Portfolio Role Definition
- Batch Type: Governance
- Current Phase: Exposure Framework Phase F
- Current Batch: Exposure Governance
- Objective: Define the formal research role, permissions, readiness, and freeze policy for first-generation price-derived exposures.
- Scope: Governance and documentation only; no exposure, formula, strategy, ranking, score, preview, shadow, formal, universe, replay, or portfolio-allocation changes.

## 1. Context

Repository evidence establishes the following sequence:

- Style Fit 1.0 became a `V1-SPECIFIC_FINDING` after failed Universe V2 generalization.
- Exposure Framework replaced one-label Style compression with measurable, multi-dimensional, point-in-time risk descriptions.
- Phase C produced five price/liquidity-derived research exposures.
- Phase D validated coverage, differentiation, stability, redundancy, and research readiness.
- Phase E-A redesigned single-benchmark market beta as a multi-benchmark vector.
- Phase E-B generated a 16-ETF, six-benchmark research-only vector and found `ADDS_EXPLANATORY_DIMENSION`.

No repository evidence shows that an exposure predicts future return or should directly change a trade decision.

## 2. Objective

This framework defines:

1. The role of Exposure in the system.
2. The readiness category for each first-generation exposure.
3. What downstream research may consume Exposure.
4. What modules remain blocked.
5. Whether first-generation price-derived exposure expansion should freeze.

## 3. Exposure System Role

Exposure is a measurement layer. It describes what risks and market drivers an ETF or portfolio currently carries, with a calculation date, lookback, confidence, and PIT status.

Exposure is not an Alpha or Signal layer.

| Layer | Formal Role | Exposure Permission |
| --- | --- | --- |
| Signal Layer | Predicts or ranks expected future opportunity and may influence BUY/WATCH/SELL. | BLOCKED. Exposure cannot create or alter signals. |
| Exposure Layer | Measures current market sensitivity, realized risk, downside behavior, liquidity, and momentum state. | ALLOWED as research artifacts. |
| Portfolio Layer | Studies combined holdings, concentration, substitution, and implementation risk. | CONDITIONAL for research design only. No allocation logic. |
| Risk Layer | Studies volatility, drawdown, liquidity, and shared market-driver concentration. | CONDITIONAL for research-only diagnostics. |
| Exit Layer | Studies when and why positions should be reduced or closed. | BLOCKED as a direct trigger. A future Exit Research batch may study exposure as context, not as an automatic rule. |

Exposure does not answer:

```text
Will this ETF outperform?
Should this ETF be bought?
Should this position be sold?
What portfolio weight should this ETF receive?
```

Exposure answers:

```text
What risk drivers are present?
How strong are they?
How concentrated or duplicated are they?
How liquid and volatile is the instrument?
How confident and point-in-time-safe is the measurement?
```

## 4. Readiness Categories

| Category | Definition | Permission Meaning | Must Not Be Misread As |
| --- | --- | --- | --- |
| READY_FOR_PORTFOLIO_RESEARCH | Sufficient PIT safety, interpretability, differentiation, and data quality for diagnostic portfolio research design. | May be studied for concentration, duplication, substitution, and risk reporting under a separate approved batch. | Portfolio-model validation, allocation approval, or execution readiness. |
| READY_FOR_RESEARCH_OBSERVATION | Suitable for historical/current monitoring, but not yet a portfolio-research input. | May be recorded and compared without changing decisions. | Weak signal, score input, or portfolio permission. |
| NEEDS_REFINEMENT | Concept remains useful, but benchmark, formula, stability, or data limitations block broader use. | Historical description and scoped refinement only. | Permission to use a provisional proxy downstream. |
| DESCRIPTIVE_ONLY | Useful as metadata or narrative description but not as strict quantitative exposure. | Current description/manual review only. | PIT-safe calculation or model feature. |
| DEFER | Not ready for active research use. | Preserve the candidate and its gap; do not calculate or integrate it. | Rejection of the economic concept. |

## 5. First-Generation Readiness Verdicts

| Exposure | Readiness Verdict | Allowed Research Role | Evidence and Conditions |
| --- | --- | --- | --- |
| `market_exposure_vector` | READY_FOR_PORTFOLIO_RESEARCH | Shared market-driver and benchmark concentration diagnostics. | E-B added explanatory dimensions in 20/32 comparisons and had 15/16 dominant-benchmark window consistency. Basket V1 remains proxy-based, lacks resource/cyclical coverage, and has localized benchmark redundancy. |
| `realized_volatility` | READY_FOR_PORTFOLIO_RESEARCH | Portfolio risk concentration and relative risk-state research. | PIT-safe, complete, strongly differentiating, and stable across 20d/60d. Must not become an automatic position-size rule. |
| `downside_drawdown_risk` | READY_FOR_PORTFOLIO_RESEARCH | Downside concentration, tail-risk overlap, and stress-report research. | PIT-safe and differentiating; partially stable across windows. Separate windows must remain visible and no single drawdown value may dictate exits. |
| `trading_liquidity` | READY_FOR_PORTFOLIO_RESEARCH | Tradability, implementation-risk, and substitution research. | PIT-safe, stable, strongly differentiating, and relatively independent. Current amount/volume proxy does not replace AUM, spread, or market-impact data. |
| `return_momentum` | READY_FOR_RESEARCH_OBSERVATION | Dynamic state observation with separate 20d/60d/120d horizons. | PIT-safe and differentiating but horizon-dependent and signal-adjacent. It is blocked from Portfolio Research until a separate governance and validation decision prevents Alpha leakage. |

The four `READY_FOR_PORTFOLIO_RESEARCH` verdicts are governance permissions for diagnostic research design. They do not upgrade the overall framework to Preview or execution readiness.

## 6. Exposure Permission Principles

1. Exposure values must preserve calculation date, source, window, PIT status, confidence, and missing flags.
2. Multiple exposures may be high simultaneously.
3. Beta values are sensitivities, not weights, and must not be normalized to sum to one.
4. A best-fit benchmark is not an economic classification.
5. Exposure values cannot directly create BUY, WATCH, SELL, score, ranking, preview, shadow, or execution actions.
6. Portfolio Research may consume Exposure only in a separately approved research batch.
7. Any future promotion requires new evidence and an explicit state transition.

## 7. Price-Derived Exposure Freeze

Verdict:

```text
Price-Derived Exposure Expansion = FROZEN
```

Freeze scope:

- No new price-derived exposure names.
- No new lookback windows.
- No formula tuning to improve results.
- No benchmark-basket expansion.
- No conversion to composite exposure scores.
- No integration into Strategy, Ranking, Score, Preview, Shadow, Formal, or Portfolio Allocation.

Allowed while frozen:

- Deterministic refresh of approved research artifacts using the same formulas and data contract.
- Bug fixes that restore documented behavior, with validation.
- Recovery validation, data-quality audit, documentation, and research observation.
- Main-approved Portfolio Research design using only the permitted diagnostic roles.

Completed scope:

- Feasibility, taxonomy, data contract, PIT rules.
- Narrow five-exposure prototype.
- Coverage, stability, differentiation, and redundancy validation.
- Multi-benchmark market exposure redesign and prototype.
- Governance, permission matrix, portfolio role, and research journal.

Unfinished scope:

- Longitudinal/out-of-sample exposure observation.
- Resource/cyclical market benchmark.
- 510500/512100 retain/remove validation.
- Structured benchmark registry with effective/available dates.
- Holdings, AUM, shares, bid/ask spread, fundamentals, duration, commodity, and FX exposure layers.
- Any portfolio construction or exit-use validation.

Future reopen conditions:

- A material data gap is closed with PIT-safe structured data.
- Existing exposure behavior fails a future validation and requires redesign.
- Main approves a narrowly defined new exposure objective.
- A benchmark/metadata governance change requires a versioned framework update.

Reopening does not automatically authorize Fundamental Exposure development.

## 8. Phase Closure

```text
Exposure Framework Phase F = COMPLETE
Exposure Governance = COMPLETE
Exposure Framework Phase 1 = COMPLETE
Price-Derived Exposure Expansion = FROZEN
Portfolio Research Integration = ELIGIBLE_FOR_RESEARCH_DESIGN
Signal Integration = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Exposure Framework Phase 1 forms a complete research loop: problem definition, data governance, prototype, validation, redesign, engineering prototype, and permission governance. It is a completed research phase, not a production model.

## 9. Validation

- No exposure formula or exposure family was modified or added.
- No Portfolio Allocation or Exit Logic was developed.
- Strategy, Ranking, Score, BUY/WATCH/SELL, Regime, Universe, Preview, Shadow, Formal, and Replay remain unchanged.
- Permissions remain research-only and require separate Main approval for downstream design work.
