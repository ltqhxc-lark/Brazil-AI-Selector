# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - SQLite 数据库 ORM 模型定义
使用 SQLAlchemy 2.0 编写，完全契合巴西电商业务场景
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# 声明式基类
class Base(DeclarativeBase):
    pass

class Product(Base):
    """
    1. 选品主表 (products)
    存储所有抓取、录入及 AI 分析过的标准商品基本数据
    """
    __tablename__ = "products"

    # 主键格式：PLATFORM_PRODUCTID (例如: ML_MLB1234567)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # 来源平台 (mercado_livre, shopee 等)
    raw_id: Mapped[str] = mapped_column(String(64), nullable=False)               # 平台原始的商品 ID
    title: Mapped[str] = mapped_column(String(256), nullable=False)               # 商品名称
    image_url: Mapped[Optional[str]] = mapped_column(String(512))                 # 商品主图链接
    current_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # 当前售价 (雷亚尔 BRL)
    weight_g: Mapped[Optional[int]] = mapped_column(Integer, default=0)           # 重量 (克)
    length_cm: Mapped[Optional[int]] = mapped_column(Integer, default=0)          # 长度 (厘米)
    width_cm: Mapped[Optional[int]] = mapped_column(Integer, default=0)           # 宽度 (厘米)
    height_cm: Mapped[Optional[int]] = mapped_column(Integer, default=0)          # 高度 (厘米)
    category_id: Mapped[Optional[str]] = mapped_column(String(64))                # 类目 ID
    category_name: Mapped[Optional[str]] = mapped_column(String(128))              # 类目名称
    shipping_type: Mapped[Optional[str]] = mapped_column(String(32))              # 配送类型 (如 full, coleta, standard)
    seller_id: Mapped[Optional[str]] = mapped_column(String(64))                  # 卖家 ID
    seller_name: Mapped[Optional[str]] = mapped_column(String(128))                # 卖家名称
    url: Mapped[str] = mapped_column(String(512), nullable=False)                 # 商品详情 URL
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 创建时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 核心字段更新时间

    # 一对多关联：一个商品有多个历史售价销量记录，多个利润试算历史
    sales_history: Mapped[List["SalesHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    profit_history: Mapped[List["ProfitHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    # 作为竞品被监控的关系
    competitor_entry: Mapped[Optional["CompetitorProduct"]] = relationship(
        back_populates="monitored_product", foreign_keys="[CompetitorProduct.monitored_product_id]"
    )


class SalesHistory(Base):
    """
    2. 销量与价格变化历史表 (sales_history)
    用于记录竞品及爆款的时间序列数据，追踪销售速率 (Run Rate) 变化
    """
    __tablename__ = "sales_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)         # 记录当时的售价 (BRL)
    sales_volume: Mapped[int] = mapped_column(Integer, default=0)                 # 当时的历史总销量 (或当日销量)
    stock: Mapped[Optional[int]] = mapped_column(Integer)                         # 当时抓取的库存数
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))                # 当时抓取的评分 (如 4.85)
    reviews_count: Mapped[Optional[int]] = mapped_column(Integer)                 # 当时抓取的评价数
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True) # 记录抓取时间

    product: Mapped["Product"] = relationship(back_populates="sales_history")


class ProfitHistory(Base):
    """
    3. 利润计算历史表 (profit_history)
    记录每次利润测算的模型结果，支持一键调取与横向比对拿货成本、汇率等变动
    """
    __tablename__ = "profit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), index=True, nullable=False)
    purchase_cost_cny: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # 人民币拿货价
    exchange_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)       # 测算汇率 (1 BRL 兑换的人民币)
    domestic_shipping_cny: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0) # 国内（头程包装等）费用
    international_shipping_cny: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0) # 国际头程物流费用
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)            # 测算时匹配的巴西税率
    platform_commission_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False) # 测算时对应的平台基本佣金比例
    fixed_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)             # 平台固定交易费
    platform_shipping_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0) # 平台扣减的尾程运费分摊
    other_cost_brl: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)        # 其他巴西杂费/损耗退货成本
    selling_price_brl: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # 拟定售价 (BRL)
    net_profit_brl: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)     # 拟定售价下的净利润 (BRL)
    profit_margin: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)       # 净利润率
    roi: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)                 # 投资回报率 (ROI)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # 计算时间

    product: Mapped["Product"] = relationship(back_populates="profit_history")


class CompetitorProduct(Base):
    """
    4. 竞品追踪表 (competitor_products)
    用于长期监控竞争对手，分析价格波动与销量走势
    """
    __tablename__ = "competitor_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitored_product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), unique=True, nullable=False)
    my_product_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("products.id")) # 关联的我方商品
    monitoring_frequency: Mapped[str] = mapped_column(String(16), default="daily") # 监控频率 (daily, weekly)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)                 # 是否激活监控
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # 追踪添加时间

    monitored_product: Mapped["Product"] = relationship(foreign_keys=[monitored_product_id])
    my_product: Mapped[Optional["Product"]] = relationship(foreign_keys=[my_product_id])


class PlatformRuleSnapshot(Base):
    """
    5. 平台与税务规则审计表 (platform_rules)
    由于巴西政策变化极为频繁，将每次测算所依赖的配置快照保存在此，确保历史财务数据的追溯性与可解释性
    """
    __tablename__ = "platform_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # 平台 (mercado_livre, shopee 等)
    rule_key: Mapped[str] = mapped_column(String(64), nullable=False)             # 规则配置键 (如 commission_classic)
    rule_value: Mapped[str] = mapped_column(Text, nullable=False)                 # 序列化后的 JSON 字符串参数值
    description: Mapped[Optional[str]] = mapped_column(String(256))               # 规则用途描述/版本更新记录
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
