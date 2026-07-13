# Style Fit Governance Framework

Validation date: 2026-07-08

Scope: Phase 3.5C research governance for the Style Fit research line. This document defines how existing Style Fit evidence may be referenced by future research. It does not create a preview, score adjustment, ranking rule, strategy rule, shadow logic change, or formal execution change.

## Source Boundaries

Authoritative inputs:

- `reports/regime_layer_phase3_style_fit.md`
- `reports/regime_layer_phase3_5a_decision.md`
- `reports/regime_layer_phase3_5b_decision.json`
- `reports/style_regime_evidence_qualification_matrix.json`
- `reports/style_fit_evidence_qualification_summary.json`
- `reports/style_fit_future_preview_research_scope.json`
- `reports/effective_sample_coverage_audit.md`
- `docs/current_phase_status.json`
- `docs/current_project_state.md`

Current preserved decisions:

- `style_fit_has_historical_support = true`
- `style_fit_has_incremental_signal_value = true`
- `style_fit_incremental_signal_value_robustness = PARTIALLY_ROBUST`
- `incremental_signal_value_final_answer = YES_WITH_ROBUSTNESS_CAVEAT`
- `ready_for_fit_shadow_observation = true`
- `ready_for_adjusted_preview_research = true`
- `ready_for_preview = false`
- `ready_for_execution = false`
- `execution_allowed = false`

Coverage boundary:

- Evidence applies to the selected 39-ETF backtest pool and the replay artifact window `2025-05-30` to `2026-07-06`.
- Evidence must not be generalized to the full 183-ETF local universe without a separate expansion/replay research batch.
- Coverage audit verdicts are `EXPLAINABLE`, not a broader-universe validation.

## Evidence Category Definitions

| Category | Definition | Applies When | Statistical Meaning | Must Not Be Misread As |
| --- | --- | --- | --- | --- |
| `QUALIFIED_SUPPORT` | Strongest positive research category currently available. Phase 3 positive evidence is supported by robustness checks without a major direction-reversal, sample-dependence, or concentration warning. | Positive Phase 3 cell plus supportive ETF-level/core horizon/time evidence and no material instability warning. | High-confidence historical support inside the current replay pool and window. | A score bonus, buy signal, execution rule, universal style advantage, or proof outside the 39-ETF pool. |
| `CONDITIONAL_SUPPORT` | Positive direction remains research-usable, but confidence is capped by partial robustness, concentration, limited sample, weak excess, or sample-dependence caveat. | Phase 3 positive direction survives enough checks to remain eligible for future positive filter research, but not enough for high confidence. | Medium-confidence historical support with active caveats. | A direct positive ranking adjustment or proof that the style should be preferred in production. |
| `DESCRIPTIVE_ONLY` | The cell may describe observed historical behavior but is not eligible for future positive or negative filter research. | Evidence is neutral, weak, incomplete, or not robust enough to support directional use. | Low-confidence descriptive context only. | A weak buy/sell tilt, a fallback signal, or a candidate for preview scoring. |
| `UNSTABLE` | Direction reversal or core instability blocks directional research use. | Pooling, ETF-level, or segment evidence materially conflicts with the apparent Phase 3 direction. | Low-confidence and unstable; historical direction should not be carried forward. | A contrarian signal, direct penalty, or reliable warning. |
| `QUALIFIED_CONFLICT` | Strongest negative research category currently available. Phase 3 conflict is supported by negative ETF-level/core horizon evidence without a major caveat. | Phase 3 conflict plus consistent negative robustness evidence. | High-confidence historical conflict inside the current replay pool and window. | A score penalty, sell signal, execution block, or universal style ban. |
| `CONDITIONAL_CONFLICT` | Negative direction remains research-usable, but only with medium confidence and caveats. | Phase 3 conflict survives enough checks to remain eligible for future negative filter research, but robustness is partial. | Medium-confidence negative historical evidence with active caveats. | A direct exclusion, short signal, or automatic ranking penalty. |
| `INSUFFICIENT` | Effective samples or Phase 3 cell evidence are insufficient. | Cell data are unavailable, too sparse, or not enough to classify. | No directional inference should be made. | Neutral evidence, zero effect, or evidence that the style does not matter. |

## Current Evidence Counts

| Category | Count |
| --- | ---: |
| `QUALIFIED_SUPPORT` | 1 |
| `CONDITIONAL_SUPPORT` | 6 |
| `DESCRIPTIVE_ONLY` | 11 |
| `UNSTABLE` | 2 |
| `QUALIFIED_CONFLICT` | 1 |
| `CONDITIONAL_CONFLICT` | 3 |
| `INSUFFICIENT` | 12 |

## Cells Eligible For Future Research

Positive filter research eligibility:

- `QUALIFIED_SUPPORT`
- `CONDITIONAL_SUPPORT`

Negative filter research eligibility:

- `QUALIFIED_CONFLICT`
- `CONDITIONAL_CONFLICT`

Disallowed from future directional filter research:

- `DESCRIPTIVE_ONLY`
- `UNSTABLE`
- `INSUFFICIENT`

This eligibility is only a research permission. It does not authorize score changes, preview portfolio creation, or formal execution.

## Special Style Treatments

### HIGH_BETA_THEME

Final treatment:

