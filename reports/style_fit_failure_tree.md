# Style Fit Failure Tree

## Failure Tree Summary

Root failure: Phase 5.2 Generalization Verdict = FAILED_GENERALIZATION.

| Node | Contribution | Confidence | Evidence |
| --- | --- | --- | --- |
| Universe Shift | HIGH | HIGH | V2 has 5/16 HIGH_BETA_THEME, 3/16 DIVIDEND utilities/dividend, 0 BOND; V1 trade pool had 8 BOND and 8 COMMODITY_CYCLICAL. Actual V2 robustness base has no BOND rows and much larger high-beta/core concentration. |
| Cell Migration | MEDIUM | HIGH | Migration counts are {'CHANGED_DIRECTION_OR_CATEGORY': 6, 'DOWNGRADED': 3, 'UNCHANGED': 24, 'UPGRADED': 3}. Most cells are unchanged, but changed cells include support/conflict flips and loss of BOND support coverage. |
| Style Instability | HIGH | MEDIUM | BOND becomes unrecoverable, SECTOR_DEFENSIVE flips sign in OFFENSIVE/DEFENSIVE, HIGH_BETA_THEME remains special-style unstable in NEUTRAL, and COMMODITY_CYCLICAL is conditional/sample-dependent. |
| Regime Instability | MEDIUM | MEDIUM | NEUTRAL concentrates unstable/downgraded outcomes; OFFENSIVE and DEFENSIVE contain direction flips but also some support cells. |
| Horizon Conflict | HIGH | HIGH | Horizon robustness is CONFLICTING with directions {'1d': 'CONFLICT_BEATS_SUPPORTED', '3d': 'CONFLICT_BEATS_SUPPORTED', '5d': 'NEUTRAL', '10d': 'NEUTRAL', '20d': 'CONFLICT_BEATS_SUPPORTED'}; incremental value robustness is CONFLICTING. |
| Methodology Limitation | HIGH | MEDIUM | Same feature/ranking/regime/style mapping with only Universe changed produces a failed verdict; this points to Universe-sensitive style buckets, ETF-day dependence, and effective sample structure fragility. |
| Unknown / Residual | LOW | MEDIUM | Engineering coverage is clean and single-source. Residual uncertainty remains around untested style definitions and whether V2 history length is too short for some exposures, but no repository evidence proves another blocking cause. |

## Tree View

```text
FAILED_GENERALIZATION
|-- Universe Shift [HIGH / HIGH]
|   |-- V2 concentrated in HIGH_BETA_THEME, DIVIDEND/utilities, core index, commodities
|   `-- BOND evidence from V1 cannot be recovered because V2 has no BOND qualified ETF
|-- Cell Migration [MEDIUM / HIGH]
|   |-- 24 unchanged cells, but many are unchanged insufficient/descriptive cells
|   |-- 3 upgraded cells, including CORE_LARGE_CAP / NEUTRAL qualified conflict
|   |-- 3 downgraded cells, including BOND support coverage loss
|   `-- 6 changed-direction/category cells, including SECTOR_DEFENSIVE direction flips
|-- Style Instability [HIGH / MEDIUM]
|   |-- HIGH_BETA_THEME remains special-style unstable in NEUTRAL
|   |-- COMMODITY_CYCLICAL retains only conditional/sample-dependent behavior
|   `-- SECTOR_DEFENSIVE and CORE styles change sign/category across regimes
|-- Regime Instability [MEDIUM / MEDIUM]
|   |-- NEUTRAL concentrates downgrade/unstable/conflict outcomes
|   `-- OFFENSIVE/DEFENSIVE include support cells but not stable cross-horizon confirmation
|-- Horizon Conflict [HIGH / HIGH]
|   |-- 1d, 3d, 20d: conflict group beats supported group
|   |-- 5d, 10d: neutral
|   `-- incremental value robustness = CONFLICTING
|-- Methodology Limitation [HIGH / MEDIUM]
|   |-- coarse style buckets
|   |-- ETF-day pooling dependence
|   `-- effective sample structure differs from row count
`-- Unknown / Residual [LOW / MEDIUM]
    `-- no repository evidence of engineering defect, but untested style definitions remain uncertain
```

## Boundary

- No Formal Execution changes.
- No Shadow changes.
- No Preview creation.
- No Strategy / Ranking / Score changes.
- No Style Mapping or Regime Logic changes.
- No Universe V1 / V2 mutation.
- No data download.
- No replay rerun for optimization.

