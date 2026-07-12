# Effective Sample Coverage Audit

Validation date: 2026-07-08

Scope: repository-only audit of effective sample coverage after Phase 3.5B recovery validation. This batch did not modify Formal Execution, Shadow, Preview, Strategy, Scoring, or existing Phase 3 / Phase 3.5 research outputs. No data download was performed and no Phase 3 / 3.5 analysis was rerun.

## Executive Verdict

| Item | Verdict |
| --- | --- |
| Replay Coverage Verdict | `EXPLAINABLE` |
| ETF Coverage Verdict | `EXPLAINABLE` |
| Methodology Risk | `MEDIUM` |
| Coverage Risk | `MEDIUM` |
| Engineering Risk | `LOW` |

Core conclusion:

- Replay starts at `2025-05-30` because the replay context uses `data/backtest_trade_pool.csv` only, builds a strict common trading calendar across those 39 ETFs, and then skips the first `MIN_HISTORY_DAYS = 60` common trading days for feature warm-up.
- The 183 -> 39 ETF reduction is not caused by Phase 3.5B, style mapping, benchmark join, or forward labels. It is caused upstream by the universe quality review / backtest trade-pool design.
- Existing Phase 3 / 3.5 conclusions remain usable as research-only, caveated conclusions over the 39-ETF backtest pool and the `2025-05-30` to `2026-07-06` replay artifact window. They should not be promoted to broader 183-ETF universe conclusions without a separate expansion/replay batch.

## Evidence Sources

Primary files inspected:

- `src/ranking_model_v2_backtest.py`
- `src/phase4c_alpha_common.py`
- `src/market_regime_replay.py`
- `src/market_regime_stabilization.py`
- `src/style_regime_fit.py`
- `src/style_fit_robustness.py`
- `data/backtest_trade_pool.csv`
- `data/market_regime_replay.csv`
- `data/market_regime_stabilization_replay.csv`
- `data/style_fit_robustness_base.csv`
- `reports/universe_quality_review.csv`
- `reports/universe_quality_review.md`
- `reports/etf_risk_profile.csv`
- `reports/etf_risk_profile.md`
- `reports/style_regime_fit_source_audit.json`
- `reports/style_fit_robustness_source_audit.json`
- `docs/current_phase_status.json`
- `docs/current_project_state.md`

## Replay Timeline

```text
ETF daily files
  global local range: 2022-01-04 -> 2026-07-07
  183 files total

Backtest trade pool context
  data/backtest_trade_pool.csv: 39 ETFs
  loaded price_data: 39 ETFs
  strict common calendar across 39 ETFs: 2025-03-03 -> 2026-07-07, 328 common dates

Feature warm-up
  MIN_HISTORY_DAYS = 60
  common date index 0  = 2025-03-03
  common date index 59 = 2025-05-29
  common date index 60 = 2025-05-30

Replay artifact
  data/market_regime_replay.csv: 2025-05-30 -> 2026-07-06, 267 dates
  data/market_regime_stabilization_replay.csv: same 267 dates

Robustness base
  data/style_fit_robustness_base.csv: 2025-05-30 -> 2026-07-06
  267 dates x top 30 ranked rows per date = 8010 rows
```

The local ETF data now extends to `2026-07-07`, while the regime replay artifacts end at `2026-07-06`. This is already consistent with the current project state warning that the latest known regime snapshot is stale relative to latest data. It is not a replay-start explanation and does not by itself invalidate the historical audit.

## Part A. Replay Time Coverage Audit

