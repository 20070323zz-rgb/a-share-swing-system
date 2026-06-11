# 东方证券 QMT / miniQMT 只读行情评估计划

资料日期：2026-06-07

本文用于更新当前项目的数据源评估方向：用户开户券商为东方证券，下一阶段重点评估东方证券 QMT / miniQMT 的只读行情能力。本文不代表已经确认当前账户可开通 QMT / miniQMT，也不代表项目会接入交易能力。

## 安全边界

本评估允许做的事情：

1. 评估东方证券 QMT / miniQMT 是否可作为 ETF 历史日线数据入口。
2. 只评估 `xtquant.xtdata` 行情模块。
3. 只尝试读取 ETF 历史日线行情。
4. 只写入 `data/staging/qmt/` 测试目录。
5. 只生成 `reports/qmt_test_report.md` 测试报告。

本评估禁止做的事情：

1. 不接交易 API。
2. 不使用 `xttrader`。
3. 不读取资金账户。
4. 不查持仓。
5. 不保存账号密码。
6. 不真实下单。
7. 不自动交易。
8. 不写入 `data/etf_daily/`。

## 候选入口

东方证券官网存在迅投 QMT 系统相关软件下载入口，因此东方证券 QMT / miniQMT 可以作为候选券商行情数据入口进入评估。

需要注意：

1. 官网或软件下载页出现 QMT 相关系统，不等于当前个人账户已经具备开通权限。
2. QMT / miniQMT 通常属于量化、机构、高净值或特定权限客户工具，实际开通条件必须以东方证券客服或客户经理确认为准。
3. 本项目只关注 QMT / miniQMT 的只读行情能力，不使用其交易、下单、撤单、资产、持仓、委托查询等能力。

## 技术评估范围

只评估：

```python
from xtquant import xtdata
```

禁止评估和禁止导入：

```python
from xtquant import xttrader
```

原因：

1. `xtdata` 是 XtQuant 中的行情数据模块，公开文档说明其提供历史和实时 K 线、分笔、财务数据、合约基础信息等行情相关能力。
2. `xtdata` 通过本机 MiniQMT 与行情服务交互，适合评估是否能获取历史 K 线。
3. `xttrader` 属于交易模块，可能涉及账户、资产、持仓、委托、下单、撤单等能力，不符合本项目边界。

## 试点标的

本阶段只验证 3 个 ETF：

| 代码 | 市场 | 用途 |
|---|---|---|
| `510300.SH` | 上海 | 宽基 ETF 代表 |
| `159915.SZ` | 深圳 | 创业板 ETF 代表 |
| `515000.SH` | 上海 | 行业 ETF 代表 |

## 试点目标

1. 获取 `2022-01-04` 到 `2026-06-03` 的 ETF 日线。
2. 周期只使用日线：`1d`。
3. 优先字段：`date,open,high,low,close,volume,amount`。
4. 输出目录：`data/staging/qmt/`。
5. 测试报告：`reports/qmt_test_report.md`。
6. 不写入正式目录：`data/etf_daily/`。
7. 不修改当前正式行情数据。
8. 不接入任何自动任务。

## 最小测试流程

第一步：用户向东方证券确认 QMT / miniQMT 权限。

第二步：用户在本机安装或开通东方证券 QMT / miniQMT 环境。

第三步：在本机项目环境中运行安全骨架脚本，不带 `--run`：

```bash
python3 scripts/test_qmt_xtdata.py
```

预期结果：

1. 脚本只尝试导入 `xtquant.xtdata`。
2. 脚本不会真实下载行情。
3. 脚本不会导入 `xttrader`。
4. 脚本会生成 `reports/qmt_test_report.md`。

第四步：确认环境安全后，由用户显式加 `--run` 执行只读行情试点：

```bash
python3 scripts/test_qmt_xtdata.py --run
```

运行后只允许产生：

```text
data/staging/qmt/510300.SH.csv
data/staging/qmt/159915.SZ.csv
data/staging/qmt/515000.SH.csv
reports/qmt_test_report.md
```

## 验收标准

试点通过的最低标准：

1. `xtquant.xtdata` 可在用户本机 Python 环境中导入。
2. 不需要导入 `xttrader`。
3. 不需要读取资金账号、资金余额或持仓。
4. 三个试点 ETF 至少有一个可以成功获取日线。
5. 返回数据覆盖目标区间内的大部分交易日。
6. CSV 字段能标准化到 `date,open,high,low,close,volume`，可选包含 `amount`。
7. 所有输出只在 `data/staging/qmt/` 和 `reports/qmt_test_report.md`。

试点不通过的情形：

1. 当前东方证券账户不能开通 QMT / miniQMT。
2. QMT / miniQMT 只能在交易模块可用后才能取行情。
3. 必须读取资金账户或持仓才能使用行情。
4. 当前环境无法使用 Python `xtquant.xtdata`。
5. ETF 历史日线无法获取，或只能获取极短窗口。
6. 只能通过 Windows 客户端使用，而用户暂时无法提供 Windows 环境。

## 用户需要向东方证券确认的问题

请向东方证券客户经理或客服确认：

1. 东方证券是否支持 QMT / miniQMT。
2. 当前账户是否可以开通 QMT / miniQMT。
3. 开通条件是什么，是否有资产、交易经验、客户等级或资金门槛。
4. 是否支持 miniQMT 极简模式。
5. 是否支持 `xtquant` / `xtdata`。
6. ETF 历史日线是否可以通过 `xtdata` 获取。
7. 是否支持 macOS；如果不支持，是否必须使用 Windows。
8. 是否可以只使用行情模块，不启用交易模块。
9. 是否能在不查询资金、不查询持仓、不启用下单权限的情况下读取行情。
10. 是否有历史行情下载频率、标的数量、时间跨度或权限限制。

## 与正式数据目录的关系

本阶段 QMT / miniQMT 输出只能停留在 staging：

```text
data/staging/qmt/
```

不得写入：

```text
data/etf_daily/
```

后续只有在以下条件全部满足后，才可以另行讨论是否建立正式导入流程：

1. 用户确认东方证券 QMT / miniQMT 权限稳定。
2. `xtdata` 能稳定获取 76 个 ETF 的历史日线。
3. 输出字段、复权方式、成交量单位、成交额单位已验证。
4. 数据健康检查通过。
5. 用户重新确认仍然只做行情，不接交易。

## 参考资料

1. 东方证券官网首页与软件下载入口：<https://www.dfzq.com.cn/>
2. 迅投 XtQuant.XtData 行情模块文档：<https://dict.thinktrader.net/nativeApi/xtdata.html>
3. QMT Python API 文档示例：<https://www.miniqmt.com/qmtapi/QMT_Python_API_Doc.html>
