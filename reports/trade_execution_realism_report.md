# 模拟交易执行真实化报告

本报告说明当前模拟盘的成交、成本和交易单位假设。它不连接真实交易系统。

## 成本参数
- PAPER_COMMISSION_RATE：0.00012
- PAPER_MIN_COMMISSION：5.00
- PAPER_STAMP_TAX_RATE：0.0
- PAPER_TRANSFER_FEE_RATE：0.0
- PAPER_SLIPPAGE_RATE：0.0003
- PAPER_LOT_SIZE：100
- PAPER_EXECUTION_PRICE_TYPE：close_price_with_slippage

## 买入计算
- raw_close = close
- execution_price = raw_close * (1 + slippage_rate)
- gross_amount = execution_price * quantity
- commission = max(gross_amount * commission_rate, minimum_commission)
- net_cash_change = -(gross_amount + commission + transfer_fee)

## 卖出计算
- execution_price = raw_close * (1 - slippage_rate)
- gross_amount = execution_price * quantity
- commission = max(gross_amount * commission_rate, minimum_commission)
- net_cash_change = gross_amount - commission - stamp_tax - transfer_fee

## 限制
- 当前无分时数据，成交价仍使用收盘价代理并叠加滑点。
- ETF 模拟暂不计印花税。
- 该口径用于模拟学习，不代表真实成交保证。