# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 业务服务核心编排包
本包对底层精确计算引擎进行业务场景编排与封装，公开高阶业务服务：
1. 平台费业务服务 FeeService 与其结果集 FeeResult
2. 税务精算业务服务 TaxService 与其结果集 TaxResult
3. 综合利润核算编排服务 ProfitService
4. 深度财务与成本结构分析服务 AnalysisService 与其分析结果集 AnalysisResult
"""

from src.services.fee_service import FeeResult, FeeService
from src.services.tax_service import TaxResult, TaxService
from src.services.profit_service import ProfitService
from src.services.analysis_service import AnalysisResult, AnalysisService

__all__ = [
    "FeeResult",
    "FeeService",
    "TaxResult",
    "TaxService",
    "ProfitService",
    "AnalysisResult",
    "AnalysisService"
]
