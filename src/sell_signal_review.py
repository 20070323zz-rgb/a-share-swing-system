"""Daily sell review for paper ETF positions.

This module only writes review reports. It does not sell, reduce, modify
paper positions, append paper trades, connect to broker APIs, or read accounts.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd

from config import DATA_DIR, REPORT_DIR, PROJECT_ROOT


POSITIONS_FILE = DATA_DIR / "paper_positions.csv"
TRADES_FILE = DATA_DIR / "paper_trades.csv"
CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
SHORT_SWING_FILE = REPORT_DIR / "latest_short_swing.md"
RANKING_FILE = REPORT_DIR / "ranking_report.md"
DATA_HEALTH_FILE = REPORT_DIR / "latest_data_health.md"
REVIEW_MD_FILE = REPORT_DIR / "sell_signal_review.md"
REVIEW_CSV_FILE = REPORT_DIR / "sell_signal_review.csv"
REVIEW_HISTORY_FILE = REPORT_DIR / "sell_signal_review_history.csv"
DESIGN_REPORT_FILE = REPORT_DIR / "sell_signal_review_design_report.md"

PROTECTION_DAYS = 2


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    positions = _read_csv(POSITIONS_FILE)
    trades = _read_csv(TRADES_FILE)
    classification = _read_csv(CLASSIFICATION_FILE)
    buy_rank = _read_buy_ranking()
    short_signals = _read_short_signals()
    mid_signals = _read_mid_signals()
    health = _read_data_health()

    rows = []
    for item in positions.to_dict(orient="records"):
        rows.append(_review_position(item, buy_rank, short_signals, mid_signals, classification, health))

    rows = _attach_history_declines(rows)
    current = pd.DataFrame(rows)
    current.to_csv(REVIEW_CSV_FILE, index=False)
    _write_review_report(current)
    _write_design_report(current, trades)
    print(f"已生成卖出复核报告：{REVIEW_MD_FILE}")
    print(f"已生成卖出复核 CSV：{REVIEW_CSV_FILE}")


def _review_position(
    item: dict,
    buy_rank: dict[str, dict],
    short_signals: dict[str, dict],
    mid_signals: dict[str, dict],
    classification: pd.DataFrame,
    health: dict[str, dict],
) -> dict:
    symbol = str(item.get("symbol", "")).strip()
    name = str(item.get("name", symbol)).strip()
    rank_row = buy_rank.get(symbol, {})
    short_row = short_signals.get(symbol, {})
    mid_row = mid_signals.get(symbol, {})
    class_row = _classification_for(symbol, name, classification)
    health_row = health.get(symbol, {})

    current_price = _float(item.get("current_price"), _latest_close(symbol))
    entry_price = _float(item.get("entry_price"))
    stop_loss = _float(item.get("stop_loss"), _default_stop_loss(entry_price, class_row))
    holding_days = int(_float(item.get("holding_days")))
    current_rank = _float(rank_row.get("rank_score"), fallback=float("nan"))
    entry_rank = _parse_reason_score(item.get("reason"))
    rank_change = current_rank - entry_rank if pd.notna(current_rank) and pd.notna(entry_rank) else float("nan")
    rank_change_pct = rank_change / entry_rank if pd.notna(rank_change) and entry_rank else float("nan")

    mid_signal = str(rank_row.get("mid_trend_signal") or mid_row.get("signal") or _parse_reason_signal(item.get("reason"), "mid_trend") or "N/A")
    short_signal = str(rank_row.get("short_swing_signal") or short_row.get("signal") or _parse_reason_signal(item.get("reason"), "short_swing") or "N/A")
    entry_short = _parse_reason_signal(item.get("reason"), "short_swing") or "N/A"
    entry_mid = _parse_reason_signal(item.get("reason"), "mid_trend") or "N/A"

    etf_type = _effective_type(symbol, name, class_row)
    sensitivity = _sell_sensitivity(symbol, name, etf_type)
    health_status = str(health_row.get("status", "N/A") or "N/A")
    health_note = str(health_row.get("note", "") or "")
    stop_distance_pct = (current_price - stop_loss) / current_price if current_price and stop_loss else float("nan")
    unrealized_pnl_pct = _float(item.get("unrealized_pnl_pct"), _float(item.get("unrealized_return")))
    in_protection = holding_days <= PROTECTION_DAYS
    max_holding_days = int(_float(class_row.get("default_holding_max_days")))

    flags = _condition_flags(
        symbol=symbol,
        etf_type=etf_type,
        sensitivity=sensitivity,
        current_price=current_price,
        stop_loss=stop_loss,
        mid_signal=mid_signal,
        short_signal=short_signal,
        entry_mid=entry_mid,
        entry_short=entry_short,
        current_rank=current_rank,
        entry_rank=entry_rank,
        rank_change=rank_change,
        rank_change_pct=rank_change_pct,
        health_status=health_status,
        health_note=health_note,
        unrealized_pnl_pct=unrealized_pnl_pct,
        holding_days=holding_days,
        max_holding_days=max_holding_days,
        in_protection=in_protection,
    )
    status, action_note = _decide_status(flags, in_protection)

    return {
        "review_date": _latest_review_date(),
        "symbol": symbol,
        "name": name,
        "etf_type": etf_type,
        "group": class_row.get("group", ""),
        "sell_sensitivity": sensitivity,
        "holding_days": holding_days,
        "protection_period": "yes" if in_protection else "no",
        "entry_price": entry_price,
        "current_price": current_price,
        "stop_loss": stop_loss,
        "stop_distance_pct": stop_distance_pct,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "entry_rank_score": entry_rank,
        "rank_score": current_rank,
        "rank_score_change": rank_change,
        "rank_score_change_pct": rank_change_pct,
        "rank_decline_days": 0,
        "mid_trend_signal": mid_signal,
        "short_swing_signal": short_signal,
        "entry_mid_trend_signal": entry_mid,
        "entry_short_swing_signal": entry_short,
        "data_health_status": health_status,
        "data_health_note": health_note,
        "sell_review_status": status,
        "action_note": action_note,
        "condition_flags": "; ".join(flags),
        "safety_note": "review_only_no_trade",
    }


def _condition_flags(**kwargs) -> list[str]:
    flags: list[str] = []
    rank_change = kwargs["rank_change"]
    rank_change_pct = kwargs["rank_change_pct"]
    short_signal = kwargs["short_signal"].upper()
    mid_signal = kwargs["mid_signal"].upper()
    entry_short = kwargs["entry_short"].upper()
    health_status = kwargs["health_status"]
    sensitivity = kwargs["sensitivity"]
    etf_type = kwargs["etf_type"]
    current_rank = kwargs["current_rank"]

    if kwargs["stop_loss"] > 0 and kwargs["current_price"] <= kwargs["stop_loss"]:
        flags.append("stop_loss_break")
    if mid_signal == "SELL":
        flags.append("mid_trend_sell")
    if short_signal == "SELL":
        flags.append("short_swing_sell")
    if pd.notna(current_rank) and current_rank < 60:
        flags.append("rank_below_60")
    if pd.notna(rank_change) and rank_change <= -8:
        flags.append("rank_score_single_day_drop")
    if pd.notna(rank_change) and rank_change <= -12:
        flags.append("rank_score_large_drop")
    if pd.notna(rank_change_pct) and rank_change_pct <= -0.12:
        flags.append("rank_score_drop_pct_over_12")
    if entry_short == "BUY" and short_signal == "WATCH":
        flags.append("short_swing_buy_to_watch")
    if entry_short == "BUY" and short_signal == "SELL":
        flags.append("short_swing_buy_to_sell")
    if health_status == "提醒":
        flags.append("data_health_caution")
    if health_status == "异常":
        flags.append("data_health_error")
    if kwargs["unrealized_pnl_pct"] <= -0.035:
        flags.append("floating_loss_over_3_5pct")
    if kwargs["holding_days"] >= kwargs["max_holding_days"] > 0 and not (mid_signal == "BUY" or short_signal == "BUY"):
        flags.append("max_holding_days_without_signal_recovery")
    if etf_type in {"theme", "hot_theme", "high_beta"} and sensitivity in {"high", "very_high"} and "rank_score_large_drop" in flags:
        flags.append("high_beta_large_rank_decay")
    if kwargs["symbol"] == "515880" and health_status == "提醒":
        flags.append("515880_caution_min_review")
    return flags


def _decide_status(flags: list[str], in_protection: bool) -> tuple[str, str]:
    hard_sell = any(flag in flags for flag in ["stop_loss_break", "mid_trend_sell", "data_health_error", "max_holding_days_without_signal_recovery"])
    short_sell_rank_bad = "short_swing_sell" in flags and "rank_below_60" in flags
    if hard_sell or short_sell_rank_bad:
        return "SELL", "卖出候选，仅生成复核提醒；不自动卖出、不写交易。"

    if in_protection:
        if any(flag in flags for flag in ["data_health_caution", "short_swing_buy_to_watch", "rank_score_large_drop", "high_beta_large_rank_decay"]):
            return "REVIEW", "买入后 1-2 日保护期：不因单日评分下降直接卖出；人工复核，禁止加仓。"
        if "rank_score_single_day_drop" in flags:
            return "WATCH", "买入保护期内评分下降，继续持有观察，次日复核。"
        return "HOLD", "保护期内未触发硬风控，继续持有。"

    if "short_swing_buy_to_sell" in flags and "rank_below_60" in flags:
        return "SELL", "short_swing 转 SELL 且 rank_score 跌破阈值，列为卖出候选。"
    if "rank_decline_3d" in flags and any(flag in flags for flag in ["short_swing_buy_to_watch", "short_swing_sell"]):
        return "REDUCE", "rank_score 连续 3 日下降且短周期转弱，列为减仓候选。"
    if "high_beta_rank_decline_2d_with_weak_short" in flags:
        return "REDUCE", "主题/高 beta ETF 连续下降且短周期转弱，列为减仓候选。"
    if any(flag in flags for flag in ["data_health_caution", "rank_decline_2d", "short_swing_buy_to_watch", "high_beta_large_rank_decay"]):
        return "REVIEW", "触发人工复核条件；不自动卖出，dashboard 标黄。"
    if "rank_score_single_day_drop" in flags:
        return "WATCH", "rank_score 单日明显下降，但未触发趋势破坏或止损，继续观察。"
    return "HOLD", "mid_trend / short_swing 和风控未触发退出条件，继续持有。"


def _attach_history_declines(rows: list[dict]) -> list[dict]:
    current = pd.DataFrame(rows)
    previous = _read_csv(REVIEW_HISTORY_FILE)
    if not previous.empty and {"review_date", "symbol"}.issubset(previous.columns):
        key_date = str(current["review_date"].iloc[0]) if not current.empty else ""
        current_symbols = set(current["symbol"].astype(str))
        previous = previous[~((previous["review_date"].astype(str) == key_date) & previous["symbol"].astype(str).isin(current_symbols))]
    history = pd.concat([previous, current], ignore_index=True, sort=False) if not previous.empty else current.copy()

    decline_days: dict[str, int] = {}
    if not history.empty and {"symbol", "review_date", "rank_score"}.issubset(history.columns):
        hist = history.copy()
        hist["rank_score"] = pd.to_numeric(hist["rank_score"], errors="coerce")
        hist = hist.sort_values(["symbol", "review_date"])
        for symbol, group in hist.groupby("symbol"):
            group = group.dropna(subset=["rank_score"])
            count = 0
            scores = group["rank_score"].tolist()
            for idx in range(len(scores) - 1, 0, -1):
                if scores[idx] < scores[idx - 1]:
                    count += 1
                else:
                    break
            decline_days[str(symbol)] = count

    for row in rows:
        score_change = row.get("rank_score_change")
        inferred_one_day = 1 if pd.notna(score_change) and score_change < 0 else 0
        days = max(decline_days.get(str(row["symbol"]), 0), inferred_one_day)
        flags = row["condition_flags"].split("; ") if row["condition_flags"] else []
        if days >= 2:
            flags.append("rank_decline_2d")
        if days >= 3:
            flags.append("rank_decline_3d")
        if row["etf_type"] in {"theme", "hot_theme", "high_beta"} and days >= 2 and row["short_swing_signal"] in {"WATCH", "SELL"}:
            flags.append("high_beta_rank_decline_2d_with_weak_short")
        row["rank_decline_days"] = days
        row["condition_flags"] = "; ".join(dict.fromkeys(flags))
        status, action_note = _decide_status(flags, row["protection_period"] == "yes")
        row["sell_review_status"] = status
        row["action_note"] = action_note
    final_current = pd.DataFrame(rows)
    final_history = pd.concat([previous, final_current], ignore_index=True, sort=False) if not previous.empty else final_current.copy()
    if not final_history.empty:
        final_history.to_csv(REVIEW_HISTORY_FILE, index=False)
    return rows


def _write_review_report(df: pd.DataFrame) -> None:
    lines = [
        f"# 卖出复核报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告只做模拟盘持仓复核，不自动卖出、不自动减仓、不写入 paper_trades.csv、不修改 paper_positions.csv。",
        "",
        "## 摘要",
        f"- 当前持仓数：{len(df)}",
        f"- 状态分布：{df['sell_review_status'].value_counts().to_dict() if not df.empty else {}}",
        "- 买入后 1-2 个交易日为保护期：除止损/趋势破坏/严重数据异常外，不因单日评分下降直接 SELL。",
        "- 研究性止损只用于复核提示，不是正式交易规则。",
        "",
        "## 当前持仓复核",
        "| ETF | 名称 | 类型 | 持仓天数 | 保护期 | rank_score | rank变化 | 连续下降天数 | mid | short | 止损价 | 距离止损 | data_health | 状态 | 动作说明 |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['symbol']} | {row['name']} | {row['etf_type']} | {int(row['holding_days'])} | {row['protection_period']} | "
            f"{_fmt(row['rank_score'])} | {_fmt(row['rank_score_change'])} | {int(row['rank_decline_days'])} | "
            f"{row['mid_trend_signal']} | {row['short_swing_signal']} | {_fmt(row['stop_loss'])} | {_pct(row['stop_distance_pct'])} | "
            f"{row['data_health_status']} {row['data_health_note']} | {row['sell_review_status']} | {row['action_note']} |"
        )
    lines += [
        "",
        "## 触发条件明细",
        "| ETF | condition_flags | safety_note |",
        "| --- | --- | --- |",
    ]
    for _, row in df.iterrows():
        lines.append(f"| {row['symbol']} | {row['condition_flags']} | {row['safety_note']} |")
    lines += [
        "",
        "## 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存密码/token。",
        "- 不自动卖出或减仓。",
        "- 不新增模拟交易。",
        "- 不修改当前模拟持仓。",
    ]
    REVIEW_MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_design_report(df: pd.DataFrame, trades: pd.DataFrame) -> None:
    lines = [
        "# 卖出复核系统设计报告",
        "",
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 权限等级：L2 联网数据权限。",
        "- 本设计只服务模拟盘复核，不生成真实交易指令。",
        "",
        "## 1. 为什么不能单日评分下降就卖",
        "- BUY ranking 是横截面评分，单日下降可能来自市场风格切换、成交量短噪声或新候选变强。",
        "- ETF 买入后 1-2 个交易日容易出现正常回撤，直接 SELL 会放大噪声交易。",
        "- 因此需要结合 mid_trend、short_swing、止损线、data_health、ETF 类型和持仓天数共同判断。",
        "",
        "## 2. 状态定义",
        "- HOLD：中期和短期信号仍健康，未触发止损和数据异常。",
        "- WATCH：rank_score 单日明显下降，但趋势和止损未破坏，继续持有观察。",
        "- REVIEW：短周期转弱、rank 连续下降、data_health caution 或高波动主题大幅降分，需要人工复核。",
        "- REDUCE：连续下降叠加短周期转弱，或主题/高 beta 动量明显衰减，仅作为减仓候选。",
        "- SELL：跌破止损、中期趋势转 SELL、短周期 SELL 且 rank 跌破阈值、严重数据异常或持有期过长且信号未恢复，仅作为卖出候选。",
        "",
        "## 3. 买入后保护期",
        f"- 买入后 {PROTECTION_DAYS} 个交易日为观察保护期。",
        "- rank_score 单日大跌：WATCH。",
        "- rank_score 大跌 + short_swing 转 WATCH：REVIEW。",
        "- rank_score 大跌 + short_swing SELL 或跌破止损：SELL 候选。",
        "- 除非硬风控触发，否则不因单日评分下降直接 SELL。",
        "",
        "## 4. ETF 类型敏感度",
        "- broad_index：宽基，卖出不敏感；连续转弱再 REVIEW。",
        "- sector：行业，中等敏感；评分下降 + short_swing 转弱进入 REVIEW。",
        "- commodity_resource：周期资源，中高敏感；关注价格和政策周期。",
        "- theme / high_beta：主题或高 beta，更敏感；连续下降 + 短周期转弱可进入 REDUCE/SELL 候选。",
        "- bond_cash：低波动，单独处理。",
        "- qdii：先 REVIEW，需要溢价/汇率/海外交易日检查。",
        "",
        "## 5. 当前三只持仓复核结果",
        "| ETF | 名称 | 类型 | 状态 | 主要原因 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in df.iterrows():
        lines.append(f"| {row['symbol']} | {row['name']} | {row['etf_type']} | {row['sell_review_status']} | {row['condition_flags']} |")
    lines += [
        "",
        "## 6. 是否修改交易记录",
        f"- paper_trades.csv 当前行数：{len(trades)}。",
        "- 本轮未新增模拟交易。",
        "- 本轮未修改 paper_positions.csv。",
        "",
        "## 7. 是否保持 L2 边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存密码/token。",
        "- 不自动卖出、减仓或修改持仓。",
        "- 不修改正式仓位规则。",
        "",
        "## 8. 下一步",
        "- 需要对 WATCH/REVIEW/REDUCE/SELL 候选规则做离线回测。",
        "- 尤其要验证 rank_score 连续下降、short_swing 转弱、类型化止损是否能改善回撤而不过度交易。",
    ]
    DESIGN_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _read_buy_ranking() -> dict[str, dict]:
    rows = _read_markdown_table(BUY_RANKING_FILE, "全部 BUY 候选得分拆解") or _read_markdown_table(BUY_RANKING_FILE, "Top BUY Ranking")
    out: dict[str, dict] = {}
    for row in rows:
        code = str(row.get("code", "")).strip()
        if not code:
            continue
        out[code] = {
            "rank_score": _float(row.get("rank_score"), fallback=float("nan")),
            "mid_trend_signal": row.get("mid", "N/A"),
            "short_swing_signal": row.get("short", "N/A"),
            "group": row.get("group", ""),
        }
    return out


def _read_short_signals() -> dict[str, dict]:
    return {str(row.get("代码", "")).strip(): {"signal": row.get("信号", "N/A")} for row in _read_markdown_table(SHORT_SWING_FILE, "短期信号")}


def _read_mid_signals() -> dict[str, dict]:
    rows = _read_markdown_table(RANKING_FILE, "当前 BUY 标的汇总")
    out = {str(row.get("代码", "")).strip(): {"signal": row.get("signal", row.get("信号", "N/A"))} for row in rows}
    for row in _read_markdown_table(RANKING_FILE, "双周期综合评分 Top 10"):
        code = str(row.get("代码", "")).strip()
        if code and code not in out:
            out[code] = {"signal": row.get("mid", "N/A")}
    return out


def _read_data_health() -> dict[str, dict]:
    rows = _read_markdown_table(DATA_HEALTH_FILE, "明细")
    result = {}
    for row in rows:
        code = str(row.get("代码", "")).strip()
        if code:
            result[code] = {"status": row.get("状态", ""), "note": row.get("提醒", ""), "hard_issue": row.get("硬问题", "")}
    return result


def _read_markdown_table(path: Path, section_title: str) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if table and in_section:
                break
            in_section = section_title in stripped
            continue
        if in_section and stripped.startswith("|"):
            table.append(stripped)
        elif in_section and table:
            break
    if len(table) < 3:
        return []
    headers = [cell.strip() for cell in table[0].strip("|").split("|")]
    rows = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _classification_for(symbol: str, name: str, classification: pd.DataFrame) -> dict:
    if not classification.empty and "code" in classification.columns:
        matched = classification[classification["code"].astype(str) == symbol]
        if not matched.empty:
            return matched.iloc[0].to_dict()
    etf_type = _infer_type(name)
    profile = {
        "broad_index": (60, "low"),
        "sector": (30, "medium"),
        "commodity_resource": (45, "medium_high"),
        "theme": (20, "high"),
        "high_beta": (20, "very_high"),
        "bond_cash": (90, "low"),
        "qdii": (45, "medium"),
    }.get(etf_type, (30, "medium"))
    return {"code": symbol, "name": name, "group": "", "etf_type": etf_type, "default_holding_max_days": profile[0], "exit_sensitivity": profile[1]}


def _infer_type(name: str) -> str:
    if any(key in name for key in ["沪深300", "中证500", "中证1000", "科创50", "创业板", "上证50"]):
        return "broad_index"
    if any(key in name for key in ["证券", "券商"]):
        return "high_beta"
    if any(key in name for key in ["机器人", "低空", "AI", "半导体", "芯片", "算力"]):
        return "theme"
    if any(key in name for key in ["煤炭", "有色", "稀土", "能源", "黄金"]):
        return "commodity_resource"
    if any(key in name for key in ["银行", "医药", "消费", "军工", "新能源", "红利"]):
        return "sector"
    if any(key in name for key in ["纳指", "恒生", "港股", "标普"]):
        return "qdii"
    if any(key in name for key in ["国债", "短债", "货币", "日利", "添益"]):
        return "bond_cash"
    return "sector"


def _effective_type(symbol: str, name: str, class_row: dict) -> str:
    if symbol == "515880" or any(key in name for key in ["证券", "券商"]):
        return "high_beta"
    return str(class_row.get("etf_type") or _infer_type(name))


def _sell_sensitivity(symbol: str, name: str, etf_type: str) -> str:
    if symbol == "512800":
        return "medium_low"
    if symbol == "515880":
        return "very_high"
    if etf_type in {"theme", "hot_theme", "high_beta"}:
        return "very_high"
    if etf_type in {"sector", "commodity_resource"}:
        return "medium"
    if etf_type == "broad_index":
        return "low"
    return "medium"


def _default_stop_loss(entry_price: float, class_row: dict) -> float:
    etf_type = str(class_row.get("etf_type", "sector"))
    pct = {
        "broad_index": 0.08,
        "sector": 0.06,
        "commodity_resource": 0.06,
        "theme": 0.05,
        "hot_theme": 0.05,
        "high_beta": 0.05,
        "bond_cash": 0.02,
        "qdii": 0.07,
    }.get(etf_type, 0.06)
    return entry_price * (1 - pct) if entry_price else 0.0


def _latest_close(symbol: str) -> float:
    prefix = "sh" if symbol.startswith(("5", "6")) else "sz"
    path = DATA_DIR / "etf_daily" / f"{prefix}_{symbol}.csv"
    if not path.exists():
        return 0.0
    try:
        df = pd.read_csv(path)
    except Exception:
        return 0.0
    if df.empty or "close" not in df.columns:
        return 0.0
    return _float(df.iloc[-1]["close"])


def _parse_reason_score(reason: object) -> float:
    match = re.search(r"rank_score=([0-9.]+)", str(reason or ""))
    return float(match.group(1)) if match else float("nan")


def _parse_reason_signal(reason: object, key: str) -> str:
    match = re.search(rf"{re.escape(key)}=([A-Z_]+)", str(reason or ""))
    return match.group(1) if match else ""


def _latest_review_date() -> str:
    latest = ""
    for path in (DATA_DIR / "etf_daily").glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or pd.Timestamp.now().strftime("%Y-%m-%d")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _fmt(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
