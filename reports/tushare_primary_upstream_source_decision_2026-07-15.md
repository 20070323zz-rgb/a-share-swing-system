# Tushare Primary Upstream Source Decision Audit — 2026-07-15

## Executive Decision

```text
Statistical Evidence Verdict: INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION
Architecture Decision: APPROVED_PRIMARY_UPSTREAM_BY_USER_AUTHORIZATION
Migration Decision: AUTHORIZED_TO_DESIGN_AND_IMPLEMENT
Formal Promotion: NOT_AUTHORIZED_FOR_FORMAL_PROMOTION_YET
Tushare role: APPROVED_PRIMARY_UPSTREAM
Decision Evidence Confidence: LIMITED_TWO_DAY_EVIDENCE
Decision Authority: USER_AUTHORIZED_EARLY_PROMOTION
BaoStock role: RECONCILIATION_ONLY
Primary Upstream Migration: AUTHORIZED_NOT_STARTED
Data Promotion: BLOCKED_PENDING_IMPLEMENTATION_VALIDATION
Canonical SSOT: data/etf_daily/ (unchanged)
Availability Audit: ACTIVE_COLLECTING
Timing Optimization: ACTIVE
```

Tushare has passed a two-day technical feasibility proof: on both observed trading days it reached `183/183` at `16:15 CST`, passed the requested field checks, and remained unchanged through `18:00`. Only 2 valid trading days exist, below the requested 3-day preliminary gate, the 5-day stability-certification gate, and the repository's stricter 10-day supported timing-candidate gate. That limitation remains fully controlling for statistical stability claims, but it no longer controls the architecture source-selection decision because the user has explicitly authorized early promotion of the architecture decision.

This is an architecture decision approval, not evidence that the formal chain has migrated. No formal production time or data promotion is approved. The audit continues to optimize the formal operating window and safety buffer; it will not reopen whether Tushare is the selected primary upstream.

## 1. Scope, Boundary, And Evidence Provenance

- Decision date: `2026-07-15`
- Evidence cutoff: `2026-07-15T18:02:20+08:00`
- PR: `#3`, Draft, open
- PR branch: `agent/tushare-etf-availability-audit`
- PR head: `2602248a982ade26fdd4c957255c90d8708b19ef`
- Main head inspected for SSOT comparison: `8d145b4999f3af578abbc69472edd4f6809785c6`
- Required universe hash: `f8bbffca7671c470c30cd418982bc4050c73cd10467c06eba77fa33063ca7f70`
- Authoritative scheduled manifests reviewed: `28` (`20` Tushare, `8` BaoStock)
- Evidence bundle SHA-256: `5679c4434a87ed63c12b8cad7e1577594a7e0fc50b38696971b920b96396b99f`

Evidence provenance limitation: the remote PR head at the time this report was first drafted contained the framework and committed evidence through 2026-07-14 16:30. The local PR worktree additionally contained ignored append-only manifests/snapshots through 2026-07-15 18:00 and three regenerated summary files. This decision preserves and incorporates that locally collected evidence without deleting the underlying staging artifacts. The decision report and sanitized summaries are now governed as PR #3 evidence; raw staging remains local and append-only.

The main checkout was already materially dirty before this audit, including runtime-updated SSOT/report files. This audit does not clean, revert, stage, or alter those files. Its only output is this report.

## 2. Evidence Coverage And Gate Status

| Gate | Requirement | Observed | Result |
|---|---:|---:|---|
| 1-day technical proof | 1 valid day | 2 valid days | PASS |
| 3-day preliminary conclusion | 3 valid days | 2 valid days | NOT_REACHED |
| 5-day stability-certification threshold | 5 valid days | 2 valid days | NOT_REACHED |
| Repository preliminary gate | 5 completed valid days | 2 valid days | NOT_REACHED |
| Repository supported candidate gate | 10 valid days + Main review | 2 valid days | NOT_REACHED |
| Extend to 10 days | Required for supported timing verdict | Yes | REQUIRED |

These gates certify timing stability only. They do not reopen the user-authorized architecture decision.

Both days were confirmed open by the cached Tushare `trade_cal`. There were no missed Tushare slots. The 2026-07-14 early-probe and duplicate-attempt manifests made zero vendor calls and are excluded from the 28 scheduled observations.

