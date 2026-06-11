# daily data update diagnosis report

- 修复时间：2026-06-10 18:42
- 权限等级：L2 联网数据权限
- 范围：BaoStock ETF 日线更新状态分类、daily_close 更新链路、全量最新日线补齐
- 安全边界：只读取公开行情并写入本地 CSV，不接券商 API，不真实下单，不读取真实账户，不保存密码/token，不修改策略规则，不新增模拟交易

## 1. 为什么之前显示 183 个 failed

旧逻辑只要某只 ETF 需要下载缺口，而 BaoStock 返回空数据，就把该 ETF 记为 `failed`。

2026-06-10 15:30 自动运行时，大量 ETF 的请求是：

```text
backfill 2018-01-01~2025-03-02: 返回空数据
forward 2026-06-10~2026-06-10: 返回空数据
```

其中 `forward` 当天返回空，常见原因是 BaoStock 当时尚未更新 ETF 日线；`backfill` 返回空，则可能是 BaoStock 不支持更早历史或 ETF 当时尚未上市。旧逻辑没有区分这些正常空数据和真正异常，所以误报为 `failed 183`。

## 2. 新状态分类

`scripts/update_etf_data.py` 已改为多状态统计：

- `success_appended`：成功追加新行。
- `up_to_date`：本地已经覆盖请求结束日期。
- `no_new_data`：本地数据可用，请求无新增。
- `pending_source_update`：forward 请求返回空，可能数据源尚未更新或当日无可用数据。
- `backfill_no_data`：历史前补返回空，但本地已有有效数据，不算失败。
- `partial_success`：部分请求成功写入，部分请求为空或异常。
- `unsupported_or_empty`：本地无有效数据且 BaoStock 全范围返回空，可能不支持该 ETF。
- `failed_error`：BaoStock 异常、登录失败、字段缺失或写入失败，这才是真正系统失败。

## 3. backfill 返回空如何处理

- 本地已有有效历史数据：标记为 `backfill_no_data`，不算真正失败。
- 本地无有效数据：标记为 `unsupported_or_empty` 或 `failed_error`，需要人工复核。

## 4. forward 当天返回空如何处理

- 如果请求日是当天或未来，且本地已有 T-1 或更早有效数据：标记为 `pending_source_update`。
- 含义：数据源可能尚未更新，不代表系统失败。
- 报告继续基于本地最新数据日生成，并在下载报告中保留说明。

## 5. 长期效率优化

`scripts/run_daily_close.sh` 已改为调用：

```bash
python scripts/update_etf_data.py --source baostock --all-etf --skip-existing --skip-backfill --max-api-calls 50000 --end YYYY-MM-DD --adjustflag 2
```

原因：

- daily_close 只需要补最近缺失交易日。
- 历史 backfill 不应在每天收盘自动反复请求。
- 历史补齐仍可手动运行不带 `--skip-backfill` 的命令单独完成。

同时新增 `--request-timeout`，默认 20 秒，避免单只 BaoStock 请求网络等待拖死 launchd。

## 6. 小样本测试结果

测试命令：

```bash
.venv/bin/python scripts/update_etf_data.py --source baostock --symbols 515220 512800 515880 --skip-existing --max-api-calls 100 --end 2026-06-10 --adjustflag 2
```

第一次小样本结果：

- `success_appended`: 3
- 三只当前模拟持仓 ETF 均追加到 2026-06-10。

第二次小样本结果：

- `backfill_no_data`: 3
- 说明本地已最新后，历史前补无数据不再计为失败。

## 7. 全量正式更新结果

执行命令：

```bash
.venv/bin/python scripts/update_etf_data.py --source baostock --all-etf --skip-existing --skip-backfill --max-api-calls 50000 --end 2026-06-10 --adjustflag 2 --request-timeout 12
```

结果：

- Universe size：183
- Estimated/actual BaoStock query calls：18
- `success_appended`: 18
- `up_to_date`: 165
- `failed_error`: 0
- `unsupported_or_empty`: 0
- `no_new_data`: 0
- `pending_source_update`: 0
- 新增行数：18
- 当前 `data/etf_daily/` 文件数：183
- 当前 183 个正式 ETF CSV 最新日期均为：2026-06-10

## 8. 报告与看板刷新

已重新生成：

- `reports/data_download_report.md`
- `reports/data_update_log.md`
- `reports/latest_data_coverage.md`
- `reports/latest_data_health.md`
- `reports/latest_brief.md`
- `reports/factor_analysis_report.md`
- `reports/model_research_report.md`
- `reports/latest_paper_portfolio.md`
- `reports/dashboard_data.json`
- `dashboard/index.html`

数据覆盖摘要：

- ETF/观察池总数：78
- ETF 数据缺失数量：0
- 有效数据数量：76
- 数据过期数量：0
- trade_pool 覆盖率：63/63 = 100.00%

数据健康摘要：

- 正常：72
- 提醒：4
- 异常：0
- 缺失：2
- 515880 仍保留 `data_health caution`，未被自动解除。

## 9. 模拟交易与持仓

- `data/paper_positions.csv` 行数：3
- `data/paper_trades.csv` 行数：3
- 本轮没有新增模拟交易。
- 本轮没有修改模拟持仓规则。

## 10. 是否需要等 BaoStock 后续更新

本轮 18:42 左右全量补齐后，183 个正式 ETF CSV 均已到 2026-06-10，因此当前不需要等待 BaoStock 再更新 2026-06-10。

但日常自动化仍应保留 `pending_source_update` 分类，因为 15:30 附近 BaoStock 可能尚未完全返回当天 ETF 日线。

## 11. 是否未来考虑 JQData 作为收盘数据补充

可以作为后续方案评估，但本轮未读取 JQData 账号，未调用 JQData。若未来使用，仍必须先进入 staging，经 validate / dry-run 后再并入正式数据。

## 12. L2 边界确认

- 不接券商交易 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不修改交易规则。
- 不修改仓位规则。
- 不新增模拟交易。
- 不使用未来数据生成当天信号。
- BaoStock 调用远低于 50000。
