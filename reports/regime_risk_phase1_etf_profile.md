# Regime & Risk Allocation Phase 1 - ETF Risk Profile

本轮目标：建立 ETF 自身 Risk Profile / Style Profile，为未来 Regime-Asset Fit 做准备。

## 方法
- risk_score 输入：['volatility_60d', 'beta_60d', 'max_drawdown_120d_abs', 'downside_volatility_60d', 'down_capture_60d', 'concentration_style_penalty']
- risk_score 权重：{'volatility_60d': 0.25, 'beta_60d': 0.2, 'max_drawdown_120d_abs': 0.2, 'downside_volatility_60d': 0.15, 'down_capture_60d': 0.1, 'concentration_style_penalty': 0.1}
- risk_profile 分层：按全池 risk_score 分位数切为 DEFENSIVE / CORE / BALANCED / OFFENSIVE / HIGH_BETA。
- style_profile：使用 watchlist group、type、ETF 名称、宽基/主题/债券/QDII 规则生成。

## 当前结果
- ETF 总数：183
- 有效画像数量：183
- 数据不足数量：0
- risk_profile 分布：{'CORE': 37, 'HIGH_BETA': 37, 'OFFENSIVE': 37, 'BALANCED': 36, 'DEFENSIVE': 36}
- style_profile 分布：{'COMMODITY_CYCLICAL': 35, 'QDII_OBSERVATION': 24, 'HIGH_BETA_THEME': 23, 'SECTOR_DEFENSIVE': 21, 'DIVIDEND': 20, 'CORE_MID_CAP': 16, 'BOND': 15, 'CORE_LARGE_CAP': 11, 'GROWTH_THEME': 10, 'SECTOR_CYCLICAL': 7, 'GROWTH_BROAD': 1}

## 当前持仓风险画像
- 加权 risk_score：51.3118
- 平均 risk_score：46.9035
- 是否偏进攻：True
- 是否缺少 CORE/DEFENSIVE：False

## BUY Ranking 风险结构
- Top 10 平均 risk_score：55.0820
- OFFENSIVE/HIGH_BETA 占比：40.00%
- 是否偏进攻：False

## 一致性与下一阶段
- high_beta 一致数量：1
- broad_base 冲突：0
- 当前是否足以做 Regime Fit：False
- 下一阶段需要先观察 risk_profile 稳定性，再做 preview-only 的 Regime Fit。

## 安全边界
- research_only=true。
- ready_for_execution=false。
- 未修改 BUY ranking / market_regime / paper_trade_engine / paper_trades / paper_positions。
- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。