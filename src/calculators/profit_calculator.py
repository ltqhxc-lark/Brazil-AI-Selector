# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务利润综合分析精算器
将计算出来的平台手续费（Fee）、本地流转税/进口税（Tax）以及实付运费（Shipping）进行聚合。
精算出单笔交易的净利润与净利润率，输出标准 ProfitResult 财务面板。
"""

from dataclasses import dataclass
from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.utils.money import round_to_two

@dataclass
class ProfitResult:
    """
    利润精算报告结果模型 (纯内存数据结构)
    存储并展示某件商品在特定平台售出后的核心利润看板数据。
    """
    revenue: float                 # 平台销售总收入 (单位: BRL 雷亚尔)
    total_fee: float               # 承担的平台交易/佣金/增值等总费用 (单位: BRL 雷亚尔)
    total_tax: float               # 本次销售产生的全部本土流转税或进口总税费 (单位: BRL 雷亚尔)
    total_shipping: float          # 卖家实际支出的物流成本总运费 (单位: BRL 雷亚尔)
    net_profit: float              # 扣除采购进货成本、平台费用、税费、物流后的纯利润 (单位: BRL 雷亚尔)
    margin: float                  # 最终纯利润率 (例: 0.1852 代表 18.52% 的纯利润)


class ProfitCalculator:
    """
    利润综合计算器 (SOLID - 合成聚合层)
    整合 FeeCalculator、TaxCalculator 与 ShippingCalculator 的结果，完成企业终极损益核算。
    """

    def calculate(
        self,
        product: Product,
        platform: Platform,
        fee: Fee,
        tax_fee_brl: float,
        shipping_fee_brl: float
    ) -> ProfitResult:
        """
        根据商品进价、销售售价及三大计算维度的输出，合成利润分析面板
        
        计算公式：
            1. 净利润 = 销售收入 - 采购成本 - 平台费用 - 纳税总额 - 承担总运费
            2. 纯利润率 = 净利润 / 销售收入
            
        Args:
            product: 商品数据模型 (Product，获取采购成本 cost_price_brl)
            platform: 平台销售参数 (Platform，获取销售售价 selling_price_brl)
            fee: 已精算出的平台手续费模型 (Fee)
            tax_fee_brl: 已精算出的全部税额 (BRL)
            shipping_fee_brl: 已精算出的实付物流运费 (BRL)
            
        Returns:
            ProfitResult: 标准财务利润精算结果
        """
        revenue = platform.selling_price_brl
        cost = product.cost_price_brl
        
        # 1. 汇总所有费用 (平台费、税金、运费)
        total_fee = fee.total_fee_brl
        total_tax = tax_fee_brl
        total_shipping = shipping_fee_brl
        
        # 2. 精算纯利润
        # net_profit = revenue - cost - total_fee - total_tax - total_shipping
        net_profit = round_to_two(revenue - cost - total_fee - total_tax - total_shipping)
        
        # 3. 计算净利润率
        if revenue > 0.0:
            margin = round(net_profit / revenue, 4)  # 精确保留 4 位小数，如 0.2561 代表 25.61%
        else:
            margin = 0.0
            
        return ProfitResult(
            revenue=revenue,
            total_fee=total_fee,
            total_tax=total_tax,
            total_shipping=total_shipping,
            net_profit=net_profit,
            margin=margin
        )
