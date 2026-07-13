# Tushare 5000 Project-Specific Capability & Gap Audit

## Batch Header

- Batch Name: Tushare 5000 Data Foundation Audit
- Batch Type: Research
- Current Phase: Post Paper Execution Safety Phase 1
- Current Batch: Tushare 5000 Project-Specific Capability & Gap Audit
- Objective: Assess project-specific research value and produce a capability-gap matrix without integration
- Scope: Repository evidence plus official Tushare capability documentation; no download, staging implementation, or production change
- Audit Date: 2026-07-12
- State Treatment: `Tushare Audit Started`; `Data Foundation Upgrade = NOT_STARTED`

## 1. Executive Verdict

Tushare 5000 is **worth using selectively, but not as a wholesale data-foundation replacement**.

The highest project value is not another ETF OHLCV source. It is a small set of structured datasets that can close confirmed gaps in benchmark composition, industry taxonomy, holdings-based exposure, valuation, size, dividend, and rate-environment research.

Recommended policy:

```text
New Data Capability
        -> Gap Reassessment
        -> Small Staging Proof
        -> PIT / Coverage / Unit Validation
        -> Only Reopen High-Value Gaps
```

No current Regime, Exposure, Style Fit, Exit, Strategy, Ranking, Score, Preview, Shadow, Paper, or Formal conclusion is changed by this audit.

## 2. Audit Boundary and Evidence

Repository evidence is authoritative for project needs. Official Tushare documentation is used only to verify available fields and permission boundaries.

Important permission distinction:

