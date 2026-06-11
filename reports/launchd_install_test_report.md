# launchd 安装与测试报告

- 检查时间：2026-06-10 12:38:10 CST
- 权限等级：L2 联网数据权限
- 项目目录：`/Users/dayin/Code/a-share-swing-system`
- launchd domain：`gui/501`

## 1. 安装/卸载/测试脚本

| 用途 | 路径 | 结果 |
| --- | --- | --- |
| 安装 launchd jobs | `scripts/install_launchd_jobs.sh` | 已执行成功 |
| 卸载 launchd jobs | `scripts/uninstall_launchd_jobs.sh` | 已执行成功 |
| 本地计划任务测试 | `scripts/test_scheduled_jobs.sh` | 已执行成功；daily_close 使用本次 shell 会话内 dry-run safe override |

说明：`scripts/test_scheduled_jobs.sh` 默认会调用 `scripts/run_daily_close.sh`，而该脚本会执行 BaoStock 增量更新。本轮为满足 dry-run/safe mode 边界，测试时仅在当前 shell 会话中接管 daily_close 分支：`update_etf_data.py` 使用 `--dry-run`，其余报告、滚动回测、同步报告和 dashboard 刷新照常执行。未修改测试脚本或 launchd 运行时间。

## 2. 已加载的 launchd job

`launchctl list | grep 'com.dayin.a-share'` 显示 6 个 job 已加载：

| label | loaded | last exit |
| --- | --- | --- |
| `com.dayin.a-share.open-check` | yes | 0 |
| `com.dayin.a-share.midday-check` | yes | 0 |
| `com.dayin.a-share.afternoon-open-check` | yes | 0 |
| `com.dayin.a-share.daily-close` | yes | 0 |
| `com.dayin.a-share.weekly-review` | yes | 0 |
| `com.dayin.a-share.monthly-model-review` | yes | 0 |

`launchctl print gui/501/<label>` 显示安装后状态均为 `state = not running`、`runs = 0`，属于刚 bootstrap 后等待日历触发的正常状态。

## 3. 每个 job 的运行时间与脚本

| job | 运行时间 | 对应脚本 | stdout | stderr |
| --- | --- | --- | --- | --- |
| `com.dayin.a-share.open-check` | 周一至周五 09:40 | `scripts/run_open_check.sh` | `logs/launchd_open_check.out.log` | `logs/launchd_open_check.err.log` |
| `com.dayin.a-share.midday-check` | 周一至周五 12:40 | `scripts/run_midday_check.sh` | `logs/launchd_midday_check.out.log` | `logs/launchd_midday_check.err.log` |
| `com.dayin.a-share.afternoon-open-check` | 周一至周五 13:10 | `scripts/run_afternoon_open_check.sh` | `logs/launchd_afternoon_open_check.out.log` | `logs/launchd_afternoon_open_check.err.log` |
| `com.dayin.a-share.daily-close` | 周一至周五 15:30 | `scripts/run_daily_close.sh` | `logs/launchd_daily_close.out.log` | `logs/launchd_daily_close.err.log` |
| `com.dayin.a-share.weekly-review` | 周五 15:40 | `scripts/run_weekly_review.sh` | `logs/launchd_weekly_review.out.log` | `logs/launchd_weekly_review.err.log` |
| `com.dayin.a-share.monthly-model-review` | 每月 1 日 16:10 | `scripts/run_monthly_model_review.sh` | `logs/launchd_monthly_model_review.out.log` | `logs/launchd_monthly_model_review.err.log` |

本轮未改变任何 plist 的 `StartCalendarInterval`。

## 4. 手动/测试结果

| 节点 | 测试方式 | 结果 | 最新日志 |
| --- | --- | --- | --- |
| open_check | `scripts/test_scheduled_jobs.sh` 调用 `scripts/run_open_check.sh` | success | `logs/open_check.log`，2026-06-10 12:36:38 |
| midday_check | `scripts/test_scheduled_jobs.sh` 调用 `scripts/run_midday_check.sh` | success | `logs/midday_check.log`，2026-06-10 12:36:39 |
| afternoon_open_check | `scripts/test_scheduled_jobs.sh` 调用 `scripts/run_afternoon_open_check.sh` | success | `logs/afternoon_open_check.log`，2026-06-10 12:36:40 |
| daily_close | safe override：`update_etf_data.py --dry-run` + 本地报告/滚动回测/sync/dashboard | success | `logs/daily_close.log`，2026-06-10 12:36:43 |
| weekly_review | `scripts/test_scheduled_jobs.sh` 调用 `scripts/run_weekly_review.sh` | success | `logs/weekly_review.log`，2026-06-10 12:36:55 |
| monthly_model_review | `scripts/test_scheduled_jobs.sh` 调用 `scripts/run_monthly_model_review.sh` | success | `logs/monthly_model_review.log`，2026-06-10 12:36:56 |

