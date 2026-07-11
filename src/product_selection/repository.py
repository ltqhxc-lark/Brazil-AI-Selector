# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品评估数据访问层 (Repository)
负责数据库的 CRUD 操作，不包含任何打分、售价反推或利润计算业务逻辑。
数据库更新在 flush/refresh 后由上层应用管理事务边界 (严格不执行 commit 或 rollback)。
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from src.product_selection.db_models import SelectionProductDB, SelectionMarketDataDB, SelectionResultDB

# ==============================================================================
# 选品数据访问层统一异常类定义
# ==============================================================================

class RepositoryError(Exception):
    """
    选品数据访问层基础异常
    """
    pass

class EntityNotFoundError(RepositoryError):
    """
    所请求的实体记录不存在异常
    """
    pass

class DuplicateEntityError(RepositoryError):
    """
    重复实体冲突异常 (如 SKU 唯一性约束冲突)
    """
    pass


# ==============================================================================
# 模块内通用私有辅助函数
# ==============================================================================

def _validate_pagination(skip: int, limit: int) -> None:
    """
    严格校验分页参数，不通过时直接抛出 ValueError。
    """
    if skip < 0:
        raise ValueError(f"分页偏移量 skip 必须大于等于 0，当前为: {skip}")
    if not (1 <= limit <= 500):
        raise ValueError(f"单页行数限制 limit 必须在 [1, 500] 之间，当前为: {limit}")


# ==============================================================================
# 1. 选品商品数据访问层 (ProductRepository)
# ==============================================================================

class ProductRepository:
    """
    选品商品数据库操作层
    """

    def __init__(self, session: Session) -> None:
        """
        初始化仓储层，注入 SQLAlchemy Session 会话对象
        """
        self.session = session

    def create(
        self,
        sku: str,
        name: str,
        cost_price_brl: Decimal,
        weight_g: Decimal,
        length_cm: Decimal,
        width_cm: Decimal,
        height_cm: Decimal,
        category: str,
        declared_value_usd: Decimal
    ) -> SelectionProductDB:
        """
        创建并持久化一个选品商品静态规格信息。
        如果 SKU 唯一性约束冲突，抛出 DuplicateEntityError；
        其他底层数据库异常抛出 RepositoryError。
        """
        db_product = SelectionProductDB(
            sku=sku,
            name=name,
            cost_price_brl=cost_price_brl,
            weight_g=weight_g,
            length_cm=length_cm,
            width_cm=width_cm,
            height_cm=height_cm,
            category=category,
            declared_value_usd=declared_value_usd
        )
        try:
            self.session.add(db_product)
            self.session.flush()
            self.session.refresh(db_product)
            return db_product
        except IntegrityError as e:
            # 判断是否为 SKU 唯一索引冲突。SQLite 典型冲突信息常包含 'UNIQUE constraint failed'
            # 无论如何，由于 SKU 是 selection_products 上的唯一键，主键是自增整型，该表上的完整性冲突即为 SKU 重复
            raise DuplicateEntityError(f"唯一约束冲突：SKU 为 '{sku}' 的选品商品已存在。") from e
        except SQLAlchemyError as e:
            raise RepositoryError("创建选品商品时，底层 SQLAlchemy 发生异常。") from e

    def update(self, id_or_sku: Union[int, str], **kwargs) -> SelectionProductDB:
        """
        更新选品商品的规格信息。
        如果修改的记录不存在，抛出 EntityNotFoundError；
        如果 SKU 修改导致重复，抛出 DuplicateEntityError。
        """
        db_product = self.get_by_id_or_sku(id_or_sku)
        if not db_product:
            raise EntityNotFoundError(f"未找到标识为 '{id_or_sku}' 的选品商品，无法执行更新。")

        try:
            for key, value in kwargs.items():
                if hasattr(db_product, key):
                    # 强类型匹配：目标字段是 Decimal 时进行高精度强制转型
                    if isinstance(getattr(db_product, key), Decimal) and value is not None:
                        setattr(db_product, key, Decimal(str(value)))
                    else:
                        setattr(db_product, key, value)
            
            self.session.flush()
            self.session.refresh(db_product)
            return db_product
        except IntegrityError as e:
            raise DuplicateEntityError(f"更新失败：修改后的 SKU 信息引发了数据库唯一性索引冲突。") from e
        except SQLAlchemyError as e:
            raise RepositoryError(f"更新商品记录 '{id_or_sku}' 时，底层 SQLAlchemy 操作异常。") from e

    def get_by_id(self, product_id: int) -> Optional[SelectionProductDB]:
        """
        根据商品自增主键 ID 查询选品商品对象
        """
        try:
            return self.session.execute(
                select(SelectionProductDB).where(SelectionProductDB.id == product_id)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"根据 ID '{product_id}' 查询商品失败，底层数据库异常。") from e

    def get_by_sku(self, sku: str) -> Optional[SelectionProductDB]:
        """
        根据唯一 SKU 查询选品商品对象
        """
        try:
            return self.session.execute(
                select(SelectionProductDB).where(SelectionProductDB.sku == sku)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"根据 SKU '{sku}' 查询商品失败，底层数据库异常。") from e

    def get_by_id_or_sku(self, id_or_sku: Union[int, str]) -> Optional[SelectionProductDB]:
        """
        自动兼容主键 ID 或是唯一 SKU 的通用查询
        """
        if isinstance(id_or_sku, int):
            return self.get_by_id(id_or_sku)
        return self.get_by_sku(str(id_or_sku))

    def list(self, skip: int = 0, limit: int = 100) -> List[SelectionProductDB]:
        """
        分页查询已录入的选品商品（按 ID 降序排列）。
        """
        _validate_pagination(skip, limit)

        try:
            return list(
                self.session.execute(
                    select(SelectionProductDB)
                    .order_by(SelectionProductDB.id.desc())
                    .offset(skip)
                    .limit(limit)
                ).scalars().all()
            )
        except SQLAlchemyError as e:
            raise RepositoryError("分页读取选品商品列表失败，底层数据库异常。") from e

    def delete(self, id_or_sku: Union[int, str]) -> bool:
        """
        物理删除某个选品商品（将级联删除其所有的市场记录和历史评估结果）
        """
        db_product = self.get_by_id_or_sku(id_or_sku)
        if not db_product:
            return False
            
        try:
            self.session.delete(db_product)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            raise RepositoryError(f"物理删除商品 '{id_or_sku}' 失败，底层数据库操作异常。") from e