| Layer | Observed Coverage | Limits Replay Start? | Reason | Normal Design? | Engineering Issue? |
| --- | --- | --- | --- | --- | --- |
| ETF Daily data | 183 files, global min/max `2022-01-04` -> `2026-07-07`; 175 files start `2025-03-03`, 5 start `2026-01-05`, 3 start `2022-01-04` | No, not directly | Full local directory is broader than replay context | Yes | No |
| Backtest trade pool | `data/backtest_trade_pool.csv` has 39 ETFs | Yes, by universe scope | `phase4c_alpha_common.load_context()` calls `ranking_model_v2_backtest.load_trade_pool()`, which reads the 39-ETF pool | Yes, but scope-limiting | No |
| Price data loading | 39 / 39 trade-pool ETFs loaded; no pool symbol lost | No additional start limit beyond pool | all 39 have valid OHLC and enough rows | Yes | No |
| Common date intersection | 39-ETF common calendar starts `2025-03-03` | Yes | `build_common_dates()` intersects all loaded ETF calendars; many pool ETFs start `2025-03-03` | Intentional but strict | No hidden bug; methodology caveat |
| Feature warm-up | first 60 common trading days skipped | Yes | `MIN_HISTORY_DAYS = 60`; `build_daily_rows()` also requires non-null `ret_60` | Yes | No |
| Regime feature availability | regime logic uses 510300, 159915, 518880 feature rows | Not beyond common + 60d warm-up | 518880 and many pool ETFs start `2025-03-03`; 60-day features mature at `2025-05-30` | Yes | No |
| Ranking replay | daily rows = 39 every replay date; ranked top30 every replay date | No additional date start loss | all 39 have features after warm-up | Yes | No |
| Benchmark coverage | 510300 benchmark labels available, joined on same T date as evaluation labels | No start loss | benchmark has longer history than replay; forward labels affect end maturity, not start | Yes | No |
| Style mapping coverage | `reports/etf_risk_profile.csv` has 183 profiles, 0 UNKNOWN style; 39 / 39 pool symbols covered | No | style map is complete for replay universe | Yes | No |
| Point-in-time replay construction | raw and stabilized replay both `2025-05-30` -> `2026-07-06` | No additional loss | stabilization transforms raw replay sequentially | Yes | No |
| Forward label maturity | 1d/3d/5d/10d/20d labels lose rows near the end | No start loss; end labels mature later | `_forward_return()` returns `None` if target date is beyond available data | Yes | No |
| Evaluation window | Phase 3 and Phase 3.5 read existing replay/base artifacts | No new start loss | research artifacts are bound to the replay artifact date range | Yes | No |

### Replay Start Root Cause

The true limiting chain is:

```text
data/backtest_trade_pool.csv
  -> 39 ETF replay universe
  -> strict common trading dates across those 39 ETFs
  -> common calendar starts 2025-03-03
  -> MIN_HISTORY_DAYS = 60
  -> replay starts at 2025-05-30
```

The 2022 daily history exists for a few ETFs, but it cannot move the replay start earlier under the current strict-common-calendar design because most effective replay-universe ETFs do not have common history before `2025-03-03`.

## Part B. ETF Coverage Funnel

### Symbol Funnel

| Stage | Count | Delta | Explanation |
| --- | ---: | ---: | --- |
| ETF daily files | 183 | - | Local `data/etf_daily/*.csv` files |
| ETF risk/style profiles | 183 | 0 | `reports/etf_risk_profile.csv`; data_quality ok; UNKNOWN style count 0 |
| Universe quality recommended trade_pool | 39 | -144 | `reports/universe_quality_review.csv`: 39 trade, 132 observe, 12 exclude |
| Backtest trade pool file | 39 | 0 | `data/backtest_trade_pool.csv`; all rows have `history/liquidity/classification pass` |
| Loaded price data | 39 | 0 | `ranking_model_v2_backtest.load_price_data()` loads all 39 |
| Common-date replay universe | 39 | 0 | all 39 survive common calendar construction |
| Daily ranking universe after warm-up | 39 | 0 | `build_daily_rows()` returns 39 rows per replay date |
| Daily top30 ranked rows | 39 unique / 30 per date | 0 unique, -9 rows per date | `rank_rows(..., top10_diversified_filter_v2)[:30]`; all 39 appear at least once across period |
| Style mapping after top30 | 39 | 0 | all ranked symbols have style profile |
| Forward label any horizon | 39 | 0 | all 39 have at least one forward label in robustness base |
| Robustness base | 39 unique, 8010 rows | 0 unique | 267 dates x top30 rows/date |