### Tushare observations

`EMPTY_UNEXPECTED` means the API call succeeded and permission passed, but the target-date table was empty. It is not an API failure. Manifest SHA-256 is the hash of the immutable manifest file; snapshot SHA-256 is the normalized 183-code content hash recorded inside the manifest.

| Trade date | Time | Count | API/result | Manifest SHA-256 | Snapshot SHA-256 |
|---|---:|---:|---|---|---|
| 2026-07-14 | 15:05 | 0/183 | EMPTY_UNEXPECTED / API access pass | `7809c7c2556648d4a26991174dca88d78b9aef8ef3f1303a8aaa42397a2cc634` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 15:15 | 0/183 | EMPTY_UNEXPECTED / API access pass | `96243ba4f5b95e6275f725787bfdbed17b610ac51499a45a1db12b09145ff061` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 15:30 | 0/183 | EMPTY_UNEXPECTED / API access pass | `1c01285fd907cdbfbd3cff47d3cf760854912c964e333ec99ddd3675832d5620` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 15:45 | 0/183 | EMPTY_UNEXPECTED / API access pass | `ed1acce8c1ce142222e58e2888c40bd90e86fb8c1b04b4287687b9e3051a89e5` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 16:00 | 0/183 | EMPTY_UNEXPECTED / API access pass | `59b0ae0a18951c3c478f43d8dde7de24bd6cdb91c6c77b6d602dd339186d7349` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 16:15 | 183/183 | ACCESS_PASS | `68875d74485f37eeac121a4f4478ed444bedbeb5b7d8aabecdfc151555ef7980` | `02b7ba803a743b8b9e689a90d5de3c7846d145eabfa3a48f9c59d9fc8e4e0ae7` |
| 2026-07-14 | 16:30 | 183/183 | ACCESS_PASS | `7070ba3a1d2d6ecb2b5760f9cac2e1a72fff0582f279605a1a2bfcefd0f630b7` | `02b7ba803a743b8b9e689a90d5de3c7846d145eabfa3a48f9c59d9fc8e4e0ae7` |
| 2026-07-14 | 17:00 | 183/183 | ACCESS_PASS | `f3f14c2b16433c67ea7e40e7800bfd73e325f3d3688d5b1cb72ef4e27f6b9baa` | `02b7ba803a743b8b9e689a90d5de3c7846d145eabfa3a48f9c59d9fc8e4e0ae7` |
| 2026-07-14 | 17:30 | 183/183 | ACCESS_PASS | `8c93f3c1ce4fda20c078eefe482b3208b8448dd653d8b41709449d287e54c510` | `02b7ba803a743b8b9e689a90d5de3c7846d145eabfa3a48f9c59d9fc8e4e0ae7` |
| 2026-07-14 | 18:00 | 183/183 | ACCESS_PASS | `e17537b5b94faebcdfd8fce7d7d3f08dc1bd50759568441288fcb874086c7282` | `02b7ba803a743b8b9e689a90d5de3c7846d145eabfa3a48f9c59d9fc8e4e0ae7` |
| 2026-07-15 | 15:05 | 0/183 | EMPTY_UNEXPECTED / API access pass | `c135577410d22906bcf96f5a352c106d109eba0625c60c71caaa0fdd40121bbc` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 15:15 | 0/183 | EMPTY_UNEXPECTED / API access pass | `68854f564926635e2a947d954a76ade6f29850d68cf2893808b20ea170123160` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 15:30 | 0/183 | EMPTY_UNEXPECTED / API access pass | `1238a3f79b2875c1f9d833f0111bb221affad07917ad36d6bb1f942517b897d8` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 15:45 | 0/183 | EMPTY_UNEXPECTED / API access pass | `2013d87554a71a10e404c46f7bfa24a95cf1eaa4c72fbc5ee6d9c79c5184a83d` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 16:00 | 0/183 | EMPTY_UNEXPECTED / API access pass | `8430a3982abb695d40ef643143dd301582c38118139e53dbf2d93099efa9887a` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 16:15 | 183/183 | ACCESS_PASS | `37aa67cb597a00f2010aa887021724080c9021e5e3d3215345f8aab45c3fceed` | `18954b4433f7b96d4251fd273aec1f35cd3b694bf21177191a6cf71e235b0608` |
| 2026-07-15 | 16:30 | 183/183 | ACCESS_PASS | `9cb0a49c6781e2a756e7b24a202d68db427224cca4f1bfe0a871e9c3f4ecafff` | `18954b4433f7b96d4251fd273aec1f35cd3b694bf21177191a6cf71e235b0608` |
| 2026-07-15 | 17:00 | 183/183 | ACCESS_PASS | `85aca55c9bd30a99b95407b6766136150db4dfe41635025756273f573815666f` | `18954b4433f7b96d4251fd273aec1f35cd3b694bf21177191a6cf71e235b0608` |
| 2026-07-15 | 17:30 | 183/183 | ACCESS_PASS | `c1c0650df0d04155a8bd081b7e52c56134245d2f742c62336d9933b05cbcf5f2` | `18954b4433f7b96d4251fd273aec1f35cd3b694bf21177191a6cf71e235b0608` |
| 2026-07-15 | 18:00 | 183/183 | ACCESS_PASS | `e3ea4db3c3574ff4f2c7ac166ad81397cf2e550348e1208b2a4b4fe07a625300` | `18954b4433f7b96d4251fd273aec1f35cd3b694bf21177191a6cf71e235b0608` |

