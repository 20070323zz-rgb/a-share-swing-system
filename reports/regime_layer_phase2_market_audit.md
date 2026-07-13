# Regime Layer Phase 2 - Market Audit / Historical Replay

本报告为研究审计，不是执行方案。

## 来源与逻辑
- 来源文件：src/phase4c_alpha_common.py
- 来源函数：market_regime(date, context)
- 状态：['risk_on', 'neutral', 'risk_off']
- 阈值：['risk_on if 510300 ret20 > 2.5%, ret60 > 0, close > ma60', 'risk_on if 159915 ret20 - 510300 ret20 > 2.5% and 510300 ret20 > 0', 'risk_off if 510300 ret20 < -2.5%', 'risk_off if 510300 ret60 < -4%', 'risk_off if 510300 vol20 > 1.8% and ret20 < 0', 'risk_off if 518880 ret20 - 510300 ret20 > 4% and 510300 ret20 < 1%']

## 回放范围
- replay_start_date：2025-05-30
- replay_end_date：2026-07-06
- replay_trading_days：267

## 分布与稳定性
- distribution：{'OFFENSIVE': {'day_count': 154, 'percentage': 0.5767790262172284}, 'NEUTRAL': {'day_count': 55, 'percentage': 0.20599250936329588}, 'DEFENSIVE': {'day_count': 58, 'percentage': 0.21722846441947566}}
- regime_switch_count：44
- average_regime_duration：5.9333
- short_regime_whipsaw_count：19
- needs_future_hysteresis_research：True

## Forward Return 结果
- style summary：{'best_by_regime_10d': {'OFFENSIVE': {'style_profile': 'HIGH_BETA_THEME', 'benchmark_excess_mean_10d': 0.015009, 'sample_count': 298}, 'NEUTRAL': {'style_profile': 'CORE_MID_CAP', 'benchmark_excess_mean_10d': 0.004912, 'sample_count': 150}, 'DEFENSIVE': {'style_profile': 'COMMODITY_CYCLICAL', 'benchmark_excess_mean_10d': 0.008554, 'sample_count': 464}}}
- structural summary：{'best_by_regime_10d': {'OFFENSIVE': {'structural_risk_profile': 'OFFENSIVE', 'benchmark_excess_mean_10d': 0.009375, 'sample_count': 1937}, 'NEUTRAL': {'structural_risk_profile': 'CORE', 'benchmark_excess_mean_10d': 0.000188, 'sample_count': 450}, 'DEFENSIVE': {'structural_risk_profile': 'HIGH_BETA', 'benchmark_excess_mean_10d': 0.00264, 'sample_count': 174}}}
- realized summary：{'best_by_regime_10d': {'OFFENSIVE': {'realized_risk_profile_pit': 'OFFENSIVE', 'benchmark_excess_mean_10d': 0.005664, 'sample_count': 1179}, 'NEUTRAL': {'realized_risk_profile_pit': 'DEFENSIVE', 'benchmark_excess_mean_10d': 0.004341, 'sample_count': 321}, 'DEFENSIVE': {'realized_risk_profile_pit': 'OFFENSIVE', 'benchmark_excess_mean_10d': -0.000275, 'sample_count': 431}}}
- realized risk 分析限制：recomputed point-in-time profile from <=T data; still a research proxy and forward returns are labels only.

## 市场宽度
- breadth：{'generated_at': '2026-07-06 21:55:33', 'rows': [{'normalized_regime': 'DEFENSIVE', 'sample_count': 58, 'buy_breadth_mean': 0.261273, 'buy_breadth_median': 0.230769, 'sell_breadth_mean': 0.59328, 'sell_breadth_median': 0.615385, 'strong_resonance_breadth_mean': 0.248011, 'strong_resonance_breadth_median': 0.205128, 'risk_pressure_mean': 0.492927, 'risk_pressure_median': 0.519231}, {'normalized_regime': 'NEUTRAL', 'sample_count': 55, 'buy_breadth_mean': 0.384149, 'buy_breadth_median': 0.358974, 'sell_breadth_mean': 0.462005, 'sell_breadth_median': 0.461538, 'strong_resonance_breadth_mean': 0.303963, 'strong_resonance_breadth_median': 0.307692, 'risk_pressure_mean': 0.399767, 'risk_pressure_median': 0.371795}, {'normalized_regime': 'OFFENSIVE', 'sample_count': 154, 'buy_breadth_mean': 0.44622, 'buy_breadth_median': 0.435897, 'sell_breadth_mean': 0.299867, 'sell_breadth_median': 0.282051, 'strong_resonance_breadth_mean': 0.313686, 'strong_resonance_breadth_median': 0.307692, 'risk_pressure_mean': 0.244838, 'risk_pressure_median': 0.217949}], 'offensive_buy_breadth_minus_defensive': 0.18494700000000003, 'defensive_sell_breadth_minus_offensive': 0.29341300000000003, 'offensive_buy_breadth_higher': True, 'defensive_sell_breadth_higher': True, 'local_hotspot_misread_risk': False, 'strong_resonance_predictive_value': 'needs forward-return confirmation; breadth is descriptive in this phase', 'research_only': True, 'execution_allowed': False}

## Decision
- existing_regime_is_informative：True
- existing_regime_is_stable：False
- existing_regime_has_whipsaw_problem：True
- style_regime_fit_supported：True
- structural_risk_regime_fit_supported：False
- ready_for_regime_fit_phase：True
- ready_for_preview：False
- ready_for_execution：False

## 安全边界
- research_only=true。
- ready_for_execution=false。
- 未修改 market_regime / BUY ranking / adjusted preview / paper_trade_engine / paper_trades / paper_positions。
- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。