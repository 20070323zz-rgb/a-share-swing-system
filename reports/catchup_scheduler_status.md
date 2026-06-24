# Catchup Scheduler Status

- 检查时间：2026-06-24 23:01:05
- dry-run：no
- 交易日判断：yes
- 安全边界：只运行本地数据/报告/模拟盘脚本，不接券商 API，不真实下单。

## 本次计划/执行
| node | action | status | reason |
| --- | --- | --- | --- |
| scheduler | noop | success | all_due_nodes_success |

## 今日状态
| node | status | last_run | source | note/error |
| --- | --- | --- | --- | --- |
| open_check | success | 2026-06-24 09:54:32 | launchd |  |
| midday_check | success | 2026-06-24 12:55:24 | launchd |  |
| afternoon_open_check | success | 2026-06-24 13:14:00 | launchd |  |
| daily_close | success | 2026-06-24 15:44:58 | launchd | success with warning |
| weekly_review | pending |  |  |  |
| monthly_model_review | pending |  |  |  |