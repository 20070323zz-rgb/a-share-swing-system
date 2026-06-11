"""Generate next-stage strategy optimization research reports.

This module writes offline research artifacts only. It does not change strategy
rules, ranking weights, paper positions, or paper trades.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from config import DATA_DIR, REPORT_DIR
from etf_classification import CLASSIFICATION_FILE, main as build_classification


KEYWORDS_FILE = DATA_DIR / "etf_theme_keywords.csv"
SENTIMENT_REPORT = REPORT_DIR / "news_sentiment_framework.md"
DATA_SOURCE_REPORT = REPORT_DIR / "news_data_source_plan.md"
POSITIONS_REPORT = REPORT_DIR / "current_positions_strategy_fit_report.md"
SUMMARY_REPORT = REPORT_DIR / "next_stage_strategy_optimization_report.md"


KEYWORD_ROWS = [
    ("commodity_resource", "周期资源", "煤炭", "煤炭,动力煤,焦煤,煤价,能源保供,火电,山西煤炭,产能,进口煤,库存下降", "煤价下跌,库存高企,需求疲弱,进口煤冲击", "发改委,能源局,保供稳价,煤电联营", "煤矿事故,安监,环保限产,价格管控", "长协价,旺季补库,安全检查", "煤化工泛词,单个公司八卦", "Tushare,东方财富,财联社,证券报", "515220 重点关注"),
    ("sector", "金融地产", "银行", "银行,息差,降准,降息,信贷,资产质量,拨备,高股息,红利", "净息差收窄,不良率,地产风险,地方债风险", "央行,金融监管总局,LPR,存款利率", "地产违约,拨备不足,资本充足率压力", "降准,信贷投放,业绩发布", "泛金融新闻", "证券报,央行,东方财富", "512800 重点关注"),
    ("sector", "金融地产", "证券", "券商,证券,成交额,两融,IPO,并购重组,资本市场改革,印花税,牛市预期", "成交额萎缩,IPO放缓,再融资收紧,监管处罚", "证监会,资本市场改革,并购重组,交易制度", "政策兑现,高开低走,市场低迷", "印花税,并购政策,成交额突破", "营销号牛市小作文", "证监会,财联社,东方财富", "515880 data_health caution"),
    ("theme", "科技成长", "科技", "半导体,AI,算力,光模块,通信,国产替代,芯片,软件,信创", "出口限制,制裁,库存周期,砍单,业绩不及预期", "工信部,数字中国,国产替代,人工智能行动计划", "海外制裁,估值过高,主题拥挤", "发布会,订单,财报,产业大会", "泛科技口号", "Tushare,财联社,证券报", ""),
    ("theme", "科技成长", "5G", "5G,通信设备,基站,运营商,光模块,算力网络,数据中心,6G", "资本开支下降,订单延后,海外限制", "工信部,通信基础设施,算力网络", "光模块拥挤,运营商capex下滑", "运营商集采,网络建设", "手机消费泛新闻", "工信部,财联社,东方财富", ""),
    ("theme", "消费医药", "创新药/医药", "创新药,医保谈判,CXO,出海,FDA,临床,医疗器械,BD授权", "集采降价,临床失败,FDA拒批,医保控费,CXO订单下滑", "医保局,药监局,审评审批,创新药支持", "政策压价,临床失败,出海预期落空", "医保谈判,临床数据,BD合作", "养生保健软文", "药监局,证券报,财联社", ""),
    ("hot_theme", "高端制造", "机器人", "机器人,人形机器人,工业母机,伺服,减速器,量产,订单", "量产推迟,商业化不及预期,订单证伪", "智能制造,工信部,机器人产业规划", "概念炒作,高位退潮,业绩空窗", "产业大会,新品发布,订单签约", "玩具机器人,消费电子泛词", "财联社,证券报,东方财富", ""),
    ("hot_theme", "高端制造", "低空经济", "低空经济,eVTOL,无人机,空域,通航,试点", "监管空域,订单证伪,商业化推迟", "低空试点,民航局,地方政策", "政策兑现,题材退潮,安全事故", "试点城市,适航认证,订单", "军事无人机无关新闻", "财联社,证券报,地方政府", ""),
    ("hot_theme", "高端制造", "商业航天", "商业航天,卫星,火箭,星座,遥感,卫星互联网", "发射失败,订单不及预期,融资困难", "航天政策,卫星互联网,军民融合", "发射失败,主题炒作,估值过高", "发射任务,星座建设,招标", "科幻娱乐新闻", "财联社,证券报,巨潮", ""),
    ("sector", "防御风格", "红利/高股息", "红利,高股息,央企,中特估,现金流,分红,低波", "分红不及预期,股息陷阱,周期利润下滑", "市值管理,央企考核,分红监管", "拥挤交易,利率上行,估值修复后收益下降", "分红预案,央企考核", "营销分红榜单", "证券报,交易所,东方财富", ""),
    ("theme", "科技成长", "半导体", "半导体,芯片,晶圆,设备,材料,国产替代,先进封装", "库存高企,砍单,出口限制,制裁", "工信部,产业基金,国产替代", "海外制裁,周期下行,估值过高", "设备订单,财报,产业基金", "消费电子泛词", "财联社,证券报,巨潮", ""),
    ("hot_theme", "科技成长", "算力/数据中心", "算力,数据中心,服务器,GPU,光模块,液冷,电力", "订单证伪,资本开支下降,供给过剩", "东数西算,算力网络,AI政策", "AI退潮,光模块拥挤,业绩不及预期", "订单,招标,云厂商capex", "泛AI口号", "财联社,东方财富,证券报", ""),
    ("sector", "新能源制造", "新能源", "新能源,光伏,风电,电池,储能,新能源车,装机", "产能过剩,价格战,组件降价,需求下滑", "双碳,能源局,补贴政策", "产能出清慢,贸易壁垒,库存高企", "装机数据,价格数据,财报", "汽车营销新闻", "能源局,财联社,证券报", ""),
    ("sector", "新能源制造", "军工", "军工,国防,装备,订单,航空发动机,船舶", "订单延迟,业绩不及预期,预算压力", "国防预算,装备采购,军民融合", "订单不透明,高估值,事件兑现", "预算发布,订单披露,产业大会", "军事冲突泛新闻", "证券报,巨潮,财联社", ""),
    ("sector", "消费医药", "消费", "消费,食品饮料,白酒,家电,旅游,免税,复苏", "需求疲弱,库存,价格下滑,消费降级", "促消费,补贴政策,假期数据", "业绩不及预期,渠道库存,高估值", "节假日数据,财报,价格调整", "泛生活新闻", "统计局,证券报,东方财富", ""),
    ("qdii", "QDII观察", "QDII", "港股,纳指,恒生,日经,印度,美股,汇率,海外交易日", "溢价扩大,汇率波动,海外休市,数据滞后", "海外央行,美联储,港交所", "高溢价,汇率急变,海外风险事件", "海外收盘,汇率,溢价率", "国内同名主题混淆", "交易所,基金公告,东方财富", "只做观察/研究优先"),
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    write_keywords()
    write_sentiment_report()
    write_data_source_report()
    write_positions_report()
    write_summary_report()
    print(f"已生成关键词库：{KEYWORDS_FILE}")
    print(f"已生成新闻情绪框架：{SENTIMENT_REPORT}")
    print(f"已生成新闻数据源计划：{DATA_SOURCE_REPORT}")
    print(f"已生成当前持仓专项复核：{POSITIONS_REPORT}")
    print(f"已生成下一阶段总报告：{SUMMARY_REPORT}")


def write_keywords() -> None:
    fields = [
        "etf_type",
        "group",
        "theme_name",
        "positive_keywords",
        "negative_keywords",
        "policy_keywords",
        "risk_keywords",
        "event_keywords",
        "avoid_keywords",
        "source_priority",
        "notes",
    ]
    with KEYWORDS_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(KEYWORD_ROWS)


def write_sentiment_report() -> None:
    lines = [
        "# 新闻情绪风险过滤框架",
        "",
        "本报告只设计离线框架，不接新闻数据进 BUY 主分，不生成交易指令。",
        "",
        "## 情绪标签",
        "- positive：正面事件 + 资金/成交确认。",
        "- neutral：有新闻但方向不明确。",
        "- negative：负面行业、政策或资金消息。",
        "- noisy：重复新闻、小作文、多源冲突、无资金确认。",
        "- event_risk：重大政策/监管/高位兑现风险。",
        "- no_data：暂无可用新闻数据。",
        "",
        "## 初版公式",
        "```text",
        "industry_sentiment_score =",
        "  新闻热度分",
        "+ 正面关键词分",
        "- 负面关键词分",
        "+ 政策催化分",
        "+ 产业事件分",
        "+ 资金/成交确认分",
        "- 风险事件分",
        "- 情绪衰减惩罚",
        "- 重复新闻惩罚",
        "+ 来源权重调整",
        "```",
        "",
        "## 使用边界",
        "- 第一阶段只作为解释层和风险提示。",
        "- 第二阶段生成 reports/industry_news_watch.md，不进入 BUY 主分。",
        "- 第三阶段有历史数据后再回测，最多考虑小权重辅助或降权。",
        "- negative/noisy/event_risk 可作为禁止加仓或 REVIEW 触发条件的候选研究项。",
        "",
        "## 风险控制",
        "- 不使用单条新闻直接买入。",
        "- 不使用社交媒体小作文直接交易。",
        "- 同一事件要按标题相似度和来源去重。",
        "- 主题 ETF 需要情绪衰减，不允许长期沿用旧催化。",
        "- 本框架不修改 mid_trend / short_swing / BUY ranking。",
    ]
    SENTIMENT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_data_source_report() -> None:
    lines = [
        "# 新闻数据源接入计划",
        "",
        "本计划只用于研究数据建设，不接真实交易，不把新闻直接接入 BUY 主分。",
        "",
        "| 数据源 | 适用性 | 风险 | 优先级 | L2 边界 |",
        "| --- | --- | --- | --- | --- |",
        "| Tushare news / major_news | 适合历史新闻研究；2000 积分是否可用需用户本地 token 实测 | 权限和积分限制 | P1 | token 只能环境变量，不写日志 |",
        "| 东方财富快讯/板块新闻/板块资金流 | 适合低频行业观察和资金确认 | 反爬、页面结构变化 | P1/P2 | 只读低频，不抓敏感数据 |",
        "| 财联社 | 适合人工复核政策和产业快讯 | 商业版权、反爬 | P2 | 优先人工复核 |",
        "| 三大证券报 | 适合权威政策确认 | 接口不统一 | P2 | 只读摘要/链接 |",
        "| 巨潮资讯 | 适合公告层和基金公告 | 不适合实时情绪 | P2 | 只读公告 |",
        "| AKShare | 可能有板块资金流、概念、新闻辅助接口 | 本机稳定性需验证 | P2 | 只读，本机验证优先 |",
        "| a-stock-data | 可作为辅助候选 | 来源许可和维护状态需审计 | P3 | 不作为主数据源 |",
        "| QVeris | 适合后期 Agent 工具层 | 不是主数据源 | P3 | 只用于检索辅助 |",
        "",
        "## 阶段计划",
        "1. 第一阶段：不自动交易，不接新闻到 BUY，只建立关键词库和人工复核报告。",
        "2. 第二阶段：低频新闻摘要，生成 reports/industry_news_watch.md，只用于解释和风险提示。",
        "3. 第三阶段：有历史数据后回测，通过后才考虑小权重辅助或降权。",
    ]
    DATA_SOURCE_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_positions_report() -> None:
    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    classification = _read_csv(CLASSIFICATION_FILE)
    class_map = classification.set_index("code").to_dict(orient="index") if not classification.empty else {}
    exposure = positions.merge(classification[["code", "etf_type", "holding_profile", "group"]], left_on="symbol", right_on="code", how="left") if not positions.empty and not classification.empty else pd.DataFrame()
    group_value = {}
    if not exposure.empty:
        exposure["market_value"] = pd.to_numeric(exposure["market_value"], errors="coerce").fillna(0)
        group_value = exposure.groupby("group")["market_value"].sum().to_dict()
    lines = [
        "# 当前模拟持仓策略适配专项复核",
        "",
        "本报告只做模拟盘研究复核，不生成交易指令，不修改持仓。",
        "",
        "## 当前持仓",
        "| symbol | name | etf_type | holding_profile | 是否适合 20-60 天 | 研究复核建议 | 关键词关注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    keyword_map = {
        "515220": "煤炭、动力煤、焦煤、煤价、能源保供、火电、进口煤、安监",
        "512800": "银行、息差、降准、降息、信贷、资产质量、房地产融资、高股息",
        "515880": "券商、成交额、两融、IPO、并购重组、资本市场改革、印花税、牛市预期",
    }
    for _, row in positions.iterrows():
        code = str(row["symbol"])
        item = class_map.get(code, {})
        suitable = "部分适合" if item.get("etf_type") in {"broad_index", "bond_cash"} else "不宜机械套用"
        review = _position_review_text(code, item)
        lines.append(
            f"| {code} | {row['name']} | {item.get('etf_type','unknown')} | {item.get('holding_profile','N/A')} | "
            f"{suitable} | {review} | {keyword_map.get(code,'')} |"
        )
    lines += [
        "",
        "## 515880 data_health caution",
        "- 515880 当前在 data_health 中有 caution：存在单日涨跌幅极端异常。",
        "- 研究建议：禁止加仓，进入 REVIEW；如连续异常或价格口径问题未解除，不作为核心加仓对象。",
        "- 本报告不自动减仓、不自动卖出。",
        "",
        "## 组合集中度",
        f"- 当前 group 市值分布：{group_value}",
        "- 组合集中于金融/周期，dashboard 应继续显示金融/周期集中度提示。",
        "- 是否加入宽基或防守 ETF 平衡，需要 Main/GPT 后续评估；本轮不改仓位。",
        "",
        "## 候选退出/减仓触发条件",
        "- rank_score 连续下降或跌出前列：只进入 REVIEW，不自动交易。",
        "- short_swing 从 BUY 转 WATCH：禁止加仓或减半候选，需要回测。",
        "- 类型化止损：需离线验证后再进入模拟观察。",
        "- 新闻 event_risk：只作为风险过滤器候选。",
    ]
    POSITIONS_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_summary_report() -> None:
    classification = _read_csv(CLASSIFICATION_FILE)
    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    watchlist = _read_csv(Path("watchlist.csv"))
    health_report = REPORT_DIR / "latest_data_health.md"
    type_counts = classification["etf_type"].value_counts().to_dict() if not classification.empty else {}
    pool_counts = classification["pool"].value_counts().to_dict() if not classification.empty and "pool" in classification.columns else {}
    watchlist_roles = watchlist["role"].value_counts().to_dict() if not watchlist.empty and "role" in watchlist.columns else {}
    held_codes = positions["symbol"].astype(str).tolist() if not positions.empty and "symbol" in positions.columns else []
    health_hint = _health_hint(health_report)
    lines = [
        "# 下一阶段策略优化研究总报告",
        "",
        "本报告汇总本轮 research/simulation 层改造，不修改当前交易策略、仓位规则或模拟持仓。",
        "",
        "## 0. 现状读取",
        f"- 当前模拟持仓：{held_codes}",
        f"- watchlist role 分布：{watchlist_roles}",
        f"- ETF 类型分层 pool 分布：{pool_counts}",
        f"- data_health 摘要：{health_hint}",
        "- 当前 paper_positions.csv / paper_trades.csv 未由本轮脚本写入或修改。",
        "",
        "## 1. 本轮优化研究范围",
        "- ETF 类型分层。",
        "- 类型化持有周期离线研究。",
        "- 候选退出规则离线研究。",
        "- 新闻情绪风险过滤框架。",
        "- 新闻数据源接入计划。",
        "- 当前持仓专项复核。",
        "- dashboard 只读研究展示。",
        "",
        "## 2. ETF 类型分层结果",
        f"- 各类型数量：{type_counts}",
        "- 详见 reports/etf_type_classification_report.md。",
        "",
        "## 3. 持有周期研究结果",
        "- 已生成 reports/holding_period_research_report.md 和 results.csv。",
        "- 当前研究使用 proxy_buy_signal、short_swing_weakening、proxy_rank_decline_3d。",
        "- 结论必须区分 evidence_supported / sample_limited / hypothesis_only。",
        "",
        "## 4. 退出规则离线验证结果",
        "- 已生成 reports/exit_rule_research_report.md。",
        "- rank_score 历史目前用 proxy_score 代替，不建议直接上线。",
        "- short_swing 转弱可优先进入 REVIEW/禁止加仓候选。",
        "",
        "## 5. 新闻情绪框架",
        "- 已生成 data/etf_theme_keywords.csv。",
        "- 已生成 reports/news_sentiment_framework.md。",
        "- 新闻情绪不进入 BUY 主分，只作为解释层/风险过滤器候选。",
        "",
        "## 6. 新闻数据源接入计划",
        "- 已生成 reports/news_data_source_plan.md。",
        "- Tushare 权限需用户本地 token 实测。",
        "- 东方财富、财联社、三大证券报、巨潮、AKShare 可分阶段低频接入或人工复核。",
        "",
        "## 7. 当前持仓专项复核",
        "- 已生成 reports/current_positions_strategy_fit_report.md。",
        "- 515220 属于 commodity_resource，研究周期 10-45 天。",
        "- 512800 属于 sector，研究周期 10-30 天。",
        "- 515880 属于 sector，且 data_health caution，应禁止加仓并 REVIEW。",
        "",
        "## 8. dashboard 展示改造",
        "- dashboard 增加 ETF 类型、holding_profile、研究周期、持仓天数 vs 研究周期、sentiment_status 占位。",
        "- dashboard 只读，不提供交易按钮。",
        "",
        "## 9. 可进入下一阶段模拟观察",
        "- ETF 类型分层展示。",
        "- 持仓天数 vs 研究周期提醒。",
        "- data_health caution 禁止加仓提示。",
        "- short_swing 转弱进入 REVIEW 的观察项。",
        "",
        "## 10. 必须继续回测",
        "- 类型化止损。",
        "- rank_score 连续下降退出。",
        "- Top3 跌出 Top10 退出。",
        "- 热度衰减代理规则。",
        "",
        "## 11. 不建议上线",
        "- 新闻情绪直接作为 BUY 主因子。",
        "- 自动卖出/自动减仓。",
        "- 未经验证的主题 ETF 短止损。",
        "- 对当前 515220、512800、515880 自动改仓。",
        "",
        "## 12. 风险与限制",
        "- rank_score 历史序列不足，部分研究使用 proxy。",
        "- 新闻数据尚未接入历史库，情绪框架只做设计。",
        "- 扩池 ETF 历史较短，部分类型 sample_limited。",
        "",
        "## 13. L2 边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存密码/token。",
        "- 不修改 mid_trend / short_swing 核心策略。",
        "- 不修改 paper_positions.csv / paper_trades.csv。",
        "- 不把新闻情绪直接接入 BUY 主分。",
    ]
    SUMMARY_REPORT.write_text("\n".join(lines), encoding="utf-8")


def _position_review_text(code: str, item: dict) -> str:
    if code == "515220":
        return "周期资源，建议更关注 10-45 天及煤价/政策变化"
    if code == "512800":
        return "金融行业，20-60 天可观察但建议 10-30 天复核"
    if code == "515880":
        return "高 beta 券商，建议更短周期复核；data_health caution 禁止加仓"
    return f"{item.get('etf_type','unknown')} 类型，按 {item.get('holding_profile','N/A')} 研究"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _health_hint(path: Path) -> str:
    if not path.exists():
        return "latest_data_health.md 不存在"
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ") and len(lines) < 5:
            lines.append(line[2:])
    return "；".join(lines) if lines else "已生成，未解析到摘要行"


if __name__ == "__main__":
    main()
