# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 商品数据模型验证器
"""

from src.models.product import Product
from src.validators import ValidationResult

def validate_product(product: Product) -> ValidationResult:
    """
    校验商品 (Product) 数据的合法性
    
    校验规则：
        1. SKU 不能为空 (不为 None 且去除首尾空格后长度大于 0)
        2. 产品名称不能为空 (不为 None 且去除首尾空格后长度大于 0)
        3. 包装重量必须大于 0 克 (weight_g > 0)
        4. 采购成本价必须大于等于 0 雷亚尔 (cost_price_brl >= 0)
        5. 商品包装尺寸 (长、宽、高) 必须大于 0 厘米 (用于物流体积重评估)
        
    Args:
        product: 待校验的 Product 实例
        
    Returns:
        ValidationResult: 统一的校验结果对象，包含是否成功及错误明细列表
    """
    errors = []
    
    # 1. 校验 SKU
    if product.sku is None or not str(product.sku).strip():
        errors.append("商品 SKU 不能为空。")
        
    # 2. 校验商品名称
    if product.name is None or not str(product.name).strip():
        errors.append("商品名称不能为空。")
        
    # 3. 校验重量
    if product.weight_g is None:
        errors.append("商品重量字段缺失。")
    elif product.weight_g <= 0:
        errors.append(f"商品重量必须大于 0g，当前值为: {product.weight_g}g。")
        
    # 4. 校验成本价
    if product.cost_price_brl is None:
        errors.append("商品成本价字段缺失。")
    elif product.cost_price_brl < 0:
        errors.append(f"商品成本价不能为负数，当前值为: R$ {product.cost_price_brl}。")
        
    # 5. 校验三维尺寸 (体积重辅助参数)
    if product.length_cm is None or product.length_cm <= 0:
        errors.append(f"商品包装长度必须大于 0 cm，当前值为: {product.length_cm} cm。")
    if product.width_cm is None or product.width_cm <= 0:
        errors.append(f"商品包装宽度必须大于 0 cm，当前值为: {product.width_cm} cm。")
    if product.height_cm is None or product.height_cm <= 0:
        errors.append(f"商品包装高度必须大于 0 cm，当前值为: {product.height_cm} cm。")

    # 汇总校验结果
    if errors:
        return ValidationResult(
            success=False,
            message=f"商品数据校验失败，共发现 {len(errors)} 处不符合规则的错误。",
            errors=errors
        )
    else:
        return ValidationResult(
            success=True,
            message="商品数据校验 100% 通过。"
        )
