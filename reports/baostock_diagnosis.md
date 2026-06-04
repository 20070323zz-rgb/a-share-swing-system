# BaoStock 诊断报告 2026-06-03

本报告只诊断免费公开行情源 BaoStock 的日线数据可用性，不包含任何券商接口、账号读取、真实下单或自动交易。

## 结论

- BaoStock Python 包已在本机 `.venv` 中安装成功。
- 系统已能按 ETF / 股票代码自动生成 BaoStock 格式代码，例如 `sh.512880`、`sz.159928`。
- 本次 7 个重点标的均已实际尝试 BaoStock。
- 本次 BaoStock 在登录阶段失败，统一表现为：`BaoStock 登录失败：网络接收错误。`
- 因 7 个标的均无本地缓存，本次没有生成新的 `data/<code>.csv`。
- 当前结论：BaoStock 架构已接入，但本机当前网络到 BaoStock 服务端仍不稳定；下一步优先使用 `raw/` 手动导入 CSV，或换网络环境后重试 BaoStock。

## 单标的结果

| 代码 | 名称 | BaoStock 格式代码 | 是否成功 | 返回行数 | 是否生成 data CSV | 是否有本地缓存 | 失败原因 |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| 510500 | 中证500ETF | sh.510500 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 588000 | 科创50ETF | sh.588000 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 512880 | 证券ETF | sh.512880 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 512800 | 银行ETF | sh.512800 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 512010 | 医药ETF | sh.512010 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 512690 | 酒ETF | sh.512690 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |
| 159928 | 消费ETF | sz.159928 | 否 | 0 | 否 | 否 | BaoStock 登录失败：网络接收错误。 |

## 行业组测试

测试命令：

```bash
python3 src/main.py --fetch-data --fetch-group 行业 --fetch-source baostock --start-date 2025-01-01 --end-date 2026-06-02 --batch-size 3 --sleep-seconds 3 --retry 1
```

结果：

- 新下载成功：0 个
- 缓存可用：0 个
- 失败：5 个
- 失败标的：`512880`、`512800`、`512010`、`512690`、`159928`
- 统一失败原因：BaoStock 登录阶段网络接收错误

## 建议

- 对 `510500`、`588000` 和行业组 5 个 ETF，短期优先从行情软件导出 CSV，放入 `raw/` 后用 `scripts/normalize_csv.py` 标准化导入。
- 不建议因为本次 BaoStock 网络失败就删除这些 ETF；如果要减少日报中的 NO_DATA 噪音，可以临时将对应标的 `enabled=0`，但需要人工确认。
- 后续可换网络环境后重试 BaoStock；如果仍失败，再评估 Tushare Pro 行情源。
