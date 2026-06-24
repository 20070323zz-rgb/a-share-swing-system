# App 一键补齐数据入口审计

检查时间：2026-06-23

## 结论

当前项目已有 ETF 日线更新脚本 `scripts/update_etf_data.py`，也已有 App 白名单任务体系 `app/backend/safe_tasks.py`。本轮新增清晰任务名 `backfill_etf_data`，中文显示为“一键补齐 ETF 数据”，避免用户在“日更数据”“补最近缺口”等技术描述中寻找入口。

## 当前数据补齐脚本

正式补齐命令由 App 后端白名单任务固定生成，前端不能传入任意命令：

```bash
.venv/bin/python scripts/update_etf_data.py \
  --source auto \
  --primary baostock \
  --fallback jqdata \
  --all-etf \
  --skip-existing \
  --source-ready-probe \
  --max-api-calls 50000 \
  --start <最近约三周> \
  --end <当天> \
  --adjustflag 2 \
  --request-timeout 20 \
  --login-retries 2 \
  --retries 1 \
  --status-json reports/data_update_status.json
```

补齐完成后继续运行：

```bash
.venv/bin/python src/data_coverage.py
.venv/bin/python src/data_health.py
.venv/bin/python dashboard/build_dashboard.py
```

## App 安全任务状态

- 是否已有数据补齐脚本：是，`scripts/update_etf_data.py`
- 是否已有 safe task：已有 `backfill_recent_data`，本轮新增更清晰的 `backfill_etf_data`
- 数据源：`auto`，日常主线以 BaoStock 为主，JQData 仅作为配置中的 fallback，不读取前端密钥
- 是否只更新本地 ETF 日线数据：是
- 是否接券商：否
- 是否真实交易：否
- 是否修改交易流水：否
- 是否修改模拟持仓：否

## 推荐按钮文案

主按钮：

> 一键补齐 ETF 数据

副文案：

> 更新本地行情数据，不会交易

数据中心说明：

> 只更新本地研究数据，不会交易，不会连接券商。

## 安全边界

`backfill_etf_data` 是后端白名单任务。前端只能提交任务名，不能提交命令、路径、账号、密码、交易方向或交易数量。任务环境会强制设置：

```text
REAL_TRADE_ENABLED=0
BROKER_API_ENABLED=0
```

因此该按钮只用于本地研究数据维护，不属于交易功能。
