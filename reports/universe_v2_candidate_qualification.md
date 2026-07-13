# Universe V2 Candidate Qualification

Generated at: 2026-07-08 18:52:15 CST

Scope: Phase 4.2 Universe V2 Candidate Qualification. This batch does not start Universe V2 Replay, does not modify Trade Pool, and does not modify Formal Execution, Shadow, Preview, Strategy, Ranking, or Score.

## Executive Verdict

All 36 Universe V2 candidates already exist in the unified ETF daily database `data/etf_daily/` and all 36 are current through 2026-07-08. No second ETF database was created, no V2 daily-data copy was created, and no ETF data refresh/backfill was required in this batch.

Qualification result:

| Verdict | Count | Meaning |
| --- | ---: | --- |
| QUALIFIED_RESEARCH | 16 | Eligible to enter Universe V2 Research Universe preparation. Not replay-ready and not trade-pool active. |
| OBSERVE | 15 | Useful to monitor, but blocked by QDII handling, short history, liquidity, classification maturity, or redundancy. |
| REJECT | 5 | Not recommended for Universe V2 Research Universe under current evidence. |

Research Universe status after this batch:

```text
Universe V2 Candidate = QUALIFIED
Universe V2 Research Universe = READY_FOR_REPLAY_PREPARATION
Universe V2 Replay = NOT_STARTED
Trade Pool = UNCHANGED
Formal Execution = BLOCKED
```

## Single Source Of Truth Check

| Check | Result |
| --- | --- |
| Candidate count | 36 |
| Candidate files present in `data/etf_daily/` | 36 / 36 |
| Latest candidate date | 2026-07-08 for all 36 |
| Duplicate dates | 0 for all 36 |
| Needs refresh | 0 |
| Needs history backfill | 0 |
| Second ETF data store created | No |
| V2 daily data copy created | No |

## Qualification Rules

- History `OK`: at least 240 local rows and current through 2026-07-08.
- History `SHORT_OBSERVE`: 120-239 local rows.
- Liquidity `OK`: 60-day average amount at least 50M.
- Liquidity `WATCH`: 20M to 50M.
- Liquidity `LOW`: 5M to 20M.
- Liquidity `ULTRA_LOW`: below 5M.
- QDII candidates remain `OBSERVE` until premium, FX, and calendar rules exist.
- `QUALIFIED_RESEARCH` means eligible for V2 Research Universe preparation only. It is not replay authorization and not trade authorization.

## Qualified Research Candidates

| Code | Name | Verdict | Value | Coverage | Liquidity | History | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 561560 | 电力ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 135.0M | OK / 329 | Power-sector defensive/dividend exposure with current data and sufficient liquidity. |
| 562550 | 绿电ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 199.8M | OK / 329 | Green-power defensive/dividend exposure with current data and sufficient liquidity. |
| 515630 | 保险证券 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 52.3M | OK / 329 | Insurance/financial-cyclical exposure adds coverage beyond V1 securities proxies; classification should be finalized before replay prep. |
| 515260 | 电子ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 74.8M | OK / 329 | Broad electronics exposure adds research coverage beyond chip-only themes; high-beta behavior should be flagged. |
| 159732 | 消费电子ETF华夏 | QUALIFIED_RESEARCH | HIGH | MEDIUM | OK / 491.6M | OK / 329 | Consumer-electronics exposure has strong liquidity and clear incremental technology-demand coverage. |
| 159638 | 高端装备ETF嘉实 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 69.7M | OK / 329 | High-end equipment/manufacturing exposure adds useful coverage with sufficient liquidity. |
| 159667 | 工业母机ETF国泰 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 298.7M | OK / 329 | Industrial-machine exposure adds manufacturing-cycle coverage; extreme-volatility flag remains a research caveat. |
| 159516 | 半导体设备ETF国泰 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 3.45B | OK / 329 | Semiconductor-equipment exposure is highly liquid and adds a distinct technology sub-theme. |
| 561360 | 石油ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 110.9M | OK / 329 | Oil/resource exposure broadens commodity-cycle coverage with sufficient liquidity. |
| 159608 | 稀有金属ETF广发 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 208.3M | OK / 329 | Rare-metal exposure adds resource-cycle breadth with sufficient liquidity. |
| 159547 | 红利低波ETF华夏 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 131.5M | OK / 329 | Dividend low-volatility exposure has sufficient liquidity and clear style contribution. |
| 159593 | 中证A50ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 95.7M | OK / 329 | A50 broad-index exposure is classified, liquid, and useful for V2 broad-index comparison. |
| 159531 | 中证2000ETF南方 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 143.9M | OK / 329 | CSI2000 small-cap exposure adds a missing size/style segment with sufficient liquidity. |
| 510050 | 上证50ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 2.83B | OK / 329 | Classic Shanghai 50 large-cap proxy is liquid and useful for broad-index robustness comparison. |
| 588220 | 科创100ETF基金 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 666.1M | OK / 329 | STAR 100 growth-broad exposure is liquid and useful despite duplicate-peer caveat. |
| 588200 | 科创芯片ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 5.28B | OK / 329 | Very liquid STAR-chip high-beta stress proxy; qualified for research, not trade activation. |

## Observe Candidates

