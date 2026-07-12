# Exposure Portfolio Role Definition

## Scope

This document defines what future Portfolio Research may study with Exposure. It does not implement portfolio weights, risk budgets, optimization, position sizing, or execution.

## Portfolio Research Role

Exposure may serve as a diagnostic input to future Portfolio Research. Its role is to reveal combined risk structure that is not visible from ETF count or nominal allocation alone.

The permitted question is:

```text
What risks would this set of ETFs combine or duplicate?
```

The prohibited question is:

```text
What weights should the system trade?
```

## Permitted Research Questions

### Duplicate Risk Exposure

Study whether apparently different ETFs carry similar market, volatility, downside, or liquidity exposure.

Examples:

- Two technology ETFs both dominated by the STAR benchmark family.
- Mid-cap and small-cap candidates with highly correlated benchmark exposure.
- Multiple defensive ETFs sharing the same dividend proxy behavior.

### Exposure Concentration

Describe whether a candidate portfolio is concentrated in one market family, high realized volatility, downside risk, or liquidity condition.

Allowed outputs:

- Exposure distribution reports.
- Concentration flags for research review.
- Pairwise similarity or clustering diagnostics.
- Historical descriptions of concentration changes.

### ETF Substitution Research

Compare ETFs that provide similar exposure but differ in liquidity, volatility, drawdown, or data confidence.

This may identify research alternatives. It must not automatically replace a formal strategy candidate or trade pool member.

### Risk Concentration Analysis

Study combinations such as:

- High technology beta plus high realized volatility.
- Shared small-cap exposure across multiple holdings.
- Weak liquidity combined with high drawdown risk.
- Defensive benchmark concentration that reduces market-family diversity.

### Portfolio Exposure Reporting

Produce research-only reports showing exposure vectors, overlap, confidence, missing data, and PIT status for a hypothetical or observed set of ETFs.

### Position Research Input

Exposure may be supplied as a research covariate when studying future position sizing. It cannot determine size, cap, or risk budget until a separate model-development and validation process is approved.

## Current Exposure Eligibility

| Exposure | Portfolio Research Eligibility | Permitted Role | Key Limitation |
| --- | --- | --- | --- |
| `market_exposure_vector` | CONDITIONAL | Market-family overlap, benchmark concentration, substitution. | Basket V1 proxy/history gaps, resource gap, benchmark redundancy. |
| `realized_volatility` | CONDITIONAL | Relative risk and volatility concentration. | Realized risk is backward-looking and not a weight rule. |
| `downside_drawdown_risk` | CONDITIONAL | Tail/downside concentration and stress description. | Window stability is partial; not an Exit trigger. |
| `trading_liquidity` | CONDITIONAL | Tradability and implementation-risk comparison. | Amount/volume do not capture AUM, spread, or market impact. |
| `return_momentum` | BLOCKED | Research observation only. | Horizon-dependent and too close to Alpha/Signal behavior. |

## Portfolio Research Architecture

```text
Existing ETF / hypothetical portfolio set
-> research-only exposure retrieval
-> confidence and PIT checks
-> overlap / concentration / substitution diagnostics
-> research report
-> Main review
```

The architecture must stop at the research report.

It must not continue automatically to:

```text
optimizer
risk budget
target weights
position sizing
BUY/WATCH/SELL
order generation
paper execution
formal execution
```

## Prohibited Portfolio Logic

This phase does not authorize:

- Mean-variance optimization.
- Risk parity.
- Minimum-volatility allocation.
- Exposure-neutral portfolios.
- Benchmark-targeting weights.
- Momentum tilts.
- Liquidity-based automatic exclusion.
- Drawdown-based automatic de-risking.
- Exposure caps in formal or paper portfolios.

## Readiness Gate

```text
Portfolio Research Integration = ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research = NOT_STARTED
Portfolio Allocation Logic = NOT_STARTED
Portfolio Weight Integration = BLOCKED
```

A future Portfolio Research batch must be separately approved by Main and must remain disconnected from Preview and Formal Execution.

## Relation To Exit Logic

Exposure governance no longer blocks Exit Logic Research. The project may shift its next main research line to Exit Logic because Exposure roles and permissions are now explicit.

However:

- Exposure is not an Exit signal.
- No exposure threshold may trigger a sale.
- Exit Logic Research must define its own hypotheses, labels, validation, and governance.
- This batch does not start Exit Logic Research.
