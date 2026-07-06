# Recommended Project Layout

> 这是保守目标结构建议。本轮不迁移，只用于后续规划。

```text
a-share-swing-system/
  app/
  assets/
  dashboard/
  data/
    etf_daily/
    raw/
    derived/
    paper/
    staging/
  docs/
    user_guides/
    technical/
    rules/
  reports/
    latest/
    weekly/
    audit/
    research/
    preview/
    shadow/
    archive/
  scripts/
    runtime/
    maintenance/
    data/
    app/
  src/
    core/
    data/
    portfolio/
    research/
    preview/
    risk/
    reporting/
    app_support/
  dist/
  logs/
```

## 迁移成本评估

- `reports/` 分类成本最高：dashboard/App/周报都读取固定路径，必须先建立兼容层或 symlink/索引。
- `src/` 子包化成本高：大量脚本以 `python3 src/xxx.py` 方式运行。
- `scripts/` 子目录化成本中等：launchd、App safe task、README 都可能引用固定脚本名。
- `data/` 拆分成本中等偏高：核心账本和 ETF 日线不能动；派生文件可后续整理。
- `docs/` 整理成本低：主要是链接同步。

## 最低风险第一阶段

1. 保持所有核心入口原路径。
2. 新增索引文档和报告地图。
3. 在 `reports/` 中先标记归档候选，不移动 latest/current 报告。
4. 后续若移动，先让 dashboard/App 通过配置读取路径。
