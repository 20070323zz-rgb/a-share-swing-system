# 本地正式版上线检查清单

版本：v0.2.0-local

## 启动检查

- [ ] `APP_VERSION` 存在。
- [ ] `RELEASE_NOTES.md` 存在。
- [ ] 双击 `打开量化研究控制台.command` 可启动。
- [ ] 双击 `A-Share Swing App.command` 可启动。
- [ ] 浏览器自动打开 `http://127.0.0.1:8000`。
- [ ] `logs/app_server.log` 可查看。

## 页面检查

- [ ] 首页可访问。
- [ ] 模拟仓可访问。
- [ ] 模型观察可访问。
- [ ] 数据中心可访问。
- [ ] 设置与安全可访问。
- [ ] 页面没有 `NaN`、`undefined`、`null`、`[object Object]`。
- [ ] 页面中文为主，英文只作为必要说明。

## 安全检查

- [ ] 没有真实交易按钮。
- [ ] 没有 broker login / place order / live trading 入口。
- [ ] 没有展示 token / 密码 / 密钥。
- [ ] 白名单任务均为研究任务，不会真实交易。
- [ ] `paper_trade_engine.py` 未被本轮改动。
- [ ] `paper_trades.csv` 未被破坏。
- [ ] `paper_positions.csv` 未被破坏。

## 构建检查

- [ ] `python3 -m py_compile dashboard/build_dashboard.py app/backend/readers.py app/backend/main.py app/backend/safe_tasks.py` 通过。
- [ ] `python3 dashboard/build_dashboard.py` 通过。
- [ ] `cd app/frontend && npm run build` 通过。
- [ ] `bash scripts/check_app_release.sh` 通过。

## 结论

本地正式版上线只代表本地 App 可稳定使用，不代表策略成熟，不代表可以实盘。