daily_close dry-run 结果：`ETF 数据下载 dry-run 完成：计划调用 183 次，标的 183 个。` 本轮未触发 BaoStock 真实下载，也未写入 ETF 日线 CSV。

## 5. 最近日志路径

| 类型 | 路径 | 状态 |
| --- | --- | --- |
| 节点日志 | `logs/open_check.log` | 本轮新增成功记录 |
| 节点日志 | `logs/midday_check.log` | 本轮新增成功记录 |
| 节点日志 | `logs/afternoon_open_check.log` | 本轮新增成功记录 |
| 节点日志 | `logs/daily_close.log` | 本轮新增 safe test 成功记录 |
| 节点日志 | `logs/weekly_review.log` | 本轮新增成功记录 |
| 节点日志 | `logs/monthly_model_review.log` | 本轮新增成功记录 |
| launchd stdout/stderr | `logs/launchd_daily_close.out.log` / `logs/launchd_daily_close.err.log` | 存在，未见本轮新增内容 |
| launchd stdout/stderr | `logs/launchd_open_check.out.log` / `logs/launchd_open_check.err.log` | 存在；stderr 为 2026-06-08 历史内容 |
| launchd stdout/stderr | `logs/launchd_weekly_review.out.log` / `logs/launchd_weekly_review.err.log` | 存在，未见本轮新增内容 |
| launchd stdout/stderr | `logs/launchd_midday_check.*.log` | 尚未由 launchd 正式触发生成 |
| launchd stdout/stderr | `logs/launchd_afternoon_open_check.*.log` | 尚未由 launchd 正式触发生成 |
| launchd stdout/stderr | `logs/launchd_monthly_model_review.*.log` | 尚未由 launchd 正式触发生成 |

## 6. 报告与 dashboard 检查

| 检查项 | 结果 |
| --- | --- |
| `reports/automation_four_node_sync_report.md` | 已更新到 2026-06-10 12:36:56；6 个节点脚本存在；6 个 launchd plist 存在；运行时间记录正确 |
| `reports/dashboard_data.json` | JSON 语法有效；生成时间 2026-06-10 12:36:56；最新数据日 2026-06-09 |
| `dashboard/index.html` | 已更新；包含与 `dashboard_data.json` 一致的生成时间和最新数据日 |

实现说明：`dashboard/build_dashboard.py` 会生成 `reports/dashboard_data.json`，并把同一份 snapshot 渲染进 `dashboard/index.html`。当前 `dashboard/index.html` 是可直接打开的静态 HTML，不在浏览器运行时 fetch JSON；页面中列出 `reports/dashboard_data.json` 作为看板快照路径。

## 7. 是否有报错

- 安装/卸载：无报错。
- plist 校验：6 个 plist 均 `OK`。
- shell 语法检查：通过。
- 本地计划任务测试：6 个节点均 success。
- 本轮 launchd stdout/stderr：未生成新的错误输出。
- 注意：`logs/launchd_open_check.err.log` 存在 2026-06-08 的历史 stderr 内容，不是本轮安装/测试产生的新错误。

## 8. L2 权限边界

本轮保持 L2 联网数据权限边界：

- 未接券商 API。
- 未真实下单。
- 未读取真实账号、密码、验证码或 token。
- 未写入真实交易。
- daily_close 使用 dry-run/safe mode，未触发真实 BaoStock 下载和 ETF CSV 写入。
- 交易相关输出仍限于本地模拟盘 CSV、报告、回测和 dashboard。

## 9. 后续查看 launchd 是否运行

查看 6 个 job 是否已加载：

```bash
launchctl list | grep 'com.dayin.a-share'
```

查看单个 job 详细状态、运行次数、最后退出码和触发日历：

```bash
launchctl print gui/$(id -u)/com.dayin.a-share.open-check
launchctl print gui/$(id -u)/com.dayin.a-share.midday-check
launchctl print gui/$(id -u)/com.dayin.a-share.afternoon-open-check
launchctl print gui/$(id -u)/com.dayin.a-share.daily-close
launchctl print gui/$(id -u)/com.dayin.a-share.weekly-review
launchctl print gui/$(id -u)/com.dayin.a-share.monthly-model-review
```

查看业务日志：

```bash
tail -n 80 logs/open_check.log
tail -n 80 logs/midday_check.log
tail -n 80 logs/afternoon_open_check.log
tail -n 80 logs/daily_close.log
tail -n 80 logs/weekly_review.log
tail -n 80 logs/monthly_model_review.log
```

查看 launchd stdout/stderr：

```bash
tail -n 80 logs/launchd_open_check.err.log
tail -n 80 logs/launchd_midday_check.err.log
tail -n 80 logs/launchd_afternoon_open_check.err.log
tail -n 80 logs/launchd_daily_close.err.log
tail -n 80 logs/launchd_weekly_review.err.log
tail -n 80 logs/launchd_monthly_model_review.err.log
```
