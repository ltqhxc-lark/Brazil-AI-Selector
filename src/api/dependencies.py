# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - API 依赖注入层 (Dependencies)
定义供 FastAPI 路由层使用 Depends 进行调用的高内聚服务单例和策略工厂，
彻底避免在控制器内直接实例化复杂后台组件，保障模块间可测试与可Mock性。
"""

from typing import Dict
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.services.profit_service import ProfitService
from src.services.analysis_service import AnalysisService
from src.strategies.recommendation_strategy import RecommendationStrategy
from src.reports.report_builder import ReportBuilder
from src.exporters import BaseExporter, JSONExporter, CSVExporter, ExcelExporter, PDFExporter

# ==============================================================================
# 1. 业务服务依赖单例提供者 (Services Singletons)
# ==============================================================================

_fee_service = FeeService()
_tax_service = TaxService()
_profit_service = ProfitService(fee_service=_fee_service, tax_service=_tax_service)
_analysis_service = AnalysisService()

def get_fee_service() -> FeeService:
    """
    获取平台费用分析服务
    """
    return _fee_service


def get_tax_service() -> TaxService:
    """
    获取税务精算分析服务
    """
    return _tax_service


def get_profit_service() -> ProfitService:
    """
    获取利润综合编排服务
    """
    return _profit_service


def get_analysis_service() -> AnalysisService:
    """
    获取财务深度诊断服务
    """
    return _analysis_service


# ==============================================================================
# 2. 策略推荐引擎依赖提供者 (Strategies Singletons)
# ==============================================================================

_recommendation_strategy = RecommendationStrategy()

def get_recommendation_strategy() -> RecommendationStrategy:
    """
    获取一站式综合策略推荐引擎
    """
    return _recommendation_strategy


# ==============================================================================
# 3. 报表构建与物理导出依赖提供者 (Report & Exporters)
# ==============================================================================

_report_builder = ReportBuilder()

# 汇总注册系统中所有的物理格式导出器
_exporters: Dict[str, BaseExporter] = {
    "json": JSONExporter(),
    "csv": CSVExporter(),
    "xlsx": ExcelExporter(),
    "pdf": PDFExporter()
}

def get_report_builder() -> ReportBuilder:
    """
    获取高级嵌套报表组装器
    """
    return _report_builder


def get_exporters() -> Dict[str, BaseExporter]:
    """
    获取系统注册支持的全部多格式物理文件导出器映射字典
    """
    return _exporters
