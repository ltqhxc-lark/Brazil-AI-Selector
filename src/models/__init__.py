# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 数据模型包初始化文件
此文件导出项目中定义的所有纯内存数据结构类 (Dataclasses)，
包括商品信息模型 Product、平台销售信息模型 Platform 以及各项费用分解模型 Fee。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee

__all__ = ["Product", "Platform", "Fee"]
