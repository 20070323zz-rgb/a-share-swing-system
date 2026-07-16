# Current Project State

## 1. Snapshot Metadata

- Project: A-Share Swing System
- Repository root: `<project_root>`
- State snapshot date: 2026-07-13
- State snapshot source: Tushare Minimal Staging Proof, PIT contract artifacts, and existing project context evidence.

This file is a human and Codex shared current project fact snapshot. It is not a history log, README replacement, or phase report.

## 2. Current Project Stage

- Engineering Maturity: approximately stable / operational
- Strategy Maturity: research validation stage
- Current Main Research Track: Regime & Risk Allocation

Current stage:

```text
工程系统基本成型
正式模型稳定运行观察
Shadow / Research 正在验证自适应 Regime Layer
Regime Layer Phase 3.5 - Style Fit Robustness Audit COMPLETE
Style Fit Research Phase COMPLETE
Universe Evolution Phase 4.1 COMPLETE
Universe Evolution Phase 4.2 COMPLETE
Universe V2 CANDIDATE / QUALIFIED
Universe V2 Research Universe READY_FOR_REPLAY_PREPARATION
Research Generalization Phase 5.1 COMPLETE
Universe V2 Replay Planning COMPLETE
Research Generalization Phase 5.2 COMPLETE
Universe V2 Replay COMPLETE
Generalization Analysis COMPLETE
Generalization Verdict FAILED_GENERALIZATION
Research Generalization Phase 5.3 COMPLETE
Failure Attribution COMPLETE
Style Fit Cross-Universe Generalization FAILED
Style Fit Current Treatment V1-SPECIFIC_FINDING
Style Framework 2.0 Phase A COMPLETE
Exposure Framework Feasibility Study COMPLETE
Exposure Framework Phase B COMPLETE
Exposure Taxonomy DESIGNED
Exposure Data Contract DESIGNED
Exposure Point-in-Time Rules DESIGNED
Exposure Framework Phase C COMPLETE
Exposure Prototype COMPLETE
Exposure Prototype Scope NARROW_PRICE_LIQUIDITY_ONLY
Exposure Framework Phase D COMPLETE
Exposure Validation COMPLETE
Exposure Research Readiness PARTIAL_READY
Exposure Framework Phase E-A COMPLETE
Market Exposure Redesign COMPLETE
Market Exposure Framework MULTI_BENCHMARK_RECOMMENDED
Exposure Framework Phase E-B COMPLETE
Market Exposure Engineering Prototype COMPLETE
Market Exposure Vector RESEARCH_ONLY
Market Exposure Explanatory Verdict ADDS_EXPLANATORY_DIMENSION
Benchmark Redundancy Verdict LOCALIZED_HIGH_REDUNDANCY
Exposure Framework Phase F COMPLETE
Exposure Governance COMPLETE
Exposure Framework Phase 1 COMPLETE
Price-Derived Exposure Expansion FROZEN
Portfolio Research Integration ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research NOT_STARTED
Signal Integration BLOCKED
Project Infrastructure Batch Standardization V1 COMPLETE
Batch Standard Version V1
Paper Execution Safety Phase 1 COMPLETE
Paper Execution Freshness Gate ACTIVE
Guarded Paper Execution Entry ACTIVE
Stale Data Fallback BLOCKED
2026-07-10 Stale Trades AUDITED_NON_DESTRUCTIVELY
Tushare 5000 Data Foundation Audit COMPLETE
Reports Governance Phase A NOT_STARTED
Report File Migration BLOCKED
Data Foundation Upgrade NOT_STARTED
PR #1 Hygiene Cleanup COMPLETE
PR #1 Diff Check CLEAN
Local Temporary Artifacts RESOLVED
July 2026 Project Checkpoint COMPLETE
PR #1 MERGED
Post-Merge Validation PASS
Main Branch STABLE
Main Branch Merge COMPLETE
Tushare Minimal Staging Proof & PIT Contract COMPLETE
Tushare Staging / PIT COMPLETE_WITH_LIMITATIONS
Style Framework 2.0 Status FEASIBILITY_STUDY_COMPLETE
Exposure Framework Development RESEARCH_ONLY_PROTOTYPE_COMPLETE
Preview Research NOT_STARTED
Formal Execution BLOCKED
```

## 3. Formal Model State

- Formal model unchanged.
- `mid_trend = 70%`
- `short_swing = 30%`
- Uses BUY / WATCH / SELL framework.
- Paper simulation active.
- ETF-first.
- Total stock exposure `<= 10%`.

Regime Layer has not changed formal execution.

Style Fit has not changed BUY ranking or raw ranking scores.

## 4. Completed Regime/Risk Phases

| Phase | Name | Status |
| --- | --- | --- |
| Phase 1 | ETF Realized Risk Profile | COMPLETE |
| Phase 1.5 | Style + Structural Risk Profile | COMPLETE |
| Phase 2 | Market Regime Audit & Historical Replay | COMPLETE |
| Phase 2.5 | Regime Stabilization Research | COMPLETE |
| Phase 3 | Style-Regime Fit Research | COMPLETE |
| Phase 3.5A | Style Fit Robustness Core Audit | COMPLETE |
| Phase 3.5B | Robustness Decision & Evidence Qualification | COMPLETE |
| Phase 3.5C | Style Fit Research Governance | COMPLETE |
| Phase 4.1 | Universe V2 Candidate Design & Versioning | COMPLETE |
| Phase 4.2 | Universe V2 Candidate Qualification | COMPLETE |
| Phase 5.1 | Universe V2 Replay Preparation | COMPLETE |
| Phase 5.2 | Universe V2 Full Replay & V1 vs V2 Comparison | COMPLETE |
| Phase 5.3 | Style Fit Failure Attribution | COMPLETE |
| Style Framework 2.0 Phase A | Exposure Framework Feasibility Study | COMPLETE |
| Exposure Framework Phase B | Taxonomy + Data Contract + Point-in-Time Rules | COMPLETE |
| Exposure Framework Phase C | Narrow Prototype Development | COMPLETE |
| Exposure Framework Phase D | Exposure Validation | COMPLETE |
| Exposure Framework Phase E-A | Market Exposure Redesign | COMPLETE |
| Exposure Framework Phase E-B | Multi-Benchmark Market Exposure Prototype | COMPLETE |
| Exposure Framework Phase F | Exposure Governance & Portfolio Role Definition | COMPLETE |
| Project Infrastructure | Batch Standardization V1 | COMPLETE |
| Paper Execution Safety Phase 1 | Freshness Gate & Non-Destructive Audit | COMPLETE |
| Data Foundation Validation | Tushare Minimal Staging Proof & PIT Contract | COMPLETE |

