# Structural Risk x Regime Forward Return

forward return 只作为 label，不参与 T 日 regime 判定。

| normalized_regime | structural_risk_profile | forward_horizon | sample_count | mean_forward_return | median_forward_return | positive_rate | benchmark_excess_mean | sample_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEFENSIVE | BALANCED | 5 | 348 | -0.0007 | -0.0012 | 0.4799 | -0.0115 | ok |
| DEFENSIVE | BALANCED | 10 | 348 | -0.0044 | -0.0110 | 0.3592 | -0.0219 | ok |
| DEFENSIVE | BALANCED | 20 | 324 | -0.0107 | -0.0161 | 0.3364 | -0.0414 | ok |
| DEFENSIVE | CORE | 5 | 522 | 0.0067 | 0.0070 | 0.6456 | -0.0041 | ok |
| DEFENSIVE | CORE | 10 | 522 | 0.0090 | 0.0077 | 0.6188 | -0.0085 | ok |
| DEFENSIVE | CORE | 20 | 486 | 0.0178 | 0.0170 | 0.6461 | -0.0130 | ok |
| DEFENSIVE | DEFENSIVE | 5 | 464 | 0.0010 | 0.0001 | 0.6444 | -0.0098 | ok |
| DEFENSIVE | DEFENSIVE | 10 | 464 | 0.0014 | 0.0004 | 0.6832 | -0.0162 | ok |
| DEFENSIVE | DEFENSIVE | 20 | 432 | 0.0022 | 0.0009 | 0.6829 | -0.0285 | ok |
| DEFENSIVE | HIGH_BETA | 5 | 174 | 0.0140 | 0.0118 | 0.6092 | 0.0032 | ok |
| DEFENSIVE | HIGH_BETA | 10 | 174 | 0.0202 | 0.0244 | 0.6954 | 0.0026 | ok |
| DEFENSIVE | HIGH_BETA | 20 | 162 | 0.0179 | 0.0297 | 0.6543 | -0.0128 | ok |
| DEFENSIVE | OFFENSIVE | 5 | 754 | 0.0118 | 0.0106 | 0.6101 | 0.0010 | ok |
| DEFENSIVE | OFFENSIVE | 10 | 754 | 0.0201 | 0.0189 | 0.6658 | 0.0025 | ok |
| DEFENSIVE | OFFENSIVE | 20 | 702 | 0.0384 | 0.0388 | 0.6809 | 0.0077 | ok |
| NEUTRAL | BALANCED | 5 | 312 | -0.0003 | -0.0045 | 0.4423 | -0.0015 | ok |
| NEUTRAL | BALANCED | 10 | 300 | -0.0073 | -0.0162 | 0.3367 | -0.0074 | ok |
| NEUTRAL | BALANCED | 20 | 288 | 0.0030 | -0.0108 | 0.4097 | -0.0082 | ok |
| NEUTRAL | CORE | 5 | 468 | 0.0008 | 0.0029 | 0.5491 | -0.0004 | ok |
| NEUTRAL | CORE | 10 | 450 | 0.0003 | 0.0031 | 0.5267 | 0.0002 | ok |
| NEUTRAL | CORE | 20 | 432 | 0.0087 | 0.0067 | 0.5625 | -0.0025 | ok |
| NEUTRAL | DEFENSIVE | 5 | 416 | -0.0002 | 0.0001 | 0.6562 | -0.0013 | ok |
| NEUTRAL | DEFENSIVE | 10 | 400 | 0.0001 | 0.0004 | 0.6975 | 0.0001 | ok |
| NEUTRAL | DEFENSIVE | 20 | 384 | 0.0013 | 0.0008 | 0.6875 | -0.0099 | ok |
| NEUTRAL | HIGH_BETA | 5 | 156 | 0.0019 | 0.0072 | 0.5513 | 0.0008 | ok |
| NEUTRAL | HIGH_BETA | 10 | 150 | -0.0075 | 0.0020 | 0.5133 | -0.0076 | ok |
| NEUTRAL | HIGH_BETA | 20 | 144 | 0.0097 | 0.0129 | 0.5347 | -0.0015 | ok |
| NEUTRAL | OFFENSIVE | 5 | 676 | -0.0041 | -0.0039 | 0.4512 | -0.0053 | ok |
| NEUTRAL | OFFENSIVE | 10 | 650 | -0.0102 | -0.0079 | 0.4062 | -0.0103 | ok |
| NEUTRAL | OFFENSIVE | 20 | 624 | 0.0041 | 0.0028 | 0.5048 | -0.0071 | ok |
| OFFENSIVE | BALANCED | 5 | 912 | -0.0003 | -0.0035 | 0.4353 | -0.0051 | ok |
| OFFENSIVE | BALANCED | 10 | 894 | 0.0003 | -0.0068 | 0.4508 | -0.0118 | ok |
| OFFENSIVE | BALANCED | 20 | 870 | -0.0076 | -0.0241 | 0.4195 | -0.0299 | ok |
| OFFENSIVE | CORE | 5 | 1368 | 0.0014 | 0.0011 | 0.5190 | -0.0033 | ok |
| OFFENSIVE | CORE | 10 | 1341 | 0.0049 | 0.0043 | 0.5585 | -0.0072 | ok |
| OFFENSIVE | CORE | 20 | 1305 | 0.0082 | 0.0062 | 0.5693 | -0.0142 | ok |
| OFFENSIVE | DEFENSIVE | 5 | 1216 | 0.0004 | 0.0001 | 0.6546 | -0.0043 | ok |
| OFFENSIVE | DEFENSIVE | 10 | 1192 | 0.0008 | 0.0003 | 0.6409 | -0.0113 | ok |
| OFFENSIVE | DEFENSIVE | 20 | 1160 | 0.0015 | 0.0007 | 0.6621 | -0.0209 | ok |
| OFFENSIVE | HIGH_BETA | 5 | 456 | 0.0032 | 0.0009 | 0.5066 | -0.0016 | ok |
| OFFENSIVE | HIGH_BETA | 10 | 447 | 0.0121 | 0.0092 | 0.5682 | -0.0000 | ok |
| OFFENSIVE | HIGH_BETA | 20 | 435 | 0.0225 | 0.0115 | 0.5471 | 0.0001 | ok |
| OFFENSIVE | OFFENSIVE | 5 | 1976 | 0.0097 | 0.0100 | 0.5941 | 0.0050 | ok |
| OFFENSIVE | OFFENSIVE | 10 | 1937 | 0.0215 | 0.0211 | 0.6551 | 0.0094 | ok |
| OFFENSIVE | OFFENSIVE | 20 | 1885 | 0.0379 | 0.0392 | 0.6626 | 0.0155 | ok |

## 限制
- 样本不足项标记 insufficient_sample。
- style / structural 来自最新静态画像；realized risk 使用 T 日 point-in-time 重新计算。