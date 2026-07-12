# Style Fit Failure Attribution

## Scope

- Generated at: 2026-07-08 21:12:25 CST
- Batch: Phase 5.3 Failure Attribution
- Evidence sources: existing Phase 5.2 outputs, Universe registry, V1 robustness base, V1 trade pool, and current repository state.
- This report does not rerun replay, modify data, modify model logic, or propose strategy fixes.

## Executive Finding

Style Fit failed to generalize primarily because Universe V2 changed the effective sample structure and exposed horizon/incremental-value instability that was not resolved by V1 evidence qualification. The failure is not an engineering replay failure: coverage is clean, QDII is excluded, and the single ETF daily database remains the source of truth.

The strongest contributors are:

- Universe shift: HIGH contribution, HIGH confidence.
- Horizon conflict: HIGH contribution, HIGH confidence.
- Methodology limitation: HIGH contribution, MEDIUM confidence.
- Style instability: HIGH contribution, MEDIUM confidence.
- Cell migration and regime instability: MEDIUM contribution.

## Part A - Universe Shift Attribution

V2 replay used 16 QUALIFIED_RESEARCH ETFs, 20880 forward-label rows, and 4272 robustness-base rows over 2025-05-30 to 2026-07-06.

### V1 vs V2 Style Structure

| style_profile | V1 Trade ETFs | V1 Base Rows | V2 ETFs | V2 Base Rows |
| --- | --- | --- | --- | --- |
| BOND | 8 | 1896 (23.7%) | 0 | 0 (0.0%) |
| COMMODITY_CYCLICAL | 8 | 1352 (16.9%) | 2 | 534 (12.5%) |
| CORE_LARGE_CAP | 4 | 816 (10.2%) | 2 | 534 (12.5%) |
| CORE_MID_CAP | 3 | 462 (5.8%) | 2 | 534 (12.5%) |
| DIVIDEND | 3 | 693 (8.7%) | 3 | 801 (18.8%) |
| HIGH_BETA_THEME | 2 | 388 (4.8%) | 5 | 1335 (31.2%) |
| SECTOR_CYCLICAL | 4 | 847 (10.6%) | 1 | 267 (6.2%) |
| SECTOR_DEFENSIVE | 7 | 1556 (19.4%) | 1 | 267 (6.2%) |

### V2 Qualified Exposures

| ETF | Name | Style | Exposure | Research Value | Redundancy |
| --- | --- | --- | --- | --- | --- |
| 561560 | 电力ETF | DIVIDEND | power / utilities | HIGH | Related to green-power candidates but not redundant with V1 trade pool. |
| 562550 | 绿电ETF | DIVIDEND | green power / utilities | HIGH | Moderate with 561560; keep one primary after V2 liquidity review. |
| 515630 | 保险证券 | SECTOR_CYCLICAL | insurance / financial beta | MEDIUM | Moderate with V1 securities and non-bank ETF exposure. |
| 515260 | 电子ETF | HIGH_BETA_THEME | electronics / growth technology | MEDIUM | Moderate with chip, AI, and high-beta theme names. |
| 159732 | 消费电子ETF华夏 | SECTOR_DEFENSIVE | consumer electronics | HIGH | Moderate with electronics and growth theme candidates. |
| 159638 | 高端装备ETF嘉实 | HIGH_BETA_THEME | high-end manufacturing | MEDIUM | Moderate with robotics/industrial-machine candidates. |
| 159667 | 工业母机ETF国泰 | HIGH_BETA_THEME | industrial machine / high-end manufacturing | MEDIUM | Moderate with 159638 and robotics. |
| 159516 | 半导体设备ETF国泰 | HIGH_BETA_THEME | semiconductor equipment | HIGH | Moderate to high with chip/AI technology exposure. |
| 561360 | 石油ETF | COMMODITY_CYCLICAL | oil and gas / resource | MEDIUM | Moderate with commodity/resource names. |
| 159608 | 稀有金属ETF广发 | COMMODITY_CYCLICAL | rare metals | MEDIUM | Moderate with nonferrous/rare-earth. |
| 159547 | 红利低波ETF华夏 | DIVIDEND | dividend low volatility | HIGH | Moderate with dividend names; low-vol factor is incremental. |
| 159593 | 中证A50ETF | CORE_LARGE_CAP | large-cap core / A50 | HIGH | Moderate with A500/CSI300/Shanghai50. |
| 159531 | 中证2000ETF南方 | CORE_MID_CAP | CSI2000 / small cap | HIGH | Low to moderate with CSI1000/Core mid-cap proxies. |
| 510050 | 上证50ETF | CORE_LARGE_CAP | large-cap core / Shanghai 50 | MEDIUM | Moderate with CSI300/A500/A50. |
| 588220 | 科创100ETF基金 | CORE_MID_CAP | STAR 100 / growth broad | MEDIUM | High with other STAR 100 peers. |
| 588200 | 科创芯片ETF | HIGH_BETA_THEME | STAR chip / high-beta growth | HIGH | High with semiconductor/chip themes. |