Tushare API accounting: `20` scheduled calls, `20` permission/access successes, `10` empty target-date responses before publication, `10` non-empty successes, `0` network failures, `0` permission failures, and `0` validation failures.

### BaoStock observations

| Trade date | Time | Count | API/result | Manifest SHA-256 | Snapshot SHA-256 |
|---|---:|---:|---|---|---|
| 2026-07-14 | 15:30 | 0/183 | EMPTY_UNEXPECTED | `dcd27918b2106799f8b27290688238ea5bdb12fa89851476c2a6eae6eb2942e1` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 16:30 | 0/183 | EMPTY_UNEXPECTED | `ed131ec17ff9093ee280177e9bec62933b1c14b10a69daf78e32d771977f7d4e` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 17:30 | 0/183 | NETWORK_FAILED at login | `7fbd1a5f380994c878291eb586e72ad32af01ebaad64c6332a87385c8d50839b` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-14 | 18:00 | 183/183 | ACCESS_PASS | `3fc7f1cca85f74133eb137f2fe2149eb49014a99d2cb3c1edaee537bffbf2dd8` | `3e19e9dd22b30c5a57f389bd917ccde9cd89470d7e47ad83cb3070b4e86e11eb` |
| 2026-07-15 | 15:30 | 0/183 | EMPTY_UNEXPECTED | `b8e9e1b7a46d05647fb5d50317402f8b23d402cf94cd4fa450284024a586b9cc` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 16:30 | 0/183 | EMPTY_UNEXPECTED | `8f3129e380e5d0c159d19c2d8006ebea1102c5af864cccceb6ae68c6608c9d8c` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2026-07-15 | 17:30 | 183/183 | ACCESS_PASS | `ad81acd021050477ed959a61a11702016672d081ced15e3c2aabe91d8fb2156c` | `d07bc934fedb737a497bfd1b39ac0419faf5aa2b4649d8317306fb380f69fd1c` |
| 2026-07-15 | 18:00 | 183/183 | ACCESS_PASS | `bb5ff58cbbfb8d92a380b7d9da4d6186601a669c8aeb1a6a7240b7160c7d257d` | `d07bc934fedb737a497bfd1b39ac0419faf5aa2b4649d8317306fb380f69fd1c` |

BaoStock API accounting: `8` scheduled slots, `7` successful logins/query cycles, `1` login network failure, and `1,281` per-symbol requests across successful slots. The failed login made zero per-symbol requests.

## 3. Availability Timing

### Daily timing

