# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报表导出抽象基类
"""

import os
from typing import List, Dict, Any

# 确保根目录下 exports/ 的各级分类文件夹物理存在
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs(os.path.join(BASE_DIR, "exports", "excel"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "exports", "csv"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "exports", "pdf"), exist_ok=True)

class BaseExporter:
    """
    数据及报告导出适配器的基类
    """
    @property
    def format_extension(self) -> str:
        """
        返回导出的文件后缀名 (如 'xlsx', 'csv', 'pdf')
        """
        raise NotImplementedError

    def export(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        执行具体的数据导出。
        :param data: 待导出的标准商品及财务试算混合列表
        :param filename: 输出文件名（不包含路径和后缀，系统自动组装）
        :return: 生成的导出文件绝对路径
        """
        raise NotImplementedError("每一个导出器必须实现 export 方法")
