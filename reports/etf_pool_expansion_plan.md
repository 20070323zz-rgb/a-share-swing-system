# ETF Pool Expansion Plan

- Generated on: 2026-06-08
- Current ETF count: 76
- Current trade_pool ETF count: 63
- Current observe_pool ETF count: 13
- New candidate count: 94
- Candidates with six-digit seed code: 36
- Direction-only candidates pending JQData code verification: 58
- Target ETF universe after JQData verification: 170
- Target layering preview: trade_pool 86, observe_pool 58, research_only 26
- Pool update policy: this plan does not modify `watchlist.csv`; it writes a reversible candidate file first.
- Import policy: every new ETF must enter staging, pass validation, pass diagnosis/dry-run, and only then may be imported.
- Merge policy: if dates overlap, existing `data/etf_daily/` rows win.
- Safety: no broker API, no real orders, no account/password storage, no strategy or position-rule changes.

## Selection Principles

- Prefer broad base, dividend/quality/low-vol, defensives, innovation drug, robotics, A500, 科创100/200.
- QDII, bond, cash-management, new hot themes, and uncertain products default to observe_pool or research_only.
- Same-index duplicates are retained only for JQData/volume comparison; final trade_pool should keep the more liquid representative.
- Direction-only rows must be resolved by JQData `get_all_securities` before download and import.

## Old ETF Downgrade Suggestions

| code | name | current role | suggested role | reason |
| --- | --- | --- | --- | --- |
| 512200 | 房地产ETF | trade_pool | observe_pool | 地产链趋势持续性和政策依赖较强，建议降级观察。 |
| 159766 | 旅游ETF | trade_pool | observe_pool | 消费复苏主题弹性强但持续性较弱，适合作为观察。 |
| 159865 | 养殖ETF | trade_pool | observe_pool | 周期和供给扰动较强，建议从主仓候选降级。 |
| 159806 | 新能源车电池ETF | trade_pool | observe_pool | 与新能源车、电池、新能源ETF同质化高。 |
| 159857 | 光伏ETF | trade_pool | observe_pool | 与515790同质化较高，保留更高质量代表即可。 |

## Homogeneity Notes

- A500 candidates are numerous; final trade_pool should keep 2-4只高流动性代表，其余观察或研究。
- 科创100 candidates overlap heavily; final trade_pool should keep 1-2只。
- 创新药 candidates overlap heavily; final trade_pool should keep 1-2只，港股创新药默认观察。
- 红利/现金流/低波是中周期主线，但不要把所有相似产品同时放入主交易池。
- 港股、日经、德国、印度、新兴市场 ETF 受跨境交易日、汇率、QDII额度和溢价影响，默认不进入主交易池。

## Candidate Table

