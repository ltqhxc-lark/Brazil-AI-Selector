# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品评估模块 (Product Selection)
"""

from src.product_selection.models import (
    MarketData,
    SelectionCriteria,
    SelectionScore,
    SelectionResult
)
from src.product_selection.calculator import ProductSelectionCalculator
from src.product_selection.scoring import ProductScoringEngine
from src.product_selection.recommendation import SelectionRecommender
from src.product_selection.service import ProductSelectionService

__all__ = [
    "MarketData",
    "SelectionCriteria",
    "SelectionScore",
    "SelectionResult",
    "ProductSelectionCalculator",
    "ProductScoringEngine",
    "SelectionRecommender",
    "ProductSelectionService"
]
