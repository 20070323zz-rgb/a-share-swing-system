"""因子有效性分析报告。

本模块只读取 model_dataset.csv 做研究分析，不参与交易信号生成。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import FACTOR_ANALYSIS_REPORT_FILE, LATEST_FACTOR_ANALYSIS_FILE, MODEL_DATASET_FILE


FACTOR_COLUMNS = ["relative_strength", "return_20d", "return_5d", "volume_ratio", "composite_score", "watch_score"]
FUTURE_RETURN_COLUMNS = ["future_5d_return", "future_10d_return", "future_20d_return", "future_60d_return"]
FUTURE_RANK_COLUMNS = ["future_5d_rank", "future_10d_rank", "future_20d_rank", "future_60d_rank"]


def write_factor_analysis_report(model_dataset_path: Path = MODEL_DATASET_FILE) -> Path:
    """生成因子有效性研究报告。"""
    lines = [
        "# 因子有效性分析报告",
        "",
        "本报告只用于研究分析。future returns 严禁参与当日 signal、ranking、composite_score 或 watch_score 计算。",
        "",
    ]
    if not model_dataset_path.exists() or model_dataset_path.stat().st_size == 0:
        lines.append("- 暂无 model_dataset.csv，无法分析。")
        return _write(lines)

    df = pd.read_csv(model_dataset_path, dtype={"code": str})
    for col in FACTOR_COLUMNS + FUTURE_RETURN_COLUMNS + FUTURE_RANK_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    valid_future_count = int(df[FUTURE_RETURN_COLUMNS].notna().any(axis=1).sum()) if all(col in df.columns for col in FUTURE_RETURN_COLUMNS) else 0
    lines += [
        "## 样本数量提示",
        f"- 总样本行数：{len(df)}",
        f"- 已有任一 future return 的样本行数：{valid_future_count}",
    ]
    if valid_future_count < 30:
        lines.append("- 样本不足，不应过度解读。")

    lines += ["", "## Pearson correlation"]
    _append_corr_table(lines, df, FACTOR_COLUMNS, FUTURE_RETURN_COLUMNS, method="pearson")

    lines += ["", "## Spearman Rank IC"]
    _append_corr_table(lines, df, FACTOR_COLUMNS, FUTURE_RANK_COLUMNS, method="spearman")

    lines += ["", "## Top-Bottom 分组收益"]
    _append_top_bottom(lines, df, "composite_score")

    lines += ["", "## watch_score Top 5 未来收益表现"]
    _append_top_only(lines, df[df.get("signal", "") == "WATCH"].copy(), "watch_score")

    lines += ["", "## 按 group 拆分表现"]
    _append_group_summary(lines, df)
    return _write(lines)


def _append_corr_table(lines: list[str], df: pd.DataFrame, factors: list[str], targets: list[str], method: str) -> None:
    lines.append("| 因子 | " + " | ".join(targets) + " |")
    lines.append("| --- | " + " | ".join(["---:"] * len(targets)) + " |")
    for factor in factors:
        values = [_corr_text(df, factor, target, method) for target in targets]
        lines.append(f"| {factor} | {' | '.join(values)} |")


def _append_top_bottom(lines: list[str], df: pd.DataFrame, score_col: str) -> None:
    if df.empty or score_col not in df.columns:
        lines.append("- 暂无可分析样本。")
        return
    ranked = df.dropna(subset=[score_col]).sort_values(score_col, ascending=False)
    groups = [("Top 5", ranked.head(5)), ("Bottom 5", ranked.tail(5))]
    _append_future_mean_table(lines, groups)


def _append_top_only(lines: list[str], df: pd.DataFrame, score_col: str) -> None:
    if df.empty or score_col not in df.columns:
        lines.append("- 暂无可分析样本。")
        return
    ranked = df.dropna(subset=[score_col]).sort_values(score_col, ascending=False)
    _append_future_mean_table(lines, [("Top 5", ranked.head(5))])


def _append_future_mean_table(lines: list[str], groups: list[tuple[str, pd.DataFrame]]) -> None:
    lines.append("| 分组 | 样本数 | 平均 future_5d | 平均 future_10d | 平均 future_20d | 平均 future_60d |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for label, part in groups:
        values = [_fmt_number(pd.to_numeric(part.get(col, pd.Series(dtype=float)), errors="coerce").mean()) for col in FUTURE_RETURN_COLUMNS]
        lines.append(f"| {label} | {len(part)} | {' | '.join(values)} |")


def _append_group_summary(lines: list[str], df: pd.DataFrame) -> None:
    if df.empty or "group" not in df.columns:
        lines.append("- 暂无 group 样本。")
        return
    lines.append("| group | 样本数 | 平均 composite_score | 平均 watch_score | 平均 future_20d | future_20d_top30 占比 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for group, group_df in df.groupby("group", dropna=False):
        top30 = pd.to_numeric(group_df.get("future_20d_top30", pd.Series(dtype=float)), errors="coerce")
        lines.append(
            f"| {group} | {len(group_df)} | {_fmt_number(group_df['composite_score'].mean())} | "
            f"{_fmt_number(group_df['watch_score'].mean())} | {_fmt_number(pd.to_numeric(group_df.get('future_20d_return', pd.Series(dtype=float)), errors='coerce').mean())} | "
            f"{_fmt_number(top30.mean())} |"
        )


def _corr_text(df: pd.DataFrame, factor: str, target: str, method: str) -> str:
    if factor not in df.columns or target not in df.columns:
        return ""
    subset = df[[factor, target]].dropna()
    if len(subset) < 3:
        return ""
    if method == "spearman":
        ranked = subset.rank(method="average")
        return _fmt_number(ranked[factor].corr(ranked[target], method="pearson"))
    return _fmt_number(subset[factor].corr(subset[target], method=method))


def _fmt_number(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.6f}".rstrip("0").rstrip(".")


def _write(lines: list[str]) -> Path:
    FACTOR_ANALYSIS_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_FACTOR_ANALYSIS_FILE.write_text(FACTOR_ANALYSIS_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return FACTOR_ANALYSIS_REPORT_FILE


def main() -> None:
    path = write_factor_analysis_report()
    print(f"已生成因子有效性报告：{path}")


if __name__ == "__main__":
    main()
