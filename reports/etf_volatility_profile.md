# ETF Volatility Profile 2026-06-18 16:01:13

本报告只用于退出规则参数研究，不接入交易执行层。

## 摘要
- ETF 数量：183
- 数据有效数量：183
- 短历史数量：5
- 低/未知流动性数量：34

## ETF 类型波动摘要
| etf_type | count | avg_annualized_volatility | median_annualized_volatility | avg_max_drawdown | median_atr_14_pct | p75_atr_14_pct | recommended_stop_search_range | recommended_trailing_search_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bond_cash | 12 | 0.0249 | 0.0095 | -0.0218 | 0.0004 | 0.0013 | 0.5%-2.5%; use bond/cash-specific validation | not primary; prefer duration/credit risk review |
| broad_index | 22 | 0.2413 | 0.2362 | -0.1786 | 0.0254 | 0.0415 | 5%-12% or 5.1%-10.1% ATR-equivalent | profit start 5%-12%, trail 6.3%-12.7% |
| commodity_resource | 20 | 0.3046 | 0.2936 | -0.2331 | 0.0306 | 0.0367 | 4%-10% or 5.5%-10.7% ATR-equivalent | profit start 4%-12%, trail 6.1%-13.8% |
| defensive | 5 | 0.1688 | 0.1520 | -0.1320 | 0.0154 | 0.0180 | observe only until classification is fixed | observe only until classification is fixed |
| high_beta | 3 | 0.5214 | 0.2320 | -0.4007 | 0.0242 | 0.0394 | 4%-10% or 3.6%-8.5% ATR-equivalent | profit start 4%-10%, trail 4.8%-9.7% |
| qdii | 15 | 0.2657 | 0.2734 | -0.2595 | 0.0261 | 0.0345 | observe only; add premium/fx/calendar checks before auto exit | observe only; premium/fx required |
| sector | 15 | 0.1854 | 0.1867 | -0.2447 | 0.0204 | 0.0217 | 4%-10% or 3.7%-7.1% ATR-equivalent | profit start 4%-12%, trail 4.1%-9.2% |
| theme | 18 | 0.3517 | 0.3254 | -0.3177 | 0.0378 | 0.0513 | 4%-10% or 5.7%-13.2% ATR-equivalent | profit start 4%-10%, trail 7.6%-15.1% |
| unknown | 73 | 0.2645 | 0.2424 | -0.2117 | 0.0283 | 0.0387 | observe only until classification is fixed | observe only until classification is fixed |

## 最高波动 ETF 样例
| symbol | name | etf_type | group | annualized_volatility | max_drawdown | atr_14_pct | liquidity_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 515880 | 证券公司ETF | high_beta | 金融地产 | 1.1087 | -0.6891 | 0.0546 | ok |
| 159516 | 159516 | unknown | expanded_formal_data | 1.0449 | -0.5709 | 0.0614 | ok |
| 515050 | 5GETF | theme | 科技成长 | 0.7200 | -0.6718 | 0.0541 | ok |
| 159667 | 159667 | unknown | expanded_formal_data | 0.6834 | -0.6808 | 0.1925 | ok |
| 512760 | 芯片ETF | theme | 科技成长 | 0.5846 | -0.6038 | 0.0554 | ok |
| 516780 | 稀土ETF | commodity_resource | 周期资源 | 0.5720 | -0.5916 | 0.0395 | ok |
| 159363 | 159363 | unknown | expanded_formal_data | 0.4505 | -0.2852 | 0.0487 | ok |
| 159518 | 159518 | unknown | expanded_formal_data | 0.4425 | -0.3127 | 0.0316 | ok |
| 159562 | 159562 | unknown | expanded_formal_data | 0.4368 | -0.4598 | 0.0380 | ok |
| 159321 | 159321 | unknown | expanded_formal_data | 0.4366 | -0.4662 | 0.0373 | watch |
| 159315 | 159315 | unknown | expanded_formal_data | 0.4304 | -0.4602 | 0.0387 | low |
| 588200 | 科创芯片ETF | theme | 科技成长 | 0.4063 | -0.1930 | 0.0568 | ok |
| 159558 | 159558 | unknown | expanded_formal_data | 0.3967 | -0.1970 | 0.0623 | ok |
| 159327 | 159327 | unknown | expanded_formal_data | 0.3933 | -0.1881 | 0.0620 | ok |
| 159608 | 159608 | unknown | expanded_formal_data | 0.3789 | -0.2374 | 0.0426 | ok |
| 512480 | 半导体ETF | theme | 科技成长 | 0.3786 | -0.1990 | 0.0548 | ok |
| 159671 | 159671 | unknown | expanded_formal_data | 0.3781 | -0.2376 | 0.0425 | ok |
| 159995 | 芯片ETF | theme | 科技成长 | 0.3778 | -0.2171 | 0.0558 | ok |
| 512400 | 有色ETF | commodity_resource | 周期资源 | 0.3776 | -0.2987 | 0.0410 | ok |
| 513120 | 港股创新药ETF | qdii | 医药与消费升级 | 0.3744 | -0.3851 | 0.0355 | ok |

