# JQData ETF 日线本机可用性测试报告

- 生成时间：2026-06-09 00:02:04
- jqdatasdk import：成功
- jqdatasdk 版本：1.9.8
- 检测到账号环境变量：是
- 检测到密码环境变量：是
- 认证成功：否
- 测试区间：2025-03-01 到 2026-03-01
- 输出目录：`data/staging/jqdata`
- 选中 ETF 数：76
- 成功返回数据 ETF 数：0
- 失败 ETF 数：76
- 成功数据日期范围一致：否
- 成功数据字段均满足项目标准：否
- 建议作为历史补齐候选源 ETF 数：0
- 安全边界：不接券商 API；不真实下单；不读取券商账号；不保存任何密码；不自动交易；不写入 `data/etf_daily/`。

## 认证与环境

- 认证/环境说明：authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)")

## ETF 结果

| symbol | jq_symbol | status | rows | start_date | end_date | fields | required_fields_ok | fallback_used | failure_reason | recommend_backfill_candidate | output_path |
|---|---|---:|---:|---|---|---|---:|---:|---|---:|---|
| 510300 | 510300.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510300.XSHG.csv` |
| 510500 | 510500.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510500.XSHG.csv` |
| 512100 | 512100.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512100.XSHG.csv` |
| 159915 | 159915.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159915.XSHE.csv` |
| 588000 | 588000.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/588000.XSHG.csv` |
| 510050 | 510050.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510050.XSHG.csv` |
| 510180 | 510180.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510180.XSHG.csv` |
| 159901 | 159901.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159901.XSHE.csv` |
| 159949 | 159949.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159949.XSHE.csv` |
| 588080 | 588080.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/588080.XSHG.csv` |
| 512880 | 512880.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512880.XSHG.csv` |
| 512800 | 512800.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512800.XSHG.csv` |
| 512200 | 512200.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512200.XSHG.csv` |
| 510230 | 510230.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510230.XSHG.csv` |
| 159940 | 159940.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159940.XSHE.csv` |
| 512070 | 512070.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512070.XSHG.csv` |
| 515880 | 515880.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515880.XSHG.csv` |
| 512010 | 512010.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512010.XSHG.csv` |
| 159929 | 159929.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159929.XSHE.csv` |
| 512170 | 512170.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512170.XSHG.csv` |
| 512690 | 512690.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512690.XSHG.csv` |
| 159928 | 159928.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159928.XSHE.csv` |
| 515650 | 515650.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515650.XSHG.csv` |
| 159996 | 159996.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159996.XSHE.csv` |
| 515170 | 515170.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515170.XSHG.csv` |
| 159736 | 159736.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159736.XSHE.csv` |
| 159766 | 159766.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159766.XSHE.csv` |
| 516110 | 516110.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516110.XSHG.csv` |
| 512480 | 512480.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512480.XSHG.csv` |
| 512760 | 512760.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512760.XSHG.csv` |
| 159995 | 159995.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159995.XSHE.csv` |
| 588200 | 588200.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/588200.XSHG.csv` |
| 515050 | 515050.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515050.XSHG.csv` |
| 515000 | 515000.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515000.XSHG.csv` |
| 515230 | 515230.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515230.XSHG.csv` |
| 159819 | 159819.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159819.XSHE.csv` |
| 515070 | 515070.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515070.XSHG.csv` |
| 159869 | 159869.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159869.XSHE.csv` |
| 516510 | 516510.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516510.XSHG.csv` |
| 512980 | 512980.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512980.XSHG.csv` |
| 515790 | 515790.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515790.XSHG.csv` |
| 159857 | 159857.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159857.XSHE.csv` |
| 516160 | 516160.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516160.XSHG.csv` |
| 515700 | 515700.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515700.XSHG.csv` |
| 159755 | 159755.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159755.XSHE.csv` |
| 516390 | 516390.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516390.XSHG.csv` |
| 516800 | 516800.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516800.XSHG.csv` |
| 512660 | 512660.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512660.XSHG.csv` |
| 512670 | 512670.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512670.XSHG.csv` |
| 159806 | 159806.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159806.XSHE.csv` |
| 512400 | 512400.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512400.XSHG.csv` |
| 516780 | 516780.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/516780.XSHG.csv` |
| 515220 | 515220.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515220.XSHG.csv` |
| 159930 | 159930.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159930.XSHE.csv` |
| 510410 | 510410.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510410.XSHG.csv` |
| 159865 | 159865.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159865.XSHE.csv` |
| 159825 | 159825.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159825.XSHE.csv` |
| 159876 | 159876.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159876.XSHE.csv` |
| 510880 | 510880.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/510880.XSHG.csv` |
| 512890 | 512890.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/512890.XSHG.csv` |
| 515080 | 515080.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/515080.XSHG.csv` |
| 159905 | 159905.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159905.XSHE.csv` |
| 518880 | 518880.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/518880.XSHG.csv` |
| 513500 | 513500.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/513500.XSHG.csv` |
| 513100 | 513100.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/513100.XSHG.csv` |
| 513180 | 513180.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/513180.XSHG.csv` |
| 159920 | 159920.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159920.XSHE.csv` |
| 513050 | 513050.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/513050.XSHG.csv` |
| 513060 | 513060.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/513060.XSHG.csv` |
| 159941 | 159941.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159941.XSHE.csv` |
| 511010 | 511010.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/511010.XSHG.csv` |
| 511260 | 511260.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/511260.XSHG.csv` |
| 511880 | 511880.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/511880.XSHG.csv` |
| 511990 | 511990.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/511990.XSHG.csv` |
| 511360 | 511360.XSHG | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/511360.XSHG.csv` |
| 159001 | 159001.XSHE | auth_failed | 0 |  |  |  | 否 | 否 | authentication failed: TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)") | 否 | `data/staging/jqdata/159001.XSHE.csv` |

## 结论

1. JQData SDK 是否可用：是。
2. 是否能认证：否。
3. 选中 ETF 是否全部返回数据：否。
4. 数据字段是否满足项目标准：否。
5. 是否能用于补齐部分历史段：否。
6. 是否保持安全边界不变：是。