| Trade date | FIRST_AVAILABLE | FIRST_COMPLETE | FIRST_STABLE | Last content change | 183/183 time | Evidence class |
|---|---:|---:|---:|---:|---:|---|
| 2026-07-14 | 16:15 | 16:15 | 16:30 | 16:15 (`0 -> 183`; not a non-empty revision) | 16:15 | VALID_DAY / LIMITED_TWO_DAY_EVIDENCE |
| 2026-07-15 | 16:15 | 16:15 | 16:30 | 16:15 (`0 -> 183`; not a non-empty revision) | 16:15 | VALID_DAY / LIMITED_TWO_DAY_EVIDENCE |

The original two-day report retrospectively labeled `FIRST_STABLE=16:15` because the complete 16:15 snapshot stayed unchanged through 18:00. That raw fact and prior interpretation are preserved. Under the activated confirmation-point definition, `FIRST_STABLE` records the confirming observation, so the same evidence is represented as `16:30`: 16:15 was first complete and 16:30 confirmed the identical manifest hash.

### Descriptive cross-day statistics

These figures describe only two days and are not an approved timing recommendation.

| Metric | P50 | P90 | Worst case |
|---|---:|---:|---:|
| FIRST_AVAILABLE | 16:15 | 16:15 | 16:15 |
| FIRST_COMPLETE | 16:15 | 16:15 | 16:15 |
| FIRST_STABLE (confirmation-point definition) | 16:30 | 16:30 | 16:30 |

### Safe-time decision

| Decision point | Current result | Reason |
|---|---|---|
| Earliest safe time | `NOT_ESTABLISHED` | Two days cannot establish a production-safe time. Observed first-complete is 16:15 and confirmation-point FIRST_STABLE is 16:30. |
| Initial implementation candidate | `16:15 STAGING / 16:30 VALIDATE_AND_ATOMIC_PROMOTION_CANDIDATE` | Authorized for migration design and implementation only; formal promotion remains blocked until implementation validation passes. |
| Timing optimization | `ACTIVE` | Five valid days may support an early-window review; ten days remain the supported timing-candidate gate. |
| Fallback review time | `18:00 MANUAL_REVIEW_CUTOFF` | At the configured cutoff, absence of a quality-complete stable snapshot must emit `DATA_NOT_READY`, preserve the old SSOT, and require manual review. It must not silently switch providers. |

## 4. Coverage And Field Quality

| Check | Result | Affected symbols | Affected dates | Severity |
|---|---|---:|---:|---|
| Universe mapping | 183/183 = 100%; SH 92, SZ 91 | 0 | 0 | PASS |
| End-of-day complete rate | 2/2 days = 100%; 366/366 required rows | 0 after 16:15 | 0 final snapshots | PASS_WITH_LIMITATIONS |
| Requested-field validation | 366/366 rows = 100% | 0 | 0 | PASS |
| Trade-date validation | All 366 rows equal requested confirmed trading day | 0 | 0 | PASS |
| OHLC non-null/numeric/positive | 366/366 | 0 | 0 | PASS |
| High/low relationship | 366/366 valid | 0 | 0 | PASS |
| Volume | 366/366 non-null, numeric, non-negative | 0 | 0 | PASS |
| Amount | 366/366 non-null, numeric, non-negative | 0 | 0 | PASS |
| Duplicate rows | 0 | 0 | 0 | PASS |
| Missing observed trading day | 0 of 2 in Tushare Shadow | 0 | 0 | PASS_WITH_LIMITATIONS |
| Suspended/zero turnover | 0 zero-volume and 0 zero-amount rows observed | 0 | 0 | PASS_WITH_LIMITATIONS |
| Code/exchange mapping | 183 unique local codes -> 183 unique `ts_code`; no duplicates/unmapped | 0 | 0 | PASS |
| New-listing-specific validation | No authoritative listing-date field in PR #3 evidence | unknown | unknown | INSUFFICIENT_EVIDENCE |

Both dates had all 183 codes missing from 15:05 through 16:00 and all 183 arrive together at 16:15. This is classified as `EXPECTED_LATE_COMPLETION`, not a symbol-level quality defect. It is nevertheless an operational timing constraint with `CAUTION` severity because any production job before publication would receive an empty target date.

The two-day quality results do not prove behavior for suspended ETFs, zero-turnover days, new listings, holidays around special schedules, or provider correction events because none occurred in this sample.

## 5. Revision Stability

