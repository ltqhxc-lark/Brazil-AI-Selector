# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品评估数据模型
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict
from src.models.product import Product

@dataclass
class MarketData:
    """
    选品相关的市场竞争与需求数据
    """
    average_selling_price_brl: float    # 市场平均零售价 (BRL)
    competitor_count: int               # 主要竞争对手数量
    demand_score: float                 # 市场需求评分 (0.0 - 10.0，10.0为最高)
    trend_factor: float = 1.0           # 市场趋势系数 (如 1.1 表示需求增长 10%)


@dataclass
class SelectionCriteria:
    """
    选品评估权重及筛选标准配置
    """
    target_roi: float = 0.3             # 目标投资回报率 (ROI，例如 30%)
    min_net_margin: float = 0.15        # 最低可接受净利润率 (例如 15%)
    
    # 评分维度权重 (总和必须精确等于 1.0)
    profit_weight: float = 0.4          # 利润维度权重
    demand_weight: float = 0.3          # 市场需求权重
    competition_weight: float = 0.2     # 竞争激烈程度权重
    logistics_weight: float = 0.1       # 物流与规格约束权重
    
    # 推荐等级最低分数线
    s_min_score: float = 80.0           # S级最低分
    a_min_score: float = 70.0           # A级最低分
    b_min_score: float = 60.0           # B级最低分
    
    # 需求分段及系数
    demand_sales_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "high": 8.0,
            "medium": 5.0
        }
    )
    
    # 竞争分段阀值 (竞争对手数量)
    competition_seller_thresholds: Dict[str, int] = field(
        default_factory=lambda: {
            "none_limit": 0,            # 0个对手 -> 100分
            "low_limit": 2,             # <= 2个对手 -> 90分
            "medium_limit": 5,          # <= 5个对手 -> 80分
            "high_limit": 10,           # <= 10个对手 -> 65分
            "very_high_limit": 20       # <= 20个对手 -> 45分，大于20 -> 20分
        }
    )
    
    # 物流扣分参数
    overweight_threshold_g: float = 500.0  # 超重起点克数
    weight_penalty_ratio: float = 5.0      # 实际超重惩罚系数 (实际重量每超出超重起点1kg扣除分数)
    volumetric_penalty_ratio: float = 10.0 # 体积超重惩罚系数 (体积重每超出实际重量1kg扣除分数)
    max_weight_penalty: float = 40.0       # 最大重量扣分上限

    def __post_init__(self) -> None:
        """
        在数据结构构建后运行，校验权重与等级阈值的合法性
        """
        # 1. 校验四项评分权重之和是否等于 1.0
        total_weight = (
            self.profit_weight +
            self.demand_weight +
            self.competition_weight +
            self.logistics_weight
        )
        if not math.isclose(total_weight, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(
                f"评分权重之和必须严格等于 1.0，当前各权重之和为: {total_weight} "
                f"(利润: {self.profit_weight}, 需求: {self.demand_weight}, "
                f"竞争: {self.competition_weight}, 物流: {self.logistics_weight})"
            )

        # 2. 校验推荐等级阈值的层级关系
        # 必须满足: 0 <= b_min_score < a_min_score < s_min_score <= 100
        if not (0 <= self.b_min_score < self.a_min_score < self.s_min_score <= 100):
            raise ValueError(
                f"推荐等级阈值关系不合法。必须满足: 0 <= b_min_score < a_min_score < s_min_score <= 100。 "
                f"当前配置为: b_min={self.b_min_score}, a_min={self.a_min_score}, s_min={self.s_min_score}"
            )


@dataclass
class SelectionScore:
    """
    商品选品评估得分明细
    """
    total_score: float                  # 选品综合评分 (0.0 - 100.0)
    profit_score: float                 # 利润维度得分 (0.0 - 100.0)
    demand_score: float                 # 需求维度得分 (0.0 - 100.0)
    competition_score: float            # 竞争维度得分 (0.0 - 100.0)
    logistics_score: float              # 物流与规格得分 (0.0 - 100.0)
    recommendation_level: str           # 推荐评级 (S, A, B, C)


@dataclass
class SelectionResult:
    """
    选品综合评估结果
    """
    product: Product                    # 评估的商品
    market_data: MarketData             # 相关的市场数据
    scores: SelectionScore              # 评估得分明细
    estimated_retail_price_brl: float   # 估算建议售价 (BRL)
    estimated_net_profit_brl: float     # 估算每单净利润 (BRL)
    estimated_roi: float                # 估算投资回报率 (ROI)
    estimated_margin: float             # 估算净利润率
    estimated_tax_brl: float = 0.0      # 估算巴西税费成本 (BRL)
    estimated_platform_fee_brl: float = 0.0 # 估算平台佣金费用 (BRL)
    estimated_shipping_brl: float = 0.0 # 估算物流运费 (BRL)
    estimated_gross_profit_brl: float = 0.0 # 估算毛利润 (BRL)
    recommendation_reasons: List[str] = field(default_factory=list) # 推荐理由
    risk_warnings: List[str] = field(default_factory=list)          # 风险提示