- 5000 points can access useful established interfaces such as `index_weight`, `index_classify`, `index_member_all`, `sw_daily`, `daily_basic`, `fund_portfolio`, and Shibor.
- The newer ETF-specialized interfaces `etf_basic`, `etf_index`, and `etf_share_size` currently state an **8000-point** requirement, so they are not counted as Tushare 5000 capability. See the official [ETF basic](https://tushare.pro/document/2?doc_id=385), [ETF benchmark index](https://tushare.pro/document/2?doc_id=386), and [ETF share/size](https://tushare.pro/document/2?doc_id=408) pages.
- The full ChinaBond yield curve interface is separately permissioned rather than unlocked by 5000 points alone. See [ChinaBond yield curve](https://tushare.pro/document/2?doc_id=201).
- Points are permission thresholds, not a per-request balance consumed on every call. The practical cost is acquisition/retention and maintenance, not query-by-query point depletion. See [Tushare permission rules](https://tushare.pro/document/1?doc_id=108).

No Tushare API data was downloaded in this batch.

## 3. Confirmed Project Gaps

### 3.1 Data-caused gaps

| Confirmed gap | Why it matters | Core decision impact | Existing substitute | Reopen value |
|---|---|---|---|---|
| ETF-to-benchmark mapping and index methodology | Defines what an ETF structurally represents | High for Exposure 2.0 and benchmark governance | Names/manual metadata are incomplete | High |
| Historical index constituents and weights | Enables concentration, sector, size and fundamentals aggregation | High for Exposure 2.0 | Price beta is only an indirect proxy | High |
| ETF/fund holdings with disclosure dates | Enables holdings-based concentration and sector attribution | High, subject to ETF coverage | No equivalent structured repository dataset | High |
| Stable industry taxonomy and PIT membership | Prevents ad hoc sector labels | High for sector exposure | Existing style labels are too coarse | High |
| Valuation, dividend, market-cap fundamentals | Supports value/growth/dividend/size exposure research | Medium-high | Price-derived factors cannot replace fundamentals | High |
| Fund AUM and shares | Supports capacity, liquidity quality and fund-flow context | Medium | Traded amount is not fund size | High, but 5000-specific access is limited |
| Interest-rate term structure | Supports rate sensitivity and rate regime | Medium | Shibor covers money-market rates only | Medium |
| Commodity/FX benchmarks | Supports direct commodity and QDII sensitivity | Medium for selected assets | ETF-price proxies are indirect | Medium |

### 3.2 Gaps not primarily caused by missing data

- Style Fit 1.0 failed Universe V2 generalization. More fields do not repair the original framework; it remains `V1-SPECIFIC_FINDING`.
- Exit Logic is blocked by research/governance sequencing, not by inability to compute trade paths. Existing daily OHLC can already support daily MFE/MAE and path analysis.
- Preview and Formal Execution are blocked by governance and evidence readiness, not by missing Tushare datasets.
- Price-derived Exposure expansion is frozen by governance. New data may justify a separate Phase 2 design, but does not automatically reopen Phase 1.

## 4. Capability Gap Matrix

The machine-readable matrix is `reports/tushare_priority_matrix.csv`. The decisive interfaces are summarized below.

| Interface | Current capability | Project need | Gap resolution | Priority | Recommended layer | Main risk |
|---|---|---|---|---|---|---|
| `fund_basic` | Fund dates, type, investment type, text benchmark and metadata | ETF metadata and benchmark clues | Partial | HIGH | STAGING_CANDIDATE | Benchmark may be unstructured text |
| `fund_portfolio` | Quarterly holdings with announcement/end dates and market-value ratios | Holdings/concentration/sector attribution | Potentially strong | HIGH | STAGING_CANDIDATE | ETF coverage and disclosed-scope completeness must be proven |
| `index_basic` | Index publisher, category, weighting rule, description | Benchmark registry/methodology | Strong metadata support | HIGH | STAGING_CANDIDATE | Methodology history may still be incomplete |
| `index_weight` | Monthly constituents and weights | Concentration and constituent aggregation | Strong | HIGH | STAGING_CANDIDATE | Coverage varies by index publisher |
| `index_classify` | SW 2014/2021 hierarchy | Stable industry taxonomy | Strong | HIGH | STAGING_CANDIDATE | Taxonomy version must be explicit |
| `index_member_all` | Industry membership with in/out dates | PIT sector membership | Strong | HIGH | STAGING_CANDIDATE | Availability date still needs ingestion governance |
| `daily_basic` | Stock PE/PB/PS/dividend yield/shares/market cap | Value, dividend, size aggregation | Strong when joined to PIT weights | HIGH | STAGING_CANDIDATE | Aggregation and reporting-date semantics |
| `sw_daily` | Industry OHLC, PE/PB, turnover and market cap | Sector environment and Regime explanation | Partial/strong | MEDIUM | STAGING_CANDIDATE | Multiple testing and taxonomy drift |
| `index_dailybasic` | Selected broad-index valuation and turnover | Valuation regime | Partial | MEDIUM | STAGING_CANDIDATE | Only a limited index set is covered |
| `shibor` | Daily money-market curve from overnight to one year | Liquidity/rate environment | Partial | MEDIUM | STAGING_CANDIDATE | Not a bond-duration curve |
| `fund_daily` | ETF OHLCV/amount | ETF prices | No material new gap closed | LOW | NOT_REQUIRED | Duplicate source and unit-normalization burden |

Official field evidence: [index constituents and weights](https://tushare.pro/document/2?doc_id=96), [SW industry classification](https://tushare.pro/document/2?doc_id=181), [SW membership](https://tushare.pro/document/2?doc_id=335), [SW daily data](https://tushare.pro/document/2?doc_id=327), [stock daily fundamentals](https://tushare.pro/document/2?doc_id=32), [broad-index daily fundamentals](https://tushare.pro/document/2?doc_id=128), and [Shibor](https://tushare.pro/document/2?doc_id=149).

## 5. Module-by-Module Assessment

### 5.1 Regime Layer

Potential high-value additions for a future Regime 2.0 study:

- `daily_basic` plus PIT stock universe: market breadth by market cap, valuation and turnover.
- `index_dailybasic`: a compact broad-index valuation/turnover environment.
- `sw_daily`: sector breadth, dispersion, valuation and liquidity environment.
- `shibor`: money-market liquidity and short-rate environment.
- PMI, CPI/PPI, money supply and social financing: slower macro explanation variables.

Assessment:

- These datasets can improve **economic interpretation and robustness testing**.
- They do not invalidate or automatically replace the completed Regime 1.0 framework.
- Macro series require release-date and revision governance. Observation period must use the value actually available at T, not a revised historical value.
- Broad feature expansion creates a serious multiple-testing risk; only pre-registered variables should enter a future Regime 2.0 design.

### 5.2 Exposure Framework

High-value Phase 2 candidates that become more feasible:

| Exposure candidate | Required Tushare chain | 5000 feasibility | Audit treatment |
|---|---|---|---|
| Sector Exposure | benchmark/holdings -> `index_member_all` -> weights | Partial to strong | Reassess after staging proof |
| Concentration Exposure | `index_weight` or validated `fund_portfolio` | Strong for supported indices | Highest reopening value |
| Dividend Exposure | PIT weights/holdings + `daily_basic.dv_ttm` | Strong in principle | High-value candidate |
| Size Exposure | PIT weights/holdings + `daily_basic.total_mv/circ_mv` | Strong in principle | High-value candidate |
| Value/Growth Exposure | PIT weights/holdings + valuation/fundamentals | Partial | Value is nearer-term; growth needs more statement data |
| Interest Rate Sensitivity | Shibor and ideally yield curve + ETF returns | Partial | Shibor prototype only; full term structure unavailable at 5000 alone |

The official `daily_basic` interface supplies PE, PB, PS, dividend yield, shares and market capitalization, while `index_weight` supplies constituent weights. This pairing is the most important 5000-point capability for a transparent, PIT-aware Exposure Phase 2 prototype.

### 5.3 Style Fit

Tushare can support a **new holdings/factor-based exposure framework**, not a repair of Style Fit 1.0.

Allowed interpretation:

- Test whether holdings-derived sector, size, dividend, value and concentration variables explain behavior that coarse style labels failed to generalize.

Forbidden interpretation:

- Add more fields, tune thresholds, and claim Style Fit 1.0 is restored.
- Map new data directly to BUY ranking, score, preview or execution.

### 5.4 Exit Logic

Core path analysis, daily MFE/MAE, adverse excursion and failure attribution are already possible from the unified ETF OHLC database.

Tushare may add explanatory context such as sector conditions, valuation, rates or liquidity, but these are **secondary attribution variables**, not prerequisites for starting a separately approved Exit Logic research batch. Minute data and sentiment feeds are not recommended for the current weekly swing horizon because they add large maintenance and overfitting costs without closing a confirmed bottleneck.

## 6. Top Five Data Capabilities

Ranked by project value at the 5000-point boundary:

1. `index_weight`: direct historical constituents and weights for concentration and constituent-level aggregation.
2. `daily_basic`: valuation, dividend, shares and market-cap fields needed for fundamental exposure research.
3. `index_classify` + `index_member_all`: maintainable industry taxonomy and membership dates.
4. `fund_portfolio`: holdings-based concentration and sector attribution, conditional on an ETF coverage proof.
5. `index_basic` + `index_daily`: benchmark registry and benchmark return history.

`sw_daily` and `shibor` are the next most useful additions for Regime explanation and future validation.

## 7. Data Not Recommended

### Reject or not required

- `fund_daily` as a replacement ETF database: existing daily data is authoritative, and prior repository staging found OHLC consistency but material provider unit differences in volume/amount.
- Hot lists, topic rankings, limit-up ladders, “winning rate”, proprietary technical factors and news-derived scores: no confirmed core gap, unstable definitions, high narrative/overfitting risk.
- Vendor-specific money-flow labels: difficult to reproduce and easy to misuse as a retrospective explanation.
- Minute/Tick data: excessive cost for the current swing horizon and not required for daily MFE/MAE.

### High value but unavailable at 5000 alone

- `etf_basic`: structured ETF-to-index mapping, current official requirement 8000.
- `etf_index`: ETF benchmark registry and adjustment cycle, current official requirement 8000.
- `etf_share_size`: daily shares/AUM/NAV, current official requirement 8000.
- `etf_sh_cons` / `etf_sz_cons`: daily pre-market ETF creation/redemption baskets, current official requirement 8000. See the official [Shanghai ETF basket](https://tushare.pro/document/2?doc_id=471) and [Shenzhen ETF basket](https://tushare.pro/document/2?doc_id=472) pages.
- `yc_cb`: full ChinaBond yield curve, separately permissioned.

These should remain explicit future gaps rather than being quietly substituted with lower-quality fields.

## 8. Staging Recommendation

Do not download all available Tushare data. If Main authorizes a later Engineering batch, the first staging proof should be small and dependency-ordered:

```text
Stage 1: fund_basic + index_basic
Stage 2: index_weight + index_classify + index_member_all
Stage 3: daily_basic for only Stage 2 constituents and required dates
Stage 4: fund_portfolio coverage sample for the current ETF universes
Stage 5: index_daily / index_dailybasic / sw_daily / shibor research context
```

Required gates before any research use:

- Preserve `data/etf_daily/` as the only ETF price source of truth.
- Store Tushare outputs only in a separate staging namespace, never as a second ETF daily database.
- Record `event_date`, `ann_date`, `available_date`, ingestion timestamp, source interface and query parameters.
- Validate code suffixes, units, duplicates, index coverage and delisted constituents.
- Use as-of joins; never forward-fill a constituent or classification before it became available.
- Report missingness by ETF, benchmark, date and field before reopening an Exposure or Regime question.

## 9. Risk Assessment

| Risk | Level | Reason |
|---|---|---|
| Data maintenance risk | MEDIUM | Multiple entity types, codes, units and update calendars |
| PIT leakage risk | HIGH before governance | Announcements, constituent changes and macro revisions need availability dates |
| Provider dependency risk | MEDIUM | Useful metadata and fundamentals would become provider-specific |
| Duplicate-source risk | HIGH if `fund_daily` is integrated | Conflicts with ETF single source of truth |
| Overfitting risk | HIGH for sentiment/news; MEDIUM for broad feature expansion | Many candidate fields can create post-hoc narratives |
| Core execution risk | LOW in this audit | No data or execution integration occurred |

## 10. Final Recommendation

### Is 5000 worth it?

**YES, conditionally**, if 5000 access is already available or can be maintained at reasonable cost and is used for the five prioritized structured datasets. It is not justified for bulk acquisition, duplicated ETF prices, hot-topic feeds or indiscriminate macro ingestion.

The strongest immediate research value is the chain:

```text
index_weight
  + industry membership
  + daily_basic fundamentals
  -> holdings/index-weighted Sector, Concentration, Dividend, Size and Value research
```

### Next stage

Recommend a separately approved **Tushare Minimal Staging Proof & PIT Contract** Engineering batch, limited to a small ETF/benchmark/date sample. The proof should validate access, historical coverage, update latency, PIT fields and units before any full staging build.

Do not start Regime 2.0, Exposure Phase 2, Style Fit repair or Exit Logic from this audit alone.

## 11. Validation

- Production code modified: NO
- Strategy / Ranking / Score modified: NO
- Formal / Shadow / Preview modified: NO
- Exposure formulas modified: NO
- Paper execution modified: NO
- `data/etf_daily/` modified by this batch: NO
- Tushare data downloaded: NO
- Second ETF database created: NO
- Data Foundation Upgrade: `NOT_STARTED`
- Tushare Audit state: `STARTED`, pending Main review
