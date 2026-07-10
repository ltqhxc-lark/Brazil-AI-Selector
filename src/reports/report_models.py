# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报告领域模型与数据契约 (DTOs)
包含系统生成分析报告所需的全部纯数据模型 (Data Transfer Objects)。
这些类不包含任何读写磁盘、数据库、HTTP 或 PDF 导出的渲染逻辑，为纯净的领域契约层。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class SummaryReport:
    """
    概要报告数据对象 (DTO)
    """
    product_sku: str                    # 被分析商品 SKU
    product_name: str                   # 被分析商品名称
    platform_name: str                  # 目标销售平台名称
    overall_alert_level: str            # 综合安全级别 ("green", "yellow", "red")
    generated_at: str                   # 报告生成时间戳 (America/Sao_Paulo)

@dataclass
class TaxReport:
    """
    税务明细报告数据对象 (DTO)
    """
    tax_regime_name: str                # 所属税制类型名称 (如 "Simples Nacional")
    total_tax_brl: float                # 纳税绝对额 (BRL)
    formatted_total_tax: str            # 格式化纳税金额 (如 "R$ 6,38")
    effective_tax_rate: float           # 实际有效税率 (如 0.0532)
    formatted_tax_rate: str             # 格式化有效税率 (如 "5.32%")

@dataclass
class PlatformReport:
    """
    平台费用报告数据对象 (DTO)
    """
    commission_fee_brl: float           # 比例销售佣金 (BRL)
    formatted_commission: str           # 格式化佣金 (如 "R$ 20,40")
    fixed_fee_brl: float                # 单件固定手续费 (BRL)
    formatted_fixed_fee: str            # 格式化手续费 (如 "R$ 6,00")
    risk_loss_fee_brl: float            # 坏账损坏计提准备金 (BRL)
    formatted_risk_loss: str            # 格式化准备金
    total_fee_brl: float                # 平台总费用扣减 (BRL)
    formatted_total_fee: str            # 格式化总平台费

@dataclass
class FinancialReport:
    """
    损益与利润核算报告数据对象 (DTO)
    """
    revenue_brl: float                  # 预估销售总收入 (BRL)
    formatted_revenue: str              # 格式化收入 (如 "R$ 120,00")
    purchase_cost_brl: float            # 采购产品采购成本 (BRL)
    formatted_purchase_cost: str        # 格式化产品采购成本
    total_fee_brl: float                # 平台费用合计支出 (BRL)
    formatted_total_fee: str            # 格式化平台费用支出
    total_tax_brl: float                # 政府税金合计支出 (BRL)
    formatted_total_tax: str            # 格式化税金支出
    total_shipping_brl: float           # 卖家实付物流运费支出 (BRL)
    formatted_total_shipping: str       # 格式化实付运费
    net_profit_brl: float               # 纯利总金额 (BRL)
    formatted_net_profit: str           # 格式化纯利金额
    profit_margin: float                # 净利润率 (例: 0.2541 即 25.41%)
    formatted_profit_margin: str        # 格式化净利润率

@dataclass
class PricingReport:
    """
    定价建议报告数据对象 (DTO)
    """
    breakeven_price_brl: float          # 绝对保本门槛售价 (BRL)
    formatted_breakeven_price: str      # 格式化保本售价
    target_price_at_15_margin: float    # 15% 净利率对应的建议售价 (BRL)
    formatted_price_at_15_margin: str   # 格式化建议售价 (15% 净利)
    target_price_at_20_margin: float    # 20% 净利率对应的建议售价 (BRL)
    formatted_price_at_20_margin: str   # 格式化建议售价 (20% 净利)
    markdown_budget_brl: float          # 大促期间最大安全让利折扣空间 (BRL)
    formatted_markdown_budget: str      # 格式化最大让利空间

@dataclass
class MarketingReport:
    """
    广告及促销推广报告数据对象 (DTO)
    """
    suggested_ads_budget_ratio: float   # 建议广告占销售营收比 (如 0.08)
    formatted_ads_budget_ratio: str    # 格式化广告占比 (如 "8.00%")
    suggested_coupon_cap_brl: float     # 建议最高新客直降券金额限制 (BRL)
    formatted_coupon_cap: str           # 格式化直降券上限
    marketing_decision_text: str        # 广告及营销综合策略文案

@dataclass
class InventoryReport:
    """
    库存及供应链备货报告数据对象 (DTO)
    """
    recommended_import_channel: str     # 推荐货代通关通路 (如 "跨境 Remessa Conforme 直邮" 或 "海运正式进口")
    replenishment_lead_time_days: int   # 备货及物流提前期周期 (天数)
    recommended_moq: int                # 建议最小起订量 (MOQ)
    recommended_safety_stock: int       # 建议常备安全库存水位 (件数)
    inventory_decision_text: str        # 备货周期与本土配货综合策略文案

@dataclass
class WarningReport:
    """
    财务预警报告数据对象 (DTO)
    """
    alert_level: str                    # 预警等级 ("green", "yellow", "red")
    alert_description: str              # 预警状态一句中文判定
    warning_list: List[str] = field(default_factory=list) # 具体的成本/费税偏高警告明细列表

@dataclass
class RecommendationReport:
    """
    商业推荐综合建议报告数据对象 (DTO)
    """
    primary_platform_recommendation: str # 首发平台推荐结论文案
    action_items_list: List[str] = field(default_factory=list) # 具体的实操型指令清单 (To-do List)

@dataclass
class BusinessReport:
    """
    一站式巴西商业运营财务综合分析报告 (根容器 DTO)
    嵌套包含所有分类子报告数据，作为数据导出的终极核心实体。
    """
    summary: SummaryReport              # 1. 概要子报告
    financial: FinancialReport          # 2. 损益财务子报告
    tax: TaxReport                      # 3. 税金精算子报告
    platform: PlatformReport            # 4. 平台费用子报告
    pricing: PricingReport              # 5. 定价策略子报告
    marketing: MarketingReport          # 6. 营销推广子报告
    inventory: InventoryReport          # 7. 备货供应链子报告
    warnings: WarningReport            # 8. 财务预警子报告
    recommendations: RecommendationReport # 9. 综合行动建议子报告
