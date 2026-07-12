# ETF Risk Profile 风险画像报告

本报告只建立 ETF 自身风险/风格画像，不修改 BUY ranking、不修改模拟仓、不接执行层。

## 摘要
- ETF 总数：183
- 有效画像数量：183
- 数据不足数量：0
- Beta/capture 基准：510300
- 基准警告：无
- risk_profile 分布：{'CORE': 37, 'HIGH_BETA': 37, 'OFFENSIVE': 37, 'BALANCED': 36, 'DEFENSIVE': 36}
- structural_risk_profile 分布：{'OFFENSIVE': 68, 'CORE': 38, 'BALANCED': 35, 'HIGH_BETA': 27, 'DEFENSIVE': 15}
- style_profile 分布：{'COMMODITY_CYCLICAL': 35, 'QDII_OBSERVATION': 24, 'HIGH_BETA_THEME': 23, 'SECTOR_DEFENSIVE': 21, 'DIVIDEND': 20, 'CORE_MID_CAP': 16, 'BOND': 15, 'CORE_LARGE_CAP': 11, 'GROWTH_THEME': 10, 'SECTOR_CYCLICAL': 7, 'GROWTH_BROAD': 1}
- UNKNOWN style 数量：0

## realized risk / compatibility alias
- risk_score / risk_profile 为兼容字段，本轮重新定义为 realized_risk_score / realized_risk_profile。
- realized risk 表示 ETF 最近历史行情中实际表现出来的风险水平。
- 所有数值指标使用全 ETF 截面分位数，不用“科技=80、证券=90”这种人工打分。
- 权重：{'volatility_60d': 0.25, 'beta_60d': 0.2, 'max_drawdown_120d_abs': 0.2, 'downside_volatility_60d': 0.15, 'down_capture_60d': 0.1, 'concentration_style_penalty': 0.1}
- 缺失指标不填 0，而是按可用指标重新归一权重，并记录 missing_feature_count。

## structural risk 方法
- structural risk 表示 ETF 基于资产类别、集中度、风格属性、长期风险特征形成的较稳定风险性格。
- Structural Risk != Realized Risk；Style Profile != Risk Profile。
- 权重：{'asset_class_and_concentration': 0.3, 'style_attribute': 0.25, 'long_cycle_risk_features': 0.35, 'diversification_concentration_adjustment': 0.1}
- 初始阈值与约束：0-25 DEFENSIVE, 25-45 CORE, 45-60 BALANCED, 60-80 OFFENSIVE, 80-100 HIGH_BETA, with asset-type constraints

## realized_risk_score Top 20
| symbol | name | group | type | realized_risk_score | realized_risk_profile | structural_risk_profile | style_profile | data_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 515880 | 证券公司ETF | 金融地产 | high_beta | 96.7760 | HIGH_BETA | HIGH_BETA | SECTOR_CYCLICAL | ok |
| 515070 | AIETF | 科技成长 | theme | 96.4754 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 515050 | 5GETF | 科技成长 | theme | 94.9454 | HIGH_BETA | HIGH_BETA | GROWTH_THEME | ok |
| 512480 | 半导体ETF | 科技成长 | theme | 94.3169 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159667 | 工业母机ETF国泰 | 科技与新质生产力 | unknown | 93.8798 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 512760 | 芯片ETF | 科技成长 | theme | 93.8251 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159995 | 芯片ETF | 科技成长 | theme | 87.9781 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159516 | 半导体设备ETF国泰 | 科技与新质生产力 | unknown | 87.8962 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159876 | 有色金属ETF | 周期资源 | commodity_resource | 87.1038 | HIGH_BETA | HIGH_BETA | COMMODITY_CYCLICAL | ok |
| 512400 | 有色ETF | 周期资源 | commodity_resource | 85.2459 | HIGH_BETA | HIGH_BETA | COMMODITY_CYCLICAL | ok |
| 588200 | 科创芯片ETF | 科技成长 | theme | 84.1257 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 516780 | 稀土ETF | 周期资源 | commodity_resource | 83.3333 | HIGH_BETA | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 588120 | 国泰科创100ETF | 新宽基与新风格 | broad_index | 82.8415 | HIGH_BETA | OFFENSIVE | CORE_MID_CAP | ok |
| 159562 | 黄金股ETF华夏 | 周期、资源、商品 | unknown | 81.8306 | HIGH_BETA | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 159315 | 黄金股ETF工银 | 周期、资源、商品 | unknown | 81.5301 | HIGH_BETA | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 159321 | 黄金股ETF华安 | 周期、资源、商品 | unknown | 80.6284 | HIGH_BETA | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 159539 | 信创ETF广发 | 科技与新质生产力 | unknown | 80.3552 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159558 | 半导体设备ETF易方达 | 科技与新质生产力 | unknown | 80.1366 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159538 | 信创ETF富国 | 科技与新质生产力 | unknown | 79.9180 | HIGH_BETA | HIGH_BETA | HIGH_BETA_THEME | ok |
| 159363 | 创业板人工智能ETF华宝 | 科技与新质生产力 | unknown | 79.3716 | HIGH_BETA | OFFENSIVE | GROWTH_BROAD | ok |

