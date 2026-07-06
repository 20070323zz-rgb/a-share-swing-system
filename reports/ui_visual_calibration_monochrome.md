# UI Visual Calibration: Monochrome Product Dashboard

完成时间：2026-07-05  
范围：`app/frontend/`

## 视觉原则

根据用户参考图，本轮提取并应用以下原则：

- 黑白灰为主，彩色只作为状态点；
- 小字号、低字重、高信息密度；
- 细边框替代阴影；
- 小圆角；
- 不使用渐变；
- 不使用大 Hero；
- Table / List / Separator 作为主要结构；
- 状态使用小 Badge 和 dot；
- 图表和表格成为页面主视觉。

## 颜色系统变化

| 项目 | 新方向 |
|---|---|
| 背景 | `#fafafa` |
| 表面 | `#ffffff` |
| 次级表面 | `#f7f7f7` |
| 主文本 | `#111111` |
| 次级文本 | `#666666` |
| 弱文本 | `#999999` |
| 边框 | `#e8e8e8` |
| 强边框 | `#d7d7d7` |
| 主操作 | 黑色 / 白色 |
| 蓝色 | 不再作为大面积主视觉，仅保留极少量链接或辅助语义 |
| 黄色 | 只用于真实 warning 的状态点 |

深色模式同步调整为黑白灰体系。

## 字号与字重变化

- 页面标题控制在约 18px；
- App 名与导航约 12-13px；
- Section 标题约 13px；
- 正文约 12px；
- Table 约 11.5px；
- Badge 约 10.5px；
- 核心资产数字约 22px；
- 字重主要为 400 / 500，少量 600。

## 圆角与阴影变化

- Button：约 6px；
- Badge：约 5px；
- Table container：约 6px；
- 普通页面区域：尽量无圆角或 8px 以下；
- 默认移除阴影；
- 使用边框和 Separator 建立层级。

## Card 数量变化

| 页面 | 当前 Card 数量 | 说明 |
|---|---:|---|
| Home | 0 | 已改为标题、inline metrics、折线图、表格 |
| Portfolio | 约 3 | 主要来自交易复盘旧 `report-preview` 命中；资产摘要已改 inline metrics |
| Research | 0 | 状态行 + Tabs + Table |
| DataCenter | 0 | action head + description rows + Table |
| SettingsSafety | 0 | setting rows + Collapsible |

无明显 Card nesting。

## 页面变化

### Home

- 删除大 Hero；
- 删除状态卡片矩阵；
- 资产指标改为 inline metric row；
- 权益曲线成为主视觉；
- 持仓观察使用 Table；
- 保留“一键补齐 ETF 数据”；
- 保留周报 / 研究状态入口。

### Portfolio

- 删除大资产 Card；
- 顶部改为 inline metric row；
- Tabs 保留；
- 风险状态进入表格列；
- REVIEW / PROFIT / HB 使用小 Badge；
- 盈亏只给数字着色，不给整行背景。

### Research

- 保持 Phase 2 的状态行 + Tabs 结构；
- 证据成熟度使用细 Progress；
- 技术 key 弱化；
- 中文结论优先。

### DataCenter

- 顶部突出“一键补齐 ETF 数据”；
- 主按钮改为黑白主按钮；
- 状态使用 description rows；
- 覆盖 / 健康使用 Table；
- warning 只使用小 Badge。

### SettingsSafety

- 使用 setting rows；
- 无 Card 矩阵；
- Button 小型化；
- 高级任务进入 Collapsible；
- 日志使用 ScrollArea；
- path 使用小字号显示。

## 图表校准

- Sparkline 线条降低到约 1.35px；
- 主线使用深灰 / 黑；
- 网格线使用极浅灰；
- 不使用 gradient fill；
- 图表区域作为首页和模拟仓主视觉之一。

## 安全确认

| 项目 | 结果 |
|---|---|
| 是否新增业务功能 | no |
| 是否修改 API | no |
| 是否修改模型逻辑 | no |
| 是否修改正式买入规则 | no |
| 是否修改正式卖出规则 | no |
| 是否修改 `src/paper_trade_engine.py` | no |
| 是否修改 `data/paper_trades.csv` | no |
| 是否修改 `data/paper_positions.csv` | no |
| 是否接券商 API | no |
| 是否真实下单 | no |
| adjusted preview 是否接执行层 | no |
| shadow 是否接执行层 | no |

## 验证

- `npm run build`：通过；
- `dashboard/build_dashboard.py`：通过；
- `scripts/check_app_release.sh`：通过；
- 主界面中文优先；
- 一键补齐 ETF 数据入口存在；
- 未发现明显 `undefined / NaN / null / [object Object]`。

