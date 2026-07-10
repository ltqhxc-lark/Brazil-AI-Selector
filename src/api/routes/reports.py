# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报表编译、物理导出与安全下载控制器路由 (Reports Router)
"""

import os
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import FileResponse
from src.models import Product, Platform
from src.api.schemas import ReportRequest, ReportResponse
from src.api.dependencies import (
    get_fee_service,
    get_tax_service,
    get_profit_service,
    get_recommendation_strategy,
    get_report_builder,
    get_exporters
)
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.services.profit_service import ProfitService
from src.strategies.recommendation_strategy import RecommendationStrategy
from src.reports.report_builder import ReportBuilder
from src.exporters import BaseExporter
from src.calculators.shipping_calculator import ShippingCalculator

reports_router = APIRouter()

# 共享物理导出存储路径 (相对路径)
EXPORTS_DIR = Path("exports").resolve()

# 实例化无状态的物流计算器
_ship_calculator = ShippingCalculator()

@reports_router.post(
    "/api/v1/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="编译商品财务数据并物理导出多格式（Excel, PDF, CSV, JSON）分析报表",
    description="传入商品实机参数与目标渠道。系统执行完整财务计提、关税精算与策略优化后，自动将报告编译并物理写入磁盘，返回相对安全下载路径。"
)
async def generate_report(
    req: ReportRequest,
    fee_service: FeeService = Depends(get_fee_service),
    tax_service: TaxService = Depends(get_tax_service),
    profit_service: ProfitService = Depends(get_profit_service),
    recommendation_strategy: RecommendationStrategy = Depends(get_recommendation_strategy),
    report_builder: ReportBuilder = Depends(get_report_builder),
    exporters: Dict[str, BaseExporter] = Depends(get_exporters)
) -> ReportResponse:
    """
    一键编译并物理导出报告控制器
    """
    # 1. 还原领域模型
    prod_req = req.product
    product_entity = Product(
        sku=prod_req.sku,
        name=prod_req.name,
        cost_price_brl=prod_req.cost_price_brl,
        weight_g=prod_req.weight_g,
        length_cm=prod_req.length_cm,
        width_cm=prod_req.width_cm,
        height_cm=prod_req.height_cm,
        category=prod_req.category,
        declared_value_usd=prod_req.declared_value_usd
    )

    plat_req = req.platform
    platform_entity = Platform(
        platform_id=plat_req.platform_id,
        platform_name=plat_req.platform_name,
        selling_price_brl=plat_req.selling_price_brl,
        seller_level=plat_req.seller_level,
        participate_fss=plat_req.participate_fss,
        affiliate_rate=plat_req.affiliate_rate
    )

    # 2. 依次调度底层运算
    fee_analysis = fee_service.get_fee_analysis(product_entity, platform_entity)
    fee_entity = fee_analysis.fee_details

    tax_analysis = tax_service.get_tax_analysis(
        product_entity,
        platform_entity,
        annual_revenue_brl=req.annual_revenue_brl,
        is_cross_border=req.is_cross_border,
        exchange_rate_usd_brl=req.exchange_rate_usd_brl
    )
    tax_fee_brl = tax_analysis.tax_fee_brl

    shipping_fee_brl = _ship_calculator.calculate(product_entity, platform_entity)

    profit_result = profit_service.calculate_profitability(
        product=product_entity,
        platform=platform_entity,
        annual_revenue_brl=req.annual_revenue_brl,
        is_cross_border=req.is_cross_border,
        exchange_rate_usd_brl=req.exchange_rate_usd_brl
    )

    proposal = recommendation_strategy.generate_integrated_proposal(
        product=product_entity,
        platform=platform_entity,
        fee=fee_entity,
        tax_fee_brl=tax_fee_brl,
        shipping_fee_brl=shipping_fee_brl,
        profit_result=profit_result
    )

    # 3. 组装嵌套 Report DTO (Report Domain)
    report_dto = report_builder.build_business_report(
        product=product_entity,
        platform=platform_entity,
        proposal=proposal,
        profit_result=profit_result,
        tax_fee_brl=tax_fee_brl,
        fee_entity=fee_entity,
        shipping_fee_brl=shipping_fee_brl,
        tax_regime_name=tax_analysis.tax_regime_name,
        effective_tax_rate=tax_analysis.effective_tax_rate
    )

    # 4. 获取对应的物理文件导出器
    fmt = req.format.lower().strip()
    exporter = exporters.get(fmt)
    if not exporter:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"不支持的物理导出格式: {fmt}"
         )

    # 5. 确定物理文件名 (安全规范：不含任何非法跨目录字符)
    # e.g., report_BR-TEST_shopee_brasil.pdf
    safe_sku = "".join(c for c in product_entity.sku if c.isalnum() or c in ("-", "_"))
    safe_plat = "".join(c for c in platform_entity.platform_id if c.isalnum() or c in ("-", "_"))
    filename = f"report_{safe_sku}_{safe_plat}.{fmt}"
    
    physical_path = EXPORTS_DIR / filename

    # 确保 exports/ 文件夹物理存在
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 6. 执行物理导出
    res = exporter.export(report_dto, str(physical_path))

    if not res.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"物理报告文件编译导出失败: {res.message}"
        )

    # 7. 安全响应：绝对不暴露系统盘符、完整父级系统路径，仅返回相对可下载路径或文件名
    download_url = f"/api/v1/reports/{filename}"

    return ReportResponse(
        success=True,
        file_path=download_url,
        filename=filename,
        format=fmt,
        message=res.message
    )


@reports_router.get(
    "/api/v1/reports/{filename}",
    summary="安全下载已生成的物理分析报表文件",
    description="支持白名单格式下载。配备最高等级的防目录穿越和沙盒控制，严格阻断任何读取 exports 目录以外文件的黑客行为。"
)
async def download_report_file(filename: str) -> FileResponse:
    """
     traversal-proof 物理报告文件安全下载控制器
    """
    # === 安全防御 1: 校验下载扩展名白名单 ===
    fmt = filename.split(".")[-1].lower().strip() if "." in filename else ""
    whitelist = {"json", "csv", "xlsx", "pdf"}
    if fmt not in whitelist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"禁止下载该类型格式的文件，仅支持下载 {list(whitelist)} 格式。"
        )

    # === 安全防御 2: 防范目录穿越攻击 (Path Traversal Protection) ===
    # 结合 Path.resolve() 和 is_relative_to 实现纯沙盒控制
    try:
        # 1. 物理绝对路径解析 (会消除所有的 '.' / '..' 及软连接)
        requested_path = (EXPORTS_DIR / filename).resolve()
        
        # 2. 强校验解析后的物理绝对路径，是否‘严格隶属于’ exports 根目录。
        # 如果黑客传入了 '/api/v1/reports/../../../../Windows/System32/drivers/etc/hosts' 
        # 解析后由于不再以 'D:\\Brazil-AI-Selector\\exports' 开头，is_relative_to 会直接返回 False，从而被安全粉碎。
        if not requested_path.is_relative_to(EXPORTS_DIR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="安全拦截：检测到目录穿越(Path Traversal)黑客攻击尝试，已被系统安全熔断！"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="安全拦截：非法的物理文件路径请求。"
        )

    # === 安全防御 3: 文件物理存在校验 ===
    if not requested_path.exists() or not requested_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请求下载的报告文件在服务器上不存在或已被清理。请重新提交编译生成。"
        )

    # 4. 执行安全下载
    return FileResponse(
        path=requested_path,
        filename=filename,
        media_type="application/octet-stream"
    )
