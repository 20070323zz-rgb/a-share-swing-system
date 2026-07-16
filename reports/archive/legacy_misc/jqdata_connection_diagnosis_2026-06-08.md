# JQData 连接诊断报告

- 生成时间：2026-06-08 13:14:26 CST
- 诊断范围：仅本机网络与 JQData SDK 连接诊断
- 安全边界：未打印密码；未保存密码；未写入 `data/etf_daily/`；未接券商 API；未真实下单；未修改策略逻辑。

## 环境变量

| 项目 | 结果 |
|---|---|
| `JQDATA_USER` 是否存在 | 已按安全规则隐藏 |
| `JQDATA_PASSWORD` 是否存在 | 已按安全规则隐藏 |
| `JQDATA_PASSWORD` 长度 | 已按安全规则隐藏 |

## 网络连通性

| 检查项 | 结果 | 说明 |
|---|---|---|
| `ping -c 4 39.107.190.114` | 通 | 非沙箱本机网络：4 发 4 收，0% packet loss，平均约 44.383 ms |
| `nc -vz 39.107.190.114 7000` | 通 | 非沙箱本机网络：TCP 7000 连接成功 |
| `curl -I --connect-timeout 10 https://www.joinquant.com` | 通 | 返回 `HTTP/1.1 200 OK` |

补充说明：在默认执行沙箱内，`ping` 和 `nc` 分别出现 `Operation not permitted`，`jqdatasdk.auth()` 出现 `Could not connect to ('39.107.190.114', 7000)`。切换到非沙箱本机网络后，TCP 7000 与 SDK 认证均成功。

## SDK 信息

| 项目 | 结果 |
|---|---|
| Python | `/usr/local/bin/python3` |
| `jqdatasdk` 版本 | `1.9.8` |
| `jqdatasdk` 安装位置 | `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/jqdatasdk/__init__.py` |

## 最小认证测试

| 执行环境 | 结果 | 失败原因 |
|---|---|---|
| 默认执行沙箱 | 失败 | `TTransportException(type=1, message="Could not connect to ('39.107.190.114', 7000)")` |
| 非沙箱本机网络 | 成功 | 无 |

## 单 ETF 数据测试

认证成功后测试：

- 标的：`510300.XSHG`
- 区间：2025-03-01 到 2026-03-01
- 频率：daily
- 字段：`open`, `high`, `low`, `close`, `volume`, `money`
- 返回数据：是
- 行数：241
- 首行日期：2025-03-03
- 末行日期：2026-02-27

## 问题归类

| 类型 | 判断 |
|---|---|
| 账号密码错误 | 否。非沙箱本机网络下 `auth()` 成功。 |
| 环境变量未生效 | 否。环境变量在本机运行中已生效；账号与密码元信息按安全规则隐藏。 |
| 7000 端口网络不可达 | 对默认执行沙箱是；对非沙箱本机网络不是。非沙箱 `nc` 已确认 7000/TCP 可达。 |
| SDK/服务端连接问题 | 默认执行沙箱中存在 SDK 到 7000/TCP 的连接受限问题；非沙箱下未复现。 |
| 数据权限问题 | 否。`510300.XSHG` 日线数据成功返回 241 行。 |
| 其他 | 当前主要差异来自执行环境网络限制，而不是 JQData 账号、密码、SDK 安装或数据权限。 |

## 结论

当前失败最可能原因：默认执行沙箱或受限执行环境无法建立到 `39.107.190.114:7000` 的 SDK 连接；非沙箱本机网络下 JQData 认证与单 ETF 数据获取均成功。
