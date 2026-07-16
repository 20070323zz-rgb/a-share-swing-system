# PR #4 Rebuild Decision

- Decision date: 2026-07-15
- Frozen PR: #4
- Frozen head: `3da9f038ea46f2e14a35ab0b38aa9b404386e628`
- Decision: `FROZEN_NEEDS_REBUILD`
- Replacement phase: `Reports Governance Phase A-R`
- Replacement base: `origin/main@8d145b4999f3af578abbc69472edd4f6809785c6`

PR #4 is preserved as failure-analysis and design evidence. It must not receive fix-forward commits, be merged, or supply Phase B candidates. The replacement branch was created independently from the latest `origin/main`; no PR #4 commit was cherry-picked and no PR #4 candidate classification is authoritative here.

PR #4 remains Draft/Open until the replacement Draft PR is created successfully. It may then be closed as `CLOSED / SUPERSEDED / NOT MERGED` with a link to the replacement PR.

Phase A-R does not move, rename, delete, or rewrite reports. It does not implement a runtime Path Registry, start Phase B, delete logs, or clean Availability data.
