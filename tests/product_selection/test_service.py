# -*- coding: utf-8 -*-
"""
选品服务业务持久化层及局部故障隔离单元测试 (SQLite 内存环境)
"""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database.base import Base
from src.models.product import Product as DomainProduct
from src.product_selection.models import MarketData as DomainMarketData, SelectionCriteria
from src.product_selection.service import ProductSelectionService
from src.product_selection.repository import (
    ProductRepository,
    MarketDataRepository,
    SelectionResultRepository
)

@pytest.fixture(name="db_session")
def fixture_db_session():
    """使用 StaticPool 共享连接保证内存表持久化可用"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionTest = sessionmaker(bind=engine)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


def test_service_single_evaluate_and_save(db_session):
    """测试单品业务持久化服务层 evaluate_and_save_product 整体执行及事务一致性"""
    service = ProductSelectionService()

    product = DomainProduct(
        sku="SKU-SERV-1", name="Service Mascara", cost_price_brl=12.00,
        weight_g=80.00, length_cm=10.00, width_cm=4.00, height_cm=2.00, category="cosmetics"
    )
    market_data = DomainMarketData(
        average_selling_price_brl=85.00, competitor_count=1, demand_score=9.50
    )

    # 1. 正常评估保存
    res = service.evaluate_and_save_product(db_session, product, market_data)
    assert res.id is not None
    assert res.recommendation_level == "S"
    assert res.estimated_retail_price_brl > Decimal("30.00")

    # 验证数据库中是否确实存在记录且已被 commit
    prod_repo = ProductRepository(db_session)
    result_repo = SelectionResultRepository(db_session)

    db_prod = prod_repo.get_by_sku("SKU-SERV-1")
    assert db_prod is not None
    assert db_prod.name == "Service Mascara"

    db_res = result_repo.get_by_id(res.id)
    assert db_res is not None
    assert db_res.recommendation_level == "S"

    # 2. 模拟异常：传入不合规的负数售价，测试异常是否被抛出，以及数据库事务是否已 rollback
    product_bad = DomainProduct(
        sku="SKU-BAD-TR", name="Bad Pricing", cost_price_brl=-5.00,  # 负数成本导致报错
        weight_g=80.00, length_cm=10.00, width_cm=4.00, height_cm=2.00, category="cosmetics"
    )
    with pytest.raises(ValueError):
        service.evaluate_and_save_product(db_session, product_bad, market_data)

    # 验证异常回滚：SKU-BAD-TR 应当未被成功创建在数据库中
    assert prod_repo.get_by_sku("SKU-BAD-TR") is None


def test_service_batch_evaluate_and_save_with_fault_isolation(db_session):
    """测试批量评估服务层 evaluate_and_save_batch 局部的 Savepoint 隔离故障与最后的推荐过滤逻辑"""
    service = ProductSelectionService()

    # 1. 正常商品 S 级
    prod_s = DomainProduct(
        sku="SKU-BATCH-OK", name="Batch OK", cost_price_brl=10.00,
        weight_g=100.00, length_cm=10.00, width_cm=8.00, height_cm=5.00, category="cosmetics"
    )
    market_s = DomainMarketData(average_selling_price_brl=90.00, competitor_count=1, demand_score=9.5)

    # 2. 失效商品 (尺寸为 0，引发算分 ValueError)
    prod_err = DomainProduct(
        sku="SKU-BATCH-ERR", name="Zero Size", cost_price_brl=12.00,
        weight_g=200.00, length_cm=0.0, width_cm=10.0, height_cm=10.0, category="electronics"
    )
    market_err = DomainMarketData(average_selling_price_brl=120.00, competitor_count=3, demand_score=8.0)

    # 3. 正常商品但低于 15% 净利率最低标准会被过滤的 B 级产品 (由于拿货成本高达售价的 85%)
    prod_low_margin = DomainProduct(
        sku="SKU-BATCH-FILTERED", name="Low Margin", cost_price_brl=80.00,
        weight_g=300.00, length_cm=15.0, width_cm=10.0, height_cm=5.0, category="clothing"
    )
    market_low_margin = DomainMarketData(average_selling_price_brl=95.00, competitor_count=2, demand_score=8.5)

    products = [prod_s, prod_err, prod_low_margin]
    market_data_list = [market_s, market_err, market_low_margin]

    # 运行批量试算
    criteria = SelectionCriteria()
    ranked_results, errors = service.evaluate_and_save_batch(db_session, products, market_data_list, criteria)

    # 4. 断言容错隔离与决策过滤效果
    # 局部错误正常记录，不中断批量
    assert len(errors) == 1
    assert errors[0][0] == "SKU-BATCH-ERR"
    assert "ValueError" in errors[0][1]

    # 错误商品被回滚，未污染数据库
    prod_repo = ProductRepository(db_session)
    assert prod_repo.get_by_sku("SKU-BATCH-ERR") is None

    # 正常评估商品被成功保存
    assert prod_repo.get_by_sku("SKU-BATCH-OK") is not None
    assert prod_repo.get_by_sku("SKU-BATCH-FILTERED") is not None

    # 推荐过滤断言：SKU-BATCH-FILTERED 虽然被持久化，但由于利润率不达标，未能呈报在最终的推荐清单中
    assert len(ranked_results) == 1
    assert ranked_results[0].product.sku == "SKU-BATCH-OK"