| Code | Name | Verdict | Value | Coverage | Liquidity | History | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 159301 | 公用事业ETF华夏 | OBSERVE | HIGH | HIGH | WATCH / 24.6M | OK / 329 | Unique utilities exposure, but 60d liquidity is only watch-level and V1 classification is unknown. |
| 159613 | 信息安全ETF嘉实 | OBSERVE | MEDIUM | MEDIUM | LOW / 7.5M | OK / 329 | Information-security exposure is useful, but liquidity is low and classification is unknown. |
| 159538 | 信创ETF富国 | OBSERVE | MEDIUM | MEDIUM | LOW / 17.5M | OK / 329 | Xinchuang exposure is useful, but 60d liquidity is low and volatility/classification are not mature. |
| 159540 | 信创ETF易方达 | OBSERVE | LOW | LOW | WATCH / 37.9M | OK / 329 | Xinchuang peer is duplicate exposure; keep only for peer monitoring. |
| 159658 | 数字经济ETF华安 | OBSERVE | MEDIUM | MEDIUM | LOW / 11.3M | OK / 329 | Digital-economy exposure is useful, but liquidity is too low for V2 research activation. |
| 159551 | 机器人ETF国泰 | OBSERVE | LOW | LOW | WATCH / 33.1M | OK / 329 | Robot peer duplicates existing V1 robot representatives; monitor only. |
| 159558 | 半导体设备ETF易方达 | OBSERVE | LOW | LOW | OK / 1.03B | OK / 329 | Highly liquid but duplicate semiconductor-equipment peer; keep for redundancy monitoring. |
| 159697 | 石油ETF鹏华 | OBSERVE | LOW | LOW | OK / 92.1M | OK / 329 | Oil peer duplicates 561360; monitor as alternate only. |
| 159595 | 中证A50ETF大成 | OBSERVE | LOW | LOW | OK / 138.4M | OK / 329 | A50 peer duplicates 159593 and remains classification-unknown in the V1 quality review. |
| 515880 | 证券公司ETF | OBSERVE | MEDIUM | MEDIUM | OK / 4.38B | SHORT_OBSERVE / 122 | Very liquid securities proxy, but unified history is short and volatility is high. |
| 513180 | 恒生科技ETF | OBSERVE | HIGH | HIGH | OK / 3.74B | OK / 329 | QDII Hang Seng Tech proxy is useful but requires premium/FX/calendar handling. |
| 159941 | 纳指ETF | OBSERVE | HIGH | HIGH | OK / 1.84B | OK / 329 | QDII NASDAQ proxy is useful but must remain separate from A-share replay. |
| 513050 | 中概互联网ETF | OBSERVE | MEDIUM | MEDIUM | OK / 2.19B | OK / 329 | QDII China-internet proxy is useful but requires separate QDII handling. |
| 513520 | 日经ETF | OBSERVE | MEDIUM | MEDIUM | OK / 470.3M | OK / 329 | QDII Japan equity proxy is useful for observation only. |
| 520550 | 港股红利低波ETF | OBSERVE | MEDIUM | MEDIUM | WATCH / 49.8M | OK / 329 | QDII Hong Kong dividend-low-vol proxy has watch-level liquidity and QDII handling needs. |

## Rejected Candidates

| Code | Name | Verdict | Value | Coverage | Liquidity | History | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 562920 | 信息安全 | REJECT | LOW | LOW | LOW / 9.9M | OK / 329 | Information-security peer has low liquidity, unknown classification, and weaker maintainability than 159613. |
| 516750 | 建材ETF | REJECT | LOW | LOW | LOW / 10.9M | OK / 329 | Building-materials exposure is useful in theory, but liquidity is low and classification is unknown. |
| 516360 | 新材料ETF | REJECT | LOW | LOW | LOW / 5.3M | OK / 329 | New-materials ETF has ultra-low liquidity and unknown classification. |
| 159332 | 央企红利ETF富国 | REJECT | LOW | HIGH | ULTRA_LOW / 2.1M | OK / 329 | Central-SOE dividend idea is useful, but actual liquidity is ultra-low in unified data. |
| 159315 | 黄金股ETF工银 | REJECT | LOW | LOW | LOW / 19.1M | OK / 329 | Gold-equity proxy has low liquidity, high volatility, and unknown classification. |

## Highest Research Value Candidates

The most valuable candidates are those that combine data readiness, sufficient liquidity, and a coverage gap that V1 did not represent well:

- `561560` 电力ETF and `562550` 绿电ETF: defensive/dividend power exposure.
- `159547` 红利低波ETF华夏: dividend low-volatility style exposure.
- `159593` 中证A50ETF and `159531` 中证2000ETF南方: improved size/style coverage.
- `159516` 半导体设备ETF国泰 and `588200` 科创芯片ETF: liquid high-beta technology stress proxies.
- `159732` 消费电子ETF华夏: consumer-electronics demand proxy.
- `510050` 上证50ETF and `588220` 科创100ETF基金: broad-index comparison anchors.

## Why Some Candidates Did Not Qualify

Observe candidates generally failed because one or more of the following is true:

- QDII calendar/premium/FX treatment is not yet defined.
- 60-day liquidity is below the research threshold.
- The candidate is a duplicate peer of a better representative ETF.
- History is short, as with `515880`.
- Classification is not mature enough for direct replay preparation.

Rejected candidates failed because the current data and metadata do not justify inclusion even as V2 Research Universe preparation inputs. The main blockers are ultra-low/low liquidity, unknown classification, high volatility, and weak incremental value relative to better alternatives.

## Impact Boundary

This batch changes only qualification metadata and reports. It does not alter:

- `data/backtest_trade_pool.csv`;
- Formal Execution;
- Shadow Logic;
- Preview Logic;
- Ranking;
- Strategy;
- Score;
- Universe V1 baseline.

## Next Gate

The project is ready for a Main decision on Phase 4.3 planning, but not ready to run replay automatically. Phase 4.3 should be explicitly authorized and should perform Universe V2 Replay plus V1 vs V2 comparison using the same unified ETF daily database.
