# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务与税务核心精算包
本包导出了所有的模块化计算器，包括：
1. 平台费用精算器 FeeCalculator
2. 物流运费精算器 ShippingCalculator
3. 巴西税务精算器 TaxCalculator
4. 综合财务分析与利润精算器 ProfitCalculator, 以及利润分析面板 ProfitResult
"""

from src.calculators.fee_calculator import FeeCalculator
from src.calculators.tax_calculator import TaxCalculator
from src.calculators.shipping_calculator import ShippingCalculator
from src.calculators.profit_calculator import ProfitCalculator, ProfitResult

__all__ = [
    "FeeCalculator",
    "TaxCalculator",
    "ShippingCalculator",
    "ProfitCalculator",
    "ProfitResult"
]