| Trade date | Empty-to-full transition | Complete snapshots compared | Row changes after first complete | OHLC changes | Volume/amount changes | Codes added/removed after first complete | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-07-14 | 16:15, 183 codes | 16:15, 16:30, 17:00, 17:30, 18:00 | 0 | 0 | 0 | 0 / 0 | EXPECTED_LATE_COMPLETION then NO_REVISION |
| 2026-07-15 | 16:15, 183 codes | 16:15, 16:30, 17:00, 17:30, 18:00 | 0 | 0 | 0 | 0 / 0 | EXPECTED_LATE_COMPLETION then NO_REVISION |

- Revision count recorded by the observer: `0` on both dates.
- Material revision: `false` on every Tushare manifest.
- Unexplained revision: none observed.
- The manifest SHA-256 and raw-payload SHA-256 naturally change because every attempt has unique timestamps/metadata and the raw response covers the full market. Revision decisions use the normalized required-universe snapshot SHA-256, which is unchanged after 16:15 on both days.
- No `MATERIAL_REVISION` affecting a formal signal was observed, but two days are insufficient to estimate its future probability.

## 6. Existing Canonical SSOT Comparison

Comparison was read-only against the existing main-checkout `data/etf_daily/`. No data was written back.

### Date coverage

- Canonical inventory: 183 files; all 183 latest dates were `2026-07-14` at inspection.
- Tushare 2026-07-14: 183/183 overlap with Canonical SSOT.
- Tushare 2026-07-15: 183/183 Shadow rows, but zero same-date Canonical SSOT rows existed at inspection.
- The 2026-07-15 non-overlap is classified as current SSOT update lag / unavailable comparison, not a Tushare conflict.
- Canonical all-history duplicate trade-date rows across the 183 files: `0`.

### 2026-07-14 overlap results

| Field | Result | Classification |
|---|---|---|
| trade date | 183/183 exact | compatible |
| symbol mapping | 183/183 exact | compatible |
| open/high/low/close | 183/183 exact for every field | no conflict |
| pre-close | 183/183 exact | no conflict |
| volume | Tushare `vol` is hands; after `x100`, all 183 match within floating noise; max absolute difference `2.38e-7` shares | provider unit difference only |
| amount | Tushare `amount` is thousand CNY; after `x1000`, all 183 are within CNY 0.1; max CNY `0.052`, mean CNY `0.0061` | reasonable precision difference |
| adjustment convention | Canonical 2026-07-14 rows all have `adjustflag=3` (unadjusted); compatible with `fund_daily` raw daily prices | compatible for overlap date |
| duplicates / invalid prices | 0 / 0 | no conflict |

True conflicts found: `0` symbols and `0` dates in the one-day overlap.

Compatibility limitation: the Canonical SSOT contains historical rows from more than one acquisition/adjustment convention, while `fund_daily` provides unadjusted daily prices and separate unit conventions. A future migration must define a single explicit storage contract and must not infer historical adjustment compatibility from this one raw-date match.

## 7. BaoStock Role

### Timing and reliability

| Trade date | Tushare complete | BaoStock complete | BaoStock lag | BaoStock stable | Failure evidence |
|---|---:|---:|---:|---:|---|
| 2026-07-14 | 16:15 | 18:00 | 105 min | unresolved: no later point after first complete | 17:30 login network failure |
| 2026-07-15 | 16:15 | 17:30 | 75 min | 17:30 | none |

### Field comparison when BaoStock was complete

- 366/366 rows matched Tushare exactly for open, high, low, close, and pre-close.
- BaoStock volume matched after the same hands-to-shares `x100` normalization; maximum floating difference was `4.77e-7` shares.
- BaoStock amount matched after thousand-CNY-to-CNY `x1000` normalization; all 366 rows were within CNY 0.1 and the maximum difference was CNY `0.052`.
- BaoStock comparator snapshots lack `change` and `pct_chg` for all 366 rows, so the audit's broader requested-field completeness flag remains false even when core OHLCV/amount is complete.
- One complete BaoStock sweep costs 183 per-symbol calls versus one whole-date Tushare call.

```text
BaoStock role decision: RECONCILIATION_ONLY
Automatic fallback: NOT_ALLOWED
Silent provider switch: NOT_ALLOWED
```

