# 因子有效性分析报告

本报告只用于研究分析。future returns 严禁参与当日 signal、ranking、composite_score 或 watch_score 计算。

## 样本数量提示
- 总样本行数：775
- 已有任一 future return 的样本行数：460

## Pearson correlation
| 因子 | future_5d_return | future_10d_return | future_20d_return | future_60d_return |
| --- | ---: | ---: | ---: | ---: |
| relative_strength | 0.10171 | 0.102334 |  |  |
| return_20d | 0.015973 | 0.059872 |  |  |
| return_5d | -0.059271 | -0.063616 |  |  |
| volume_ratio | -0.171799 | -0.121671 |  |  |
| composite_score | 0.158227 | 0.237682 |  |  |
| watch_score | 0.152465 | 0.21932 |  |  |

## Spearman Rank IC
| 因子 | future_5d_rank | future_10d_rank | future_20d_rank | future_60d_rank |
| --- | ---: | ---: | ---: | ---: |
| relative_strength | 0.152497 | 0.299244 |  |  |
| return_20d | 0.141945 | 0.28232 |  |  |
| return_5d | 0.026614 | 0.00534 |  |  |
| volume_ratio | -0.041616 | 0.036121 |  |  |
| composite_score | 0.18586 | 0.262731 |  |  |
| watch_score | 0.247472 | 0.282377 |  |  |

## Top-Bottom 分组收益
| 分组 | 样本数 | 平均 future_5d | 平均 future_10d | 平均 future_20d | 平均 future_60d |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top 5 | 5 | -0.040595 | -0.045989 |  |  |
| Bottom 5 | 5 | 0.05066 | -0.04038 |  |  |

## watch_score Top 5 未来收益表现
| 分组 | 样本数 | 平均 future_5d | 平均 future_10d | 平均 future_20d | 平均 future_60d |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top 5 | 5 | -0.031623 |  |  |  |

## 按 group 拆分表现
| group | 样本数 | 平均 composite_score | 平均 watch_score | 平均 future_20d | future_20d_top30 占比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 周期资源 | 96 | 35.581283 | 41.0625 |  |  |
| 宽基 | 125 | 56.256941 | 62.672 |  |  |
| 新能源制造 | 122 | 27.737439 | 27.95082 |  |  |
| 消费医药 | 135 | 21.654448 | 19.614815 |  |  |
| 科技成长 | 148 | 48.438961 | 56.202703 |  |  |
| 金融地产 | 86 | 56.805197 | 65.837209 |  |  |
| 防御风格 | 63 | 35.888061 | 35.52381 |  |  |