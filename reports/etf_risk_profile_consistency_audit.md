# ETF Risk Profile 一致性审计

本报告分别对比 Structural Risk 与 Realized Risk，不要求人工 high_beta 必须与近期 realized HIGH_BETA 完全一致。

- 现有 high_beta 标的数：1
- high_beta structural 一致数量：1
- high_beta realized offensive 数量：0
- high_beta realized gap 数量：1
- broad_base 候选数量：10
- 债券 ETF 数量：15
- structural 冲突数量：0
- 冲突解释：Structural conflicts are potential taxonomy issues. Realized gaps are not automatically errors; they may reflect recent risk being lower/higher than stable asset character.

## high_beta structural 冲突
| symbol | name | structural_risk_score | structural_risk_profile | realized_risk_profile | style_profile | conflict_reason |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## high_beta realized gap（不自动视为错误）
| symbol | name | structural_risk_profile | realized_risk_profile | style_profile | gap_reason |
| --- | --- | --- | --- | --- | --- |
| 512880 | 证券ETF | HIGH_BETA | BALANCED | SECTOR_CYCLICAL | existing high_beta but recent realized risk is not OFFENSIVE/HIGH_BETA; this can be normal |

## broad_base 冲突
| symbol | name | type | structural_risk_score | structural_risk_profile | realized_risk_profile | style_profile | conflict_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## bond 冲突
| symbol | name | structural_risk_score | structural_risk_profile |
| --- | --- | --- | --- |
|  |  |  |  |