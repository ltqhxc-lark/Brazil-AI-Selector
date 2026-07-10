# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 综合商业策略推荐器
作为策略中心的统一协调者 (SOLID - 聚合推荐职责)，
调度定价、物流、推广、库存等所有细分子策略，为中国及本土卖家合成一站式的巴西市场商业运营企划白皮书。
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.profit_calculator import ProfitResult
from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.strategies.marketplace_strategy import MarketplaceStrategy
from src.strategies.pricing_strategy import PricingStrategy
from src.strategies.promotion_strategy import PromotionStrategy
from src.strategies.shipping_strategy import ShippingStrategy
from src.strategies.inventory_strategy import InventoryStrategy

@dataclass
class IntegratedBusinessProposal:
    """
    一站式巴西商业运营综合企划案模型 (Dataclass)
    """
    product_sku: str                    # 被分析商品 SKU
    primary_platform_recommendation: str # 首推平台及决策依据
    overall_alert_level: str            # 综合财务预警级别 ("green", "yellow", "red")
    pricing_strategy_report: StrategyResult # 售价建议报告
    logistics_strategy_report: StrategyResult # 物流及包装优化报告
    marketing_strategy_report: StrategyResult # 广告与促销推广报告
    supply_chain_strategy_report: StrategyResult # 库存与供应链备货报告
    combined_suggestions_list: List[str] # 汇编整合后的极简实操清单列表


class RecommendationStrategy(BaseStrategy):
    """
    综合商业策略推荐器 (策略门面 - Orchestrator / Facade)
    调度和整合全部底层子决策，输出可以直接交付给项目出海高管或大卖家的综合商业白皮书。
    """

    def __init__(
        self,
        marketplace_strategy: MarketplaceStrategy = None,
        pricing_strategy: PricingStrategy = None,
        promotion_strategy: PromotionStrategy = None,
        shipping_strategy: ShippingStrategy = None,
        inventory_strategy: InventoryStrategy = None
    ) -> None:
        # 支持全面的依赖注入，保证扩展和单元测试替身插入
        self._marketplace = marketplace_strategy or MarketplaceStrategy()
        self._pricing = pricing_strategy or PricingStrategy()
        self._promotion = promotion_strategy or PromotionStrategy()
        self._shipping = shipping_strategy or ShippingStrategy()
        self._inventory = inventory_strategy or InventoryStrategy()

    @property
    def name(self) -> str:
        return "一站式巴西出海综合商业推荐策略"

    def execute(self, *args, **kwargs) -> StrategyResult:
        """
        继承基类要求，实现单点调用契约
        """
        raise NotImplementedError("综合推荐策略请调用 generate_integrated_proposal 方法以获取结构化企划书。")

    def generate_integrated_proposal(
        self,
        product: Product,
        platform: Platform,
        fee: Fee,
        tax_fee_brl: float,
        shipping_fee_brl: float,
        profit_result: ProfitResult,
        all_platforms_metrics: Optional[Dict[str, Tuple[Platform, ProfitResult, Fee]]] = None
    ) -> IntegratedBusinessProposal:
        """
        全自动化编排与深度聚合：串联执行五个子策略模块，汇编生成完整的商业企划建议
        
        Args:
            product: 商品数据模型 (Product)
            platform: 平台销售配置 (Platform)
            fee: 精算出的平台费用模型 (Fee)
            tax_fee_brl: 精算出的税金金额 (BRL)
            shipping_fee_brl: 精算出的物理运费 (BRL)
            profit_result: 精算出的利润汇总 (ProfitResult)
            all_platforms_metrics: 可选，用于多平台横向比选的决策数据集
            
        Returns:
            IntegratedBusinessProposal: 一站式巴西商业运营综合企划案
        """
        # 1. 运行多渠道横向比选策略
        metrics = all_platforms_metrics or {platform.platform_id: (platform, profit_result, fee)}
        market_res = self._marketplace.execute(product, metrics)
        
        # 2. 运行逆向定价与利润优化策略
        pricing_res = self._pricing.execute(
            product=product,
            platform=platform,
            fee=fee,
            tax_fee_brl=tax_fee_brl,
            shipping_fee_brl=shipping_fee_brl,
            profit_result=profit_result
        )
        
        # 3. 运行 PPC 广告与联盟分销促销策略
        promo_res = self._promotion.execute(
            product=product,
            platform=platform,
            fee=fee,
            profit_result=profit_result
        )
        
        # 4. 运行物理包材轻量化与体积重起征线优化策略
        ship_res = self._shipping.execute(
            product=product,
            platform=platform,
            profit_result=profit_result
        )
        
        # 5. 运行供应链清关链路与补货控制策略
        inv_res = self._inventory.execute(product, platform)

        # 6. 整合所有子策略的警告等级，决定综合安全级别 (有一处为红即红，有一处为黄即黄，否则为绿)
        sub_alerts = [market_res.alert_level, pricing_res.alert_level, promo_res.alert_level, ship_res.alert_level, inv_res.alert_level]
        if "red" in sub_alerts:
            overall_alert = "red"
        elif "yellow" in sub_alerts:
            overall_alert = "yellow"
        else:
            overall_alert = "green"

        # 7. 过滤汇编所有有价值的实操建议列表
        combined_list = []
        combined_list.extend(pricing_res.suggestions)
        combined_list.extend(ship_res.suggestions)
        combined_list.extend(promo_res.suggestions)
        combined_list.extend(inv_res.suggestions)

        return IntegratedBusinessProposal(
            product_sku=product.sku,
            primary_platform_recommendation=market_res.decision_summary,
            overall_alert_level=overall_alert,
            pricing_strategy_report=pricing_res,
            logistics_strategy_report=ship_res,
            marketing_strategy_report=promo_res,
            supply_chain_strategy_report=inv_res,
            combined_suggestions_list=combined_list
        )
