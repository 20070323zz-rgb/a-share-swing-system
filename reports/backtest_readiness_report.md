# Backtest Readiness Report 2026-06-18 15:47:04

本报告用于决定是否进入 Phase 4A 回测引擎开发；不修改交易规则，不修改模拟持仓。

## 结论
- 当前 183 只 ETF 是否够第一版回测：够，但必须过滤
- 推荐 trade_pool 数量：39
- 推荐 observe_pool 数量：132
- 推荐 exclude_pool 数量：12
- 最新可用数据日：2026-06-17
- 是否可以进入 Phase 4A：可以，前提是使用推荐 trade_pool 并保留风险过滤

## 回测前必须处理的风险
1. 幸存者偏差：当前池来自现有 ETF 文件，第一版可做策略验证，但报告必须标注 survivorship bias。
2. QDII：15 只应先剔出自动交易池，等待溢价/汇率/海外交易日检查。
3. unknown 分类：73 只需人工分类，否则只观察。
4. 低流动性：34 只低流动性/未知流动性 ETF 不适合第一版交易池。
5. 历史不足：5 只历史不足 ETF 不应用于估计稳定参数。
6. 重复暴露：同主题多个 ETF 要优先保留流动性更好的标的。

## 第一版回测建议
- 使用推荐 trade_pool，不直接使用全 183 只。
- 交易口径：日线收盘后生成信号，下一交易日 close proxy 或 next open proxy 二选一；第一版建议先用 next close/close proxy 并明确偏差。
- 加入佣金、最低佣金、滑点、100 份整数倍。
- 最大持仓 3 只，单只不超过 20%。
- QDII、unknown、短历史、低流动性标的不进入自动买入池。
- 比较策略：original ranking、adjusted preview、沪深300 ETF buy-and-hold、现金基准。
- market_state 先作为报告分组维度，不直接控制仓位。

