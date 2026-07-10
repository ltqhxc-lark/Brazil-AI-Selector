# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 库存控制、进口渠道与物流供应链备货策略引擎
针对巴西漫长的海运报关清关时效（通常60天+）以及跨境合规包裹（15天左右）的特征，结合商品的实重，提供精准的进口渠道推荐（跨境直邮 vs 正式海运）、安全库存水位（Safety Stock）及二次备货周期。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.utils.formatter import format_weight

class InventoryStrategy(BaseStrategy):
    """
    备货与进口渠道优化策略 (SOLID - 供应链职责)
    依据商品的重量梯度和进口完税价格，智能匹配清关链路与补货时效模型。
    """

    @property
    def name(self) -> str:
        return "备货与供应链渠道优化策略"

    def execute(
        self,
        product: Product,
        platform: Platform
    ) -> StrategyResult:
        """
        核算重量、申报价值等指标，推算安全库存及备货链路
        """
        weight = product.weight_g
        val_usd = product.declared_value_usd
        pid = platform.platform_id.lower().strip()
        
        suggestions = []
        alert_level = "green"
        confidence = 0.92
        
        # 1. 核心备货渠道决策 (Heuristic Logic)
        if weight > 3000.0:
            # 重型超规格件
            summary = "大货重件备货决策：【巴西本土海运正式报关 (Importação Formal)】。严禁空运直邮！"
            suggestions.append(
                "1. 【清关通路建议】：由于单品重量高达 {}，跨境空运直邮的尾程邮费将产生惊人溢价。".format(format_weight(weight)) +
                "必须选用本土海运正式报关，将产品以整柜形式运抵圣保罗或圣卡塔琳娜港结关，大幅摊薄单件运费。"
            )
            suggestions.append(
                "2. 【漫长备货周期】：巴西海运正式报关从‘中国工厂生产 -> 货代集港 -> 漫长海运 -> 结关交税 -> 送达本土仓’，"
                "全链路刚性时效长达 60 - 75 天。建议备货提前期（Lead Time）必须设为 75 天，最小起订量（MOQ）设为 500 件。"
            )
            suggestions.append(
                "3. 【本土仓配送】：正式海运结关后，建议分拨转送至圣保罗（SP）保税自营仓或第三方合作仓，以此作为现货发货中心。"
            )
            alert_level = "yellow"
        else:
            # 轻小件
            if val_usd <= 50.00:
                summary = "轻小货跨境备货决策：【Remessa Conforme 跨境空运直邮（零轻库存）】。"
                suggestions.append(
                    f"1. 【清关通路建议】：商品重量轻（仅 {format_weight(weight)}），且海关申报单价在 50 美元黄金起征点以下，"
                    "处于 Remessa Conforme 跨境直邮最核心红利期。建议采用跨境小包从中国深圳/义乌直接空运寄往巴西消费者手中，"
                    "享受‘零巴西压仓轻资本运作’，免除沉重海运资金垫付压力。"
                )
                suggestions.append(
                    "2. 【轻资产补货周期】：中国空运寄送至巴西，在合规计划下全流程一般仅需 12 - 15 天。 "
                    "建议日常备货提前期设为 15 天即可，安全库存水位保持在 30 - 50 件，根据销量变动实现即卖即采。"
                )
            else:
                summary = "高客单价跨境备货决策：【高额关税警告！建议本土海运】。"
                suggestions.append(
                    f"1. 【清关通路建议】：商品申报价值达 {val_usd:.2f} 美元，已越过 50 美元门槛，"
                    "将被惩罚性加征 60% 联邦进口税，综合进口税耗极重。强烈建议停止跨境直邮，"
                    "改为小批量海运正式拼箱进口（LCL），或者降低申报货值（合规前提下）以挤入 50 美元免税区。"
                )
                suggestions.append("2. 【安全库存建议】：本土拼箱进口备货提前期设为 45 天，在圣保罗保税仓库中至少保留 30 天销量现货。")
                alert_level = "yellow"

        # 2. 特定平台仓库选择及曝光加权策略 (美客多 Full 特色)
        if pid == "mercado_livre_brasil":
            suggestions.append(
                "4. 【美客多 Full 仓履约策略】：美客多流量算法对 Full 官方仓（圣保罗等 Full 履约仓）给予 150%+ 的强曝光加权。 "
                "若采用本土现货发货，结关后必须第一优先级向美客多 Full 仓申请库容并进行调拨送入，"
                "Full 仓常备安全库存设定为 15 天销量，以防爆单断货被扣除店铺信誉分（Reputação）。"
            )
        elif pid == "shopee_brasil":
            suggestions.append(
                "4. 【虾皮本地化备货】：若采用本土店铺运营，结关后产品可送入虾皮圣保罗本土的 Coleta 揽收范围仓，"
                "可享有极速发货勋章加成，买家收货时效由 15 天压缩至 3 天，转化率提升翻倍。"
            )

        return StrategyResult(
            strategy_name=self.name,
            decision_summary=summary,
            suggestions=suggestions,
            confidence_score=confidence,
            alert_level=alert_level,
            raw_metrics={
                "weight_g": weight,
                "declared_usd": val_usd,
                "is_heavy_item": weight > 3000.0,
                "moq_suggestion": 500 if weight > 3000.0 else 50,
                "lead_time_days": 75 if weight > 3000.0 else 15
            }
        )