## 5. Current Research Architecture

```text
Market Regime
↓
ASYMMETRIC_CONFIRM shadow stabilization
↓
Style-Regime Fit
↓
Evidence Qualification
↓
Research Governance
↓
Future research-only preview scope
↓
mid_trend + short_swing
↓
BUY Ranking
```

Style Fit evidence is now cell-level qualified. Raw Phase 3 `SUPPORTED` / `CONFLICT` labels must not be treated as equal-confidence evidence.

## 6. Selected Shadow Regime

- selected candidate: `ASYMMETRIC_CONFIRM`
- shadow-only: true
- research-only: true
- not formal execution

Latest known snapshot:

```text
latest_data_date = 2026-07-10
latest_known_regime_date = 2026-07-06
raw regime as of 2026-07-06 = NEUTRAL
selected shadow regime as of 2026-07-06 = NEUTRAL
regime_snapshot_stale = true
```

This regime snapshot is stale relative to 2026-07-10 data. Do not describe it as the live current market regime.

## 7. Phase 3.5B Current Conclusions

From `reports/regime_layer_phase3_5b_decision.json`:

```text
style_fit_has_historical_support = true
style_fit_has_incremental_signal_value = true
style_fit_incremental_signal_value_robustness = PARTIALLY_ROBUST
incremental_signal_value_final_answer = YES_WITH_ROBUSTNESS_CAVEAT
ready_for_fit_shadow_observation = true
ready_for_adjusted_preview_research = true
ready_for_preview = false
ready_for_execution = false
execution_allowed = false
```

Incremental signal value remains true, but robustness is qualified: `PARTIALLY_ROBUST` due to ETF-level pooling reversal warnings.

Qualification counts:

```text
QUALIFIED_SUPPORT = 1
CONDITIONAL_SUPPORT = 6
DESCRIPTIVE_ONLY = 11
UNSTABLE = 2
QUALIFIED_CONFLICT = 1
CONDITIONAL_CONFLICT = 3
INSUFFICIENT = 12
```

HIGH_BETA_THEME final interpretation:

```text
MULTI_REGIME_SUPPORT_NOT_QUALIFIED
flags = ['SAMPLE_DEPENDENCE_RISK']
```

COMMODITY_CYCLICAL final interpretation:

```text
CONDITIONAL_MULTI_REGIME_SUPPORT
flags = ['TRUE_MULTI_REGIME_BEHAVIOR']
```

Future preview research scope is defined, but no adjusted preview is created. Score bonus and score penalty are not authorized.

## 7A. Phase 3.5C Governance Conclusions

From `reports/style_fit_governance_framework.md` and `reports/style_fit_permission_matrix.md`:

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

Governance permissions:

- `QUALIFIED_SUPPORT` and `CONDITIONAL_SUPPORT` may support future positive filter research only after Main approval.
- `QUALIFIED_CONFLICT` and `CONDITIONAL_CONFLICT` may support future negative filter research only after Main approval.
- `DESCRIPTIVE_ONLY`, `UNSTABLE`, and `INSUFFICIENT` are excluded from future directional filter research.
- No evidence category maps directly to BUY ranking, score bonus, score penalty, preview, strategy, or execution.

## 8. Open Research Risks

Current unresolved issues:

- ETF-level pooling reversal remains an active major robustness warning.
- `HIGH_BETA_THEME` still carries sample dependence risk.
- Cell-level evidence heterogeneity means future research may only use qualified evidence cells.
- DESCRIPTIVE_ONLY / UNSTABLE / INSUFFICIENT cells are excluded from future preview filter research.

## 8A. Universe V2 Status

From `configs/universe_versions/universe_v1.yaml`, `configs/universe_versions/universe_v2_candidate.yaml`, `configs/universe_versions/universe_v2_registry.yaml`, `reports/universe_v2_coverage_gap_analysis.md`, `reports/universe_v2_expansion_plan.md`, `reports/universe_v2_candidate_qualification.md`, and `reports/universe_registry.md`:

