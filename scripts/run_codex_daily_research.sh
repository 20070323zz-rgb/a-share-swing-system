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
logs = root / "logs"
output = reports / "codex_daily_research_prompt.md"

latest_daily = reports / "latest_daily.md"
latest_ranking = reports / "latest_ranking.md"
latest_factor_analysis = reports / "latest_factor_analysis.md"
watchlist_health = reports / "watchlist_health_report.md"
model_dataset = reports / "model_dataset.csv"
signals_file = reports / "signals.csv"
daily_log = logs / "daily_close.log"


def read_text(path: Path, fallback: str) -> str:
    if path.exists() and path.stat().st_size > 0:
        return path.read_text(encoding="utf-8")
    return fallback


def tail_lines(path: Path, count: int = 100) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "暂无日志。"
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[-count:])


daily_text = read_text(latest_daily, "暂无 latest_daily.md。")
ranking_text = read_text(latest_ranking, "暂无 latest_ranking.md。")
factor_text = read_text(latest_factor_analysis, "暂无 latest_factor_analysis.md。")
health_text = read_text(watchlist_health, "暂无 watchlist_health_report.md。")
daily_log_tail = tail_lines(daily_log, 100)

signal_counts = "暂无 signals.csv。"
strong_list = "暂无 model_dataset.csv。"
data_issues = []

if signals_file.exists() and signals_file.stat().st_size > 0:
    signals = pd.read_csv(signals_file, dtype={"code": str})
    if not signals.empty and "date" in signals.columns:
        latest_date = signals["date"].max()
        latest = signals[signals["date"] == latest_date]
        counts = latest["signal"].value_counts().to_dict()
        signal_counts = "\n".join([f"- {key}: {value}" for key, value in counts.items()])
        if "NO_DATA" in latest["signal"].values:
            missing = latest[latest["signal"] == "NO_DATA"][["code", "name", "block_reasons"]]
            data_issues = [f"- {row.code} {row.name}: {row.block_reasons}" for row in missing.itertuples()]

if model_dataset.exists() and model_dataset.stat().st_size > 0:
    model = pd.read_csv(model_dataset, dtype={"code": str})
    if not model.empty and "date" in model.columns:
        latest_date = model["date"].max()
        latest = model[model["date"] == latest_date].copy()
        for col in ["relative_strength", "volume_ratio", "close"]:
            if col in latest.columns:
                latest[col] = pd.to_numeric(latest[col], errors="coerce")
        strong = latest.sort_values(["relative_strength", "volume_ratio"], ascending=False).head(10)
        rows = []
        for row in strong.itertuples():
            rows.append(
                f"- {row.code} {row.name} [{getattr(row, 'group', '')}/{getattr(row, 'role', '')}] "
                f"signal={getattr(row, 'signal', '')}, close={getattr(row, 'close', '')}, "
                f"relative_strength={getattr(row, 'relative_strength', '')}, volume_ratio={getattr(row, 'volume_ratio', '')}"
            )
        strong_list = "\n".join(rows) if rows else "暂无强势列表。"

lines = [
    "# Codex 每日研究提示",
    "",
    "本文件由脚本生成，只用于人工交给 Codex 做研究分析。脚本不会调用 API、不会改代码、不会交易。",
    "",
    "## 今日最新信号摘要",
    daily_text,
    "",
    "## ETF 横截面强弱排名",
    ranking_text,
    "",
    "## 因子有效性分析",
    factor_text,
    "",
    "## 数据池健康情况",
    health_text,
    "",
    "## BUY / WATCH / SELL / NO_DATA 数量",
    signal_counts,
    "",
    "## 强势 ETF 初步列表",
    strong_list,
    "",
    "## 数据异常标的",
    "\n".join(data_issues) if data_issues else "- 暂无从最新 signals.csv 识别出的 NO_DATA 标的。",
    "",
    "## daily_close.log 最后 100 行",
    "```text",
    daily_log_tail,
    "```",
    "",
    "## 需要 Codex 分析的问题",
    "1. 哪些 ETF 最值得观察？",
    "2. 当前 BUY 是否可靠？",
    "3. 当前策略是否过严？",
    "4. 哪些标的数据异常？",
    "5. 是否建议调整 watchlist 或模型特征？",
    "6. 当前强势 ETF 前 10 是否集中在某些 group？",
    "7. 当前 BUY 是否集中在某些 group？",
    "8. WATCH 中最接近 BUY 的标的是哪些？",
    "9. 哪些 group 整体走强？",
    "10. 哪些数据缺失影响了排名？",
    "11. 哪些 ETF 出现双周期共振？",
    "12. 哪些 ETF 出现中期和短期冲突？",
    "13. 当前是否有 STRONG_RESONANCE / SHORT_TRIAL / RISK_ALERT？",
    "14. short_swing 是否过度交易？",
    "15. mid_trend 是否过慢？",
    "16. 是否需要调整 watchlist 或补充数据？",
    "17. 是否需要修改代码？如果需要，只写 proposal，不直接改主策略。",
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
