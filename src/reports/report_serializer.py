# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报告领域模型序列化工具
提供将嵌套复杂结构的 BusinessReport DTO 转换为标准 Python Dict 及精美排版的 JSON 字符串的功能。
"""

import json
from dataclasses import asdict
from typing import Dict, Any
from src.reports.report_models import BusinessReport

class ReportSerializer:
    """
    报告数据序列化器 (SOLID - 序列化职责)
    实现数据实体与外部传输格式 (JSON/Dict) 的无缝双向转换，为未来的 Web 界面、REST API 以及命令行渲染打下稳固基础。
    """

    def to_dict(self, report: BusinessReport) -> Dict[str, Any]:
        """
        将 BusinessReport 嵌套实体递归序列化为标准 Python 字典类型
        
        Args:
            report: 待处理的 BusinessReport 根容器
            
        Returns:
            Dict[str, Any]: 树状层级结构的字典对象
        """
        if not isinstance(report, BusinessReport):
            raise TypeError("序列化器仅支持处理 BusinessReport 类型的报告。")
        # 利用标准 dataclasses 递归转换方法，安全、无副作用
        return asdict(report)

    def to_json(self, report: BusinessReport, indent: int = 2) -> str:
        """
        将 BusinessReport 嵌套实体序列化为美观可读的 JSON 字符串
        
        Args:
            report: 待处理的 BusinessReport 根容器
            indent: 缩进空格数，默认 2
            
        Returns:
            str: 格式化后的 JSON 文本 (支持 UTF-8 中文不转码)
        """
        dict_data = self.to_dict(report)
        # ensure_ascii=False: 确保输出的中文、巴葡字符直接展示，不被强制转码为 \uXXXX
        return json.dumps(dict_data, ensure_ascii=False, indent=indent)
