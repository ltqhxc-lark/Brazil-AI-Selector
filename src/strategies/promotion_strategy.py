# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台活动、广告投放与联盟分销促销策略引擎
针对巴西本地消费者的促销习惯和平台的扣点，输出科学的广告（ADS/PPC）预算占比、优惠券让利安全区间以及联盟达人抽佣分账建议。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.profit_calculator import ProfitResult
from src.strategies.base_strategy import BaseStrategy, StrategyResult
from src.utils.formatter import format_brl, format_percentage

class PromotionStrategy(BaseStrategy):
    """
    广告与促销活动推荐策略 (SOLID - 营销促销职责)
    通过利润模型动态评估营销让利底线，规划高回报的 PPC 投放及分销分账比例。
    """

    @property
    def name(self) -> str:
        return "广告投放与活动促销建议策略"

    def execute(
        self,
        product: Product,
        platform: Platform,
        fee: Fee,
        profit_result: ProfitResult
    ) -> StrategyResult:
        """
        结合售价及纯利，核算优惠券发放额度、广告 PPC 投放和达人带货比例
        """
        margin = profit_result.margin
        price = platform.selling_price_brl
        net_profit = profit_result.net_profit
        pid = platform.platform_id.lower().strip()
        
        suggestions = []
        alert_level = "green"
        confidence = 0.88
        
        # 1. 基础广告及促销预算建议算法 (Heuristic Rules)
        if margin < 0.0:
            alert_level = "red"
            summary = "营销红单警告：商品处于净亏损状态，禁止一切降价或付费投放行为！"
            suggestions.append("1. 【禁止付费流量】：必须立刻关停一切美客多 ADS 广告、Shopee 搜索广告或 TikTok 达人定向高佣，仅采用纯免费的自然搜索 SEO 优化。")
            suggestions.append("2. 【禁止无门槛券】：禁止设置任何无门槛优惠券（Cupom de Desconto Sem Limite），防止亏损漏洞进一步扩大。")
        elif 0.0 <= margin < 0.10:
            alert_level = "yellow"
            summary = f"薄利经营评级：当前利润率仅为 {format_percentage(margin)}。营销策略必须保持‘极致克制’。"
            suggestions.append("1. 【严格限额广告】：建议将广告费占比限制在销售额的 2% - 3% 以内（即每单不超过 R$ {:.2f}）。且只能用于针对核心精准搜索关键词的精准匹配，不能跑泛泛的“自动/曝光”模式。".format(price * 0.03))
            suggestions.append("2. 【仅限满减券】：禁止提供直降券。仅允许配置针对高客单价的‘满减券’（如满 R$ 150 减 R$ 10），以此诱导买家多件加购凑单，降低均单手续费。")
        elif 0.10 <= margin < 0.20:
            alert_level = "green"
            summary = f"合格毛利评级：利润率 {format_percentage(margin)} 处于稳定区间。可采纳‘稳健性营销’组合拳。"
            suggestions.append("1. 【稳健广告占比】：可设置销售总营收的 5% - 7% 作为日常广告 PPC 预算（即每单 R$ {:.2f} - R$ {:.2f}），用于拉升新品销量权重。".format(price * 0.05, price * 0.07))
            suggestions.append("2. 【梯度满减特惠】：建议配置平台日常折扣（如 5% 直降折扣），或者在后台参加每月的固定双位数大促（如 9.9, 10.10 等），争取平台大流量曝光入口。")
        else:
            alert_level = "green"
            summary = f"高暴利黄金评级：利润率达 {format_percentage(margin)}，极强盈利厚板，建议采纳‘侵略性扩张’营销方案。"
            suggestions.append("1. 【侵略性广告爆单】：建议果断拿出销售营收的 10% - 12%（即每单 R$ {:.2f} 左右）作为日常广告预算，直接卡位行业搜索主页前三名，打压低利润竞品，抢占自然坑位权重。".format(price * 0.10))
            suggestions.append("2. 【大额新客券】：后台可设置 8% - 10% 的‘新客专属关注礼券（Cupom de Seguidor）’，快速积累店铺粉丝库，实现老客二次回购套利。")

        # 2. 针对平台的特有特色营销建议
        if pid == "tiktok_shop_brasil":
            if margin >= 0.20:
                suggestions.append(
                    "3. 【TikTok 达人裂变】：由于该商品毛利丰厚，强烈建议在 TikTok Shop 联盟后台发布 15% - 18% 的高额‘定向联盟计划（Plano Direcionado）’，"
                    "诱使巴西本地万粉中腰部网红（Creators）帮进行自发短视频/直播带货，快速产生病毒式裂变。"
                )
            else:
                suggestions.append(
                    "3. 【TikTok 达人防守】：由于利润空间较窄，只允许提供平台底线 1% - 3% 的‘店铺通用联盟比率（Plano de Loja）’，"
                    "且将精力转移至官方自播或红人寄样合作，不跑高额带货抽成。"
                )
        elif pid == "shopee_brasil":
            if platform.participate_fss:
                suggestions.append(
                    "3. 【虾皮联营满减】：鉴于你已缴纳了 6% 的免邮（FSS）佣金，必须全力利用虾皮官方提供的‘买家运费补贴’，"
                    "引导买家使用免邮券加购凑单，搭配‘加购优惠 (Leve Mais por Menos)’活动提高笔单价。"
                )

        return StrategyResult(
            strategy_name=self.name,
            decision_summary=summary,
            suggestions=suggestions,
            confidence_score=confidence,
            alert_level=alert_level,
            raw_metrics={
                "margin": margin,
                "suggested_ad_budget_percentage": 0.10 if margin >= 0.20 else (0.05 if margin >= 0.10 else 0.02),
                "suggested_coupon_cap": round(net_profit * 0.3, 2) if net_profit > 0 else 0.0
            }
        )
