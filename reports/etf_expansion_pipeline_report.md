# ETF Expansion Pipeline Report

- Generated on: 2026-06-09
- Mode: batch staging -> validate -> dry-run -> partial formal import.
- Expanded staging CSV total: 121
- Validation valid: 121
- Validation failed: 0
- Dry-run success: 107
- Dry-run failed: 0
- Formal import completed: yes
- Formal import count: 107
- BaoStock API calls: 0
- Safety: no broker API, no real orders, no account/password storage, no automatic trading, no strategy or position-rule changes.
- Staging rule: new data is downloaded only to `data/staging/jqdata_expanded/` before validation and dry-run.
- Merge rule: formal import uses existing local rows first on duplicate dates.

## Step Summary

| step | status | returncode | note |
| --- | --- | ---: | --- |
| fetch_jqdata_candidates | skipped | 0 | JQData credentials not set; using existing local candidate list. |
| resolve_candidates | ok | 0 | resolved candidate rows written: data/staging/etf_candidates/resolved_etf_expansion_candidates.csv |
| download_resolved_staging | skipped | 0 | JQData credentials not set; using existing data/staging/jqdata_expanded/ files. |
| validate_staging | ok | 0 | data/staging/jqdata_expanded/159053.XSHE.csv failed validation: bad OHLC rows: 241; volume negative or invalid rows: 241; money negative or invalid rows: 241 |
| diagnose_units | skipped | 0 | diagnose_jqdata_units.py does not support --input-dir yet; import script handles local-overlap checks where possible. |
| dry_run_import | ok | 0 | jqdata staging dry-run finished: success 107, failed 0, validation_failed 14 |
| formal_import | ok | 0 | jqdata staging import finished: success 107, failed 0, validation_failed 0 |
| data_coverage | ok | 0 | 已生成数据覆盖报告：/Users/dayin/Code/a-share-swing-system/reports/data_coverage_report.md |
| data_health | ok | 0 | 已生成数据健康报告：/Users/dayin/Code/a-share-swing-system/reports/data_health_report.md |
| main_reports | ok | 0 | 已生成每日信号报告：/Users/dayin/Code/a-share-swing-system/reports/daily_signal_2026-06-03.md |
| factor_analysis | ok | 0 | 已生成因子有效性报告：/Users/dayin/Code/a-share-swing-system/reports/factor_analysis_report.md |
| model_research | ok | 0 | 已生成模型研究报告：/Users/dayin/Code/a-share-swing-system/reports/model_research_report.md |

## Step Output

### fetch_jqdata_candidates

- Status: skipped
- Return code: 0

```text
JQData credentials not set; using existing local candidate list.
```

### resolve_candidates

- Status: ok
- Return code: 0

```text
resolved candidate rows written: data/staging/etf_candidates/resolved_etf_expansion_candidates.csv
resolution summary: resolved 121, unresolved 20, duplicate 10, existing 4
downloadable resolved ETFs: 121
```

### download_resolved_staging

- Status: skipped
- Return code: 0

```text
JQData credentials not set; using existing data/staging/jqdata_expanded/ files.
```

### validate_staging

- Status: ok
- Return code: 0