```text
Universe V1 = LOCKED_HISTORICAL_BASELINE
Universe V2 Candidate = QUALIFIED
Universe V2 Research Universe = READY_FOR_REPLAY_PREPARATION
Universe V2 Replay Planning = COMPLETE
Universe V2 Replay = COMPLETE
Generalization Analysis = COMPLETE
Generalization Verdict = FAILED_GENERALIZATION
Universe V2 Trade Pool Activation = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Universe V1 remains the binding universe for Phase 3 and Phase 3.5 conclusions.

V2 qualification reviewed 36 named candidates:

```text
QUALIFIED_RESEARCH = 16
OBSERVE = 15
REJECT = 5
```

All 36 candidates exist in the unified ETF daily database `data/etf_daily/` and are current through 2026-07-08. No second ETF data store or copied V2 daily data exists.

V2 is not connected to preview, trade activation, or execution. Phase 5.2 has completed a research-only V2 replay and V1 vs V2 comparison; a future Main-approved decision is required before any Preview Research transition.

Phase 5.1 established:

```text
Replay batch plan = reports/universe_v2_replay_plan.md
Checkpoint/recovery plan = reports/replay_checkpoint_plan.md
Generalization evaluation plan = reports/generalization_evaluation_plan.md
Operational playbook = docs/operational_playbook.md
```

## 8B. Phase 5.2 Generalization Results

From `reports/universe_v2_full_replay.md`, `reports/v1_vs_v2_generalization.md`, and `reports/generalization_verdict.md`:

```text
Phase 5.2 = COMPLETE
Universe V2 Replay = COMPLETE
Replay ETF Count = 16 QUALIFIED_RESEARCH
Replay Range = 2025-05-30 to 2026-07-06
Forward Rows = 20,880
Robustness Base Rows = 4,272
Only QUALIFIED_RESEARCH used = true
QDII included = false
Single ETF data source = true
Generalization Verdict = FAILED_GENERALIZATION
Phase 3 Research Impact After V2 = CHALLENGED
Methodology Risk = MEDIUM
Coverage Risk = LOW
Engineering Risk = LOW
```

V2 evidence counts:

```text
QUALIFIED_SUPPORT = 4
CONDITIONAL_SUPPORT = 4
DESCRIPTIVE_ONLY = 9
UNSTABLE = 3
QUALIFIED_CONFLICT = 1
CONDITIONAL_CONFLICT = 0
INSUFFICIENT = 15
```

V2 robustness summary:

```text
Time Robustness = FRAGILE
ETF-level Robustness = PARTIAL_SUPPORT
Segment Robustness = FRAGILE
Horizon Robustness = CONFLICTING
Incremental Value Robustness = CONFLICTING
Major Robustness Warning = true
Phase 3 original conclusion still directionally supported = false
Phase 3 incremental value still directionally supported = false
```

Evidence migration:

```text
UNCHANGED = 24
UPGRADED = 3
DOWNGRADED = 3
CHANGED_DIRECTION_OR_CATEGORY = 6
```

The failed generalization verdict is a research result, not an engineering failure. Replay completed successfully and used the unified ETF daily database, but Universe V2 did not recover enough robustness to support automatic continuation into Preview Research.

## 8C. Phase 5.3 Failure Attribution

From `reports/style_fit_failure_attribution.md`, `reports/style_fit_failure_tree.md`, and `reports/style_fit_failure_postmortem.md`:

```text
Phase 5.3 = COMPLETE
Failure Attribution = COMPLETE
Generalization Verdict Explained = true
Primary Causes = Universe Shift, Horizon Conflict, Methodology Limitation, Style Instability
Style Fit Cross-Universe Generalization = FAILED
Style Fit Current Treatment = Universe V1-specific historical finding
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Failure tree:

```text
Universe Shift = HIGH contribution / HIGH confidence
Horizon Conflict = HIGH contribution / HIGH confidence
Methodology Limitation = HIGH contribution / MEDIUM confidence
Style Instability = HIGH contribution / MEDIUM confidence
Cell Migration = MEDIUM contribution / HIGH confidence
Regime Instability = MEDIUM contribution / MEDIUM confidence
Unknown / Residual = LOW contribution / MEDIUM confidence
```

Top interpreted channels:

```text
BOND coverage loss: V2 has no BOND qualified research ETF, so V1 bond support cannot be recovered.
HIGH_BETA_THEME: largest V2 style exposure; OFFENSIVE/DEFENSIVE conditional support remains, but NEUTRAL is unstable.
COMMODITY_CYCLICAL: retains conditional multi-regime behavior but is sample-dependent.
SECTOR_DEFENSIVE: OFFENSIVE and DEFENSIVE cells flip from V1 conflict to V2 support.
NEUTRAL regime: concentrates downgraded / unstable / conflict outcomes.
Horizon behavior: 1d, 3d, and 20d conflict with expected supported-vs-conflict ordering.
```

Phase 5.3 did not modify Formal Execution, Shadow, Preview, Strategy, Ranking, Score, Style Mapping, Regime Logic, Universe V1, or Universe V2. It also did not download data or rerun replay for optimization.

## 8D. Style Framework 2.0 Phase A

From `reports/exposure_framework_feasibility_study.md`, `reports/exposure_candidate_matrix.md`, and `reports/exposure_gap_analysis.md`:

```text
Style Framework 2.0 Phase A = COMPLETE
Exposure Framework Feasibility = POSITIVE_WITH_DATA_GAPS
Style Framework 2.0 Status = FEASIBILITY_STUDY_COMPLETE
Style Framework 2.0 Development = NOT_STARTED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Exposure Framework interpretation:

```text
Exposure = measurable ETF sensitivity or structural linkage to economic drivers, risk factors, asset class, sector, theme, or implementation properties.
Style = compressed naming layer.
Theme = narrative/product identity that requires taxonomy before becoming exposure.
Factor = systematic characteristic and one subset of exposure.
Industry/Sector = business classification and one possible source of exposure.
```

Admission standards:

```text
Economic Meaning
Point-in-Time Validity
Stability
Maintainability
Measurability
Non-redundancy
Cross-universe robustness potential
Separability from strategy/ranking
Confidence governance
Versioning
```

Most feasible current exposure candidates:

```text
Market Beta
Realized Volatility
Liquidity
Momentum
Drawdown / downside risk
```

Major database gaps:

```text
Benchmark index mapping
Index methodology
Fund holdings and constituent weights
Industry / sector / theme taxonomy
Factor fundamentals
Fund AUM
Bond duration / yield / credit spread
Commodity and FX benchmark data
```

Recommended research route:

```text
Route C = Exposure + Clustering
Sequence = economic taxonomy first, point-in-time data contracts second, clustering as validation third, cross-universe validation before preview.
```

Phase A did not start development, replay, preview, or execution.

## 8E. Exposure Framework Phase B

From `reports/exposure_taxonomy_design.md`, `reports/exposure_data_contract.md`, `reports/exposure_point_in_time_rules.md`, and `reports/exposure_phase_c_readiness.md`:

```text
Exposure Framework Phase B = COMPLETE
Exposure Taxonomy = DESIGNED
Exposure Data Contract = DESIGNED
Exposure Point-in-Time Rules = DESIGNED
Exposure Phase C Readiness Gate = DESIGNED
Exposure Framework Development = NOT_STARTED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Exposure taxonomy level-1 categories:

