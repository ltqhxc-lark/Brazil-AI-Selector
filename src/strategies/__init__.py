# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 决策与策略核心模块包
本包整合并外开所有的业务运营决策子策略及综合决策大管家：
1. 决策基类 BaseStrategy 与统一输出模型 StrategyResult
2. 多平台对比推荐策略 MarketplaceStrategy
3. 逆向定价与利润率提存策略 PricingStrategy
4. 广告流量投放与分销比例促销策略 PromotionStrategy
5. 物理包材与美客多 R$ 79 临界点物流优化策略 ShippingStrategy
6. 进口供应链、清关补货与安全库存周期策略 InventoryStrategy
7. 一站式决策总门面 RecommendationStrategy 与企划案模型 IntegratedBusinessProposal
"""

from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.strategies.marketplace_strategy import MarketplaceStrategy
from src.strategies.pricing_strategy import PricingStrategy
from src.strategies.promotion_strategy import PromotionStrategy
from src.strategies.shipping_strategy import ShippingStrategy
from src.strategies.inventory_strategy import InventoryStrategy
from src.strategies.recommendation_strategy import RecommendationStrategy, IntegratedBusinessProposal

__all__ = [
    "BaseStrategy",
    "StrategyResult",
    "MarketplaceStrategy",
    "PricingStrategy",
    "PromotionStrategy",
    "ShippingStrategy",
    "InventoryStrategy",
    "RecommendationStrategy",
    "IntegratedBusinessProposal"
]
