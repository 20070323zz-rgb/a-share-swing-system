# QMT / miniQMT xtdata 只读行情测试报告

- 生成时间：2026-06-07 23:44:02
- 是否显式执行真实下载：否
- xtquant.xtdata 导入：失败
- 测试区间：2022-01-04 到 2026-06-03
- 输出目录：`data/staging/qmt`
- 安全边界：未导入 xttrader；不连接交易账户；不读取账号密码；不查资金；不查持仓；不下单；不写入 data/etf_daily/。

## 导入错误

```text
No module named 'xtquant'
```

## 标的结果

| symbol | status | rows | start_date | end_date | output_path | message |
|---|---:|---:|---|---|---|---|
| 510300.SH | import_failed | 0 |  |  | `` | No module named 'xtquant' |
| 159915.SZ | import_failed | 0 |  |  | `` | No module named 'xtquant' |
| 515000.SH | import_failed | 0 |  |  | `` | No module named 'xtquant' |

## 下一步

1. 如需真实验证 QMT 历史日线，请在已开通 QMT / miniQMT 且确认只读行情边界后运行 `python3 scripts/test_qmt_xtdata.py --run`。
