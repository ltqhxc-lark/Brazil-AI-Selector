# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台费用服务层
整合平台费计算器，并输出高阶本地化格式明细 FeeResult
"""

from dataclasses import dataclass
from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.fee_calculator import FeeCalculator
from src.utils.formatter import format_brl, format_percentage

@dataclass
class FeeResult:
    """
    平台费用业务处理结果集 (Dataclass)
    """
    fee_details: Fee                 # 原始费用实体
    formatted_commission: str        # 格式化比例佣金 (如 "R$ 20,40")
    formatted_fixed_fee: str         # 格式化固定交易手续费
    formatted_risk_loss: str         # 格式化风险损失计提
    formatted_total_fee: str         # 格式化平台总扣点费用
    fee_to_revenue_ratio: float      # 平台总费用占售价比例 (例如: 0.165即16.5%)
    formatted_fee_ratio: str         # 格式化后的占比百分比字符串 (如 "16.50%")


class FeeService:
    """
    平台费业务服务 (单一职责)
    管理并调用底层 FeeCalculator 精算引擎，转换并输出带有格式化呈现的业务实体 FeeResult。
    """

    def __init__(self, fee_calculator: FeeCalculator = None) -> None:
        # 支持依赖注入，若未传入则默认实例化
        self._calculator = fee_calculator or FeeCalculator()

    def get_fee_analysis(self, product: Product, platform: Platform) -> FeeResult:
        """
        核算单次交易的平台所有费用，并转化为高度可视化的业务结果
        
        Args:
            product: 商品实体
            platform: 平台销售配置
            
        Returns:
            FeeResult: 包含原始数据和多维本地化展现的结果
        """
        # 调用底层精算引擎
        raw_fee = self._calculator.calculate(product, platform)
        
        revenue = platform.selling_price_brl
        
        # 计算平台扣费占比
        ratio = round(raw_fee.total_fee_brl / revenue, 4) if revenue > 0.0 else 0.0
        
        return FeeResult(
            fee_details=raw_fee,
            formatted_commission=format_brl(raw_fee.commission_fee_brl),
            formatted_fixed_fee=format_brl(raw_fee.fixed_fee_brl),
            formatted_risk_loss=format_brl(raw_fee.risk_loss_fee_brl),
            formatted_total_fee=format_brl(raw_fee.total_fee_brl),
            fee_to_revenue_ratio=ratio,
            formatted_fee_ratio=format_percentage(ratio)
        )