```text
Market / Size Exposure
Risk / Volatility Exposure
Liquidity / Tradability Exposure
Momentum / Trend Exposure
Dividend / Value Exposure
Commodity / Resource Exposure
Interest Rate / Bond Sensitivity
Sector / Industry Exposure
Theme / Innovation Exposure
Concentration / Diversification Exposure
```

Phase C readiness:

```text
READY_FOR_PHASE_C:
- market_beta
- realized_volatility
- downside_drawdown_risk
- trading_liquidity
- return_momentum

NEEDS_DATA_BEFORE_PHASE_C:
- size_segment
- commodity_resource_sensitivity
- interest_rate_bond_sensitivity
- concentration_proxy
- value_factor
- growth_factor

DESCRIPTIVE_ONLY_OR_DEFER:
- dividend_intent as quantitative yield exposure
- sector_industry_tag
- technology_innovation_tag
- manufacturing_upgrade_tag
- ai_digital_theme_tag
- qdii_fx_cross_border
```

Point-in-time rules:

```text
Only data known at calculation date T may be used.
Event date, data_as_of_date, data_available_date, ingestion_date, and calculation_date must be separated.
Fields without reliable data_available_date cannot enter strict replay calculation.
Rolling calculations require warm-up and must end at T.
Future returns, future classifications, future holdings, and future constituents are forbidden.
Non-PIT-safe exposures must be DESCRIPTIVE_ONLY or NOT_PIT_SAFE.
```

Phase B did not calculate exposure scores, start replay, modify Universe, or connect exposure to ranking/score/preview/execution.

## 8F. Exposure Framework Phase C

From `src/exposure/exposure_calculator.py`, `scripts/run_exposure_prototype.py`, `reports/exposure_prototype_summary.md`, and `reports/exposure_prototype_data_quality.md`:

```text
Exposure Framework Phase C = COMPLETE
Exposure Prototype = COMPLETE
Exposure Prototype Scope = NARROW_PRICE_LIQUIDITY_ONLY
Universe Version = universe_v2_qualified_research
Calculation Date = 2026-07-08
ETF Count = 16
Value Rows = 240
Missing Rows = 0
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Approved exposure scope:

```text
market_beta
realized_volatility
downside_drawdown_risk
trading_liquidity
return_momentum
```

Prototype output files:

```text
data/research/exposure_prototype/exposure_prototype_values.csv
data/research/exposure_prototype/exposure_prototype_wide.csv
data/research/exposure_prototype/exposure_prototype_missing_data.csv
data/research/exposure_prototype/exposure_prototype_universe_coverage.csv
data/research/exposure_prototype/exposure_prototype_manifest.json
reports/exposure_prototype_summary.md
reports/exposure_prototype_data_quality.md
```

PIT and governance notes:

```text
All rolling windows end at calculation_date.
No forward returns are read or generated.
market_beta uses 510300 as a PIT-safe broad-market proxy and is confidence-capped by window.
All outputs include universe_version, lookback_window, point_in_time_status, confidence_level, and missing_data_flag.
ETF daily data remains single source of truth under data/etf_daily/.
ETF daily data was not copied.
No exposure was connected to BUY ranking, score, preview, strategy, or formal execution.
```

The Phase C prototype uses the 16 `QUALIFIED_RESEARCH` A-share ETFs from Universe V2. `OBSERVE`, `REJECT`, and QDII candidates remain excluded.

## 8G. Exposure Framework Phase D

From `reports/exposure_validation_summary.md`, `reports/exposure_window_stability.md`, `reports/exposure_redundancy_analysis.md`, and `reports/exposure_research_readiness.md`:

```text
Exposure Framework Phase D = COMPLETE
Exposure Validation = COMPLETE
Exposure Research Readiness = PARTIAL_READY
Universe Version = universe_v2_qualified_research
Calculation Date = 2026-07-08
ETF Count = 16
Value Rows = 240
Missing Rows = 0
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Coverage validation:

```text
All 5 Phase C exposures cover all 16 ETFs.
Missing values = 0.
Confidence HIGH = 224 rows.
Confidence MEDIUM = 16 rows.
PIT_SAFE = 208 rows.
PIT_SAFE_WITH_PROXY = 32 rows, all from market_beta.
```

Window stability:

```text
market_beta = STABLE
realized_volatility = STABLE
downside_drawdown_risk = PARTIALLY_STABLE
trading_liquidity = STABLE
return_momentum = PARTIALLY_STABLE
```

Research readiness:

```text
READY_FOR_RESEARCH_OBSERVATION:
- realized_volatility
- downside_drawdown_risk
- trading_liquidity
- return_momentum

NEEDS_REFINEMENT:
- market_beta
```

Market beta treatment:

```text
market_beta remains provisional.
510300 is usable as a PIT-safe broad A-share proxy, but it is not sufficient as a final V2 universe market proxy.
Future research should evaluate multi-benchmark beta for large/core, small/mid, STAR/technology, resource/commodity, and defensive/dividend exposures.
```

Governance boundary:

```text
No exposure validation result is connected to Preview, Ranking, Score, Strategy, Shadow, or Formal Execution.
No exposure formula was changed.
No Replay was started.
Universe V1 and Universe V2 were not modified.
```

