# Exposure Permission Matrix

## Purpose

This matrix governs how Exposure readiness categories may be used. It creates no automatic mapping from exposure values to trading behavior.

Status meanings:

| Status | Meaning |
| --- | --- |
| ALLOWED | Permitted within the current research boundary. |
| CONDITIONAL | Requires a separate Main-approved batch, explicit method, baseline, and non-integration boundary. |
| BLOCKED | Not permitted under Exposure Framework Phase 1 governance. |

## Category Permission Matrix

| Readiness Category | Historical Description | Research Observation | Portfolio Research | Risk Research | Signal Research | BUY Ranking | Score Adjustment | Preview | Formal Execution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| READY_FOR_PORTFOLIO_RESEARCH | ALLOWED | ALLOWED | CONDITIONAL | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| READY_FOR_RESEARCH_OBSERVATION | ALLOWED | ALLOWED | BLOCKED | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| NEEDS_REFINEMENT | ALLOWED | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| DESCRIPTIVE_ONLY | ALLOWED | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| DEFER | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

`CONDITIONAL` never means automatic integration. It means the question may be researched in a new batch while all execution consumers remain disconnected.

## Current Exposure Permission Matrix

| Exposure | Readiness | Historical Description | Research Observation | Portfolio Research | Risk Research | Signal Research | BUY Ranking | Score Adjustment | Preview | Formal Execution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `market_exposure_vector` | READY_FOR_PORTFOLIO_RESEARCH | ALLOWED | ALLOWED | CONDITIONAL | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| `realized_volatility` | READY_FOR_PORTFOLIO_RESEARCH | ALLOWED | ALLOWED | CONDITIONAL | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| `downside_drawdown_risk` | READY_FOR_PORTFOLIO_RESEARCH | ALLOWED | ALLOWED | CONDITIONAL | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| `trading_liquidity` | READY_FOR_PORTFOLIO_RESEARCH | ALLOWED | ALLOWED | CONDITIONAL | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| `return_momentum` | READY_FOR_RESEARCH_OBSERVATION | ALLOWED | ALLOWED | BLOCKED | CONDITIONAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

## Conditional Portfolio Research Requirements

Before a `READY_FOR_PORTFOLIO_RESEARCH` exposure is used in Portfolio Research, the approved batch must define:

- Research question and non-trading objective.
- Universe version and calculation date.
- Exposure version, source, window, PIT status, and confidence policy.
- Baseline portfolio description.
- Missing-data handling.
- Concentration or duplication metric.
- Explicit statement that no allocation, optimizer, risk budget, ranking, score, signal, preview, or execution change is produced.

## Explicitly Forbidden Mappings

```text
high market exposure -> BUY / SELL
high volatility -> automatic position reduction
high drawdown risk -> exit trigger
low liquidity -> automatic exclusion from current strategy
positive momentum -> ranking bonus
negative momentum -> ranking penalty
exposure category -> BUY/WATCH/SELL
exposure vector -> portfolio weight
exposure concentration -> formal risk budget
```

These mappings remain blocked even when the underlying exposure is `READY_FOR_PORTFOLIO_RESEARCH`.

## Signal and Exit Boundary

Exposure is not Alpha. `return_momentum` is especially signal-adjacent, so its presence in the Exposure Layer does not grant Signal Research permission.

Exposure is also not an Exit rule. A future Exit Logic Research batch may compare exposure context with exit outcomes, but must not inherit an automatic exposure-to-exit mapping from this framework.

## Governance State

```text
Signal Integration = BLOCKED
BUY Ranking = UNCHANGED
Score Adjustment = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```
