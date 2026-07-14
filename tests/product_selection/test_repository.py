# -*- coding: utf-8 -*-
"""
选品数据访问仓储层单元测试 (内存 SQLite 环境)
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database.base import Base
from src.product_selection.db_models import SelectionProductDB, SelectionMarketDataDB, SelectionResultDB
from src.product_selection.repository import (
    ProductRepository,
    MarketDataRepository,
    SelectionResultRepository,
    EntityNotFoundError,
    DuplicateEntityError
)

@pytest.fixture(name="db_session")
def fixture_db_session():
    """建立内存 SQLite 会话生命周期 fixture，使用 StaticPool 共享连接保证表结构持久可用"""
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


def test_product_repository_crud(db_session):
    """测试商品基础信息 CRUD 的正确性及 SKU 唯一约束校验"""
    repo = ProductRepository(db_session)

    # 1. 测试创建商品
    prod = repo.create(
        sku="SKU-TEST-CRUD",
        name="Test Mascara",
        cost_price_brl=Decimal("15.50"),
        weight_g=Decimal("120.00"),
        length_cm=Decimal("12.00"),
        width_cm=Decimal("5.00"),
        height_cm=Decimal("3.00"),
        category="cosmetics",
        declared_value_usd=Decimal("2.50")
    )
    assert prod.id is not None
    assert prod.sku == "SKU-TEST-CRUD"
    assert prod.cost_price_brl == Decimal("15.50")
    
    # 显式 commit 首个商品，防止后续因异常回滚导致此商品信息丢失
    db_session.commit()

    # 2. 测试重复 SKU 创建抛出 DuplicateEntityError
    with pytest.raises(DuplicateEntityError):
        repo.create(
            sku="SKU-TEST-CRUD",  # 重复的唯一索引 SKU
            name="Another Name",
            cost_price_brl=Decimal("20.00"),
            weight_g=Decimal("10.00"),
            length_cm=Decimal("5.00"),
            width_cm=Decimal("5.00"),
            height_cm=Decimal("5.00"),
            category="cosmetics",
            declared_value_usd=Decimal("0.00")
        )
    
    # 特别注意：因唯一约束冲突引发底层 flush 报错，必须显式 rollback 事务，清除会话脏状态
    db_session.rollback()

    # 3. 测试查询
    found_by_id = repo.get_by_id(prod.id)
    assert found_by_id is not None
    assert found_by_id.sku == "SKU-TEST-CRUD"

    found_by_sku = repo.get_by_sku("SKU-TEST-CRUD")
    assert found_by_sku is not None
    assert found_by_sku.id == prod.id

    # 4. 测试更新商品
    updated_prod = repo.update(prod.id, name="New Glow Mascara", cost_price_brl="18.90")
    assert updated_prod.name == "New Glow Mascara"
    assert updated_prod.cost_price_brl == Decimal("18.90")
    db_session.commit()

    # 更新不存在商品抛出 EntityNotFoundError
    with pytest.raises(EntityNotFoundError):
        repo.update(99999, name="None")

    # 5. 测试删除商品
    assert repo.delete("SKU-TEST-CRUD") is True
    db_session.commit()
    assert repo.get_by_id(prod.id) is None


def test_market_data_and_selection_result_relationships(db_session):
    """测试市场环境、评估报告历史记录的关联、排序、分页以及级联物理删除"""
    prod_repo = ProductRepository(db_session)
    market_repo = MarketDataRepository(db_session)
    result_repo = SelectionResultRepository(db_session)

    # 1. 建立评估商品
    prod = prod_repo.create(
        sku="SKU-REL", name="Relationship Product", cost_price_brl=Decimal("10.00"),
        weight_g=Decimal("100.00"), length_cm=Decimal("10.00"), width_cm=Decimal("5.00"), height_cm=Decimal("5.00"),
        category="clothing", declared_value_usd=Decimal("0.00")
    )
    db_session.commit()

    # 2. 建立评估市场瞬时条件
    market1 = market_repo.create(
        product_id=prod.id,
        average_selling_price_brl=Decimal("60.00"),
        competitor_count=2,
        demand_score=Decimal("8.50"),
        trend_factor=Decimal("1.000000")
    )
    # 再建第二条历史市场分析
    market2 = market_repo.create(
        product_id=prod.id,
        average_selling_price_brl=Decimal("80.00"),
        competitor_count=5,
        demand_score=Decimal("9.00"),
        trend_factor=Decimal("1.100000")
    )
    db_session.commit()

    # 校验 get_latest_by_product_id
    latest_market = market_repo.get_latest_by_product_id(prod.id)
    assert latest_market.id == market2.id
    assert latest_market.average_selling_price_brl == Decimal("80.00")

    # 3. 建立并保存选品历史决策评估结果
    res1 = result_repo.save_result(
        product_id=prod.id,
        market_data_id=market1.id,
        estimated_retail_price_brl=Decimal("59.00"),
        estimated_net_profit_brl=Decimal("15.00"),
        estimated_roi=Decimal("1.500000"),
        estimated_margin=Decimal("0.254200"),
        estimated_tax_brl=Decimal("2.40"),
        estimated_platform_fee_brl=Decimal("10.10"),
        estimated_shipping_brl=Decimal("11.50"),
        estimated_gross_profit_brl=Decimal("49.00"),
        total_score=Decimal("78.50"),
        profit_score=Decimal("80.00"),
        demand_score=Decimal("85.00"),
        competition_score=Decimal("90.00"),
        logistics_score=Decimal("100.00"),
        recommendation_level="A",
        recommendation_reasons=["高毛利"],
        risk_warnings=["抛货警告"]
    )
    
    # 建立第二条决策评估结果 (比第一条晚1秒，用于评估排序)
    import time
    from datetime import datetime, timezone
    res2 = result_repo.save_result(
        product_id=prod.id,
        market_data_id=market2.id,
        estimated_retail_price_brl=Decimal("79.00"),
        estimated_net_profit_brl=Decimal("25.00"),
        estimated_roi=Decimal("2.500000"),
        estimated_margin=Decimal("0.316450"),
        estimated_tax_brl=Decimal("3.20"),
        estimated_platform_fee_brl=Decimal("13.40"),
        estimated_shipping_brl=Decimal("12.40"),
        estimated_gross_profit_brl=Decimal("69.00"),
        total_score=Decimal("88.20"),
        profit_score=Decimal("90.00"),
        demand_score=Decimal("92.00"),
        competition_score=Decimal("80.00"),
        logistics_score=Decimal("100.00"),
        recommendation_level="S",
        recommendation_reasons=["S理由"],
        risk_warnings=["S警告"]
    )
    
    # 手动微调 evaluated_at 时间，测试排序
    res1.evaluated_at = datetime(2026, 7, 11, 10, 0, 0, tzinfo=timezone.utc)
    res2.evaluated_at = datetime(2026, 7, 11, 11, 0, 0, tzinfo=timezone.utc)
    db_session.commit()

    # 4. 测试 get_history 过滤与排序 (evaluated_at DESC, id DESC)
    history = result_repo.get_history(product_id=prod.id)
    assert len(history) == 2
    assert history[0].id == res2.id # 最新生成的排在第一位 (evaluated_at 11点 > 10点)
    assert history[1].id == res1.id

    # 按推荐评级过滤
    history_s = result_repo.get_history(recommendation_level="S")
    assert len(history_s) == 1
    assert history_s[0].id == res2.id

    # 5. 测试 get_latest_by_product_id
    latest_res = result_repo.get_latest_by_product_id(prod.id)
    assert latest_res.id == res2.id

    # 6. 测试外键和级联删除规则
    # 物理删除产品 prod，应该级联清理 selection_market_data 和 selection_results 中所有的关联表项
    assert prod_repo.delete(prod.id) is True
    db_session.commit()

    assert market_repo.get_by_id(market1.id) is None
    assert market_repo.get_by_id(market2.id) is None
    assert result_repo.get_by_id(res1.id) is None
    assert result_repo.get_by_id(res2.id) is None
    print("级联删除成功：当评估商品下架时，所有关联的评分和市场记录在数据库级别已安全物理擦除。")