## realized_risk_score Bottom 20
| symbol | name | group | type | realized_risk_score | realized_risk_profile | structural_risk_profile | style_profile | data_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 159001 | 货币ETF | 债券货币观察 | bond_cash | 4.5902 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511360 | 短融ETF | 债券货币观察 | bond_cash | 4.5902 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511690 | 交易货币ETF大成 | 债券货币 | bond_cash | 4.7541 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511880 | 银华日利ETF | 债券货币观察 | bond_cash | 4.7541 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511990 | 华宝添益ETF | 债券货币观察 | bond_cash | 4.9180 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511600 | 货币ETF | 债券货币 | bond_cash | 5.9016 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 159398 | 信用债ETF天弘 | 债券货币 | unknown | 6.4208 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511010 | 国债ETF | 债券货币观察 | bond_cash | 6.4754 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511030 | 公司债ETF | 债券货币 | bond_cash | 6.8033 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 159395 | 信用债ETF大成 | 债券货币 | unknown | 7.3770 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511260 | 十年国债ETF | 债券货币观察 | bond_cash | 7.4044 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 159396 | 信用债ETF博时 | 债券货币 | unknown | 7.5410 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511520 | 政金债ETF | 债券货币 | bond_cash | 8.1148 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 511090 | 30年国债ETF | 债券货币 | bond_cash | 9.6448 | DEFENSIVE | DEFENSIVE | BOND | ok |
| 512890 | 红利低波ETF | 防御风格 | sector | 15.7104 | DEFENSIVE | CORE | DIVIDEND | ok |
| 512800 | 银行ETF | 金融地产 | sector | 16.5574 | DEFENSIVE | CORE | SECTOR_DEFENSIVE | ok |
| 159302 | 港股高股息ETF银华 | 防御、红利、质量 | unknown | 16.9672 | DEFENSIVE | CORE | QDII_OBSERVATION | ok |
| 159549 | 红利低波ETF天弘 | 防御、红利、质量 | unknown | 17.0765 | DEFENSIVE | CORE | DIVIDEND | ok |
| 159547 | 红利低波ETF华夏 | 防御、红利、质量 | unknown | 17.3224 | DEFENSIVE | CORE | DIVIDEND | ok |
| 511380 | 可转债ETF | 债券货币 | bond_cash | 17.6776 | DEFENSIVE | DEFENSIVE | BOND | ok |

## 当前正式模拟仓风险画像
- 持仓加权 realized_risk_score：51.3118
- 持仓加权 structural_risk_score：66.9416
- realized OFFENSIVE/HIGH_BETA 持仓权重：52.11%
- structural OFFENSIVE/HIGH_BETA 持仓权重：71.73%
- structural CORE/DEFENSIVE 持仓权重：28.27%
- 是否缺少 CORE/DEFENSIVE：False
| symbol | name | current_weight | realized_risk_score | realized_risk_profile | structural_risk_score | structural_risk_profile | style_profile | volatility_60d | beta_60d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 0.2827 | 16.5574 | DEFENSIVE | 44.1250 | CORE | SECTOR_DEFENSIVE | 0.1539 | -0.1391 |
| 515000 | 科技ETF | 0.5211 | 68.5519 | OFFENSIVE | 76.0750 | OFFENSIVE | GROWTH_THEME | 0.4359 | 1.8881 |
| 512880 | 证券ETF | 0.1961 | 55.6011 | BALANCED | 75.5625 | HIGH_BETA | SECTOR_CYCLICAL | 0.3035 | 0.8849 |

