# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品分析综合服务
"""

import logging
from typing import List, Optional, Tuple
from src.models.product import Product
from src.models.platform import Platform
from src.services.profit_service import ProfitService
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.calculators.shipping_calculator import ShippingCalculator
from src.product_selection.models import MarketData, SelectionCriteria, SelectionResult
from src.product_selection.calculator import ProductSelectionCalculator
from src.product_selection.scoring import ProductScoringEngine
from src.product_selection.recommendation import SelectionRecommender

logger = logging.getLogger(__name__)

class ProductSelectionService:
    """
    选品综合分析服务层
    """

    def __init__(
        self,
        profit_service: Optional[ProfitService] = None,
        fee_service: Optional[FeeService] = None,
        tax_service: Optional[TaxService] = None,
        shipping_calculator: Optional[ShippingCalculator] = None
    ) -> None:
        """
        依赖注入已有服务与计算器，避免复制计算逻辑。
        """
        self._profit_service = profit_service or ProfitService()
        self._fee_service = fee_service or FeeService()
        self._tax_service = tax_service or TaxService()
        self._shipping_calculator = shipping_calculator or ShippingCalculator()

    def evaluate_product(
        self,
        product: Product,
        market_data: MarketData,
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> SelectionResult:
        """
        评估单款商品的选品可行性并输出综合报告。
        
        调用已有模块（ProfitService, TaxService, FeeService, ShippingCalculator）来核算财务成本，
        结合反推公式估算售价，并通过打分引擎给出最终综合得分和推荐等级。
        """
        # 1. 确保评估配置存在
        criteria = criteria or SelectionCriteria()

        # 2. 建立一个初始的销售平台实例 (使用市场平均售价作为试算价格，用来反算税率、佣金费率和物流费)
        temp_platform = Platform(
            platform_id=platform_id,
            platform_name=platform_name,
            selling_price_brl=market_data.average_selling_price_brl
        )

        # 3. 试算此产品的费率 (佣金比例、有效税率、首重运费成本) - 完全复用已有模块
        fee_res = self._fee_service.get_fee_analysis(product, temp_platform)
        platform_fee_ratio = fee_res.fee_to_revenue_ratio
        
        tax_res = self._tax_service.get_tax_analysis(product, temp_platform)
        tax_ratio = tax_res.effective_tax_rate
        
        shipping_fee_brl = self._shipping_calculator.calculate(product, temp_platform)

        # 4. 反推满足最低净利率目标的建议零售价
        estimated_retail_price = ProductSelectionCalculator.calculate_estimated_selling_price(
            cost_price_brl=product.cost_price_brl,
            estimated_shipping_brl=shipping_fee_brl,
            platform_fee_ratio=platform_fee_ratio,
            tax_ratio=tax_ratio,
            target_margin_ratio=criteria.min_net_margin
        )

        # 5. 用反推售价建立最终销售平台实例
        final_platform = Platform(
            platform_id=platform_id,
            platform_name=platform_name,
            selling_price_brl=estimated_retail_price
        )

        # 6. 调用已有 ProfitService 汇总计算真实利润和各维度支出，拒绝公式复制
        profit_res = self._profit_service.calculate_profitability(product, final_platform)

        # 7. 基于已有计算结果计算 ROI 与利润率
        estimated_net_profit = profit_res.net_profit
        estimated_margin = profit_res.margin
        estimated_roi = ProductSelectionCalculator.calculate_roi(estimated_net_profit, product.cost_price_brl)
        estimated_gross_profit = estimated_retail_price - product.cost_price_brl

        # 8. 执行打分引擎评估选品得分
        scores = ProductScoringEngine.calculate_scores(
            product=product,
            market_data=market_data,
            estimated_margin=estimated_margin,
            estimated_roi=estimated_roi,
            criteria=criteria
        )

        # 9. 自动生成高信号推荐理由与风险预警
        reasons = []
        warnings = []

        # 评分评级反馈
        if scores.recommendation_level == "S":
            reasons.append(f"产品打分极高 ({scores.total_score}分)，综合表现极其强劲。")
        elif scores.recommendation_level == "A":
            reasons.append(f"产品打分优异 ({scores.total_score}分)，具备高推荐度。")
        elif scores.recommendation_level == "B":
            reasons.append(f"产品打分及格 ({scores.total_score}分)，商业可行，建议谨慎跟进。")

        # 财务指标反馈
        if estimated_roi >= criteria.target_roi:
            reasons.append(f"预期 ROI ({round(estimated_roi * 100, 2)}%) 达到或超过目标水平。")
        else:
            warnings.append(f"预期 ROI ({round(estimated_roi * 100, 2)}%) 未能达标。")

        if estimated_margin >= criteria.min_net_margin:
            reasons.append(f"预期净利率 ({round(estimated_margin * 100, 2)}%) 处于健康区间。")
        else:
            warnings.append(f"预期净利率 ({round(estimated_margin * 100, 2)}%) 偏低，利润空间不足。")

        # 物流物理反馈
        vol_weight_g = ProductSelectionCalculator.calculate_volumetric_weight_g(product)
        if product.weight_g > criteria.overweight_threshold_g:
            warnings.append(f"商品实际重量为 {product.weight_g}g，已超过 {criteria.overweight_threshold_g}g 的轻量门槛。")
        if vol_weight_g > product.weight_g:
            warnings.append(f"商品体积重为 {vol_weight_g}g，显著超出物理实重，属于轻抛货物。")

        # 市场环境反馈
        if market_data.demand_score >= criteria.demand_sales_thresholds.get("high", 8.0):
            reasons.append(f"市场需求极其旺盛 (需求评分: {market_data.demand_score}/10.0)。")
        if market_data.competitor_count >= criteria.competition_seller_thresholds.get("very_high_limit", 20):
            warnings.append(f"该品类竞争极度激烈，已有超过 {market_data.competitor_count} 家竞争卖家。")

        return SelectionResult(
            product=product,
            market_data=market_data,
            scores=scores,
            estimated_retail_price_brl=estimated_retail_price,
            estimated_net_profit_brl=estimated_net_profit,
            estimated_roi=estimated_roi,
            estimated_margin=estimated_margin,
            estimated_tax_brl=profit_res.total_tax,
            estimated_platform_fee_brl=profit_res.total_fee,
            estimated_shipping_brl=profit_res.total_shipping,
            estimated_gross_profit_brl=estimated_gross_profit,
            recommendation_reasons=reasons,
            risk_warnings=warnings
        )

    def evaluate_batch(
        self,
        products: List[Product],
        market_data_list: List[MarketData],
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> Tuple[List[SelectionResult], List[Tuple[str, str]]]:
        """
        批量评估多款候选商品，支持部分商品失败不中断整体流程。
        
        Args:
            products: 商品 Product 数据对象列表
            market_data_list: 商品市场 MarketData 属性列表
            criteria: 选品配置对象
            
        Returns:
            Tuple[List[SelectionResult], List[Tuple[str, str]]]:
                - 评估成功且满足 Criteria 过滤条件并通过排序的选品列表。
                - 评估失败的商品 SKU 及其对应异常详细信息的列表，形如: [("SKU_001", "ValueError...")]
        """
        if len(products) != len(market_data_list):
            raise ValueError(
                f"商品列表与市场数据列表长度不一致，无法匹配。"
                f"(商品数量: {len(products)}, 市场数据数量: {len(market_data_list)})"
            )

        criteria = criteria or SelectionCriteria()
        results = []
        errors = []

        for prod, market in zip(products, market_data_list):
            try:
                res = self.evaluate_product(
                    product=prod,
                    market_data=market,
                    criteria=criteria,
                    platform_id=platform_id,
                    platform_name=platform_name
                )
                results.append(res)
            except Exception as e:
                # 记录单个评估失败错误，保障整批流程继续
                error_msg = f"{type(e).__name__}: {str(e)}"
                sku = prod.sku if hasattr(prod, 'sku') else "Unknown"
                logger.error(f"商品 {sku} 选品试算评估失败，错误信息: {error_msg}")
                errors.append((sku, error_msg))

        # 调用 SelectionRecommender 进行排序降序、底线过滤
        ranked_results = SelectionRecommender.rank_and_filter(results, criteria)
        return ranked_results, errors