### Universe Shift Verdict

Universe Shift is a major failure source with HIGH confidence. V2 is not a balanced extension of V1; it deliberately adds high-beta technology/manufacturing, dividend/utilities, core index, and resource exposures while excluding bonds from the qualified research replay. The BOND cells therefore become unrecoverable in V2, and high-beta/core style cells gain much larger influence on the effective sample.

## Part B - Cell-Level Attribution

Migration counts: {'CHANGED_DIRECTION_OR_CATEGORY': 6, 'DOWNGRADED': 3, 'UNCHANGED': 24, 'UPGRADED': 3}.

The 24 unchanged cells do not mean the research conclusion is stable. Within unchanged cells, the V2 categories are {'DESCRIPTIVE_ONLY': 8, 'CONDITIONAL_SUPPORT': 3, 'INSUFFICIENT': 12, 'UNSTABLE': 1}; many are still INSUFFICIENT or DESCRIPTIVE_ONLY, so they preserve absence of evidence rather than confirming generalization.

### Top Failure-Contributing Cells

| Style | Regime | V1 | V2 | Migration | V1 Evidence | V2 Evidence | V1 Excess | V2 Excess | Severity | Why |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SECTOR_DEFENSIVE | DEFENSIVE | QUALIFIED_CONFLICT | QUALIFIED_SUPPORT | CHANGED_DIRECTION_OR_CATEGORY | CONFLICT | SUPPORTED | -0.0251 | 0.0225 | 8 | changed direction/category; support/conflict direction flip; material excess-return shift |
| SECTOR_DEFENSIVE | OFFENSIVE | CONDITIONAL_CONFLICT | QUALIFIED_SUPPORT | CHANGED_DIRECTION_OR_CATEGORY | CONFLICT | SUPPORTED | -0.0204 | 0.0272 | 8 | changed direction/category; support/conflict direction flip; material excess-return shift |
| BOND | NEUTRAL | CONDITIONAL_SUPPORT | INSUFFICIENT | DOWNGRADED | SUPPORTED | INSUFFICIENT | 0.0040 |  | 5 | downgraded; lost support coverage |
| SECTOR_CYCLICAL | NEUTRAL | CONDITIONAL_CONFLICT | DESCRIPTIVE_ONLY | DOWNGRADED | CONFLICT | NEUTRAL | -0.0115 | -0.0049 | 4 | downgraded; lost negative evidence |
| BOND | DEFENSIVE | DESCRIPTIVE_ONLY | INSUFFICIENT | CHANGED_DIRECTION_OR_CATEGORY | WEAK_SUPPORT | INSUFFICIENT | -0.0170 |  | 3 | changed direction/category |
| COMMODITY_CYCLICAL | DEFENSIVE | QUALIFIED_SUPPORT | CONDITIONAL_SUPPORT | CHANGED_DIRECTION_OR_CATEGORY | SUPPORTED | SUPPORTED | 0.0061 | 0.0170 | 3 | changed direction/category |
| CORE_MID_CAP | DEFENSIVE | CONDITIONAL_SUPPORT | QUALIFIED_SUPPORT | CHANGED_DIRECTION_OR_CATEGORY | SUPPORTED | SUPPORTED | 0.0052 | 0.0091 | 3 | changed direction/category |
| CORE_MID_CAP | OFFENSIVE | CONDITIONAL_SUPPORT | QUALIFIED_SUPPORT | CHANGED_DIRECTION_OR_CATEGORY | SUPPORTED | SUPPORTED | 0.0113 | 0.0153 | 3 | changed direction/category |
| BOND | OFFENSIVE | UNSTABLE | INSUFFICIENT | DOWNGRADED | WEAK_SUPPORT | INSUFFICIENT | -0.0131 |  | 2 | downgraded |
| CORE_MID_CAP | NEUTRAL | DESCRIPTIVE_ONLY | UNSTABLE | UPGRADED | NEUTRAL | WEAK_CONFLICT | 0.0007 | -0.0022 | 2 | upgraded to unstable rather than usable evidence |
| HIGH_BETA_THEME | NEUTRAL | CONDITIONAL_CONFLICT | UNSTABLE | UPGRADED | CONFLICT | WEAK_CONFLICT | -0.0189 | -0.0090 | 2 | upgraded to unstable rather than usable evidence |
| HIGH_BETA_THEME | DEFENSIVE | CONDITIONAL_SUPPORT | CONDITIONAL_SUPPORT | UNCHANGED | SUPPORTED | SUPPORTED | 0.0001 | 0.0294 | 1 | material excess-return shift |

