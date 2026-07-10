# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - API 全局异常截获与统一报错处理器 (Error Handlers)
捕获参数校验异常 (RequestValidationError)、文件不存在、值错误以及系统未知崩溃，
统一格式化打包为标准化 JSON 报错信封返回。
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# 获取 API 的日志记录器
logger = logging.getLogger("src.api")

def register_error_handlers(app: FastAPI) -> None:
    """
    在 FastAPI 应用实例上注册全部全局异常捕获钩子
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        截获 Pydantic 数据边界强校验错误（422 Unprocessable Entity）
        """
        error_details = []
        for error in exc.errors():
            loc = " -> ".join(str(loc_item) for loc_item in error.get("loc", []))
            msg = error.get("msg", "未知校验报错")
            error_details.append(f"参数位置 [{loc}]: {msg}")

        logger.warning(f"接收到非法的请求荷载，拦截参数校验异常: {error_details}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "请求输入参数强校验未通过，已被防穿透机制安全拦截。",
                "errors": error_details
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """
        截获业务层产生的值范围非法异常 (400 Bad Request)
        """
        err_msg = str(exc)
        logger.warning(f"业务运行拦截到不合法值异常: {err_msg}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "业务数据参数合理性校验失败。",
                "errors": [err_msg]
            }
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        """
        截获物理文件缺失异常（404 Not Found）
        """
        err_msg = str(exc)
        logger.error(f"物理文件缺失或读取失败: {err_msg}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": "请求访问的物理报告文件不存在，请核实生成状态。",
                "errors": ["File physical path not found on the local disk."]
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        兜底截获未知的系统内部报错（500 Internal Server Error）
        防范泄漏后台核心堆栈
        """
        logger.exception(f"系统运行时暴发未捕获严重异常: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "系统内部运行时突发未知故障，已被熔断机制安全阻断。",
                "errors": ["Internal Server Error. Please contact administrator or check logs."]
            }
        )
