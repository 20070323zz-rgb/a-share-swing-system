# ETF 类型分层报告

本报告只用于研究分层，不修改交易规则、不改模拟持仓、不生成买卖指令。

## 摘要
- 分类总数：114
- 各类型数量：{'sector': 22, 'commodity_resource': 21, 'broad_index': 17, 'theme': 16, 'qdii': 15, 'unknown': 11, 'bond_cash': 10, 'hot_theme': 2}
- pool 分布：{'trade_pool': 79, 'observe_pool': 32, 'research_only': 3}
- unknown 数量：11
- failed/quarantine/unresolved/excluded 排除类数量：3

## 当前持仓所属类型
| code | name | group | etf_type | holding_profile | exit_sensitivity | news_required | classification_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | 10-30 | medium | medium | 行业ETF关键词 |
| 515880 | 证券公司ETF | 金融地产 | sector | 10-30 | medium | medium | 行业ETF关键词 |
| 515220 | 煤炭ETF | 周期资源 | commodity_resource | 10-45 | medium_high | medium_high | 商品/周期资源关键词 |

## 分类规则说明
- broad_index：宽基指数关键词，如沪深300、中证500、中证1000、创业板50、科创50、中证A500。
- sector：银行、证券、医药、消费、军工、新能源、红利等行业/风格 ETF。
- theme：AI、5G、芯片、半导体、创新药等主题 ETF。
- hot_theme：机器人、低空经济、商业航天、半导体设备、算力等强事件主题。
- bond_cash：国债、短债、货币、现金管理类 ETF。
- qdii：港股、美股、日经、印度等跨境 ETF。
- commodity_resource：黄金、煤炭、有色、铜、油气、稀土等商品/资源相关 ETF。
- unknown：规则无法确定，需人工确认，不强行分类。

## 需要人工确认的 ETF
| code | name | group | pool | status | reason |
| --- | --- | --- | --- | --- | --- |
| 515000 | 科技ETF | 科技成长 | trade_pool |  | ETF但规则无法确定 |
| 600519 | 贵州茅台 | 个股观察 | observe_pool |  | 非ETF或无法确定 |
| 300750 | 宁德时代 | 个股观察 | observe_pool |  | 非ETF或无法确定 |
| 588220 | 科创100ETF基金 | 新宽基与新风格 | trade_pool | imported | ETF但规则无法确定 |
| 588030 | 博时科创100ETF | 新宽基与新风格 | trade_pool | imported | ETF但规则无法确定 |
| 588190 | 银华科创100ETF | 新宽基与新风格 | observe_pool | imported | ETF但规则无法确定 |
| 588120 | 国泰科创100ETF | 新宽基与新风格 | observe_pool | imported | ETF但规则无法确定 |
| 588800 | 华夏科创100ETF | 新宽基与新风格 | observe_pool | imported | ETF但规则无法确定 |
| 159209 | 红利质量ETF | 防御、红利、质量 | trade_pool | failed_validation | excluded status=failed_validation |
| 159119 | 800现金流ETF | 防御、红利、质量 | trade_pool | failed_validation | excluded status=failed_validation |
| 562080 | 300现金流ETF | 防御、红利、质量 | trade_pool | failed_validation | excluded status=failed_validation |

## 安全边界
- 本轮只生成研究分类 sidecar 文件 data/etf_type_classification.csv。
- 不修改 mid_trend / short_swing 核心策略。
- 不修改 paper_positions.csv 或 paper_trades.csv。
- 不接券商 API，不真实下单。