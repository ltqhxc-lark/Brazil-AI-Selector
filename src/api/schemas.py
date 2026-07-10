# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - API 输入与输出 Pydantic 数据校验模型 (Schemas)
包含强类型的数据绑定、属性边界检查（如防范负数金额与零克重），确保 API 输入 100% 安全规整。
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

# ==============================================================================
# 1. 基础请求 Sub-Models
# ==============================================================================

class ProductRequest(BaseModel):
    """
    商品物理属性请求校验模型
    """
    sku: str = Field(..., min_length=1, description="商品唯一识别编码 (SKU)")
    name: str = Field(..., min_length=1, description="商品名称")
    cost_price_brl: float = Field(..., description="采购进价/到岸货值成本 (BRL)")
    weight_g: float = Field(..., description="商品包装实重 (单位: 克 g)")
    length_cm: float = Field(..., description="包装长度 (厘米)")
    width_cm: float = Field(..., description="包装宽度 (厘米)")
    height_cm: float = Field(..., description="包装高度 (厘米)")
    category: str = Field(..., min_length=1, description="商品分类标签 (用于匹配税费和佣金比例)")
    declared_value_usd: float = Field(0.0, description="跨境直邮模式海关申报美元货值 (选填)")

    @field_validator("cost_price_brl", "declared_value_usd")
    @classmethod
    def validate_non_negative_prices(cls, v: float, info) -> float:
        if v < 0.0:
            raise ValueError(f"字段 '{info.field_name}' 不能为负数，当前传入为: {v}")
        return v

    @field_validator("weight_g", "length_cm", "width_cm", "height_cm")
    @classmethod
    def validate_positive_bounds(cls, v: float, info) -> float:
        if v <= 0.0:
            raise ValueError(f"物理规格字段 '{info.field_name}' 必须为正数且大于 0，当前传入为: {v}")
        return v


class PlatformRequest(BaseModel):
    """
    平台销售参数请求校验模型
    """
    platform_id: str = Field(..., description="平台唯一标志符 (如 mercado_livre_brasil)")
    platform_name: str = Field(..., description="平台显示名称")
    selling_price_brl: float = Field(..., description="商品预估销售售价 (BRL)")
    seller_level: str = Field("normal", description="卖家账户信誉等级 (如 platinum, gold)")
    participate_fss: bool = Field(True, description="是否参与营销极速免邮包 (Shopee FSS)")
    affiliate_rate: float = Field(0.0, description="联盟达人佣金分账比例 (0.00 至 0.99)")

    @field_validator("selling_price_brl")
    @classmethod
    def validate_selling_price(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError(f"销售价格不能为负数，当前传入为: {v}")
        return v

    @field_validator("affiliate_rate")
    @classmethod
    def validate_affiliate_rate(cls, v: float) -> float:
        if not (0.0 <= v < 1.0):
            raise ValueError(f"联盟/达人分账扣点必须处于 [0.0, 1.0) 之间，当前传入为: {v}")
        return v


# ==============================================================================
# 2. 顶层业务请求 Models
# ==============================================================================

class AnalysisRequest(BaseModel):
    """
    精算分析请求模型
    """
    product: ProductRequest = Field(..., description="商品物理数据")
    platform: PlatformRequest = Field(..., description="平台销售设置")
    annual_revenue_brl: float = Field(0.0, description="商家历史 12 个月累计年销售总额 (计算本土阶梯税率)")
    is_cross_border: bool = Field(False, description="是否采用 Remessa Conforme 跨境直邮模式计税")
    exchange_rate_usd_brl: float = Field(5.0, description="跨境申报汇率比率")

    @field_validator("annual_revenue_brl", "exchange_rate_usd_brl")
    @classmethod
    def validate_positive_parameters(cls, v: float, info) -> float:
        if v < 0.0:
            raise ValueError(f"参数 '{info.field_name}' 不能为负数，当前为: {v}")
        return v


class ReportRequest(BaseModel):
    """
    编译及物理导出报告请求模型
    """
    product: ProductRequest = Field(..., description="商品物理数据")
    platform: PlatformRequest = Field(..., description="平台销售设置")
    format: str = Field(..., description="请求导出的物理文件格式 (仅限: json, csv, xlsx, pdf)")
    annual_revenue_brl: float = Field(0.0, description="商家历史累计年销售总额")
    is_cross_border: bool = Field(False, description="是否采用跨境直邮计税")
    exchange_rate_usd_brl: float = Field(5.0, description="跨境申报汇率")

    @field_validator("format")
    @classmethod
    def validate_format_whitelist(cls, v: str) -> str:
        fmt = v.lower().strip()
        whitelist = {"json", "csv", "xlsx", "pdf"}
        if fmt not in whitelist:
            raise ValueError(f"不支持的物理文件导出格式: '{v}'。仅限: {list(whitelist)}")
        return fmt


# ==============================================================================
# 3. API 输出响应 Models
# ==============================================================================

class AnalysisResponse(BaseModel):
    """
    精算分析统一响应模型
    """
    success: bool = Field(True, description="处理是否成功")
    revenue: float = Field(..., description="预估营收售价 (BRL)")
    net_profit: float = Field(..., description="纯利总金额 (BRL)")
    margin: float = Field(..., description="纯利润率 (浮点)")
    formatted_margin: str = Field(..., description="格式化纯利率 (如 '35.20%')")
    formatted_profit: str = Field(..., description="格式化纯利金额 (如 'R$ 31,08')")
    overall_alert_level: str = Field(..., description="综合预警等级 ('green', 'yellow', 'red')")
    suggestions: List[str] = Field(default_factory=list, description="精选落地行动指令清单")
    details: Dict[str, Any] = Field(default_factory=dict, description="底层各项税、费及分项成本字典快照")


class ReportResponse(BaseModel):
    """
    物理报告编译导出统一响应模型
    """
    success: bool = Field(True, description="导出是否成功")
    file_path: str = Field(..., description="生成文件的相对URL或局部文件路径")
    filename: str = Field(..., description="生成文件的标准文件名")
    format: str = Field(..., description="文件格式名称")
    message: str = Field(..., description="执行成功的描述文案")


class HealthResponse(BaseModel):
    """
    健康检查接口响应模型
    """
    status: str = Field("UP", description="服务健康状态")
    project_name: str = Field("Brazil-AI-Selector", description="项目名称")
    version: str = Field("1.0.0", description="系统主版本号")


class ErrorResponse(BaseModel):
    """
    系统及业务异常统一报错响应模型
    """
    success: bool = Field(False, description="状态标识")
    message: str = Field(..., description="宏观异常解释")
    errors: List[str] = Field(default_factory=list, description="微观具体异常或错误描述列表")
