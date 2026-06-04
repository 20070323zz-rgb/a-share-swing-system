# 本机行情源验证记录 2026-06-03

## 核心规则

所有行情数据源可用性判断，必须以用户本机 PyCharm/.venv 环境运行结果为准。Codex 云端/沙盒环境的网络失败，只能记录为 Codex 环境限制，不能据此判定 AKShare、BaoStock、东方财富或其他数据源不可用。

## 职责分工

- Codex 负责开发、修复、生成脚本和报告逻辑。
- 用户本机负责关键行情源可用性验证。
- ChatGPT/用户根据本机运行结果决定项目方向。
- 不要用 Codex 云端网络失败否定某个数据源。

## 用户本机验证结果

- BaoStock 在用户本机 PyCharm / `.venv` 环境中可用。
- BaoStock 登录成功：`error_code = 0`，`error_msg = success`。
- BaoStock 可获取股票日线数据：`sh.600519` 可返回 `date,open,high,low,close,volume`。
- BaoStock 可获取 ETF 日线数据：`sh.512880` 可返回 `date,open,high,low,close,volume`。
- `512880` 返回数据起始日期可能晚于请求 `start-date`，例如从 2026-01-05 开始。这说明部分 ETF 在 BaoStock 的历史覆盖可能不完整，但接口本身可用。
- 用户本机已通过 BaoStock 成功补齐多个 ETF 数据。
- 行业组本机运行结果：新下载成功 5 个，缓存可用 0 个，失败 0 个。
- 后续剩余 ETF 数据也已在用户本机补齐。

## Codex 环境说明

Codex 云端/沙盒环境中 BaoStock / AKShare 可能出现连接失败、DNS 失败或服务端断开。这类结果只说明 Codex 当前网络环境受限，不代表用户本机数据源不可用。

## 安全边界

- 不接入任何真实券商 API。
- 不真实下单。
- 不读取证券账户账号密码。
- 不保存 token、验证码、交易账号等敏感信息。
- 不做融资融券、杠杆或自动交易。
- cron 只负责自动生成模拟盘报告。
- 当前所有交易均为模拟盘和学习用途。
