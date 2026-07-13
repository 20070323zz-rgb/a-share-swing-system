# 本地数据健康报告 2026-07-11 16:43:41

本报告只检查本地 CSV，不联网，不接券商 API，不下单。
QDII观察、债券货币观察、个股观察只做提醒，避免用过严规则误判。

## 摘要
- 检查标的总数：185
- 正常：171
- 提醒：12
- 异常：0
- 缺失：2

## 明细
| 代码 | 名称 | 类型 | pool | group | 文件 | 行数 | 最近日期 | 状态 | 硬问题 | 提醒 |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| 159001 | 货币ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sz_159001.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159301 | 159301 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159301.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159302 | 159302 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159302.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159315 | 159315 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159315.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159321 | 159321 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159321.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159327 | 159327 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159327.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159332 | 159332 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159332.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159333 | 159333 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159333.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159336 | 159336 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159336.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159338 | 国泰中证A500ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sz_159338.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159352 | 南方中证A500ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sz_159352.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159363 | 159363 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159363.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159395 | 159395 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159395.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159396 | 159396 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159396.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159398 | 159398 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159398.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159516 | 159516 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159516.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：3 次，仅提示不删除 |
| 159518 | 159518 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159518.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159531 | 159531 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159531.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159532 | 159532 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159532.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159536 | 159536 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159536.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159538 | 159538 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159538.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159539 | 159539 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159539.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159540 | 159540 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159540.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159545 | 159545 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159545.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159547 | 159547 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159547.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159549 | 159549 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159549.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159551 | 159551 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159551.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159558 | 159558 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159558.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 159559 | 159559 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159559.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159562 | 159562 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159562.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159593 | 中证A50ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sz_159593.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159595 | 159595 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159595.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159608 | 159608 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159608.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159611 | 159611 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159611.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159613 | 159613 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159613.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159615 | 159615 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159615.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159625 | 159625 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159625.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159638 | 159638 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159638.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159658 | 159658 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159658.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159663 | 159663 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159663.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 159667 | 159667 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159667.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 159669 | 159669 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159669.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159671 | 159671 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159671.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159697 | 159697 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159697.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159699 | 159699 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159699.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159703 | 159703 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159703.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159717 | 159717 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159717.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159726 | 159726 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159726.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159732 | 159732 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159732.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159735 | 159735 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159735.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159736 | 食品ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159736.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159745 | 159745 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159745.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159755 | 电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159755.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159758 | 159758 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159758.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159763 | 159763 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159763.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159766 | 旅游ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159766.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159770 | 机器人ETF | ETF | observe_pool | 科技与新质生产力 | data/etf_daily/sz_159770.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159787 | 159787 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159787.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159791 | 159791 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159791.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159795 | 159795 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159795.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159797 | 159797 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159797.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159806 | 新能源车电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159806.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159819 | 人工智能ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159819.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159825 | 农业ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159825.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159835 | 建信创新药ETF | ETF | observe_pool | 医药与消费升级 | data/etf_daily/sz_159835.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159840 | 159840 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159840.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159857 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159857.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159858 | 南方创新药ETF | ETF | observe_pool | 医药与消费升级 | data/etf_daily/sz_159858.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159865 | 养殖ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159865.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159869 | 游戏ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159869.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159870 | 化工ETF | ETF | observe_pool | 周期、资源、商品 | data/etf_daily/sz_159870.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159876 | 有色金属ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159876.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159883 | 159883 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159883.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159888 | 159888 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159888.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159889 | 159889 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159889.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159898 | 159898 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159898.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159901 | 深100ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159901.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159905 | 深红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sz_159905.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159915 | 创业板ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159915.csv | 1093 | 2026-07-10 | 正常 |  |  |
| 159920 | 恒生ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159920.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159928 | 消费ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159928.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159929 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159929.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159930 | 能源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159930.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159940 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sz_159940.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159941 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159941.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159949 | 创业板50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159949.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159954 | 159954 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159954.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159992 | 银华创新药ETF | ETF | trade_pool | 医药与消费升级 | data/etf_daily/sz_159992.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159995 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159995.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 159996 | 家电ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159996.csv | 331 | 2026-07-10 | 正常 |  |  |
| 159997 | 159997 | ETF | research_only | expanded_formal_data | data/etf_daily/sz_159997.csv | 331 | 2026-07-10 | 正常 |  |  |
| 300750 | 宁德时代 | STOCK | observe_pool | 个股观察 |  | 0 |  | 缺失 |  | 缺少本地 CSV |
| 510050 | 上证50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510050.csv | 331 | 2026-07-10 | 正常 |  |  |
| 510060 | 510060 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_510060.csv | 331 | 2026-07-10 | 正常 |  |  |
| 510180 | 上证180ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510180.csv | 124 | 2026-07-10 | 正常 |  |  |
| 510230 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_510230.csv | 331 | 2026-07-10 | 正常 |  |  |
| 510270 | 510270 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_510270.csv | 331 | 2026-07-10 | 正常 |  |  |
| 510300 | 沪深300ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510300.csv | 1093 | 2026-07-10 | 正常 |  |  |
| 510410 | 资源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_510410.csv | 331 | 2026-07-10 | 正常 |  |  |
| 510500 | 中证500ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510500.csv | 124 | 2026-07-10 | 正常 |  |  |
| 510880 | 红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_510880.csv | 124 | 2026-07-10 | 正常 |  |  |
| 511010 | 国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511010.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511030 | 公司债ETF | ETF | observe_pool | 债券货币 | data/etf_daily/sh_511030.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511090 | 30年国债ETF | ETF | observe_pool | 债券货币 | data/etf_daily/sh_511090.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511260 | 十年国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511260.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511360 | 短融ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511360.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511380 | 可转债ETF | ETF | observe_pool | 债券货币 | data/etf_daily/sh_511380.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511520 | 政金债ETF | ETF | observe_pool | 债券货币 | data/etf_daily/sh_511520.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511600 | 511600 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_511600.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511690 | 511690 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_511690.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511880 | 银华日利ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511880.csv | 331 | 2026-07-10 | 正常 |  |  |
| 511990 | 华宝添益ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511990.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512010 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512010.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512050 | 华夏中证A500ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sh_512050.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512070 | 非银ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512070.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512100 | 中证1000ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_512100.csv | 124 | 2026-07-10 | 正常 |  |  |
| 512170 | 医疗ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512170.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512200 | 房地产ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512200.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512400 | 有色ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_512400.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512480 | 半导体ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512480.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 512660 | 军工ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512660.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512670 | 国防ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512670.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512690 | 酒ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512690.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512760 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512760.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 512800 | 银行ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512800.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512880 | 证券ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512880.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512890 | 红利低波ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_512890.csv | 331 | 2026-07-10 | 正常 |  |  |
| 512980 | 传媒ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512980.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513030 | 德国ETF | ETF | research_only | 跨境与港股 | data/etf_daily/sh_513030.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513050 | 中概互联网ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513050.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513060 | 恒生医疗ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513060.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513100 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513100.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513120 | 港股创新药ETF | ETF | observe_pool | 医药与消费升级 | data/etf_daily/sh_513120.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513130 | 恒生科技ETF | ETF | observe_pool | 跨境与港股 | data/etf_daily/sh_513130.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513150 | 港股科技ETF | ETF | observe_pool | 跨境与港股 | data/etf_daily/sh_513150.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513180 | 恒生科技ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513180.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513330 | 恒生互联网ETF | ETF | observe_pool | 跨境与港股 | data/etf_daily/sh_513330.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513500 | 标普500ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513500.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513520 | 日经ETF | ETF | research_only | 跨境与港股 | data/etf_daily/sh_513520.csv | 331 | 2026-07-10 | 正常 |  |  |
| 513880 | 日经225ETF | ETF | research_only | 跨境与港股 | data/etf_daily/sh_513880.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515000 | 科技ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515000.csv | 1093 | 2026-07-10 | 正常 |  |  |
| 515050 | 5GETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515050.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 515070 | AIETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515070.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 515080 | 中证红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_515080.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515120 | 广发创新药ETF | ETF | trade_pool | 医药与消费升级 | data/etf_daily/sh_515120.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515170 | 食品饮料ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515170.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515210 | 515210 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_515210.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515220 | 煤炭ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_515220.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515230 | 软件ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515230.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515260 | 515260 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_515260.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515630 | 515630 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_515630.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515650 | 消费50ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515650.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515700 | 新能源车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515700.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515790 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515790.csv | 331 | 2026-07-10 | 正常 |  |  |
| 515880 | 证券公司ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_515880.csv | 124 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：2 次，仅提示不删除 |
| 516020 | 化工ETF | ETF | trade_pool | 周期、资源、商品 | data/etf_daily/sh_516020.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516080 | 易方达创新药ETF | ETF | trade_pool | 医药与消费升级 | data/etf_daily/sh_516080.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516110 | 汽车ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_516110.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516160 | 新能源ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516160.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516360 | 516360 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_516360.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516390 | 新能源汽车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516390.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516510 | 云计算ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_516510.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516720 | 516720 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_516720.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516750 | 516750 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_516750.csv | 331 | 2026-07-10 | 正常 |  |  |
| 516780 | 稀土ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_516780.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 516800 | 智能制造ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516800.csv | 331 | 2026-07-10 | 正常 |  |  |
| 518880 | 黄金ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_518880.csv | 331 | 2026-07-10 | 正常 |  |  |
| 520550 | 港股红利低波ETF | ETF | observe_pool | 防御、红利、质量 | data/etf_daily/sh_520550.csv | 331 | 2026-07-10 | 正常 |  |  |
| 560510 | 泰康中证A500ETF | ETF | observe_pool | 新宽基与新风格 | data/etf_daily/sh_560510.csv | 331 | 2026-07-10 | 正常 |  |  |
| 561360 | 561360 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_561360.csv | 331 | 2026-07-10 | 正常 |  |  |
| 561560 | 561560 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_561560.csv | 331 | 2026-07-10 | 正常 |  |  |
| 562500 | 机器人ETF华夏 | ETF | trade_pool | 科技与新质生产力 | data/etf_daily/sh_562500.csv | 331 | 2026-07-10 | 正常 |  |  |
| 562550 | 562550 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_562550.csv | 331 | 2026-07-10 | 正常 |  |  |
| 562920 | 562920 | ETF | research_only | expanded_formal_data | data/etf_daily/sh_562920.csv | 331 | 2026-07-10 | 正常 |  |  |
| 563360 | 华泰柏瑞中证A500ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sh_563360.csv | 331 | 2026-07-10 | 正常 |  |  |
| 563800 | 广发中证A500ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sh_563800.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588000 | 科创50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588000.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588030 | 博时科创100ETF | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sh_588030.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588080 | 科创创业50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588080.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588120 | 国泰科创100ETF | ETF | observe_pool | 新宽基与新风格 | data/etf_daily/sh_588120.csv | 331 | 2026-07-10 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 588190 | 银华科创100ETF | ETF | observe_pool | 新宽基与新风格 | data/etf_daily/sh_588190.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588200 | 科创芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_588200.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588220 | 科创100ETF基金 | ETF | trade_pool | 新宽基与新风格 | data/etf_daily/sh_588220.csv | 331 | 2026-07-10 | 正常 |  |  |
| 588800 | 华夏科创100ETF | ETF | observe_pool | 新宽基与新风格 | data/etf_daily/sh_588800.csv | 331 | 2026-07-10 | 正常 |  |  |
| 600519 | 贵州茅台 | STOCK | observe_pool | 个股观察 |  | 0 |  | 缺失 |  | 缺少本地 CSV |