```text
MULTI_REGIME_SUPPORT_NOT_QUALIFIED
```

Governance interpretation:

- `HIGH_BETA_THEME` contains conditional support in `DEFENSIVE` and `OFFENSIVE`, and conditional conflict in `NEUTRAL`.
- The style carries `LIMITED_ETF_COUNT` and `SAMPLE_DEPENDENCE_RISK`.
- It may be observed in shadow and used as a caveated research candidate only where the evidence matrix marks a cell eligible.
- It must not be promoted as a broad multi-regime support style.

### COMMODITY_CYCLICAL

Final treatment:

```text
CONDITIONAL_MULTI_REGIME_SUPPORT
```

Governance interpretation:

- `COMMODITY_CYCLICAL / DEFENSIVE` is the only current `QUALIFIED_SUPPORT` cell.
- `COMMODITY_CYCLICAL / OFFENSIVE` is `CONDITIONAL_SUPPORT`.
- `COMMODITY_CYCLICAL / NEUTRAL` is `DESCRIPTIVE_ONLY`.
- The style may support future positive filter research in qualified/conditional cells, but it still does not authorize direct score bonus or execution.

## Prohibited Uses

The following mappings are explicitly prohibited:

| Prohibited Mapping | Reason |
| --- | --- |
| `QUALIFIED_SUPPORT` -> direct score bonus | Evidence is historical and cell-level; current scope disallows score bonus. |
| `CONDITIONAL_SUPPORT` -> direct score bonus | Conditional support has medium confidence and active caveats. |
| `QUALIFIED_CONFLICT` -> direct score penalty | Negative evidence is research evidence, not an execution/ranking rule. |
| `CONDITIONAL_CONFLICT` -> direct score penalty | Conditional conflict is weak negative research evidence only. |
| Evidence category -> direct BUY ranking mapping | Ranking must remain unchanged; evidence categories are not ranking factors. |
| Evidence category -> direct WATCH/SELL mapping | Style Fit is not an execution signal or sell rule. |
| Evidence category -> preview portfolio construction | Current `ready_for_preview=false`; preview is not created in Phase 3.5C. |
| Evidence category -> formal execution | `execution_allowed=false`; protected execution files remain out of scope. |
| `DESCRIPTIVE_ONLY` / `UNSTABLE` / `INSUFFICIENT` -> fallback adjustments | These categories are explicitly disallowed from future directional filter research. |

## Future Preview Research Preconditions

Style Fit may enter a future preview research batch only after all of the following are true:

1. Evidence Qualification remains complete and internally consistent with `reports/style_regime_evidence_qualification_matrix.json`.
2. Effective Sample Coverage Audit remains acknowledged; any future claim must preserve the 39-ETF and `2025-05-30` to `2026-07-06` coverage boundary unless a separate expansion batch changes the evidence base.
3. Future preview research scope remains limited to eligible categories:
   - positive: `QUALIFIED_SUPPORT`, `CONDITIONAL_SUPPORT`
   - negative: `QUALIFIED_CONFLICT`, `CONDITIONAL_CONFLICT`
4. `DESCRIPTIVE_ONLY`, `UNSTABLE`, and `INSUFFICIENT` cells remain excluded from directional filter research.
5. A separate Main approval explicitly starts Preview Research.
6. A future preview batch defines evaluation design before implementation, including:
   - no change to raw BUY ranking;
   - no score bonus or penalty unless separately authorized after preview research;
   - no formal execution linkage;
   - clear comparison against current baseline behavior.
7. Current readiness flags are not reinterpreted:
   - `ready_for_adjusted_preview_research=true` means research can be scoped later.
   - `ready_for_preview=false` means no preview artifact is authorized now.

## Phase 3 Research Closure

| Stage | Question Answered | Current Answer |
| --- | --- | --- |
| Phase 3 | Does Style-Regime Fit have historical support as a research-only layer? | Yes, historical support exists, but initial labels were not equal-confidence evidence. |
| Phase 3.5A | Is the Style Fit result robust across time, ETF-level behavior, segments, horizons, and incremental tests? | Partially. Time and horizon support were robust, ETF-level evidence was conflicting, segment support was partial, and incremental value was preliminary partial support. |
| Phase 3.5B | How should Phase 3 evidence be qualified? | Historical support remains; incremental signal value remains directionally supported but downgraded to `YES_WITH_ROBUSTNESS_CAVEAT` / `PARTIALLY_ROBUST`. Evidence is now cell-level qualified. |
| Coverage Audit | Are replay and ETF coverage losses explainable? | Yes. Both replay and ETF coverage are `EXPLAINABLE`, with methodology and coverage risks marked `MEDIUM`, engineering risk `LOW`. |
| Phase 3.5C | How may existing evidence be used by the project in the future? | Only as governed research evidence. Shadow observation and future preview research scope are allowed under constraints; preview creation, score changes, ranking changes, strategy changes, and execution remain blocked. |

## Phase 3.5C Governance Verdict

```text
Phase 3.5C = COMPLETE
Style Fit Research Phase = COMPLETE
Preview Research = NOT STARTED
Formal Execution = BLOCKED
Formal model changed = false
Shadow logic changed = false
Preview created = false
Ranking changed = false
Strategy changed = false
Score changed = false
```