### Row Funnel Inside Robustness Base

```text
267 replay dates x 39 daily-ranked symbols = 10413 possible symbol-date rows
top30 filter keeps 267 x 30 = 8010 rows
row-level top30 filter loss = 2403 rows
unique-symbol loss from top30 over the full period = 0
```

Forward-label maturity by horizon in `data/style_fit_robustness_base.csv`:

| Horizon | Non-null Rows | Row Loss vs 8010 | Unique Symbols | Max Date with Non-null Label |
| --- | ---: | ---: | ---: | --- |
| 1d | 8010 | 0 | 39 | 2026-07-06 |
| 3d | 7950 | 60 | 39 | 2026-07-02 |
| 5d | 7890 | 120 | 39 | 2026-06-30 |
| 10d | 7740 | 270 | 39 | 2026-06-23 |
| 20d | 7440 | 570 | 39 | 2026-06-08 |

### Why 183 Became 39

The 183 -> 39 reduction occurs before replay, in universe-quality selection:

- `reports/universe_quality_review.csv`: 183 total ETFs
- recommended_pool:
  - `trade_pool`: 39
  - `observe_pool`: 132
  - `exclude_pool`: 12
- recommended_action:
  - `eligible_for_phase4a_backtest`: 39
  - `observe_only_before_backtest`: 82
  - `keep_best_liquidity_peer_in_trade_pool`: 40
  - `observe_or_small_weight_only`: 10
  - `exclude_before_backtest`: 12

Non-exclusive reason-token counts:

| Reason Token | Count |
| --- | ---: |
| `duplicate_exposure_lower_liquidity` | 123 |
| `classification_unknown` | 73 |
| `history/liquidity/classification pass` | 39 |
| `liquidity_low` | 22 |
| `high_volatility` | 15 |
| `qdii_needs_premium_fx_calendar_check` | 15 |
| `liquidity_ultra_low` | 12 |
| `extreme_volatility` | 5 |
| `history_lt_120d` | 5 |

This is a designed first-pass backtest/research universe, not accidental loss inside Phase 3.5B.

## Coverage Funnel Diagram

```text
183 ETF daily files
  | 0 lost: ETF risk/style profile covers all 183
  v
183 style-profiled ETFs
  | 144 moved out by universe quality review
  |   - 132 observe_pool
  |   - 12 exclude_pool
  v
39 recommended trade_pool ETFs
  | 0 lost loading price data
  v
39 loaded replay-context ETFs
  | 0 symbol loss, but date intersection starts 2025-03-03
  v
39 common-calendar ETFs
  | 60 common trading days skipped for feature warm-up
  v
39 replay-eligible ETFs from 2025-05-30
  | daily top30 ranking keeps 30 rows/date
  | 0 unique-symbol loss over full period
  v
39 unique ETFs / 8010 robustness rows
```

## Part C. Coverage Loss Classification

