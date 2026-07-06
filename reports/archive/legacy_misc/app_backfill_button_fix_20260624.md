# App 一键补齐数据修复记录

检查时间：2026-06-24 00:40

## 问题结论

App 内“一键补齐 ETF 数据”不可用不是前端按钮没有点击，而是后端执行链路有三处断点：

1. `app/backend/schemas.py` 的任务请求白名单未包含 `backfill_etf_data`，导致前端提交任务时会被接口校验拒绝。
2. App 安全任务使用项目 `.venv/bin/python`，但 `.venv` 缺少 `pandas`、`numpy`、`baostock`，导致数据更新脚本启动即失败。
3. 凌晨或盘中点击补齐时，任务目标日期原来直接使用当天日期；A 股当日日线尚未发布时会显示无新增。现已改成 18:00 前默认补最近已结束交易日。

## 修复内容

- 更新 `app/backend/schemas.py`：加入 `backfill_etf_data` 及当前 App 常用白名单任务。
- 更新 `app/backend/task_runner.py`：让 `backfill_etf_data` 能正确读取 `reports/data_update_status.json` 并展示数据更新状态。
- 更新 `app/backend/safe_tasks.py`：新增最近已结束交易日判断，避免凌晨/盘中强求当天日线。
- 安装项目依赖到 `.venv`：`pandas`、`numpy`、`baostock` 等 requirements 依赖已补齐。

## 本轮补齐结果

- 触发方式：App API `/api/tasks/run`
- 任务：`backfill_etf_data`
- 目标区间：2026-06-02 至 2026-06-23
- 实际数据源：BaoStock
- ETF 文件数：183
- 新增行数：183
- 最新本地数据日：2026-06-23
- 失败数：0
- BaoStock 调用：183
- 本地原行优先：是

说明：当前自然日期为 2026-06-24 凌晨，2026-06-24 当日日线尚未发布，因此本轮正确补齐到最近已结束交易日 2026-06-23。

## 安全边界

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码或 token
- 不修改模拟交易流水
- 不修改模拟持仓
- 不修改正式交易执行逻辑
