# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - TikTok Shop 巴西本土店配置解析与业务对象转换器
"""

from typing import List
from src.calculators.fee_calculator import load_platform_rules
from src.platforms import (
    CommissionRule,
    FixedFeeRule,
    WeightRule,
    DiscountRule,
    ShippingRule,
    PromotionRule,
    SellerLevel,
    FeePolicy,
    ShippingPolicy,
    PromotionPolicy,
    AffiliatePolicy
)

class TikTokShopAdapter:
    """
    TikTok Shop Brasil (TikTok 巴西) 配置解析适配器
    桥接平台原始 YAML 规则与系统业务决策层，实现零硬编码规则读取。
    """

    def __init__(self) -> None:
        # 动态加载并提取 TikTok Shop 专属的规则段落
        all_rules = load_platform_rules()
        self.raw_rules = all_rules.get("tiktok_shop_brasil", {})

    def get_fee_policy(self) -> FeePolicy:
        """
        解析生成 TikTok Shop 销售佣金率及订单处理费政策
        """
        raw_comm = self.raw_rules.get("commission", {})
        
        # 比例销售佣金规则 (15%)
        comm_rule = CommissionRule(
            base_rate=float(raw_comm.get("base_rate", 0.15)),
            category_rates={
                "base_rate": float(raw_comm.get("base_rate", 0.15))
            }
        )

        # 单笔订单固定收取处理费 (每单 BRL 1.00)
        fixed_rule = FixedFeeRule(
            threshold_brl=0.0,
            fee_brl=float(raw_comm.get("fixed_handling_fee_brl", 1.00))
        )

        return FeePolicy(commission_rule=comm_rule, fixed_fee_rule=fixed_rule)

    def get_shipping_policy(self) -> ShippingPolicy:
        """
        解析生成 TikTok Shop 的物流运费政策及坏账纠纷损耗储备比率
        """
        raw_ship = self.raw_rules.get("shipping", {})
        
        # TikTok 的运费在 rules 里为比例分摊 co_paying_shipping_rate (1%)，故运费阶梯留空
        ship_rule = ShippingRule(
            free_shipping_threshold_brl=0.0,
            brackets=[],
            discounts=DiscountRule(level_discounts={"normal": 0.00})
        )

        # 提取卖家退换货及丢包损耗储备比率 (1.5%)
        loss_rate = float(raw_ship.get("loss_and_return_rate", 0.015))

        return ShippingPolicy(shipping_rule=ship_rule, loss_and_return_rate=loss_rate)

    def get_affiliate_policy(self) -> AffiliatePolicy:
        """
        解析生成 TikTok 特色达人联盟营销 (Afiliados) 政策
        """
        raw_comm = self.raw_rules.get("commission", {})
        raw_aff = raw_comm.get("affiliate", {})

        return AffiliatePolicy(
            enabled=bool(raw_aff.get("enabled", True)),
            default_rate=float(raw_aff.get("default_rate", 0.10)),
            min_rate=float(raw_aff.get("min_rate", 0.01))
        )

    def get_promotion_policy(self) -> PromotionPolicy:
        """
        解析生成 TikTok Shop 新店铺冷启动激励（前90天/大促特惠佣金）政策
        """
        raw_comm = self.raw_rules.get("commission", {})
        raw_promo = raw_comm.get("new_seller_incentive", {})

        prom_rule = PromotionRule(
            enabled=bool(raw_promo.get("enabled", False)),
            promo_rate=float(raw_promo.get("promo_rate", 0.0199))
        )

        return PromotionPolicy(promotion_rule=prom_rule)

    def get_seller_levels(self) -> List[SellerLevel]:
        """
        解析生成 TikTok Shop 支持的卖家等级
        """
        return [SellerLevel(level_id="normal", level_name="普通本土卖家 (Normal)")]
