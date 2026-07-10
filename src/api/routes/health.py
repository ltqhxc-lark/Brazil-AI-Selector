# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 系统状态健康检查路由 (Health Router)
"""

from fastapi import APIRouter, status
from src.api.schemas import HealthResponse

health_router = APIRouter()

@health_router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="获取系统微服务运行健康状态",
    description="快速诊断 REST API 是否健康在线，该端点绝不访问数据库，亦不执行任何消耗计算"
)
async def check_health() -> HealthResponse:
    """
    健康状态检测契约
    """
    return HealthResponse(
        status="UP",
        project_name="Brazil-AI-Selector",
        version="1.0.0"
    )