| code | name | group | role | strategy | priority | staging pull? | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 159338 | 国泰中证A500ETF | 新宽基与新风格 | trade_pool | mid_trend | S | yes | A500是新一代核心宽基，成交活跃，适合作为沪深300之外的核心观察与交易标的。 |
| 159352 | 南方中证A500ETF | 新宽基与新风格 | trade_pool | mid_trend | S | yes | A500主流产品，适合与现有宽基形成中盘覆盖补充。 |
| 563360 | 华泰柏瑞中证A500ETF | 新宽基与新风格 | trade_pool | mid_trend | S | yes | A500主流产品，流动性关注度高，适合核心宽基扩容。 |
| 563800 | 广发中证A500ETF | 新宽基与新风格 | trade_pool | mid_trend | A | yes | A500同类补充，先进入交易候选，后续用成交与相关性筛选最终留存。 |
| 512050 | 华夏中证A500ETF | 新宽基与新风格 | trade_pool | mid_trend | A | yes | A500同类补充，适合做同质化比较后择优保留。 |
| 560510 | 泰康中证A500ETF | 新宽基与新风格 | observe_pool | observe | A | yes | A500同类较多，先观察不直接增加主仓拥挤度。 |
| 588220 | 科创100ETF基金 | 新宽基与新风格 | trade_pool | both | S | yes | 科创100补齐科创板中小盘弹性，与现有科创50不同质。 |
| 588030 | 博时科创100ETF | 新宽基与新风格 | trade_pool | both | A | yes | 科创100同类补充，用于后续流动性择优。 |
| 588190 | 银华科创100ETF | 新宽基与新风格 | observe_pool | observe | A | yes | 科创100同类观察，避免同质化直接挤占交易池。 |
| 588120 | 国泰科创100ETF | 新宽基与新风格 | observe_pool | observe | A | yes | 科创100同类观察，适合做成交与跟踪误差比较。 |
| 588800 | 华夏科创100ETF | 新宽基与新风格 | observe_pool | observe | B | yes | 科创100备选，同质化较强，先观察。 |
| 159593 | 中证A50ETF | 新宽基与新风格 | trade_pool | mid_trend | A | yes | A50偏核心龙头，适合作为上证50和沪深300之间的风格补充。 |
| PENDING_A50_01 | 中证A50ETF备选 | 新宽基与新风格 | research_only | observe | B | after_jqdata_code_resolve | 需由JQData确认具体场内代码与上市状态后再判断。 |
| PENDING_CSI2000_01 | 中证2000ETF主流产品 | 新宽基与新风格 | observe_pool | observe | A | after_jqdata_code_resolve | 小微盘弹性高但波动大，适合观察池而非直接主仓。 |
| PENDING_KC200_01 | 科创200ETF主流产品 | 新宽基与新风格 | research_only | observe | B | after_jqdata_code_resolve | 新指数样本短，先研究不进入交易池。 |
| PENDING_BJ50_01 | 北证50ETF主流产品 | 新宽基与新风格 | research_only | observe | B | after_jqdata_code_resolve | 北交所波动和流动性约束更强，先研究。 |
| 562500 | 机器人ETF华夏 | 科技与新质生产力 | trade_pool | short_swing | S | yes | 机器人是新质生产力主线，适合小仓短波段与主题共振观察。 |
| 159770 | 机器人ETF | 科技与新质生产力 | observe_pool | observe | A | yes | 机器人同类产品，先观察成交与跟踪指数差异。 |
| PENDING_ROBOT_50_01 | 机器人50ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | 机器人细分方向，待JQData确认代码和历史长度。 |
| PENDING_SEMI_EQUIP_01 | 半导体设备ETF主流产品 | 科技与新质生产力 | trade_pool | short_swing | A | after_jqdata_code_resolve | 补齐半导体上游设备，和现有芯片ETF不完全同质。 |
| PENDING_AI_KCB_01 | 科创人工智能ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | AI主题高波动，先观察，避免过热主题直接重仓。 |
| PENDING_COMPUTE_01 | 算力ETF主流产品 | 科技与新质生产力 | trade_pool | short_swing | A | after_jqdata_code_resolve | 算力与数据中心是AI产业链核心分支，适合短波段研究。 |
| PENDING_DATA_CENTER_01 | 数据中心ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | 与算力/通信有重叠，先观察后择优。 |
| PENDING_TELECOM_EQUIP_01 | 通信设备ETF主流产品 | 科技与新质生产力 | trade_pool | short_swing | A | after_jqdata_code_resolve | 补齐通信设备，和现有5G ETF形成细分对照。 |
| PENDING_XINCHUANG_01 | 信创ETF主流产品 | 科技与新质生产力 | observe_pool | observe | B | after_jqdata_code_resolve | 政策主题属性强，需观察趋势持续性。 |
| PENDING_INFOSAFE_01 | 信息安全ETF主流产品 | 科技与新质生产力 | observe_pool | observe | B | after_jqdata_code_resolve | 与软件、信创、AI有相关性，先观察。 |
| PENDING_MACHINE_TOOL_01 | 工业母机ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | 高端制造补充，适合观察池。 |
| PENDING_HIGH_END_EQUIP_01 | 高端装备ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | 制造升级主题，需与军工/智能制造去重。 |
| PENDING_LOW_ALTITUDE_01 | 低空经济ETF主流产品 | 科技与新质生产力 | research_only | observe | B | after_jqdata_code_resolve | 新发热门主题，先研究不直接交易。 |
| PENDING_SPACE_01 | 商业航天ETF主流产品 | 科技与新质生产力 | research_only | observe | B | after_jqdata_code_resolve | 新发热门主题，样本和成交需要验证。 |
| 515120 | 广发创新药ETF | 医药与消费升级 | trade_pool | both | S | yes | 创新药是医药中弹性最高的主线之一，和现有医药/医疗ETF不完全同质。 |
| 516080 | 易方达创新药ETF | 医药与消费升级 | trade_pool | both | A | yes | 创新药同类备选，用成交和历史长度筛选。 |
| 159992 | 银华创新药ETF | 医药与消费升级 | trade_pool | both | A | yes | 创新药主流产品，适合作为短波段研究。 |
| 159858 | 南方创新药ETF | 医药与消费升级 | observe_pool | observe | B | yes | 创新药同类观察，避免主题拥挤。 |
| 159835 | 建信创新药ETF | 医药与消费升级 | observe_pool | observe | B | yes | 创新药同类观察，后续按流动性择优。 |
| 513120 | 港股创新药ETF | 医药与消费升级 | observe_pool | observe | A | yes | 港股创新药弹性高但QDII/港股口径特殊，默认观察。 |
| PENDING_HK_BIOTECH_01 | 恒生生物科技ETF主流产品 | 医药与消费升级 | observe_pool | observe | A | after_jqdata_code_resolve | 港股医药弹性补充，需处理QDII/港股交易日差异。 |
| PENDING_MED_DEVICE_01 | 医疗器械ETF主流产品 | 医药与消费升级 | trade_pool | both | A | after_jqdata_code_resolve | 补齐医药设备方向，与创新药、医疗服务分散。 |
| 159209 | 红利质量ETF | 防御、红利、质量 | trade_pool | mid_trend | S | yes | 红利质量兼顾分红与盈利质量，适合中周期防御。 |
| 159119 | 800现金流ETF | 防御、红利、质量 | trade_pool | mid_trend | S | yes | 自由现金流因子适合A股高分红与质量风格补充。 |
| 562080 | 300现金流ETF | 防御、红利、质量 | trade_pool | mid_trend | A | yes | 沪深300自由现金流方向，适合作为质量因子补充。 |
| 520550 | 港股红利低波ETF | 防御、红利、质量 | observe_pool | observe | A | yes | 港股高股息/低波补充，默认观察池。 |
| PENDING_CENTRAL_DIV_01 | 央企红利ETF主流产品 | 防御、红利、质量 | trade_pool | mid_trend | A | after_jqdata_code_resolve | 央企红利与红利低波形成防御风格补充。 |
| PENDING_QUALITY_LOWVOL_01 | 质量低波ETF主流产品 | 防御、红利、质量 | trade_pool | mid_trend | A | after_jqdata_code_resolve | 低波质量适合小资金中周期稳健筛选。 |
| PENDING_UTILITY_01 | 公用事业ETF主流产品 | 防御、红利、质量 | observe_pool | observe | A | after_jqdata_code_resolve | 偏防御行业，和电力/红利有相关性，先观察。 |
| PENDING_POWER_01 | 电力ETF主流产品 | 防御、红利、质量 | trade_pool | mid_trend | A | after_jqdata_code_resolve | 电力具备防御与周期双属性，适合中趋势。 |
| PENDING_A500_DIV_LOWVOL_01 | A500红利低波ETF主流产品 | 防御、红利、质量 | research_only | observe | B | after_jqdata_code_resolve | 新宽基叠加红利低波，历史短，先研究。 |
| PENDING_COPPER_01 | 铜ETF主流产品 | 周期、资源、商品 | observe_pool | observe | A | after_jqdata_code_resolve | 铜和全球制造周期相关，适合周期观察。 |
| PENDING_INDUSTRIAL_METAL_01 | 工业金属ETF主流产品 | 周期、资源、商品 | observe_pool | observe | A | after_jqdata_code_resolve | 补齐工业金属，和有色ETF去重后择优。 |
| PENDING_OILGAS_01 | 油气ETF主流产品 | 周期、资源、商品 | observe_pool | observe | A | after_jqdata_code_resolve | 油气受海外价格和汇率影响，默认观察。 |
| 516020 | 化工ETF | 周期、资源、商品 | trade_pool | short_swing | A | yes | 化工是典型周期行业，适合短波段研究。 |
| 159870 | 化工ETF | 周期、资源、商品 | observe_pool | observe | B | yes | 化工同类备选，先观察成交。 |
| PENDING_GOLD_STOCK_01 | 黄金股ETF主流产品 | 周期、资源、商品 | observe_pool | observe | A | after_jqdata_code_resolve | 黄金股与黄金ETF风险收益不同，适合观察。 |
| PENDING_STEEL_01 | 钢铁ETF主流产品 | 周期、资源、商品 | research_only | observe | C | after_jqdata_code_resolve | 强周期且波动受政策影响，先研究。 |
| PENDING_BUILDING_MATERIAL_01 | 建材ETF主流产品 | 周期、资源、商品 | research_only | observe | C | after_jqdata_code_resolve | 地产链相关性高，先研究。 |
| PENDING_NEW_MATERIAL_01 | 新材料ETF主流产品 | 周期、资源、商品 | observe_pool | observe | A | after_jqdata_code_resolve | 新材料横跨周期与成长，先观察。 |
| 513330 | 恒生互联网ETF | 跨境与港股 | observe_pool | observe | A | yes | 港股互联网与现有中概/恒科有重叠，默认观察。 |
| 513130 | 恒生科技ETF | 跨境与港股 | observe_pool | observe | B | yes | 恒生科技同类产品，先观察不扩主仓。 |
| 513150 | 港股科技ETF | 跨境与港股 | observe_pool | observe | B | yes | 港股科技同类补充，注意QDII/港股交易日差异。 |
| 513520 | 日经ETF | 跨境与港股 | research_only | observe | B | yes | 跨境分散工具，非A股主策略，研究即可。 |
| 513880 | 日经225ETF | 跨境与港股 | research_only | observe | B | yes | 日经同类，先研究。 |
| 513030 | 德国ETF | 跨境与港股 | research_only | observe | C | yes | 跨境单一市场，非主策略。 |
| PENDING_INDIA_01 | 印度ETF主流产品 | 跨境与港股 | research_only | observe | C | after_jqdata_code_resolve | QDII额度和溢价风险较高，研究即可。 |
| PENDING_EMERGING_01 | 新兴市场ETF主流产品 | 跨境与港股 | research_only | observe | C | after_jqdata_code_resolve | 跨境配置属性强，不适合作为A股主策略交易池。 |
| 511090 | 30年国债ETF | 债券货币 | observe_pool | observe | A | yes | 长久期债券可作为权益风险对冲观察。 |
| 511520 | 政金债ETF | 债券货币 | observe_pool | observe | A | yes | 政金债适合作为防御资产观察。 |
| 511380 | 可转债ETF | 债券货币 | observe_pool | observe | A | yes | 转债兼具股债属性，适合观察而非主仓。 |
| 511030 | 公司债ETF | 债券货币 | observe_pool | observe | B | yes | 信用债需额外关注信用利差环境，默认观察。 |
| PENDING_SHORT_BOND_01 | 短债ETF主流产品 | 债券货币 | observe_pool | observe | B | after_jqdata_code_resolve | 现金替代观察，不进入权益交易池。 |
| PENDING_CREDIT_BOND_01 | 信用债ETF主流产品 | 债券货币 | observe_pool | observe | B | after_jqdata_code_resolve | 信用债扩容较快，先观察口径和流动性。 |
| PENDING_POLICY_BANK_02 | 政金债ETF备选 | 债券货币 | research_only | observe | C | after_jqdata_code_resolve | 债券同类较多，研究备选。 |
| PENDING_CASH_01 | 现金管理ETF备选 | 债券货币 | research_only | observe | C | after_jqdata_code_resolve | 现金管理功能性强，非波段主策略。 |
| PENDING_DIV_QUALITY_02 | 红利质量ETF备选 | 防御、红利、质量 | research_only | observe | B | after_jqdata_code_resolve | 红利质量同类，待JQData确认后按规模和流动性筛选。 |
| PENDING_HK_HIGHDIV_02 | 港股高股息ETF备选 | 防御、红利、质量 | research_only | observe | B | after_jqdata_code_resolve | 港股红利同类，关注溢价和港股交易日。 |
| PENDING_CONSUME_UP_01 | 消费升级ETF主流产品 | 医药与消费升级 | observe_pool | observe | B | after_jqdata_code_resolve | 消费升级与现有消费/食品饮料相关，先观察。 |
| PENDING_SILVER_ECONOMY_01 | 银发经济ETF主流产品 | 医药与消费升级 | research_only | observe | C | after_jqdata_code_resolve | 新主题样本短，研究即可。 |
| PENDING_DIGITAL_ECON_01 | 数字经济ETF主流产品 | 科技与新质生产力 | observe_pool | observe | B | after_jqdata_code_resolve | 与AI、云计算、软件重叠，先观察。 |
| PENDING_ELECTRONICS_01 | 电子ETF主流产品 | 科技与新质生产力 | observe_pool | observe | A | after_jqdata_code_resolve | 电子行业覆盖广，可与半导体/芯片去重。 |
| PENDING_PHOTONICS_01 | 光通信ETF主流产品 | 科技与新质生产力 | research_only | observe | B | after_jqdata_code_resolve | AI算力细分链条，高弹性但波动大。 |
| PENDING_DRONE_01 | 无人机ETF主流产品 | 科技与新质生产力 | research_only | observe | C | after_jqdata_code_resolve | 主题过热风险高，先研究。 |
| PENDING_AUTONOMOUS_01 | 智能汽车ETF主流产品 | 科技与新质生产力 | observe_pool | observe | B | after_jqdata_code_resolve | 和新能源车相关但偏智能化，先观察。 |
| PENDING_LITHIUM_01 | 锂电材料ETF主流产品 | 周期、资源、商品 | observe_pool | observe | B | after_jqdata_code_resolve | 新能源上游周期性强，先观察。 |
| PENDING_RARE_METAL_01 | 稀有金属ETF主流产品 | 周期、资源、商品 | observe_pool | observe | B | after_jqdata_code_resolve | 与稀土/有色相关，后续去重。 |
| PENDING_AGRI_SEED_01 | 种业ETF主流产品 | 周期、资源、商品 | research_only | observe | C | after_jqdata_code_resolve | 农业细分主题，成交和持续性需验证。 |
| PENDING_REIT_01 | 基建REITs ETF主流产品 | 防御、红利、质量 | research_only | observe | C | after_jqdata_code_resolve | 资产属性不同于股票ETF，暂不进主策略。 |
| PENDING_BANK_DIV_01 | 银行红利ETF主流产品 | 防御、红利、质量 | observe_pool | observe | B | after_jqdata_code_resolve | 与银行ETF和红利ETF高度相关，先观察。 |
| PENDING_INSURANCE_01 | 保险ETF主流产品 | 金融地产 | observe_pool | observe | B | after_jqdata_code_resolve | 金融细分补充，和非银/证券去重。 |
| PENDING_BROKER_LEADER_01 | 证券龙头ETF主流产品 | 金融地产 | observe_pool | observe | B | after_jqdata_code_resolve | 券商同质化高，先观察。 |
| PENDING_DIV_LOWVOL_02 | 红利低波ETF备选 | 防御、红利、质量 | research_only | observe | B | after_jqdata_code_resolve | 同类冗余控制，作为替代备选。 |
| PENDING_STATE_OWNED_01 | 国企ETF主流产品 | 防御、红利、质量 | observe_pool | observe | B | after_jqdata_code_resolve | 国企/央企风格与红利相关，先观察。 |
| PENDING_ESG_01 | ESG ETF主流产品 | 防御、红利、质量 | research_only | observe | C | after_jqdata_code_resolve | 因子解释力需单独验证。 |
| PENDING_GREEN_POWER_01 | 绿电ETF主流产品 | 防御、红利、质量 | observe_pool | observe | B | after_jqdata_code_resolve | 电力细分，先观察与电力ETF的替代关系。 |
| PENDING_HK_CONSUME_01 | 港股消费ETF主流产品 | 跨境与港股 | research_only | observe | C | after_jqdata_code_resolve | 跨境消费主题，非A股主策略。 |
| PENDING_SEA_01 | 东南亚ETF主流产品 | 跨境与港股 | research_only | observe | C | after_jqdata_code_resolve | 跨境分散研究，不进入主交易池。 |

## JQData Execution Status

- Current session status: `JQDATA_USER` and `JQDATA_PASSWORD` are not set.
- Therefore JQData `get_all_securities` and historical staging download were not executed in this run.
- Local continuation command:

```bash
export JQDATA_USER='你的聚宽用户名'
export JQDATA_PASSWORD='你的聚宽密码'
python3 scripts/fetch_jqdata_expansion_candidates.py
python3 scripts/download_jqdata_expanded_etfs.py --all-candidates --start 2020-01-01 --end 2026-06-08
python3 scripts/validate_manual_csv.py --all-etf --input-dir data/staging/jqdata_expanded
python3 scripts/import_jqdata_staging.py --all-etf --input-dir data/staging/jqdata_expanded --dry-run
```

- Estimated JQData API calls after code resolution: one candidate-list call plus one history call per six-digit candidate selected.
- BaoStock calls in this expansion plan: 0.