### Cell-Level Verdict

Cell migration is a MEDIUM contributor. It explains where the generalization broke, but it is not alone sufficient to explain FAILED_GENERALIZATION because the decisive failure also comes from horizon and incremental-value robustness turning CONFLICTING.

## Part C - Style-Level Attribution

| Style | Contribution | Severity Score | V2 Categories | Migrations | Horizon Conflicts | V2 Base Share | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SECTOR_DEFENSIVE | HIGH | 16 | QUALIFIED_SUPPORT=2, UNSTABLE=1 | CHANGED_DIRECTION_OR_CATEGORY=2, UNCHANGED=1 | 1 | 6.2% | Direction flips from V1 conflict to V2 support in OFFENSIVE/DEFENSIVE; material sign instability. |
| BOND | HIGH | 10 | INSUFFICIENT=3 | CHANGED_DIRECTION_OR_CATEGORY=1, DOWNGRADED=2 | 0 | 0.0% | V2 contains no BOND qualified ETFs, so V1 bond support becomes unrecoverable rather than contradicted. |
| CORE_MID_CAP | HIGH | 8 | QUALIFIED_SUPPORT=2, UNSTABLE=1 | CHANGED_DIRECTION_OR_CATEGORY=2, UPGRADED=1 | 1 | 12.5% | OFFENSIVE/DEFENSIVE strengthen, NEUTRAL becomes unstable; contributes to regime/horizon inconsistency. |
| SECTOR_CYCLICAL | MEDIUM | 4 | DESCRIPTIVE_ONLY=3 | DOWNGRADED=1, UNCHANGED=2 | 0 | 6.2% | NEUTRAL negative evidence downgrades to descriptive; financial beta does not replicate V1 negative cell. |
| COMMODITY_CYCLICAL | MEDIUM | 3 | CONDITIONAL_SUPPORT=2, DESCRIPTIVE_ONLY=1 | CHANGED_DIRECTION_OR_CATEGORY=1, UNCHANGED=2 | 0 | 12.5% | Retains multi-regime support in V2 but is capped to conditional and carries sample-dependence risk. |
| HIGH_BETA_THEME | MEDIUM | 3 | CONDITIONAL_SUPPORT=2, UNSTABLE=1 | UNCHANGED=2, UPGRADED=1 | 1 | 31.2% | Largest V2 style exposure; OFFENSIVE/DEFENSIVE support remains, but NEUTRAL becomes UNSTABLE and special-style risk persists. |
| GROWTH_BROAD | MEDIUM | 0 | INSUFFICIENT=3 | UNCHANGED=3 | 0 | 0.0% | No V2 qualified exposure; remains insufficient. |
| GROWTH_THEME | MEDIUM | 0 | INSUFFICIENT=3 | UNCHANGED=3 | 0 | 0.0% | No V2 qualified exposure; remains insufficient. |
| LOW_VOL | MEDIUM | 0 | INSUFFICIENT=3 | UNCHANGED=3 | 0 | 0.0% | No V2 qualified exposure; remains insufficient. |
| QDII_OBSERVATION | MEDIUM | 0 | INSUFFICIENT=3 | UNCHANGED=3 | 0 | 0.0% | No V2 qualified exposure; remains insufficient. |
| CORE_LARGE_CAP | LOW | 0 | DESCRIPTIVE_ONLY=2, QUALIFIED_CONFLICT=1 | UNCHANGED=2, UPGRADED=1 | 0 | 12.5% | NEUTRAL becomes new qualified conflict while other regimes remain descriptive. |
| DIVIDEND | LOW | 0 | DESCRIPTIVE_ONLY=3 | UNCHANGED=3 | 0 | 18.8% | V2 adds dividend/utilities exposure, but all regimes remain descriptive, not a direct evidence driver. |