## BUY Ranking Top 10 风险结构
- Top 10 平均 realized_risk_score：55.0820
- Top 10 平均 structural_risk_score：64.8338
- realized OFFENSIVE/HIGH_BETA 占比：40.00%
- structural OFFENSIVE/HIGH_BETA 占比：70.00%
- CORE/DEFENSIVE 占比：40.00%
- 是否明显偏进攻：False
| rank | symbol | name | group | rank_score | realized_risk_score | realized_risk_profile | structural_risk_score | structural_risk_profile | style_profile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 512010 | 医药ETF | 消费医药 | 94.3042 | 39.7541 | CORE | 49.8125 | BALANCED | SECTOR_DEFENSIVE |
| 2 | 512880 | 证券ETF | 金融地产 | 93.9395 | 55.6011 | BALANCED | 75.5625 | HIGH_BETA | SECTOR_CYCLICAL |
| 3 | 159929 | 医药ETF | 消费医药 | 89.3657 | 39.3443 | CORE | 51.5625 | BALANCED | SECTOR_DEFENSIVE |
| 4 | 588080 | 科创创业50ETF | 宽基 | 76.5887 | 76.6667 | HIGH_BETA | 67.6250 | OFFENSIVE | CORE_MID_CAP |
| 5 | 588000 | 科创50ETF | 宽基 | 76.5586 | 77.2951 | HIGH_BETA | 67.6250 | OFFENSIVE | CORE_MID_CAP |
| 6 | 512170 | 医疗ETF | 消费医药 | 76.2914 | 39.5355 | CORE | 52.7875 | BALANCED | SECTOR_DEFENSIVE |
| 7 | 159865 | 养殖ETF | 周期资源 | 74.8890 | 43.1694 | CORE | 64.3875 | OFFENSIVE | COMMODITY_CYCLICAL |
| 8 | 515000 | 科技ETF | 科技成长 | 71.3463 | 68.5519 | OFFENSIVE | 76.0750 | OFFENSIVE | GROWTH_THEME |
| 9 | 159825 | 农业ETF | 周期资源 | 68.3897 | 44.3169 | BALANCED | 66.1375 | OFFENSIVE | COMMODITY_CYCLICAL |
| 10 | 159869 | 游戏ETF | 科技成长 | 67.6638 | 66.5847 | OFFENSIVE | 76.7625 | OFFENSIVE | GROWTH_THEME |

## 重点 ETF
| symbol | name | group | type | style_profile | realized_risk_score | realized_risk_profile | structural_risk_score | structural_risk_profile | volatility_60d | beta_60d | data_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | SECTOR_DEFENSIVE | 16.5574 | DEFENSIVE | 44.1250 | CORE | 0.1539 | -0.1391 | ok |
| 515000 | 科技ETF | 科技成长 | unknown | GROWTH_THEME | 68.5519 | OFFENSIVE | 76.0750 | OFFENSIVE | 0.4359 | 1.8881 | ok |
| 512880 | 证券ETF | 金融地产 | high_beta | SECTOR_CYCLICAL | 55.6011 | BALANCED | 75.5625 | HIGH_BETA | 0.3035 | 0.8849 | ok |
| 512010 | 医药ETF | 消费医药 | sector | SECTOR_DEFENSIVE | 39.7541 | CORE | 49.8125 | BALANCED | 0.2431 | 0.2846 | ok |
| 588000 | 科创50ETF | 宽基 | broad_index | CORE_MID_CAP | 77.2951 | HIGH_BETA | 67.6250 | OFFENSIVE | 0.4858 | 1.8235 | ok |
| 159915 | 创业板ETF | 宽基 | broad_index | CORE_MID_CAP | 63.8251 | OFFENSIVE | 63.2500 | OFFENSIVE | 0.3783 | 1.7183 | ok |
| 510300 | 沪深300ETF | 宽基 | broad_index | CORE_LARGE_CAP | 38.0328 | CORE | 42.7750 | CORE | 0.2019 | 1.0000 | ok |
| 510500 | 中证500ETF | 宽基 | broad_index | CORE_MID_CAP | 52.1038 | BALANCED | 62.0250 | OFFENSIVE | 0.2695 | 1.2000 | ok |
| 510180 | 上证180ETF | 宽基 | broad_index | CORE_LARGE_CAP | 32.2131 | CORE | 42.7750 | CORE | 0.1806 | 0.8392 | ok |

## 研究边界
- research_only=true。
- execution_allowed=false。
- 不修改 paper_trade_engine / paper_trades / paper_positions / BUY ranking / market_regime。