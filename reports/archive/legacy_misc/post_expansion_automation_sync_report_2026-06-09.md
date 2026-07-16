# ETF 扩池后自动化同步与近期补数报告

检查时间：2026-06-09 23:41:41 CST

本报告只记录本地数据更新、launchd 自动化链路与研究报告再生成情况。全程不接券商 API，不真实下单，不读取或保存交易账户，不保存任何数据源密码。

## 结论摘要

- 扩池后正式 ETF 数据文件数量：183
- daily update universe 数量：183
- 本轮补齐区间：2026-03-02 至 2026-06-09
- BaoStock API calls 估算/实际：183 / 183，远低于 50000
- 成功更新或已覆盖 ETF 数：183
- 失败 ETF 数：0
- 本轮新增日线行数：7580
- 183 个正式 ETF 文件的最新日期均为：2026-06-09
- 正式目录 CSV 验证：valid 183，failed 0
- 重复日期处理：合并时保留 data/etf_daily/ 本地原有行
- launchd daily_close 已覆盖扩池后的正式 ETF 数据文件
- 主策略 watchlist 未自动扩入新增 ETF；latest_brief、factor_analysis、model_research 仍按现有策略池生成

## 自动化问题与修复

原问题：

- `scripts/run_daily_close.sh` 原先调用 `scripts/update_etf_data.py --end 当日 --adjustflag 2`。
- 旧调用默认只读取 `watchlist.csv` 中 `trade_pool` / `observe_pool` 的 ETF，无法覆盖扩池后已正式并入 `data/etf_daily/` 的新增 ETF 文件。
- 因此扩池 ETF 虽已正式入库，但不会被每日收盘自动更新链路持续补齐。

已修复：

- `scripts/update_etf_data.py` 已支持 `--all-etf`、`--symbols`、`--start`、`--end`、`--source baostock`、`--dry-run`、`--skip-existing`、`--max-api-calls`。
- `--all-etf` 的更新 universe 以 `data/etf_daily/` 中正式 ETF CSV 为基础，同时读取 watchlist 和扩池候选状态。
- 自动排除 `failed_validation`、`failed_dry_run`、`unresolved`、`excluded` 以及隔离目录中的 ETF。
- 调用 BaoStock 前估算 API calls，超过上限会停止。
- `scripts/run_daily_close.sh` 已改为调用：

```bash
.venv/bin/python scripts/update_etf_data.py --source baostock --all-etf --skip-existing --max-api-calls 50000 --end "$(date '+%Y-%m-%d')" --adjustflag 2
```

launchd plist 状态：

- `launchd/com.dayin.a-share.daily-close.plist` 继续调用 `/Users/dayin/Code/a-share-swing-system/scripts/run_daily_close.sh`
- 工作目录为 `/Users/dayin/Code/a-share-swing-system`
- 运行时间未修改，仍为工作日 15:30

## 更新 Universe 与排除项

- 正式 `data/etf_daily/` ETF CSV：183
- 扩池 valid staging CSV：107
- 扩池 failed/quarantine CSV：14
- `reports/etf_expansion_import_results.csv` final_action：
  - imported：107
  - quarantined：14
  - unresolved：20
  - skipped_existing：4
- `data/etf_pool_expansion_candidates.csv` status：
  - imported：70
  - unresolved：21
  - failed_validation：3

排除规则：

- failed/quarantine/unresolved ETF 不进入每日更新 universe
- 不删除原有 76 个老池 ETF
- 不删除已正式并入且数据健康合格的 ETF
- 新增 ETF 进入数据更新 universe 不等于进入 trade_pool

## 近期数据补齐结果

- 数据源：BaoStock 公开行情
- 更新范围：2026-03-02 至 2026-06-09
- 调用方式：`--all-etf`
- Universe size：183
- Estimated/actual BaoStock query calls：183
- Success or skipped：183
- Failed：0
- Added rows：7580
- Duplicate-date rule：existing local rows win during merge
- 所有 183 个正式 ETF 文件最新日期：2026-06-09
- `data/etf_daily/` 总行数：57798
- `data/etf_daily/` 全量 CSV 验证：183 passed，0 failed

输出报告：

- `reports/data_download_report.md`
- `reports/data_update_log.md`

## 重新生成报告

已重新生成：

- `reports/latest_data_coverage.md`
- `reports/latest_data_health.md`
- `reports/latest_brief.md`
- `reports/factor_analysis_report.md`
- `reports/model_research_report.md`
- `reports/model_dataset.csv`

检查结果：

- latest_data_coverage：当前 active watchlist ETF 覆盖率 76/76 = 100.00%，数据过期数量 0
- latest_data_health：异常 0，缺失 2；缺失项为 600519、300750 个股观察，不属于 ETF 下载脚本处理范围
- latest_brief：已使用 2026-06-09 本地数据生成
- factor_analysis：已生成；future return 样本仍不足，报告提示不应过度解读
- model_research：已生成；可训练样本数 0，本次不训练模型
- model_dataset：已更新，145 行，覆盖现有 active watchlist 的 63 个 trade_pool ETF

补充修复：

- `src/factor_analysis.py` 增加 Spearman Rank IC 的本地计算兜底，避免环境缺少 SciPy 时导致 `src/main.py` 和 launchd daily_close 报告阶段失败。
- 该修改只影响研究报告计算稳定性，不参与交易信号，不修改策略规则。

## 安全边界确认

- 不接券商 API：yes
- 不真实下单：yes
- 不读取或保存交易账户：yes
- 不保存 JQData/Tushare/BaoStock 密钥：yes
- 不 echo 密码：yes
- 不读取 JQData 账号密码：yes
- 不调用 JQData 下载：yes
- 不修改交易规则：yes
- 不修改仓位规则：yes
- 不改变策略逻辑：yes
- 不把新增 ETF 自动放入 trade_pool：yes
- 不删除原有 76 个老池 ETF：yes
- 不把 failed_validation ETF 放回更新池：yes
- BaoStock 调用量远低于 50000：yes，183 calls

## 修改文件

- `scripts/update_etf_data.py`
- `scripts/run_daily_close.sh`
- `src/factor_analysis.py`
- `reports/data_download_report.md`
- `reports/data_update_log.md`
- `reports/latest_data_coverage.md`
- `reports/latest_data_health.md`
- `reports/latest_brief.md`
- `reports/factor_analysis_report.md`
- `reports/model_research_report.md`
- `reports/model_dataset.csv`
- `reports/post_expansion_automation_sync_report.md`
