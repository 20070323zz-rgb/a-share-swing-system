# Phase 3.5 Style Fit Research Journal

Created: 2026-07-08

Purpose: long-term research memory for the Style Fit research line. This is a research journal, not a run report and not an implementation plan.

## 1. Research Goal

The Style Fit research line asked whether ETF style behavior has regime-dependent historical structure that is useful beyond the existing ranking layer.

The governance goal of Phase 3.5C is narrower: define how the project may use existing Style Fit evidence in future research without accidentally turning historical evidence into trading logic.

## 2. Core Findings

Current preserved findings:

- Style Fit has historical support.
- Style Fit has directional incremental signal value.
- Incremental signal value remains supported only with a robustness caveat:

```text
style_fit_incremental_signal_value_robustness = PARTIALLY_ROBUST
incremental_signal_value_final_answer = YES_WITH_ROBUSTNESS_CAVEAT
```

- Evidence must be handled at style-regime cell level, not as one global Style Fit switch.
- `COMMODITY_CYCLICAL / DEFENSIVE` is the only current `QUALIFIED_SUPPORT` cell.
- `SECTOR_DEFENSIVE / DEFENSIVE` is the only current `QUALIFIED_CONFLICT` cell.
- `HIGH_BETA_THEME` remains sample-dependent and is not qualified as broad multi-regime support.
- `COMMODITY_CYCLICAL` has conditional multi-regime support, but not across all regimes.

Current evidence counts:

```text
QUALIFIED_SUPPORT = 1
CONDITIONAL_SUPPORT = 6
DESCRIPTIVE_ONLY = 11
UNSTABLE = 2
QUALIFIED_CONFLICT = 1
CONDITIONAL_CONFLICT = 3
INSUFFICIENT = 12
```

## 3. Hypotheses Rejected Or Downgraded

The repository evidence supports the following rejected or downgraded hypotheses:

| Hypothesis | Current Treatment | Evidence Basis |
| --- | --- | --- |
| Raw Phase 3 `SUPPORTED` labels can be treated as equal-confidence positive evidence. | Rejected. | Phase 3.5B evidence qualification splits cells into qualified, conditional, descriptive, unstable, conflict, and insufficient categories. |
| Style Fit incremental value is fully robust. | Downgraded. | Phase 3.5B final answer is `YES_WITH_ROBUSTNESS_CAVEAT`; robustness is `PARTIALLY_ROBUST`. |
| `HIGH_BETA_THEME` has qualified multi-regime support. | Rejected. | Final interpretation is `MULTI_REGIME_SUPPORT_NOT_QUALIFIED` with sample-dependence risk. |
| Descriptive or unstable cells can be used as weak directional filters. | Rejected. | Future preview research scope disallows `DESCRIPTIVE_ONLY`, `UNSTABLE`, and `INSUFFICIENT`. |
| Existing evidence authorizes score bonus or penalty. | Rejected. | Future preview research scope sets `score_bonus_allowed=false` and `score_penalty_allowed=false`. |
| Existing evidence authorizes preview or execution. | Rejected. | `ready_for_preview=false`, `ready_for_execution=false`, and `execution_allowed=false`. |

No additional rejected hypotheses are inferred beyond repository evidence.

## 4. Remaining Uncertainty

Unresolved uncertainties:

- ETF-level pooling reversal remains a major robustness warning.
- Evidence is currently bounded to the 39-ETF selected backtest pool.
- Replay artifacts cover `2025-05-30` to `2026-07-06`, not the full local ETF archive.
- Full 183-ETF generalization is not established.
- Real forward shadow samples remain limited.
- Preview effect size is unknown because preview research has not started.
- The formal model remains unchanged and statistically unproven as a complete strategy system.

## 5. Why Evidence Qualification Was Needed

Phase 3 found historical Style Fit structure, but raw labels such as `SUPPORTED` and `CONFLICT` did not encode robustness quality.

Evidence Qualification was needed because:

- Some Phase 3 support was descriptive rather than robust.
- Some cells had direction reversal or pooling instability.
- Some styles had limited ETF count or sample-dependence risk.
- Positive and negative evidence needed separate permissions.
- Future research needed to know which cells were eligible and which were excluded.

The result is a governance-ready evidence layer, not a trading rule.

## 6. Why Coverage Audit Was Needed

After Phase 3.5B, two coverage questions remained:

- Why replay began at `2025-05-30` despite broader local ETF daily files.
- Why roughly 183 ETF daily files became 39 ETFs in the robustness base.

The audit found both losses explainable:

- Replay start is derived from the 39-ETF trade pool, strict common-date intersection from `2025-03-03`, and `MIN_HISTORY_DAYS = 60`.
- The 183 to 39 reduction occurs upstream in the universe quality review / backtest trade-pool design.

This preserved existing research while limiting its claim scope.

## 7. Why Preview Remains Blocked

Preview remains blocked because:

- `ready_for_preview=false`.
- No preview batch has been approved by Main.
- Existing evidence is historical and cell-level, not a strategy rule.
- Score bonus and score penalty are explicitly not authorized.
- Raw BUY ranking must remain unchanged.
- Effective sample coverage is explainable but still carries medium methodology and coverage risk.
- Current governance only defines permissions for future research use.

`ready_for_adjusted_preview_research=true` means a future research batch can be scoped. It does not mean a preview has started or is authorized.

## 8. Next Research Directions

Recommended future directions, subject to Main approval:

1. Shadow observation design that records qualified/conditional evidence tags without changing decisions.
2. Preview research design for eligible evidence categories only, with baseline comparison and no raw ranking change.
3. Universe expansion replay if Main wants claims beyond the 39-ETF selected pool.
4. Real forward monitoring to compare historical evidence against live shadow outcomes.
5. Exit logic research, which remains a separate formal-strategy bottleneck and should not be solved by Style Fit evidence alone.

## 9. Closure State

```text
Phase 3 = COMPLETE
Phase 3.5A = COMPLETE
Phase 3.5B = COMPLETE
Effective Sample Coverage Audit = COMPLETE
Phase 3.5C = COMPLETE
Style Fit Research Phase = COMPLETE
Preview Research = NOT STARTED
Formal Execution = BLOCKED
```

This journal preserves the research memory needed to continue later without relying on conversation history.
