# Market Regime 来源审计

本报告只审计现有逻辑，不修改 market_regime。

- primary source：src/phase4c_alpha_common.py
- function：market_regime(date, context)
- raw states：['risk_on', 'neutral', 'risk_off']
- normalized mapping：{'risk_on': 'OFFENSIVE', 'neutral': 'NEUTRAL', 'risk_off': 'DEFENSIVE'}
- market_state source：src/market_state.py / build_market_rows / _summary_row / _state_and_range

## 输入与阈值
- 输入特征：510300 ret_20 ret_60 volatility_20 close_vs_ma60；159915 ret_20 minus 510300 ret_20；518880 ret_20 minus 510300 ret_20
- 阈值：risk_on if 510300 ret20 > 2.5%, ret60 > 0, close > ma60；risk_on if 159915 ret20 - 510300 ret20 > 2.5% and 510300 ret20 > 0；risk_off if 510300 ret20 < -2.5%；risk_off if 510300 ret60 < -4%；risk_off if 510300 vol20 > 1.8% and ret20 < 0；risk_off if 518880 ret20 - 510300 ret20 > 4% and 510300 ret20 < 1%
- 是否读取未来数据：No direct future data in phase4c_alpha_common.market_regime; it uses row_on_date(df, date), which selects <= date.
- 是否只看单一指数：High. 510300 is the main anchor; 159915 and 518880 are auxiliary.
- 是否使用 ETF pool breadth：False
- 是否使用 BUY/WATCH/SELL 数量：False
- 是否使用 high_beta/growth strength：Growth only through 159915 relative strength; no ETF pool high_beta breadth.
- 是否使用风险压力：Gold relative strength and 510300 vol/drawdown proxy only.
- 逻辑复杂度：simple rule-based proxy

## 读取 market_regime 的模块
- app/backend/readers.py
- app/frontend/src/pages/Research.jsx
- dashboard/build_dashboard.py
- src/backtest_diagnostics.py
- src/etf_risk_profile.py
- src/market_regime_replay.py
- src/missed_opportunity_tracker.py
- src/persistence_breakout_shadow.py
- src/phase4c_alpha_common.py
- src/shadow_observation_weekly.py

## 执行层影响
- No direct paper_trade_engine dependency found in this audit; Phase 4C/shadow research reads market_regime.
- research_only=true
- execution_allowed=false