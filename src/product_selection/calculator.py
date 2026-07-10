# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品财务与规格计算器
"""

from decimal import Decimal
from src.models.product import Product
from src.utils.rounding import round_half_up
from src.utils.money import round_to_two

class ProductSelectionCalculator:
    """
    选品相关的财务指标估算与物理特征计算器
    """

    @staticmethod
    def calculate_volumetric_weight_g(product: Product) -> float:
        """
        根据商品的长宽高计算其体积重量 (单位: 克 g)
        巴西邮政(Correios)与大部分物流商通常采用 6000 作为体积折算系数 (L * W * H / 6000 = kg)
        即 L * W * H / 6 = g
        长、宽、高必须严格大于 0。
        仅进行纯数学计算，不读取外部配置、数据库、API，亦不调用服务。
        """
        if product.length_cm <= 0 or product.width_cm <= 0 or product.height_cm <= 0:
            raise ValueError(
                f"商品的长、宽、高尺寸必须严格大于 0，"
                f"当前尺寸为: 长={product.length_cm}, 宽={product.width_cm}, 高={product.height_cm}"
            )
        
        # 纯数学物理计算
        vol_weight = (product.length_cm * product.width_cm * product.height_cm) / 6.0
        return float(round_half_up(Decimal(str(vol_weight)), 2))

    @staticmethod
    def calculate_estimated_selling_price(
        cost_price_brl: float,
        estimated_shipping_brl: float,
        platform_fee_ratio: float,
        tax_ratio: float,
        target_margin_ratio: float
    ) -> float:
        """
        根据反推公式，计算出满足目标利润率的预期最低零售价格。
        
        校验：
            - 所有费率参数必须介于 0 到 1 之间 (含0和1)。
            - 平台费率、税率和目标利润率之和必须严格小于 1.0。
            - 不允许硬编码任何默认比率。
            
        公式推导:
            售价 (S) = 采购价 (C) + 实付运费 (F) + 平台佣金费 (S * platform_fee_ratio) + 税费 (S * tax_ratio) + 目标纯利润 (S * target_margin_ratio)
            S * (1 - platform_fee_ratio - tax_ratio - target_margin_ratio) = C + F
            S = (C + F) / (1 - platform_fee_ratio - tax_ratio - target_margin_ratio)
            
        如果分母 <= 0.05，则使用安全倍数兜底 (采购价与运费之和的2.5倍)。
        """
        # 1. 严格校验费率取值区间
        if not (0 <= platform_fee_ratio <= 1):
            raise ValueError(f"平台费率范围必须在 [0, 1] 之间，当前值为: {platform_fee_ratio}")
        if not (0 <= tax_ratio <= 1):
            raise ValueError(f"税率范围必须在 [0, 1] 之间，当前值为: {tax_ratio}")
        if not (0 <= target_margin_ratio <= 1):
            raise ValueError(f"目标利润率范围必须在 [0, 1] 之间，当前值为: {target_margin_ratio}")
            
        # 2. 严格校验费率和小于 1
        rate_sum = platform_fee_ratio + tax_ratio + target_margin_ratio
        if rate_sum >= 1.0:
            raise ValueError(
                f"平台费率、税率与目标利润率之和必须严格小于 1.0，"
                f"当前各项之和为: {rate_sum} (平台费: {platform_fee_ratio}, 税: {tax_ratio}, 目标利润: {target_margin_ratio})"
            )
            
        # 3. 优先使用高精度 Decimal 进行计算，防止浮点偏差
        dec_cost = Decimal(str(cost_price_brl))
        dec_shipping = Decimal(str(estimated_shipping_brl))
        dec_platform = Decimal(str(platform_fee_ratio))
        dec_tax = Decimal(str(tax_ratio))
        dec_margin = Decimal(str(target_margin_ratio))
        
        denominator = Decimal("1.0") - dec_platform - dec_tax - dec_margin
        cost_sum = dec_cost + dec_shipping
        
        # 4. 兜底策略：如果剩余利润空间不足（分母极小），直接使用 2.5 倍安全毛利价
        if denominator <= Decimal("0.05"):
            estimated_price = cost_sum * Decimal("2.5")
        else:
            estimated_price = cost_sum / denominator
            
        return round_to_two(float(estimated_price))

    @staticmethod
    def calculate_roi(net_profit_brl: float, cost_price_brl: float) -> float:
        """
        计算投资回报率 (ROI)
        ROI = 净利润 / 采购成本
        如果采购成本小于等于 0，抛出 ValueError，不允许静默返回错误结果。
        """
        dec_cost = Decimal(str(cost_price_brl))
        if dec_cost <= Decimal("0"):
            raise ValueError(f"商品采购成本必须严格大于 0，当前为: {cost_price_brl}。无法计算 ROI。")
            
        dec_profit = Decimal(str(net_profit_brl))
        roi = dec_profit / dec_cost
        return float(round_half_up(roi, 4))

    @staticmethod
    def calculate_margin(net_profit_brl: float, revenue_brl: float) -> float:
        """
        计算纯利润率 (Margin)
        Margin = 净利润 / 销售收入
        如果销售收入（售价）小于等于 0，抛出 ValueError。
        """
        dec_rev = Decimal(str(revenue_brl))
        if dec_rev <= Decimal("0"):
            raise ValueError(f"销售收入（售价）必须严格大于 0，当前为: {revenue_brl}。无法计算利润率。")
            
        dec_profit = Decimal(str(net_profit_brl))
        margin = dec_profit / dec_rev
        return float(round_half_up(margin, 4))
