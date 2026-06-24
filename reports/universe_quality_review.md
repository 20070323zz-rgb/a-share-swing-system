# ETF Universe Quality Review 2026-06-18 15:47:04

本报告只读取本地 ETF CSV、watchlist 和分类文件；不接券商 API，不下单，不修改模拟持仓。

## 摘要
- ETF 文件数量：183
- 最新统一数据日：2026-06-17
- 推荐 trade_pool：39
- 推荐 observe_pool：132
- 推荐 exclude_pool：12
- 低流动性/未知流动性数量：34
- 历史不足数量：5
- QDII 数量：15
- unknown 分类数量：73
- 高波动数量：20
- 是否支持 Phase 4A 第一版回测：是

## 类型分布
- unknown: 73
- broad_index: 22
- commodity_resource: 21
- sector: 19
- theme: 18
- qdii: 15
- bond_cash: 12
- high_beta: 3

## Group 分布
- expanded_formal_data: 74
- 新宽基与新风格: 12
- 科技成长: 12
- 消费医药: 11
- 宽基: 10
- 新能源制造: 10
- 周期资源: 8
- QDII观察: 7
- 金融地产: 7
- 债券货币观察: 6
- 医药与消费升级: 6
- 跨境与港股: 6
- 防御风格: 5
- 债券货币: 4
- 周期、资源、商品: 2
- 科技与新质生产力: 2
- 防御、红利、质量: 1

## 需要人工复核的 ETF 样例
| symbol | name | etf_type | group | pool_current | recommended_pool | avg_amount_20d | trading_days | review_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 159332 | 159332 | unknown | expanded_formal_data | research_only | exclude_pool | 2671692.01 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159717 | 159717 | unknown | expanded_formal_data | research_only | exclude_pool | 3283446.61 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159787 | 159787 | unknown | expanded_formal_data | research_only | exclude_pool | 2294982.05 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159791 | 159791 | unknown | expanded_formal_data | research_only | exclude_pool | 3366009.69 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159797 | 159797 | unknown | expanded_formal_data | research_only | exclude_pool | 3270538.52 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159889 | 159889 | unknown | expanded_formal_data | research_only | exclude_pool | 3475165.61 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159954 | 159954 | unknown | expanded_formal_data | research_only | exclude_pool | 3259726.48 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 510060 | 510060 | unknown | expanded_formal_data | research_only | exclude_pool | 479583.65 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 510270 | 510270 | unknown | expanded_formal_data | research_only | exclude_pool | 3306404.30 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 516360 | 516360 | unknown | expanded_formal_data | research_only | exclude_pool | 4941707.30 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 516720 | 516720 | unknown | expanded_formal_data | research_only | exclude_pool | 715817.90 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159940 | 金融ETF | sector | 金融地产 | trade_pool | exclude_pool | 3365933.67 | 315 | liquidity_ultra_low |
| 159920 | 恒生ETF | qdii | QDII观察 | observe_pool | observe_pool | 328661100.74 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 159941 | 纳指ETF | qdii | QDII观察 | observe_pool | observe_pool | 2494952972.51 | 315 | qdii_needs_premium_fx_calendar_check |
| 513050 | 中概互联网ETF | qdii | QDII观察 | observe_pool | observe_pool | 2079747765.75 | 315 | qdii_needs_premium_fx_calendar_check |
| 513060 | 恒生医疗ETF | qdii | QDII观察 | observe_pool | observe_pool | 536924797.05 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 513100 | 纳指ETF | qdii | QDII观察 | observe_pool | observe_pool | 1189220874.40 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 513180 | 恒生科技ETF | qdii | QDII观察 | observe_pool | observe_pool | 3488282706.10 | 315 | qdii_needs_premium_fx_calendar_check |
| 513500 | 标普500ETF | qdii | QDII观察 | observe_pool | observe_pool | 476904046.15 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 159301 | 159301 | unknown | expanded_formal_data | research_only | observe_pool | 30877053.08 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159302 | 159302 | unknown | expanded_formal_data | research_only | observe_pool | 8278977.69 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159315 | 159315 | unknown | expanded_formal_data | research_only | observe_pool | 18676645.27 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159321 | 159321 | unknown | expanded_formal_data | research_only | observe_pool | 34953405.52 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159327 | 159327 | unknown | expanded_formal_data | research_only | observe_pool | 211605708.72 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159333 | 159333 | unknown | expanded_formal_data | research_only | observe_pool | 8958556.55 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159336 | 159336 | unknown | expanded_formal_data | research_only | observe_pool | 5598089.37 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159363 | 159363 | unknown | expanded_formal_data | research_only | observe_pool | 1485386504.81 | 315 | classification_unknown; high_volatility |
| 159395 | 159395 | unknown | expanded_formal_data | research_only | observe_pool | 989274513.97 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159396 | 159396 | unknown | expanded_formal_data | research_only | observe_pool | 371294201.81 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159398 | 159398 | unknown | expanded_formal_data | research_only | observe_pool | 1073551669.69 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159516 | 159516 | unknown | expanded_formal_data | research_only | observe_pool | 3322278424.63 | 315 | classification_unknown; extreme_volatility |
| 159518 | 159518 | unknown | expanded_formal_data | research_only | observe_pool | 1083533145.51 | 315 | classification_unknown; high_volatility |
| 159531 | 159531 | unknown | expanded_formal_data | research_only | observe_pool | 163132960.24 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159532 | 159532 | unknown | expanded_formal_data | research_only | observe_pool | 38302805.51 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159536 | 159536 | unknown | expanded_formal_data | research_only | observe_pool | 17192487.29 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159538 | 159538 | unknown | expanded_formal_data | research_only | observe_pool | 8997938.47 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159539 | 159539 | unknown | expanded_formal_data | research_only | observe_pool | 16675704.94 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159540 | 159540 | unknown | expanded_formal_data | research_only | observe_pool | 37173768.65 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159545 | 159545 | unknown | expanded_formal_data | research_only | observe_pool | 105293130.63 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159547 | 159547 | unknown | expanded_formal_data | research_only | observe_pool | 148927098.22 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159549 | 159549 | unknown | expanded_formal_data | research_only | observe_pool | 10276420.27 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159551 | 159551 | unknown | expanded_formal_data | research_only | observe_pool | 36228825.04 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159558 | 159558 | unknown | expanded_formal_data | research_only | observe_pool | 958204593.73 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159559 | 159559 | unknown | expanded_formal_data | research_only | observe_pool | 195744096.44 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159562 | 159562 | unknown | expanded_formal_data | research_only | observe_pool | 161363794.52 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159595 | 159595 | unknown | expanded_formal_data | research_only | observe_pool | 152759351.47 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159608 | 159608 | unknown | expanded_formal_data | research_only | observe_pool | 178248249.08 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159611 | 159611 | unknown | expanded_formal_data | research_only | observe_pool | 913604367.80 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159613 | 159613 | unknown | expanded_formal_data | research_only | observe_pool | 8025290.05 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159615 | 159615 | unknown | expanded_formal_data | research_only | observe_pool | 99485142.61 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159625 | 159625 | unknown | expanded_formal_data | research_only | observe_pool | 80834845.35 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159638 | 159638 | unknown | expanded_formal_data | research_only | observe_pool | 69002749.02 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159658 | 159658 | unknown | expanded_formal_data | research_only | observe_pool | 12210138.68 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159663 | 159663 | unknown | expanded_formal_data | research_only | observe_pool | 121085632.79 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159667 | 159667 | unknown | expanded_formal_data | research_only | observe_pool | 339208095.75 | 315 | classification_unknown; extreme_volatility; duplicate_exposure_lower_liquidity |
| 159669 | 159669 | unknown | expanded_formal_data | research_only | observe_pool | 11106246.20 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159671 | 159671 | unknown | expanded_formal_data | research_only | observe_pool | 89570481.67 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159697 | 159697 | unknown | expanded_formal_data | research_only | observe_pool | 88725978.34 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159699 | 159699 | unknown | expanded_formal_data | research_only | observe_pool | 50312127.88 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159703 | 159703 | unknown | expanded_formal_data | research_only | observe_pool | 7187381.96 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |

## 推荐 trade_pool 样例
| symbol | name | etf_type | group | avg_amount_20d | trading_days | duplicate_exposure_group | duplicate_liquidity_rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 511360 | 短融ETF | bond_cash | 债券货币观察 | 16978454988.35 | 315 | bond_cash:债券货币观察 | 1 |
| 511880 | 银华日利ETF | bond_cash | 债券货币观察 | 16418985023.80 | 315 | bond_cash:债券货币观察 | 2 |
| 511380 | 可转债ETF | bond_cash | 债券货币 | 10672470905.60 | 315 | bond_cash:债券货币 | 1 |
| 511990 | 华宝添益ETF | bond_cash | 债券货币观察 | 10047864524.65 | 315 | bond_cash:债券货币观察 | 3 |
| 588000 | 科创50ETF | broad_index | 宽基 | 6465872778.65 | 315 | broad_index:宽基 | 1 |
| 159915 | 创业板ETF | broad_index | 宽基 | 5806638195.97 | 1077 | broad_index:宽基 | 2 |
| 563360 | 华泰柏瑞中证A500ETF | broad_index | 新宽基与新风格 | 4413037979.30 | 315 | broad_index:新宽基与新风格 | 1 |
| 159338 | 国泰中证A500ETF | broad_index | 新宽基与新风格 | 4318763269.34 | 315 | broad_index:新宽基与新风格 | 2 |
| 511090 | 30年国债ETF | bond_cash | 债券货币 | 4276356393.20 | 315 | bond_cash:债券货币 | 2 |
| 510300 | 沪深300ETF | broad_index | 宽基 | 4130779491.85 | 1077 | broad_index:宽基 | 3 |
| 518880 | 黄金ETF | commodity_resource | 防御风格 | 3251841575.25 | 315 | commodity_resource:防御风格 | 1 |
| 159352 | 南方中证A500ETF | broad_index | 新宽基与新风格 | 3103581841.03 | 315 | broad_index:新宽基与新风格 | 3 |
| 511030 | 公司债ETF | bond_cash | 债券货币 | 2738338169.25 | 315 | bond_cash:债券货币 | 3 |
| 512880 | 证券ETF | high_beta | 金融地产 | 2375797614.30 | 315 | high_beta:金融地产 | 2 |
| 511520 | 政金债ETF | bond_cash | 债券货币 | 1818536352.55 | 315 | bond_cash:债券货币 | 4 |
| 512400 | 有色ETF | commodity_resource | 周期资源 | 1295707610.95 | 315 | commodity_resource:周期资源 | 1 |
| 562500 | 机器人ETF华夏 | theme | 科技与新质生产力 | 1255230392.35 | 315 | theme:科技与新质生产力 | 1 |
| 515220 | 煤炭ETF | commodity_resource | 周期资源 | 1243805109.65 | 315 | commodity_resource:周期资源 | 2 |
| 512800 | 银行ETF | sector | 金融地产 | 858914991.65 | 315 | sector:金融地产 | 1 |
| 159870 | 化工ETF | commodity_resource | 周期、资源、商品 | 792429665.00 | 315 | commodity_resource:周期、资源、商品 | 1 |
| 512890 | 红利低波ETF | sector | 防御风格 | 789593311.85 | 315 | sector:防御风格 | 1 |
| 512690 | 酒ETF | sector | 消费医药 | 784664860.80 | 315 | sector:消费医药 | 1 |
| 159755 | 电池ETF | commodity_resource | 新能源制造 | 751754992.40 | 315 | commodity_resource:新能源制造 | 1 |
| 159992 | 银华创新药ETF | theme | 医药与消费升级 | 588179664.09 | 315 | theme:医药与消费升级 | 1 |
| 512170 | 医疗ETF | sector | 消费医药 | 570074951.10 | 315 | sector:消费医药 | 2 |
| 512070 | 非银ETF | high_beta | 金融地产 | 549551811.60 | 315 | high_beta:金融地产 | 3 |
| 512010 | 医药ETF | sector | 消费医药 | 531346428.20 | 315 | sector:消费医药 | 3 |
| 515790 | 光伏ETF | commodity_resource | 新能源制造 | 436999293.30 | 315 | commodity_resource:新能源制造 | 2 |
| 515080 | 中证红利ETF | sector | 防御风格 | 398747302.30 | 315 | sector:防御风格 | 3 |
| 512660 | 军工ETF | commodity_resource | 新能源制造 | 362883596.35 | 315 | commodity_resource:新能源制造 | 3 |
| 515120 | 广发创新药ETF | theme | 医药与消费升级 | 335626538.85 | 315 | theme:医药与消费升级 | 2 |
| 159770 | 机器人ETF | theme | 科技与新质生产力 | 332310158.52 | 315 | theme:科技与新质生产力 | 2 |
| 516020 | 化工ETF | commodity_resource | 周期、资源、商品 | 229850900.60 | 315 | commodity_resource:周期、资源、商品 | 2 |
| 159930 | 能源ETF | commodity_resource | 周期资源 | 169237859.58 | 315 | commodity_resource:周期资源 | 3 |
| 512200 | 房地产ETF | sector | 金融地产 | 156541505.00 | 315 | sector:金融地产 | 2 |
| 510230 | 金融ETF | sector | 金融地产 | 116245458.95 | 315 | sector:金融地产 | 3 |
| 516080 | 易方达创新药ETF | theme | 医药与消费升级 | 67375350.75 | 315 | theme:医药与消费升级 | 3 |
| 159905 | 深红利ETF | sector | 防御风格 | 55562256.70 | 315 | sector:防御风格 | 4 |
| 511690 | 511690 | bond_cash | expanded_formal_data | 27235630.80 | 315 | bond_cash:expanded_formal_data | 1 |

## 判断规则
- 数据少于 120 个交易日：不进入第一版自动交易回测池。
- 近 20 日平均成交额低于 20,000,000 元：不进入 trade_pool。
- QDII：先进入 observe_pool，等待溢价、汇率、海外交易日检查。
- unknown 分类：先进入 observe_pool，等待人工分类。
- 高度重复暴露：优先保留同暴露中流动性靠前的 ETF。
- 极端波动或数据非最新：进入 observe/exclude，避免污染第一版回测。
