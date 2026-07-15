---
artifact_type: GOVERNANCE_CONTROL
schema_version: reports-governance-phase-ar-build-v1
phase: Reports Governance Phase A-R
status: ACTIVE_PENDING_INDEPENDENT_QC
---

# Reports Governance Phase A-R Build Report

## Branch and PR governance

- clean-room base: `origin/main@8d145b4999f3af578abbc69472edd4f6809785c6`
- branch: `agent/reports-governance-phase-a-rebuild`
- Draft PR: `#5 / OPEN / DRAFT / MERGEABLE / CLEAN`
- PR #4: `CLOSED / SUPERSEDED / NOT MERGED`
- PR #4 frozen head: `3da9f038ea46f2e14a35ab0b38aa9b404386e628`
- PR #4 commits merged or cherry-picked: `0`
- report move/rename/delete/rewrite: `0`

## Salvage and rejection

The naming, metadata, immutable-write, Phase B contract, Availability lifecycle, PR #3 authority, Evidence schema, temporal, scope, and deprecated-path ideas were retained only after independent validation. Catalog, dependency, Evidence generation, location, migration, and deletion logic were independently reimplemented. All PR #4 safe/rename-required/92-candidate and historical fixed-count conclusions were rejected.

## Clean build results

| Gate | Result |
| --- | ---: |
| Inventory records | 644 |
| Duplicate report IDs | 0 |
| Structured references | 1,961 |
| Backstop references | 4,104 |
| Governance Evidence records | 6,946 |
| Unresolved Evidence IDs | 0 |
| Scanner disagreements | 35 |
| PR #4 known active regressions | 43/43 blocked |
| Regressions found by Backstop | 43/43 |
| Confirmed regression Producers found by Structured | 100% |
| Machine-provisional candidates | 52 |
| Candidate full review | 52/52 PASS |
| Final provisional dry-run candidates | 52 |
| Archived files in provisional candidates | 0 |
| Active Producer/Consumer/Backstop/Runtime/Unknown in provisional candidates | 0 |
| `SAFE_TO_DELETE_AFTER_AUTHORIZATION` | 0 |

The 35 scanner disagreements are explicit and fail closed. None enters the machine-provisional or final provisional set.

## Immutable snapshot

- snapshot namespace: `reports/governance/phase_ar/`
- governed snapshot files: 17 plus one manifest
- group manifest SHA-256: `86f1f31c6e128df6eeb4b9a259d822637c58f93f8053a2d8de8ab71bd5b33939`
- same-byte rerun: `18/18 IDEMPOTENT`
- different-byte occupied-path write: `FAIL_FAST / TESTED`
- three independent clean rebuilds: `BYTE_STABLE`

## PR #3 authority

- latest remote PR #3 head: `2602248a982ade26fdd4c957255c90d8708b19ef`
- Availability audit: `ACTIVE_COLLECTING`
- PR #3 Availability-owned leaf conflicts after deep merge: `0`
- Reports-owned PR #3 placeholder superseded: `reports_governance_phase_a_status` only
- unknown nested fields: preserved
- Reports-owned state: added without overwriting Availability values

## Validation

- full pytest: `67 passed, 2 pre-existing collection warnings, 8 subtests passed`
- Phase A-R focused suite: `14 passed`
- Dashboard build: `PASS`
- frontend production build: `PASS`
- App release check: `PASS`
- frontend dependency audit at install: `2 known findings (1 moderate, 1 high)`; build is unaffected and dependency remediation is outside this governance batch
- context validate/bootstrap: `VALID_WITH_WARNINGS`; only the known dated Regime stale warning
- `git diff --check`: `PASS`
- new private-path/secret hits: `0`

## ETF and protected boundaries

- canonical ETF files: `183`
- canonical content manifest SHA-256: `5d4d445c35809cfcc9cfbcaaf9b24a51275f5463a1a4b277d873003e1d676102`
- ETF per-file diff versus `origin/main`: `0/183`
- `src/paper_trade_engine.py`: unchanged, SHA-256 `93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926`
- `data/paper_trades.csv`: unchanged, SHA-256 `db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5`
- `data/paper_positions.csv`: unchanged, SHA-256 `a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906`
- App/Dashboard/Formal/Model/Replay/Ranking/Score/Exposure implementation diff: `0`

## End state and stop gate

```text
PR #4 = CLOSED / SUPERSEDED / NOT MERGED
Phase A-R = ACTIVE
Report Inventory = IMPLEMENTED_PENDING_INDEPENDENT_QC
Active Reference Index = IMPLEMENTED_PENDING_INDEPENDENT_QC
Migration Readiness = PROVISIONAL_PENDING_INDEPENDENT_QC
Deletion = BLOCKED
Phase B = BLOCKED
Runtime Path Registry = NOT_STARTED
Availability Audit = ACTIVE_COLLECTING (PR #3 authority)
Independent QC Readiness = YES
```

No Phase B work, report movement, log deletion, or Availability cleanup is authorized by this report.