HIGH_BETA_THEME remains unstable in the research sense: V2 shows OFFENSIVE and DEFENSIVE conditional support, but NEUTRAL becomes UNSTABLE and the style remains structurally concentrated in technology/chip/manufacturing exposures. COMMODITY_CYCLICAL retains some multi-regime behavior, but V2 caps it at conditional support and flags sample-dependence risk rather than qualified robustness.

## Part D - Regime-Level Attribution

| Regime | Contribution | Severity Score | V2 Categories | Migrations | Horizon Conflict Cells | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| DEFENSIVE | HIGH | 18 | CONDITIONAL_SUPPORT=2, DESCRIPTIVE_ONLY=3, INSUFFICIENT=5, QUALIFIED_SUPPORT=2 | CHANGED_DIRECTION_OR_CATEGORY=4, UNCHANGED=8 | 0 | Includes direction changes in sector/core styles; contributes through category flips rather than broad collapse. |
| NEUTRAL | HIGH | 13 | DESCRIPTIVE_ONLY=3, INSUFFICIENT=5, QUALIFIED_CONFLICT=1, UNSTABLE=3 | DOWNGRADED=2, UNCHANGED=7, UPGRADED=3 | 3 | Largest concentration of downgrades/unstable cells; NEUTRAL is the clearest regime-level failure source. |
| OFFENSIVE | HIGH | 13 | CONDITIONAL_SUPPORT=2, DESCRIPTIVE_ONLY=3, INSUFFICIENT=5, QUALIFIED_SUPPORT=2 | CHANGED_DIRECTION_OR_CATEGORY=2, DOWNGRADED=1, UNCHANGED=9 | 0 | OFFENSIVE has support in some V2 growth/core cells but also direction flips in defensive sectors. |

NEUTRAL is the clearest regime-level source of failure because it concentrates downgrade/unstable outcomes and contributes the new CORE_LARGE_CAP qualified conflict. OFFENSIVE and DEFENSIVE are not cleanly stable either; they include direction flips, especially SECTOR_DEFENSIVE turning from V1 conflict to V2 support.

## Part E - Horizon Attribution

Phase 5.2 robustness summary: Time=FRAGILE, Segment=FRAGILE, Horizon=CONFLICTING, Incremental=CONFLICTING.

| Horizon | Direction | Supported Count | Conflict Count | Median Diff | Excess Diff | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| 1d | CONFLICT_BEATS_SUPPORTED | 359 | 59 | -0.0002 | -0.0015 | conflict group beats supported group |
| 3d | CONFLICT_BEATS_SUPPORTED | 359 | 57 | -0.0037 | -0.0041 | conflict group beats supported group |
| 5d | NEUTRAL | 358 | 56 | 0.0098 | -0.0055 | neutral/no edge |
| 10d | NEUTRAL | 353 | 56 | 0.0112 | -0.0042 | neutral/no edge |
| 20d | CONFLICT_BEATS_SUPPORTED | 340 | 50 | -0.0061 | -0.0163 | conflict group beats supported group |

