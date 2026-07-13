# Tushare Point-in-Time Contract

## Status

- Scope: minimal, research-only staging proof
- Unified ETF price database: `data/etf_daily/` remains authoritative
- Historical replay admission: blocked unless this contract explicitly permits it
- Schema version: `1`

## Required Metadata

Every normalized row must have a separate PIT record containing:

`source`, `source_interface`, `entity_id`, `observation_date`, `period_end`, `announcement_date`, `source_update_window`, `retrieved_at`, `available_at`, `available_date`, `pit_basis`, `pit_confidence`, `pit_status`, `query_hash`, `raw_payload_hash`, and `schema_version`.

Business dates and historical availability dates are different concepts. A trade date, effective date, report period, or constituent entry date does not prove that the value was available to the project on that date.

## Status Definitions

| Status | Meaning | Historical-use policy |
|---|---|---|
| `PIT_RESOLVED` | A row-level availability anchor exists, such as a valid announcement date. | Allowed only with version preservation and contract tests. |
| `PIT_CONSERVATIVE` | Availability is assigned using a documented lag that avoids same-day look-ahead. | Allowed only under the specified conservative rule. |
| `PIT_PARTIAL` | An observation/effective date exists but historical publication time is not proven. | Forward collection or manual review; historical replay blocked by default. |
| `PIT_UNRESOLVED` | No reliable historical availability date can be reconstructed. | Description only; historical replay blocked. |
| `REJECT_FOR_HISTORICAL_BACKTEST` | No approved availability rule exists. | Rejected. |

## Interface Rules

### `fund_portfolio`

`end_date` is the reporting period and `ann_date` is the availability anchor. `available_date` must never precede `ann_date`. Multiple announcements for the same fund, period, and holding are retained as separate versions ordered by `ann_date`; a later revision must not overwrite the earlier historical version. Valid rows are `PIT_RESOLVED`.

### `daily_basic`

`trade_date` is an observation date, not a release timestamp. The default historical contract is `available_date = next observed trading day`, classified `PIT_CONSERVATIVE`. Negative PE values may be economically meaningful and are retained; missing valuation fields remain missing. A future retrieval-audited same-day rule would require proof that retrieval occurred after the confirmed source update window and is not approved by this batch.

### `index_daily`

The same conservative next-trading-day rule applies. Prices, volume, and amount are validated against the provider schema, but `trade_date` is not automatically treated as the historical availability date.

### `index_weight`

`trade_date` identifies a monthly snapshot. Without a row-level announcement/publication timestamp it is `PIT_PARTIAL`. Weight range, duplicate constituents, and per-snapshot weight sums are validated. Historical exposure use requires either a separately approved conservative lag or forward-collected versions.

### `index_classify` and `index_member_all`

Taxonomy rows without publication history are `PIT_UNRESOLVED`. Membership effective dates (`in_date`/`out_date`) provide structural history but not publication history, so member rows are `PIT_PARTIAL`. They may support current explanation or forward collection, not reconstructed claims that the classification was known on its effective date.

### `index_basic`

Current index metadata is `PIT_UNRESOLVED` unless historical metadata versions and publication dates are collected. It may assist dynamic sample resolution but does not establish historical availability.

### `shibor`

The date-level value uses the documented daily update pattern and a conservative noon Asia/Shanghai availability timestamp. It is `PIT_CONSERVATIVE`, not intraday tick evidence. Holiday gaps remain valid missing dates and must not be forward-filled across unknown publication times.

## Storage And Audit Rules

- Real responses, normalized samples, row-level PIT records, and validation details live under a unique `data/staging/tushare_minimal_proof/<run_id>/` directory.
- Run directories are immutable by convention and Git-ignored. A repeated run creates a new ID.
- Commit-safe reports contain hashes, counts, schemas, permission verdicts, and aggregate statistics, not authentication material or bulk vendor payloads.
- Query hashes exclude credentials. Raw hashes cover only the response bytes.
- The legacy sample under `data/staging/tushare/` remains `LEGACY_UNVERIFIED_SAMPLE`.
- No proof output is promoted into `data/etf_daily/`, Replay, Exposure Phase 2, Strategy, Ranking, Preview, or execution by this contract.
