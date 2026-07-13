# Universe V2 Coverage Gap Analysis

Generated at: 2026-07-08

Scope: Phase 4.1 Universe Evolution audit and design. This report does not modify Formal Execution, Shadow Logic, Preview, Strategy, Ranking, Score, or Universe V1 research conclusions.

## Executive Verdict

Universe V1 is traceable and sufficient as the historical baseline for Phase 3 / Phase 3.5, but it is not broad enough to serve as the only future research universe. The main issue is not the raw number of ETF files. The issue is representation: V1 research evidence was effectively constrained to a 39-symbol `backtest_trade_pool`, while many observe/research-only symbols either duplicate existing exposure, lack classification, require QDII handling, or have liquidity/history issues.

Universe V2 should therefore expand coverage deliberately:

- broaden underrepresented sectors and styles;
- keep QDII separate;
- promote only symbols that pass refreshed classification, liquidity, history, and duplicate-exposure screens;
- preserve Universe V1 as the locked Phase 3 / 3.5 baseline.

## V1 Inventory Summary

Primary source files:

- `data/etf_daily/*.csv`
- `data/backtest_trade_pool.csv`
- `reports/universe_quality_review.csv`
- `reports/etf_risk_profile.csv`
- `reports/effective_sample_coverage_audit.md`

V1 counts from repository artifacts:

| Layer / audit view | Count | Source |
| --- | ---: | --- |
| Master ETF daily files | 183 | `data/etf_daily/` |
| Quality-review trade_pool | 39 | `reports/universe_quality_review.csv` |
| Quality-review observe_pool | 132 | `reports/universe_quality_review.csv` |
| Quality-review exclude_pool | 12 | `reports/universe_quality_review.csv` |
| Backtest trade pool | 39 | `data/backtest_trade_pool.csv` |

V1 quality-review pool by ETF type:

| ETF type | Exclude | Observe | Trade |
| --- | ---: | ---: | ---: |
| bond_cash | 0 | 4 | 8 |
| broad_index | 0 | 16 | 6 |
| commodity_resource | 0 | 12 | 9 |
| high_beta | 0 | 1 | 2 |
| qdii | 0 | 15 | 0 |
| sector | 1 | 9 | 9 |
| theme | 0 | 13 | 5 |
| unknown | 11 | 62 | 0 |

V1 action distribution:

| Recommended action | Count |
| --- | ---: |
| observe_only_before_backtest | 82 |
| keep_best_liquidity_peer_in_trade_pool | 40 |
| eligible_for_phase4a_backtest | 39 |
| exclude_before_backtest | 12 |
| observe_or_small_weight_only | 10 |

## Important Timestamp Caveat

The repository has multiple valid but differently dated artifacts:

- `reports/dashboard_data.json` latest data date: 2026-07-08.
- `reports/etf_risk_profile.csv` risk profile data end: 2026-07-06.
- `reports/universe_quality_review.csv` quality-review data end: 2026-06-17.

This is not treated as an engineering contradiction for Phase 4.1 because this batch is a design/versioning batch, not a refreshed universe-quality rerun. It does mean all V2 promotions must be revalidated by a dedicated V2 data coverage and quality-review batch before replay.

## V1 Coverage Gaps

### Sector Gaps

Underrepresented or not cleanly represented in the V1 39-symbol evidence base:

- utilities / public services;
- electricity and green power;
- insurance as a separate financial exposure;
- electronics and consumer electronics distinct from chip-only ETFs;
- information security and Xinchuang;
- high-end manufacturing and industrial machine tools;
- oil and gas;
- rare metals / new materials / building materials;
- Hong Kong technology and offshore China technology, but these must remain QDII observation only.

### Theme Gaps

V1 contains technology and high-beta theme exposure, but much of it is either duplicated or high-volatility. V2 should separate:

- AI;
- semiconductor equipment;
- information security;
- Xinchuang / domestic substitution;
- digital economy;
- robotics;
- high-end manufacturing;
- industrial machine tools.

Theme heat alone is not an inclusion reason. Every theme candidate needs history, liquidity, and duplicate-exposure validation.

### Style Gaps

V1 evidence is weaker for:

- dividend low-volatility;
- central-SOE dividend;
- public-utility defensive dividend;
- A50 / A-share core-large-cap alternatives;
- small-cap CSI2000 exposure;
- clean QDII observation tiers.

