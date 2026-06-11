# ETF 类型化持有周期研究报告

本报告是离线研究，不修改交易规则、不修改仓位、不写模拟买卖。

## 样本说明
- 分类 ETF 数量：114
- 研究结果行数：1962
- proxy_buy_signal：close > ma20 > ma60 且 20 日收益为正。
- short_swing_weakening：前一日 5 日收益为正，当日 5 日收益转弱。
- proxy_rank_decline_3d：价格动量代理分连续 3 日下降。
- 所有 future return 只用于离线研究，严禁参与当天信号。

## 按类型和窗口汇总
| etf_type | signal_type | window | avg_return | win_rate | max_forward_drawdown | return/drawdown | signal_count | evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| bond_cash | proxy_buy | 3 | 0.01% | 54.19% | -4.97% | 0.14 | 1252 | evidence_supported |
| bond_cash | proxy_buy | 5 | 0.02% | 55.18% | -4.97% | 0.18 | 1238 | evidence_supported |
| bond_cash | proxy_buy | 10 | 0.04% | 57.27% | -4.97% | 0.34 | 1203 | evidence_supported |
| bond_cash | proxy_buy | 20 | 0.06% | 54.97% | -7.88% | 0.60 | 1138 | evidence_supported |
| bond_cash | proxy_buy | 30 | 0.06% | 50.08% | -8.33% | 0.86 | 1079 | evidence_supported |
| bond_cash | proxy_buy | 60 | 0.25% | 61.94% | -9.05% | 1.63 | 942 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 3 | -0.01% | 62.85% | -4.51% | 0.83 | 313 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 5 | 0.04% | 70.83% | -4.51% | 1.23 | 313 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 10 | 0.04% | 64.66% | -4.67% | 1.96 | 307 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 20 | 0.11% | 68.03% | -6.58% | 3.64 | 298 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 30 | 0.17% | 68.86% | -7.04% | 5.11 | 292 | evidence_supported |
| bond_cash | proxy_rank_decline_3d | 60 | 0.45% | 67.72% | -7.04% | 9.93 | 267 | evidence_supported |
| bond_cash | short_swing_weakening | 3 | -0.01% | 61.16% | -2.83% | 0.26 | 288 | evidence_supported |
| bond_cash | short_swing_weakening | 5 | 0.02% | 59.61% | -3.25% | 0.37 | 286 | evidence_supported |
| bond_cash | short_swing_weakening | 10 | 0.04% | 64.47% | -4.98% | 0.67 | 283 | evidence_supported |
| bond_cash | short_swing_weakening | 20 | 0.10% | 64.55% | -6.95% | 1.23 | 275 | evidence_supported |
| bond_cash | short_swing_weakening | 30 | 0.24% | 66.93% | -7.40% | 1.79 | 263 | evidence_supported |
| bond_cash | short_swing_weakening | 60 | 0.57% | 73.43% | -7.40% | 3.47 | 237 | evidence_supported |
| broad_index | proxy_buy | 3 | 0.20% | 55.38% | -23.08% | 0.08 | 2114 | evidence_supported |
| broad_index | proxy_buy | 5 | 0.34% | 53.28% | -23.64% | 0.13 | 2100 | evidence_supported |
| broad_index | proxy_buy | 10 | 0.76% | 49.81% | -25.50% | 0.19 | 2059 | evidence_supported |
| broad_index | proxy_buy | 20 | 1.73% | 54.63% | -25.50% | 0.37 | 1916 | evidence_supported |
| broad_index | proxy_buy | 30 | 4.75% | 64.99% | -25.50% | 0.45 | 1803 | evidence_supported |
| broad_index | proxy_buy | 60 | 8.22% | 78.64% | -25.50% | 0.77 | 1766 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 3 | 0.52% | 63.79% | -9.68% | 0.18 | 592 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 5 | 1.01% | 67.55% | -9.68% | 0.31 | 588 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 10 | 1.12% | 61.01% | -15.96% | 0.29 | 580 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 20 | 2.87% | 66.82% | -15.96% | 0.56 | 518 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 30 | 3.85% | 71.50% | -16.37% | 0.71 | 509 | evidence_supported |
| broad_index | proxy_rank_decline_3d | 60 | 7.88% | 87.57% | -27.59% | 1.10 | 483 | evidence_supported |
| broad_index | short_swing_weakening | 3 | 0.17% | 53.03% | -8.35% | 0.09 | 565 | evidence_supported |
| broad_index | short_swing_weakening | 5 | 0.36% | 54.74% | -12.24% | 0.08 | 562 | evidence_supported |
| broad_index | short_swing_weakening | 10 | 0.51% | 53.28% | -16.97% | 0.07 | 540 | evidence_supported |
| broad_index | short_swing_weakening | 20 | 1.74% | 54.25% | -19.73% | 0.16 | 521 | evidence_supported |
| broad_index | short_swing_weakening | 30 | 2.72% | 58.03% | -20.38% | 0.24 | 508 | evidence_supported |
| broad_index | short_swing_weakening | 60 | 6.90% | 76.41% | -25.46% | 0.57 | 460 | evidence_supported |
| commodity_resource | proxy_buy | 3 | 0.61% | 56.73% | -18.88% | 0.06 | 2609 | evidence_supported |
| commodity_resource | proxy_buy | 5 | 0.91% | 59.58% | -18.88% | 0.08 | 2605 | evidence_supported |
| commodity_resource | proxy_buy | 10 | 1.88% | 62.69% | -53.82% | 0.14 | 2596 | evidence_supported |
| commodity_resource | proxy_buy | 20 | 3.96% | 67.10% | -55.08% | 0.22 | 2567 | evidence_supported |
| commodity_resource | proxy_buy | 30 | 6.38% | 66.93% | -27.02% | 0.40 | 2487 | evidence_supported |
| commodity_resource | proxy_buy | 60 | 11.68% | 77.73% | -58.35% | 0.70 | 2394 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 3 | 0.28% | 52.53% | -15.70% | 0.11 | 663 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 5 | 0.69% | 57.00% | -50.03% | 0.14 | 651 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 10 | 0.94% | 61.21% | -52.80% | 0.16 | 637 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 20 | 3.38% | 70.29% | -55.08% | 0.22 | 573 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 30 | 5.39% | 76.06% | -21.63% | 0.51 | 545 | evidence_supported |
| commodity_resource | proxy_rank_decline_3d | 60 | 12.48% | 86.11% | -21.63% | 1.11 | 475 | evidence_supported |
| commodity_resource | short_swing_weakening | 3 | 0.37% | 54.55% | -11.26% | 0.07 | 637 | evidence_supported |
| commodity_resource | short_swing_weakening | 5 | 0.57% | 56.96% | -12.00% | 0.07 | 634 | evidence_supported |
| commodity_resource | short_swing_weakening | 10 | 1.28% | 62.67% | -52.24% | 0.11 | 622 | evidence_supported |
| commodity_resource | short_swing_weakening | 20 | 2.56% | 63.30% | -48.60% | 0.17 | 602 | evidence_supported |
| commodity_resource | short_swing_weakening | 30 | 4.32% | 63.52% | -51.88% | 0.28 | 583 | evidence_supported |
| commodity_resource | short_swing_weakening | 60 | 12.67% | 83.64% | -56.29% | 0.77 | 516 | evidence_supported |
| hot_theme | proxy_buy | 3 | 0.42% | 59.50% | -9.26% | 0.04 | 163 | sample_limited |
| hot_theme | proxy_buy | 5 | 0.59% | 63.81% | -9.37% | 0.06 | 163 | sample_limited |
| hot_theme | proxy_buy | 10 | 1.01% | 59.11% | -12.14% | 0.08 | 159 | sample_limited |
| hot_theme | proxy_buy | 20 | 2.67% | 55.40% | -12.14% | 0.22 | 139 | sample_limited |
| hot_theme | proxy_buy | 30 | 1.34% | 46.62% | -15.02% | 0.09 | 133 | sample_limited |
| hot_theme | proxy_buy | 60 | -2.30% | 30.08% | -19.69% | 0.12 | 133 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 3 | -0.21% | 52.44% | -16.61% | 0.01 | 82 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 5 | 0.36% | 53.63% | -16.61% | 0.02 | 82 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 10 | 1.11% | 54.09% | -17.97% | 0.06 | 74 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 20 | 1.55% | 51.32% | -20.65% | 0.08 | 74 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 30 | 3.73% | 58.11% | -20.65% | 0.18 | 74 | sample_limited |
| hot_theme | proxy_rank_decline_3d | 60 | 7.26% | 75.74% | -20.65% | 0.35 | 66 | sample_limited |
| hot_theme | short_swing_weakening | 3 | -0.09% | 41.66% | -6.27% | 0.02 | 60 | sample_limited |
| hot_theme | short_swing_weakening | 5 | 0.11% | 46.61% | -9.23% | 0.02 | 60 | sample_limited |
| hot_theme | short_swing_weakening | 10 | 0.84% | 48.21% | -15.68% | 0.05 | 58 | sample_limited |
| hot_theme | short_swing_weakening | 20 | 0.88% | 46.55% | -20.65% | 0.04 | 58 | sample_limited |
| hot_theme | short_swing_weakening | 30 | 1.91% | 50.00% | -20.65% | 0.09 | 54 | sample_limited |
| hot_theme | short_swing_weakening | 60 | 4.08% | 58.26% | -20.65% | 0.20 | 48 | sample_limited |
| qdii | proxy_buy | 3 | 0.22% | 53.33% | -10.31% | 0.06 | 1375 | evidence_supported |
| qdii | proxy_buy | 5 | 0.46% | 53.38% | -11.05% | 0.09 | 1363 | evidence_supported |
| qdii | proxy_buy | 10 | 1.06% | 57.38% | -12.23% | 0.16 | 1331 | evidence_supported |
| qdii | proxy_buy | 20 | 2.25% | 64.46% | -21.26% | 0.23 | 1285 | evidence_supported |
| qdii | proxy_buy | 30 | 2.89% | 65.64% | -23.21% | 0.25 | 1241 | evidence_supported |
| qdii | proxy_buy | 60 | 3.35% | 59.07% | -25.95% | 0.25 | 1238 | evidence_supported |
| qdii | proxy_rank_decline_3d | 3 | 0.73% | 58.70% | -9.54% | 0.15 | 540 | evidence_supported |
| qdii | proxy_rank_decline_3d | 5 | 1.12% | 59.49% | -10.80% | 0.18 | 530 | evidence_supported |
| qdii | proxy_rank_decline_3d | 10 | 1.60% | 58.25% | -14.01% | 0.19 | 528 | evidence_supported |
| qdii | proxy_rank_decline_3d | 20 | 2.42% | 59.70% | -19.72% | 0.21 | 481 | evidence_supported |
| qdii | proxy_rank_decline_3d | 30 | 2.56% | 59.87% | -20.12% | 0.22 | 477 | evidence_supported |
| qdii | proxy_rank_decline_3d | 60 | 4.63% | 58.15% | -23.89% | 0.35 | 443 | evidence_supported |
| qdii | short_swing_weakening | 3 | 0.15% | 49.16% | -16.90% | 0.05 | 459 | evidence_supported |
| qdii | short_swing_weakening | 5 | 0.19% | 52.87% | -16.90% | 0.07 | 459 | evidence_supported |
| qdii | short_swing_weakening | 10 | 0.42% | 51.37% | -16.90% | 0.09 | 456 | evidence_supported |
| qdii | short_swing_weakening | 20 | 1.12% | 58.14% | -19.72% | 0.13 | 442 | evidence_supported |
| qdii | short_swing_weakening | 30 | 1.39% | 59.21% | -23.21% | 0.16 | 436 | evidence_supported |
| qdii | short_swing_weakening | 60 | 3.04% | 57.80% | -24.31% | 0.35 | 377 | evidence_supported |
| sector | proxy_buy | 3 | 0.31% | 54.83% | -7.14% | 0.08 | 1313 | evidence_supported |
| sector | proxy_buy | 5 | 0.47% | 55.70% | -7.98% | 0.11 | 1311 | evidence_supported |
| sector | proxy_buy | 10 | 0.72% | 54.79% | -12.02% | 0.16 | 1306 | evidence_supported |
| sector | proxy_buy | 20 | 1.21% | 50.00% | -15.65% | 0.31 | 1286 | evidence_supported |
| sector | proxy_buy | 30 | 0.25% | 47.43% | -21.15% | 0.17 | 1269 | evidence_supported |
| sector | proxy_buy | 60 | -1.41% | 39.83% | -27.00% | 0.16 | 1242 | evidence_supported |
| sector | proxy_rank_decline_3d | 3 | -0.03% | 44.31% | -11.46% | 0.17 | 707 | evidence_supported |
| sector | proxy_rank_decline_3d | 5 | 0.07% | 43.78% | -11.46% | 0.20 | 685 | evidence_supported |
| sector | proxy_rank_decline_3d | 10 | 0.24% | 48.34% | -11.88% | 0.24 | 675 | evidence_supported |
| sector | proxy_rank_decline_3d | 20 | 0.59% | 48.65% | -14.05% | 0.26 | 630 | evidence_supported |
| sector | proxy_rank_decline_3d | 30 | 0.56% | 52.60% | -18.01% | 0.25 | 613 | evidence_supported |
| sector | proxy_rank_decline_3d | 60 | 2.55% | 51.58% | -24.22% | 0.94 | 552 | evidence_supported |
| sector | short_swing_weakening | 3 | -0.38% | 46.50% | -65.73% | 0.08 | 631 | evidence_supported |
| sector | short_swing_weakening | 5 | -0.43% | 47.32% | -67.59% | 0.06 | 628 | evidence_supported |
| sector | short_swing_weakening | 10 | -0.52% | 45.74% | -67.85% | 0.08 | 622 | evidence_supported |
| sector | short_swing_weakening | 20 | -1.22% | 42.47% | -67.85% | 0.12 | 611 | evidence_supported |
| sector | short_swing_weakening | 30 | -1.15% | 42.12% | -67.85% | 0.14 | 585 | evidence_supported |
| sector | short_swing_weakening | 60 | -0.70% | 45.06% | -67.85% | 0.17 | 487 | evidence_supported |
| theme | proxy_buy | 3 | 0.72% | 57.57% | -66.73% | 0.07 | 1499 | evidence_supported |
| theme | proxy_buy | 5 | 1.22% | 60.81% | -66.73% | 0.11 | 1489 | evidence_supported |
| theme | proxy_buy | 10 | 2.54% | 62.52% | -67.18% | 0.21 | 1472 | evidence_supported |
| theme | proxy_buy | 20 | 4.50% | 63.82% | -67.18% | 0.30 | 1416 | evidence_supported |
| theme | proxy_buy | 30 | 6.31% | 63.94% | -64.70% | 0.37 | 1361 | evidence_supported |
| theme | proxy_buy | 60 | 8.07% | 60.91% | -60.38% | 0.39 | 1327 | evidence_supported |
| theme | proxy_rank_decline_3d | 3 | 0.76% | 64.96% | -18.65% | 0.13 | 540 | evidence_supported |
| theme | proxy_rank_decline_3d | 5 | 1.27% | 60.43% | -49.01% | 0.25 | 527 | evidence_supported |
| theme | proxy_rank_decline_3d | 10 | 1.15% | 58.90% | -52.84% | 0.18 | 510 | evidence_supported |
| theme | proxy_rank_decline_3d | 20 | 2.52% | 61.70% | -56.05% | 0.25 | 478 | evidence_supported |
| theme | proxy_rank_decline_3d | 30 | 4.26% | 63.37% | -57.65% | 0.34 | 474 | evidence_supported |
| theme | proxy_rank_decline_3d | 60 | 11.15% | 68.76% | -59.03% | 0.60 | 445 | evidence_supported |
| theme | short_swing_weakening | 3 | 0.33% | 51.40% | -10.42% | 0.05 | 491 | evidence_supported |
| theme | short_swing_weakening | 5 | 0.48% | 50.69% | -10.42% | 0.08 | 488 | evidence_supported |
| theme | short_swing_weakening | 10 | 0.94% | 51.43% | -62.72% | 0.13 | 478 | evidence_supported |
| theme | short_swing_weakening | 20 | 2.00% | 50.90% | -63.22% | 0.12 | 465 | evidence_supported |
| theme | short_swing_weakening | 30 | 3.61% | 56.20% | -57.65% | 0.21 | 451 | evidence_supported |
| theme | short_swing_weakening | 60 | 10.63% | 63.81% | -58.83% | 0.52 | 388 | evidence_supported |
| unknown | proxy_buy | 3 | 0.92% | 62.17% | -10.66% | 0.11 | 891 | evidence_supported |
| unknown | proxy_buy | 5 | 1.39% | 68.51% | -10.66% | 0.16 | 884 | evidence_supported |
| unknown | proxy_buy | 10 | 2.54% | 66.04% | -11.23% | 0.23 | 869 | evidence_supported |
| unknown | proxy_buy | 20 | 4.69% | 66.68% | -15.36% | 0.37 | 809 | evidence_supported |
| unknown | proxy_buy | 30 | 6.50% | 60.65% | -20.46% | 0.51 | 754 | evidence_supported |
| unknown | proxy_buy | 60 | 11.64% | 74.69% | -23.19% | 0.76 | 752 | evidence_supported |
| unknown | proxy_rank_decline_3d | 3 | 1.00% | 68.22% | -11.26% | 0.21 | 289 | evidence_supported |
| unknown | proxy_rank_decline_3d | 5 | 1.84% | 73.20% | -11.26% | 0.34 | 289 | evidence_supported |
| unknown | proxy_rank_decline_3d | 10 | 1.26% | 60.39% | -13.11% | 0.10 | 286 | evidence_supported |
| unknown | proxy_rank_decline_3d | 20 | 2.40% | 66.41% | -20.80% | 0.15 | 272 | evidence_supported |
| unknown | proxy_rank_decline_3d | 30 | 4.17% | 62.06% | -20.80% | 0.26 | 267 | evidence_supported |
| unknown | proxy_rank_decline_3d | 60 | 11.45% | 85.82% | -30.76% | 0.70 | 256 | evidence_supported |
| unknown | short_swing_weakening | 3 | 0.23% | 56.22% | -13.29% | 0.02 | 257 | evidence_supported |
| unknown | short_swing_weakening | 5 | 0.55% | 50.15% | -13.29% | 0.04 | 257 | evidence_supported |
| unknown | short_swing_weakening | 10 | 0.95% | 48.15% | -14.24% | 0.07 | 246 | evidence_supported |
| unknown | short_swing_weakening | 20 | 2.95% | 58.27% | -20.28% | 0.18 | 236 | evidence_supported |
| unknown | short_swing_weakening | 30 | 5.52% | 55.64% | -22.99% | 0.34 | 230 | evidence_supported |
| unknown | short_swing_weakening | 60 | 13.67% | 84.15% | -32.52% | 0.83 | 207 | evidence_supported |

## 重点判断
- 宽基是否适合 20-60 天：当前最佳窗口约 60 日，avg_return=22.42%，signal_count=114，证据等级=sample_limited。
- 行业是否更适合 10-30 天：当前最佳窗口约 20 日，avg_return=16.98%，signal_count=5，证据等级=hypothesis_only。
- 主题是否更适合 5-20 天：当前最佳窗口约 60 日，avg_return=19.59%，signal_count=106，证据等级=sample_limited。
- 强事件主题是否应 3-10 天：当前最佳窗口约 20 日，avg_return=2.71%，signal_count=69，证据等级=sample_limited。

## 当前持仓研究周期
| code | name | etf_type | holding_profile | conclusion |
| --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | 10-30 | 行业ETF关键词 |
| 515880 | 证券公司ETF | sector | 10-30 | 行业ETF关键词 |
| 515220 | 煤炭ETF | commodity_resource | 10-45 | 商品/周期资源关键词 |

## 结论边界
- evidence_supported：样本数量相对较多，可进入下一阶段模拟观察。
- sample_limited：样本有限，只能作为提示。
- hypothesis_only：样本不足或缺失，需要继续积累。
- 本报告不直接改变 mid_trend / short_swing / BUY ranking。