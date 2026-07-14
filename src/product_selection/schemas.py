# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品 API 数据校验模型 (Pydantic)
"""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

class ProductCreateSchema(BaseModel):
    sku: str = Field(..., description="唯一的 SKU 代码", min_length=1, max_length=64)
    name: str = Field(..., description="商品名称", min_length=1, max_length=256)
    cost_price_brl: Decimal = Field(..., description="采购成本价 (BRL)", gt=0)
    weight_g: Decimal = Field(..., description="商品物理重量 (g)", ge=0)
    length_cm: Decimal = Field(..., description="商品外包装长 (cm)", ge=0)
    width_cm: Decimal = Field(..., description="商品外包装宽 (cm)", ge=0)
    height_cm: Decimal = Field(..., description="商品外包装高 (cm)", ge=0)
    category: str = Field(..., description="分类标签", min_length=1, max_length=128)
    declared_value_usd: Decimal = Field(Decimal("0.00"), description="申报价值 (USD)", ge=0)


class MarketDataSchema(BaseModel):
    average_selling_price_brl: Decimal = Field(..., description="市场平均建议零售价 (BRL)", gt=0)
    competitor_count: int = Field(..., description="主要卖家竞对数量", ge=0)
    demand_score: Decimal = Field(..., description="市场需求度评分 (0.0-10.0)", ge=0, le=10)
    trend_factor: Decimal = Field(Decimal("1.0"), description="销售趋势因子", ge=0)


class SelectionCriteriaSchema(BaseModel):
    target_roi: Decimal = Field(Decimal("0.30"), description="期望目标 ROI", ge=0)
    min_net_margin: Decimal = Field(Decimal("0.15"), description="最低可接受纯利润率", ge=0)
    
    profit_weight: Decimal = Field(Decimal("0.40"), description="利润维度打分权重", ge=0, le=1)
    demand_weight: Decimal = Field(Decimal("0.30"), description="需求维度打分权重", ge=0, le=1)
    competition_weight: Decimal = Field(Decimal("0.20"), description="竞争维度打分权重", ge=0, le=1)
    logistics_weight: Decimal = Field(Decimal("0.10"), description="物流维度打分权重", ge=0, le=1)
    
    s_min_score: Decimal = Field(Decimal("80.00"), description="S 级推荐最低分数边界", ge=0, le=100)
    a_min_score: Decimal = Field(Decimal("70.00"), description="A 级推荐最低分数边界", ge=0, le=100)
    b_min_score: Decimal = Field(Decimal("60.00"), description="B 级推荐最低分数边界", ge=0, le=100)


class SingleEvaluateRequest(BaseModel):
    product: ProductCreateSchema
    market_data: MarketDataSchema
    criteria: Optional[SelectionCriteriaSchema] = None
    platform_id: str = Field("mercado_livre_brasil", description="平台标识符")
    platform_name: str = Field("Mercado Livre Brasil", description="平台名称")


class BatchEvaluateRequest(BaseModel):
    products: List[ProductCreateSchema]
    market_data_list: List[MarketDataSchema]
    criteria: Optional[SelectionCriteriaSchema] = None
    platform_id: str = Field("mercado_livre_brasil", description="平台标识符")
    platform_name: str = Field("Mercado Livre Brasil", description="平台名称")


class ProductResponseSchema(BaseModel):
    id: int
    sku: str
    name: str
    cost_price_brl: Decimal
    weight_g: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    category: str
    declared_value_usd: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class MarketDataResponseSchema(BaseModel):
    id: int
    product_id: int
    average_selling_price_brl: Decimal
    competitor_count: int
    demand_score: Decimal
    trend_factor: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class SelectionResultResponse(BaseModel):
    id: int
    product_id: int
    market_data_id: int
    
    estimated_retail_price_brl: Decimal
    estimated_net_profit_brl: Decimal
    estimated_roi: Decimal
    estimated_margin: Decimal
    estimated_tax_brl: Decimal
    estimated_platform_fee_brl: Decimal
    estimated_shipping_brl: Decimal
    estimated_gross_profit_brl: Decimal
    
    total_score: Decimal
    profit_score: Decimal
    demand_score: Decimal
    competition_score: Decimal
    logistics_score: Decimal
    recommendation_level: str
    
    recommendation_reasons: List[str]
    risk_warnings: List[str]
    
    evaluated_at: datetime
    created_at: datetime
    
    product: Optional[ProductResponseSchema] = None
    market_data: Optional[MarketDataResponseSchema] = None

    class Config:
        from_attributes = True


class BatchEvaluateResponse(BaseModel):
    results: List[SelectionResultResponse]
    errors: List[Tuple[str, str]]
