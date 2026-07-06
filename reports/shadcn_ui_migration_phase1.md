# shadcn/ui Migration Phase 1

完成时间：2026-07-05  
目标：建立统一 UI primitives，并渐进式迁移 Home / Portfolio。

## 技术栈

- React：18.3.1
- Vite：5.4.x
- Tailwind CSS：已新增 4.3.x
- shadcn CLI：已确认 `4.13.0`
- shadcn 配置：已新增 `app/frontend/components.json`
- alias：已新增 `@/`
- Radix：已新增 tabs / tooltip / collapsible / scroll-area / progress / slot
- lucide-react：已新增，供后续图标统一使用

## 接入方式

本轮未推倒重写 App，而是按 shadcn 本地组件模式建立 `src/components/ui/` primitives。已确认当前 shadcn CLI 为 `4.13.0`；考虑到项目是既有 JavaScript Vite App，且原来没有 Tailwind/alias，本轮没有让 CLI 批量生成并重写页面，而是采用最小、本地可控迁移：

1. 增加 Tailwind Vite 插件；
2. 增加 `components.json`；
3. 增加 `jsconfig.json` path alias；
4. 增加 `src/lib/utils.js`;
5. 增加基础 UI primitives；
6. 只迁移 Home 和 Portfolio。

## 新增组件

- `button`
- `card`
- `badge`
- `tabs`
- `table`
- `separator`
- `tooltip`
- `collapsible`
- `scroll-area`
- `progress`

## Home 迁移内容

- 由大 Hero 改为紧凑控制台布局。
- 保留“一键补齐 ETF 数据”。
- 保留“刷新研究报告”。
- 保留“打开模拟仓”。
- 保留正式模拟仓摘要、风险摘要、周报入口。
- 仅保留核心状态块，不堆叠报告卡片。

## Portfolio 迁移内容

- 使用 Radix Tabs 替代旧 segmented control。
- 持仓表迁移到统一 Table primitive。
- REVIEW / PROFIT / HB 状态使用统一 Badge。
- 盈亏数字只在数字本身使用 A 股红绿语义，不做整行大面积染色。
- 保留所有持仓、历史盈亏、交易记录和复盘内容。

## 旧组件保留

- `StatusPill.jsx`
- `SegmentedControl.jsx`
- `Section.jsx`
- `ActionButton.jsx`
- 其他页面仍依赖的旧组件

这些组件后续逐页迁移，不在本轮删除。

## 视觉方向

采用 `Compact Quant Research Workbench`：

- 字号缩小；
- 卡片圆角收敛到 12-14px；
- 阴影更轻；
- 灰阶为主；
- 低饱和蓝作为主操作色；
- 黄色只用于 warning；
- 减少毛玻璃和大面积渐变；
- 中文主界面。

## 安全确认

| 项目 | 结果 |
|---|---|
| 是否改变业务逻辑 | no |
| 是否改变 API | no |
| 是否修改交易规则 | no |
| 是否修改 `src/paper_trade_engine.py` | no |
| 是否修改 `data/paper_trades.csv` | no |
| 是否修改 `data/paper_positions.csv` | no |
| 是否接券商 API | no |
| 是否真实下单 | no |
| adjusted preview 是否接执行层 | no |
| shadow 是否接执行层 | no |
