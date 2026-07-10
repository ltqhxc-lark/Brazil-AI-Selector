# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务计算器抽象基类
"""

class BaseCalculator:
    """
    财务与税费计算器的基类
    """
    def calculate(self, *args, **kwargs) -> dict:
        """
        核心计算入口，返回计算所得的各项明细字典
        """
        raise NotImplementedError
