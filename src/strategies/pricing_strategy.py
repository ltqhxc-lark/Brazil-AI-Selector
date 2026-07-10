# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 定价与利润率精算优化策略引擎
依据当前的财务毛利表现，逆向推导保本售价、黄金售价（15% / 20% 净利率）以及在促销/黑五大促中的最大降价让利区间（Markdown Space）。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.profit_calculator import ProfitResult
from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.utils.formatter import format_brl, format_percentage

class PricingStrategy(BaseStrategy):
    """
    售价建议与利润率优化策略 (SOLID - 定价职责)
    利用财务逆向工程模型，帮助卖家逃离低价竞争，科学精准定标最优销售价。
    """

    @property
    def name(self) -> str:
        return "售价建议与利润率优化策略"

    def execute(
        self,
        product: Product,
        platform: Platform,
        fee: Fee,
        tax_fee_brl: float,
        shipping_fee_brl: float,
        profit_result: ProfitResult
    ) -> StrategyResult:
        """
        根据商品当前纯利及费税耗损，逆向推演黄金定价及合理促销让利空间
        """
        price = platform.selling_price_brl
        cost = product.cost_price_brl
        net_profit = profit_result.net_profit
        margin = profit_result.margin
        
        suggestions = []
        alert_level = "green"
        confidence = 0.95
        
        # 1. 测算平台比例扣点率和税率 (比例支出因子 Proportional Rate)
        # commission_rate + tax_rate
        prop_rate = (fee.commission_fee_brl + tax_fee_brl) / price if price > 0.0 else 0.0
        # 避免分母为 0 或因异常比例导致计算异常
        prop_rate = min(prop_rate, 0.50) 
        
        # 2. 测算固定成本因子 (采购成本 + 运费成本 + 平台固定手续费)
        fixed_cost = cost + shipping_fee_brl + fee.fixed_fee_brl

        # === 核心逆向算法（巴西法定企业定价模型）：===
        # 目标售价 = 固定成本 / (1 - 目标利润率 - 比例扣点率)
        def reverse_price(target_margin: float) -> float:
            denominator = 1.0 - target_margin - prop_rate
            if denominator <= 0.10: # 防范分母穿透
                denominator = 0.10
            raw_p = fixed_cost / denominator
            return round(raw_p, 2)

        # 3. 制定针对不同利润档次的具体决策
        if margin < 0.10:
            # 【低毛利评级】
            alert_level = "red" if net_profit <= 0.0 else "yellow"
            p_15 = reverse_price(0.15)
            p_20 = reverse_price(0.20)
            
            if net_profit <= 0.0:
                summary = f"财务亏损告警：当前售价 {format_brl(price)} 无法覆盖成本！保本售价建议提高至 R$ {reverse_price(0.00):.2f} 以上。"
                suggestions.append(f"1. 【紧急提价】：请将该产品售价立即提至 R$ {p_15:.2f} (可获 15% 净利) 或 R$ {p_20:.2f} (可获 20% 净利)。")
            else:
                summary = f"利润垫过薄：当前利润率仅为 {format_percentage(margin)}，抗风险能力脆弱。建议提价进行毛利重组。"
                suggestions.append(f"1. 【防御性调价】：建议将当前价格微调至 R$ {p_15:.2f}，使利润空间进入 15% 安全线。")
                
            suggestions.append(
                "2. 【采购压降】：如果前台市场限价无法提价，你必须向中国供应商砍价，"
                f"将采购进价压低至 {format_brl(price * (1.0 - 0.15 - prop_rate) - fee.fixed_fee_brl - shipping_fee_brl)} 以下，方可在当前售价下实现 15% 净利。"
            )
        else:
            # 【高毛利评级】
            alert_level = "green"
            p_safe_min = reverse_price(0.10) # 降价到 10% 利润率的临界售价
            max_markdown = price - p_safe_min # 最大降价额度
            
            summary = f"财务表现卓越：当前利润率达 {format_percentage(margin)}，属于健康高回报款。"
            suggestions.append(
                f"1. 【大促降价让利预算】：在巴西黑五（Black Friday）或平台大促中，该商品可支持的最大让利额度为 {format_brl(max_markdown)}。 "
                f"即大促促销价最低可设为 R$ {p_safe_min:.2f}，此时仍可保有 10% 的基本防御利润空间。"
            )
            suggestions.append(
                "2. 【广告投放预算】：鉴于当前利润充沛，建议拿出销售额的 5% - 10% 投放在美客多 ADS 或 Shopee 搜索广告中，"
                "加速销量起爆，利用“高利润 + 强投放”打压同类低毛利竞品。"
            )

        # 4. 保本临界售价
        p_breakeven = reverse_price(0.0)
        suggestions.append(f"3. 【保本底线】：该商品的绝对财务保本售价（0利润临界点）为 R$ {p_breakeven:.2f}。低于此价格销售必亏。")

        return StrategyResult(
            strategy_name=self.name,
            decision_summary=summary,
            suggestions=suggestions,
            confidence_score=confidence,
            alert_level=alert_level,
            raw_metrics={
                "breakeven_price": p_breakeven,
                "price_at_15_margin": reverse_price(0.15),
                "price_at_20_margin": reverse_price(0.20),
                "proportional_rate": prop_rate,
                "fixed_cost": fixed_cost
            }
        )
