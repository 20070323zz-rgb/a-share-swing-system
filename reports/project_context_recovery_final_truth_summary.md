# Project Context Recovery Final Truth Summary

生成时间：2026-07-07 23:56:13 CST

## Project Identity

- Project: A-Share Swing System
- Repository root: `<project_root>`
- Old repository path: deprecated; do not use `<deprecated_project_root>` for new references.

## Formal Boundary

- Formal model changed: false
- `mid_trend = 70%`
- `short_swing = 30%`
- Paper simulation active: true
- ETF-first: true
- Stock exposure limit: `<= 10%`
- Regime Layer connected to formal execution: false
- Style Fit changed BUY ranking: false

## Completed Research Phases

- Regime & Risk Allocation Phase 1
- Regime & Risk Allocation Phase 1.5
- Regime Layer Phase 2
- Regime Layer Phase 2.5
- Regime Layer Phase 3

## Current Research Architecture

```text
Market Regime
↓
Stable Shadow Regime
↓
Style-Regime Fit
↓
mid_trend + short_swing
↓
BUY Ranking
↓
Structural / Realized Risk
↓
Portfolio Exposure
```

Responsibilities:

- Style Profile: opportunity / regime fit
- Structural Risk: future risk budget research
- Realized Risk: recent observed risk
- `structural_risk_regime_fit_supported = false`

## Shadow Candidate

- selected shadow regime candidate: `ASYMMETRIC_CONFIRM`
- candidate layer: SHADOW / RESEARCH
- formal status: research-only, shadow-only, not formal execution

## Latest-Known Snapshot

```text
latest_data_date = 2026-07-07
latest_known_regime_date = 2026-07-06
latest_known_raw_regime = NEUTRAL
latest_known_shadow_regime = NEUTRAL
regime_snapshot_stale = true
```

截至 2026-07-06 的 latest-known raw/shadow regime 为 `NEUTRAL`。该 snapshot 相对 2026-07-07 数据已过期，不能视为 live current market regime。

## Phase 3 Decision

```text
style_fit_has_historical_support = true
style_fit_has_incremental_signal_value = true
ready_for_fit_shadow_observation = true
ready_for_adjusted_preview_research = true
ready_for_preview = false
ready_for_execution = false
execution_allowed = false
```

Research permission != preview permission != execution permission.

## Open Research Risks

- `HIGH_BETA_THEME` multi-regime support anomaly
- `COMMODITY_CYCLICAL` multi-regime support anomaly
- real dual-regime behavior
- style aggregation masking
- cross-sectional dependence
- effective sample size inflation
- regime segment dependence

## Current Bottlenecks

- Style Fit robustness not yet proven
- real forward shadow samples limited
- formal exit logic remains a major strategy bottleneck
- formal model remains statistically research-unproven

## Next Research Phase

```text
Regime Layer Phase 3.5 - Style Fit Robustness Audit
status = NOT_STARTED
```
