# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - FastAPI 核心应用程序入口 (App Entry)
初始化 API 容器，挂载健康检查、精算分析与物理报告路由，加载全局异常熔断拦截处理器。
"""

import logging
from fastapi import FastAPI
from src.api.routes.health import health_router
from src.api.routes.analysis import analysis_router
from src.api.routes.reports import reports_router
from src.api.error_handlers import register_error_handlers

# 1. 统一初始化日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("src.api")

# 2. 实例化 FastAPI 应用容器
app = FastAPI(
    title="Brazil-AI-Selector REST API",
    description="巴西选品精算、复杂关税计提、本地物流分账与综合商业决策自动化核算微服务。",
    version="1.0.0",
    docs_url="/docs",               # Swagger 自动开发交互文档公开
    redoc_url="/redoc"              # ReDoc 交互文档公开
)

# 3. 注册全局错误截获处理器 (熔断与校验拦截)
register_error_handlers(app)

# 4. 挂载模块化控制器路由路由
app.include_router(health_router, tags=["系统监控"])
app.include_router(analysis_router, tags=["财务与策略诊断"])
app.include_router(reports_router, tags=["报表生成与物理导出"])

logger.info("✓ FastAPI 应用程序初始化完毕。已注册全部路由与错误处理中间件。")
