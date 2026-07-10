# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 虾皮巴西本土店配置解析与业务对象转换器
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

class ShopeeAdapter:
    """
    Shopee Brasil (虾皮巴西) 配置解析适配器
    桥接平台原始 YAML 规则与系统业务决策层，实现零硬编码规则读取。
    """

    def __init__(self) -> None:
        # 动态加载并提取 Shopee 专属的规则段落
        all_rules = load_platform_rules()
        self.raw_rules = all_rules.get("shopee_brasil", {})

    def get_fee_policy(self) -> FeePolicy:
        """
        解析生成虾皮佣金扣点及单件固定交易费政策
        """
        raw_comm = self.raw_rules.get("commission", {})
        
        # 组装比例佣金规则：基础 14% + 2% 支付手续费
        comm_rule = CommissionRule(
            base_rate=float(raw_comm.get("base_rate", 0.14)),
            category_rates={
                "base_rate": float(raw_comm.get("base_rate", 0.14)),
                "payment_processing_rate": float(raw_comm.get("payment_processing_rate", 0.02))
            }
        )

        # 组装单件固定交易附加费规则 (每售一件固定扣 BRL 3.00)
        fixed_rule = FixedFeeRule(
            threshold_brl=0.0,  # 虾皮无高低售价判断，属于无差别扣款
            fee_brl=float(raw_comm.get("fixed_fee_per_item_brl", 3.00))
        )

        return FeePolicy(commission_rule=comm_rule, fixed_fee_rule=fixed_rule)

    def get_shipping_policy(self) -> ShippingPolicy:
        """
        解析生成虾皮官方物流策略及损失储备费率
        """
        raw_ship = self.raw_rules.get("shipping", {})
        
        # 虾皮尾程寄送基础运费由买家自付或买家免邮券抵扣，卖家一般不直接承担分段物理运费
        # 故运费阶梯留空
        ship_rule = ShippingRule(
            free_shipping_threshold_brl=0.0,
            brackets=[],
            discounts=DiscountRule(level_discounts={"normal": 0.00})
        )

        # 提取卖家退换货及丢包损耗储备比率 (2%)
        loss_rate = float(raw_ship.get("loss_and_return_rate", 0.02))

        return ShippingPolicy(shipping_rule=ship_rule, loss_and_return_rate=loss_rate)

    def get_affiliate_policy(self) -> AffiliatePolicy:
        """
        解析生成虾皮特有的免邮流量计划 (FSS - Programa de Frete Grátis) 政策。
        我们将免邮增值计划 (FSS 额外 6% 抽税) 作为特种流量/达人政策进行业务输出映射。
        """
        raw_comm = self.raw_rules.get("commission", {})
        fss = raw_comm.get("free_shipping_program", {})

        return AffiliatePolicy(
            enabled=bool(fss.get("participated", True)),
            default_rate=float(fss.get("extra_rate", 0.06)),
            min_rate=float(fss.get("extra_rate", 0.06)) # 强制性固定分账扣点
        )

    def get_seller_levels(self) -> List[SellerLevel]:
        """
        解析生成虾皮支持的卖家等级
        """
        return [SellerLevel(level_id="normal", level_name="普通本土卖家 (Normal)")]

    def get_promotion_policy(self) -> PromotionPolicy:
        """
        生成虾皮大促活动政策 (由于规则表内无特殊大促，输出禁用)
        """
        return PromotionPolicy(
            promotion_rule=PromotionRule(enabled=False, promo_rate=0.0)
        )
