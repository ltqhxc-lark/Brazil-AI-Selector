# -*- coding: utf-8 -*-
"""
选品 API 路由控制层单元测试 (FastAPI TestClient + 依赖注入覆盖)
"""

from decimal import Decimal
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database.base import Base
from src.database.connection import get_db
from src.product_selection.api import router

# 建立一个隔离测试的专属 FastAPI App 并挂载选品路由器
app = FastAPI()
app.include_router(router)

# 建立共享的测试用 SQLite 内存数据库 (使用 StaticPool 共享单个物理连接，防止多会话隔离下无表报错)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(bind=engine)
SessionTest = sessionmaker(bind=engine)

def override_get_db():
    """测试用依赖注入：返回内存 SQLite 会话以隔离真实的持久化文件"""
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()

# 覆盖 FastAPI App 的全局数据库连接依赖
app.dependency_overrides[get_db] = override_get_db

# 实例化测试客户端
client = TestClient(app)


def test_api_single_evaluate():
    """测试单品算分及持久化 API (POST /selection/evaluate)"""
    payload = {
        "product": {
            "sku": "SKU-API-1",
            "name": "API Hair Gel",
            "cost_price_brl": 15.00,
            "weight_g": 150.00,
            "length_cm": 12.00,
            "width_cm": 6.00,
            "height_cm": 4.00,
            "category": "cosmetics",
            "declared_value_usd": 3.00
        },
        "market_data": {
            "average_selling_price_brl": 95.00,
            "competitor_count": 1,
            "demand_score": 9.20,
            "trend_factor": 1.00
        },
        "criteria": {
            "target_roi": 0.30,
            "min_net_margin": 0.15,
            "profit_weight": 0.40,
            "demand_weight": 0.30,
            "competition_weight": 0.20,
            "logistics_weight": 0.10,
            "s_min_score": 80.00,
            "a_min_score": 70.00,
            "b_min_score": 60.00
        },
        "platform_id": "mercado_livre_brasil",
        "platform_name": "Mercado Livre"
    }

    # 1. 成功请求：创建单品选品记录
    response = client.post("/selection/evaluate", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["product_id"] is not None
    assert data["recommendation_level"] == "S"
    assert float(data["estimated_retail_price_brl"]) > 15.0

    # 2. 重复 SKU：更新商品并生成新的评估记录（非错误）
    response_dup = client.post("/selection/evaluate", json=payload)
    assert response_dup.status_code == status.HTTP_201_CREATED
    data_dup = response_dup.json()
    assert data_dup["product_id"] == data["product_id"]
    assert data_dup["id"] != data["id"]

    # 3. 失败请求：非法输入验证 (售价/成本负数)
    payload_bad = dict(payload)
    payload_bad["product"]["cost_price_brl"] = -10.0
    response_bad = client.post("/selection/evaluate", json=payload_bad)
    assert response_bad.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_api_batch_evaluate_and_history():
    """测试批量选品接口 (POST /evaluate-batch) 及历史组合条件查询接口 (GET /history)"""
    payload_batch = {
        "products": [
            {
                "sku": "SKU-BATCH-API-1", "name": "Shirt", "cost_price_brl": 20.00,
                "weight_g": 200.00, "length_cm": 15.0, "width_cm": 10.0, "height_cm": 5.0, "category": "clothing"
            },
            {
                "sku": "SKU-BATCH-API-BAD", "name": "Zero Dimension", "cost_price_brl": 15.00,
                "weight_g": 100.00, "length_cm": 0.0, "width_cm": 5.0, "height_cm": 5.0, "category": "clothing"
            }
        ],
        "market_data_list": [
            {"average_selling_price_brl": 100.00, "competitor_count": 3, "demand_score": 8.0},
            {"average_selling_price_brl": 80.00, "competitor_count": 1, "demand_score": 7.5}
        ]
    }

    # 1. 批量评估，验证部分商品失败不中断 (SKU-BATCH-API-BAD 应该进入 errors)
    response = client.post("/selection/evaluate-batch", json=payload_batch)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert len(data["results"]) == 1
    assert len(data["errors"]) == 1
    assert data["results"][0]["recommendation_level"] == "S"  # 100售价 vs 20拿货高毛利
    assert data["errors"][0][0] == "SKU-BATCH-API-BAD"
    assert "ValueError" in data["errors"][0][1]

    # 保存创建成功单品的 ID，用于后面的详情 GET 查询
    result_id = data["results"][0]["id"]

    # 2. 查询选品历史记录 API (GET /selection/history)
    response_history = client.get("/selection/history")
    assert response_history.status_code == status.HTTP_200_OK
    history_list = response_history.json()
    # 包含了单品测试创建的 SKU-API-1（两次评估共两条），以及批量评估成功的 SKU-BATCH-API-1，共三条
    assert len(history_list) == 3
    assert history_list[0]["id"] == result_id  # 批量算分的在后面，时间更新，排第一位

    # 条件过滤查询
    response_filter = client.get("/selection/history?recommendation_level=S")
    assert len(response_filter.json()) == 3

    # 分页校验拦截测试
    response_page_err = client.get("/selection/history?limit=1000") # limit 超过 500
    assert response_page_err.status_code == status.HTTP_400_BAD_REQUEST
    assert "单页行数限制" in response_page_err.json()["detail"]

    # 3. 按主键查询评估决策详情 API (GET /selection/history/{id})
    response_detail = client.get(f"/selection/history/{result_id}")
    assert response_detail.status_code == status.HTTP_200_OK
    detail = response_detail.json()
    assert detail["id"] == result_id
    assert detail["recommendation_level"] == "S"

    # 查询不存在主键
    response_detail_err = client.get("/selection/history/999999")
    assert response_detail_err.status_code == status.HTTP_404_NOT_FOUND
