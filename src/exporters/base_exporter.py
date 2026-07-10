# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 导出层统一契约与基类
定义所有物理文件导出器 (XLSX, PDF, CSV, JSON) 继承的 BaseExporter 接口，
以及统一的导出执行结果状态容器 ExportResult。
"""

from dataclasses import dataclass, field
from typing import List
from abc import ABC, abstractmethod
from src.reports.report_models import BusinessReport

@dataclass
class ExportResult:
    """
    统一的导出结果状态数据模型 (Dataclass)
    """
    success: bool                       # 导出物理文件是否成功
    file_path: str                      # 成功后物理文件的绝对或相对路径
    message: str                        # 提示/成功反馈文案
    errors: List[str] = field(default_factory=list) # 导出失败时的具体技术及物理异常明细列表


class BaseExporter(ABC):
    """
    文件导出器通用接口契约 (SOLID - 接口隔离/依赖倒置)
    所有的物理导出类（Excel, PDF, CSV, JSON）必须继承该基类并实现三大核心契约方法。
    """

    @abstractmethod
    def export(self, report: BusinessReport, output_path: str) -> ExportResult:
        """
        核心物理导出入口
        
        Args:
            report: 已经构建好完整数据的 BusinessReport DTO
            output_path: 保存物理文件的路径
            
        Returns:
            ExportResult: 统一文件导出结果
        """
        pass

    @abstractmethod
    def supports(self, format_name: str) -> bool:
        """
        核对当前导出器是否支持特定的物理文件格式名称
        
        Args:
            format_name: 格式缩写 (如: 'xlsx', 'pdf', 'csv', 'json')
            
        Returns:
            bool: 是否支持
        """
        pass

    def validate(self, report: BusinessReport) -> bool:
        """
        统一的导出前 DTO 安全性核对
        
        Args:
            report: 待核对的报告 DTO
            
        Returns:
            bool: 报告是否合格且内容完整
        """
        # 1. 检验是否为 BusinessReport 实体类型
        if not isinstance(report, BusinessReport):
            return False
            
        # 2. 检查基本关键属性是否完整
        if not report.summary or not report.financial:
            return False
            
        return True
