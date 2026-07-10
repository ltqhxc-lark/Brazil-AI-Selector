# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 物流包材与起征线优化决策策略引擎
结合商品的物理重量、体积大小以及平台的运费阈值，给出包括：包材重构减重、体积重压缩、美客多 R$ 79 包邮阈值溢价套利等物流运营优化方向。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.calculators.profit_calculator import ProfitResult
from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.utils.formatter import format_brl, format_percentage

class ShippingStrategy(BaseStrategy):
    """
    物流与包材优化策略 (SOLID - 物流优化职责)
    评估实物物理三维与平台起征点，进行体积重与客单价起征套利精算。
    """

    @property
    def name(self) -> str:
        return "物流成本与包材优化策略"

    def execute(
        self,
        product: Product,
        platform: Platform,
        profit_result: ProfitResult
    ) -> StrategyResult:
        """
        根据商品实重、体积大小及计算出的总物流费用，输出高实操性的物流节流建议
        """
        weight = product.weight_g
        price = platform.selling_price_brl
        ship_cost = profit_result.total_shipping
        pid = platform.platform_id.lower().strip()
        
        suggestions = []
        alert_level = "green"
        confidence = 0.90
        
        # 1. 物理减重与开模体积重评估 (Heuristics)
        volume = product.length_cm * product.width_cm * product.height_cm
        # 巴西常用的体积重折算系数为 6000 (部分为 5000)
        vol_weight_g = (volume / 6000.0) * 1000.0
        
        # 核心决策一句话摘要
        if ship_cost > 18.00:
            summary = f"物流负担偏重：单件实付运费达 {format_brl(ship_cost)}，严重侵蚀后方毛利，亟需进行物流轻量化改善。"
            alert_level = "yellow"
        else:
            summary = "物流支出健康：单件物流成本控制在良性合理区间。"
            alert_level = "green"

        # 2. 启发式减重决策
        if weight >= 1000.0:
            suggestions.append(
                f"1. 【克重压缩跨阶】：该商品包装后重量达 {weight/1000.0:.2f} kg。处于高费率物流阶梯。 "
                "建议：丢弃笨重彩盒改用高回弹牛皮纸袋或气泡袋包材，只要能将总重量压缩至 999g 以下（即降入 1kg 内档），"
                "在美客多上每单可立减 R$ 2.50 - R$ 3.50 的刚性物流开支！"
            )
        elif 300.0 < weight <= 500.0:
            suggestions.append(
                f"1. 【极小重跨阶建议】：当前重量为 {weight:.0f}g。非常接近 300g 这一美客多最便宜物流档。 "
                "建议：缩减包装气泡垫层数，或将原厂重胶纸改为轻量纸质拉链盒，若能压到 300g 内，运费单价可瞬间下降一个台阶！"
            )
        else:
            suggestions.append("1. 【包装克重核准】：当前商品克重符合标准，无显著的越级降阶空间。请继续维持当前材质。")

        # 3. 启发式体积重决策
        if vol_weight_g > weight * 1.5:
            suggestions.append(
                f"2. 【体积重暴险警告】：商品实重仅 {weight:.0f}g，但由尺寸 ({product.length_cm}x{product.width_cm}x{product.height_cm}cm) "
                f"折算出的体积重高达 {vol_weight_g:.0f}g，属于典型的‘轻抛货/买空气发运费’。 "
                "主导方案：将产品内部折叠放置，或者使用真空压缩袋（针对纺织衣服类），将外包装纸箱高度压低 5cm 以上，"
                "可彻底避开体积重惩罚罚款。"
            )

        # 4. 启发式平台线套利 (美客多 R$ 79 特殊起征点)
        if pid == "mercado_livre_brasil":
            if 65.00 <= price < 79.00:
                # 售价处于 65 到 79 的尴尬线 (买家付高额 18+ 运费，严重打压转化)
                suggestions.append(
                    f"3. 【美客多 R$ 79 临界套利】：当前定价 {format_brl(price)} 极为接近免邮红线。 "
                    "由于处于低价档，买家付款时需自己额外支付 R$ 18.00 左右运费（转化率极低）。 "
                    "最佳方案：直接提价至 R$ 79.00 触发买家免邮。虽然你作为卖家需要承担铂金折后运费（约 R$ 11.25），"
                    "但对于买家而言到手价反而从 [70 + 18 = 88] 降到了 79！同时由于提价 9.00 雷亚尔，"
                    "你每单的纯利润通常还会直接增加 R$ 4.00 - R$ 5.00，属于绝妙的双赢套利空间！"
                )
            elif price >= 79.00:
                suggestions.append(
                    "3. 【强制包邮锁利润】：商品售价已越过 R$ 79 强制包邮线。买家享有 100% 免邮，"
                    "请全力在店铺前端详情页首图上打上【Frete Grátis】(免费送达) 的闪亮图标，直接拉升流量转化率。"
                )
        elif pid == "shopee_brasil":
            suggestions.append(
                "3. 【虾皮联营补贴】：虾皮本土店物流均由买家免邮券稀释，请配合在产品标题前缀加上【Cupom de Frete Grátis】"
                "字样，诱使买家在后台领券下单，以借用虾皮官方的流量和物流费用补贴渠道。"
            )

        return StrategyResult(
            strategy_name=self.name,
            decision_summary=summary,
            suggestions=suggestions,
            confidence_score=confidence,
            alert_level=alert_level,
            raw_metrics={
                "physical_weight_g": weight,
                "volumetric_weight_g": vol_weight_g,
                "volume_cm3": volume,
                "is_light_throw": vol_weight_g > weight * 1.5
            }
        )
