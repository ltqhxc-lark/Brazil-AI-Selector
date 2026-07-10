# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 美客多巴西本土店配置解析与业务对象转换器
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

class MercadoLivreAdapter:
    """
    Mercado Livre Brasil (美客多巴西) 配置解析适配器
    桥接平台原始 YAML 规则与系统业务决策层，实现零硬编码规则读取。
    """

    def __init__(self) -> None:
        # 动态加载并提取 ML 专属的规则段落
        all_rules = load_platform_rules()
        self.raw_rules = all_rules.get("mercado_livre_brasil", {})

    def get_fee_policy(self) -> FeePolicy:
        """
        解析生成美客多佣金扣点及固定附加费政策
        """
        raw_rates = self.raw_rules.get("commission_rates", {})
        # 基础佣金默认为经典 Classic 曝光率
        comm_rule = CommissionRule(
            base_rate=float(raw_rates.get("classic", 0.12)),
            category_rates={
                "classic": float(raw_rates.get("classic", 0.12)),
                "premium": float(raw_rates.get("premium", 0.17))
            }
        )

        raw_fixed = self.raw_rules.get("fixed_fee", {})
        fixed_rule = FixedFeeRule(
            threshold_brl=float(raw_fixed.get("threshold_brl", 79.00)),
            fee_brl=float(raw_fixed.get("fee_brl", 6.00))
        )

        return FeePolicy(commission_rule=comm_rule, fixed_fee_rule=fixed_rule)

    def get_shipping_policy(self) -> ShippingPolicy:
        """
        解析生成美客多官方物流 (Mercado Envios Full) 政策，含运费重量梯度和信誉折扣
        """
        raw_ship = self.raw_rules.get("shipping", {})
        
        # 1. 组装重量分段 brackets
        brackets_list: List[WeightRule] = []
        for b in raw_ship.get("brackets", []):
            brackets_list.append(
                WeightRule(
                    max_weight_g=float(b["max_weight_g"]),
                    base_freight_brl=float(b["base_freight_brl"])
                )
            )

        # 2. 组装折扣规则
        raw_discounts = raw_ship.get("seller_discounts", {})
        disc_rule = DiscountRule(
            level_discounts={k: float(v) for k, v in raw_discounts.items()}
        )

        # 3. 生成物流核心规则
        ship_rule = ShippingRule(
            free_shipping_threshold_brl=float(raw_ship.get("free_shipping_threshold_brl", 79.00)),
            brackets=brackets_list,
            discounts=disc_rule
        )

        # 4. 统计合并坏账退换货风险率 (3% 退款 + 0.5% 丢件 = 3.5%)
        raw_risk = self.raw_rules.get("risk_factors", {})
        loss_rate = float(raw_risk.get("return_rate", 0.03)) + float(raw_risk.get("loss_rate", 0.005))

        return ShippingPolicy(shipping_rule=ship_rule, loss_and_return_rate=loss_rate)

    def get_seller_levels(self) -> List[SellerLevel]:
        """
        解析生成美客多支持的五档官方卖家等级映射
        """
        raw_ship = self.raw_rules.get("shipping", {})
        raw_discounts = raw_ship.get("seller_discounts", {})
        
        # 汉化名描述字典
        display_names = {
            "platinum": "铂金领袖 (Platinum)",
            "gold": "黄金领袖 (Gold)",
            "leader": "绿标领袖 (Leader)",
            "normal": "黄标普通卖家 (Normal)",
            "red": "橙红标低信誉卖家 (Red)"
        }

        levels: List[SellerLevel] = []
        for lvl_id in raw_discounts.keys():
            levels.append(
                SellerLevel(
                    level_id=lvl_id,
                    level_name=display_names.get(lvl_id, f"信誉等级: {lvl_id}")
                )
            )
        return levels

    def get_promotion_policy(self) -> PromotionPolicy:
        """
        生成美客多促销特惠政策 (美客多暂无新商家默认让利活动，输出禁用)
        """
        return PromotionPolicy(
            promotion_rule=PromotionRule(enabled=False, promo_rate=0.0)
        )

    def get_affiliate_policy(self) -> AffiliatePolicy:
        """
        生成美客多联盟营销政策 (美客多暂无内置达人带货，输出禁用)
        """
        return AffiliatePolicy(enabled=False, default_rate=0.0, min_rate=0.0)
