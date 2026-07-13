# shadcn Card Density Audit

检查时间：2026-07-05
范围：App 一级页面与本轮迁移组件

## 结论

Phase 2 已明显降低剩余一级页面的 Card 密度。Research、DataCenter、SettingsSafety 不再使用 Card 矩阵；页面主要使用 summary row、description list、Table、Tabs、Badge、Collapsible 和 ScrollArea。

## Card 数量估算

| 页面 | 当前 Card 数量 | 说明 |
|---|---:|---|
| Home | 约 11 | Phase 1 保留：控制台、权益摘要、9 个核心状态块 |
| Portfolio | 约 13 | Phase 1 保留：页头与概览指标；本轮未重写 |
| Research | 0 | 已迁移为 summary rows、Tabs、Table、文档列表 |
| DataCenter | 0 | 已迁移为 action bar、Tabs、description list、Table |
| SettingsSafety | 0 | 已迁移为 setting rows、Collapsible、Table |

## Card nesting

未发现明显 Card inside Card。Phase 2 新增区域不使用嵌套 Card。

## 为什么保留 Home / Portfolio Card

- Home 的 Card 用于核心状态摘要和入口，不是一个报告一个 Card。
- Portfolio 的 Card 用于账户摘要和绩效指标，是第一阶段已验证页面。
- 本轮任务明确不重写 Home / Portfolio，除非做极小一致性修复。

## 后续建议

1. 下一轮可单独迁移 Portfolio 交易复盘的旧 `details.report-preview`。
2. `ControlRoom.jsx` 如果重新纳入导航，应另开一轮迁移。
3. Card 应继续只用于核心资产、账户摘要和高层状态，不用于一条状态一个卡片。
