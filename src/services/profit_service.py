# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务利润综合编排服务层
协调 FeeService、TaxService、ShippingCalculator，统一提交给 ProfitCalculator 汇总生成 ProfitResult。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.calculators.shipping_calculator import ShippingCalculator
from src.calculators.profit_calculator import ProfitCalculator, ProfitResult

class ProfitService:
    """
    利润核算编排服务 (单一职责与门面模式 Facade)
    作为整个系统交易损益核算的高层接口，自动调度和协调费用、税务、物流和利润汇总。
    """

    def __init__(
        self,
        fee_service: FeeService = None,
        tax_service: TaxService = None,
        shipping_calculator: ShippingCalculator = None,
        profit_calculator: ProfitCalculator = None
    ) -> None:
        # 支持完整的依赖注入与生命周期管理
        self._fee_service = fee_service or FeeService()
        self._tax_service = tax_service or TaxService()
        self._shipping_calculator = shipping_calculator or ShippingCalculator()
        self._profit_calculator = profit_calculator or ProfitCalculator()

    def calculate_profitability(
        self,
        product: Product,
        platform: Platform,
        annual_revenue_brl: float = 0.0,
        is_cross_border: bool = False,
        exchange_rate_usd_brl: float = 5.0
    ) -> ProfitResult:
        """
        全自动化编排：核算单次交易的费用、税金和物流成本，完成整体财务损益的综合核算。
        
        Args:
            product: 商品数据模型 (Product)
            platform: 平台销售参数 (Platform)
            annual_revenue_brl: 商家历史 12 个月累计总销售额 (计算本土阶梯有效税率所需)
            is_cross_border: 是否采用 Remessa Conforme 跨境直邮报关模式
            exchange_rate_usd_brl: 跨境计税时美元兑雷亚尔汇率
            
        Returns:
            ProfitResult: 标准财务利润精算结果 (包含售价、总税、总费、总物流、纯利及利润率)
        """
        # 1. 精算平台扣点及其他杂费 (获取 Fee 实体)
        fee_res = self._fee_service.get_fee_analysis(product, platform)
        fee_entity = fee_res.fee_details
        
        # 2. 精算应缴税金总额 (本土流转税或进口关税)
        tax_res = self._tax_service.get_tax_analysis(
            product,
            platform,
            annual_revenue_brl=annual_revenue_brl,
            is_cross_border=is_cross_border,
            exchange_rate_usd_brl=exchange_rate_usd_brl
        )
        tax_fee_brl = tax_res.tax_fee_brl
        
        # 3. 精算卖家承担的实际物流运费成本 (BRL)
        shipping_fee_brl = self._shipping_calculator.calculate(product, platform)
        
        # 4. 汇总输入并调用 ProfitCalculator，组装返回最终 ProfitResult 看板
        return self._profit_calculator.calculate(
            product=product,
            platform=platform,
            fee=fee_entity,
            tax_fee_brl=tax_fee_brl,
            shipping_fee_brl=shipping_fee_brl
        )
