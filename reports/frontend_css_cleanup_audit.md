# Frontend CSS Cleanup Audit

检查时间：2026-07-05  
范围：`app/frontend/src/styles.css`

## 结论

本轮只新增 compact workbench token 和 shadcn-style primitive class，不大规模删除旧 CSS。原因是多个页面仍依赖旧 class，贸然删除会影响 Data Center、Research、Settings Safety 等未迁移页面。

## 已收敛方向

- 新增统一字体栈：`-apple-system`, `SF Pro Text`, `PingFang SC`, `Helvetica Neue`, `Arial`, `sans-serif`。
- 新增统一灰阶、低饱和蓝、success / warning / danger 颜色语义。
- 新增 `ui-*` primitive class：button、card、badge、tabs、table、separator、tooltip、scroll-area、progress。
- Home / Portfolio 使用 `workbench-*` 紧凑布局。

## Legacy CSS 候选

以下 class 仍保留，本轮不删除：

| 候选 | 原因 |
|---|---|
| `.apple-hero` | 其他页面仍使用 |
| `.hero-orb-card` | 其他页面仍使用 |
| `.segmented-control` | 旧组件仍存在，其他页面可能复用 |
| `.quick-action` | Data Center 仍有入口使用 |
| `.table-wrap` | Logs、Settings、Signals 等页面仍使用 |
| `.status-pill` / `.badge` | 旧组件和非迁移页面仍使用 |
| 大量 `.research-*` | Research 页面暂未迁移 |
| `.source-*` / `.task-*` | Data Center / Settings 仍使用 |

## 后续建议

1. 第二阶段迁移 Data Center 和 Settings Safety。
2. 第三阶段迁移 Research 页面。
3. 全部页面完成后，再删除 `.apple-hero`、`.segmented-control`、`.quick-action` 等旧 class。
4. 删除前先用构建和页面截图检查，不做批量盲删。

## Phase 2 Update

更新时间：2026-07-05

### removed

| CSS | 原因 |
|---|---|
| `.status-pill` 及 tone 样式 | 一级页面已迁移到 `Badge`，当前只剩未引用旧组件文件 |
| `.segmented-control` 及 active 样式 | 一级页面已迁移到 Radix `Tabs`，当前只剩未引用旧组件文件 |

### still_used

| CSS | 仍保留原因 |
|---|---|
| `.metric-card` | `ControlRoom.jsx` 仍使用，且不在本轮一级页面范围 |
| `.report-preview-grid` / `.report-preview` | `Portfolio.jsx` 交易复盘详情仍使用，后续可单独迁移 |
| `.table-wrap` | 旧页面和日志类区域仍可能使用 |
| `.quick-action` | 样式暂保留，后续确认无引用后再删除 |
| `.apple-hero` | 部分非一级或历史页面样式仍可能依赖，暂不高风险删除 |

### legacy_candidate

- `StatusPill.jsx`
- `SegmentedControl.jsx`
- `ActionButton.jsx`

这些组件已不被当前一级页面引用，但本轮不删除组件文件，便于回滚和避免潜在隐藏引用。

### deferred

- `ControlRoom.jsx` 不是当前 App 一级导航页面，本轮不迁移。
- `Portfolio.jsx` 内交易复盘的旧 `details.report-preview` 保留，避免影响第一阶段已验证页面。
- 大规模 CSS 清理延后到所有页面和历史入口都完成迁移后。
