# shadcn/ui Compatibility Audit

检查时间：2026-07-05
范围：`app/frontend/`

## 结论

`compatible_with_changes`

当前 App 是 React 18 + Vite 5，适合渐进式接入 shadcn/ui 的本地组件结构；但接入前缺少 Tailwind、`components.json`、`@/` alias、Radix 基础依赖和统一 UI primitives，因此不是开箱即用兼容。

## 当前技术栈

| 项目 | 状态 |
|---|---|
| React | 18.3.1 |
| Vite | 5.4.x |
| Tailwind CSS | 已新增 4.3.x |
| shadcn components.json | 已新增 |
| path alias `@/` | 已新增 |
| lucide-react | 已新增 |
| Radix UI | 已新增 tabs / tooltip / collapsible / scroll-area / progress / slot |
| CSS 架构 | 仍以 `src/styles.css` 为主，新增 compact workbench tokens |
| TypeScript | 未使用，继续保持 JavaScript 项目 |

## 兼容性说明

- 兼容：React/Vite 架构适合 shadcn/ui 的本地组件模式。
- 需要调整：原项目无 Tailwind 和 alias，已按最小范围补齐。
- 不建议的做法：不建议一次性运行大范围 UI 重写或升级整套前端依赖。
- 本轮采用：本地 shadcn 风格 primitives + Radix 基础组件 + 保留现有业务页面逻辑。

## 当前自定义组件

- `ActionButton.jsx`
- `DataHealthPanel.jsx`
- `LogsPanel.jsx`
- `PortfolioPanel.jsx`
- `ReportCard.jsx`
- `Section.jsx`
- `SegmentedControl.jsx`
- `SignalsPanel.jsx`
- `Sparkline.jsx`
- `StatusCard.jsx`
- `StatusPill.jsx`
- `TaskPanel.jsx`
- `Timeline.jsx`

## 新增 UI primitives

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

## 设计方向

采用 `Compact Quant Research Workbench`：

- 紧凑；
- 专业；
- 灰阶为主；
- 低饱和蓝点缀；
- 黄色只用于真正 warning；
- 小圆角；
- 小字号；
- 中文主界面。

## 安全边界

本次审计和接入不涉及交易、行情下载、模型、持仓和 API 业务逻辑。
