# App 一键补齐数据按钮修复报告

检查时间：2026-06-18 20:45

## 结论

- App 端“一键补齐数据”按钮存在任务反馈和运行环境问题。
- 已修复：白名单任务固定使用项目 `.venv/bin/python`，不再依赖启动 App 时的外部 Python 环境。
- 已修复：任务启动后立即写入 latest log，前端会显示“任务已启动”。
- 已修复：补齐任务会读取 `reports/data_update_status.json`，如果数据源未发布或无新增，会显示 `warning`，不再伪装成绿色成功。
- 已补齐 2026-06-18 数据：183 个 ETF 全部更新到 2026-06-18，新增 183 行。

## 原因

旧逻辑中 `app/backend/safe_tasks.py` 使用 `sys.executable` 作为任务 Python。  
当 App 或测试入口不是通过项目 `.venv` 启动时，补齐任务会调用系统 Python，导致任务很快退出，看起来像“按钮没有运行”。

另一个体验问题是：旧任务面板只显示 stderr，不显示 stdout 和数据更新摘要。  
当数据源未发布、无新增行或快速结束时，用户无法从页面直接判断任务到底是否启动、是否真的补齐。

## 修复内容

1. `app/backend/safe_tasks.py`
   - 固定任务 Python 为 `PROJECT_ROOT/.venv/bin/python`。
   - 如果 `.venv/bin/python` 不存在，才 fallback 到当前解释器。

2. `app/backend/task_runner.py`
   - 任务进入队列后立即写入 `logs/app_tasks/latest.log`。
   - 数据更新类任务读取 `reports/data_update_status.json`。
   - 当数据源未发布、无新增且仍 stale 时，App 任务状态显示 `warning`。
   - 当数据更新成功时，也记录 `data_update_status / latest_local_date / added_rows`。

3. `app/frontend/src/App.jsx`
   - 点击按钮后立即显示“任务已启动”反馈。

4. `app/frontend/src/components/TaskPanel.jsx`
   - 展示 stdout、warning、数据更新摘要。

5. `app/frontend/src/styles.css` 和 `app/frontend/src/pages/Logs.jsx`
   - 增加 warning 状态样式。

## 本轮补齐结果

- 数据源：BaoStock
- 请求结束日：2026-06-18
- ETF 文件数：183
- 成功更新 ETF：183
- 新增行数：183
- 最新本地数据日：2026-06-18
- failed：0
- pending：0
- BaoStock API calls：183
- 重复日期规则：本地原行优先

## 已重新生成

- `reports/data_update_status.json`
- `reports/data_source_status.json`
- `reports/data_download_report.md`
- `reports/data_update_log.md`
- `reports/latest_data_coverage.md`
- `reports/latest_data_health.md`
- `reports/latest_brief.md`
- `reports/buy_signal_ranking.md`
- `reports/latest_paper_portfolio.md`
- `reports/sell_signal_review.md`
- `reports/model_research_report.md`
- `reports/dashboard_data.json`
- `dashboard/index.html`
- `app/frontend/dist/`

## 安全边界

- 不接券商 API：yes
- 不真实下单：yes
- 不读取真实账户：yes
- 不保存账号密码/token：yes
- 不运行真实交易按钮：yes
- 仅更新本地行情、报告和只读看板：yes
