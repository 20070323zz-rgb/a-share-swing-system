# Universe Registry

Generated at: 2026-07-08 18:52:15 CST

This registry is the project-level gate for ETF universe additions. It stores configuration, metadata, selection status, and qualification decisions only. It does not store market data and does not create a second ETF daily database.

## Registry Policy

```text
ETF Data Single Source of Truth = data/etf_daily/*.csv
Universe Registry stores = metadata / selection / qualification
Universe Registry does not store = ETF daily bars / copied V2 data
```

Future ETF additions must enter this registry before they can be considered for any Research Universe. Direct additions to Research Universe, Trade Pool, Preview, or Formal Execution are blocked.

## Current Registry Summary

| Field | Value |
| --- | --- |
| Registry version | universe_v2_registry |
| Candidate source | configs/universe_versions/universe_v2_candidate.yaml |
| Candidate count | 36 |
| QUALIFIED_RESEARCH | 16 |
| OBSERVE | 15 |
| REJECT | 5 |
| Research Universe status | READY_FOR_REPLAY_PREPARATION |
| Replay status | NOT_STARTED |
| Trade Pool activation | BLOCKED |

## Registry Records

| Code | Name | Verdict | Value | Coverage | Liquidity | History | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 159301 | 公用事业ETF华夏 | OBSERVE | HIGH | HIGH | WATCH / 24.6M | OK / 329 | Unique utilities exposure, but 60d liquidity is only watch-level and V1 classification is unknown. |
| 561560 | 电力ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 135.0M | OK / 329 | Power-sector defensive/dividend exposure with current data and sufficient liquidity. |
| 562550 | 绿电ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 199.8M | OK / 329 | Green-power defensive/dividend exposure with current data and sufficient liquidity. |
| 515630 | 保险证券 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 52.3M | OK / 329 | Insurance/financial-cyclical exposure adds coverage beyond V1 securities proxies; classification should be finalized before replay prep. |
| 515260 | 电子ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 74.8M | OK / 329 | Broad electronics exposure adds research coverage beyond chip-only themes; high-beta behavior should be flagged. |
| 159732 | 消费电子ETF华夏 | QUALIFIED_RESEARCH | HIGH | MEDIUM | OK / 491.6M | OK / 329 | Consumer-electronics exposure has strong liquidity and clear incremental technology-demand coverage. |
| 159613 | 信息安全ETF嘉实 | OBSERVE | MEDIUM | MEDIUM | LOW / 7.5M | OK / 329 | Information-security exposure is useful, but liquidity is low and classification is unknown. |
| 562920 | 信息安全 | REJECT | LOW | LOW | LOW / 9.9M | OK / 329 | Information-security peer has low liquidity, unknown classification, and weaker maintainability than 159613. |
| 159538 | 信创ETF富国 | OBSERVE | MEDIUM | MEDIUM | LOW / 17.5M | OK / 329 | Xinchuang exposure is useful, but 60d liquidity is low and volatility/classification are not mature. |
| 159540 | 信创ETF易方达 | OBSERVE | LOW | LOW | WATCH / 37.9M | OK / 329 | Xinchuang peer is duplicate exposure; keep only for peer monitoring. |
| 159658 | 数字经济ETF华安 | OBSERVE | MEDIUM | MEDIUM | LOW / 11.3M | OK / 329 | Digital-economy exposure is useful, but liquidity is too low for V2 research activation. |
| 159551 | 机器人ETF国泰 | OBSERVE | LOW | LOW | WATCH / 33.1M | OK / 329 | Robot peer duplicates existing V1 robot representatives; monitor only. |
| 159638 | 高端装备ETF嘉实 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 69.7M | OK / 329 | High-end equipment/manufacturing exposure adds useful coverage with sufficient liquidity. |
| 159667 | 工业母机ETF国泰 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 298.7M | OK / 329 | Industrial-machine exposure adds manufacturing-cycle coverage; extreme-volatility flag remains a research caveat. |
| 159516 | 半导体设备ETF国泰 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 3.45B | OK / 329 | Semiconductor-equipment exposure is highly liquid and adds a distinct technology sub-theme. |
| 159558 | 半导体设备ETF易方达 | OBSERVE | LOW | LOW | OK / 1.03B | OK / 329 | Highly liquid but duplicate semiconductor-equipment peer; keep for redundancy monitoring. |
| 561360 | 石油ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 110.9M | OK / 329 | Oil/resource exposure broadens commodity-cycle coverage with sufficient liquidity. |
| 159697 | 石油ETF鹏华 | OBSERVE | LOW | LOW | OK / 92.1M | OK / 329 | Oil peer duplicates 561360; monitor as alternate only. |
| 159608 | 稀有金属ETF广发 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 208.3M | OK / 329 | Rare-metal exposure adds resource-cycle breadth with sufficient liquidity. |
| 516750 | 建材ETF | REJECT | LOW | LOW | LOW / 10.9M | OK / 329 | Building-materials exposure is useful in theory, but liquidity is low and classification is unknown. |
| 516360 | 新材料ETF | REJECT | LOW | LOW | LOW / 5.3M | OK / 329 | New-materials ETF has ultra-low liquidity and unknown classification. |
| 159332 | 央企红利ETF富国 | REJECT | LOW | HIGH | ULTRA_LOW / 2.1M | OK / 329 | Central-SOE dividend idea is useful, but actual liquidity is ultra-low in unified data. |
| 159547 | 红利低波ETF华夏 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 131.5M | OK / 329 | Dividend low-volatility exposure has sufficient liquidity and clear style contribution. |
| 159593 | 中证A50ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 95.7M | OK / 329 | A50 broad-index exposure is classified, liquid, and useful for V2 broad-index comparison. |
| 159531 | 中证2000ETF南方 | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 143.9M | OK / 329 | CSI2000 small-cap exposure adds a missing size/style segment with sufficient liquidity. |
| 159595 | 中证A50ETF大成 | OBSERVE | LOW | LOW | OK / 138.4M | OK / 329 | A50 peer duplicates 159593 and remains classification-unknown in the V1 quality review. |
| 510050 | 上证50ETF | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 2.83B | OK / 329 | Classic Shanghai 50 large-cap proxy is liquid and useful for broad-index robustness comparison. |
| 588220 | 科创100ETF基金 | QUALIFIED_RESEARCH | MEDIUM | MEDIUM | OK / 666.1M | OK / 329 | STAR 100 growth-broad exposure is liquid and useful despite duplicate-peer caveat. |
| 515880 | 证券公司ETF | OBSERVE | MEDIUM | MEDIUM | OK / 4.38B | SHORT_OBSERVE / 122 | Very liquid securities proxy, but unified history is short and volatility is high. |
| 588200 | 科创芯片ETF | QUALIFIED_RESEARCH | HIGH | HIGH | OK / 5.28B | OK / 329 | Very liquid STAR-chip high-beta stress proxy; qualified for research, not trade activation. |
| 513180 | 恒生科技ETF | OBSERVE | HIGH | HIGH | OK / 3.74B | OK / 329 | QDII Hang Seng Tech proxy is useful but requires premium/FX/calendar handling. |
| 159941 | 纳指ETF | OBSERVE | HIGH | HIGH | OK / 1.84B | OK / 329 | QDII NASDAQ proxy is useful but must remain separate from A-share replay. |
| 513050 | 中概互联网ETF | OBSERVE | MEDIUM | MEDIUM | OK / 2.19B | OK / 329 | QDII China-internet proxy is useful but requires separate QDII handling. |
| 513520 | 日经ETF | OBSERVE | MEDIUM | MEDIUM | OK / 470.3M | OK / 329 | QDII Japan equity proxy is useful for observation only. |
| 520550 | 港股红利低波ETF | OBSERVE | MEDIUM | MEDIUM | WATCH / 49.8M | OK / 329 | QDII Hong Kong dividend-low-vol proxy has watch-level liquidity and QDII handling needs. |
| 159315 | 黄金股ETF工银 | REJECT | LOW | LOW | LOW / 19.1M | OK / 329 | Gold-equity proxy has low liquidity, high volatility, and unknown classification. |

## Machine-Readable Registry

The machine-readable registry is stored at `configs/universe_versions/universe_v2_registry.yaml`.
