# -*- coding: utf-8 -*-
"""
选品财务与规格计算器单元测试
"""

import pytest
from src.models.product import Product
from src.product_selection.calculator import ProductSelectionCalculator

def test_volumetric_weight():
    """测试体积重量计算逻辑以及尺寸限制"""
    # 正常尺寸：长10cm, 宽10cm, 高6cm => 10*10*6/6 = 100g
    product_ok = Product(
        sku="SKU-OK", name="OK", cost_price_brl=10.0, weight_g=200.0,
        length_cm=10.0, width_cm=10.0, height_cm=6.0, category="e"
    )
    vol_g = ProductSelectionCalculator.calculate_volumetric_weight_g(product_ok)
    assert vol_g == 100.0

    # 边界限制：尺寸小于等于 0 抛出 ValueError
    product_bad = Product(
        sku="SKU-BAD", name="Bad", cost_price_brl=10.0, weight_g=200.0,
        length_cm=0.0, width_cm=10.0, height_cm=6.0, category="e"
    )
    with pytest.raises(ValueError, match="商品的长、宽、高尺寸必须严格大于 0"):
        ProductSelectionCalculator.calculate_volumetric_weight_g(product_bad)


def test_estimated_selling_price_precision():
    """测试建议售价反推公式、高精度 Decimal 运算及费率验证"""
    # 正常入参
    price = ProductSelectionCalculator.calculate_estimated_selling_price(
        cost_price_brl=30.0,
        estimated_shipping_brl=15.0,
        platform_fee_ratio=0.15,
        tax_ratio=0.10,
        target_margin_ratio=0.20
    )
    # 30 + 15 = 45; 1 - 0.15 - 0.10 - 0.20 = 0.55 => 45 / 0.55 = 81.8181... => 四舍五入后 81.82
    assert price == 81.82

    # 兜底测试：分母极小时采用 2.5 倍安全毛利价
    price_safe = ProductSelectionCalculator.calculate_estimated_selling_price(
        cost_price_brl=10.0,
        estimated_shipping_brl=5.0,
        platform_fee_ratio=0.40,
        tax_ratio=0.35,
        target_margin_ratio=0.21 # sum = 0.96 => denominator = 0.04 <= 0.05
    )
    # (10 + 5) * 2.5 = 37.50
    assert price_safe == 37.50

    # 费率合理区间边界拦截
    with pytest.raises(ValueError, match="平台费率范围必须在"):
        ProductSelectionCalculator.calculate_estimated_selling_price(10, 5, -0.01, 0.1, 0.2)
    with pytest.raises(ValueError, match="税率范围必须在"):
        ProductSelectionCalculator.calculate_estimated_selling_price(10, 5, 0.1, 1.05, 0.2)
    with pytest.raises(ValueError, match="之和必须严格小于 1.0"):
        ProductSelectionCalculator.calculate_estimated_selling_price(10, 5, 0.4, 0.4, 0.2)


def test_roi_and_margin_division_by_zero():
    """测试 ROI 和利润率计算，并对除以 0 的非正常边界进行严格拦截验证"""
    # 正常计算
    roi = ProductSelectionCalculator.calculate_roi(20.0, 100.0) # 20 / 100 = 0.2000
    assert roi == 0.2000

    margin = ProductSelectionCalculator.calculate_margin(15.0, 75.0) # 15 / 75 = 0.2000
    assert margin == 0.2000

    # 采购成本为 0 / 负数时抛出 ValueError
    with pytest.raises(ValueError, match="商品采购成本必须严格大于 0"):
        ProductSelectionCalculator.calculate_roi(10.0, 0.0)
    with pytest.raises(ValueError, match="商品采购成本必须严格大于 0"):
        ProductSelectionCalculator.calculate_roi(10.0, -5.0)

    # 销售售价为 0 / 负数时抛出 ValueError
    with pytest.raises(ValueError, match="销售收入（售价）必须严格大于 0"):
        ProductSelectionCalculator.calculate_margin(10.0, 0.0)
    with pytest.raises(ValueError, match="销售收入（售价）必须严格大于 0"):
        ProductSelectionCalculator.calculate_margin(10.0, -1.0)
