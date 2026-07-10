# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 金额财务计算工具
提供高精度金额加减乘除、百分比计算以及保留两位小数的操作，
底层通过 Decimal 实现，彻底杜绝浮点数计算造成的几分钱账目偏差。
"""

from decimal import Decimal
from typing import Union
from src.utils.rounding import round_half_up

def add_money(a: Union[float, int, str, Decimal], b: Union[float, int, str, Decimal]) -> float:
    """
    高精度金额相加 (a + b)
    
    Args:
        a: 加数1
        b: 加数2
        
    Returns:
        float: 相加后保留两位小数的结果
    """
    res = Decimal(str(a)) + Decimal(str(b))
    return round_half_up(res, 2)


def subtract_money(a: Union[float, int, str, Decimal], b: Union[float, int, str, Decimal]) -> float:
    """
    高精度金额相减 (a - b)
    
    Args:
        a: 被减数
        b: 减数
        
    Returns:
        float: 相减后保留两位小数的结果
    """
    res = Decimal(str(a)) - Decimal(str(b))
    return round_half_up(res, 2)


def multiply_money(a: Union[float, int, str, Decimal], b: Union[float, int, str, Decimal]) -> float:
    """
    高精度金额相乘 (a * b)
    
    Args:
        a: 乘数1
        b: 乘数2
        
    Returns:
        float: 相乘后保留两位小数的结果
    """
    res = Decimal(str(a)) * Decimal(str(b))
    return round_half_up(res, 2)


def divide_money(a: Union[float, int, str, Decimal], b: Union[float, int, str, Decimal]) -> float:
    """
    高精度金额相除 (a / b)
    
    Args:
        a: 被除数
        b: 除数
        
    Returns:
        float: 相除后保留两位小数的结果
        
    Raises:
        ZeroDivisionError: 当除数 b 为 0 时抛出
    """
    dec_b = Decimal(str(b))
    if dec_b == Decimal('0'):
        raise ZeroDivisionError("金额除法中除数不能为0。")
    res = Decimal(str(a)) / dec_b
    return round_half_up(res, 2)


def calculate_percentage(amount: Union[float, int, str, Decimal], rate: Union[float, int, str, Decimal]) -> float:
    """
    计算金额的指定百分比金额 (amount * rate)
    
    例如：
        计算 150.00 雷亚尔的 12% 佣金费用：
        calculate_percentage(150.00, 0.12) -> 18.00
        
    Args:
        amount: 基准金额
        rate: 百分比比率 (例如 12% 传入 0.12)
        
    Returns:
        float: 对应的百分比金额 (保留两位小数)
    """
    res = Decimal(str(amount)) * Decimal(str(rate))
    return round_half_up(res, 2)


def add_percentage(amount: Union[float, int, str, Decimal], rate: Union[float, int, str, Decimal]) -> float:
    """
    在基准金额上加上指定的百分比增幅 (amount * (1 + rate))
    
    例如：
        在商品进价 100.00 元基础上加 20% 利润溢价：
        add_percentage(100.00, 0.20) -> 120.00
        
    Args:
        amount: 基准金额
        rate: 溢价百分比 (例如 20% 传入 0.20)
        
    Returns:
        float: 溢价后的金额结果 (保留两位小数)
    """
    res = Decimal(str(amount)) * (Decimal('1') + Decimal(str(rate)))
    return round_half_up(res, 2)


def round_to_two(value: Union[float, int, str, Decimal]) -> float:
    """
    将任意数值以四舍五入精确保留到两位小数 (财务标准)
    
    Args:
        value: 待保留小数的数值
        
    Returns:
        float: 保留两位小数后的数值
    """
    return round_half_up(value, 2)
