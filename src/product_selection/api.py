# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品 API 路由控制层 (FastAPI)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.models.product import Product as DomainProduct
from src.product_selection.models import (
    MarketData as DomainMarketData,
    SelectionCriteria as DomainSelectionCriteria
)
from src.product_selection.service import ProductSelectionService
from src.product_selection.repository import EntityNotFoundError, DuplicateEntityError, RepositoryError
from src.product_selection.schemas import (
    SingleEvaluateRequest,
    BatchEvaluateRequest,
    SelectionResultResponse,
    BatchEvaluateResponse
)

router = APIRouter(prefix="/selection", tags=["Product Selection"])

# 单例或默认服务工厂
def get_selection_service() -> ProductSelectionService:
    return ProductSelectionService()


@router.post("/evaluate", response_model=SelectionResultResponse, status_code=status.HTTP_201_CREATED)
def evaluate_single_product(
    request: SingleEvaluateRequest,
    db: Session = Depends(get_db),
    service: ProductSelectionService = Depends(get_selection_service)
):
    """
    单商品评估与试算：
    接收商品物理信息及竞争环境，利用财务和物流模型反算最佳零售价格，执行多维度打分，并将结果和规格持久化存储到数据库。
    """
    # 1. 转换 Request 数据为内部领域实体
    try:
        product_domain = DomainProduct(
            sku=request.product.sku,
            name=request.product.name,
            cost_price_brl=float(request.product.cost_price_brl),
            weight_g=float(request.product.weight_g),
            length_cm=float(request.product.length_cm),
            width_cm=float(request.product.width_cm),
            height_cm=float(request.product.height_cm),
            category=request.product.category,
            declared_value_usd=float(request.product.declared_value_usd)
        )
        
        market_domain = DomainMarketData(
            average_selling_price_brl=float(request.market_data.average_selling_price_brl),
            competitor_count=request.market_data.competitor_count,
            demand_score=float(request.market_data.demand_score),
            trend_factor=float(request.market_data.trend_factor)
        )
        
        criteria_domain = None
        if request.criteria:
            criteria_domain = DomainSelectionCriteria(
                target_roi=float(request.criteria.target_roi),
                min_net_margin=float(request.criteria.min_net_margin),
                profit_weight=float(request.criteria.profit_weight),
                demand_weight=float(request.criteria.demand_weight),
                competition_weight=float(request.criteria.competition_weight),
                logistics_weight=float(request.criteria.logistics_weight),
                s_min_score=float(request.criteria.s_min_score),
                a_min_score=float(request.criteria.a_min_score),
                b_min_score=float(request.criteria.b_min_score)
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"参数验证不通过: {str(e)}"
        )

    # 2. 调用业务服务层，自动接管事务 commit/rollback
    try:
        db_result = service.evaluate_and_save_product(
            session=db,
            product=product_domain,
            market_data=market_domain,
            criteria=criteria_domain,
            platform_id=request.platform_id,
            platform_name=request.platform_name
        )
        return db_result
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"计算数据边界错误: {str(e)}"
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据存取故障: {str(e)}"
        )


@router.post("/evaluate-batch", response_model=BatchEvaluateResponse, status_code=status.HTTP_201_CREATED)
def evaluate_batch_products(
    request: BatchEvaluateRequest,
    db: Session = Depends(get_db),
    service: ProductSelectionService = Depends(get_selection_service)
):
    """
    批量商品评估、试算与持久化过滤推荐：
    支持单品失败事务级别隔离（Savepoint 隔离），自动对符合净利率与 ROI 门槛的产品进行降序排序呈报。
    """
    if len(request.products) != len(request.market_data_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"列表长度不匹配。商品数量 ({len(request.products)}) 必须等于市场数据数量 ({len(request.market_data_list)})。"
        )

    products_domain = []
    market_data_domain = []

    try:
        for p in request.products:
            products_domain.append(
                DomainProduct(
                    sku=p.sku,
                    name=p.name,
                    cost_price_brl=float(p.cost_price_brl),
                    weight_g=float(p.weight_g),
                    length_cm=float(p.length_cm),
                    width_cm=float(p.width_cm),
                    height_cm=float(p.height_cm),
                    category=p.category,
                    declared_value_usd=float(p.declared_value_usd)
                )
            )
            
        for m in request.market_data_list:
            market_data_domain.append(
                DomainMarketData(
                    average_selling_price_brl=float(m.average_selling_price_brl),
                    competitor_count=m.competitor_count,
                    demand_score=float(m.demand_score),
                    trend_factor=float(m.trend_factor)
                )
            )
            
        criteria_domain = None
        if request.criteria:
            criteria_domain = DomainSelectionCriteria(
                target_roi=float(request.criteria.target_roi),
                min_net_margin=float(request.criteria.min_net_margin),
                profit_weight=float(request.criteria.profit_weight),
                demand_weight=float(request.criteria.demand_weight),
                competition_weight=float(request.criteria.competition_weight),
                logistics_weight=float(request.criteria.logistics_weight),
                s_min_score=float(request.criteria.s_min_score),
                a_min_score=float(request.criteria.a_min_score),
                b_min_score=float(request.criteria.b_min_score)
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量参数校验不通过: {str(e)}"
        )

    # 调用业务层批量嵌套 Savepoint 持久化服务
    try:
        ranked_results, errors = service.evaluate_and_save_batch(
            session=db,
            products=products_domain,
            market_data_list=market_data_domain,
            criteria=criteria_domain,
            platform_id=request.platform_id,
            platform_name=request.platform_name
        )
        return {"results": ranked_results, "errors": errors}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量选品执行重大异常: {str(e)}"
        )


@router.get("/history", response_model=List[SelectionResultResponse])
def get_selection_history(
    product_id: Optional[int] = None,
    recommendation_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    service: ProductSelectionService = Depends(get_selection_service)
):
    """
    条件组合查询历史决策报告：
    支持 product_id、recommendation_level 过滤，支持标准分页 skip 和 limit，默认按评估时间降序排列。
    """
    try:
        history = service.get_history(
            session=db,
            product_id=product_id,
            recommendation_level=recommendation_level,
            skip=skip,
            limit=limit
        )
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"分页参数非法: {str(e)}"
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取历史数据异常: {str(e)}"
        )


@router.get("/history/{id}", response_model=SelectionResultResponse)
def get_selection_result_by_id(
    id: int,
    db: Session = Depends(get_db),
    service: ProductSelectionService = Depends(get_selection_service)
):
    """
    根据主键获取单条决策评估详情。
    """
    try:
        result = service.get_result_by_id(session=db, result_id=id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到 ID 为 '{id}' 的评估报告。"
            )
        return result
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取决策详情异常: {str(e)}"
        )
