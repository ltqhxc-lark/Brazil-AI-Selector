# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台销售参数数据模型
"""

from dataclasses import dataclass

@dataclass
class Platform:
    """
    平台销售参数数据模型 (纯内存数据结构)
    保存商品在特定目标电商平台的销售价格、运费服务模式、卖家信誉等级、以及营销活动参与度等参数。
    """
    platform_id: str             # 平台唯一标识符 (例如: 'mercado_livre_brasil', 'shopee_brasil', 'tiktok_shop_brasil')
    platform_name: str           # 平台的展示名称 (例如: 'Mercado Livre Brasil')
    selling_price_brl: float     # 该商品在平台上的销售单价 (单位: BRL 雷亚尔)
    seller_level: str = "normal" # 卖家账户的信誉或等级 (如 'platinum', 'gold', 'leader', 'normal', 用于美客多运费折扣分级)
    participate_fss: bool = True # 是否参与平台的免邮计划/极速达等付费流量包 (针对 Shopee FSS 6% 或 TikTok 联营补贴等)
    affiliate_rate: float = 0.0  # 联盟营销/达人带货的预设抽拥比例 (典型值 0.0 - 0.30，常用于 TikTok Shop 计算达人溢价)
