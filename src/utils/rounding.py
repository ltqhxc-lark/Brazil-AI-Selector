# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 精确舍入算法工具箱
提供高精度舍入操作，包含银行家舍入（五舍六入双留双，近偶舍入）、标准四舍五入、向上取整和向下取整。
内部基于 Python decimal 模块实现，彻底避免 IEEE-754 浮点数丢失精度的缺陷。
"""

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from typing import Union

def round_bankers(value: Union[float, int, str, Decimal], decimals: int = 2) -> float:
    """
    银行家舍入 (Banker's Rounding / 近偶舍入)
    
    规则：
        四舍六入，逢五看奇偶。若保留位后面是5，且5后面无数字：
        若5前面一位是奇数则进位，若5前面一位是偶数则舍去（使保留位变为偶数）。
        这是 ISO 标准和 Python 默认的舍入方式，能最大程度减少累加时的系统误差。
        
    Args:
        value: 待舍入的数值 (支持 float, int, str, Decimal)
        decimals: 保留的小数位数，默认为 2
        
    Returns:
        float: 舍入后的浮点数结果
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # 构建精度模版，如 "0.01" 表示保留两位
    precision = Decimal('1.' + '0' * decimals) if decimals > 0 else Decimal('1')
    return float(value.quantize(precision, rounding=ROUND_HALF_EVEN))


def round_half_up(value: Union[float, int, str, Decimal], decimals: int = 2) -> float:
    """
    标准四舍五入 (Standard Mathematical Rounding / 逢五进一)
    
    规则：
        不管前一位奇偶性，只要第 decimals + 1 位大于等于 5，均向进 1。
        符合大多数财务会计和普通人群的直观习惯。
        
    Args:
        value: 待舍入的数值
        decimals: 保留的小数位数，默认为 2
        
    Returns:
        float: 四舍五入后的浮点数结果
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
        
    precision = Decimal('1.' + '0' * decimals) if decimals > 0 else Decimal('1')
    return float(value.quantize(precision, rounding=ROUND_HALF_UP))


def round_ceiling(value: Union[float, int, str, Decimal], decimals: int = 2) -> float:
    """
    向上取整 (Ceiling / 往正无穷方向舍入)
    
    规则：
        在指定小数位上，只要后面有非零值，直接进位。常用于保守估计物流成本或运费。
        
    Args:
        value: 待舍入的数值
        decimals: 保留的小数位数，默认为 2
        
    Returns:
        float: 向上取整后的浮点数结果
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
        
    precision = Decimal('1.' + '0' * decimals) if decimals > 0 else Decimal('1')
    return float(value.quantize(precision, rounding=ROUND_CEILING))


def round_floor(value: Union[float, int, str, Decimal], decimals: int = 2) -> float:
    """
    向下取整 (Floor / 往负无穷方向舍入)
    
    规则：
        在指定小数位上，直接舍弃后面的一切多余数字。
        
    Args:
        value: 待舍入的数值
        decimals: 保留的小数位数，默认为 2
        
    Returns:
        float: 向下取整后的浮点数结果
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
        
    precision = Decimal('1.' + '0' * decimals) if decimals > 0 else Decimal('1')
    return float(value.quantize(precision, rounding=ROUND_FLOOR))
