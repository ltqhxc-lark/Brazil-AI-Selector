# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务与成本深度分析服务层
无需调用大模型 AI 或数据库，通过纯数学财务模型和预设 Heuristic（启发式规则），
自动对精算结果进行深度诊断，生成全方位的利润、成本、利润率及费用占比分析报告。
"""

from dataclasses import dataclass
from src.models.product import Product
from src.models.platform import Platform
from src.calculators.profit_calculator import ProfitResult
from src.utils.formatter import format_percentage, format_brl

@dataclass
class AnalysisResult:
    """
    财务深度诊断与分析报告结果模型 (Dataclass)
    """
    product_sku: str                    # 被分析商品 SKU
    platform_name: str                  # 目标销售平台名称
    revenue_brl: float                  # 销售总营收 (BRL)
    purchase_cost_brl: float            # 采购产品成本 (BRL)
    purchase_cost_ratio: float          # 采购成本占比
    
    total_fee_brl: float                # 平台总手续费 (BRL)
    fee_ratio: float                    # 平台费占比
    
    total_tax_brl: float                # 销售或进口总税费 (BRL)
    tax_ratio: float                    # 税费占比
    
    total_shipping_brl: float           # 实付物流成本 (BRL)
    shipping_ratio: float               # 物流费占比
    
    net_profit_brl: float               # 精算纯利润金额 (BRL)
    profit_margin: float                # 净利润率 (例: 0.25 即 25%)
    
    # 四大核心维度诊断诊断文书
    profit_analysis: str                # 1. 利润诊断综合文书
    cost_analysis: str                  # 2. 产品与供应链成本分析
    margin_analysis: str                # 3. 利润率水平安全评级及提升建议
    fee_proportion_analysis: str        # 4. 费用占比结构分析与优化方向


class AnalysisService:
    """
    财务深度成本分析服务 (SOLID - 诊断分析层)
    针对跨境和巴西本土卖家的财务健康水平进行全自动指标分解和诊断，提供实操性的节税与物流优化方案。
    """

    def generate_financial_report(
        self,
        product: Product,
        platform: Platform,
        profit_result: ProfitResult
    ) -> AnalysisResult:
        """
        根据计算结果，执行全方位财务诊断和文本化深度分析
        
        Args:
            product: 商品数据模型 (Product)
            platform: 平台销售参数 (Platform)
            profit_result: 前置计算出的利润分析面板 (ProfitResult)
            
        Returns:
            AnalysisResult: 完整的财务诊断与成本深度分析报告
        """
        rev = profit_result.revenue
        cost = product.cost_price_brl
        fee = profit_result.total_fee
        tax = profit_result.total_tax
        ship = profit_result.total_shipping
        net_p = profit_result.net_profit
        margin = profit_result.margin

        # 1. 自动计算各项财务占比 (Ratios)
        cost_ratio = round(cost / rev, 4) if rev > 0.0 else 0.0
        fee_ratio = round(fee / rev, 4) if rev > 0.0 else 0.0
        tax_ratio = round(tax / rev, 4) if rev > 0.0 else 0.0
        ship_ratio = round(ship / rev, 4) if rev > 0.0 else 0.0

        # === 2. 诊断逻辑 A: 综合利润诊断文书 ===
        if net_p > 0.0:
            p_text = (
                f"商品在 {platform.platform_name} 的销售表现健康，单笔交易可稳健产出 {format_brl(net_p)} 的纯收益。 "
                f"在目前的定价策略下，每 100 雷亚尔的销售营收，可以留存出约 {format_percentage(margin)} 的真金白银。 "
                "当前定价能够实现资金正向循环。"
            )
        else:
            p_text = (
                f"严重警告：该商品在 {platform.platform_name} 出现了 R$ {abs(net_p):.2f} 的财务亏损！ "
                "当前的售价严重低于由 [采购成本 + 平台扣点 + 巴西高额税收 + 实付物理运费] 构成的刚性价格红线。 "
                "在当前定价与供应链水平下，卖得越多、亏得越多，必须立即叫停销售或采取紧急优化！"
            )

        # === 3. 诊断逻辑 B: 产品与供应链成本分析 ===
        cost_ratio_pct = format_percentage(cost_ratio)
        if cost_ratio > 0.40:
            c_text = (
                f"采购进货成本占比偏高（占售价的 {cost_ratio_pct}），大幅挤压了后端的利润空间。 "
                "在巴西电商高额综合费率常态下，建议目标进价成本占比控制在 25% - 35% 之间。 "
                "主要优化建议：向工厂争取阶梯拿货价，或者寻找同款高毛利替代品进行供应链重构。"
            )
        elif cost_ratio == 0.0:
            c_text = "采购进货成本记录为 0。此商品为赠品、引流搭售品或虚拟资源包，成本结构具有极强弹性。"
        else:
            c_text = (
                f"采购进货成本控制卓越（仅占售价的 {cost_ratio_pct}），具有极为丰厚的供应链利润底盘。 "
                "这极大地增强了该商品应对巴西汇率大幅波动以及各大平台后续提升扣点的抗风险能力。"
            )

        # === 4. 诊断逻辑 C: 利润率安全评级与建议 ===
        if margin < 0.10:
            m_text = (
                f"利润率评级：【低毛利红色预警】(当前为 {format_percentage(margin)})。 "
                "极易因买家退款、丢件损失、以及巴西州内/跨州税差等细磨损导致整月实质性亏本。 "
                "强烈建议：1) 将平台定价上调 15% 以上；2) 探索打包（Combo）销售，降低每单固定成交费蚕食。"
            )
        elif 0.10 <= margin < 0.20:
            m_text = (
                f"利润率评级：【中等盈利黄色预警】(当前为 {format_percentage(margin)})。 "
                "具有基本的资金正向回笼能力，但遇到大促降价、退换货率飙升时利润垫容易被穿透。 "
                "建议：密切追踪特定平台的退货率。若退货率超过 5%，需增加买家发货确认，或在包材内增设防碎衬垫。"
            )
        else:
            m_text = (
                f"利润率评级：【高毛利绿色安全】(当前为 {format_percentage(margin)})。 "
                "这是一条极其罕见的优质高利润产品线。极强的盈利缓冲空间允许你在后续运营中投入大比例的流量广告（ADS）进行爆单拉升， "
                "同时建议对该爆款产品迅速进行一比一全平台复制占坑。"
            )

        # === 5. 诊断逻辑 D: 费用占比结构分析与优化方向 ===
        recs = []
        if fee_ratio > 0.20:
            recs.append(
                f"1. 平台杂费占比过高 ({format_percentage(fee_ratio)})。若为 Shopee，检查是否可退出 6% 的 FSS 免邮计划进行轻装上阵；"
                "若 ML 售价低于 R$ 79，低价固定费 R$ 6 严重稀释利润，强烈建议通过两件打包方式将客单价提到 R$ 79 以上，"
                "利用免收固定附加费的空子提升纯利。"
            )
        if ship_ratio > 0.15:
            recs.append(
                f"2. 实付物流成本占营收 {format_percentage(ship_ratio)}，对轻小件而言较为偏高。若在 Mercado Livre 运营，"
                "核心方法是通过提高客服、物流发货率以将卖家信誉评级（Reputação）提升至绿色以上（乃至铂金 Platinum），"
                "以直接享有 50% 官方运费分摊减免，纯利可瞬间提升近 5-10 雷亚尔！"
            )
        if tax_ratio > 0.15:
            recs.append(
                f"3. 综合纳税总额占售价比例达 {format_percentage(tax_ratio)}。若是由于年销售额处于高税档（Simples Nacional 高阶）造成的，"
                "建议注册多张‘微型企业（ME / EPP）’执照分拆年总营收；若是跨境 Remessa Conforme 大包裹关税飙升导致的，"
                "建议利用低于 50 美元起征点的政策，采用‘拆包裹、分单邮寄’的合规方案大幅节免关税。"
            )

        if not recs:
            f_text = (
                f"平台费用({format_percentage(fee_ratio)})、税金比例({format_percentage(tax_ratio)})与物流占比({format_percentage(ship_ratio)})"
                "均控制在极佳比例。该款商品的综合账目健康度近乎完美，无显著的结构性成本漏损。"
            )
        else:
            f_text = "综合诊断出的最急需改善的成本漏洞：\n" + "\n".join(recs)

        return AnalysisResult(
            product_sku=product.sku,
            platform_name=platform.platform_name,
            revenue_brl=rev,
            purchase_cost_brl=cost,
            purchase_cost_ratio=cost_ratio,
            total_fee_brl=fee,
            fee_ratio=fee_ratio,
            total_tax_brl=tax,
            tax_ratio=tax_ratio,
            total_shipping_brl=ship,
            shipping_ratio=ship_ratio,
            net_profit_brl=net_p,
            profit_margin=margin,
            profit_analysis=p_text,
            cost_analysis=c_text,
            margin_analysis=m_text,
            fee_proportion_analysis=f_text
        )
