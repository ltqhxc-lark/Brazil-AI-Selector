# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 物流运费精算器
负责针对三大平台本土店铺的物流策略，计算卖家需要承担的实际运费。
包括美客多的强制起征包邮阶梯及卖家信誉等级运费折算，以及虾皮和 TikTok 的运费补贴分摊。
"""

from src.calculators.fee_calculator import load_platform_rules
from src.models.product import Product
from src.models.platform import Platform
from src.utils.money import round_to_two, calculate_percentage

class ShippingCalculator:
    """
    物流运费计算器 (SOLID - 单一职责)
    精算交易中卖家应承担的物流、包邮补贴与运费成本。
    """

    def __init__(self) -> None:
        # 一次性加载 platform_rules.yaml
        self.rules = load_platform_rules()

    def calculate(self, product: Product, platform: Platform) -> float:
        """
        计算单笔交易卖家需要实付的物流总费用 (BRL)
        
        Args:
            product: 商品数据模型 (Product)
            platform: 平台销售参数 (Platform)
            
        Returns:
            float: 卖家实际承担的物流费用 (BRL，保留两位小数)
        """
        pid = platform.platform_id.lower().strip()
        
        if pid == "mercado_livre_brasil":
            return self._calculate_mercado_livre(product, platform)
        elif pid == "shopee_brasil":
            return self._calculate_shopee(product, platform)
        elif pid == "tiktok_shop_brasil":
            return self._calculate_tiktok(product, platform)
        else:
            return 0.0

    def _calculate_mercado_livre(self, product: Product, platform: Platform) -> float:
        """
        美客多巴西官方物流 (Mercado Envios Full) 运费计算
        
        规则：
            1. 当售价 >= 79.00 BRL 时，买家免邮，卖家强制分摊运费。
            2. 运费计算：根据商品包装重量 (weight_g) 匹配运费阶梯。
            3. 折扣：卖家根据信誉等级 (seller_level) 享受 10% 至 50% 不等的折扣。
            4. 当售价 < 79.00 BRL 时，买家自理运费，卖家运费支出为 0.0。
        """
        cfg = self.rules["mercado_livre_brasil"]["shipping"]
        price = platform.selling_price_brl
        
        # 判断是否达到免邮门槛
        if price < float(cfg["free_shipping_threshold_brl"]):
            return 0.0
            
        # 匹配重量梯度 (找出第一个 max_weight_g >= product.weight_g)
        weight = product.weight_g
        brackets = cfg["brackets"]
        base_freight = float(brackets[-1]["base_freight_brl"]) # 默认最后一档兜底
        
        for b in brackets:
            if weight <= float(b["max_weight_g"]):
                base_freight = float(b["base_freight_brl"])
                break
                
        # 匹配卖家信誉折扣
        level = platform.seller_level.lower().strip()
        discounts = cfg["seller_discounts"]
        discount_rate = float(discounts.get(level, discounts["normal"]))
        
        # 卖家实付运费 = 基准运费 * (1 - 折扣率)
        seller_freight = base_freight * (1.0 - discount_rate)
        return round_to_two(seller_freight)

    def _calculate_shopee(self, product: Product, platform: Platform) -> float:
        """
        虾皮巴西官方物流 (Shopee Envios) 运费计算
        
        本土店铺下，常规运费均由买家直接支付或由买家使用平台的免邮券 (FSS) 抵扣。
        除非卖家在后台主动设置了“卖家运费补贴（Frete Grátis Personalizado）”。
        """
        cfg = self.rules["shopee_brasil"]["shipping"]
        # 直接读取配置文件中的卖家主动提供的运费补贴金额 (默认 0.0)
        subsidy = float(cfg.get("seller_shipping_subsidy_brl", 0.0))
        return round_to_two(subsidy)

    def _calculate_tiktok(self, product: Product, platform: Platform) -> float:
        """
        TikTok Shop 巴西官方物流运费分摊计算
        
        TikTok Shop 对参与平台免邮或联合促售活动的商家，常采用“销售额扣点分摊运费”或“固定运费分摊”的模式。
        """
        cfg = self.rules["tiktok_shop_brasil"]["shipping"]
        price = platform.selling_price_brl
        
        # 卖家联合运费分摊比例 (默认 1% 的销售额)
        co_paying_rate = float(cfg.get("co_paying_shipping_rate", 0.01))
        co_paying_fee = calculate_percentage(price, co_paying_rate)
        
        # 叠加每单固定分摊费 (默认 0.0 BRL)
        flat_fee = float(cfg.get("flat_co_paying_fee_brl", 0.0))
        
        total_shipping_fee = co_paying_fee + flat_fee
        return round_to_two(total_shipping_fee)
