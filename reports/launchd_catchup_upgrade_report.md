# launchd catchup 自动化升级报告

- 生成时间：2026-06-11 09:17:39
- 权限等级：L2 联网数据权限。
- 本报告只说明本地自动化调度，不涉及真实交易。

## 为什么需要 catchup
- Mac 可能不在固定时间开机、登录或保持唤醒。
- 固定时间 launchd 可能错过节点。
- catchup 每 30 分钟检查一次，判断哪些节点应补跑或标记 missed。

## 当前 7 个 launchd job
| job | 触发方式 | 作用 |
| --- | --- | --- |
| open_check | 工作日 09:40 | 开盘风险观察 |
| midday_check | 工作日 12:40 | 午盘模拟执行检查 |
| afternoon_open_check | 工作日 13:10 | 下午开盘复核 |
| daily_close | 工作日 15:30 | 收盘数据更新与主报告 |
| weekly_review | 周五 15:40 | 周度完整复盘 |
| monthly_model_review | 每月 1 日 16:10 | 月度模型复盘 |
| catchup_check | RunAtLoad + 每 30 分钟 | 登录/唤醒补偿检查 |

## 固定时间 job 与 catchup job 分工
- 固定时间 job：在理想情况下按时运行节点。
- catchup job：登录/加载后和每 30 分钟检查状态，补跑仍有意义的节点。
- catchup 不重复执行已经 success 的节点。

## catchup 补偿规则
- 09:40-12:39：open_check 未成功则补跑。
- 12:40-13:09：midday_check 未成功则补跑，open_check 标记 missed。
- 13:10-15:29：afternoon_open_check 未成功则补跑；midday_check 未成功则补跑 proxy 检查。
- 15:30 后：不再补跑盘中节点；daily_close 未成功则补跑。
- 周五 15:40 后：daily_close 成功后才补跑 weekly_review。
- 每月 1 日 16:10 后：daily_close 成功后才补跑 monthly_model_review。

## automation_state.json 状态结构
```json
{
  "2026-06-10": {
    "open_check": {"status": "success", "last_run": "2026-06-10 09:40:12", "source": "launchd"},
    "daily_close": {"status": "success", "last_run": "2026-06-10 15:31:08", "source": "catchup"}
  }
}
```

## 如何避免重复执行
- 每个脚本成功或失败后写入 data/automation_state.json。
- catchup 执行前先检查当日节点是否 status=success。
- success 节点直接跳过。

## 如何避免重复下载和重复写模拟交易
- daily_close 仍使用 update_etf_data.py --skip-existing 和本地原行优先合并。
- src/main.py 的模拟买入逻辑已有同日同信号幂等检查，不重复写相同模拟买入。
- catchup 不直接写交易，只调用既有本地脚本。

## 场景示例
- 如果电脑 12:50 开机：open_check 标记 missed，补跑 midday_check。
- 如果电脑 16:00 开机：盘中节点标记 missed_after_close，补跑 daily_close；如果是周五且 daily_close 成功，再补跑 weekly_review。
- 如果电脑当天不开机：不会补跑当天盘中节点；下次开机只处理当前日期。

## 用户如何查看 catchup 是否运行
- 查看状态：python3 src/automation_scheduler.py --mode status
- 查看状态文件：data/automation_state.json
- 查看日志：logs/catchup_check.log
- 查看 launchd 日志：logs/launchd_catchup_check.out.log 和 logs/launchd_catchup_check.err.log

## 安全边界确认
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不修改交易规则或仓位规则。
- 不自动调参。
- 不把网页变成交易终端。
- 不删除 ETF 数据。
- 不把 failed/quarantine ETF 放回主流程。
- 不使用未来数据。
- 不绕过人工审查。