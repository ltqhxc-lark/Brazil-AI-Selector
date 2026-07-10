# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务精算分析控制器路由 (Analysis Router)
"""

from fastapi import APIRouter, Depends, status
from src.models import Product, Platform
from src.api.schemas import AnalysisRequest, AnalysisResponse
from src.api.dependencies import (
    get_fee_service,
    get_tax_service,
    get_profit_service,
    get_recommendation_strategy
)
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.services.profit_service import ProfitService
from src.strategies.recommendation_strategy import RecommendationStrategy
from src.calculators.shipping_calculator import ShippingCalculator
from src.utils.formatter import format_brl, format_percentage

analysis_router = APIRouter()

# 共享实例化物流计算器 (无状态，线程安全)
_ship_calculator = ShippingCalculator()

@analysis_router.post(
    "/api/v1/analysis",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="对商品上架巴西电商进行一站式财务精算与策略诊断",
    description="传入商品实重、长宽高、到岸成本价及各平台的售价。自动精算并打包返回：销售税、佣金、固费、实付运费、纯利润、盈亏平衡点及爆单营销建议。"
)
async def perform_analysis(
    req: AnalysisRequest,
    fee_service: FeeService = Depends(get_fee_service),
    tax_service: TaxService = Depends(get_tax_service),
    profit_service: ProfitService = Depends(get_profit_service),
    recommendation_strategy: RecommendationStrategy = Depends(get_recommendation_strategy)
) -> AnalysisResponse:
    """
    一站式财务诊断服务控制器 (路由不参与业务逻辑)
    """
    # 1. 将 DTO 请求荷载还原为纯净的领域实体 Domain Models
    prod_req = req.product
    product_entity = Product(
        sku=prod_req.sku,
        name=prod_req.name,
        cost_price_brl=prod_req.cost_price_brl,
        weight_g=prod_req.weight_g,
        length_cm=prod_req.length_cm,
        width_cm=prod_req.width_cm,
        height_cm=prod_req.height_cm,
        category=prod_req.category,
        declared_value_usd=prod_req.declared_value_usd
    )

    plat_req = req.platform
    platform_entity = Platform(
        platform_id=plat_req.platform_id,
        platform_name=plat_req.platform_name,
        selling_price_brl=plat_req.selling_price_brl,
        seller_level=plat_req.seller_level,
        participate_fss=plat_req.participate_fss,
        affiliate_rate=plat_req.affiliate_rate
    )

    # 2. 依次调度底层高阶业务服务核算 (不硬编码)
    fee_analysis = fee_service.get_fee_analysis(product_entity, platform_entity)
    fee_entity = fee_analysis.fee_details

    tax_analysis = tax_service.get_tax_analysis(
        product_entity,
        platform_entity,
        annual_revenue_brl=req.annual_revenue_brl,
        is_cross_border=req.is_cross_border,
        exchange_rate_usd_brl=req.exchange_rate_usd_brl
    )
    tax_fee_brl = tax_analysis.tax_fee_brl

    shipping_fee_brl = _ship_calculator.calculate(product_entity, platform_entity)

    # 3. 编排服务核准综合财务损益 ProfitResult
    profit_result = profit_service.calculate_profitability(
        product=product_entity,
        platform=platform_entity,
        annual_revenue_brl=req.annual_revenue_brl,
        is_cross_border=req.is_cross_border,
        exchange_rate_usd_brl=req.exchange_rate_usd_brl
    )

    # 4. 执行策略中心黄金分析建议 (Recommendation Strategy)
    proposal = recommendation_strategy.generate_integrated_proposal(
        product=product_entity,
        platform=platform_entity,
        fee=fee_entity,
        tax_fee_brl=tax_fee_brl,
        shipping_fee_brl=shipping_fee_brl,
        profit_result=profit_result
    )

    # 5. 拼装打包财务与策略的完整快照响应
    pricing_metrics = proposal.pricing_strategy_report.raw_metrics
    details_snapshot = {
        "platform_fee_details": {
            "commission_fee_brl": fee_entity.commission_fee_brl,
            "fixed_fee_brl": fee_entity.fixed_fee_brl,
            "risk_loss_fee_brl": fee_entity.risk_loss_fee_brl,
            "total_platform_fee_brl": fee_entity.total_fee_brl,
            "fee_ratio_pct": fee_analysis.formatted_fee_ratio
        },
        "tax_details": {
            "tax_regime_name": tax_analysis.tax_regime_name,
            "effective_tax_rate_pct": tax_analysis.formatted_tax_rate,
            "tax_fee_brl": tax_fee_brl
        },
        "shipping_fee_brl": shipping_fee_brl,
        "purchase_cost_brl": product_entity.cost_price_brl,
        "pricing_guidelines": {
            "breakeven_price_brl": float(pricing_metrics["breakeven_price"]),
            "price_at_15_margin_brl": float(pricing_metrics["price_at_15_margin"]),
            "price_at_20_margin_brl": float(pricing_metrics["price_at_20_margin"]),
            "markdown_limit_brl": max(platform_entity.selling_price_brl - float(pricing_metrics["breakeven_price"]), 0.0)
        }
    }

    return AnalysisResponse(
        success=True,
        revenue=profit_result.revenue,
        net_profit=profit_result.net_profit,
        margin=profit_result.margin,
        formatted_margin=format_percentage(profit_result.margin),
        formatted_profit=format_brl(profit_result.net_profit),
        overall_alert_level=proposal.overall_alert_level,
        suggestions=proposal.combined_suggestions_list,
        details=details_snapshot
    )