## 推荐 trade_pool 列表
| symbol | name | etf_type | group | avg_amount_20d | trading_days | review_reason |
| --- | --- | --- | --- | --- | --- | --- |
| 511690 | 511690 | bond_cash | expanded_formal_data | 27235630.80 | 315 | history/liquidity/classification pass |
| 511030 | 公司债ETF | bond_cash | 债券货币 | 2738338169.25 | 315 | history/liquidity/classification pass |
| 511090 | 30年国债ETF | bond_cash | 债券货币 | 4276356393.20 | 315 | history/liquidity/classification pass |
| 511380 | 可转债ETF | bond_cash | 债券货币 | 10672470905.60 | 315 | history/liquidity/classification pass |
| 511520 | 政金债ETF | bond_cash | 债券货币 | 1818536352.55 | 315 | history/liquidity/classification pass |
| 511360 | 短融ETF | bond_cash | 债券货币观察 | 16978454988.35 | 315 | history/liquidity/classification pass |
| 511880 | 银华日利ETF | bond_cash | 债券货币观察 | 16418985023.80 | 315 | history/liquidity/classification pass |
| 511990 | 华宝添益ETF | bond_cash | 债券货币观察 | 10047864524.65 | 315 | history/liquidity/classification pass |
| 159992 | 银华创新药ETF | theme | 医药与消费升级 | 588179664.09 | 315 | history/liquidity/classification pass |
| 515120 | 广发创新药ETF | theme | 医药与消费升级 | 335626538.85 | 315 | history/liquidity/classification pass |
| 516080 | 易方达创新药ETF | theme | 医药与消费升级 | 67375350.75 | 315 | history/liquidity/classification pass |
| 159870 | 化工ETF | commodity_resource | 周期、资源、商品 | 792429665.00 | 315 | history/liquidity/classification pass |
| 516020 | 化工ETF | commodity_resource | 周期、资源、商品 | 229850900.60 | 315 | history/liquidity/classification pass |
| 159930 | 能源ETF | commodity_resource | 周期资源 | 169237859.58 | 315 | history/liquidity/classification pass |
| 512400 | 有色ETF | commodity_resource | 周期资源 | 1295707610.95 | 315 | history/liquidity/classification pass |
| 515220 | 煤炭ETF | commodity_resource | 周期资源 | 1243805109.65 | 315 | history/liquidity/classification pass |
| 159915 | 创业板ETF | broad_index | 宽基 | 5806638195.97 | 1077 | history/liquidity/classification pass |
| 510300 | 沪深300ETF | broad_index | 宽基 | 4130779491.85 | 1077 | history/liquidity/classification pass |
| 588000 | 科创50ETF | broad_index | 宽基 | 6465872778.65 | 315 | history/liquidity/classification pass |
| 159338 | 国泰中证A500ETF | broad_index | 新宽基与新风格 | 4318763269.34 | 315 | history/liquidity/classification pass |
| 159352 | 南方中证A500ETF | broad_index | 新宽基与新风格 | 3103581841.03 | 315 | history/liquidity/classification pass |
| 563360 | 华泰柏瑞中证A500ETF | broad_index | 新宽基与新风格 | 4413037979.30 | 315 | history/liquidity/classification pass |
| 159755 | 电池ETF | commodity_resource | 新能源制造 | 751754992.40 | 315 | history/liquidity/classification pass |
| 512660 | 军工ETF | commodity_resource | 新能源制造 | 362883596.35 | 315 | history/liquidity/classification pass |
| 515790 | 光伏ETF | commodity_resource | 新能源制造 | 436999293.30 | 315 | history/liquidity/classification pass |
| 512010 | 医药ETF | sector | 消费医药 | 531346428.20 | 315 | history/liquidity/classification pass |
| 512170 | 医疗ETF | sector | 消费医药 | 570074951.10 | 315 | history/liquidity/classification pass |
| 512690 | 酒ETF | sector | 消费医药 | 784664860.80 | 315 | history/liquidity/classification pass |
| 159770 | 机器人ETF | theme | 科技与新质生产力 | 332310158.52 | 315 | history/liquidity/classification pass |
| 562500 | 机器人ETF华夏 | theme | 科技与新质生产力 | 1255230392.35 | 315 | history/liquidity/classification pass |
| 510230 | 金融ETF | sector | 金融地产 | 116245458.95 | 315 | history/liquidity/classification pass |
| 512070 | 非银ETF | high_beta | 金融地产 | 549551811.60 | 315 | history/liquidity/classification pass |
| 512200 | 房地产ETF | sector | 金融地产 | 156541505.00 | 315 | history/liquidity/classification pass |
| 512800 | 银行ETF | sector | 金融地产 | 858914991.65 | 315 | history/liquidity/classification pass |
| 512880 | 证券ETF | high_beta | 金融地产 | 2375797614.30 | 315 | history/liquidity/classification pass |
| 159905 | 深红利ETF | sector | 防御风格 | 55562256.70 | 315 | history/liquidity/classification pass |
| 512890 | 红利低波ETF | sector | 防御风格 | 789593311.85 | 315 | history/liquidity/classification pass |
| 515080 | 中证红利ETF | sector | 防御风格 | 398747302.30 | 315 | history/liquidity/classification pass |
| 518880 | 黄金ETF | commodity_resource | 防御风格 | 3251841575.25 | 315 | history/liquidity/classification pass |