# ==============================================================================
# 2. 市场环境数据访问层 (MarketDataRepository)
# ==============================================================================

class MarketDataRepository:
    """
    市场环境数据库操作层
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        product_id: int,
        average_selling_price_brl: Decimal,
        competitor_count: int,
        demand_score: Decimal,
        trend_factor: Decimal
    ) -> SelectionMarketDataDB:
        """
        创建并持久化一次市场竞争环境分析快照。
        """
        db_market = SelectionMarketDataDB(
            product_id=product_id,
            average_selling_price_brl=average_selling_price_brl,
            competitor_count=competitor_count,
            demand_score=demand_score,
            trend_factor=trend_factor
        )
        try:
            self.session.add(db_market)
            self.session.flush()
            self.session.refresh(db_market)
            return db_market
        except SQLAlchemyError as e:
            raise RepositoryError(f"创建商品 ID '{product_id}' 的市场快照记录失败。") from e

    def update(self, market_data_id: int, **kwargs) -> SelectionMarketDataDB:
        """
        更新特定市场快照（更新前先校验记录存在，否则抛出 EntityNotFoundError）。
        """
        db_market = self.get_by_id(market_data_id)
        if not db_market:
            raise EntityNotFoundError(f"未找到主键为 '{market_data_id}' 的市场快照记录，更新失败。")

        try:
            for key, value in kwargs.items():
                if hasattr(db_market, key):
                    if isinstance(getattr(db_market, key), Decimal) and value is not None:
                        setattr(db_market, key, Decimal(str(value)))
                    else:
                        setattr(db_market, key, value)
            self.session.flush()
            self.session.refresh(db_market)
            return db_market
        except SQLAlchemyError as e:
            raise RepositoryError(f"更新市场快照 ID '{market_data_id}' 失败，底层数据库异常。") from e

    def get_by_id(self, market_data_id: int) -> Optional[SelectionMarketDataDB]:
        """
        根据主键查询市场记录快照
        """
        try:
            return self.session.execute(
                select(SelectionMarketDataDB).where(SelectionMarketDataDB.id == market_data_id)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"根据 ID '{market_data_id}' 读取市场环境失败。") from e

    def list_by_product_id(self, product_id: int) -> List[SelectionMarketDataDB]:
        """
        查询属于某件商品的所有历史抓取或录入的市场环境数值快照（按 ID 降序排列）。
        """
        try:
            return list(
                self.session.execute(
                    select(SelectionMarketDataDB)
                    .where(SelectionMarketDataDB.product_id == product_id)
                    .order_by(SelectionMarketDataDB.id.desc())
                ).scalars().all()
            )
        except SQLAlchemyError as e:
            raise RepositoryError(f"读取商品 ID '{product_id}' 的市场历史时数据库操作异常。") from e

    def get_latest_by_product_id(self, product_id: int) -> Optional[SelectionMarketDataDB]:
        """
        获取该商品最近一次提交分析的市场快照记录
        """
        try:
            return self.session.execute(
                select(SelectionMarketDataDB)
                .where(SelectionMarketDataDB.product_id == product_id)
                .order_by(SelectionMarketDataDB.id.desc())
                .limit(1)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"调取商品 ID '{product_id}' 最新的市场分析记录时异常。") from e

    def delete(self, market_data_id: int) -> bool:
        """
        物理删除单条市场记录，若不存在返回 False，成功返回 True
        """
        db_market = self.get_by_id(market_data_id)
        if not db_market:
            return False

        try:
            self.session.delete(db_market)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            raise RepositoryError(f"删除市场数据记录 '{market_data_id}' 时数据库异常。") from e


# ==============================================================================
# 3. 选品结果历史数据访问层 (SelectionResultRepository)
# ==============================================================================

class SelectionResultRepository:
    """
    选品结果报告数据库操作层 (历史评估结果不提供任何物理删除接口)
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_result(
        self,
        product_id: int,
        market_data_id: int,
        estimated_retail_price_brl: Decimal,
        estimated_net_profit_brl: Decimal,
        estimated_roi: Decimal,
        estimated_margin: Decimal,
        estimated_tax_brl: Decimal,
        estimated_platform_fee_brl: Decimal,
        estimated_shipping_brl: Decimal,
        estimated_gross_profit_brl: Decimal,
        total_score: Decimal,
        profit_score: Decimal,
        demand_score: Decimal,
        competition_score: Decimal,
        logistics_score: Decimal,
        recommendation_level: str,
        recommendation_reasons: List[str],
        risk_warnings: List[str]
    ) -> SelectionResultDB:
        """
        持久化保存一次完整产品的精算与打分综合选品报告结果（不自动 commit）。
        """
        db_result = SelectionResultDB(
            product_id=product_id,
            market_data_id=market_data_id,
            estimated_retail_price_brl=estimated_retail_price_brl,
            estimated_net_profit_brl=estimated_net_profit_brl,
            estimated_roi=estimated_roi,
            estimated_margin=estimated_margin,
            estimated_tax_brl=estimated_tax_brl,
            estimated_platform_fee_brl=estimated_platform_fee_brl,
            estimated_shipping_brl=estimated_shipping_brl,
            estimated_gross_profit_brl=estimated_gross_profit_brl,
            total_score=total_score,
            profit_score=profit_score,
            demand_score=demand_score,
            competition_score=competition_score,
            logistics_score=logistics_score,
            recommendation_level=recommendation_level,
            recommendation_reasons=recommendation_reasons,
            risk_warnings=risk_warnings
        )
        try:
            self.session.add(db_result)
            self.session.flush()
            self.session.refresh(db_result)
            return db_result
        except SQLAlchemyError as e:
            raise RepositoryError("保存产品综合评估决策报告时，底层数据库写操作异常。") from e

    def get_by_id(self, result_id: int) -> Optional[SelectionResultDB]:
        """
        根据主键查询单次选品评估历史结果详情
        """
        try:
            return self.session.execute(
                select(SelectionResultDB).where(SelectionResultDB.id == result_id)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"根据 ID '{result_id}' 调取评估结果记录失败。") from e

    def get_history(
        self,
        product_id: Optional[int] = None,
        recommendation_level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SelectionResultDB]:
        """
        多重过滤条件组合查询系统的选品历史结果清单。
        
        排序规则：
            - 优先按实际评估生成时间降序: SelectionResultDB.evaluated_at.desc()
            - 评估时间相同时按主键 ID 降序: SelectionResultDB.id.desc()
        """
        _validate_pagination(skip, limit)

        stmt = select(SelectionResultDB)
        
        # 逐层添加可选的多维度过滤规则
        if product_id is not None:
            stmt = stmt.where(SelectionResultDB.product_id == product_id)
        if recommendation_level is not None:
            stmt = stmt.where(SelectionResultDB.recommendation_level == recommendation_level)
        if start_time is not None:
            stmt = stmt.where(SelectionResultDB.evaluated_at >= start_time)
        if end_time is not None:
            stmt = stmt.where(SelectionResultDB.evaluated_at <= end_time)

        # 排序机制与分页
        stmt = stmt.order_by(
            SelectionResultDB.evaluated_at.desc(),
            SelectionResultDB.id.desc()
        ).offset(skip).limit(limit)

        try:
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError("多重过滤查询历史评估记录发生数据库底层异常。") from e

    def get_latest_by_product_id(self, product_id: int) -> Optional[SelectionResultDB]:
        """
        获取某个商品最新的单次选品评估历史结果 (按 evaluated_at DESC, id DESC 排序)
        """
        try:
            return self.session.execute(
                select(SelectionResultDB)
                .where(SelectionResultDB.product_id == product_id)
                .order_by(
                    SelectionResultDB.evaluated_at.desc(),
                    SelectionResultDB.id.desc()
                )
                .limit(1)
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"读取商品 ID '{product_id}' 最新的评估历史发生异常。") from e
