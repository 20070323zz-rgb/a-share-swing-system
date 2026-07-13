# Tushare Real Run Attestations

## Scope

This attestation reconstructs commit-safe evidence for the three historical real runs without calling Tushare again, committing vendor payloads, exposing a Token, moving a run directory, or fabricating a missing report.

| Run ID | Executed at | Interfaces | Real calls | Budget | Remediated status | Manifest hash | Proof report hash | Evidence availability |
|---|---|---:|---:|---:|---|---|---|---|
| `real-20260713-minimal-proof` | 2026-07-13 10:21:44 +08:00 | 8 | 17 | 30 | `REAL_PROOF_PARTIAL` | `bdf1d732a8406a4ad1e6887d3e4fd86a7adefab166141829780cf9a7a733a2b0` | `UNAVAILABLE` | `AVAILABLE_EVIDENCE_LIMITED` |
| `real-20260713-minimal-proof-v2` | 2026-07-13 10:23:28 +08:00 | 8 | 17 | 30 | `REAL_PROOF_COMPLETE` | `778d708f6056d0762c0cb7c3522b2af40a45d758b548d20321a41fbb696e731c` | `UNAVAILABLE` | `AVAILABLE_EVIDENCE_LIMITED` |
| `real-20260713-minimal-proof-v3` | 2026-07-13 10:24:30 +08:00 | 8 | 17 | 30 | `REAL_PROOF_COMPLETE` | `6837bd6363bd8e0b0555110bec0d0f130efc5a5c82f9edbfeff3ce6a20299bce` | `1bdceca7b8ccfbd4ab2856c6c689ec03bcfba61fa4820d588a7a04c4b479e85e` | final commit-safe report retained |
| **Total** |  |  | **51** |  | `AGGREGATE_BUDGET_WARNING` |  |  | mock calls excluded |

All three runs exercised the same eight interface families: `index_basic`, `index_daily`, `index_weight`, `index_classify`, `index_member_all`, `daily_basic`, `fund_portfolio`, and `shibor`.

## Evidence Basis

- Manifest hashes were calculated from the retained immutable local run manifests.
- Interface lists were reconstructed from retained normalized artifact names and manifest metadata, not from a new request.
- `raw_payload_tracked=false` is supported by the Git tracked-file scan; the local raw artifacts remain under the ignored staging root.
- `token_exposed=false` records the commit-safe report/manifest scan result. No Token value is copied into this attestation.
- The final-run report hash points to the remediated `reports/tushare_minimal_staging_proof.md`.

## Limitations

The historical global report workflow overwrote the first two run-specific proof reports, so their individual proof-report hashes are unavailable. Their calls cannot be reproduced line by line from a committed report. The attestation therefore preserves the retained manifest hashes and explicitly labels the gap `AVAILABLE_EVIDENCE_LIMITED`; it does not infer or invent missing hashes. The legacy flat run directories remain in place by requirement, while new runs use mode-separated directories.