BaoStock is too late and has one observed login-network failure. It can reconcile a completed Tushare snapshot after unit normalization, but using it automatically would risk a mixed-provider SSOT, field-shape differences, timing inconsistency, and partial-day promotion. Emergency use, if ever authorized separately, must be manual, whole-date, provider-tagged, fully validated, and atomically promoted; no such authorization exists here.

## 8. Quota And Operational Viability

### 5000-point permission and call sustainability

- The two-day evidence contains 20/20 successful `fund_daily` access/permission results.
- Tushare's current official `fund_daily` documentation requires at least 5000 points, allows up to 5000 rows per request, and reports volume in hands and amount in thousand CNY: <https://tushare.pro/document/2?doc_id=127>.
- The current official frequency table states that 5000+ points allow 500 calls/minute and no total cap for regular data: <https://tushare.pro/document/1?doc_id=290>.
- `trade_cal` currently requires 2000 points: <https://tushare.pro/document/2?doc_id=26>.
- Observed full-market `fund_daily` response size was 2,059 rows per call, below the documented 5,000-row limit; local filtering produced the required 183 rows.
- Audit load was 10 Tushare calls spread over three hours per trading day. A future production design would normally require one whole-date call plus bounded retries. Both are far below the documented 500 calls/minute limit.
- Tushare states points/permissions normally remain valid for one year; renewal and policy drift must be monitored. Therefore quota sustainability is `PASS_WITH_LIMITATIONS`, not unconditional.

### Runtime controls

| Item | Observed/current state | Assessment |
|---|---|---|
| Timeout | 25 seconds | bounded; acceptable for observer |
| Per-slot network retry | configured `0` | acceptable for measurement purity; insufficient as final production recovery policy |
| Scheduled retry cadence | 5–30 minutes through 18:00 under the activated schedule | adaptive observer only; production policy not implemented |
| Provider error classes | token missing, permission blocked, network failed, API/validation failed, empty target date | explicit and sanitized |
| Token safety | environment/local `.env` loader; token removed/redacted from manifests/errors; `token_exposed=false` | PASS_WITH_LIMITATIONS |
| LaunchAgent | reloaded from the 8-trigger template; idle after reload with no install-time vendor call | technically working, only two observed days |
| LaunchAgent setup incident | initial system Python lacked pandas; wrapper fixed and later runs succeeded | resolved setup defect, still limited history |
| Tushare API failures | 0 of 20 | promising, insufficient duration |
| BaoStock API failures | 1 of 8 slots | unsuitable for silent fallback |

### Mandatory production architecture gate

| Requirement | Current state | Gate |
|---|---|---|
| Write Tushare output to isolated staging first | Observer staging exists; formal upstream staging architecture not implemented | BLOCKED |
| Validate complete 183-code/date/schema/unit contract | Observer validates it; formal promotion validator not connected | BLOCKED |
| Atomic promotion into Canonical SSOT | Not implemented for Tushare | BLOCKED |
| Preserve old SSOT on any failure | Required by design, not implemented in a Tushare promotion path | BLOCKED |
| `DATA_NOT_READY` fail-closed | Defined in observer reporting logic, not connected to the formal download chain | BLOCKED |
| Prevent half-updated SSOT | No Tushare production promoter exists | BLOCKED |
| Prevent models from reading staging | Current observer is isolated; formal enforcement not yet implemented/tested | BLOCKED |
| Provider/date/unit provenance in promoted rows | Not implemented | BLOCKED |
| Rollback/recovery audit | Not implemented for Tushare promotion | BLOCKED |

The architecture decision is approved, but approval is not implementation. `Tushare Formal Staging Architecture = AUTHORIZED_NOT_STARTED` and `Data Promotion = BLOCKED_PENDING_IMPLEMENTATION_VALIDATION` remain correct.

## 9. App Backfill Button Impact

The current App backfill tasks call the existing BaoStock/JQData route. The source router explicitly returns `Tushare = NOT_IMPLEMENTED`. Therefore:

- The App button must not be changed in this decision audit.
- The button cannot be treated as proof that Tushare promotion or recovery exists.
- A future, separately approved implementation must make the button request a date, write Tushare to staging, validate 183/183 and field/unit/PIT contracts, atomically promote only on full pass, and return `DATA_NOT_READY` without modifying SSOT on failure.
- It must show provider/date/validation status and require manual review for any provider change.
- It must never expose staging directly to models, reports, paper execution, or the formal ledger.
- BaoStock must not be silently invoked when Tushare is empty or unavailable.

App change in this task: `NONE`.

## 10. Risks And Limitations

1. Only 2 valid trading days exist. This blocks five-day stability certification and formal timing claims, not the user-authorized architecture decision.
2. Both days have the same 16:15 outcome; there is no evidence across holidays, month-end, high-volume days, provider incidents, corrections, suspensions, or special market schedules.
3. New-listing behavior is not independently testable from PR #3 evidence because listing dates are not part of the audit universe manifest.
4. No material revision was observed, but a two-day zero-event sample cannot establish a reliable revision rate.
5. Only one trade date overlaps the current Canonical SSOT. The second Shadow date is ahead of the inspected SSOT, so SSOT compatibility has one-day direct evidence.
6. Later local manifests/snapshots are ignored and not present in the remote PR head, reducing remote reproducibility until separately governed evidence publication occurs.
7. The formal Tushare source router, staging validator, atomic promoter, recovery path, provenance contract, and App path do not exist.
8. The observer's zero network retries preserve timing evidence purity but are not a complete production retry strategy.
9. Tushare quota and point policy can change; current 5000-point sustainability requires entitlement renewal and periodic official-policy review.
10. BaoStock's later availability, missing change/pct_chg fields, per-symbol request pattern, and observed network failure prohibit silent automatic fallback.

## 11. Decision Matrix

| Dimension | Score | Evidence |
|---|---|---|
| Availability Timing | INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION | 2 valid days; both first-complete at 16:15 and confirmation-point stable at 16:30, below 3/5/10-day timing gates |
| Completeness | PASS_WITH_LIMITATIONS | 366/366 final rows and 183/183 both days; only two dates |
| Field Quality | PASS_WITH_LIMITATIONS | 100% requested-field pass, no invalid rows; no suspension/new-listing stress case |
| Revision Stability | PASS_WITH_LIMITATIONS | zero in-universe revisions through 18:00 on both days; sample too short |
| Operational Reliability | INSUFFICIENT_EVIDENCE | 20/20 Tushare calls without API failure and launchd last exit 0; only two days and formal path absent |
| Quota Sustainability | PASS_WITH_LIMITATIONS | 5000-point access proved; 1 whole-date call is efficient; annual renewal/policy drift and production telemetry remain |
| PIT Compliance | PASS_WITH_LIMITATIONS | confirmed trade calendar, immutable timestamped manifests, requested trade date, no earlier-date substitution; formal promotion PIT gate absent |
| SSOT Compatibility | PASS_WITH_LIMITATIONS | 183/183 exact OHLC/pre-close on one overlap date after explicit unit normalization; historical convention and second-date overlap unresolved |
| Fallback Design | FAIL | no validated failover design; BaoStock is later, field-incomplete, and had a network failure; silent fallback prohibited |
| Auditability | PASS_WITH_LIMITATIONS | append-only manifests, hashes, sanitized errors, no token/SSOT writes; later local evidence is not remotely present in PR #3 |

## 12. Final Determination

```text
Statistical Evidence Verdict: INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION
Architecture Decision: APPROVED_PRIMARY_UPSTREAM_BY_USER_AUTHORIZATION
Migration Decision: AUTHORIZED_TO_DESIGN_AND_IMPLEMENT
Formal Promotion: NOT_AUTHORIZED_FOR_FORMAL_PROMOTION_YET
Approved Primary Upstream: YES — architecture decision only
Decision Evidence Confidence: LIMITED_TWO_DAY_EVIDENCE
Decision Authority: USER_AUTHORIZED_EARLY_PROMOTION
Continue Availability Timing Audit: YES
Start Primary Upstream Migration Design: AUTHORIZED_NOT_STARTED
Start Report Migration: NO
Promote Data: NO
Modify App/Formal Download Chain/Model/Paper Engine/Ledger: NO
```

