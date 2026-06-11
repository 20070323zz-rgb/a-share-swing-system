#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/.venv/bin/activate"

python3 - <<'PY'
from pathlib import Path
import pandas as pd

root = Path("/Users/dayin/Code/a-share-swing-system")
reports = root / "reports"
output = reports / "codex_weekly_research_prompt.md"

latest_weekly = reports / "latest_weekly.md"
latest_ranking = reports / "latest_ranking.md"
latest_factor_analysis = reports / "latest_factor_analysis.md"
model_dataset = reports / "model_dataset.csv"
backtest_summary = reports / "backtest_summary.md"


def read_text(path: Path, fallback: str) -> str:
    if path.exists() and path.stat().st_size > 0:
        return path.read_text(encoding="utf-8")
    return fallback


weekly_text = read_text(latest_weekly, "暂无 latest_weekly.md。")
ranking_text = read_text(latest_ranking, "暂无 latest_ranking.md。")
factor_text = read_text(latest_factor_analysis, "暂无 latest_factor_analysis.md。")
backtest_text = read_text(backtest_summary, "暂无 backtest_summary.md。")

dataset_summary = "暂无 model_dataset.csv。"
if model_dataset.exists() and model_dataset.stat().st_size > 0:
    df = pd.read_csv(model_dataset, dtype={"code": str})
    if not df.empty and "date" in df.columns:
        latest_date = df["date"].max()
        latest = df[df["date"] == latest_date]
        group_counts = latest.groupby(["group", "signal"]).size().reset_index(name="count") if {"group", "signal"}.issubset(latest.columns) else pd.DataFrame()
        lines = [f"- 最新模型数据日期：{latest_date}", f"- 最新截面样本数：{len(latest)}"]
        if not group_counts.empty:
            lines.append("- 分组信号数量：")
            for row in group_counts.itertuples():
                lines.append(f"  - {row.group} / {row.signal}: {row.count}")
        dataset_summary = "\n".join(lines)

lines = [
    "# Codex 每周研究提示",
    "",
    "本文件由脚本生成，只用于人工交给 Codex 做研究分析。脚本不会调用 API、不会改代码、不会交易。",
    "",
    "## 最新周复盘",
    weekly_text,
    "",
    "## ETF 横截面强弱排名",
    ranking_text,
    "",
    "## 因子有效性分析",
    factor_text,
    "",
    "## 模型数据集摘要",
    dataset_summary,
    "",
    "## 最近回测摘要",
    backtest_text,
    "",
    "## 需要 Codex 分析的问题",
    "1. 本周策略执行是否稳定？",
    "2. 哪些 ETF 应该进入下周重点观察？",
    "3. 哪些分组信号偏强或偏弱？",
    "4. 本周强弱变化是否集中在某些 group？",
    "5. WATCH 中最接近 BUY 的标的下周是否值得重点看？",
    "6. 当前策略是否过严或过松？",
    "7. 是否建议调整 watchlist、补充数据或优化模型特征？",
    "8. 如果需要修改代码，只写 proposal，不直接改主策略。",
    "",
    "## 安全边界",
    "- 不接券商 API。",
    "- 不真实下单。",
    "- 不读取账号、密码、验证码或 token。",
    "- 不自动交易。",
]

output.write_text("\n".join(lines), encoding="utf-8")
print(f"已生成 {output}")
PY
