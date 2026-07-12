# Style Fit Permission Matrix

Validation date: 2026-07-08

Scope: formal permission matrix for Style Fit evidence categories after Phase 3.5C governance. This matrix governs research usage only. It does not map evidence into strategy, ranking, score, preview, or execution.

## Global Execution Boundary

| Boundary | Status |
| --- | --- |
| Historical Description | Allowed |
| Shadow Observation | Allowed |
| Preview Research | Not started; future scoped research only after Main approval |
| Formal Strategy | Blocked |
| BUY Ranking Change | Blocked |
| Score Bonus / Penalty | Blocked |
| Execution | Blocked |

Current readiness flags remain unchanged:

```text
ready_for_fit_shadow_observation = true
ready_for_adjusted_preview_research = true
ready_for_preview = false
ready_for_execution = false
execution_allowed = false
```

## Category Permission Matrix

| Evidence Category | Historical Description | Shadow Observation | Preview Research | Formal Strategy |
| --- | --- | --- | --- | --- |
| `QUALIFIED_SUPPORT` | Allowed as high-confidence positive historical evidence inside the current coverage boundary. | Allowed as non-executing observation tag. | Future positive filter research eligible after Main approval; no current preview. | Prohibited. |
| `CONDITIONAL_SUPPORT` | Allowed as medium-confidence positive historical evidence with caveats. | Allowed as caveated non-executing observation tag. | Future positive filter research eligible after Main approval; no current preview. | Prohibited. |
| `DESCRIPTIVE_ONLY` | Allowed only as descriptive historical context. | Allowed only as non-directional context if needed. | Prohibited for directional filter research. | Prohibited. |
| `UNSTABLE` | Allowed only as an instability warning. | Allowed only as a warning/context tag. | Prohibited for positive or negative filter research. | Prohibited. |
| `QUALIFIED_CONFLICT` | Allowed as high-confidence negative historical evidence inside the current coverage boundary. | Allowed as non-executing risk observation tag. | Future negative filter research eligible after Main approval; no current preview. | Prohibited. |
| `CONDITIONAL_CONFLICT` | Allowed as medium-confidence negative historical evidence with caveats. | Allowed as caveated non-executing risk observation tag. | Future negative filter research eligible after Main approval; no current preview. | Prohibited. |
| `INSUFFICIENT` | Allowed only to state that evidence is insufficient. | Allowed only as a missing-evidence tag. | Prohibited. | Prohibited. |

## Allowed Uses

Historical Description:

- Summarize Phase 3 / Phase 3.5 findings with category-level caveats.
- Explain why raw Phase 3 `SUPPORTED` / `CONFLICT` labels are not equal-confidence evidence.
- Report category counts and eligible research cells.
- State coverage boundaries: 39-ETF selected backtest pool and replay window `2025-05-30` to `2026-07-06`.

Shadow Observation:

- Attach non-executing evidence tags to research dashboards or shadow logs.
- Monitor whether real forward outcomes agree with qualified or conditional evidence.
- Track `HIGH_BETA_THEME` sample-dependence risk and `COMMODITY_CYCLICAL` conditional multi-regime behavior.
- Preserve the distinction between observation and trade decision.

Future Preview Research:

- May be proposed in a separate batch only after Main approval.
- May only use eligible evidence classes:
  - positive: `QUALIFIED_SUPPORT`, `CONDITIONAL_SUPPORT`
  - negative: `QUALIFIED_CONFLICT`, `CONDITIONAL_CONFLICT`
- Must keep raw ranking unchanged unless a later approved batch changes that boundary.
- Must evaluate against baseline before any promotion is considered.

## Prohibited Uses

The following are blocked in all current project states:

- `QUALIFIED_SUPPORT` -> direct score bonus.
- `CONDITIONAL_SUPPORT` -> direct score bonus.
- `QUALIFIED_CONFLICT` -> direct score penalty.
- `CONDITIONAL_CONFLICT` -> direct score penalty.
- Any evidence category -> direct BUY ranking mapping.
- Any evidence category -> direct WATCH/SELL decision.
- Any evidence category -> direct Formal strategy rule.
- Any evidence category -> direct paper simulation action.
- `DESCRIPTIVE_ONLY`, `UNSTABLE`, or `INSUFFICIENT` -> directional preview input.

## Future Research Queue

The following are permitted only as future research questions, not as current implementation:

- Whether eligible positive evidence can improve preview-only filtering without changing raw ranking.
- Whether eligible negative evidence can reduce poor candidates without overfitting.
- Whether full-universe replay over more than the current 39-ETF pool changes evidence categories.
- Whether real shadow observations confirm or weaken the historical evidence.
- Whether score changes should ever be considered after preview research. Current answer: not authorized.

## Consistency Check

This permission matrix is consistent with:

- `reports/style_fit_future_preview_research_scope.json`: `score_bonus_allowed=false`, `score_penalty_allowed=false`, `raw_ranking_must_remain_unchanged=true`, `execution_allowed=false`.
- `reports/regime_layer_phase3_5b_decision.json`: `ready_for_preview=false`, `ready_for_execution=false`, `execution_allowed=false`.
- `docs/current_project_state.md`: Style Fit has not changed BUY ranking or raw ranking scores.

No automatic strategy mapping is created by this matrix.
