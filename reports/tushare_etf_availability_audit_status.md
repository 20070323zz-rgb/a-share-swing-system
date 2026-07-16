# Tushare ETF Daily Availability Timing Audit Status

- Generated at: `2026-07-16T00:23:24+08:00`
- Audit status: `ACTIVE_COLLECTING`
- Observation days started: `2`
- Observation days completed: `2`
- Valid stable observation days: `2`
- Timing evidence: `INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION`
- Tushare role: `APPROVED_PRIMARY_UPSTREAM`
- Decision evidence confidence: `LIMITED_TWO_DAY_EVIDENCE`
- Decision authority: `USER_AUTHORIZED_EARLY_PROMOTION`
- BaoStock role: `RECONCILIATION_ONLY`
- Canonical ETF data: `data/etf_daily/` (unchanged)
- Primary upstream migration: `AUTHORIZED_NOT_STARTED`
- Data promotion: `BLOCKED_PENDING_IMPLEMENTATION_VALIDATION`
- Formal execution logic: `UNCHANGED`

## Schedule

- Core Tushare: `16:00, 16:05, 16:10, 16:15, 16:30, 17:00` CST
- Conditional Tushare: `17:30, 18:00` CST
- Low-frequency health check (excluded from timing): `15:30` CST
- BaoStock: `15:30, 16:30, 17:30, 18:00` CST
- A trading day is accepted only when confirmed by the cached Tushare trade calendar.

## Daily Progress

| Trade date | Status | Observation state | Slots | First available | First complete | First stable | Last revision |
|---|---|---|---:|---|---|---|---|
| 2026-07-14 | COMPLETE | STABLE | 10/10 | 16:15 | 16:15 | 16:30 | - |
| 2026-07-15 | COMPLETE | STABLE | 10/10 | 16:15 | 16:15 | 16:30 | - |

## Cross-Day Statistics And Safety Candidate

- Statistics status: `NOT_ISSUED_INSUFFICIENT_DAYS`
- FIRST_AVAILABLE P50 / P90 / worst: `16:15 / 16:15 / 16:15`
- FIRST_COMPLETE P50 / P90 / worst: `16:15 / 16:15 / 16:15`
- FIRST_STABLE P50 / P90 / worst: `16:30 / 16:30 / 16:30`
- Candidate first probe time: `NOT_ISSUED`
- Candidate retry interval: `15 minutes`
- Candidate safety cutoff: `18:00`
- Candidate maximum retries: `0`
- DATA_NOT_READY rule: At 18:00, emit DATA_NOT_READY if no current field-quality-complete stable pair exists; preserve the existing SSOT and do not invoke BaoStock fallback. No timing recommendation is issued before five completed valid trading days.
- Paper execution rule: No change; the existing freshness gate remains authoritative.

## Migration Timing Design Candidate

- First formal staging fetch candidate: `16:15`
- Confirmation / validation / atomic-promotion candidate: `16:30`
- Fail-closed manual-review cutoff: `18:00`
- Formal promotion authorized: `false`

## Decision Boundary

Tushare adoption is already approved by user authorization. Five-day and ten-day evidence gates now govern only timing-window optimization and safety-buffer certification; they do not reopen the upstream-source decision. Formal promotion remains blocked until migration implementation and validation pass.
