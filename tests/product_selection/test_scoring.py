# -*- coding: utf-8 -*-
"""
选品综合打分引擎单元测试
"""

from src.models.product import Product
from src.product_selection.models import MarketData, SelectionCriteria
from src.product_selection.scoring import ProductScoringEngine

def test_scoring_weights_validation():
    """测试 Criteria 评分权重和必须等于 1.0 的校验逻辑"""
    # 权重和为 1.1 抛出 ValueError
    import pytest
    with pytest.raises(ValueError, match="评分权重之和必须严格等于 1.0"):
        SelectionCriteria(profit_weight=0.5, demand_weight=0.3, competition_weight=0.2, logistics_weight=0.1)


def test_scoring_level_boundaries():
    """测试 S, A, B, C 等级划分边界以及总打分值范围约束"""
    criteria = SelectionCriteria(
        profit_weight=0.25, demand_weight=0.25, competition_weight=0.25, logistics_weight=0.25,
        s_min_score=80.0, a_min_score=70.0, b_min_score=60.0
    )
    product_standard = Product(sku="P", name="P", cost_price_brl=10, weight_g=500, length_cm=10, width_cm=10, height_cm=6, category="elec")

    # 1. 构造 S 级 (总分 >= 80)
    # 物流分 100 (不超重)
    # 竞争分 80 (5个对手)
    # 需求分 75 (需求5.5, 中档 -> 75分)
    # 利润分 70 (margin=15%, roi=30%, 刚好达标 -> 70分)
    # 加权和: 100*0.25 + 80*0.25 + 75*0.25 + 70*0.25 = 81.25 (S)
    market_s = MarketData(average_selling_price_brl=100, competitor_count=5, demand_score=5.5)
    score_s = ProductScoringEngine.calculate_scores(product_standard, market_s, 0.15, 0.30, criteria)
    assert score_s.recommendation_level == "S"
    assert 80.0 <= score_s.total_score <= 100.0

    # 2. 构造 A 级 (总分 70-79.99)
    # 降低需求至 4.0 (得分 60)
    # 加权和: 100*0.25 + 80*0.25 + 60*0.25 + 70*0.25 = 77.5 (A)
    market_a = MarketData(average_selling_price_brl=100, competitor_count=5, demand_score=4.0)
    score_a = ProductScoringEngine.calculate_scores(product_standard, market_a, 0.15, 0.30, criteria)
    assert score_a.recommendation_level == "A"
    assert 70.0 <= score_a.total_score < 80.0

    # 3. 构造 B 级 (总分 60-69.99)
    # 增加竞争对手至 12 (得分 45)
    # 加权和: 100*0.25 + 45*0.25 + 60*0.25 + 70*0.25 = 68.75 (B)
    market_b = MarketData(average_selling_price_brl=100, competitor_count=12, demand_score=4.0)
    score_b = ProductScoringEngine.calculate_scores(product_standard, market_b, 0.15, 0.30, criteria)
    assert score_b.recommendation_level == "B"
    assert 60.0 <= score_b.total_score < 70.0

    # 4. 构造 C 级 (总分 < 60)
    # 发生亏损 (margin=0, roi=0 -> 利润0分)，并添加物流超重惩罚 (物流分 60)
    # 加权和: 60*0.25 + 45*0.25 + 60*0.25 + 0 = 41.25 (C)
    product_heavy = Product(sku="PH", name="PH", cost_price_brl=10, weight_g=20000, length_cm=10, width_cm=10, height_cm=6, category="elec")
    score_c = ProductScoringEngine.calculate_scores(product_heavy, market_b, 0.0, 0.0, criteria)
    assert score_c.recommendation_level == "C"
    assert 0.0 <= score_c.total_score < 60.0


def test_scoring_logistics_penalties():
    """测试实际物理重量 (weight_penalty_ratio) 与体积重 (volumetric_penalty_ratio) 罚分的物理隔离与扣分上限"""
    # 构造一件双重超重商品：实重 2000g (超重 1.5kg)，体积重 4500g (超抛 2.5kg)
    product_log = Product(sku="PL", name="PL", cost_price_brl=50.0, weight_g=2000.0, length_cm=30.0, width_cm=30.0, height_cm=30.0, category="e")
    market_ref = MarketData(average_selling_price_brl=150.0, competitor_count=5, demand_score=8.0)
    
    # 校验 1：实重超重罚分比重 5.0，体积超标罚重比重 10.0
    # penalty = (1.5 * 5.0) + (2.5 * 10.0) = 7.5 + 25.0 = 32.5 => logistics score = 67.5
    crit_1 = SelectionCriteria(weight_penalty_ratio=5.0, volumetric_penalty_ratio=10.0)
    score_1 = ProductScoringEngine.calculate_scores(product_log, market_ref, 0.20, 0.40, crit_1)
    assert score_1.logistics_score == 67.5

    # 校验 2：实重罚重比重上调至 20.0，体积超重保持 10.0
    # penalty = (1.5 * 20.0) + (2.5 * 10.0) = 30.0 + 25.0 = 55.0 => logistics score = 45.0
    # 这证明了实际重量惩罚的改动不会污染、混用体积超标惩罚的值
    crit_2 = SelectionCriteria(weight_penalty_ratio=20.0, volumetric_penalty_ratio=10.0)
    score_2 = ProductScoringEngine.calculate_scores(product_log, market_ref, 0.20, 0.40, crit_2)
    assert score_2.logistics_score == 45.0
