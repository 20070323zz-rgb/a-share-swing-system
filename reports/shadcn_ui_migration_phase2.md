# shadcn/ui Migration Phase 2

完成时间：2026-07-05
目标：完成剩余一级页面渐进式迁移，统一为紧凑型量化研究工作台。

## 迁移页面与组件

| 文件 | 迁移内容 |
|---|---|
| `app/frontend/src/pages/Research.jsx` | 取消大 Hero 与 Card 矩阵，改为 summary row + Tabs + Table + Progress + 文档列表 |
| `app/frontend/src/pages/DataCenter.jsx` | 顶部突出“一键补齐 ETF 数据”，主体改为数据状态 / 数据覆盖 / 数据健康 / 报告 Tabs |
| `app/frontend/src/pages/SettingsSafety.jsx` | 从后台式卡片矩阵改为设置页：setting rows、Collapsible、Table、ScrollArea |
| `app/frontend/src/components/TaskPanel.jsx` | 从按钮墙改为紧凑 action list；安全说明只保留一次 |
| `app/frontend/src/components/ReportCard.jsx` | 从大报告卡片改为文档列表 item，查看内容折叠显示 |
| `app/frontend/src/components/DataHealthPanel.jsx` | 从数据源卡片改为数据源表格和简洁摘要 |

## Research 如何减负

- 主界面只回答：正式模型是否改变、shadow 是否成熟、当前观察重点。
- 使用 `Tabs` 拆分：影子模型、证据成熟度、错失机会、研究报告。
- 影子模型和错失机会使用 `Table`。
- 成熟度使用 `Progress`。
- 报告使用文档列表，不再一个报告一个大卡片。

## DataCenter 如何突出一键补齐数据

- 顶部 action bar 直接展示“一键补齐 ETF 数据”按钮。
- 说明明确：更新本地行情数据，不会交易，不连接券商。
- 其他信息进入 Tabs，避免巨大 Hero 和卡片堆叠。

## SettingsSafety 如何变为设置页

- 系统安全使用 setting rows：真实交易、券商接口、真实账户读取、Shadow 执行等。
- App 启动使用路径、地址、日志、环境检查等设置行。
- 高级诊断进入 Collapsible。
- 日志使用 Collapsible + ScrollArea。

## TaskPanel 改造

- 常用任务只显示：一键补齐 ETF 数据、刷新研究报告、刷新模拟仓绩效。
- 每个任务是 action row，不再是按钮墙。
- 高级任务默认折叠。
- 内部 task key 仅作为小字显示。

## ReportCard 改造

- 改为文档列表 item。
- 中文标题优先，文件名弱化。
- 摘要最多两行。
- 查看按钮小型化。
- 详细内容折叠并限制高度。

## Card 数量变化

详见 `reports/shadcn_card_density_audit.md`。

- Research：0 个 Card 根节点；
- DataCenter：0 个 Card 根节点；
- SettingsSafety：0 个 Card 根节点；
- 未发现明显 Card nesting。

## 中文统一情况

- 页面主标题、Tabs、Buttons、主状态均为中文。
- 技术 key 只作为小字或文件名保留。
- 主界面不展示大段英文设计名。

## CSS 清理情况

详见 `reports/frontend_css_cleanup_audit.md`。

已删除低风险旧样式：

- `.status-pill`
- `.segmented-control`

仍保留高风险或仍被引用样式：

- `.metric-card`
- `.report-preview`
- `.table-wrap`
- `.apple-hero`

## 安全确认

| 项目 | 结果 |
|---|---|
| 是否改变业务逻辑 | no |
| 是否改变 API | no |
| 是否新增业务功能 | no |
| 是否新增 safe task | no |
| 是否修改 `src/paper_trade_engine.py` | no |
| 是否修改 `data/paper_trades.csv` | no |
| 是否修改 `data/paper_positions.csv` | no |
| 是否接券商 API | no |
| 是否真实下单 | no |
| adjusted preview 是否接执行层 | no |
| shadow 是否接执行层 | no |