## 8H. Project Infrastructure - Batch Standardization V1

From `docs/project_batch_standard.md` and `docs/templates/`:

```text
Project Infrastructure = ACTIVE
Batch Standardization V1 = COMPLETE
Batch Standard Version = V1
Batch Types = Research, Engineering, Validation, Governance
Standard Header = DESIGNED
Standard Nine-Section Structure = DESIGNED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Batch templates:

```text
docs/templates/research_batch_template.md
docs/templates/engineering_batch_template.md
docs/templates/validation_batch_template.md
docs/templates/governance_batch_template.md
```

Standard batch sections:

```text
1. Context
2. Objective
3. Scope
4. Inputs
5. Method
6. Deliverables
7. Validation
8. State Transition
9. Chinese Summary
```

Governance boundary:

```text
Batch Standardization V1 is process infrastructure only.
No Strategy, Ranking, Score, Preview, Shadow, Formal Execution, Replay, Universe, Exposure formula, or model logic was changed.
Future batches should use the standard header and the template matching the declared Batch Type.
```

## 8I. Exposure Framework Phase E-A - Market Exposure Redesign

From `reports/market_exposure_redesign.md`, `reports/multi_benchmark_framework.md`, and `reports/market_exposure_data_contract.md`:

```text
Exposure Framework Phase E-A = COMPLETE
Market Exposure Redesign = COMPLETE
Single Benchmark Framework = RETAIN_AS_BASELINE_ONLY
Multi-Benchmark Framework = RECOMMENDED
Market Exposure Engineering Prototype = NOT_STARTED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Research conclusion:

```text
market_beta was not rejected as a concept.
The rejected design is single-benchmark interpretation against 510300 only.
Market Exposure should be represented as market_exposure_vector: one ETF x one benchmark x one lookback window x one calculation date.
```

Candidate benchmark families:

```text
large_core: CSI 300 / 510300
large_blue_chip: SSE 50 / 510050
mid_cap: CSI 500 / 510500
small_cap: CSI 1000 / 512100 or equivalent
growth_board: ChiNext / 159915
star_technology: STAR 50 / 588000
dividend_defensive: dividend or dividend-low-vol proxy
resource_cyclical: needs benchmark selection
sector_family: defer to sector framework
```

Data contract status:

```text
market_exposure_vector data contract = DESIGNED
Engineering Prototype Readiness = READY_FOR_RESEARCH_ONLY_PROTOTYPE_DESIGN
Engineering Prototype = NOT_STARTED
```

The `NOT_STARTED` value above records the Phase E-A close state. It is superseded by the completed Phase E-B prototype in Section 8J.

Governance boundary:

```text
No code was modified.
No exposure formula was changed.
No new exposure value was calculated.
No Replay was started.
No Strategy, Ranking, Score, Preview, Shadow, Formal Execution, Universe, or model logic was changed.
```

## 8J. Exposure Framework Phase E-B - Multi-Benchmark Market Exposure Prototype

From `src/exposure/market_exposure_vector.py`, `scripts/run_market_exposure_vector.py`, `reports/market_exposure_vector_summary.md`, and `reports/benchmark_redundancy_analysis.md`:

```text
Exposure Framework Phase E-B = COMPLETE
Multi-Benchmark Market Exposure Prototype = COMPLETE
Market Exposure Vector = RESEARCH_ONLY
Universe Version = universe_v2_qualified_research
Calculation Date = 2026-07-08
ETF Count = 16
Benchmark Count = 6
Available Benchmarks = 6
Lookback Windows = 60d, 120d
Vector Rows = 192
Missing Rows = 0
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Benchmark basket V1:

```text
510300 = core_market
510500 = mid_cap
512100 = small_cap
159915 = growth
588000 = technology
510880 = defensive
```

Research result:

```text
Single 510300 vs Multi-Benchmark Verdict = ADDS_EXPLANATORY_DIMENSION
Rows with non-core R-squared improvement >= 0.05 = 20 / 32
120d ETFs with non-core R-squared improvement >= 0.05 = 10 / 16
Dominant benchmark consistency across 60d / 120d = 15 / 16 ETFs
Distinct 120d dominant benchmark families = 6
```

Benchmark redundancy:

```text
Benchmark Redundancy Verdict = LOCALIZED_HIGH_REDUNDANCY
HIGH pair-window rows = 3 / 30
510500 vs 512100 = HIGH at 60d and 120d
510300 vs 159915 = HIGH at 60d only
```

Interpretation limits:

```text
Best benchmark is relative statistical fit, not economic classification.
561360 lacks a resource/cyclical benchmark; its current defensive fit must not be treated as a defensive label.
159516 remains weakly explained by basket V1.
510500 and 512100 require future redundancy-versus-differentiation validation.
No predictive claim was made.
```

Governance boundary:

```text
The existing Phase C exposure formula and artifacts were not modified.
No beta was normalized to sum to 1.
No Replay was started.
No trading signal was generated.
No Strategy, Ranking, Score, Preview, Shadow, Formal Execution, Universe, or paper execution logic was changed.
```

## 8K. Exposure Framework Phase F - Governance & Portfolio Role

From `reports/exposure_governance_framework.md`, `reports/exposure_permission_matrix.md`, `reports/exposure_portfolio_role_definition.md`, and `docs/research/exposure_framework_phase1_journal.md`:

```text
Exposure Framework Phase F = COMPLETE
Exposure Governance = COMPLETE
Exposure Framework Phase 1 = COMPLETE
Price-Derived Exposure Expansion = FROZEN
Portfolio Research Integration = ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research = NOT_STARTED
Portfolio Allocation Logic = NOT_STARTED
Signal Integration = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
```

Formal system role:

```text
Exposure Layer = measurable, PIT-aware risk and market-driver description
Alpha / Signal Layer = NOT_EXPOSURE_ROLE
Portfolio Layer = conditional diagnostic research consumer only
Risk Layer = conditional diagnostic research consumer only
Exit Layer = exposure cannot act as a direct trigger
```

Current readiness:

```text
READY_FOR_PORTFOLIO_RESEARCH:
- market_exposure_vector
- realized_volatility
- downside_drawdown_risk
- trading_liquidity

