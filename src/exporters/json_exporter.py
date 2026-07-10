# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - JSON 数据报告物理导出器
"""

import os
from src.reports.report_models import BusinessReport
from src.reports.report_serializer import ReportSerializer
from src.exporters.base_exporter import BaseExporter, ExportResult

class JSONExporter(BaseExporter):
    """
    JSON 格式物理文件导出器
    主要用于系统数据对账、Web 端 API 数据推送、或者快速将财务分析看板转换为轻量持久化物理文件。
    """

    def __init__(self) -> None:
        self._serializer = ReportSerializer()

    def supports(self, format_name: str) -> bool:
        return format_name.lower().strip() == "json"

    def export(self, report: BusinessReport, output_path: str) -> ExportResult:
        """
        核心物理导出：将 DTO 转换为高读性的 UTF-8 JSON 文本文件
        """
        # 1. 安全前置校验
        if not self.validate(report):
            return ExportResult(
                success=False,
                file_path="",
                message="JSON 导出失败：BusinessReport DTO 结构缺失或内容不完整。",
                errors=["BusinessReport instance validation failed."]
            )

        try:
            # 自动创建父级物理文件夹 (如 exports/ 等)
            parent_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(parent_dir, exist_ok=True)

            # 2. 序列化转换
            json_text = self._serializer.to_json(report, indent=2)

            # 3. 物理磁盘写入
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_text)

            return ExportResult(
                success=True,
                file_path=os.path.abspath(output_path),
                message=f"成功将财务分析报告导出为 JSON 文件！物理路径: {output_path}"
            )
        except Exception as e:
            return ExportResult(
                success=False,
                file_path="",
                message=f"JSON 导出运行异常: {str(e)}",
                errors=[f"File I/O or serialization error: {str(e)}"]
            )
