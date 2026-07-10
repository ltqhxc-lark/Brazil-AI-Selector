# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 重量单位转换工具
提供克 (g)、千克 (kg)、磅 (lb)、盎司 (oz) 之间的精确互转。
"""

from typing import Union

# 国际标准换算常数 (以 克 g 为基准)
CONVERSION_FACTORS = {
    "g": 1.0,
    "kg": 1000.0,
    "lb": 453.59237,          # 1 磅 = 453.59237 克
    "oz": 28.349523125        # 1 盎司 = 28.349523125 克
}

def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """
    通用重量单位相互转换函数
    
    Args:
        value: 待转换的重量数值
        from_unit: 原始单位 (支持: 'g', 'kg', 'lb', 'oz', 不区分大小写)
        to_unit: 目标单位 (支持: 'g', 'kg', 'lb', 'oz', 不区分大小写)
        
    Returns:
        float: 转换后的重量值
        
    Raises:
        ValueError: 当传入不支持的单位时抛出
    """
    f_unit = from_unit.lower().strip()
    t_unit = to_unit.lower().strip()
    
    if f_unit not in CONVERSION_FACTORS or t_unit not in CONVERSION_FACTORS:
        raise ValueError(
            f"不支持的重量单位转换: 从 '{from_unit}' 到 '{to_unit}'。仅支持 'g', 'kg', 'lb', 'oz'。"
        )
        
    # 先将原始单位统一转换为 "克 (g)"，然后再转换为目标单位
    value_in_grams = value * CONVERSION_FACTORS[f_unit]
    converted_value = value_in_grams / CONVERSION_FACTORS[t_unit]
    return converted_value


def g_to_kg(g: float) -> float:
    """
    克转换为千克 (g -> kg)
    """
    return convert_weight(g, "g", "kg")


def kg_to_g(kg: float) -> float:
    """
    千克转换为克 (kg -> g)
    """
    return convert_weight(kg, "kg", "g")


def lb_to_g(lb: float) -> float:
    """
    磅转换为克 (lb -> g)
    """
    return convert_weight(lb, "lb", "g")


def g_to_lb(g: float) -> float:
    """
    克转换为磅 (g -> lb)
    """
    return convert_weight(g, "g", "lb")


def oz_to_g(oz: float) -> float:
    """
    盎司转换为克 (oz -> g)
    """
    return convert_weight(oz, "oz", "g")


def g_to_oz(g: float) -> float:
    """
    克转换为盎司 (g -> oz)
    """
    return convert_weight(g, "g", "oz")


def kg_to_lb(kg: float) -> float:
    """
    千克转换为磅 (kg -> lb)
    """
    return convert_weight(kg, "kg", "lb")


def lb_to_kg(lb: float) -> float:
    """
    磅转换为千克 (lb -> kg)
    """
    return convert_weight(lb, "lb", "kg")
