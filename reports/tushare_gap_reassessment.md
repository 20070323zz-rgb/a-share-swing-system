# Tushare Gap Reassessment

- Evidence mode: `real`
- Run status: `REAL_PROOF_COMPLETE`
- Proven accessible: `index_basic, index_daily, index_weight, index_classify, index_member_all, daily_basic, fund_portfolio, shibor`
- Permission/dependency/validation gaps: `none`

## Reassessment

This proof changes capability claims only where a real response and schema validation were observed. A configured token or a catalog response alone is not proof that dependent interfaces are usable.
Current ETF daily files remain the only ETF price source of truth. Tushare outputs are staged evidence, not a replacement database.
PIT-unresolved taxonomy or metadata may support current-state description, but must not enter historical replay without publication-time evidence or a conservative versioned rule.

## Exposure Gap Matrix

| Candidate | Newly available data | PIT readiness | Coverage | Maintenance | Incremental value | Overfitting risk | Status |
|---|---|---|---|---|---|---|---|
| Concentration Exposure | fund_portfolio + index_weight | PIT_RESOLVED for announced fund versions; index weights remain partial | minimal ETF/index samples | MEDIUM | HIGH | MEDIUM | HIGH_VALUE_REOPEN_CANDIDATE |
| Dividend Exposure | daily_basic dv_ratio/dv_ttm | PIT_CONSERVATIVE: next trading day | minimal constituents | LOW | HIGH | MEDIUM | HIGH_VALUE_REOPEN_CANDIDATE |
| Size Exposure | daily_basic total/circulating market value | PIT_CONSERVATIVE: next trading day | minimal constituents | LOW | HIGH | LOW | HIGH_VALUE_REOPEN_CANDIDATE |
| Sector Exposure | index taxonomy + member effective dates | PIT_PARTIAL/UNRESOLVED without publication history | one taxonomy/member sample | MEDIUM | HIGH | MEDIUM | RESEARCH_OBSERVATION |
| Value / Growth Exposure | valuation fields only; growth fundamentals absent | PIT_CONSERVATIVE for observed valuation | minimal constituents | MEDIUM | MEDIUM | HIGH | RESEARCH_OBSERVATION |
| Interest Rate Sensitivity | Shibor curve only; no ETF duration/cash-flow contract | PIT_CONSERVATIVE | short rate window | LOW | MEDIUM | MEDIUM | EXPLANATION_ONLY |

Top 3 for Main reassessment are Concentration, Dividend, and Size, conditional on the corresponding real access verdicts above. This is a governance recommendation only; Exposure Phase 2 remains not started.

## Next Gate

Formal Staging Architecture remains `NOT_STARTED`. Tushare Primary Upstream Migration, ETF Daily Availability Timing Audit, Data Foundation Upgrade, and Data Promotion have not been activated; Data Promotion remains `BLOCKED`. A future separately authorized engineering batch would still require schema-versioned ingestion and acceptance tests against the PIT contract.