### Incremental Robustness Rows

| Method | Group | Horizon | Direction | Median Diff | Excess Diff |
| --- | --- | --- | --- | --- | --- |
| Pooled ETF-day | ALL | 5d | NEUTRAL | 0.0098 | -0.0055 |
| Pooled ETF-day | ALL | 10d | NEUTRAL | 0.0112 | -0.0042 |
| Pooled ETF-day | ALL | 20d | CONFLICT_BEATS_SUPPORTED | -0.0061 | -0.0163 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 5d | NEUTRAL | 0.0125 | -0.0103 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 10d | NEUTRAL | 0.0216 | -0.0052 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 20d | NEUTRAL | 0.0047 | -0.0184 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 5d | INSUFFICIENT | 0.0040 | 0.0215 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 10d | INSUFFICIENT | -0.0227 | -0.0033 |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 20d | INSUFFICIENT | 0.0208 | 0.0328 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 5d | NEUTRAL | 0.0103 | -0.0103 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 10d | NEUTRAL | 0.0200 | -0.0052 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 20d | NEUTRAL | 0.0041 | -0.0195 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 5d | INSUFFICIENT | 0.0115 | 0.0212 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 10d | INSUFFICIENT | -0.0126 | -0.0032 |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 20d | INSUFFICIENT | 0.0323 | 0.0339 |
| ETF-Level Aggregation | ALL | 5d | SUPPORTED_BEATS_CONFLICT | 0.0029 | -0.0074 |
| Regime-Segment Aggregation | ALL | 5d | SUPPORTED_BEATS_CONFLICT | 0.0120 | 0.0036 |
| ETF-Level Aggregation | ALL | 10d | SUPPORTED_BEATS_CONFLICT | 0.0090 | -0.0007 |
| Regime-Segment Aggregation | ALL | 10d | SUPPORTED_BEATS_CONFLICT | 0.0111 | 0.0056 |
| ETF-Level Aggregation | ALL | 20d | CONFLICT_BEATS_SUPPORTED | -0.0099 | -0.0115 |
| Regime-Segment Aggregation | ALL | 20d | SUPPORTED_BEATS_CONFLICT | 0.0263 | 0.0119 |
| Horizon | ALL | 5d | NEUTRAL | 0.0098 | -0.0055 |
| Horizon | ALL | 10d | NEUTRAL | 0.0112 | -0.0042 |
| Horizon | ALL | 20d | CONFLICT_BEATS_SUPPORTED | -0.0061 | -0.0163 |

Time split directions: {'NEUTRAL': 12, 'INSUFFICIENT': 12}. Segment concentration flags: {'INSUFFICIENT': 65, 'MODERATE': 4, 'HIGH': 1}. Segment direction consistency: {nan: 70}.

Horizon conflict is a HIGH-confidence primary contributor. The 1d, 3d, and 20d horizons show CONFLICT_BEATS_SUPPORTED while 5d and 10d are neutral. This means the V2 label behavior does not preserve a stable positive Style Fit edge across horizons, and the incremental-value test becomes CONFLICTING.

## Part F - Methodology Attribution

The failure exposes methodology fragility rather than an obvious implementation defect. The same regime source, ranking logic, score inputs, and style labels produce different conclusions when the universe changes. This indicates:

- Style Mapping may be too coarse for high-beta technology, chip, electronics, STAR, and industrial-machine exposures.
- ETF-day pooling remains sensitive to which ETF families dominate the sample.
- Effective sample size is not equivalent to row count; V2 has 4,272 robustness-base rows but much of that sample is concentrated in a smaller set of style families.
- Style Fit should be treated as Universe-sensitive and likely V1-specific until a future framework proves cross-universe robustness.
- The repository does not prove that simple parameter tuning would fix the failure; this batch should not optimize or repair the model.

## Attribution Verdict

The failure is best explained as a combination of Universe Shift + Horizon Conflict + Methodology Limitation. Cell and regime analysis localize the breakage, while style analysis shows that BOND absence, high-beta concentration, sector direction flips, and conditional commodity behavior are the visible channels through which the failure appears.
