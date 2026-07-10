# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 销售平台推荐选择与策略引擎
对比商品在美客多、虾皮、TikTok 等多个平台的实际利润、扣点及运费开销，推荐最优首发平台，并对卖家等级、免邮流量包参与提供决策。
"""

from typing import List, Dict, Tuple
from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.profit_calculator import ProfitResult
from src.strategies.base_strategy import BaseStrategy, StrategyResult

class MarketplaceStrategy(BaseStrategy):
    """
    销售平台选择与推荐策略 (SOLID - 平台选择职责)
    通过对比多个平台的利润核算结果，推荐出最具有盈利韧性的销售平台，并规划增值活动参与策略。
    """

    @property
    def name(self) -> str:
        return "销售平台选择与等级推荐策略"

    def execute(
        self,
        product: Product,
        platform_metrics: Dict[str, Tuple[Platform, ProfitResult, Fee]]
    ) -> StrategyResult:
        """
        对比多个平台的财务状况，生成选品上架平台和等级政策建议
        
        Args:
            product: 待评估商品实体
            platform_metrics: 各个平台的精算数据集，键名为 platform_id (如 'shopee_brasil')，
                              值为三元组 (Platform 实体, ProfitResult 实体, Fee 费用实体)
                              
        Returns:
            StrategyResult: 带有置信度、预警级别的平台选择诊断报告
        """
        suggestions = []
        alert_level = "green"
        confidence = 0.90
        
        if not platform_metrics:
            return StrategyResult(
                strategy_name=self.name,
                decision_summary="无可供对比的平台数据，无法生成推荐策略。",
                suggestions=["请提供至少一个平台的利润核算数据。"],
                alert_level="yellow",
                confidence_score=0.5
            )

        # 1. 寻找净利润绝对值最大和利润率最大的平台
        best_profit_pid = None
        best_profit_val = -999999.0
        best_margin_pid = None
        best_margin_val = -999999.0

        for pid, (plat, prof, fee) in platform_metrics.items():
            if prof.net_profit > best_profit_val:
                best_profit_val = prof.net_profit
                best_profit_pid = pid
            if prof.margin > best_margin_val:
                best_margin_val = prof.margin
                best_margin_pid = pid

        # 构建分析指标快照用于前端展示
        metrics_snapshot = {}
        for pid, (plat, prof, fee) in platform_metrics.items():
            metrics_snapshot[pid] = {
                "name": plat.platform_name,
                "net_profit": prof.net_profit,
                "margin": prof.margin,
                "total_fee": prof.total_fee
            }

        # 核心判定决策摘要
        best_plat_name = platform_metrics[best_profit_pid][0].platform_name
        if best_profit_val > 0.0:
            summary = f"首推销售平台：【{best_plat_name}】，单笔可获纯利 R$ {best_profit_val:.2f}，利润率 {best_margin_val*100:.2f}%。"
        else:
            summary = "警告：该商品在所有拟上架平台中均处于亏损状态！不建议以当前成本和定价强行上架。"
            alert_level = "red"

        # 2. 深入制定各大平台的个性化优化决策
        for pid, (plat, prof, fee) in platform_metrics.items():
            p_name = plat.platform_name
            
            # --- 美客多专项策略 (Mercado Livre) ---
            if pid == "mercado_livre_brasil":
                if plat.seller_level == "normal" and prof.total_shipping > 15.0:
                    suggestions.append(
                        f"【美客多优化】：当前运费支出达 R$ {prof.total_shipping:.2f}。强烈建议将店铺信誉提升至铂金（Platinum），"
                        "运费减免折扣将从 10% 暴拉至 50%，每单可瞬间多赚 R$ {prof.total_shipping * 0.4 / 0.9:.2f} 的纯利！"
                    )
                if plat.selling_price_brl < 79.00:
                    suggestions.append(
                        f"【美客多提价提示】：售价低于 R$ 79.00 被强制征收 R$ 6.00 的低价手续费。建议采用‘2件起包邮装’（Combo），"
                        "将客单价拉过 R$ 79 槛，直接免除固定服务费以套利。"
                    )

            # --- 虾皮专项策略 (Shopee) ---
            elif pid == "shopee_brasil":
                if plat.participate_fss:
                    fss_pct = (fee.affiliate_fee_brl / plat.selling_price_brl) * 100 if plat.selling_price_brl > 0 else 0
                    suggestions.append(
                        f"【虾皮FSS流控】：免邮计划（FSS）扣掉了售价的 {fss_pct:.2f}% 额外佣金（R$ {fee.affiliate_fee_brl:.2f}）。"
                        "对于超轻、超低货值的爆款，如果单价极低且无物流优势，可考虑主动退出免邮计划，降低 6% 扣点以保本。"
                    )
                if prof.net_profit < 3.0:
                    suggestions.append(
                        "【虾皮起征警告】：由于虾皮按件扣除 R$ 3.00 固定服务费。对于极低价引流款（如 R$ 10 以下商品），"
                        "单笔交易利润会被该固定附加费瞬间吸干，建议提高打包基数（3合1销售）。"
                    )

            # --- TikTok Shop 专项策略 ---
            elif pid == "tiktok_shop_brasil":
                if plat.affiliate_rate > 0.15:
                    suggestions.append(
                        f"【TikTok联盟预警】：设置的达人分销佣金率 ({plat.affiliate_rate*100:.1f}%) 偏高，"
                        "已挤占了 1/3 的毛利。建议将常规达人佣金压低到 10% 以内，只给头部带货大咖（带货能力高）定向发放 15%+ 定向高佣计划。"
                    )

        # 汇总平台间横向对比建议
        if len(platform_metrics) > 1:
            if best_profit_pid != best_margin_pid:
                margin_plat_name = platform_metrics[best_margin_pid][0].platform_name
                suggestions.append(
                    f"【多渠道横向】：首发上架建议：若追求资金周转和爆单，推荐纯利额最大的平台【{best_plat_name}】；"
                    f"若资金垫款链较紧，推荐投资回报率/利润率最高的平台【{margin_plat_name}】。"
                )
        else:
            suggestions.append("【多渠道提示】：当前仅进行了单平台核算，建议补充其他两大巴西主流平台的配置进行联合横向选品，寻找暴利蓝海。")

        return StrategyResult(
            strategy_name=self.name,
            decision_summary=summary,
            suggestions=suggestions,
            confidence_score=confidence,
            alert_level=alert_level,
            raw_metrics=metrics_snapshot
        )
