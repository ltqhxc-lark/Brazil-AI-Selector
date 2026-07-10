# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 商品信息数据模型
"""

from dataclasses import dataclass

@dataclass
class Product:
    """
    商品信息数据模型 (纯内存数据结构)
    用于保存商品的物理属性、采购成本和类目等基础静态数据，不包含任何业务计算逻辑或数据库状态。
    """
    sku: str                     # 商品的唯一识别编码 (SKU)
    name: str                    # 商品的名称 (名称)
    cost_price_brl: float        # 商品在巴西本土的采购成本或离岸到岸成本 (单位: BRL 雷亚尔)
    weight_g: float              # 商品包装后的实重/计费重 (单位: 克 g)
    length_cm: float             # 包装箱的长度尺寸 (单位: 厘米 cm)
    width_cm: float              # 包装箱的宽度尺寸 (单位: 厘米 cm)
    height_cm: float             # 包装箱的高度尺寸 (单位: 厘米 cm)
    category: str                # 商品的分类标签 (如 'electronics', 'cosmetics', 'clothing' 等，用于匹配不同的税率和佣金规则)
    declared_value_usd: float = 0.0 # 跨境直邮模式下的海关申报价值 (单位: USD 美元，选填，主要用于评估跨境关税风险)