| Loss / Constraint | Category | Evidence | Interpretation |
| --- | --- | --- | --- |
| 183 -> 39 ETF universe | Normal design + Replay pipeline scope | `universe_quality_review` recommends 39 trade_pool; `data/backtest_trade_pool.csv` has 39 rows | Designed first-pass backtest pool |
| 144 ETFs outside trade pool | Normal design | observe/exclude reasons include QDII, unknown classification, low liquidity, duplicate exposure, short history, volatility | Not proof of missing data |
| Common calendar starts `2025-03-03` | Join intersection + feature coverage | `build_common_dates()` uses intersection across 39 loaded ETFs | Strict but explainable |
| Replay starts `2025-05-30` | Warm-up | `MIN_HISTORY_DAYS = 60`; common date index 60 is `2025-05-30` | Normal feature warm-up |
| Last replay artifact date `2026-07-06` while local data reaches `2026-07-07` | Artifact staleness | current project state warns stale regime snapshot | Minor operational staleness, not a historical start bug |
| Top30 row reduction | Replay pipeline design | Phase 3 / 3.5 signal interaction uses `rank_rows(... )[:30]` | Intentional signal-focused sample |
| Forward labels missing near end for longer horizons | Label maturity | `_forward_return()` returns `None` if future target is unavailable | Normal; affects end-of-window labels only |
| Benchmark labels mature earlier/later by horizon | Benchmark coverage / label maturity | benchmark returns are forward labels from 510300 | Normal evaluation-label behavior |
| Style profile loss | None found | 183 profiles, 0 UNKNOWN style, 39 / 39 pool covered | No issue |

## Part D. Anomaly Check

| Check | Finding | Impact |
| --- | --- | --- |
| Non-expected inner join | No hidden inner join found in Phase 3.5B. The strict common-date intersection is explicit in `build_common_dates()`. | No engineering defect; methodology caveat |
| Date intersection too strict | Strict by design across 39 ETFs; this shortens history to the latest-start effective pool members. | Coverage risk `MEDIUM`, not blocking |
| Replay start hardcoded | No direct hardcoded `2025-05-30` start found. Start is derived from common dates and `MIN_HISTORY_DAYS = 60`. | No issue |
| Benchmark data gap | No start gap found. Benchmark forward labels naturally mature by horizon. | No issue |
| Style mapping missing | None found. 183 style profiles, 0 UNKNOWN style in risk profile output; 39 / 39 replay symbols covered. | No issue |
| Signal replay coverage不足 | Daily rows = 39 each replay date; top30 = 30 each replay date; 39 unique symbols appear across top30 over full period. | No symbol-level coverage issue |
| Forward label提前截断 | Forward labels are absent near the end by design when future target date is unavailable. | Normal label maturity |
| Artifact staleness | Replay artifacts end `2026-07-06`; local daily files reach `2026-07-07`. | Known stale snapshot warning; not blocking for this audit |

### Effect on Existing Phases

| Phase | Impact |
| --- | --- |
| Phase 3 | Conclusions remain valid as research-only conclusions over the 39-ETF selected backtest pool and current replay window. They should not be generalized to the full 183-ETF pool. |
| Phase 3.5A | Robustness audit remains valid for its stated input base. Existing caveats about overlapping windows, cross-sectional dependence, and segment dependence remain important. |
| Phase 3.5B | Evidence qualification remains recoverable and internally consistent. The effective sample audit does not reveal a blocking engineering contradiction. |

No major engineering issue was found that proves existing research invalid. No immediate rerun of Phase 3, Phase 3.5A, or Phase 3.5B is recommended by this audit alone.

## Part E. Research Impact Assessment

1. Current Replay Coverage 是否足以支持已有研究？

Yes, for research-only / shadow-only conclusions over the current 39-ETF replay universe. Methodology risk remains `MEDIUM` because the date window is short, forward windows overlap, and the common-date universe starts in 2025.

2. Current ETF Coverage 是否足以支持已有 Robustness？

Yes, for robustness of the selected 39-ETF backtest pool. It is not sufficient to claim robustness across the full 183-ETF local data universe.

3. 当前是否需要立即扩充 ETF？

No immediate expansion is required to preserve existing Phase 3 / 3.5 conclusions. A future expansion batch may be useful if Main wants broader-universe evidence.

4. 当前是否需要重新下载历史数据？

No. The audit did not find evidence that missing downloads caused the 2025 start or 39-ETF universe. The limiting factors are current pool construction, common-calendar intersection, and warm-up.

5. 当前是否需要重新运行 Phase 3？

