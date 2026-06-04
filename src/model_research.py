"""模型研究骨架。

只读取 model_dataset.csv 做离线研究，不参与实时信号、不连接券商、不下单。
"""

from __future__ import annotations

import pandas as pd

from config import LATEST_MODEL_RESEARCH_FILE, MODEL_DATASET_FILE, MODEL_RESEARCH_REPORT_FILE


FEATURE_COLUMNS = [
    "relative_strength",
    "return_20d",
    "return_5d",
    "volume_ratio",
    "composite_score",
    "watch_score",
]
TARGET_COLUMN = "future_20d_top30"


def write_model_research_report() -> None:
    lines = [
        "# 模型研究报告",
        "",
        "本报告只用于离线模型研究，不生成交易指令，不接券商 API，不下单。",
        "",
    ]
    if not MODEL_DATASET_FILE.exists() or MODEL_DATASET_FILE.stat().st_size == 0:
        lines.append("- 暂无 model_dataset.csv，无法研究。")
        return _write(lines)

    df = pd.read_csv(MODEL_DATASET_FILE, dtype={"code": str})
    if TARGET_COLUMN not in df.columns:
        lines.append("- 暂无 future_20d_top30 标签，无法训练。")
        return _write(lines)

    for col in FEATURE_COLUMNS + [TARGET_COLUMN]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    samples = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
    lines += [
        "## 样本数量",
        f"- 原始样本数：{len(df)}",
        f"- 可训练样本数：{len(samples)}",
    ]
    if len(samples) < 50 or samples[TARGET_COLUMN].nunique() < 2:
        lines += [
            "",
            "## 训练状态",
            "- 样本不足或标签类别不足，本次不训练模型，只保留研究骨架。",
            "- 当前阶段不应过度解读模型结果。",
        ]
        return _write(lines)

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
    except Exception as exc:
        lines += [
            "",
            "## 训练状态",
            f"- sklearn 依赖不可用，本次只生成占位报告：{type(exc).__name__}: {exc}",
        ]
        return _write(lines)

    x = samples[FEATURE_COLUMNS]
    y = samples[TARGET_COLUMN].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)
    model = LogisticRegression(max_iter=1000)
    model.fit(x_train_scaled, y_train)
    train_score = model.score(x_train_scaled, y_train)
    test_score = model.score(x_test_scaled, y_test)

    lines += [
        "",
        "## 训练状态",
        f"- 训练样本数量：{len(x_train)}",
        f"- 测试样本数量：{len(x_test)}",
        f"- 训练准确率：{train_score:.4f}",
        f"- 测试准确率：{test_score:.4f}",
        "",
        "## 特征系数",
        "| feature | coefficient |",
        "| --- | ---: |",
    ]
    for feature, coef in zip(FEATURE_COLUMNS, model.coef_[0]):
        lines.append(f"| {feature} | {coef:.6f} |")
    lines += [
        "",
        "## 提醒",
        "- 模型输出只用于研究，不参与当日信号。",
        "- 样本仍少时，不应把模型结果当作交易依据。",
    ]
    return _write(lines)


def _write(lines: list[str]) -> None:
    MODEL_RESEARCH_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_MODEL_RESEARCH_FILE.write_text(MODEL_RESEARCH_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"已生成模型研究报告：{MODEL_RESEARCH_REPORT_FILE}")


if __name__ == "__main__":
    write_model_research_report()
