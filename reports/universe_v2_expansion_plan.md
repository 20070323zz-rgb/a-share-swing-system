# Universe V2 Expansion Plan

Generated at: 2026-07-08

Phase: 4.1 - Universe Evolution: ETF Pool Expansion and Universe V2 Versioning

This is a design and governance artifact. It does not modify Formal Execution, Shadow Logic, Preview, Strategy, Ranking, Score, or the Universe V1 research baseline.

## Status

```text
Universe V1 = LOCKED_HISTORICAL_BASELINE
Universe V2 = CANDIDATE / DESIGNED
Universe V2 Replay = NOT_STARTED
Universe V2 Trade Pool Activation = BLOCKED
Preview Research = NOT_STARTED
Formal Execution = BLOCKED
Phase 4.2 = NOT_STARTED
```

## Versioning Files

| File | Purpose |
| --- | --- |
| `configs/universe_versions/universe_v1.yaml` | Locked V1 baseline and Phase 3 / 3.5 binding |
| `configs/universe_versions/universe_v2_candidate.yaml` | V2 candidate design, layer definitions, and candidate records |
| `reports/universe_v2_coverage_gap_analysis.md` | V1 gap audit and upgrade logic |
| `reports/universe_v2_expansion_plan.md` | This implementation plan and status summary |

## Universe Architecture

```text
Master Universe
  Full ETF maintenance and discovery
  Includes A-share ETF, QDII observe, commodity/resource, bond/cash, and future special assets

Research Universe
  Future replay / robustness / style-fit / regime research
  Requires history, liquidity, classification, duplicate control, and Main approval

Trade Pool
  Future formal strategy candidate pool
  Smaller, high-liquidity, representative, ETF-first
  Blocked until separate activation approval
```

## V1 Structure

V1 consists of:

- 183 ETF daily files in `data/etf_daily/`;
- 39 symbols in `data/backtest_trade_pool.csv`;
- 132 observe-pool symbols and 12 exclude-pool symbols in `reports/universe_quality_review.csv`;
- Phase 3 / 3.5 conclusions bound to Universe V1.

The 39-symbol trade pool remains a historical research baseline, not a current execution permission.

## V2 Design Principles

- Coverage before count.
- Low duplicate exposure.
- High-quality ETF first.
- No theme-chasing.
- No sacrifice of liquidity or history length.
- QDII is separate observation, not mixed with A-share ETF replay.
- Every promotion needs an explicit incremental research value.
- V1 conclusions remain bound to V1.

## Recommended V2 Candidate Tiers

### High Priority Research Candidates

These candidates address meaningful V1 coverage gaps and should be first in a future V2 validation batch.

| Symbol | Name | Exposure | Reason | Constraint |
| --- | --- | --- | --- | --- |
| 159301 | 公用事业ETF华夏 | utilities / defensive dividend | Adds missing public-service exposure | classification cleanup |
| 561560 | 电力ETF | power / dividend | Adds electricity sector behavior | classification cleanup |
| 562550 | 绿电ETF | green power / dividend | Adds green-power defensive/dividend proxy | duplicate check with 561560 |
| 159332 | 央企红利ETF富国 | central-SOE dividend | Improves value/dividend coverage | V2 liquidity screen |
| 159547 | 红利低波ETF华夏 | dividend low-vol | Adds low-vol factor | V2 duplicate screen |
| 159593 | 中证A50ETF | large-cap core / A50 | Broad-index representation beyond V1 A500 | avoid multiple A50 peers |
| 159531 | 中证2000ETF南方 | small-cap / CSI2000 | Adds small-cap breadth | liquidity and volatility validation |

### Medium Priority Research Candidates

These add useful representation but require stricter gating.