No, not from this audit alone. A rerun is only recommended if Main intentionally changes the effective universe, calendar policy, or replay construction.

6. 当前是否建议继续进入 Phase 3.5C？

Yes, after Main reviews this audit. Phase 3.5C can proceed as research output integration / shadow tracking design, but it should explicitly carry these caveats:

- evidence applies to the 39-ETF selected backtest pool;
- replay artifact window is `2025-05-30` to `2026-07-06`;
- full 183-ETF generalization requires a separate universe-expansion research batch;
- preview/scoring/execution remain blocked.

## Risk Breakdown

### Methodology Risk: `MEDIUM`

Reasons:

- Effective replay window is short relative to the full local data archive.
- Overlapping forward windows and cross-sectional dependence are already acknowledged in Phase 3.5A source audit.
- The top30 ranked-row design focuses on signal-relevant candidates, not the full ETF universe.

### Coverage Risk: `MEDIUM`

Reasons:

- 39 ETFs are enough for the current selected-pool robustness audit, but not enough to generalize to all 183 profiled ETFs.
- Common-date intersection across the selected pool materially shortens history.
- Some styles in the full universe are represented only indirectly or sparsely in the 39-pool sample.

### Engineering Risk: `LOW`

Reasons:

- No hardcoded replay start was found.
- No style mapping gap was found.
- No benchmark start gap was found.
- No unexpected Phase 3.5B join loss was found.
- Stale replay end date is already represented as a dated snapshot warning.

## Final Chinese Summary

1. 为什么 Replay 从 2025-05-30 开始：

不是因为本地 ETF 日线只有 2025 年数据，也不是因为 Phase 3.5B 硬编码了起点。真正链路是：Replay 使用 `data/backtest_trade_pool.csv` 的 39 个 ETF；这 39 个 ETF 的严格共同交易日从 `2025-03-03` 开始；排名/Regime 特征需要 `MIN_HISTORY_DAYS = 60` 的 warm-up；第 60 个共同交易日就是 `2025-05-30`。

2. 为什么 183 个 ETF 最终变成约 39 个：

183 个 ETF 都有本地日线和 style profile。数量收缩发生在上游 universe quality review：`reports/universe_quality_review.csv` 将 39 个推荐为 `trade_pool`，132 个放入 `observe_pool`，12 个放入 `exclude_pool`。原因包括重复暴露保留高流动性代表、unknown 分类、低流动性、QDII 需要额外检查、短历史和高波动。Phase 3 / 3.5 的 replay context 只读取这个 39-ETF backtest trade pool。

3. 哪些损失属于正常设计：

Universe 过滤到 39、共同日期交集、60 日 warm-up、每日 top30 ranked-row 样本、forward label 末端缺失，都属于当前研究设计。它们限制结论外推范围，但不是工程错误。

4. 哪些损失值得进一步关注：

值得关注的是方法学和覆盖范围，而不是立即修 bug。具体包括：39-ETF universe 不能代表完整 183 ETF；严格共同日期交集让 replay 从 2025 年开始；样本窗口短且 forward windows 重叠；当前 replay artifact 比最新日线数据晚一天，属于已知 stale snapshot。

5. 是否影响 Phase 3 与 Phase 3.5 的可信度：

不推翻已有结论。Phase 3 / 3.5 仍可信于“39-ETF selected backtest pool + 2025-05-30 至 2026-07-06 replay window + research-only/shadow-only”这个范围内。但不能把结论直接扩展为“183 ETF 全池充分验证”。

6. 是否建议继续推进 Phase 3.5C：

建议 Main 审阅本审计后继续推进 Phase 3.5C。理由是没有发现 blocking 工程问题，也不需要立即下载数据或重跑 Phase 3/3.5。Phase 3.5C 必须保留覆盖 caveat，且仍不得创建 adjusted preview、不得改 BUY ranking、不得接执行。
