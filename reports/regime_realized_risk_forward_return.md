# Point-in-time Realized Risk x Regime Forward Return

forward return 只作为 label，不参与 T 日 regime 判定。

| normalized_regime | realized_risk_profile_pit | forward_horizon | sample_count | mean_forward_return | median_forward_return | positive_rate | benchmark_excess_mean | sample_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEFENSIVE | BALANCED | 5 | 435 | 0.0076 | 0.0070 | 0.6184 | -0.0038 | ok |
| DEFENSIVE | BALANCED | 10 | 435 | 0.0102 | 0.0086 | 0.5724 | -0.0073 | ok |
| DEFENSIVE | BALANCED | 20 | 403 | 0.0141 | 0.0053 | 0.5236 | -0.0156 | ok |
| DEFENSIVE | CORE | 5 | 361 | 0.0058 | 0.0046 | 0.6122 | -0.0054 | ok |
| DEFENSIVE | CORE | 10 | 361 | 0.0073 | 0.0051 | 0.5651 | -0.0101 | ok |
| DEFENSIVE | CORE | 20 | 333 | 0.0149 | 0.0101 | 0.5916 | -0.0149 | ok |
| DEFENSIVE | DEFENSIVE | 5 | 450 | 0.0023 | 0.0002 | 0.6800 | -0.0094 | ok |
| DEFENSIVE | DEFENSIVE | 10 | 450 | 0.0025 | 0.0004 | 0.6867 | -0.0148 | ok |
| DEFENSIVE | DEFENSIVE | 20 | 418 | 0.0044 | 0.0010 | 0.7010 | -0.0252 | ok |
| DEFENSIVE | HIGH_BETA | 5 | 437 | 0.0095 | 0.0081 | 0.5858 | -0.0019 | ok |
| DEFENSIVE | HIGH_BETA | 10 | 437 | 0.0123 | 0.0116 | 0.5995 | -0.0051 | ok |
| DEFENSIVE | HIGH_BETA | 20 | 405 | 0.0168 | 0.0131 | 0.5852 | -0.0131 | ok |
| DEFENSIVE | INSUFFICIENT_DATA | 5 | 148 | -0.0047 | -0.0018 | 0.4324 | -0.0065 | ok |
| DEFENSIVE | INSUFFICIENT_DATA | 10 | 148 | 0.0109 | 0.0097 | 0.7568 | -0.0094 | ok |
| DEFENSIVE | INSUFFICIENT_DATA | 20 | 148 | 0.0324 | 0.0301 | 0.8919 | -0.0123 | ok |
| DEFENSIVE | OFFENSIVE | 5 | 431 | 0.0121 | 0.0082 | 0.5870 | 0.0006 | ok |
| DEFENSIVE | OFFENSIVE | 10 | 431 | 0.0171 | 0.0107 | 0.5847 | -0.0003 | ok |
| DEFENSIVE | OFFENSIVE | 20 | 399 | 0.0299 | 0.0230 | 0.5815 | 0.0004 | ok |
| NEUTRAL | BALANCED | 5 | 321 | -0.0005 | -0.0026 | 0.4579 | 0.0008 | ok |
| NEUTRAL | BALANCED | 10 | 305 | -0.0047 | -0.0068 | 0.3934 | -0.0003 | ok |
| NEUTRAL | BALANCED | 20 | 289 | -0.0000 | -0.0059 | 0.4256 | -0.0013 | ok |
| NEUTRAL | CORE | 5 | 249 | -0.0026 | -0.0008 | 0.4699 | -0.0006 | ok |
| NEUTRAL | CORE | 10 | 235 | -0.0061 | -0.0045 | 0.4128 | -0.0002 | ok |
| NEUTRAL | CORE | 20 | 222 | -0.0040 | -0.0075 | 0.4324 | -0.0028 | ok |
| NEUTRAL | DEFENSIVE | 5 | 337 | -0.0005 | 0.0001 | 0.6083 | 0.0010 | ok |
| NEUTRAL | DEFENSIVE | 10 | 321 | -0.0009 | 0.0004 | 0.6511 | 0.0043 | ok |
| NEUTRAL | DEFENSIVE | 20 | 304 | 0.0004 | 0.0007 | 0.6414 | 0.0017 | ok |
| NEUTRAL | HIGH_BETA | 5 | 328 | -0.0103 | -0.0110 | 0.3598 | -0.0090 | ok |
| NEUTRAL | HIGH_BETA | 10 | 311 | -0.0229 | -0.0184 | 0.3119 | -0.0183 | ok |
| NEUTRAL | HIGH_BETA | 20 | 295 | -0.0123 | -0.0283 | 0.3593 | -0.0133 | ok |
| NEUTRAL | INSUFFICIENT_DATA | 5 | 481 | 0.0080 | 0.0052 | 0.7318 | -0.0016 | ok |
| NEUTRAL | INSUFFICIENT_DATA | 10 | 481 | 0.0096 | 0.0050 | 0.6861 | -0.0062 | ok |
| NEUTRAL | INSUFFICIENT_DATA | 20 | 481 | 0.0334 | 0.0287 | 0.8212 | -0.0111 | ok |
| NEUTRAL | OFFENSIVE | 5 | 312 | -0.0059 | -0.0079 | 0.3846 | -0.0043 | ok |
| NEUTRAL | OFFENSIVE | 10 | 297 | -0.0139 | -0.0165 | 0.3535 | -0.0085 | ok |
| NEUTRAL | OFFENSIVE | 20 | 281 | -0.0092 | -0.0260 | 0.3630 | -0.0076 | ok |
| OFFENSIVE | BALANCED | 5 | 1188 | 0.0017 | 0.0000 | 0.4840 | -0.0030 | ok |
| OFFENSIVE | BALANCED | 10 | 1166 | 0.0062 | 0.0031 | 0.5283 | -0.0059 | ok |
| OFFENSIVE | BALANCED | 20 | 1134 | 0.0100 | 0.0059 | 0.5309 | -0.0119 | ok |
| OFFENSIVE | CORE | 5 | 1021 | 0.0031 | 0.0020 | 0.5416 | -0.0020 | ok |
| OFFENSIVE | CORE | 10 | 1000 | 0.0073 | 0.0056 | 0.5810 | -0.0049 | ok |
| OFFENSIVE | CORE | 20 | 972 | 0.0115 | 0.0063 | 0.5833 | -0.0116 | ok |
| OFFENSIVE | DEFENSIVE | 5 | 1235 | -0.0002 | 0.0001 | 0.6308 | -0.0048 | ok |
| OFFENSIVE | DEFENSIVE | 10 | 1211 | 0.0004 | 0.0002 | 0.6243 | -0.0116 | ok |
| OFFENSIVE | DEFENSIVE | 20 | 1179 | 0.0005 | 0.0006 | 0.6446 | -0.0205 | ok |
| OFFENSIVE | HIGH_BETA | 5 | 1205 | 0.0061 | 0.0082 | 0.5651 | 0.0014 | ok |
| OFFENSIVE | HIGH_BETA | 10 | 1181 | 0.0152 | 0.0145 | 0.5936 | 0.0032 | ok |
| OFFENSIVE | HIGH_BETA | 20 | 1149 | 0.0217 | 0.0221 | 0.5857 | -0.0001 | ok |
| OFFENSIVE | INSUFFICIENT_DATA | 5 | 74 | 0.0073 | 0.0025 | 0.7432 | 0.0047 | ok |
| OFFENSIVE | INSUFFICIENT_DATA | 10 | 74 | 0.0151 | 0.0137 | 0.8378 | -0.0008 | ok |
| OFFENSIVE | INSUFFICIENT_DATA | 20 | 74 | 0.0553 | 0.0542 | 0.8919 | -0.0012 | ok |
| OFFENSIVE | OFFENSIVE | 5 | 1205 | 0.0082 | 0.0051 | 0.5519 | 0.0034 | ok |
| OFFENSIVE | OFFENSIVE | 10 | 1179 | 0.0177 | 0.0146 | 0.6132 | 0.0057 | ok |
| OFFENSIVE | OFFENSIVE | 20 | 1147 | 0.0304 | 0.0260 | 0.6059 | 0.0085 | ok |

## 限制
- 样本不足项标记 insufficient_sample。
- style / structural 来自最新静态画像；realized risk 使用 T 日 point-in-time 重新计算。