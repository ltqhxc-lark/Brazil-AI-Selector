# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台适配器包初始化文件
本模块定义了从平台配置文件映射而来的核心结构化业务规则模型 (Dataclasses)，
作为配置文件、数据模型、以及业务服务层之间的桥梁。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ==============================================================================
# 平台业务政策与规则定义 (Platform Business Objects)
# ==============================================================================

@dataclass
class CommissionRule:
    """
    佣金率规则
    """
    base_rate: float                      # 基础佣金率 (如 0.14 代表 14%)
    category_rates: Dict[str, float]      # 细分类目或曝光级别的特定佣金比例 (如 {"classic": 0.12, "premium": 0.17})

@dataclass
class FixedFeeRule:
    """
    固定手续费规则
    """
    threshold_brl: float                  # 低价判定阈值金额 (如 79.00 BRL)
    fee_brl: float                        # 每笔/每件加收的固定交易附加费金额 (如 6.00 BRL)

@dataclass
class WeightRule:
    """
    单个重量段运费规则
    """
    max_weight_g: float                   # 该梯度最大包装重量 (克)
    base_freight_brl: float               # 该重量区间对应的标准运费单价 (BRL)

@dataclass
class DiscountRule:
    """
    卖家等级折扣规则
    """
    level_discounts: Dict[str, float]     # 卖家信誉等级对应的运费折扣比率 (如 {"platinum": 0.50, "normal": 0.10})

@dataclass
class ShippingRule:
    """
    标准运费规则
    """
    free_shipping_threshold_brl: float    # 强制免费配送起征售价阈值 (如 79.00 BRL)
    brackets: List[WeightRule]            # 分段计费重量梯度列表
    discounts: DiscountRule               # 卖家折扣规则

@dataclass
class PromotionRule:
    """
    平台专属优惠/新店铺促销特惠规则
    """
    enabled: bool                         # 该特惠是否激活启用
    promo_rate: float                     # 激活时享受的特殊低佣金率 (如 0.0199 即 1.99%)

@dataclass
class SellerLevel:
    """
    平台卖家信誉等级定义
    """
    level_id: str                         # 等级唯一标志 (如 'platinum', 'gold', 'normal')
    level_name: str                       # 对应的等级展示名称 (如 '铂金领袖', '普通卖家')

@dataclass
class FeePolicy:
    """
    平台手续费与销售佣金整体政策
    """
    commission_rule: CommissionRule        # 比例销售佣金规则
    fixed_fee_rule: FixedFeeRule          # 单笔固定服务费规则

@dataclass
class ShippingPolicy:
    """
    平台物流运费及配送政策
    """
    shipping_rule: ShippingRule           # 标准运费匹配及折扣规则
    loss_and_return_rate: float           # 坏账、退单、纠纷损失储备率 (如 0.02)

@dataclass
class PromotionPolicy:
    """
    新卖家及大促激励政策
    """
    promotion_rule: PromotionRule         # 新卖家冷启动优惠细节

@dataclass
class AffiliatePolicy:
    """
    达人联盟/分销分账政策
    """
    enabled: bool                         # 联盟计划是否开启
    default_rate: float                   # 达人带货默认设定的分账比例 (如 0.10)
    min_rate: float                       # 平台限制的最低分销佣金比率 (如 0.01)

# ==============================================================================
# 导入具体平台的配置解析适配器 (Platform Adapters)
# ==============================================================================
from src.platforms.mercadolivre import MercadoLivreAdapter
from src.platforms.shopee import ShopeeAdapter
from src.platforms.tiktok import TikTokShopAdapter

__all__ = [
    # 核心业务政策对象
    "CommissionRule",
    "FixedFeeRule",
    "WeightRule",
    "DiscountRule",
    "ShippingRule",
    "PromotionRule",
    "SellerLevel",
    "FeePolicy",
    "ShippingPolicy",
    "PromotionPolicy",
    "AffiliatePolicy",
    
    # 平台具体适配器实现
    "MercadoLivreAdapter",
    "ShopeeAdapter",
    "TikTokShopAdapter"
]
