# Generalization Evaluation Plan

Generated at: 2026-07-08 19:05:00 CST

Scope: future V1 vs V2 comparison framework. This plan does not run replay and does not validate Style Fit.

## Objective

The purpose of future generalization evaluation is to determine whether research conclusions developed on Universe V1 remain stable, weaken, strengthen, or change when evaluated on the qualified Universe V2 Research Universe.

The goal is not to turn Style Fit into trading logic. The goal is to understand research portability.

## Required Inputs For Future Evaluation

Future Phase 5 replay/evaluation must record:

- Universe V1 version file: `configs/universe_versions/universe_v1.yaml`
- Universe V2 registry file: `configs/universe_versions/universe_v2_registry.yaml`
- Exact V2 batch manifests and completion markers
- Single ETF daily data source: `data/etf_daily/*.csv`
- Regime source and date ranges
- Feature warm-up rules
- Forward-label maturity rules
- Evidence qualification framework from Phase 3.5B / 3.5C

## Comparison Axes

### 1. Data And Coverage Alignment

Compare:

- effective replay start and end dates;
- symbol count;
- style profile count;
- exposure category count;
- missing data rate;
- forward-label maturity coverage;
- benchmark coverage;
- feature warm-up loss.

Questions:

- Does V2 materially change the effective sample window?
- Does V2 add coverage without creating hidden missing-data loss?
- Are V1 and V2 comparisons date-aligned or only qualitatively comparable?

### 2. Style Fit Persistence

Compare:

- whether style-regime fit remains directionally present;
- per-style forward-return separation;
- per-regime style ranking;
- hit rate and effect direction;
- strength of fit by horizon.

Questions:

- Does the original V1 Style Fit relationship remain visible in V2?
- Which style-regime cells are stable across universes?
- Which cells weaken or reverse?

### 3. Evidence Category Migration

Use the Phase 3.5 evidence categories:

- `QUALIFIED_SUPPORT`
- `CONDITIONAL_SUPPORT`
- `DESCRIPTIVE_ONLY`
- `UNSTABLE`
- `QUALIFIED_CONFLICT`
- `CONDITIONAL_CONFLICT`
- `INSUFFICIENT`

Compare category transitions:

| V1 Category | V2 Possible Outcome | Meaning |
| --- | --- | --- |
| QUALIFIED_SUPPORT | remains qualified | stronger generalization |
| QUALIFIED_SUPPORT | conditional/descriptive | weaker but not necessarily invalidated |
| CONDITIONAL_SUPPORT | qualified | possible strengthened evidence |
| DESCRIPTIVE_ONLY | qualified/conditional | possible new evidence, requires caution |
| UNSTABLE | stable | possible sample-specific repair |
| CONFLICT | remains conflict | robust negative relationship |
| INSUFFICIENT | sufficient | coverage improvement |

Questions:

- Which evidence cells migrate upward?
- Which migrate downward?
- Which new cells become testable only because V2 broadens coverage?

### 4. Robustness Impact

Compare:

- ETF-level pooling reversal rate;
- batch-level consistency;
- style-level consistency;
- regime-segment consistency;
- horizon robustness;
- sensitivity to high-beta themes;
- sensitivity to commodity/resource cyclicals.

Questions:

- Does V2 reduce the ETF-level pooling reversal warning?
- Does V2 increase heterogeneity by adding more specialized ETFs?
- Are Phase 3.5B caveats still active?

### 5. New Style-Regime Relationships

V2 adds exposures underrepresented in V1:

- power / green power;
- dividend low-volatility;
- A50 and CSI2000 size extensions;
- semiconductor equipment;
- industrial machine / high-end equipment;
- oil and rare metals;
- consumer electronics.

Future evaluation should mark any new relationship as `NEW_V2_ONLY` until it is tested in a later robustness phase. New evidence must not be promoted directly into preview or execution.

### 6. Methodology Risk

Track:

- universe-dependence risk;
- small-sample risk;
- style classification risk;
- duplicate exposure risk;
- liquidity survivorship risk;
- regime date staleness risk;
- QDII exclusion boundary.

Questions:

- Does V2 improve external validity or only add another sample-specific result?
- Are new V2 effects driven by one sector cluster?
- Are results stable across replay batches?

## Required Future Outputs

Future execution should produce, at minimum:

```text
reports/universe_v2_replay/aggregate/v1_vs_v2_coverage_alignment.md
reports/universe_v2_replay/aggregate/v1_vs_v2_style_fit_comparison.md
reports/universe_v2_replay/aggregate/v1_vs_v2_evidence_migration.md
reports/universe_v2_replay/aggregate/v1_vs_v2_robustness_delta.md
reports/universe_v2_replay/aggregate/generalization_decision.md
```

## Decision States

Future generalization conclusion should use one of:

- `GENERALIZES_STRONGLY`
- `GENERALIZES_WITH_CAVEATS`
- `PARTIAL_GENERALIZATION`
- `DOES_NOT_GENERALIZE`
- `INCONCLUSIVE`

No decision state authorizes preview, ranking, score, strategy, or execution by itself.

## Current Phase 5.1 Verdict

This plan is complete enough to support a future Main-approved replay execution phase. It is not evidence that V2 generalizes. Replay execution remains `NOT_STARTED`.
