# Tushare Minimal Staging Proof

- Run ID: `real-20260713-minimal-proof-v3`
- Final status: `COMPLETE`
- Final-run HTTP request count: `17 / 30`
- Batch real HTTP request count: `51` across three immutable corrective runs (`AGGREGATE_BUDGET_WARNING`)
- Run-scoped staging: `data/staging/tushare_minimal_proof/real-20260713-minimal-proof-v3` (git-ignored)
- ETF daily SSOT write: `NONE`
- Formal / Strategy / Replay integration: `NONE`

## Interface Results

| Interface | Access | Permission | Raw rows | Proof rows | Schema | PIT |
|---|---|---|---:|---:|---|---|
| index_basic | ACCESS_PASS | ACCESS_PASS | 693 | 693 | ACCESS_PASS | PIT_UNRESOLVED |
| index_daily | ACCESS_PASS | ACCESS_PASS | 6 | 6 | ACCESS_PASS | PIT_CONSERVATIVE / PIT_PARTIAL |
| index_weight | ACCESS_PASS | ACCESS_PASS | 1350 | 900 | ACCESS_PASS | PIT_PARTIAL |
| index_classify | ACCESS_PASS | ACCESS_PASS | 31 | 31 | ACCESS_PASS | PIT_UNRESOLVED |
| index_member_all | ACCESS_PASS | ACCESS_PASS | 517 | 517 | ACCESS_PASS | PIT_PARTIAL |
| daily_basic | ACCESS_PASS | ACCESS_PASS | 3 | 3 | ACCESS_PASS | PIT_PARTIAL |
| fund_portfolio | ACCESS_PASS | ACCESS_PASS | 538 | 538 | ACCESS_PASS | PIT_RESOLVED |
| shibor | ACCESS_PASS | ACCESS_PASS | 11 | 11 | ACCESS_PASS | PIT_CONSERVATIVE |

## Governance

Raw responses, deterministic normalized samples, validation records and row-level PIT metadata are isolated under the run directory and are not committed.
The legacy `data/staging/tushare/tushare_etf_daily_sample.csv` remains `LEGACY_UNVERIFIED_SAMPLE` and was not overwritten.
No interface is admitted to historical replay unless its PIT contract is `PIT_RESOLVED` or an explicitly approved conservative rule applies.

## Evidence Boundaries

- Real API evidence: the interface matrix above, run-scoped response hashes, schemas, row counts, and PIT records from this run.
- Mock evidence: unit tests cover normal, empty, permission, network, schema, duplicate-key, unit, versioning, and PIT failure paths; mock PASS is not used as permission evidence.
- Official documentation: update patterns and units are sourced from the official URLs recorded in the interface matrix.
- Inference: conservative availability rules are governance choices designed to prevent look-ahead; they are not provider row-level timestamps.
- Unresolved: taxonomy publication history and snapshot publication times remain unavailable; the latest trade-date rows also need a future local trading-calendar date before next-day availability can be materialized.

## Versioning And Call-Budget Note

The final two-period `fund_portfolio` sample did not contain multiple announcement dates for one period. The primary key includes `ann_date`, and the mock test confirms that multiple announcement versions are retained rather than overwritten.

The final proof run stayed within the hard per-run cap at 17/30 requests. Two earlier immutable corrective runs also made 17 requests each, so this batch used 51 real requests in total and exceeded the suggested aggregate target of 30. No run exceeded the configured hard cap; the deviation is recorded rather than hidden.
