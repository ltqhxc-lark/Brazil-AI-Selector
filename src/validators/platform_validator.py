# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台销售参数验证器
"""

from src.models.platform import Platform
from src.validators import ValidationResult

# 2026年系统支持的巴西本土三大主流平台 ID 集合
SUPPORTED_PLATFORMS = {
    "mercado_livre_brasil",
    "shopee_brasil",
    "tiktok_shop_brasil"
}

# 美客多支持的信誉等级 (用于精确折扣运费核算)
MERCADO_LIVRE_LEVELS = {
    "platinum",
    "gold",
    "leader",
    "normal",
    "red"
}

def validate_platform(platform: Platform) -> ValidationResult:
    """
    校验平台销售参数 (Platform) 的合法性
    
    校验规则：
        1. 平台唯一标识 platform_id 必须属于系统支持的集合 (SUPPORTED_PLATFORMS)
        2. 售价 selling_price_brl 必须大于等于 0
        3. 卖家等级 seller_level 必须合法 (针对美客多需要落在特定的几档内)
        4. 分销抽佣率 affiliate_rate 必须在合理的百分比范围内 (0.00 至 0.99 之间)
        
    Args:
        platform: 待校验的 Platform 实例
        
    Returns:
        ValidationResult: 统一的校验结果对象，包含是否成功及错误列表
    """
    errors = []
    
    # 1. 校验平台 ID 是否为空以及是否支持
    if platform.platform_id is None or not str(platform.platform_id).strip():
        errors.append("平台标识 (platform_id) 不能为空。")
    else:
        pid = platform.platform_id.lower().strip()
        if pid not in SUPPORTED_PLATFORMS:
            errors.append(f"不支持的平台标识: '{platform.platform_id}'。当前仅支持 {list(SUPPORTED_PLATFORMS)}。")
            
    # 2. 校验销售售价
    if platform.selling_price_brl is None:
        errors.append("商品销售售价字段缺失。")
    elif platform.selling_price_brl < 0:
        errors.append(f"销售价格不能为负数，当前值为: R$ {platform.selling_price_brl}。")
        
    # 3. 校验特定平台的卖家等级
    if platform.platform_id:
        pid = platform.platform_id.lower().strip()
        level = str(platform.seller_level).lower().strip()
        if pid == "mercado_livre_brasil":
            if level not in MERCADO_LIVRE_LEVELS:
                errors.append(
                    f"美客多平台不支持卖家等级 '{platform.seller_level}'。合法等级为: {list(MERCADO_LIVRE_LEVELS)}。"
                )
        else:
            # 虾皮或 TikTok 默认支持普通等级
            if level != "normal" and not level:
                errors.append(f"该平台非美客多，卖家等级通常应设置为 'normal'，当前值为: '{platform.seller_level}'。")
                
    # 4. 校验达人分销佣金比例
    if platform.affiliate_rate is None:
        errors.append("达人分销抽佣率字段缺失。")
    elif not (0.0 <= platform.affiliate_rate < 1.0):
        errors.append(f"达人分销抽佣比例必须处于 [0.0, 1.0) 之间，当前值为: {platform.affiliate_rate}。")

    # 汇总校验结果
    if errors:
        return ValidationResult(
            success=False,
            message=f"平台销售参数校验失败，共发现 {len(errors)} 处错误。",
            errors=errors
        )
    else:
        return ValidationResult(
            success=True,
            message="平台销售参数校验 100% 通过。"
        )
