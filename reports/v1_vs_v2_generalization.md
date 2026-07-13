# V1 vs V2 Generalization Analysis

## Summary

- Generalization Verdict: FAILED_GENERALIZATION
- Phase 3 Research Impact: CHALLENGED
- Methodology Risk: MEDIUM
- Coverage Risk: LOW
- Engineering Risk: LOW

## Qualification Counts

- V1: QUALIFIED_SUPPORT=1, CONDITIONAL_SUPPORT=6, DESCRIPTIVE_ONLY=11, UNSTABLE=2, QUALIFIED_CONFLICT=1, CONDITIONAL_CONFLICT=3, INSUFFICIENT=12
- V2: QUALIFIED_SUPPORT=4, CONDITIONAL_SUPPORT=4, DESCRIPTIVE_ONLY=9, UNSTABLE=3, QUALIFIED_CONFLICT=1, CONDITIONAL_CONFLICT=0, INSUFFICIENT=15

## Evidence Migration

- CHANGED_DIRECTION_OR_CATEGORY: 6
- DOWNGRADED: 3
- UNCHANGED: 24
- UPGRADED: 3

## New Stable Relationships

- CORE_LARGE_CAP / NEUTRAL: QUALIFIED_CONFLICT

## Robustness Delta

- Time Robustness: FRAGILE
- ETF-level Robustness: PARTIAL_SUPPORT
- Segment Robustness: FRAGILE
- Horizon Robustness: CONFLICTING
- Incremental Value Robustness: CONFLICTING
- Major Robustness Warning: True

## Preview Boundary

- Recommendation: DO_NOT_START_AUTOMATICALLY
- Blocking Reason: Phase 5.2 is a generalization validation batch only; Preview Research requires explicit Main approval and governance gate even when generalization is supported.
