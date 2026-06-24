# BaoStock App 一键补齐修复报告

检查时间：2026-06-16 16:00

## 问题

动态 App 中“一键补齐数据”此前使用 BaoStock 主连接模式，并设置较短等待参数：

- `request-timeout=25`
- `retries=1`
- 登录阶段缺少硬超时保护

当 BaoStock 登录或网络接收延迟较高时，任务会出现两类问题：

1. 登录阶段 25 秒左右失败，按钮显示 failed；
2. 某些连接等待可能长时间挂住，导致用户感觉“看板显示任务跑了，但数据没有真正更新”。

## 修复

已修改：

- `scripts/update_etf_data.py`
- `app/backend/safe_tasks.py`

修复内容：

1. 增加 BaoStock 登录重试参数：
   - `--login-retries`
   - `--login-retry-delay`

2. 给 BaoStock 登录加硬超时：
   - 登录超过 `--request-timeout` 会退出当前尝试并进入重试；
   - 不再无限等待。

3. App 数据按钮改为隔离请求模式：
   - `--isolated-queries`
   - 每只 ETF 使用独立子进程；
   - 单只卡住不会拖死整轮。

4. 新增数据源就绪探针：
   - `--source-ready-probe`
   - 先检查 `510300 / 159915 / 512800 / 515000 / 515220` 等锚定 ETF；
   - 如果这些 ETF 对请求日都返回空，说明 BaoStock 当日数据尚未就绪；
   - 直接快速标记 `pending_source_update`，不再全池 183 只空跑。

5. App 一键补齐完成后会刷新：
   - data coverage
   - data health
   - main reports
   - paper portfolio valuation
   - sell review
   - market state
   - portfolio exposure
   - strategy preview
   - strategy tracking
   - dashboard snapshot

## 本轮补齐结果

请求区间：

- `2026-05-26` 到 `2026-06-16`

当前 BaoStock 探针结果：

- `510300`: 返回空数据
- `159915`: 返回空数据
- `512800`: 返回空数据
- `515000`: 返回空数据
- `515220`: 返回空数据

结论：

BaoStock 当前尚未提供 `2026-06-16` ETF 日线数据。本轮没有新增数据行。

## 当前数据状态

- 最新本地 ETF 日期：`2026-06-15`
- 请求结束日期：`2026-06-16`
- 状态：`CAUTION / pending_source_update`
- 预计全池调用：`183`
- 实际探针调用：`5`
- 新增行数：`0`
- failed_count：`0`

## 安全边界

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码/token
- 不开放任意命令执行
- 本地已有行情行优先
- BaoStock API 调用控制在安全范围内