## 最大回撤 ETF 样例
| symbol | name | etf_type | group | annualized_volatility | max_drawdown | atr_14_pct | liquidity_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 515880 | 证券公司ETF | high_beta | 金融地产 | 1.1087 | -0.6891 | 0.0546 | ok |
| 159667 | 159667 | unknown | expanded_formal_data | 0.6834 | -0.6808 | 0.1925 | ok |
| 515050 | 5GETF | theme | 科技成长 | 0.7200 | -0.6718 | 0.0541 | ok |
| 512760 | 芯片ETF | theme | 科技成长 | 0.5846 | -0.6038 | 0.0554 | ok |
| 516780 | 稀土ETF | commodity_resource | 周期资源 | 0.5720 | -0.5916 | 0.0395 | ok |
| 159516 | 159516 | unknown | expanded_formal_data | 1.0449 | -0.5709 | 0.0614 | ok |
| 159915 | 创业板ETF | broad_index | 宽基 | 0.3145 | -0.5244 | 0.0358 | ok |
| 515000 | 科技ETF | unknown | 科技成长 | 0.2868 | -0.4687 | 0.0461 | ok |
| 159321 | 159321 | unknown | expanded_formal_data | 0.4366 | -0.4662 | 0.0373 | watch |
| 159315 | 159315 | unknown | expanded_formal_data | 0.4304 | -0.4602 | 0.0387 | low |
| 159562 | 159562 | unknown | expanded_formal_data | 0.4368 | -0.4598 | 0.0380 | ok |
| 513050 | 中概互联网ETF | qdii | QDII观察 | 0.2893 | -0.3983 | 0.0270 | ok |
| 513330 | 恒生互联网ETF | qdii | 跨境与港股 | 0.2955 | -0.3910 | 0.0261 | ok |
| 513060 | 恒生医疗ETF | qdii | QDII观察 | 0.3229 | -0.3870 | 0.0307 | ok |
| 159869 | 游戏ETF | theme | 科技成长 | 0.3245 | -0.3859 | 0.0282 | ok |
| 513120 | 港股创新药ETF | qdii | 医药与消费升级 | 0.3744 | -0.3851 | 0.0355 | ok |
| 159615 | 159615 | unknown | expanded_formal_data | 0.3520 | -0.3819 | 0.0344 | ok |
| 512980 | 传媒ETF | theme | 科技成长 | 0.3188 | -0.3782 | 0.0287 | ok |
| 515230 | 软件ETF | theme | 科技成长 | 0.3262 | -0.3714 | 0.0340 | ok |
| 512690 | 酒ETF | sector | 消费医药 | 0.2089 | -0.3666 | 0.0248 | ok |

## 使用说明
- 本报告给出的是参数搜索范围，不是正式止盈止损规则。
- 固定百分比规则容易忽略 ETF 类型差异，后续回测应与 ATR/波动率规则对比。
- 债券/货币 ETF 不应套用普通权益 ETF 止盈止损。
- QDII 暂不建议自动交易，需要溢价、汇率、海外交易日、申赎状态检查。