## 推荐 observe_pool 样例
| symbol | name | etf_type | group | avg_amount_20d | trading_days | review_reason |
| --- | --- | --- | --- | --- | --- | --- |
| 159920 | 恒生ETF | qdii | QDII观察 | 328661100.74 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 159941 | 纳指ETF | qdii | QDII观察 | 2494952972.51 | 315 | qdii_needs_premium_fx_calendar_check |
| 513050 | 中概互联网ETF | qdii | QDII观察 | 2079747765.75 | 315 | qdii_needs_premium_fx_calendar_check |
| 513060 | 恒生医疗ETF | qdii | QDII观察 | 536924797.05 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 513100 | 纳指ETF | qdii | QDII观察 | 1189220874.40 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 513180 | 恒生科技ETF | qdii | QDII观察 | 3488282706.10 | 315 | qdii_needs_premium_fx_calendar_check |
| 513500 | 标普500ETF | qdii | QDII观察 | 476904046.15 | 315 | qdii_needs_premium_fx_calendar_check; duplicate_exposure_lower_liquidity |
| 159301 | 159301 | unknown | expanded_formal_data | 30877053.08 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159302 | 159302 | unknown | expanded_formal_data | 8278977.69 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159315 | 159315 | unknown | expanded_formal_data | 18676645.27 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159321 | 159321 | unknown | expanded_formal_data | 34953405.52 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159327 | 159327 | unknown | expanded_formal_data | 211605708.72 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159333 | 159333 | unknown | expanded_formal_data | 8958556.55 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159336 | 159336 | unknown | expanded_formal_data | 5598089.37 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159363 | 159363 | unknown | expanded_formal_data | 1485386504.81 | 315 | classification_unknown; high_volatility |
| 159395 | 159395 | unknown | expanded_formal_data | 989274513.97 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159396 | 159396 | unknown | expanded_formal_data | 371294201.81 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159398 | 159398 | unknown | expanded_formal_data | 1073551669.69 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159516 | 159516 | unknown | expanded_formal_data | 3322278424.63 | 315 | classification_unknown; extreme_volatility |
| 159518 | 159518 | unknown | expanded_formal_data | 1083533145.51 | 315 | classification_unknown; high_volatility |
| 159531 | 159531 | unknown | expanded_formal_data | 163132960.24 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159532 | 159532 | unknown | expanded_formal_data | 38302805.51 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159536 | 159536 | unknown | expanded_formal_data | 17192487.29 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159538 | 159538 | unknown | expanded_formal_data | 8997938.47 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159539 | 159539 | unknown | expanded_formal_data | 16675704.94 | 315 | liquidity_low; classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159540 | 159540 | unknown | expanded_formal_data | 37173768.65 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159545 | 159545 | unknown | expanded_formal_data | 105293130.63 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159547 | 159547 | unknown | expanded_formal_data | 148927098.22 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159549 | 159549 | unknown | expanded_formal_data | 10276420.27 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159551 | 159551 | unknown | expanded_formal_data | 36228825.04 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159558 | 159558 | unknown | expanded_formal_data | 958204593.73 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159559 | 159559 | unknown | expanded_formal_data | 195744096.44 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159562 | 159562 | unknown | expanded_formal_data | 161363794.52 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 159595 | 159595 | unknown | expanded_formal_data | 152759351.47 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159608 | 159608 | unknown | expanded_formal_data | 178248249.08 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159611 | 159611 | unknown | expanded_formal_data | 913604367.80 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159613 | 159613 | unknown | expanded_formal_data | 8025290.05 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159615 | 159615 | unknown | expanded_formal_data | 99485142.61 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159625 | 159625 | unknown | expanded_formal_data | 80834845.35 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159638 | 159638 | unknown | expanded_formal_data | 69002749.02 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159658 | 159658 | unknown | expanded_formal_data | 12210138.68 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159663 | 159663 | unknown | expanded_formal_data | 121085632.79 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159667 | 159667 | unknown | expanded_formal_data | 339208095.75 | 315 | classification_unknown; extreme_volatility; duplicate_exposure_lower_liquidity |
| 159669 | 159669 | unknown | expanded_formal_data | 11106246.20 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159671 | 159671 | unknown | expanded_formal_data | 89570481.67 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159697 | 159697 | unknown | expanded_formal_data | 88725978.34 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159699 | 159699 | unknown | expanded_formal_data | 50312127.88 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159703 | 159703 | unknown | expanded_formal_data | 7187381.96 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159726 | 159726 | unknown | expanded_formal_data | 13709851.41 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159732 | 159732 | unknown | expanded_formal_data | 595558287.12 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159735 | 159735 | unknown | expanded_formal_data | 51868701.57 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159745 | 159745 | unknown | expanded_formal_data | 59550622.79 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159758 | 159758 | unknown | expanded_formal_data | 67630104.31 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159763 | 159763 | unknown | expanded_formal_data | 7649500.42 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159795 | 159795 | unknown | expanded_formal_data | 5133796.76 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159840 | 159840 | unknown | expanded_formal_data | 131973061.45 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159883 | 159883 | unknown | expanded_formal_data | 88789029.94 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159888 | 159888 | unknown | expanded_formal_data | 31060705.95 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 159898 | 159898 | unknown | expanded_formal_data | 19763282.29 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159997 | 159997 | unknown | expanded_formal_data | 98606273.19 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 511600 | 511600 | bond_cash | expanded_formal_data | 6830220.40 | 315 | liquidity_low |
| 515210 | 515210 | unknown | expanded_formal_data | 97524943.75 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 515260 | 515260 | unknown | expanded_formal_data | 90540613.80 | 315 | classification_unknown; high_volatility; duplicate_exposure_lower_liquidity |
| 515630 | 515630 | unknown | expanded_formal_data | 53377650.00 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 516750 | 516750 | unknown | expanded_formal_data | 12032989.75 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 561360 | 561360 | unknown | expanded_formal_data | 82441432.30 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 561560 | 561560 | unknown | expanded_formal_data | 168100376.75 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 562550 | 562550 | unknown | expanded_formal_data | 255153277.80 | 315 | classification_unknown; duplicate_exposure_lower_liquidity |
| 562920 | 562920 | unknown | expanded_formal_data | 12434409.65 | 315 | liquidity_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159001 | 货币ETF | bond_cash | 债券货币观察 | 596859295.12 | 315 | duplicate_exposure_lower_liquidity |
| 511010 | 国债ETF | bond_cash | 债券货币观察 | 419522969.50 | 315 | duplicate_exposure_lower_liquidity |
| 511260 | 十年国债ETF | bond_cash | 债券货币观察 | 3994881751.15 | 315 | duplicate_exposure_lower_liquidity |
| 159835 | 建信创新药ETF | theme | 医药与消费升级 | 16714629.86 | 315 | liquidity_low |
| 159858 | 南方创新药ETF | theme | 医药与消费升级 | 11566872.85 | 315 | liquidity_low |
| 513120 | 港股创新药ETF | qdii | 医药与消费升级 | 4041873508.85 | 315 | qdii_needs_premium_fx_calendar_check |
| 159825 | 农业ETF | commodity_resource | 周期资源 | 79763573.16 | 315 | duplicate_exposure_lower_liquidity |
| 159865 | 养殖ETF | commodity_resource | 周期资源 | 151781946.69 | 315 | duplicate_exposure_lower_liquidity |
| 159876 | 有色金属ETF | commodity_resource | 周期资源 | 113612726.66 | 315 | duplicate_exposure_lower_liquidity |
| 510410 | 资源ETF | commodity_resource | 周期资源 | 27128472.75 | 315 | duplicate_exposure_lower_liquidity |
| 516780 | 稀土ETF | commodity_resource | 周期资源 | 159660509.80 | 315 | extreme_volatility; duplicate_exposure_lower_liquidity |
| 159901 | 深100ETF | broad_index | 宽基 | 486724692.59 | 315 | duplicate_exposure_lower_liquidity |
| 159949 | 创业板50ETF | broad_index | 宽基 | 2505693349.44 | 315 | duplicate_exposure_lower_liquidity |
| 510050 | 上证50ETF | broad_index | 宽基 | 2608312387.25 | 315 | duplicate_exposure_lower_liquidity |
| 510180 | 上证180ETF | broad_index | 宽基 | 225843231.10 | 108 | history_lt_120d; duplicate_exposure_lower_liquidity |
| 510500 | 中证500ETF | broad_index | 宽基 | 3385723844.60 | 108 | history_lt_120d; duplicate_exposure_lower_liquidity |
| 512100 | 中证1000ETF | broad_index | 宽基 | 3088662433.35 | 108 | history_lt_120d; duplicate_exposure_lower_liquidity |
| 588080 | 科创创业50ETF | broad_index | 宽基 | 2002465950.15 | 315 | duplicate_exposure_lower_liquidity |
| 159593 | 中证A50ETF | broad_index | 新宽基与新风格 | 62293444.48 | 315 | duplicate_exposure_lower_liquidity |
| 512050 | 华夏中证A500ETF | broad_index | 新宽基与新风格 | 2254115828.05 | 315 | duplicate_exposure_lower_liquidity |
| 560510 | 泰康中证A500ETF | broad_index | 新宽基与新风格 | 67456866.50 | 315 | duplicate_exposure_lower_liquidity |
| 563800 | 广发中证A500ETF | broad_index | 新宽基与新风格 | 474579142.30 | 315 | duplicate_exposure_lower_liquidity |
| 588030 | 博时科创100ETF | broad_index | 新宽基与新风格 | 321705212.85 | 315 | duplicate_exposure_lower_liquidity |
| 588120 | 国泰科创100ETF | broad_index | 新宽基与新风格 | 112469737.40 | 315 | duplicate_exposure_lower_liquidity |
| 588190 | 银华科创100ETF | broad_index | 新宽基与新风格 | 189966850.25 | 315 | duplicate_exposure_lower_liquidity |
| 588220 | 科创100ETF基金 | broad_index | 新宽基与新风格 | 721767423.90 | 315 | duplicate_exposure_lower_liquidity |
| 588800 | 华夏科创100ETF | broad_index | 新宽基与新风格 | 344615553.00 | 315 | duplicate_exposure_lower_liquidity |
| 159806 | 新能源车电池ETF | commodity_resource | 新能源制造 | 30768681.97 | 315 | duplicate_exposure_lower_liquidity |
| 159857 | 光伏ETF | commodity_resource | 新能源制造 | 146027749.78 | 315 | duplicate_exposure_lower_liquidity |
| 512670 | 国防ETF | commodity_resource | 新能源制造 | 121322613.65 | 315 | duplicate_exposure_lower_liquidity |
| 515700 | 新能源车ETF | commodity_resource | 新能源制造 | 64456838.95 | 315 | duplicate_exposure_lower_liquidity |
| 516160 | 新能源ETF | commodity_resource | 新能源制造 | 259952755.25 | 315 | duplicate_exposure_lower_liquidity |
| 516390 | 新能源汽车ETF | commodity_resource | 新能源制造 | 5572068.45 | 315 | liquidity_low; duplicate_exposure_lower_liquidity |
| 516800 | 智能制造ETF | commodity_resource | 新能源制造 | 23713105.95 | 315 | duplicate_exposure_lower_liquidity |
| 159736 | 食品ETF | sector | 消费医药 | 27065672.64 | 315 | duplicate_exposure_lower_liquidity |
| 159766 | 旅游ETF | sector | 消费医药 | 202263141.44 | 315 | duplicate_exposure_lower_liquidity |
| 159928 | 消费ETF | sector | 消费医药 | 343424612.49 | 315 | duplicate_exposure_lower_liquidity |
| 159929 | 医药ETF | sector | 消费医药 | 72639570.16 | 315 | duplicate_exposure_lower_liquidity |
| 159996 | 家电ETF | sector | 消费医药 | 97888511.86 | 315 | duplicate_exposure_lower_liquidity |
| 515170 | 食品饮料ETF | sector | 消费医药 | 83763584.10 | 315 | duplicate_exposure_lower_liquidity |
| 515650 | 消费50ETF | sector | 消费医药 | 65396626.90 | 315 | duplicate_exposure_lower_liquidity |
| 516110 | 汽车ETF | sector | 消费医药 | 41216587.25 | 315 | duplicate_exposure_lower_liquidity |
| 159819 | 人工智能ETF | theme | 科技成长 | 770510261.57 | 315 | duplicate_exposure_lower_liquidity |
| 159869 | 游戏ETF | theme | 科技成长 | 393809041.93 | 315 | duplicate_exposure_lower_liquidity |
| 159995 | 芯片ETF | theme | 科技成长 | 1470343210.67 | 315 | high_volatility |
| 512480 | 半导体ETF | theme | 科技成长 | 1942413192.20 | 315 | high_volatility |
| 512760 | 芯片ETF | theme | 科技成长 | 647807451.20 | 315 | extreme_volatility; duplicate_exposure_lower_liquidity |
| 512980 | 传媒ETF | theme | 科技成长 | 230361565.55 | 315 | duplicate_exposure_lower_liquidity |
| 515000 | 科技ETF | unknown | 科技成长 | 185540692.10 | 1077 | classification_unknown |
| 515050 | 5GETF | theme | 科技成长 | 1417386420.45 | 315 | extreme_volatility; duplicate_exposure_lower_liquidity |
| 515070 | AIETF | theme | 科技成长 | 266679747.60 | 315 | duplicate_exposure_lower_liquidity |

## 推荐 exclude_pool 样例
| symbol | name | etf_type | group | avg_amount_20d | trading_days | review_reason |
| --- | --- | --- | --- | --- | --- | --- |
| 159332 | 159332 | unknown | expanded_formal_data | 2671692.01 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159717 | 159717 | unknown | expanded_formal_data | 3283446.61 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159787 | 159787 | unknown | expanded_formal_data | 2294982.05 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159791 | 159791 | unknown | expanded_formal_data | 3366009.69 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159797 | 159797 | unknown | expanded_formal_data | 3270538.52 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159889 | 159889 | unknown | expanded_formal_data | 3475165.61 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159954 | 159954 | unknown | expanded_formal_data | 3259726.48 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 510060 | 510060 | unknown | expanded_formal_data | 479583.65 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 510270 | 510270 | unknown | expanded_formal_data | 3306404.30 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 516360 | 516360 | unknown | expanded_formal_data | 4941707.30 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 516720 | 516720 | unknown | expanded_formal_data | 715817.90 | 315 | liquidity_ultra_low; classification_unknown; duplicate_exposure_lower_liquidity |
| 159940 | 金融ETF | sector | 金融地产 | 3365933.67 | 315 | liquidity_ultra_low |
