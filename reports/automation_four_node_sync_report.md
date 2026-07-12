# 四节点自动化同步报告

- 检查时间：2026-07-10 16:29:13
- dry-run：no
- 正式 ETF 日线文件数量：183
- 权限等级：L2 联网数据权限；本轮未读取账号、未接券商、未真实下单。

## 节点脚本
| node | script | exists | purpose |
| --- | --- | --- | --- |
| open_check | scripts/run_open_check.sh | True | 开盘只读风险观察 |
| midday_check | scripts/run_midday_check.sh | True | 午盘模拟执行检查 |
| afternoon_open_check | scripts/run_afternoon_open_check.sh | True | 下午开盘复核 |
| daily_close_update | scripts/run_daily_close.sh | True | 收盘数据更新、主报告、滚动回测、看板刷新 |
| weekly_full_review | scripts/run_weekly_review.sh | True | 周度完整复盘 |
| monthly_model_review | scripts/run_monthly_model_review.sh | True | 月度模型复盘 |

## launchd plist
| label | plist | exists | scheduled |
| --- | --- | --- | --- |
| com.dayin.a-share.open-check | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.open-check.plist | True | 09:40 weekdays |
| com.dayin.a-share.midday-check | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.midday-check.plist | True | 12:40 weekdays |
| com.dayin.a-share.afternoon-open-check | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.afternoon-open-check.plist | True | 13:10 weekdays |
| com.dayin.a-share.daily-close | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.daily-close.plist | True | 15:30 weekdays |
| com.dayin.a-share.weekly-review | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.weekly-review.plist | True | 15:40 Friday |
| com.dayin.a-share.monthly-model-review | /Users/dayin/Code/a-share-swing-system/launchd/com.dayin.a-share.monthly-model-review.plist | True | 16:10 day 1 monthly |

## 报告同步状态
| report | exists | updated_at |
| --- | --- | --- |
| open_check.md | True | 2026-07-10 09:56:01 |
| midday_check.md | True | 2026-07-09 12:41:52 |
| afternoon_open_check.md | True | 2026-07-09 13:16:43 |
| daily_rolling_backtest.md | True | 2026-07-10 16:28:11 |
| weekly_full_review.md | True | 2026-07-10 16:28:25 |
| monthly_model_review.md | True | 2026-07-01 23:50:06 |
| latest_brief.md | True | 2026-07-10 16:28:13 |
| latest_paper_portfolio.md | True | 2026-07-10 16:28:13 |
| buy_signal_ranking.md | True | 2026-07-10 16:28:13 |
| dashboard_data.json | True | 2026-07-10 16:28:13 |

## 诊断结论
- 当前 launchd 调用项目内 scripts/run_*.sh 脚本。
- daily_close 使用 update_etf_data.py --all-etf --source baostock --skip-existing，覆盖扩池后正式 ETF 数据目录。
- paper_portfolio.py 已在 src/main.py 中更新模拟盘盈亏。
- dashboard/build_dashboard.py 读取 dashboard_data.json、模拟持仓、交易、ranking 与四节点报告摘要。
- backtest.py、factor_analysis.py、model_research.py 已复用为周/月复盘基础。

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存账号、密码或 token。
- 不自动交易。
- 不修改 mid_trend / short_swing 核心交易规则。
- 所有交易相关输出仅为本地模拟盘和研究报告。