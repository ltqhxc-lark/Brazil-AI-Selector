# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 数据格式化显示工具
提供高可读性的数据格式化输出，包括：
1. 巴西雷亚尔本地化货币字符串 (R$ 1.234.567,89)
2. 美元标准货币字符串 ($1,234,567.89)
3. 百分比字符串 (12.50%)
4. 重量高可读性字符串 (1.25 kg 或 350g)
本模块逻辑不依赖任何操作系统本地 Local 环境，保证跨平台、跨 Docker 容器结果一致。
"""

from decimal import Decimal
from typing import Union

def format_brl(value: Union[float, int, str, Decimal]) -> str:
    """
    格式化为巴西雷亚尔 (BRL / R$) 格式
    
    巴西本地化规范：
        1. 货币前缀为 "R$ "
        2. 千分位分隔符为点号 "."
        3. 小数分隔符为逗号 ","
        
    例如：
        1234567.89 -> "R$ 1.234.567,89"
        -50.00 -> "R$ -50,00"
        
    Args:
        value: 待格式化的数值
        
    Returns:
        str: 格式化后的巴西雷亚尔字符串
    """
    if value is None:
        return "R$ 0,00"
    num = float(value)
    
    # 获取带正负号的标准美式两位小数格式: e.g., 1,234,567.89 或 -50.00
    formatted_us = f"{num:,.2f}"
    
    # 通过字符替换，无缝转换为巴西本土千位点、分位逗格式
    # 替换路线: 逗号 -> 临时符号 | 点号 -> 逗号 | 临时符号 -> 点号
    placeholder = "___TEMP_COMMA___"
    brazil_notation = formatted_us.replace(",", placeholder).replace(".", ",").replace(placeholder, ".")
    
    # 拼接 BRL 货币前缀
    return f"R$ {brazil_notation}"


def format_usd(value: Union[float, int, str, Decimal]) -> str:
    """
    格式化为标准美元 (USD / $) 格式
    
    格式规范：
        千分位分隔符为 ","，小数分隔符为 "."
        
    例如：
        1234567.89 -> "$1,234,567.89"
        
    Args:
        value: 待格式化的数值
        
    Returns:
        str: 格式化后的美元字符串
    """
    if value is None:
        return "$0.00"
    num = float(value)
    return f"${num:,.2f}"


def format_percentage(value: Union[float, int, str, Decimal], decimals: int = 2) -> str:
    """
    将小数值格式化为百分比字符串 (e.g. 0.125 -> "12.50%")
    
    Args:
        value: 百分比小数值 (如 0.12 代表 12%)
        decimals: 保留的小数位数，默认 2
        
    Returns:
        str: 格式化后的百分比字符串
    """
    if value is None:
        return "0.00%"
    # 乘以 100 并以标准浮点保留小数
    percentage_value = float(value) * 100.0
    return f"{percentage_value:.{decimals}f}%"


def format_weight(weight_g: float, auto_unit: bool = True) -> str:
    """
    格式化重量为易读字符串
    
    例如：
        1250 g -> "1.25 kg" (若开启 auto_unit)
        350 g -> "350g"
        
    Args:
        weight_g: 重量值，单位为克 (g)
        auto_unit: 是否自动转换为最合适的单位 (若 >= 1000g，自动以 kg 表示)
        
    Returns:
        str: 重量格式化易读字符串
    """
    if weight_g is None or weight_g < 0:
        return "0g"
        
    if auto_unit and weight_g >= 1000.0:
        weight_kg = weight_g / 1000.0
        # 消除尾部的多余零，保持易读
        if weight_kg == int(weight_kg):
            return f"{int(weight_kg)} kg"
        return f"{weight_kg:.2f} kg"
    else:
        return f"{int(weight_g)}g"
