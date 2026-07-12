# Universe V2 Replay Plan

Generated at: 2026-07-08 19:05:00 CST

Phase: 5.1 - Research Generalization: Universe V2 Replay Preparation

This is a planning artifact only. Universe V2 Replay is not started in this batch.

## Scope Boundary

Allowed:

- Plan replay batches for Universe V2.
- Use only `QUALIFIED_RESEARCH` records from `configs/universe_versions/universe_v2_registry.yaml`.
- Keep ETF data single-source-of-truth at `data/etf_daily/*.csv`.
- Define checkpoint and recovery expectations.

Forbidden:

- Start Universe V2 Replay.
- Modify Universe V1.
- Modify Trade Pool.
- Include `OBSERVE` or `REJECT` candidates.
- Include QDII candidates.
- Modify Formal Execution, Shadow, Preview, Strategy, Ranking, or Score.

## Replay Input Universe

Source: `configs/universe_versions/universe_v2_registry.yaml`

Filter:

```text
qualification_verdict = QUALIFIED_RESEARCH
asset_flags contains A_SHARE_ETF
asset_flags does not contain QDII
```

Planned symbols:

| Symbol | Name | Style profile | Exposure |
| --- | --- | --- | --- |
| 561560 | 电力ETF | DIVIDEND | power / utilities |
| 562550 | 绿电ETF | DIVIDEND | green power / utilities |
| 515630 | 保险证券 | SECTOR_CYCLICAL | insurance / financial beta |
| 515260 | 电子ETF | HIGH_BETA_THEME | electronics / growth technology |
| 159732 | 消费电子ETF华夏 | SECTOR_DEFENSIVE | consumer electronics |
| 159638 | 高端装备ETF嘉实 | HIGH_BETA_THEME | high-end manufacturing |
| 159667 | 工业母机ETF国泰 | HIGH_BETA_THEME | industrial machine / high-end manufacturing |
| 159516 | 半导体设备ETF国泰 | HIGH_BETA_THEME | semiconductor equipment |
| 561360 | 石油ETF | COMMODITY_CYCLICAL | oil and gas / resource |
| 159608 | 稀有金属ETF广发 | COMMODITY_CYCLICAL | rare metals |
| 159547 | 红利低波ETF华夏 | DIVIDEND | dividend low volatility |
| 159593 | 中证A50ETF | CORE_LARGE_CAP | large-cap core / A50 |
| 159531 | 中证2000ETF南方 | CORE_MID_CAP | CSI2000 / small cap |
| 510050 | 上证50ETF | CORE_LARGE_CAP | large-cap core / Shanghai 50 |
| 588220 | 科创100ETF基金 | CORE_MID_CAP | STAR 100 / growth broad |
| 588200 | 科创芯片ETF | HIGH_BETA_THEME | STAR chip / high-beta growth |

Explicit exclusions:

- `OBSERVE` candidates: excluded from replay planning.
- `REJECT` candidates: excluded from replay planning.
- QDII candidates: excluded from this stage even when research value is high.

## Batch Design

The 16 symbols are split into four batches of four symbols each. Each batch mixes broad/style anchors with defensive, growth, cyclical, or manufacturing exposure so that a single interrupted batch can still be interpreted and validated independently.

### Batch V2-RP-01: Core Defensive And Growth Anchor

| Symbol | Name | Role |
| --- | --- | --- |
| 159593 | 中证A50ETF | large-cap core anchor |
| 159531 | 中证2000ETF南方 | small-cap breadth anchor |
| 561560 | 电力ETF | defensive dividend / utility |
| 159516 | 半导体设备ETF国泰 | high-liquidity technology growth |

Rationale: combines size breadth, defensive power, and high-beta technology. It is the best first smoke-test batch because it covers several V2 expansion motives without QDII or low-liquidity names.

### Batch V2-RP-02: Broad Growth And Defensive Pair

| Symbol | Name | Role |
| --- | --- | --- |
| 510050 | 上证50ETF | classic large-cap anchor |
| 588220 | 科创100ETF基金 | STAR growth-broad anchor |
| 562550 | 绿电ETF | defensive dividend / green power |
| 588200 | 科创芯片ETF | liquid high-beta chip stress proxy |

Rationale: contrasts classic defensive large-cap with STAR/high-beta technology while retaining one green-power defensive exposure.

### Batch V2-RP-03: Sector Cyclical And Manufacturing

| Symbol | Name | Role |
| --- | --- | --- |
| 515630 | 保险证券 | financial cyclical |
| 159732 | 消费电子ETF华夏 | consumer-electronics demand proxy |
| 561360 | 石油ETF | oil/resource cyclical |
| 159638 | 高端装备ETF嘉实 | high-end manufacturing |

Rationale: tests sector generalization outside the V1 core, with financial, resource, consumer electronics, and manufacturing exposure in one recoverable unit.

### Batch V2-RP-04: Dividend Resource And Industrial High Beta

| Symbol | Name | Role |
| --- | --- | --- |
| 159547 | 红利低波ETF华夏 | dividend low-volatility style |
| 159608 | 稀有金属ETF广发 | rare-metal resource cyclical |
| 159667 | 工业母机ETF国泰 | industrial-machine high beta |
| 515260 | 电子ETF | broad electronics high beta |

Rationale: combines style-defensive dividend with resource and high-beta industrial/electronics exposure. This batch is expected to be the most style-heterogeneous, so it should run after the earlier smoke-test batches.

## Execution Order

Recommended order:

1. `V2-RP-01`
2. `V2-RP-02`
3. `V2-RP-03`
4. `V2-RP-04`

Reasoning:

- Batch 1 is the broadest smoke test.
- Batch 2 tests another broad-index plus high-beta pair.
- Batch 3 moves into sector/cyclical generalization.
- Batch 4 captures the most heterogeneous tail of qualified V2 exposure.

## Batch Independence

Each batch must be runnable and verifiable on its own:

- The input symbol list is fixed.
- Each batch writes to its own batch-scoped output paths.
- Each batch has a manifest, validation summary, and completion marker.
- Aggregate V2 outputs are generated only after all batch completion markers exist.

## Planned Output Namespace

No replay output is created in Phase 5.1. Future replay execution should use batch-scoped paths such as:

```text
reports/universe_v2_replay/batch_v2_rp_01/
reports/universe_v2_replay/batch_v2_rp_02/
reports/universe_v2_replay/batch_v2_rp_03/
reports/universe_v2_replay/batch_v2_rp_04/
reports/universe_v2_replay/aggregate/
```

## Completion Criteria For Future Replay Phase

A future replay execution phase should not aggregate V2 evidence unless all are true:

- all four batch manifests exist;
- all four validation summaries pass;
- all four completion markers exist;
- no batch includes `OBSERVE`, `REJECT`, or QDII symbols;
- no batch writes to Universe V1 or Trade Pool files;
- aggregate report records the exact Universe V2 registry version used.
