# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品评估多维度打分引擎
"""

from src.models.product import Product
from src.product_selection.models import MarketData, SelectionCriteria, SelectionScore
from src.product_selection.calculator import ProductSelectionCalculator

class ProductScoringEngine:
    """
    选品综合打分引擎
    """

    @staticmethod
    def calculate_scores(
        product: Product,
        market_data: MarketData,
        estimated_margin: float,
        estimated_roi: float,
        criteria: SelectionCriteria
    ) -> SelectionScore:
        """
        根据财务预测、物理规格以及市场竞争/需求数据，对商品进行多维度百分制打分
        
        评分权重与参数：
            由传入的 SelectionCriteria 全权控制，彻底杜绝硬编码。
            各维度评分及总评分范围均限制在 0.0 - 100.0 之间。
            
        推荐等级评定（统一划分为四档）：
            - S 级 (>= criteria.s_min_score) 推荐范围: 80.00 – 100.00
            - A 级 (>= criteria.a_min_score) 推荐范围: 70.00 – 79.99
            - B 级 (>= criteria.b_min_score) 推荐范围: 60.00 – 69.99
            - C 级 (< criteria.b_min_score)  推荐范围: 0.00 – 59.99
            
        安全准则：
            只接收已计算好的财务和物理分析结果进行加权打分，绝不重新运行利润、税费或物流运费精算。
        """
        # 1. 利润维度得分 (0.0 - 100.0)
        if estimated_margin <= 0 or estimated_roi <= 0:
            profit_score = 0.0
        else:
            # 利润率得分 (以 criteria.min_net_margin 为标准)
            margin_score = (estimated_margin / criteria.min_net_margin) * 70.0
            margin_score = max(0.0, min(margin_score, 100.0))
            
            # ROI 得分 (以 criteria.target_roi 为标准)
            roi_score = (estimated_roi / criteria.target_roi) * 70.0
            roi_score = max(0.0, min(roi_score, 100.0))
            
            profit_score = round((margin_score + roi_score) / 2.0, 2)

        # 2. 需求维度得分 (0.0 - 100.0)
        high_thresh = criteria.demand_sales_thresholds.get("high", 8.0)
        med_thresh = criteria.demand_sales_thresholds.get("medium", 5.0)
        
        if market_data.demand_score >= high_thresh:
            base_demand_score = 100.0
        elif market_data.demand_score >= med_thresh:
            base_demand_score = 75.0
        else:
            if med_thresh > 0:
                base_demand_score = (market_data.demand_score / med_thresh) * 75.0
            else:
                base_demand_score = 0.0
                
        # 乘以市场趋势系数，并限制在 0-100 之间
        demand_score = base_demand_score * market_data.trend_factor
        demand_score = max(0.0, min(demand_score, 100.0))
        demand_score = round(demand_score, 2)

        # 3. 竞争维度得分 (0.0 - 100.0)
        comp_limits = criteria.competition_seller_thresholds
        comp_count = market_data.competitor_count
        
        if comp_count <= comp_limits.get("none_limit", 0):
            competition_score = 100.0
        elif comp_count <= comp_limits.get("low_limit", 2):
            competition_score = 90.0
        elif comp_count <= comp_limits.get("medium_limit", 5):
            competition_score = 80.0
        elif comp_count <= comp_limits.get("high_limit", 10):
            competition_score = 65.0
        elif comp_count <= comp_limits.get("very_high_limit", 20):
            competition_score = 45.0
        else:
            competition_score = 20.0

        # 4. 物流与规格维度得分 (0.0 - 100.0)
        logistics_score = 100.0
        
        # 实重扣分 (独立使用 weight_penalty_ratio)
        weight_g = product.weight_g
        if weight_g > criteria.overweight_threshold_g:
            excess_weight = weight_g - criteria.overweight_threshold_g
            # 采用实际超重惩罚系数 weight_penalty_ratio：每超 1000g 扣除对应分数
            weight_penalty = (excess_weight / 1000.0) * criteria.weight_penalty_ratio
            logistics_score -= min(weight_penalty, criteria.max_weight_penalty)

        # 体积重量（抛重）扣分 (独立使用 volumetric_penalty_ratio)
        vol_weight_g = ProductSelectionCalculator.calculate_volumetric_weight_g(product)
        if vol_weight_g > weight_g:
            excess_vol = vol_weight_g - weight_g
            # 采用体积重惩罚系数 volumetric_penalty_ratio：体积重每超实重 1000g 扣除对应分数
            vol_penalty = (excess_vol / 1000.0) * criteria.volumetric_penalty_ratio
            logistics_score -= min(vol_penalty, criteria.max_weight_penalty)

        logistics_score = max(0.0, min(logistics_score, 100.0))
        logistics_score = round(logistics_score, 2)

        # 5. 计算加权总得分
        total_score = (
            profit_score * criteria.profit_weight +
            demand_score * criteria.demand_weight +
            competition_score * criteria.competition_weight +
            logistics_score * criteria.logistics_weight
        )
        total_score = max(0.0, min(total_score, 100.0))
        total_score = round(total_score, 2)

        # 6. 生成推荐评级 (S, A, B, C)
        if total_score >= criteria.s_min_score:
            recommendation_level = "S"
        elif total_score >= criteria.a_min_score:
            recommendation_level = "A"
        elif total_score >= criteria.b_min_score:
            recommendation_level = "B"
        else:
            recommendation_level = "C"

        return SelectionScore(
            total_score=total_score,
            profit_score=profit_score,
            demand_score=demand_score,
            competition_score=competition_score,
            logistics_score=logistics_score,
            recommendation_level=recommendation_level
        )