```text
aging/jqdata_expanded/159758.XSHE.csv passed validation.
data/staging/jqdata_expanded/159763.XSHE.csv passed validation.
data/staging/jqdata_expanded/159770.XSHE.csv passed validation.
data/staging/jqdata_expanded/159787.XSHE.csv passed validation.
data/staging/jqdata_expanded/159791.XSHE.csv passed validation.
data/staging/jqdata_expanded/159795.XSHE.csv passed validation.
data/staging/jqdata_expanded/159797.XSHE.csv passed validation.
data/staging/jqdata_expanded/159835.XSHE.csv passed validation.
data/staging/jqdata_expanded/159840.XSHE.csv passed validation.
data/staging/jqdata_expanded/159858.XSHE.csv passed validation.
data/staging/jqdata_expanded/159870.XSHE.csv passed validation.
data/staging/jqdata_expanded/159883.XSHE.csv passed validation.
data/staging/jqdata_expanded/159888.XSHE.csv passed validation.
data/staging/jqdata_expanded/159889.XSHE.csv passed validation.
data/staging/jqdata_expanded/159898.XSHE.csv passed validation.
data/staging/jqdata_expanded/159954.XSHE.csv passed validation.
data/staging/jqdata_expanded/159992.XSHE.csv passed validation.
data/staging/jqdata_expanded/159997.XSHE.csv passed validation.
data/staging/jqdata_expanded/510060.XSHG.csv passed validation.
data/staging/jqdata_expanded/510270.XSHG.csv passed validation.
data/staging/jqdata_expanded/511030.XSHG.csv passed validation.
data/staging/jqdata_expanded/511090.XSHG.csv passed validation.
data/staging/jqdata_expanded/511380.XSHG.csv passed validation.
data/staging/jqdata_expanded/511520.XSHG.csv passed validation.
data/staging/jqdata_expanded/511600.XSHG.csv passed validation.
data/staging/jqdata_expanded/511690.XSHG.csv passed validation.
data/staging/jqdata_expanded/512050.XSHG.csv passed validation.
data/staging/jqdata_expanded/513030.XSHG.csv passed validation.
data/staging/jqdata_expanded/513120.XSHG.csv passed validation.
data/staging/jqdata_expanded/513130.XSHG.csv passed validation.
data/staging/jqdata_expanded/513150.XSHG.csv passed validation.
data/staging/jqdata_expanded/513330.XSHG.csv passed validation.
data/staging/jqdata_expanded/513520.XSHG.csv passed validation.
data/staging/jqdata_expanded/513880.XSHG.csv passed validation.
data/staging/jqdata_expanded/515120.XSHG.csv passed validation.
data/staging/jqdata_expanded/515210.XSHG.csv passed validation.
data/staging/jqdata_expanded/515260.XSHG.csv passed validation.
data/staging/jqdata_expanded/515630.XSHG.csv passed validation.
data/staging/jqdata_expanded/516020.XSHG.csv passed validation.
data/staging/jqdata_expanded/516080.XSHG.csv passed validation.
data/staging/jqdata_expanded/516360.XSHG.csv passed validation.
data/staging/jqdata_expanded/516720.XSHG.csv passed validation.
data/staging/jqdata_expanded/516750.XSHG.csv passed validation.
data/staging/jqdata_expanded/520550.XSHG.csv passed validation.
data/staging/jqdata_expanded/560510.XSHG.csv passed validation.
data/staging/jqdata_expanded/561360.XSHG.csv passed validation.
data/staging/jqdata_expanded/561560.XSHG.csv passed validation.
data/staging/jqdata_expanded/562080.XSHG.csv failed validation: bad OHLC rows: 30; volume negative or invalid rows: 30; money negative or invalid rows: 30
data/staging/jqdata_expanded/562500.XSHG.csv passed validation.
data/staging/jqdata_expanded/562550.XSHG.csv passed validation.
data/staging/jqdata_expanded/562920.XSHG.csv passed validation.
data/staging/jqdata_expanded/563360.XSHG.csv passed validation.
data/staging/jqdata_expanded/563800.XSHG.csv passed validation.
data/staging/jqdata_expanded/588030.XSHG.csv passed validation.
data/staging/jqdata_expanded/588120.XSHG.csv passed validation.
data/staging/jqdata_expanded/588190.XSHG.csv passed validation.
data/staging/jqdata_expanded/588220.XSHG.csv passed validation.
data/staging/jqdata_expanded/588800.XSHG.csv passed validation.
data/staging/jqdata_expanded/589520.XSHG.csv failed validation: bad OHLC rows: 8; volume negative or invalid rows: 8; money negative or invalid rows: 8
manual CSV validation finished: valid 107, failed 14
```

### diagnose_units

- Status: skipped
- Return code: 0

```text
diagnose_jqdata_units.py does not support --input-dir yet; import script handles local-overlap checks where possible.
```

### dry_run_import

- Status: ok
- Return code: 0

```text
jqdata staging dry-run finished: success 107, failed 0, validation_failed 14
report written: reports/jqdata_import_report.md
expansion report written: reports/etf_expansion_import_report.md
results csv written: reports/etf_expansion_import_results.csv
```

### formal_import

- Status: ok
- Return code: 0

```text
jqdata staging import finished: success 107, failed 0, validation_failed 0
report written: reports/jqdata_import_report.md
expansion report written: reports/etf_expansion_import_report.md
results csv written: reports/etf_expansion_import_results.csv
```

### data_coverage

- Status: ok
- Return code: 0

```text
已生成数据覆盖报告：/Users/dayin/Code/a-share-swing-system/reports/data_coverage_report.md
本报告只读取本地 CSV，不包含任何真实交易接口。
```

### data_health

- Status: ok
- Return code: 0

```text
已生成数据健康报告：/Users/dayin/Code/a-share-swing-system/reports/data_health_report.md
本报告只读取本地 CSV，不包含任何真实交易接口。
```

### main_reports

- Status: ok
- Return code: 0

```text
已生成每日信号报告：/Users/dayin/Code/a-share-swing-system/reports/daily_signal_2026-06-03.md
已生成每日最简摘要：/Users/dayin/Code/a-share-swing-system/reports/latest_brief.md
已生成ETF横截面排名报告：/Users/dayin/Code/a-share-swing-system/reports/ranking_report.md
已生成因子有效性报告：/Users/dayin/Code/a-share-swing-system/reports/factor_analysis_report.md
已生成短期策略报告：/Users/dayin/Code/a-share-swing-system/reports/latest_short_swing.md
已生成数据覆盖报告：reports/latest_data_coverage.md
已生成数据健康报告：reports/latest_data_health.md
已生成模拟盘持仓报告：/Users/dayin/Code/a-share-swing-system/reports/latest_paper_portfolio.md
已生成风险控制报告：/Users/dayin/Code/a-share-swing-system/reports/risk_report.md
已更新模型研究数据集：/Users/dayin/Code/a-share-swing-system/reports/model_dataset.csv
所有交易均为模拟盘记录，不含任何真实下单接口。
```

### factor_analysis

- Status: ok
- Return code: 0

```text
已生成因子有效性报告：/Users/dayin/Code/a-share-swing-system/reports/factor_analysis_report.md
```

### model_research

- Status: ok
- Return code: 0

```text
已生成模型研究报告：/Users/dayin/Code/a-share-swing-system/reports/model_research_report.md
```
