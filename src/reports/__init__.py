# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报表领域契约与模型转换包
本包定义了系统所有分类报表、财务数据传输对象 (DTOs) 以及报告的拼装、本地化和序列化体系：
1. 报表模型 Report Models (BusinessReport, SummaryReport, FinancialReport 等 10 大 DTO)
2. 报告高阶本地化格式器 ReportFormatter
3. 一站式报告转换器/组装器 ReportBuilder
4. 递归字典/JSON 序列化器 ReportSerializer
"""

# 报表领域模型导出
from src.reports.report_models import (
    SummaryReport,
    TaxReport,
    PlatformReport,
    FinancialReport,
    PricingReport,
    MarketingReport,
    InventoryReport,
    WarningReport,
    RecommendationReport,
    BusinessReport
)

# 报告基础组件导出
from src.reports.report_formatter import ReportFormatter
from src.reports.report_builder import ReportBuilder
from src.reports.report_serializer import ReportSerializer

__all__ = [
    # 领域数据实体
    "SummaryReport",
    "TaxReport",
    "PlatformReport",
    "FinancialReport",
    "PricingReport",
    "MarketingReport",
    "InventoryReport",
    "WarningReport",
    "RecommendationReport",
    "BusinessReport",
    
    # 构建与序列化组件
    "ReportFormatter",
    "ReportBuilder",
    "ReportSerializer"
]