| Symbol | Name | Exposure | Reason | Constraint |
| --- | --- | --- | --- | --- |
| 515630 | 保险证券 | insurance / financial beta | Separate financial-cyclical exposure | unknown classification |
| 515260 | 电子ETF | electronics | Broader electronics beyond chip-only names | high volatility / unknown classification |
| 159732 | 消费电子ETF华夏 | consumer electronics | Demand-side technology proxy | V2 quality screen |
| 159613 | 信息安全ETF嘉实 | information security | Xinchuang/security coverage | V2 quality screen |
| 159538 | 信创ETF富国 | domestic substitution | Xinchuang exposure | theme overlap check |
| 159658 | 数字经济ETF华安 | digital economy | Digital economy coverage | theme overlap check |
| 159638 | 高端装备ETF嘉实 | high-end manufacturing | Manufacturing-cycle coverage | V2 liquidity screen |
| 159667 | 工业母机ETF国泰 | industrial machine | High-end manufacturing proxy | extreme-volatility review |
| 159516 | 半导体设备ETF国泰 | semiconductor equipment | Equipment exposure distinct from chips | volatility / duplicate check |
| 561360 | 石油ETF | oil and gas | Energy/resource exposure | classification cleanup |
| 159608 | 稀有金属ETF广发 | rare metals | Resource-cycle breadth | commodity robustness check |
| 510050 | 上证50ETF | classic large-cap | Large-cap defensive comparison | duplicate with A50/A500/CSI300 |
| 588220 | 科创100ETF基金 | STAR growth broad | Growth broad comparison | duplicate STAR 100 peer |
| 515880 | 证券公司ETF | securities high beta | High-liquidity conditional proxy | short history / high volatility |
| 588200 | 科创芯片ETF | STAR chip high beta | Very liquid high-beta stress proxy | high volatility |

### Observe-Only or Master-Only Candidates

These should be maintained or observed but not activated for V2 replay/trade without additional work.

| Symbol | Name | Exposure | Treatment | Reason |
| --- | --- | --- | --- | --- |
| 513180 | 恒生科技ETF | HK technology / QDII | QDII observe only | premium/FX/calendar handling required |
| 159941 | 纳指ETF | NASDAQ / QDII | QDII observe only | external-market calendar mismatch |
| 513050 | 中概互联网ETF | China internet / QDII | QDII observe only | QDII and high drawdown profile |
| 513520 | 日经ETF | Japan equity / QDII | QDII observe only | QDII handling required |
| 520550 | 港股红利低波ETF | HK dividend low-vol / QDII | QDII observe only | QDII plus watch-liquidity |
| 562920 | 信息安全 | information security | observe only | low liquidity and unknown classification |
| 516750 | 建材ETF | building materials | observe only | low liquidity and unknown classification |
| 516360 | 新材料ETF | new materials | exclude/observe only | ultra-low liquidity and unknown classification |
| 159315 | 黄金股ETF工银 | gold equities | observe only | low liquidity, high volatility, unknown classification |
| 159540 | 信创ETF易方达 | Xinchuang peer | observe only | duplicate peer for 159538 |
| 159551 | 机器人ETF国泰 | robotics peer | observe only | V1 already has robot representatives |
| 159558 | 半导体设备ETF易方达 | semiconductor equipment peer | observe only | duplicate plus high volatility |
| 159595 | 中证A50ETF大成 | A50 peer | observe only | duplicate peer for 159593 |

## Candidate Funnel

```text
Existing V1 Master: 183 ETF daily files
        |
        v
Coverage gap review
        |
        v
Named V2 candidates: 33
        |
        +--> High priority research candidates: 7
        +--> Medium priority research candidates: 15
        +--> Observe/master-only candidates: 11
        |
        v
Future gated work only:
classification refresh -> V2 quality review -> data coverage check -> V2 replay -> V1 vs V2 comparison -> Main decision
```

## Replay / Research Boundary

Universe V2 is not connected to replay in this batch.

Before V2 may enter replay:

1. Main approves a dedicated V2 data and quality-refresh batch.
2. V2 symbols have current daily data coverage.
3. Classification gaps are resolved.
4. QDII symbols are separated from A-share ETF replay or handled with explicit QDII rules.
5. Duplicate clusters are reduced to representative leaders.
6. Forward-label maturity and benchmark coverage are audited.
7. V1 vs V2 robustness comparison is planned separately.

## Impact on Prior Research

Phase 3 and Phase 3.5 remain valid under their stated Universe V1 scope. Universe V2 may broaden future external validity, but it does not retroactively change:

- Style Fit evidence qualification;
- Phase 3.5B robustness conclusions;
- Phase 3.5C governance permissions;
- readiness flags;
- Formal Execution status.

## Verification

Required Phase 4.1 checks:

- Universe V1 traceability: PASS via `configs/universe_versions/universe_v1.yaml`.
- Universe V2 candidate file: PASS via `configs/universe_versions/universe_v2_candidate.yaml`.
- Candidate inclusion reasons: PASS; each named candidate includes an inclusion reason.
- V2 does not affect Phase 3 / 3.5 conclusions: PASS; V1 binding is explicit.
- Formal / Shadow / Preview / Execution unchanged: PASS by file scope and status.
- Context validator: run after status update.

## Recommendation

Do not enter Phase 4.2 automatically. Recommended next Main decision is whether to approve a scoped V2 data coverage and quality-refresh batch. That next batch should refresh universe quality to the same latest data date before any V2 replay design.
