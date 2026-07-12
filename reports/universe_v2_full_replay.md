# Universe V2 Full Replay

## Verdict

- Replay Status: COMPLETE
- Universe Version: universe_v2
- Replay ETF Count: 16
- Qualified-only input: True
- QDII included: False
- Single ETF data source: True
- Replay Range: 2025-05-30 to 2026-07-06
- V2 Common Date Range: 2025-03-03 to 2026-07-08 (329 common dates)
- Forward rows: 20880
- Robustness base rows: 4272

## Input Universe

159516, 159531, 159547, 159593, 159608, 159638, 159667, 159732, 510050, 515260, 515630, 561360, 561560, 562550, 588200, 588220

## Validation

- Feature Coverage: PASS. Every QUALIFIED_RESEARCH ETF has a local unified ETF daily file and computable ranking features.
- Replay Coverage: PASS. Replay uses the stabilized regime replay date intersection after ranking warm-up.
- Label Maturity: PASS for available labels; forward labels are skipped where horizon maturity is unavailable.
- Output Completeness: PASS. Style fit, robustness base, robustness summaries, evidence qualification, and V1 vs V2 migration files were written.
- Data Consistency: PASS. 510300 is used only as the relative-strength reference, not as an extra V2 sample member.

## Evidence Counts

QUALIFIED_SUPPORT=4, CONDITIONAL_SUPPORT=4, DESCRIPTIVE_ONLY=9, UNSTABLE=3, QUALIFIED_CONFLICT=1, CONDITIONAL_CONFLICT=0, INSUFFICIENT=15

## Replay Boundary

- Research only: true
- Shadow only: true
- Execution allowed: false
- Preview started: false
- Formal model changed: false

## Source Audit

- Regime source: data/market_regime_stabilization_replay.csv selected candidate column from Phase 2.5 decision
- Signal source: ranking_model_v2_backtest feature and rank logic; top10_diversified_filter_v2; Universe V2 membership only
- Style source: configs/universe_versions/universe_v2_registry.yaml style_profile, cross-checked with reports/etf_risk_profile.csv
- Benchmark label source: data/market_regime_replay.csv benchmark_return_{h}d columns
- Future leakage found: False