### Duplicate Exposure Clusters

The V1 review found large duplicate clusters:

- broad-index peers, especially A500, CSI300/500/1000, STAR 100, and A50-like products;
- chip / semiconductor / AI / software / cloud;
- robotics peers;
- dividend / low-volatility / SOE dividend peers;
- bond/cash peers;
- QDII peers with the same external-market exposure;
- unknown expanded-formal-data group with 72 duplicate-exposure members.

V2 should choose representative leaders, not promote every peer.

### Classification Gaps

The largest V1 barrier is classification, not file availability:

- 62 unknown symbols remain in observe_pool.
- 11 unknown symbols remain in exclude_pool.
- Unknown symbols can be useful master candidates, but they should not enter research/replay until classification is fixed.

Examples with possible research value but unknown classification in V1 quality review:

| Symbol | Name | Potential exposure | V2 treatment |
| --- | --- | --- | --- |
| 159301 | 公用事业ETF华夏 | utilities / defensive dividend | research candidate after classification cleanup |
| 561560 | 电力ETF | power / dividend | research candidate after classification cleanup |
| 562550 | 绿电ETF | green power / dividend | research candidate after classification cleanup |
| 515630 | 保险证券 | insurance / financial beta | conditional research candidate |
| 515260 | 电子ETF | electronics | conditional research candidate |
| 561360 | 石油ETF | oil and gas | conditional research candidate |
| 516750 | 建材ETF | building materials | observe only |
| 516360 | 新材料ETF | new materials | exclude/observe only due to ultra-low liquidity |

## Observe Pool Upgrade Potential

Potential upgrade candidates are not automatic promotions. They should be screened in this order:

1. Classification fixed and mapped to a stable style profile.
2. Daily data coverage refreshed to a consistent V2 review date.
3. Liquidity passes V2 threshold.
4. Duplicate-exposure cluster has a single preferred representative.
5. Replay and forward-label maturity are verified.
6. Main explicitly approves research activation.

High-priority upgrade candidates:

- `159301` 公用事业ETF华夏
- `561560` 电力ETF
- `562550` 绿电ETF
- `159332` 央企红利ETF富国
- `159547` 红利低波ETF华夏
- `159593` 中证A50ETF
- `159531` 中证2000ETF南方

Conditional upgrade candidates:

- `515630` 保险证券
- `515260` 电子ETF
- `159613` 信息安全ETF嘉实
- `159538` 信创ETF富国
- `159658` 数字经济ETF华安
- `159638` 高端装备ETF嘉实
- `159667` 工业母机ETF国泰
- `159516` 半导体设备ETF国泰
- `561360` 石油ETF
- `159608` 稀有金属ETF广发

Observe-only / separate treatment:

- QDII: `513180`, `159941`, `513050`, `513520`, `520550`.
- Low-quality or liquidity-blocked: `562920`, `516750`, `516360`, `159315`.
- Highly duplicated peers: `159540`, `159551`, `159558`, `159595`.

## Public-Source Discovery Gaps

The staged expansion resolver explicitly failed to find confident matches for some target categories. These should remain discovery tasks, not invented candidates:

| Category | Repository evidence | V2 status |
| --- | --- | --- |
| 北证50 / 北证相关 | `PENDING_BJ50_01` unresolved | discovery required |
| 科创200 | `PENDING_KC200_01` unresolved | discovery required |
| 算力 / 数据中心 / 通信设备 | pending categories unresolved | discovery required |
| REITs | not represented in V1 research design | separate asset-class design required |

## Risk Assessment

Methodology Risk: MEDIUM

Reason: Universe V2 may change evidence composition and needs V1 vs V2 comparison before any research conclusion is generalized.

Coverage Risk: MEDIUM

Reason: V1 coverage is explainable but concentrated; V2 improves representation only after refreshed quality review.

Engineering Risk: LOW

Reason: Phase 4.1 only adds versioning and reports. It does not alter replay, preview, ranking, strategy, score, shadow, or execution logic.

## Conclusion

V1 should remain the locked baseline. V2 should proceed as a candidate universe design with no replay or trade activation until a separate Main-approved data coverage, classification, and V1-vs-V2 research batch is run.
