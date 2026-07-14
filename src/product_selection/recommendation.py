# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品推荐与排序过滤策略
"""

from typing import List
from src.product_selection.models import SelectionResult, SelectionCriteria

class SelectionRecommender:
    """
    选品推荐、过滤与排序机制
    """

    @staticmethod
    def rank_and_filter(
        results: List[SelectionResult],
        criteria: SelectionCriteria
    ) -> List[SelectionResult]:
        """
        根据 SelectionCriteria 过滤不满足最低净利润率、最低 ROI 以及最低推荐等级的选品，
        并对满足条件的选品按综合得分由高到低（降序）进行排序。
        
        过滤规则：
            - 必须满足最低利润率: r.estimated_margin >= criteria.min_net_margin
            - 必须满足最低目标 ROI: r.estimated_roi >= criteria.target_roi
            - 等级过滤：不推荐 C 级选品，仅保留 S, A, B 级
        """
        if not results:
            return []
            
        filtered_results = []
        for r in results:
            # 1. 过滤低于最低净利润率标准的选品
            if r.estimated_margin < criteria.min_net_margin:
                continue
                
            # 2. 过滤低于目标 ROI 标准的选品
            if r.estimated_roi < criteria.target_roi:
                continue
                
            # 3. 过滤处于 C 级不推荐水平的选品
            if r.scores.recommendation_level == "C":
                continue
                
            filtered_results.append(r)
            
        # 按综合得分进行降序（从高到低）排列
        return sorted(filtered_results, key=lambda x: x.scores.total_score, reverse=True)
