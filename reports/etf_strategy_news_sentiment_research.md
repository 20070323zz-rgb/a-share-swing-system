# ETF 双周期策略与新闻情绪因子研究报告

生成时间：2026-06-10  
权限边界：L2 联网数据权限  
用途：交给 Main/GPT 做策略方案评估。  
重要声明：本报告是研究材料，不是最终执行方案；不修改交易策略、不修改仓位规则、不修改模拟持仓、不生成真实交易指令。

## 1. 摘要结论

1. 当前系统的 `mid_trend + short_swing + BUY ranking` 框架方向合理，属于趋势跟随、动量轮动和横截面 ETF 轮动的组合。类似思想在 ETF 动量/行业轮动研究中常见，例如 Quantpedia 的行业 ETF 动量轮动研究、CXO Advisory 的 ETF momentum 组合、Fidelity 对 sector rotation 的解释。但这只能说明“方向合理”，不能直接说明“盈利能力强”。盈利能力必须继续通过本项目本地样本、扩池后历史、模拟盘和滚动回测验证。证据来源：[Quantpedia Sector Momentum](https://quantpedia.com/strategies/sector-momentum-rotational-system)、[CXO SACEMS](https://www.cxoadvisory.com/momentum-strategy/)、[Fidelity Sector Rotation](https://www.fidelity.com/learning-center/trading-investing/markets-sectors/intro-sector-rotation-strats)。

2. 20-60 天持有期不应无差别套用到所有 ETF。宽基 ETF 可以继续以 20-60 天为主；行业 ETF 更适合 10-30 天作为主观察周期；高热度主题 ETF 更适合 5-20 天，强事件主题可压缩到 3-10 天；债券/货币 ETF 更适合 30-90 天；QDII 需要 10-45 天并额外检查汇率、溢价、海外交易日和数据滞后。这个分层结论部分有动量/轮动资料支持，具体到 A 股主题 ETF 的天数区间仍属于研究假设，需要回测验证。

3. 行业/主题 ETF 相比宽基更容易受政策预期、资金风格、热点退潮、拥挤交易、新闻兑现和高波动影响。持有 20-60 天可能在主题退潮时暴露过久，尤其是券商、科技、5G、创新药、机器人、低空经济、商业航天这类“叙事驱动 + 高弹性”品种。证据来源：ETF 发行商对集中主题/行业 ETF 风险的提醒，以及 sector momentum 近年 alpha 衰减研究。[Vanguard ETF strategy](https://www.nl.vanguard/professional/events-education/etfs/strategy)、[Quantpedia: How to Improve ETF Sector Momentum](https://quantpedia.com/how-to-improve-etf-sector-momentum/)。

4. 新闻/情绪因子有必要研究，但初期不建议直接作为 BUY 主因子。更稳妥的定位是：解释层 + 风险过滤器 + 小权重辅助降权。新闻情绪在短期更有效，尤其是 1-2 天到数周；行业情绪对行业 ETF 或 sector ETF 有研究基础，但噪声、重复新闻、滞后新闻、小作文和追涨新闻风险很高。证据来源：Heston & Sinha 对新闻和收益预测的研究、CFA Institute 摘要、RavenPack 行业轮动情绪研究、Sector News Sentiment Indices 研究。[CFA Institute: News vs. Sentiment](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/news-vs-sentiment-predicting-stock-returns-from-news-stories)、[Federal Reserve PDF](https://www.federalreserve.gov/econresdata/feds/2016/files/2016048pap.pdf)、[RavenPack sector rotation](https://www.ravenpack.com/blog/sector-rotation-gains-more-traction-with-sentiment)、[Sector News Sentiment Indices](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3080318)。

5. 当前持仓 515220 煤炭 ETF、512800 银行 ETF、515880 证券公司 ETF 集中在周期资源和金融地产，组合缺少宽基和防守 ETF 平衡。515880 已有 data_health caution，应至少禁止加仓并进入 REVIEW 状态；是否减仓只能由模拟盘规则和后续复核决定，本报告不生成交易指令。

## 2. 主流 ETF 交易逻辑

### 2.1 长期配置 / 定投 / 核心资产配置

长期配置逻辑强调低成本、分散化、资产配置和长期持有。Vanguard 认为 ETF 具备分散、低成本、盘中交易等特征；其 ETF portfolio 资料强调可用少量宽基 ETF 构建高度分散组合。这个逻辑适合宽基、债券、全球资产和长期核心仓，不适合用来解释短期主题炒作。[Vanguard ETF overview](https://investor.vanguard.com/investment-products/etfs)、[Vanguard ETF portfolio](https://investor.vanguard.com/investment-products/etfs/etf-investment-options)。

对本项目含义：宽基 ETF 和债券/货币 ETF 可承担稳定器角色；行业/主题 ETF 不应全部按长期配置处理。

### 2.2 趋势跟随 trend following

趋势跟随通常用均线、动量、突破、相对强弱等方式识别趋势延续。ETF 适合趋势系统，因为单个 ETF 已经分散了个股风险，且比个股停牌/黑天鹅风险低。当前 `mid_trend` 使用中期趋势，属于主流趋势跟随思想。

对本项目含义：`mid_trend` 作为 70% 主策略合理，但不同 ETF 的趋势稳定性不同。宽基趋势更平滑，主题 ETF 趋势更脆弱。

### 2.3 动量轮动 momentum rotation

动量轮动比较不同资产或 ETF 的近期表现，持有排名靠前者。CXO Advisory 的 SACEMS 使用月度再平衡，在一组 ETF 中选择近期总回报靠前资产；Quantpedia 的资产类别轮动和行业 ETF 动量也属于这类框架。[CXO SACEMS](https://www.cxoadvisory.com/momentum-strategy/)、[Quantpedia Asset Class Momentum](https://quantpedia.com/strategies/asset-class-momentum-rotational-system)、[Quantpedia Sector Momentum](https://quantpedia.com/strategies/sector-momentum-rotational-system)。

对本项目含义：BUY ranking 本质上是 ETF 横截面轮动评分，合理；但需要防止只看价格导致追高和同质化集中。

### 2.4 行业轮动 sector rotation

行业轮动基于经济周期、盈利周期、利率、政策、估值、资金流和行业景气度切换。Fidelity 将 sector rotation 描述为随经济周期阶段在行业间切换；State Street/SSGA 也有 sector rotation ETF model portfolio 类资料，强调行业机会和风险缓释。[Fidelity Sector Rotation](https://www.fidelity.com/learning-center/trading-investing/markets-sectors/intro-sector-rotation-strats)、[State Street sector rotation ETF model portfolio PDF](https://www.ssga.com/uk/en_gb/intermediary/library-content/assets/pdf/emea/capabilities/sector-rotation-etf-model-portfolio.pdf)。

对本项目含义：行业 ETF 不应只看 K 线，还应至少加入行业景气、资金、政策/新闻解释层。

### 2.5 主题 ETF 交易

主题 ETF 通常集中于 AI、机器人、低空经济、创新药、商业航天、半导体设备等叙事。Vanguard 的 ETF strategy 资料提醒，某些 ETF 策略可能带来集中仓位，需要权衡额外风险。[Vanguard ETF strategy](https://www.nl.vanguard/professional/events-education/etfs/strategy)。

对本项目含义：主题 ETF 适合 observe_pool/research_only 起步，交易周期应更短，止盈/止损更紧，必须有热度衰减和风险过滤。

### 2.6 均值回归 / 超跌反弹

均值回归适合超跌反弹、区间震荡、红利低波、部分宽基或防御 ETF，但不应与趋势跟随混在同一个 BUY 规则里。行业主题在下跌趋势中“越跌越买”风险很高。

对本项目含义：如果未来做均值回归，应作为独立实验策略，而不是直接改 mid_trend。

### 2.7 事件驱动 / 新闻情绪驱动

事件驱动常见于政策变化、产业催化、财报、并购重组、利率变化、监管政策、行业突发事件。金融新闻情绪研究显示新闻对短期收益有预测信息，但效果与源、处理方法、时间尺度相关。[CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/news-vs-sentiment-predicting-stock-returns-from-news-stories)、[Tetlock media sentiment PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf)。

对本项目含义：新闻情绪适合做主题 ETF 的风险过滤和解释，不适合初期直接做 BUY 主因子。

### 2.8 风险平价 / 波动率控制 / 仓位控制

ETF 组合常见风险控制包括波动率目标、最大回撤、单品种上限、行业集中度、现金比例、风险平价。当前本项目使用总仓位、单只 ETF 上限、最多持有数量，方向正确；下一步可研究按 ETF 类型动态止损和主题集中度限制。

### 2.9 ETF 执行交易逻辑

ETF 发行商和交易最佳实践资料通常强调使用限价单、关注 bid-ask spread、避免开盘和收盘极端时段、考虑流动性、必要时使用 VWAP/TWAP 或分批执行。Vanguard ETF trading guidance 和 iShares/BlackRock ETF 资料都强调 ETF 在二级市场按市价交易，可能产生 premium/discount 和 bid-ask spread；Mackenzie ETF trading tips 也强调限价单等执行规则。[Vanguard ETF trading guidance PDF](https://www.ch.vanguard/content/dam/intl/europe/documents/en/etf-trading-guidance-and-best-practices-eu-en-pro.pdf)、[iShares ETF prospectus example](https://www.ishares.com/us/literature/prospectus/p-ishares-us-etf-trust-focused-7-31.pdf)、[Mackenzie ETF trading best practices PDF](https://www.mackenzieinvestments.com/content/dam/final/corporate/mackenzie/docs/etfs/mm-etf-trading-tips-en.pdf)。

对本项目含义：当前模拟执行窗口“次日 14:30-14:50、不追开盘、不 14:55 后追单、close_proxy”是合理的学习型执行规则；真实交易仍永久禁止。

## 3. 当前双周期模型合理性评估

### 3.1 符合主流思想的部分

- `mid_trend`：符合趋势跟随。
- `short_swing`：符合短期动量/波段。
- `BUY ranking`：符合横截面 ETF 动量轮动。
- 流动性、风险、数据质量：符合 ETF 交易实际约束。
- 双周期共振：相当于趋势确认，可降低单周期噪声。

证据支持：ETF 动量轮动和 sector momentum 研究确实存在；行业 ETF momentum 在历史样本中被研究过，但也有资料提示简单 sector momentum 的 alpha 可能衰减。[Quantpedia Sector Momentum](https://quantpedia.com/strategies/sector-momentum-rotational-system)、[Quantpedia: How to Improve Sector Momentum](https://quantpedia.com/how-to-improve-etf-sector-momentum/)、[CXO Simple Sector ETF Momentum](https://www.cxoadvisory.com/momentum-investing/simple-sector-etf-momentum-strategy-performance/)。

### 3.2 目前过于价格化的部分

当前模型主要依赖价格趋势、短期收益、流动性、风险和数据质量。缺少：

- 行业资金流；
- 行业景气/估值；
- 政策事件；
- 新闻热度和情绪；
- ETF 溢价率/折价率；
- QDII 海外交易日和汇率影响；
- 主题拥挤度或热度衰减。

这意味着模型可能抓到价格已反映的趋势，但对“趋势为何存在、是否即将退潮”判断不足。

### 3.3 潜在盈利来源

1. 趋势延续：上涨 ETF 短期继续上涨。
2. 横截面强弱：资金在行业和主题之间轮动。
3. 风险过滤：避开流动性差、数据质量差、波动异常标的。
4. 执行纪律：避免开盘追高和尾盘追单。
5. 小组合集中：持有 1-3 只强信号 ETF，提高信号暴露。

### 3.4 容易失效的环境

1. 全市场快速风格切换，昨日强势变成今日杀跌。
2. 主题 ETF 高位新闻兑现，高开低走。
3. 宽基震荡无趋势，趋势系统频繁假突破。
4. 行业 ETF 被政策或突发新闻逆转。
5. 低流动性 ETF 出现跳价、折溢价扩大。
6. 扩池后同质化严重，排名看似分散但实际暴露同一风险。

结论：当前模型可被评价为“方向合理、结构清晰、值得模拟验证”，不能评价为“盈利能力已强”。

## 4. ETF 类型与建议持有周期

下表中的“证据/假设”用于区分资料支持和本项目研究推导。

| ETF 类型 | 例子 | 建议持有周期 | 依据性质 | 说明 |
| --- | --- | ---: | --- | --- |
| 宽基 ETF | 沪深300、中证500、中证1000、创业板50、科创50 | 20-60 天 | 有动量/趋势资料支持 + 项目假设 | 宽基噪声低于主题，适合 mid_trend 主导 |
| 行业 ETF | 银行、证券、煤炭、医药、消费、军工、新能源 | 10-30 天 | 研究假设为主 | 行业受政策、资金、周期切换影响较快 |
| 主题 ETF | 机器人、低空经济、AI、算力、半导体设备、创新药、5G | 5-20 天 | 研究假设为主 | 热点退潮快，适合 short_swing 更高权重 |
| 强事件主题 | 印花税、并购重组、政策发布、产业大会 | 3-10 天 | 研究假设 | 新闻驱动更短，需热度衰减 |
| 债券/货币 ETF | 国债、政金债、货币、短债 | 30-90 天 | 有资产属性支持 | 波动低，适合现金管理和防守观察 |
| QDII ETF | 恒生科技、纳指、日经、印度等 | 10-45 天 | 资料支持 + 项目假设 | 需考虑海外交易日、汇率、折溢价、时差 |
| 商品/资源 ETF | 黄金、煤炭、有色、铜、油气 | 10-45 天 | 研究假设 | 商品周期强，但事件冲击大 |

主流 ETF 动量/资产轮动常用月度再平衡或多月回看；CXO SACEMS 是月度配置，Quantpedia asset/sector momentum 也是典型轮动框架。A 股主题 ETF 的 3-20 天建议不是直接来自单一权威结论，而是基于主题波动、新闻催化和 A 股资金风格切换的研究假设，需要用本地回测验证。

## 5. 行业/主题 ETF 快速变化风险

行业/主题 ETF 的主要风险：

1. 政策预期变化：利好预期提前交易，政策落地后反而兑现。
2. 资金风格切换：A 股短期主题资金切换快，强势板块可能快速失血。
3. 热点退潮：机器人、低空、AI、商业航天等容易从“主线”变“旧题材”。
4. 拥挤交易：同类 ETF 和成分股拥挤导致回撤放大。
5. 高波动：主题成分股 beta 高，ETF 仍可能大幅波动。
6. 高开低走：新闻刺激开盘冲高，收盘回落。
7. 新闻兑现：发布会、会议、政策细则后，资金兑现。
8. 估值修复后回落：短期涨幅兑现后缺少基本面接力。
9. 基本面不支持主题炒作：订单、业绩、现金流没有跟上。
10. A 股特殊风险：涨跌停、资金抱团、交易拥挤、短线小作文、政策预期反复。

研究建议：

- 行业/主题 ETF 持有 20-60 天可能比短周期更危险，尤其是纯主题和事件驱动品种。
- 主题 ETF 应更快止盈/止损。
- 应研究热度衰减规则，例如新闻热度峰值后 3-5 个交易日无资金确认则降权。
- 应研究 rank_score 连续下降退出，例如连续 3 日下降且跌破阈值进入 REVIEW。
- 应研究 short_swing 从 BUY 转 WATCH 时减仓或禁止加仓。
- 主题 ETF 可设置更紧止损，例如 4%-6%；行业 ETF 5%-8%；宽基可维持 7%-10%。这些阈值是研究假设，不是上线规则。

## 6. 新闻与行业情绪是否有必要引入

### 6.1 证据总结

Heston & Sinha 的研究显示，日频新闻对收益的预测通常偏短，日新闻约 1-2 天，周频新闻可预测更长周期；正面新闻反应较快，负面新闻可能延迟反应。CFA Institute 摘要和 Federal Reserve 工作论文均支持这个方向。[CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/news-vs-sentiment-predicting-stock-returns-from-news-stories)、[Federal Reserve PDF](https://www.federalreserve.gov/econresdata/feds/2016/files/2016048pap.pdf)。

Tetlock 的媒体情绪研究说明媒体悲观情绪与市场活动存在关系，是新闻情绪研究的经典基础。[Tetlock PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf)。

RavenPack 和 sector news sentiment index 研究表明，行业层面的新闻情绪可以用于 sector rotation 或与行业 ETF 存在关系，但这些多基于成熟市场和专业新闻数据源。[RavenPack](https://www.ravenpack.com/blog/sector-rotation-gains-more-traction-with-sentiment)、[Sector News Sentiment Indices](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3080318)。

### 6.2 对本项目的结论

新闻情绪有必要研究，但初期不应做 BUY 主因子。

建议定位：

1. 解释层：解释为何行业/主题 ETF 上榜。
2. 风险过滤器：负面新闻、监管、数据异常、过热退潮时禁止加仓。
3. 小权重辅助：最多 5%-10% rank_score 辅助，且只在回测验证后加入。
4. 触发复核：新闻冲突、重复小作文、政策不确定时进入 REVIEW。

不建议：

- 直接因为新闻热度买入。
- 直接用单条新闻改变仓位。
- 把实时快讯当成稳定 alpha。
- 把社交媒体热度不加过滤地纳入 BUY。

## 7. 可用新闻/情绪数据源

| 数据源 | 免费/账号 | 稳定性 | 历史数据 | 自动化适合度 | A 股 ETF 主题适配 | L2 边界适配 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tushare Pro 新闻快讯 `news` | 需权限，新闻资讯单独权限 | 较规范 | 文档称 6 年以上 | 高 | 高 | 适合，只读 | 需 token，必须环境变量，不写日志。[Tushare news](https://tushare.pro/document/2?doc_id=143)、[权限说明](https://tushare.pro/document/1?doc_id=290) |
| Tushare `major_news` | 需权限 | 较规范 | 文档称 8 年以上 | 高 | 中高 | 适合，只读 | 长篇新闻适合离线情绪。[major_news](https://tushare.pro/document/2?doc_id=195) |
| 东方财富快讯 | 免费网页 | 中等，可能反爬 | 有页面，历史不确定 | 中 | 高 | 可只读，但谨慎 | 适合人工/半自动观察，不建议高频抓取。[东财快讯](https://kuaixun.eastmoney.com/) |
| 东方财富板块资金流 | 免费网页 | 中等 | 页面展示为主 | 中 | 高 | 可只读 | 适合行业资金确认。[东财板块资金流](https://data.eastmoney.com/bkzj/) |
| 财联社电报 | 免费网页/可能商业服务 | 中等 | 历史有限 | 中 | 高 | 可只读 | 适合政策/产业快讯人工复核。[财联社电报](https://m.cls.cn/) |
| 同花顺财经 | 免费网页/商业限制 | 中等 | 不确定 | 中低 | 高 | 可只读 | 适合题材热度，但需注意版权和反爬 |
| 证券时报/上证报/中证报 | 免费网页/商业限制 | 高 | 有历史但接口不统一 | 中 | 高 | 可只读 | 更适合政策确认和权威新闻 |
| 巨潮资讯 / CNINFO | 免费网页 + 数据服务 | 高 | 公告历史好 | 中高 | 中 | 可只读 | 更适合公告/基金公告，不是快讯情绪主源。[巨潮](https://www.cninfo.com.cn/)、[CNINFO Data Service](https://webapi.cninfo.com.cn/) |
| AKShare | 免费开源 | 接口变动较多 | 依接口而定 | 中 | 中高 | 可只读 | 有行业板块、概念板块、资金流、人气等数据字典，但本机网络稳定性需验证。[AKShare 数据字典](https://akshare.akfamily.xyz/data/index.html) |
| a-stock-data | GitHub/社区项目 | 待评估 | 待评估 | 中低 | 可能适合辅助 | 可只读 | 可作为题材/资金流辅助候选，需审计数据来源和许可 |
| QVeris | Agent/检索工具层 | 取决于接入 | 取决于源 | 中 | 适合后期研究助手 | 可只读 | 不建议作为主行情/新闻数据库，可做后期 Agent 工具层 |
| RSS/API 组合 | 部分免费 | 取决于源 | 取决于源 | 中 | 中 | 可只读 | 适合低频每日新闻摘要 |

初期最适合：Tushare Pro 新闻权限如果可用，用于历史研究；东方财富/财联社/三大证券报用于人工复核和关键词库校验；AKShare 资金流/板块数据用于辅助确认，但不作为唯一信号源。

## 8. ETF 主题关键词库草案

设计原则：

- 正面关键词：产业景气、政策支持、涨价、订单、出海、盈利改善。
- 负面关键词：监管、降价、亏损、需求下滑、风险暴露。
- 政策关键词：国务院、发改委、央行、证监会、工信部、医保局、能源局等。
- 风险关键词：调查、处罚、限制、反垄断、制裁、退坡、爆雷。
- 事件关键词：大会、发布会、财报、政策细则、价格调整、库存变化。
- 减少误匹配：必须同时命中行业核心词 + 事件词；对泛词如“科技”“创新”“金融”降低权重；按来源去重；同一新闻标题相似度去重。

### 8.1 煤炭 ETF

- 正面：煤炭、动力煤、焦煤、煤价、能源保供、火电、山西煤炭、产能、进口煤、库存下降、长协价。
- 负面：煤价下跌、库存高企、需求疲弱、限产放松、进口煤冲击、事故停产。
- 政策：能源局、发改委、保供稳价、煤电联营。
- 风险：煤矿事故、安监、环保限产、价格管控。

### 8.2 银行 ETF

- 正面：银行、息差企稳、降准、信贷、资产质量改善、拨备、高股息、红利、中特估。
- 负面：净息差收窄、不良率、房地产风险、地方债、资本充足率压力。
- 政策：央行、金融监管总局、LPR、存款利率、房地产融资协调。
- 风险：地产链违约、拨备不足、息差继续下行。

### 8.3 证券公司 ETF

- 正面：券商、证券、成交额、两融、IPO、并购重组、资本市场改革、印花税、牛市预期、权益市场活跃。
- 负面：成交额萎缩、IPO 放缓、再融资收紧、市场低迷、监管处罚。
- 政策：证监会、资本市场改革、并购六条、交易制度优化。
- 风险：高开低走、政策兑现、牛市预期落空。

### 8.4 科技 ETF

- 正面：半导体、AI、算力、光模块、通信、国产替代、芯片、软件、信创、数据中心。
- 负面：出口限制、制裁、库存周期、砍单、估值过高、业绩不及预期。
- 政策：工信部、数字中国、国产替代、人工智能行动计划。
- 风险：海外制裁、主题拥挤、AI 兑现、业绩空窗。

### 8.5 5G ETF

- 正面：5G、通信设备、基站、运营商、光模块、算力网络、数据中心、6G、光通信。
- 负面：资本开支下降、价格战、订单延后、海外限制。
- 政策：工信部、通信基础设施、算力网络。
- 风险：光模块拥挤、AI 链退潮、运营商 capex 下滑。

### 8.6 创新药 / 医药

- 正面：创新药、医保谈判、CXO、出海、FDA、临床、医疗器械、BD 授权、集采缓和。
- 负面：集采降价、临床失败、FDA 拒批、医保控费、CXO 订单下滑。
- 政策：医保局、药监局、创新药支持、审评审批。
- 风险：单品种临床失败、政策压价、出海预期落空。

### 8.7 机器人 / 低空经济 / 商业航天

- 正面：机器人、人形机器人、工业母机、低空经济、eVTOL、无人机、商业航天、卫星、订单、量产。
- 负面：量产推迟、商业化不及预期、监管空域、订单证伪、估值过高。
- 政策：低空经济试点、商业航天政策、智能制造。
- 风险：概念炒作、产业链兑现慢、高位退潮。

### 8.8 红利 / 高股息

- 正面：红利、高股息、央企、中特估、现金流、分红、低波、稳定现金流。
- 负面：分红不及预期、利率上行、周期利润下滑、股息陷阱。
- 政策：市值管理、央企考核、分红监管。
- 风险：拥挤交易、估值修复后收益下降。

## 9. 情绪评分框架草案

初版不建议直接上线，只建议离线研究。

```text
industry_sentiment_score =
  新闻热度分
+ 正面关键词分
- 负面关键词分
+ 政策催化分
+ 产业事件分
+ 资金/成交确认分
- 风险事件分
- 情绪衰减惩罚
- 重复新闻惩罚
+ 来源权重调整
```

建议输出离散标签，而不是直接输出交易分数：

- positive：正面事件 + 资金确认；
- neutral：有新闻但方向不明确；
- negative：负面行业/政策/资金消息；
- noisy：重复新闻、小作文、多源冲突；
- event_risk：重大政策/监管/高位兑现风险。

建议用途：

1. BUY 降权：negative/noisy 时降低 rank_score。
2. 禁止加仓：event_risk 或 data_health caution 时禁止加仓。
3. 触发复核：正负新闻冲突时 REVIEW。
4. RISK_REDUCE 辅助：负面新闻连续出现且 short_swing 转弱时进入减仓复核。
5. 解释层：展示“为什么某行业上榜/降权”。

暂不建议作为 BUY 主分，因为新闻数据清洗、历史回测和噪声控制尚未完成。

## 10. 当前模拟持仓适配评估

### 10.1 515220 煤炭 ETF

- 类型：周期资源 / 商品价格敏感行业 ETF。
- 建议研究持有周期：10-45 天；如果是煤价/能源保供事件驱动，则 5-20 天更合适。
- 关注新闻：煤价、动力煤、焦煤、库存、进口煤、火电需求、山西产能、安监、能源保供、发改委价格政策。
- 退出/减仓触发研究：煤价转弱、库存高企、政策压价、rank_score 连续下降、short_swing 从 BUY 转 WATCH、跌破止损。
- 研究判断：不适合完全按宽基 20-60 天机械持有；应加入商品价格和政策新闻观察。

### 10.2 512800 银行 ETF

- 类型：金融地产 / 高股息 / 宏观利率敏感行业 ETF。
- 建议研究持有周期：20-60 天可接受；若由降准/降息/地产政策短期催化，则 10-30 天更合适。
- 关注新闻：息差、降准、降息、信贷投放、地产融资、资产质量、拨备、不良率、高股息、红利。
- 退出/减仓触发研究：息差继续收窄、地产信用风险升温、银行股高股息拥挤退潮、rank_score 下降、mid_trend 转弱。
- 研究判断：银行 ETF 比券商更适合中期趋势，但仍需宏观政策过滤。

### 10.3 515880 证券公司 ETF

- 类型：金融地产 / 高 beta / 市场成交额敏感行业 ETF。
- 建议研究持有周期：5-20 天或 10-30 天；不宜机械持有 20-60 天。
- 关注新闻：券商、成交额、两融、IPO、并购重组、资本市场改革、印花税、牛市预期。
- 退出/减仓触发研究：成交额回落、政策预期兑现、指数高开低走、short_swing 转 WATCH、rank_score 连续下降。
- data_health：当前有 caution，原因是单日涨跌幅极端异常。研究建议：禁止加仓；进入 REVIEW；后续若连续异常或价格口径问题未解除，应不作为核心加仓对象。
- 研究判断：证券 ETF 对情绪和成交额高度敏感，新闻/资金/成交确认比宽基更重要。

### 10.4 组合层面

当前组合集中于周期资源和金融地产，缺少宽基和防御 ETF 平衡。研究建议：后续模拟盘可以评估宽基或防御 ETF 作为平衡器，但不能自动修改仓位或直接下单。

## 11. 对项目下一步优化的候选方案

以下是候选研究方案，不是上线方案。

### 方案 A：ETF 类型分层持有周期

- 宽基：20-60 天；
- 行业：10-30 天；
- 主题：5-20 天；
- 强事件主题：3-10 天；
- 债券/货币：30-90 天；
- QDII：10-45 天 + 汇率/溢价/海外交易日检查。

优点：符合 ETF 类型差异。  
风险：需要大量回测，避免过拟合。

### 方案 B：rank_score 连续下降复核

- 连续 3 个交易日下降，进入 WATCH；
- 跌破阈值，进入 REVIEW；
- 对主题 ETF 阈值更严格。

优点：减少热点退潮回吐。  
风险：震荡中可能频繁退出。

### 方案 C：short_swing 退出辅助

- mid_trend BUY 但 short_swing 转 WATCH：禁止加仓或减半；
- short_swing SELL/REVIEW 且 rank_score 下滑：触发复核。

优点：适合主题和行业 ETF。  
风险：可能过早退出大趋势。

### 方案 D：新闻情绪风险过滤器

- negative/noisy/event_risk：禁止加仓；
- positive 只能解释或小幅加分；
- 连续负面 + 技术转弱：RISK_REDUCE 复核。

优点：适合 A 股主题 ETF。  
风险：新闻噪声高，数据源许可和稳定性需验证。

### 方案 E：行业资金确认

- 引入板块资金流、成交额、两融、ETF 成交额作为确认。
- 无资金确认的新闻热度不加分。

优点：降低“只有新闻没有钱”的误判。  
风险：资金流数据质量和可得性需验证。

## 12. 需要 Main/GPT 进一步判断的问题

1. 是否同意 ETF 按“宽基/行业/主题/债券/QDII/商品”分层设置观察周期？
2. 是否同意行业/主题 ETF 将 `short_swing` 权重提高，而不是改 mid_trend 核心规则？
3. 是否同意新闻情绪初期只做解释层和风险过滤器？
4. 是否同意 515880 在 data_health caution 未解除前禁止加仓？
5. 是否需要把行业/主题 ETF 的止损从统一 ETF 止损改为类型化止损？如果是，应先回测。
6. 是否需要建立“主题热度衰减”报告，而不是直接进 BUY ranking？
7. 是否要优先接入 Tushare 新闻权限，还是先用公开新闻 + 手工验证？
8. 是否要将当前组合加入“金融/周期集中度”警戒线？

## 13. 引用来源与链接

ETF 配置与执行：

- Vanguard ETF overview: https://investor.vanguard.com/investment-products/etfs
- Vanguard ETF portfolio: https://investor.vanguard.com/investment-products/etfs/etf-investment-options
- Vanguard ETF strategy: https://www.nl.vanguard/professional/events-education/etfs/strategy
- Vanguard ETF trading guidance PDF: https://www.ch.vanguard/content/dam/intl/europe/documents/en/etf-trading-guidance-and-best-practices-eu-en-pro.pdf
- iShares ETF prospectus example: https://www.ishares.com/us/literature/prospectus/p-ishares-us-etf-trust-focused-7-31.pdf
- Mackenzie ETF trading best practices PDF: https://www.mackenzieinvestments.com/content/dam/final/corporate/mackenzie/docs/etfs/mm-etf-trading-tips-en.pdf

动量、行业轮动与 ETF 轮动：

- Quantpedia Sector Momentum: https://quantpedia.com/strategies/sector-momentum-rotational-system
- Quantpedia Asset Class Momentum: https://quantpedia.com/strategies/asset-class-momentum-rotational-system
- Quantpedia How to Improve ETF Sector Momentum: https://quantpedia.com/how-to-improve-etf-sector-momentum/
- CXO Advisory SACEMS: https://www.cxoadvisory.com/momentum-strategy/
- CXO Simple Sector ETF Momentum: https://www.cxoadvisory.com/momentum-investing/simple-sector-etf-momentum-strategy-performance/
- Fidelity Sector Rotation: https://www.fidelity.com/learning-center/trading-investing/markets-sectors/intro-sector-rotation-strats
- State Street sector rotation ETF model portfolio PDF: https://www.ssga.com/uk/en_gb/intermediary/library-content/assets/pdf/emea/capabilities/sector-rotation-etf-model-portfolio.pdf

新闻情绪研究：

- CFA Institute, News vs. Sentiment: https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/news-vs-sentiment-predicting-stock-returns-from-news-stories
- Federal Reserve PDF, News vs. Sentiment: https://www.federalreserve.gov/econresdata/feds/2016/files/2016048pap.pdf
- Tetlock media sentiment PDF: https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf
- RavenPack sector rotation sentiment: https://www.ravenpack.com/blog/sector-rotation-gains-more-traction-with-sentiment
- Sector News Sentiment Indices: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3080318
- QuantConnect sector rotation news sentiment: https://www.quantconnect.com/research/15309/sector-rotation-based-on-news-sentiment/

A 股新闻/资金/公告数据源：

- Tushare news: https://tushare.pro/document/2?doc_id=143
- Tushare major_news: https://tushare.pro/document/2?doc_id=195
- Tushare 权限说明: https://tushare.pro/document/1?doc_id=290
- 东方财富快讯: https://kuaixun.eastmoney.com/
- 东方财富板块资金流: https://data.eastmoney.com/bkzj/
- 财联社电报: https://m.cls.cn/
- 巨潮资讯: https://www.cninfo.com.cn/
- CNINFO Data Service: https://webapi.cninfo.com.cn/
- AKShare 数据字典: https://akshare.akfamily.xyz/data/index.html
- AKShare 股票数据: https://akshare.akfamily.xyz/data/stock/stock.html

## 14. 证据支持与研究假设边界

证据支持较强：

- ETF 适合长期配置、分散化、低成本工具；
- ETF 存在趋势/动量/轮动类策略研究；
- 行业/sector rotation 是主流投资框架之一；
- ETF 执行应关注流动性、bid-ask、premium/discount、限价和执行时段；
- 新闻情绪对短期收益有研究证据，尤其是短期和行业层面。

研究假设，需要本项目验证：

- A 股宽基 20-60 天、行业 10-30 天、主题 5-20 天的具体周期分层；
- 主题 ETF 是否应设置 4%-6% 更紧止损；
- rank_score 连续下降退出是否优于固定止损；
- short_swing 转 WATCH 是否应触发减仓；
- 新闻情绪作为 rank_score 5%-10% 小权重是否有效；
- 主题热度衰减窗口应为 3 日、5 日还是 10 日；
- 515880 data_health caution 对模拟仓是否应降低仓位。

最终建议：先让 Main/GPT 基于本报告做方案评估，再决定是否进入离线回测。任何新闻/情绪因子上线前，必须先完成数据源稳定性验证、历史样本构建、去重、标签定义、回测和模拟盘观察。
