# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台插件基类与标准商品数据模型
采用 Pydantic v2 实现强类型、可校验的标准数据契约，彻底将采集模块与计算/AI模块解耦
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StandardProductData(BaseModel):
    """
    系统统一的数据交换实体 (DTO)
    无论是爬虫还是官方 API 获取的数据，均必须转化为该标准数据模型
    """
    platform: str = Field(..., description="商品所属平台 (如: mercado_livre, shopee, tiktok_shop, amazon_brasil)")
    raw_id: str = Field(..., description="平台商品原始 ID")
    title: str = Field(..., description="标准商品标题")
    price: float = Field(..., description="售价 (雷亚尔 BRL)")
    image_url: Optional[str] = Field(None, description="商品首图 URL")
    url: str = Field(..., description="商品详情页完整链接")
    
    # 尺寸与重量 (巴西尾程计算、头程运费的关键入参)
    weight_g: int = Field(0, description="商品重量 (克)")
    length_cm: int = Field(0, description="长度 (厘米)")
    width_cm: int = Field(0, description="宽度 (厘米)")
    height_cm: int = Field(0, description="高度 (厘米)")
    
    # 类目配置 (用于确定税目或平台特定的佣金扣点)
    category_id: Optional[str] = Field(None, description="平台原始类目编码")
    category_name: Optional[str] = Field(None, description="标准化类目名称")
    
    # 店铺与派送类型参数
    shipping_type: str = Field("standard", description="平台运送模式 (如: ML的'full','coleta'; Shopee的'fss')")
    seller_id: Optional[str] = Field(None, description="平台卖家编码")
    seller_name: Optional[str] = Field(None, description="平台卖家店铺名称")
    
    # 可选字段：采集到的前台互动数据 (用于 AI 爆款潜力预估)
    rating: float = Field(0.0, description="商品评分 (0.0 - 5.0)")
    reviews_count: int = Field(0, description="商品评价总数")
    sales_volume: int = Field(0, description="商品历史累计销量 (平台显示)")
    stock: Optional[int] = Field(None, description="平台当前库存数 (若可见)")
    
    # 平台专属参数快照（用作保留，防止后续需要特定平台的特有数据）
    raw_meta: Dict[str, Any] = Field(default_factory=dict, description="爬取出来的最底层完整 JSON 字段备份")


class BasePlatformPlugin:
    """
    所有平台数据抓取插件的抽象基类 (契约接口)
    """
    @property
    def platform_name(self) -> str:
        """
        返回平台唯一注册标识（如 'mercado_livre'）
        """
        raise NotImplementedError("每一个插件必须定义其 platform_name 属性")

    def fetch_product_by_id(self, raw_id: str) -> StandardProductData:
        """
        通过商品平台原始 ID 获取，并清洗转换成标准 StandardProductData 格式
        """
        raise NotImplementedError("插件必须实现 fetch_product_by_id 方法")

    def fetch_product_by_url(self, url: str) -> StandardProductData:
        """
        通过解析商品网页链接获取，并清洗转换成标准 StandardProductData 格式
        """
        raise NotImplementedError("插件必须实现 fetch_product_by_url 方法")
