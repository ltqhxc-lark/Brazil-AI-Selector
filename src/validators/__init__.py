# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 验证器包初始化文件
定义了统一的校验结果模型 ValidationResult，并公开商品、平台与配置文件的核心校验器。
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationResult:
    """
    统一的校验结果数据模型
    所有校验器函数禁止直接抛出 Exception 异常，必须捕获错误并返回此实例。
    """
    success: bool                  # 校验是否通过 (True 为通过，False 为未通过)
    message: str                 # 总体校验说明信息 (如 "校验通过" 或 "校验失败，共有 2 处错误")
    errors: List[str] = field(default_factory=list) # 具体的错误原因列表 (若 success 为 True，则为空列表)

# 导出公共核心组件与函数
from src.validators.product_validator import validate_product
from src.validators.platform_validator import validate_platform
from src.validators.config_validator import validate_config

__all__ = ["ValidationResult", "validate_product", "validate_platform", "validate_config"]
