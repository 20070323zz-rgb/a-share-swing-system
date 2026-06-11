# 因子有效性分析报告

本报告只用于研究分析。future returns 严禁参与当日 signal、ranking、composite_score 或 watch_score 计算。

## 样本数量提示
- 总样本行数：208
- 已有任一 future return 的样本行数：82

## Pearson correlation
| 因子 | future_5d_return | future_10d_return | future_20d_return | future_60d_return |
| --- | ---: | ---: | ---: | ---: |
| relative_strength | -0.067988 |  |  |  |
| return_20d | -0.061235 |  |  |  |
| return_5d | -0.146114 |  |  |  |
| volume_ratio | 0.085756 |  |  |  |
| composite_score | 0.047592 |  |  |  |
| watch_score | 0.01139 |  |  |  |

## Spearman Rank IC
| 因子 | future_5d_rank | future_10d_rank | future_20d_rank | future_60d_rank |
| --- | ---: | ---: | ---: | ---: |
| relative_strength | 0.060405 |  |  |  |
| return_20d | 0.048193 |  |  |  |
| return_5d | -0.055888 |  |  |  |
| volume_ratio | 0.141249 |  |  |  |
| composite_score | 0.044177 |  |  |  |
| watch_score | 0.049035 |  |  |  |

## Top-Bottom 分组收益
| 分组 | 样本数 | 平均 future_5d | 平均 future_10d | 平均 future_20d | 平均 future_60d |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top 5 | 5 | -0.071889 |  |  |  |
| Bottom 5 | 5 | -0.040362 |  |  |  |

## watch_score Top 5 未来收益表现
| 分组 | 样本数 | 平均 future_5d | 平均 future_10d | 平均 future_20d | 平均 future_60d |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top 5 | 5 | -0.044807 |  |  |  |

## 按 group 拆分表现
| group | 样本数 | 平均 composite_score | 平均 watch_score | 平均 future_20d | future_20d_top30 占比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 周期资源 | 24 | 33.071164 | 36.833333 |  |  |
| 宽基 | 35 | 49.112839 | 51.542857 |  |  |
| 新能源制造 | 32 | 22.321209 | 22.6875 |  |  |
| 消费医药 | 36 | 25.614146 | 21.5 |  |  |
| 科技成长 | 40 | 45.746378 | 53.8 |  |  |
| 金融地产 | 23 | 46.57278 | 46.347826 |  |  |
| 防御风格 | 18 | 46.729203 | 44.666667 |  |  |