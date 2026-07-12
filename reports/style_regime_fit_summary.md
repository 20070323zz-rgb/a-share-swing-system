# Style-Regime Fit Summary

| Style | OFFENSIVE | NEUTRAL | DEFENSIVE |
| --- | --- | --- | --- |
| BOND | WEAK_SUPPORT / 10d med=0.000222 / excess=-0.013078 / n=1104 | SUPPORTED / 10d med=0.000422 / excess=0.004019 / n=464 | WEAK_SUPPORT / 10d med=0.000395 / excess=-0.016971 / n=496 |
| DIVIDEND | NEUTRAL / 10d med=0.002519 / excess=-0.016161 / n=414 | NEUTRAL / 10d med=-0.001301 / excess=-0.001952 / n=174 | WEAK_SUPPORT / 10d med=0.004096 / excess=-0.013824 / n=186 |
| LOW_VOL | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None |
| CORE_LARGE_CAP | SUPPORTED / 10d med=0.017378 / excess=0.000018 / n=552 | NEUTRAL / 10d med=-0.005215 / excess=-0 / n=232 | SUPPORTED / 10d med=0.02217 / excess=0.001515 / n=248 |
| CORE_MID_CAP | SUPPORTED / 10d med=0.018273 / excess=0.01134 / n=414 | NEUTRAL / 10d med=-0.004485 / excess=0.000715 / n=174 | SUPPORTED / 10d med=0.015158 / excess=0.005195 / n=186 |
| GROWTH_BROAD | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None |
| GROWTH_THEME | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None |
| SECTOR_CYCLICAL | NEUTRAL / 10d med=0.00651 / excess=-0.007272 / n=552 | CONFLICT / 10d med=-0.011625 / excess=-0.011463 / n=232 | NEUTRAL / 10d med=0.006984 / excess=-0.018667 / n=248 |
| SECTOR_DEFENSIVE | CONFLICT / 10d med=-0.007404 / excess=-0.020352 / n=966 | CONFLICT / 10d med=-0.010727 / excess=-0.004805 / n=406 | CONFLICT / 10d med=-0.009812 / excess=-0.025147 / n=434 |
| HIGH_BETA_THEME | SUPPORTED / 10d med=0.033086 / excess=0.013881 / n=276 | CONFLICT / 10d med=-0.016684 / excess=-0.01887 / n=116 | SUPPORTED / 10d med=0.016827 / excess=0.0001 / n=124 |
| COMMODITY_CYCLICAL | SUPPORTED / 10d med=0.021571 / excess=0.004926 / n=1104 | NEUTRAL / 10d med=-0.001799 / excess=-0.000969 / n=464 | SUPPORTED / 10d med=0.025123 / excess=0.006124 / n=496 |
| QDII_OBSERVATION | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None | INSUFFICIENT / 10d med=N/A / excess=N/A / n=None |

## Support by Regime
{
  "OFFENSIVE": [
    "BOND",
    "CORE_LARGE_CAP",
    "CORE_MID_CAP",
    "HIGH_BETA_THEME",
    "COMMODITY_CYCLICAL"
  ],
  "NEUTRAL": [
    "BOND"
  ],
  "DEFENSIVE": [
    "BOND",
    "DIVIDEND",
    "CORE_LARGE_CAP",
    "CORE_MID_CAP",
    "HIGH_BETA_THEME",
    "COMMODITY_CYCLICAL"
  ]
}

## Conflict by Regime
{
  "OFFENSIVE": [
    "SECTOR_DEFENSIVE"
  ],
  "NEUTRAL": [
    "SECTOR_CYCLICAL",
    "SECTOR_DEFENSIVE",
    "HIGH_BETA_THEME"
  ],
  "DEFENSIVE": [
    "SECTOR_DEFENSIVE"
  ]
}