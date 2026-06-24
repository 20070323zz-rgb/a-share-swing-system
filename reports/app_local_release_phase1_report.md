# App Release Phase 1 本地正式版上线报告

生成时间：2026-06-22

## 版本

- 当前版本：v0.1.0-local
- 上线类型：本地正式版
- 当前阶段：Shadow Observation Period
- 正式模型：未改变
- 真实交易：禁用

## 本轮完成内容

1. 新增 `APP_VERSION`，统一本地版本号为 `0.1.0-local`。
2. 新增 `RELEASE_NOTES.md`，记录本地正式版功能、安全边界和下一步计划。
3. 新增 `docs/app_release_checklist.md`，作为本地上线前检查清单。
4. 新增 `docs/local_app_release_guide.md`，说明启动、关闭、查看日志和安全确认方式。
5. 增强 `scripts/run_app.sh` 和双击启动器，启动日志显示版本号。
6. 新增 `app/frontend/src/designTokens.js`，并在 CSS 中统一颜色、字体、圆角、阴影、间距和状态色。
7. 优化动态 App 首页、模拟仓、模型观察、数据中心、设置与安全页面的视觉层级。
8. 同步静态看板 `dashboard/index.html` 和 `reports/dashboard_data.json`，显示本地版本号。
9. 新增 `scripts/check_app_release.sh`，用于本地发布前 QA 检查。

## 设计原则

- Apple HIG：系统字体、克制留白、清晰状态表达。
- Material Design：卡片承载单一主题，减少信息堆叠。
- IBM Carbon dashboard：关键指标优先，风险状态清楚。
- Ant Design 数据展示：表格、标签、空状态和报告入口按使用频率组织。
- 金融科技产品原则：数字清晰、风险醒目、操作入口克制。

## 验证结果

已通过：

- Python 编译检查。
- 静态看板生成。
- React/Vite 前端正式构建。
- 发布检查脚本语法检查。
- 发布检查脚本运行。
- 双击启动器可执行权限检查。
- 禁止真实交易入口关键词检查。
- 前端硬编码密钥模式检查。
- 静态可见 NaN / undefined / null / [object Object] 检查。

## 关键安全确认

- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未读取或暴露 token / 密码 / 密钥。
- 未新增真实交易按钮。
- 未修改正式模型规则。
- 未扩池。
- 未把 shadow 模型接入正式执行层。

## 文件指纹确认

本轮发布后关键文件指纹保持：

- `data/paper_trades.csv`：`e3c43a6aee418666fb19460a7bb7ddeb846ced2220b8ab4030bda0d373666425`
- `data/paper_positions.csv`：`1ea405dc2e7bd7eaf1a98bd5b519f45fa1882c8657b66a84e083bee6654ff734`
- `src/paper_trade_engine.py`：`b51f30fc60777d6cb53ccf8bacc460d05082e55fa5b94f2d35a8bc7abddb9d2d`

## 结论

App 已从开发可用版提升到本地正式版 v0.1.0-local。当前版本适合作为本地量化研究控制台继续使用，但仍不是实盘系统，不支持真实交易，不支持公网部署，不替代人工复核。