The evidence supports technical feasibility but is insufficient for a five-day stability certification or any long-term stability claim. The primary-upstream architecture selection is nevertheless approved by explicit user authorization. This approval permits design and implementation work; it does not mean the current formal chain has migrated and does not authorize formal data promotion.

## 13. Required Follow-Up

1. Continue the existing Shadow observer without deleting or rewriting temporary evidence.
2. Reach 5 completed valid trading days for a preliminary timing-window review; do not promote data automatically.
3. Continue to 10 valid trading days for a supported timing candidate, as required by the repository audit configuration.
4. Include at least one day with a later/abnormal publication or provider failure if naturally observed; do not create synthetic real-time evidence or substitute historical calls.
5. Add a governance-approved new-listing/suspension/zero-turnover review using already collected future evidence, not an ad hoc live call.
6. Re-run the read-only SSOT comparison for every naturally overlapping date and preserve provider-unit classification.
7. Under the new migration-design authorization, separately design and test staging-first validation, atomic promotion, unchanged-SSOT failure behavior, provenance, rollback, `DATA_NOT_READY`, and model isolation before requesting formal promotion.
8. Keep BaoStock reconciliation-only unless a separate, whole-date, no-mixed-provider emergency design is approved and validated.
9. Return to Main only for timing-window QC and formal-promotion authorization. Do not reopen the Tushare source-selection decision.

## 14. Chinese Summary

1. 有效观察交易日数量：`2`（2026-07-14、2026-07-15）。
2. 每日 FIRST_AVAILABLE：两日均为 `16:15`。
3. 每日 FIRST_COMPLETE：两日均为 `16:15`。
4. 每日 FIRST_STABLE：按新“确认时点”定义，两日均为 `16:30`；原报告的 `16:15` 回溯式标注及其后续四点哈希不变事实保留在正文中。
5. P50/P90/Worst Case：FIRST_AVAILABLE、FIRST_COMPLETE 均为 `16:15 / 16:15 / 16:15`；FIRST_STABLE 为 `16:30 / 16:30 / 16:30`；仅为两日描述统计，不是正式时点认证。
6. 183 只 ETF 完整率：mapping `183/183`；两日最终快照 `366/366`，100%。
7. 字段质量：OHLC、昨收、volume、amount、日期、代码均通过；零重复、零非法价格、零 high/low 异常、零负数、零零成交。新上市专项证据不足。
8. Revision：两日均为 16:15 从 0 一次性到 183，之后 `NO_REVISION`；无 Material Revision、无 unexplained revision。
9. SSOT 差异：2026-07-14 的 183 行 OHLC/昨收全量一致；volume `x100`、amount `x1000` 后一致，仅有最高 0.052 元舍入差；2026-07-15 SSOT 尚无同日行，属于当前 SSOT 更新滞后，不是供应商冲突。
10. BaoStock 角色：`RECONCILIATION_ONLY`；比 Tushare 晚 75–105 分钟，且出现 1 次登录网络失败，不允许静默自动 fallback。
11. 5000 积分可持续性：`PASS_WITH_LIMITATIONS`；已实证可调用 `fund_daily`，官方当前频率/总量足够，但权限年度有效、政策可能变化，需续期和监控。
12. 初期迁移实现候选：`16:15` 首次正式 staging 获取、`16:30` 确认/校验/原子 Promotion 候选、`18:00` fail-closed 人工复核截止；这不是正式 Promotion 授权。
13. 主要限制：仅 2 日；少于 3/5/10 日门槛；仅 1 日 SSOT 重叠；缺少新上市/停牌/修订压力样本；正式 staging/promotion/App 路径未实现；后续本地证据尚未进入远端 PR。
14. 统计证据结论：`INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION`；不得声称长期稳定。
15. 架构决策：`APPROVED_PRIMARY_UPSTREAM_BY_USER_AUTHORIZATION`；迁移设计与实现 `AUTHORIZED_TO_DESIGN_AND_IMPLEMENT`，正式 Promotion `NOT_AUTHORIZED_FOR_FORMAL_PROMOTION_YET`。

本报告完成后停止。Canonical SSOT、模型输入、paper trade engine、正式 ledger、App、正式下载链和报告迁移均保持不变；PR #3 继续保持 Draft。
