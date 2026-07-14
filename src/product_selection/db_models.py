# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品评估 SQLAlchemy 数据库模型
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base

def get_utc_now() -> datetime:
    """
    获取带时区的当前 UTC 时间，避免 Python 3.13+ 中 utcnow() 废弃的问题。
    """
    return datetime.now(timezone.utc)


class SelectionProductDB(Base):
    """
    1. 选品商品表 (selection_products)
    存储用于选品试算评估的商品静态属性及采购规格
    """
    __tablename__ = "selection_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True) # 商品 SKU (唯一，带索引)
    name: Mapped[str] = mapped_column(String(256), nullable=False)                         # 商品名称
    cost_price_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)       # 采购成本 (BRL)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 实际物理重量 (克)
    length_cm: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 外包装长 (厘米)
    width_cm: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))  # 外包装宽 (厘米)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 外包装高 (厘米)
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)          # 商品分类
    declared_value_usd: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 申报价值 (USD)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # 双向关联定义 (cascade 限制在商品主表，避免在关联表产生环形级联删除)
    market_data_entries: Mapped[List["SelectionMarketDataDB"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    selection_results: Mapped[List["SelectionResultDB"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class SelectionMarketDataDB(Base):
    """
    2. 选品市场环境数据表 (selection_market_data)
    """
    __tablename__ = "selection_market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("selection_products.id", ondelete="CASCADE"), index=True, nullable=False)
    
    average_selling_price_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False) # 市场平均零售价 (BRL)
    competitor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)         # 主要竞争对手数
    demand_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)               # 市场需求评分 (0.0-10.0)
    trend_factor: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=Decimal("1.000000")) # 需求趋势系数
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # 关联定义
    product: Mapped["SelectionProductDB"] = relationship(back_populates="market_data_entries")
    results: Mapped[List["SelectionResultDB"]] = relationship(
        back_populates="market_data", cascade="all, delete-orphan"
    )


class SelectionResultDB(Base):
    """
    3. 选品综合评估结果历史记录表 (selection_results)
    """
    __tablename__ = "selection_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("selection_products.id", ondelete="CASCADE"), index=True, nullable=False)
    market_data_id: Mapped[int] = mapped_column(Integer, ForeignKey("selection_market_data.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # 精算出的核心财务与成本估算字段 (Decimal 类型，高精度)
    estimated_retail_price_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)  # 建议售价 (BRL)
    estimated_net_profit_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)    # 纯利润 (BRL)
    estimated_roi: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)               # 投资回报率 (ROI)
    estimated_margin: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)            # 纯利润率
    estimated_tax_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))    # 巴西税费
    estimated_platform_fee_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 平台扣点费用
    estimated_shipping_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))     # 实付物流运费
    estimated_gross_profit_brl: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00")) # 精算毛利润
    
    # 百分制综合与子项评分
    total_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)                  # 综合总分
    profit_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)                 # 利润得分
    demand_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)                 # 需求得分
    competition_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)            # 竞争得分
    logistics_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)              # 物流得分
    recommendation_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)    # 评级 (S, A, B, C)
    
    # 诊断文书 (使用 SQLAlchemy JSON 列，原生存储列表型数据)
    recommendation_reasons: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list) # 推荐优势原因
    risk_warnings: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)          # 运营风险警示
    
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True) # 选品评估生成时间 (带时区)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # 关联定义 (避免级联删除引发循环作用)
    product: Mapped["SelectionProductDB"] = relationship(back_populates="selection_results")
    market_data: Mapped["SelectionMarketDataDB"] = relationship(back_populates="results")