READY_FOR_RESEARCH_OBSERVATION:
- return_momentum
```

`READY_FOR_PORTFOLIO_RESEARCH` means eligible for a separate diagnostic research-design batch. It does not authorize optimizer, risk budget, target weights, position sizing, ranking, score, signal, preview, or execution changes.

Freeze boundary:

```text
No new price-derived exposure names, windows, formulas, benchmark additions, or composite scores.
Deterministic refresh, bug-fix validation, recovery audit, and approved research observation remain allowed.
Reopen requires PIT-safe data improvement, material validation failure, or a specific Main-approved research need.
Fundamental Exposure Development = NOT_STARTED
```

Governance boundary:

```text
No exposure formula or exposure family was changed.
No Portfolio Allocation or Exit Logic was developed.
No Strategy, Ranking, Score, BUY/WATCH/SELL, Regime, Universe, Preview, Shadow, Formal, Replay, or paper execution logic was changed.
```

## 8L. Paper Execution Safety Phase 1

From `src/execution/paper_freshness_gate.py`, `scripts/run_paper_execution_guarded.py`, `reports/paper_execution_preflight.json`, `reports/paper_execution_freshness_gate_summary.md`, and `data/audit/paper_execution_audit.jsonl`:

```text
Paper Execution Safety Phase 1 = COMPLETE
Paper Execution Freshness Gate = ACTIVE
Guarded Paper Execution Entry = ACTIVE
Stale Data Fallback = BLOCKED
2026-07-10 Stale Trades = AUDITED_NON_DESTRUCTIVELY
Paper Execution Strategy Logic = UNCHANGED
Formal Execution Logic Change = NONE
Data Foundation Upgrade = NOT_STARTED
```

The guarded entry checks the expected trading date, market data date, failed and pending update counts, dynamic formal ETF universe coverage, signal date, ranking date, proposed-trade bars, and critical input structure. Any non-PASS result prevents the existing paper trade engine from being invoked. It never falls back to a previous trading day's price.

Active entrypoints:

```text
scripts/run_daily_close.sh -> scripts/run_paper_execution_guarded.py
App run_paper_engine_dryrun -> scripts/run_paper_execution_guarded.py
PASS only -> src/paper_trade_engine.py
```

The latest real repository preflight for 2026-07-10 is `BLOCKED_STALE_SIGNAL`: market data and 63/63 dynamic formal ETF symbols cover 2026-07-10, but signals and ranking remain dated 2026-07-09. `engine_invoked=false`.

The three 2026-07-10 stale-price records for 512800, 516510, and 159929 are preserved unchanged and recorded in append-only audit evidence. No correction, replacement trade, cash rewrite, or position rewrite was performed.

Validation:

```text
Unit/integration tests = 15 PASS
Python compilation = PASS
run_daily_close shell syntax = PASS
Protected file hashes unchanged = true
```

The separately authorized Tushare 5000 Data Foundation Audit is `COMPLETE` after Main review. Capability and priority artifacts are available. No Tushare data integration or data-source upgrade has started; `Data Foundation Upgrade = NOT_STARTED`.

Reports Governance Phase A remains `NOT_STARTED`: the taxonomy feasibility study exists, but the catalog generator, catalog outputs, dependency summary, and Path Registry design required by Phase A do not exist. Report migration remains `BLOCKED`.

PR #1 final hygiene cleanup is `COMPLETE`. PR #1 was merged into `main` with merge commit `40a6017402456d62609169325cb5f1d31a1a140b` at 2026-07-13 09:49:26 CST. Post-merge validation is `PASS` and `main` is `STABLE`. Formal execution logic, protected paper ledgers, and ETF business data were unchanged by the merge/validation batch.

## 8M. Tushare Minimal Staging Proof & PIT Contract

The separately authorized proof completed run `real-20260713-minimal-proof-v3` with 17 real API requests under the configured limit of 30. `index_basic`, `index_daily`, `index_weight`, `index_classify`, `index_member_all`, `daily_basic`, `fund_portfolio`, and `shibor` all returned accessible real data and passed the configured schema checks.

```text
Tushare Minimal Staging Proof = COMPLETE
Tushare PIT Contract = COMPLETE_WITH_LIMITATIONS
Evidence Isolation = COMPLETE
PR #2 = MERGED
Accessible interfaces = 8 / 8
Real API requests = 17 / 30
Aggregate real API calls = 51 (AGGREGATE_BUDGET_WARNING)
Mock calls included in real totals = 0
Formal Staging Architecture = NOT_STARTED
Tushare Primary Upstream = APPROVED_PRIMARY_UPSTREAM
Decision Evidence Confidence = LIMITED_TWO_DAY_EVIDENCE
Decision Authority = USER_AUTHORIZED_EARLY_PROMOTION
Tushare Primary Upstream Migration = AUTHORIZED_NOT_STARTED
ETF Daily Availability Timing Audit = ACTIVE_COLLECTING
Timing Optimization = ACTIVE
Data Foundation Upgrade = NOT_STARTED
Data Promotion = BLOCKED_PENDING_IMPLEMENTATION_VALIDATION
Unified Data Upgrade = NOT_STARTED
Exposure Phase 2 = NOT_STARTED
Regime 2.0 = NOT_STARTED
Universe V3 = NOT_STARTED
Exit Logic = NOT_STARTED
Style Fit 1.0 = CLOSED
Next Decision = Timing-window and safety-buffer optimization only; source selection is closed
```

PIT handling is intentionally asymmetric: `fund_portfolio` is `PIT_RESOLVED` through retained `ann_date` versions; `daily_basic` and `index_daily` use a conservative next-trading-day contract when the next date exists; Shibor uses official release `11:00` plus the project's 60-minute conservative lag to `12:00` with basis `OFFICIAL_11AM_PLUS_PROJECT_LAG`; `index_weight` and `index_member_all` remain partial; current taxonomy and index metadata remain unresolved for historical publication time. The latest 2026-07-10 daily rows remain partial until a later local trading-calendar date is present. Shibor remains `EXPLANATION_ONLY / INTEREST_RATE_CONTEXT`, not ETF duration exposure.

All historical real payloads and row-level proof artifacts remain in their existing Git-ignored run directories and were not moved or rewritten. New runs are programmatically separated under `real/<real-run_id>/` and `mock/<mock-run_id>/`, including mode-scoped report evidence. Mock runs cannot read the Token provider, create the production client, emit real permission verdicts, produce `REAL_PROOF_COMPLETE`, overwrite global real reports, or enter the attested real call total. `data/etf_daily/` remains the ETF price Single Source of Truth. No staged response was promoted into Replay, Exposure Phase 2, Strategy, Ranking, Preview, Shadow, Formal, or paper execution.

Three real-run attestations explain `17 + 17 + 17 = 51` calls. The first two individual proof reports were not retained by the historical global-report workflow, so their report hashes are explicitly `UNAVAILABLE / AVAILABLE_EVIDENCE_LIMITED`; no missing evidence was fabricated. The final `index_weight` reduction from 1350 raw rows to 900 proof rows is `PROOF_SAMPLE_DATE_WINDOW_REDUCTION`: the 2026-04-30 snapshot was excluded and the 2026-05-29 and 2026-06-30 snapshots were retained for all three indices.

PR #2 was merged into `main` with merge commit `47d129bfa7a055b7af81f4c57fea3a95d41287c6` at 2026-07-14 14:00:33 CST after the live head and boundary gate remained unchanged. Post-merge validation is `PASS`, `main` is `STABLE`, and Tushare proof evidence is `ACCEPTED`. The ETF SSOT, protected files, model, Replay, Ranking, Score, Exposure, and Formal Execution boundaries were unchanged. No real Tushare API call was made during validation.

## 8N. Tushare ETF Daily Availability Timing Audit

The independently authorized post-close availability observer is implemented on branch `agent/tushare-etf-availability-audit` and is collecting evidence. It dynamically maps all 183 canonical ETF files to Tushare codes and roles, uses Tushare `trade_cal` rather than weekday inference, and calls `fund_daily` once per executed Tushare slot. The user has approved Tushare as the primary upstream architecture decision. This is not a completed migration and does not authorize formal promotion.

```text
ETF Daily Availability Timing Audit = ACTIVE_COLLECTING
Observation Days Started = 2
Observation Days Completed = 2
Statistical Evidence Verdict = INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION
Tushare = APPROVED_PRIMARY_UPSTREAM
Decision Evidence Confidence = LIMITED_TWO_DAY_EVIDENCE
Decision Authority = USER_AUTHORIZED_EARLY_PROMOTION
BaoStock = RECONCILIATION_ONLY
data/etf_daily = CANONICAL_SSOT
Tushare Primary Upstream Migration = AUTHORIZED_NOT_STARTED
Data Foundation Upgrade = NOT_STARTED
Data Promotion = BLOCKED_PENDING_IMPLEMENTATION_VALIDATION
Timing Optimization = ACTIVE
Formal Execution Logic = UNCHANGED
```

Probe manifests and normalized snapshots are append-only and Git-ignored under `data/staging/tushare_etf_availability/`. Only sanitized mapping and timing summaries are committed. The observer does not call `run_daily_close.sh`, the Freshness Gate, or the paper engine. Five valid days can support only preliminary timing optimization; ten valid days remain the supported timing-candidate gate. Neither gate reopens the Tushare architecture decision.

The two preserved real trading days, 2026-07-14 and 2026-07-15, both remained empty through 16:00, reached 183/183 with full field quality at 16:15, and stayed hash-identical through 18:00. Under the activated confirmation-point rule, `FIRST_AVAILABLE=16:15`, `FIRST_COMPLETE=16:15`, and `FIRST_STABLE=16:30`. The original raw statistics and the prior retrospective 16:15 stability interpretation remain documented in `reports/tushare_primary_upstream_source_decision_2026-07-15.md`.

From 2026-07-16, core probes run at 16:00, 16:05, 16:10, 16:15, 16:30, and 17:00. The 17:30 and 18:00 slots run conditionally when stability is unresolved or invalidated. The 15:30 point is no longer a daily Availability timing slot; it is retained only for explicit low-frequency interface health checks and excluded from FIRST_AVAILABLE/COMPLETE/STABLE.

Draft PR #3 tracks the framework, decision report, schedule change, and accumulating sanitized timing summaries on branch `agent/tushare-etf-availability-audit`. Its state is `DRAFT_AWAITING_DECISION_QC`; it must not be merged in this batch.

## 8O. Reports Governance Phase A-R

Draft PR #5 cleanly rebuilds report governance without merging or cherry-picking PR #4. PR #4 is `CLOSED / SUPERSEDED / NOT MERGED`. Its candidate conclusions are rejected; only independently validated design semantics and the 43 false-negative regression facts are retained.

```text
Reports Governance Phase A-R = ACTIVE / ARCHITECTURE_ACCEPTED
PR #5 = READY_FOR_REVIEW / MERGE_READY
Report Inventory = 651 / REFRESHED_QC_PASS
Structured Scanner = REMEDIATED_QC_PASS
Backstop Scanner = REMEDIATED_QC_PASS
Structured References = 2593
Backstop Query Records = 5208
Governance Evidence Records = 12416
PR #4 Active-Reference Regression Recall = 43/43
Scanner Disagreements = 9 / MATERIALIZED_FAIL_CLOSED_QC_PASS
Machine-Provisional Candidates = 49
Full Candidate Review = 49/49 PASS
Final Provisional Dry-Run Candidates = 49
PROVISIONALLY_SAFE_FOR_PHASE_B_DRY_RUN = 13
PROVISIONALLY_SAFE_RENAME_REQUIRED = 36
Archived / Active / Runtime / Unknown Candidate Contamination = 0
SAFE_TO_DELETE_AFTER_AUTHORIZATION = 0
Runtime Path Registry = NOT_STARTED
Reports Migration Phase B = BLOCKED
Zero Move = PASS
```

The provisional label authorizes only a future Phase B dry-run. No report has been moved, renamed, deleted, or rewritten. App/Dashboard paths, Formal Execution, logs, and Availability data remain unchanged. The v1 snapshot remains `VALID_HISTORICAL_SNAPSHOT / SUPERSEDED`; the authoritative v2 group hash is stored in `reports/governance/phase_ar/immutable_governance_snapshot_manifest_v2_2026-07-16.json`.

## 9. Current Main Bottlenecks

- Paper execution freshness is now guarded. The remaining 2026-07-10 question is correction-policy governance; original ledger rows remain unchanged and no correction is authorized.
- Future Preview Research has not started and requires separate Main approval.
- Real forward shadow samples are limited.
- Formal exit logic remains a major strategy bottleneck.
- Formal model is still research-unproven statistically.
- Longitudinal/out-of-sample Exposure observation remains incomplete.
- Basket V1 still lacks a resource/cyclical benchmark and does not strongly explain every sector/theme ETF.
- 510500 and 512100 show persistent high redundancy and need a retain/remove comparison.
- Portfolio Research is eligible for design but has not started.
- Future Main-authored batches should use Batch Standard V1 templates by default.

## 10. Project Context Persistence

```text
Project Context Persistence Phase = COMPLETE
```

New threads must still execute repository bootstrap before substantive edits.

## 11. Immediate Next Work

```text
Tushare 5000 Data Foundation Audit = COMPLETE
Reports Governance Phase A = NOT_STARTED
Report File Migration = BLOCKED
Preview Research = NOT STARTED
Formal Execution = BLOCKED
Exposure Framework Phase C = COMPLETE
Exposure Prototype = COMPLETE
Exposure Framework Phase D = COMPLETE
Exposure Validation = COMPLETE
Exposure Research Readiness = PARTIAL_READY
Exposure Framework Phase E-A = COMPLETE
Market Exposure Redesign = COMPLETE
Exposure Framework Phase E-B = COMPLETE
Market Exposure Engineering Prototype = COMPLETE
Market Exposure Vector = RESEARCH_ONLY
Exposure Framework Phase F = COMPLETE
Exposure Governance = COMPLETE
Exposure Framework Phase 1 = COMPLETE
Price-Derived Exposure Expansion = FROZEN
Portfolio Research Integration = ELIGIBLE_FOR_RESEARCH_DESIGN
Portfolio Research = NOT_STARTED
Signal Integration = BLOCKED
Project Infrastructure Batch Standardization V1 = COMPLETE
Batch Standard Version = V1
Exposure Framework Development = RESEARCH_ONLY_PROTOTYPE_COMPLETE
Paper Execution Safety Phase 1 = COMPLETE
Paper Execution Freshness Gate = ACTIVE
Guarded Paper Execution Entry = ACTIVE
Stale Data Fallback = BLOCKED
2026-07-10 Stale Trades = AUDITED_NON_DESTRUCTIVELY
Tushare 5000 Data Foundation Audit = COMPLETE
Reports Governance Phase A = NOT_STARTED
Report File Migration = BLOCKED
Data Foundation Upgrade = NOT_STARTED
PR #1 Hygiene Cleanup = COMPLETE
PR #1 Diff Check = CLEAN
Local Temporary Artifacts = RESOLVED
July 2026 Project Checkpoint = COMPLETE
PR #1 = MERGED
Post-Merge Validation = PASS
Main Branch = STABLE
Main Branch Merge = COMPLETE
Tushare Minimal Staging Proof & PIT Contract = COMPLETE
Tushare Staging / PIT = COMPLETE_WITH_LIMITATIONS
Evidence Isolation = COMPLETE
PR #2 = MERGED
PR #2 Merge Commit = 47d129bfa7a055b7af81f4c57fea3a95d41287c6
PR #2 Post-Merge Validation = PASS
Tushare Proof Evidence = ACCEPTED
Tushare Primary Upstream = APPROVED_PRIMARY_UPSTREAM
Decision Evidence Confidence = LIMITED_TWO_DAY_EVIDENCE
Decision Authority = USER_AUTHORIZED_EARLY_PROMOTION
Tushare Formal Staging Architecture = AUTHORIZED_NOT_STARTED
Tushare Primary Upstream Migration = AUTHORIZED_NOT_STARTED
ETF Daily Availability Timing Audit = ACTIVE_COLLECTING
Timing Optimization = ACTIVE
Data Foundation Upgrade = NOT_STARTED
Data Promotion = BLOCKED_PENDING_IMPLEMENTATION_VALIDATION
BaoStock = RECONCILIATION_ONLY
Exposure Phase 2 = NOT_STARTED
Next Data Foundation Decision = Timing-window and safety-buffer optimization only
```

Do not create adjusted preview. Current `ready_for_preview=false`.

Context updated at: 2026-07-14 14:03:31 CST
