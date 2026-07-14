# Tushare ETF Daily Availability Timing Audit Status

- Generated at: `2026-07-14T15:08:05+08:00`
- Audit status: `ACTIVE_COLLECTING`
- Observation days started: `1`
- Observation days completed: `0`
- Valid stable observation days: `0`
- Timing evidence: `COLLECTING_INSUFFICIENT_DAYS`
- Tushare role: `SHADOW_PRIMARY_CANDIDATE`
- BaoStock role: `COMPARATOR_ONLY`
- Canonical ETF data: `data/etf_daily/` (unchanged)
- Primary upstream migration: `NOT_STARTED`
- Formal execution logic: `UNCHANGED`

## Schedule

- Tushare: `15:05, 15:15, 15:30, 15:45, 16:00, 16:15, 16:30, 17:00, 17:30, 18:00` CST
- BaoStock: `15:30, 16:30, 17:30, 18:00` CST
- A trading day is accepted only when confirmed by the cached Tushare trade calendar.

## Daily Progress

| Trade date | Status | Slots | First available | First complete | First stable | Last revision |
|---|---|---:|---|---|---|---|
| 2026-07-14 | IN_PROGRESS | 1/10 | - | - | - | - |

## Cross-Day Statistics And Safety Candidate

- Statistics status: `NOT_ISSUED_INSUFFICIENT_DAYS`
- FIRST_AVAILABLE P50 / P90 / worst: `- / - / -`
- FIRST_COMPLETE P50 / P90 / worst: `- / - / -`
- FIRST_STABLE P50 / P90 / worst: `- / - / -`
- Candidate first probe time: `NOT_ISSUED`
- Candidate retry interval: `15 minutes`
- Candidate safety cutoff: `18:00`
- Candidate maximum retries: `0`
- DATA_NOT_READY rule: No recommendation before five completed valid trading days.
- Paper execution rule: No change; the existing freshness gate remains authoritative.

## Decision Boundary

No safety-time or primary-source recommendation is issued before five valid days. Five-day evidence is preliminary; ten valid trading days are required before a supported timing verdict can be proposed to Main.
