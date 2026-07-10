# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 巴西税务精算服务层
协调税务计算引擎，支持本土统一税制和跨境 Remessa Conforme 关税精算。
"""

from dataclasses import dataclass
from src.models.product import Product
from src.models.platform import Platform
from src.calculators.tax_calculator import TaxCalculator
from src.utils.formatter import format_brl, format_percentage

@dataclass
class TaxResult:
    """
    税务精算业务结果集 (Dataclass)
    """
    tax_fee_brl: float               # 最终纳税总金额 (BRL)
    effective_tax_rate: float        # 最终有效税率 (如 0.0532)
    formatted_tax_fee: str           # 格式化纳税额 (如 "R$ 6,38")
    formatted_tax_rate: str          # 格式化税率 (如 "5.32%")
    tax_regime_name: str             # 所属税制名称 (如 "Simples Nacional" 或 "Remessa Conforme")


class TaxService:
    """
    税务业务编排服务 (单一职责)
    衔接 TaxCalculator，针对本土公司销售或跨境包裹报关两种税务场景进行高阶运算和格式化输出。
    """

    def __init__(self, tax_calculator: TaxCalculator = None) -> None:
        # 依赖注入支持
        self._calculator = tax_calculator or TaxCalculator()

    def get_tax_analysis(
        self,
        product: Product,
        platform: Platform,
        annual_revenue_brl: float = 0.0,
        is_cross_border: bool = False,
        exchange_rate_usd_brl: float = 5.0
    ) -> TaxResult:
        """
        核算单笔交易所产生的各项销售或进口环节税金
        
        Args:
            product: 商品数据模型 (Product，获取跨境申报价值)
            platform: 平台销售配置 (Platform，获取本土售价)
            annual_revenue_brl: 商家历史 12 个月累计总销售额 (计算本土阶梯有效税率所需)
            is_cross_border: 是否采用 Remessa Conforme 跨境直邮报关模式
            exchange_rate_usd_brl: 跨境计税时美元兑雷亚尔汇率
            
        Returns:
            TaxResult: 填充完毕的税务分析业务结果
        """
        if is_cross_border:
            # 1. 跨境直邮合规模式 (Remessa Conforme)
            declared_usd = product.declared_value_usd
            # 精算进口税
            tax_brl = self._calculator.calculate_remessa_conforme(declared_usd, exchange_rate_usd_brl)
            
            # 跨境有效税率以：实交税额 / (申报价值折算为雷亚尔后的金额) 衡量
            declared_value_brl = declared_usd * exchange_rate_usd_brl
            rate = round(tax_brl / declared_value_brl, 4) if declared_value_brl > 0.0 else 0.0
            regime_name = "Remessa Conforme 跨境直邮税"
        else:
            # 2. 巴西本土销售模式 (Simples Nacional 商业 Anexo I)
            price = platform.selling_price_brl
            tax_brl = self._calculator.calculate_simples_nacional_tax(price, annual_revenue_brl)
            rate = self._calculator.calculate_simples_nacional_rate(annual_revenue_brl)
            regime_name = "Simples Nacional 统一税制(商业)"

        return TaxResult(
            tax_fee_brl=tax_brl,
            effective_tax_rate=rate,
            formatted_tax_fee=format_brl(tax_brl),
            formatted_tax_rate=format_percentage(rate),
            tax_regime_name=regime_name
        )
